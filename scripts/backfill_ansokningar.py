# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openpyxl",
#     "supabase==2.31.0",
#     "python-dotenv",
# ]
# ///
"""Backfill signals from a "Jobbansökningar"-style xlsx tracker.

One-off import script, built for a specific spreadsheet shape (sheet
"Ansökningar" with columns: Företag, Roll, Ort, Form, Deadline, Match,
Status, Inskickad, Största gap / not). Re-adjust PERSON_OVERRIDES/FLAGGED
below if you reuse this for a different export - they're specific to the
rows in the source file this was written against, not a generic mapping.

Usage:
    uv run scripts/backfill_ansokningar.py <path-to-xlsx>              # dry-run preview
    uv run scripts/backfill_ansokningar.py <path-to-xlsx> --insert     # actually write

Prompts for the Signals login email/password interactively (never stored
in this file or in .env) and writes through the same anon-key + user-session
pattern the app itself uses, so RLS applies exactly as it would for the
logged-in user.

Idempotent: matches existing signals by (organization, role_opportunity) and
signal_type="ansökan" - updates them if the mapped fields differ, skips them
otherwise. Safe to re-run.
"""
import getpass
import os
import re
import sys

import openpyxl
from dotenv import load_dotenv

load_dotenv()

DASH = "–"

# Rows where the source notes clearly name an individual as the actual
# contact/signal subject. Keyed by (organization, role_opportunity) after
# org-name cleanup. Anything not listed here keeps the generic placeholder.
PERSON_OVERRIDES = {
    ("Prick över IT", "Digital Product Manager"): "Niklas",
    ("Prick över IT", "Interim ledare utvecklingsteam"): "Niklas",
    ("Softronic", "Leveransledare"): "Mattias Flock",
    ("Softronic", "Programledare"): "Mattias Flock",
    ("WirelessCar", "Senior Product Owner"): "Nisha",
}

# Rows flagged as ambiguous: a name is mentioned but it's unclear whether it
# should replace the placeholder for the whole signal, or whether the row
# actually represents two distinct interactions compressed into one. Not
# auto-resolved - reported at the end for manual review instead.
FLAGGED = {
    ("OneForLife AB", "Projektledare/PMO-stöd (konsult)"): (
        "Anteckningen nämner Maria (Sylog-intervju gick bra), men ansökan gick till "
        "OneForLife/Saab. Detta kan vara två separata signaler (ansökan + intervju "
        "med Maria) som klumpats ihop i källdatan."
    ),
}


def load_rows(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Ansökningar"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    mapped = []
    for r in rows:
        foretag, roll, ort, form, deadline, match, status, inskickad, gap = r
        org_match = re.match(r"^(.*?)\s*\((.+)\)\s*$", foretag)
        if org_match:
            organization, paren = org_match.group(1), org_match.group(2)
        else:
            organization, paren = foretag, None

        note_parts = ["Ansökan skickad."]
        if paren:
            note_parts.append(f"Kontext: {paren}.")
        if ort and ort != DASH:
            note_parts.append(f"Ort: {ort}.")
        if form:
            note_parts.append(f"Form: {form}.")
        if match not in (None, DASH):
            note_parts.append(f"Match: {match}%.")
        if status:
            note_parts.append(f"Status: {status}.")
        if deadline and deadline != DASH:
            note_parts.append(f"Deadline: {deadline}.")
        note = " ".join(note_parts)

        key = (organization, roll)
        person = PERSON_OVERRIDES.get(key, "Rekryteringsprocess")

        mapped.append(
            {
                "key": key,
                "date": inskickad.date().isoformat() if hasattr(inskickad, "date") else str(inskickad),
                "person": person,
                "organization": organization,
                "role_opportunity": roll,
                "signal_type": "ansökan",
                "note": note,
                "learning": gap,
            }
        )
    return mapped


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Usage: uv run scripts/backfill_ansokningar.py <path-to-xlsx> [--insert]")
        sys.exit(1)
    xlsx_path = args[0]
    do_insert = "--insert" in sys.argv

    mapped = load_rows(xlsx_path)
    for i, m in enumerate(mapped, 1):
        print(f"--- {i}/{len(mapped)} ---")
        print(f"date={m['date']}  person={m['person']}  organization={m['organization']}")
        print(f"role_opportunity={m['role_opportunity']}")
        print(f"note={m['note']}")
        print(f"learning={m['learning'][:120]}{'...' if len(m['learning']) > 120 else ''}")
        print()
    print(f"Totalt {len(mapped)} rader mappade.")
    if FLAGGED:
        print(f"\n{len(FLAGGED)} rad(er) flaggade för manuell granskning:")
        for (org, role), reason in FLAGGED.items():
            print(f"  - {org} / {role}: {reason}")

    if not do_insert:
        print("\n(Dry run - kör med --insert för att faktiskt skriva till databasen.)")
        return

    from supabase import ClientOptions, create_client

    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_ANON_KEY"],
        options=ClientOptions(schema="signals"),
    )
    email = os.environ.get("SIGNALS_EMAIL") or input("E-post: ")
    password = getpass.getpass("Lösenord: ")
    auth = client.auth.sign_in_with_password({"email": email, "password": password})
    client.auth.set_session(auth.session.access_token, auth.session.refresh_token)
    user_id = auth.user.id

    existing = (
        client.table("signals")
        .select("id, organization, role_opportunity, person, note, learning, date")
        .eq("user_id", user_id)
        .eq("signal_type", "ansökan")
        .execute()
        .data
    )
    existing_by_key = {(r["organization"], r["role_opportunity"]): r for r in existing}

    created, updated, skipped = 0, 0, 0
    for m in mapped:
        key = m["key"]
        payload = {k: v for k, v in m.items() if k != "key"}
        match_row = existing_by_key.get(key)
        if match_row is None:
            client.table("signals").insert({**payload, "user_id": user_id}).execute()
            created += 1
        else:
            diffs = {
                f: payload[f]
                for f in ("person", "note", "learning", "date")
                if match_row.get(f) != payload[f]
            }
            if diffs:
                client.table("signals").update(diffs).eq("id", match_row["id"]).execute()
                updated += 1
            else:
                skipped += 1

    print(f"\nKlart. Skapade: {created}, uppdaterade: {updated}, oförändrade: {skipped}.")


if __name__ == "__main__":
    main()
