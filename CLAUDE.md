# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Signals is a personal field journal for one person's job search: capture short "signals" (a coffee meeting, a recruiter's LinkedIn message, an interview) and link them to evolving hypotheses about the job market. It optimizes for learning ("what did this teach me?"), not pipeline tracking — there is deliberately no CRM/ATS-style stage or status concept. See `HYPOTHESIS.md` for the experiment framing and success criteria.

Live at https://signals-market-discovery.vercel.app.

## Commands

```bash
uv run app.py                                              # run locally on :5050 (requires .env — see .env.example)
python3 -c "import ast; ast.parse(open('app.py').read())"  # syntax-check (no linter/formatter configured)
vercel --prod                                               # manual deploy (normally automatic on push to main via the connected GitHub repo)
```

There is no automated test suite by design (single-user personal tool). Verification is manual: run the app, drive it with `curl` (cookies via `-c`/`-b` for authenticated flows) and inspect state with `sqlite3`-style SQL against Supabase (via the Supabase MCP tools or dashboard SQL editor), and check mobile rendering with real device emulation (touch + iPhone UA + viewport via CDP, not just a resized desktop browser window) since this is a mobile-first app.

## Architecture

**Single file.** `app.py` is the entire application — routes, Supabase queries, and HTML all live here. Templates are Python string constants (`STYLE`, `NAV`, `LOGIN_TEMPLATE`, `SIGNAL_FORM_TEMPLATE`, `FEED_TEMPLATE`, `HYPOTHESES_LIST_TEMPLATE`, `HYPOTHESIS_DETAIL_TEMPLATE`, `REVIEW_TEMPLATE`) rendered via Flask's `render_template_string`, wrapped by `page(title, body_template)` which stitches in `HEAD_EXTRAS`, `STYLE`, `SPLASH`, and `NAV`. No build step, no client-side framework. Dependencies are declared twice and must be kept in sync: the PEP 723 header at the top of `app.py` (for `uv run`) and `requirements.txt` (for Vercel's build).

**Persistence: Supabase Postgres, not SQLite.** All data lives in a `signals` Postgres schema inside a Supabase project that is *shared with an unrelated app* ("Equinet") — Signals' tables are isolated in their own schema (`public`/`staging` in that project belong to the other app; never touch them). The `signals` schema had to be explicitly exposed to PostgREST via `pgrst.db_schemas` — this isn't visible anywhere in this repo, only in the Supabase project config. `get_supabase()` creates a client scoped with `ClientOptions(schema="signals")`. A leftover `signals.db` file and `*.db` gitignore rule are vestigial from an earlier SQLite prototype and are unused by the current code.

**Data model.** Five tables (`signals`, `tags`, `signal_tags`, `hypotheses`, `signal_hypotheses`), every one carrying its own `user_id` (denormalized rather than joined through `signals`, so every RLS policy is a simple `USING (user_id = auth.uid())`). Tags dedupe per-user via `UNIQUE(user_id, text, category)`. **RLS is the actual access boundary** — the app never uses a service-role/privileged key, only the anon key plus the logged-in user's access token, so a query can only ever see that user's own rows regardless of app-level bugs. (App code still adds explicit `.eq("user_id", ...)` filters as defense in depth.)

**Auth.** Supabase Auth, email/password only, no public sign-up (accounts are created by hand in the Supabase dashboard). No server-side session store: the Flask session cookie holds the Supabase access/refresh tokens directly (httpOnly, secure, `SameSite=Lax`, 30-day permanent). `get_supabase()` calls `client.auth.set_session(...)` on every request, which transparently refreshes an expired access token and rewrites the (possibly new) tokens back into the Flask session. `@login_required` wraps every route except `/login`.

**Static assets on Vercel.** The app icon is served from `public/app-icon.svg`, *not* Flask's `static/` folder — Vercel's own docs advise against `static_folder` there in favor of `public/**`, which is served directly from the edge rather than through the Python function. A small `@app.route("/app-icon.svg")` exists purely so the same URL also works under local `uv run app.py`, where there is no `public/**` routing layer; on Vercel this route is effectively dead code since the platform intercepts the path first (mirrors the pattern Vercel's own docs use for `/favicon.ico`).

**Design system.** Coral/cream palette and type scale as CSS custom properties at the top of `STYLE` (`--coral-500`, `--ink-950`, `--cream-50`, etc.) — reuse these tokens rather than hardcoding new colors. Nav is a fixed bottom tab bar (icon + label, inline SVGs using `stroke="currentColor"` so they inherit link color/hover state with no per-icon CSS) with `env(safe-area-inset-bottom)` padding for the iPhone home indicator. A splash screen (`SPLASH` constant) shows once per browser session via `sessionStorage`, not on every page load — it must stay gated like this or it reappears on every internal navigation (this app has no client-side routing, so *every* nav click is a full page reload).

## Known gotchas

- **Vercel env vars set via `vercel env add <key> <env>` piped from stdin (or `--value`) can silently save as an empty string** even though the CLI reports success. Always verify with `vercel env pull` and check the actual byte length after setting a var this way; when it happens, delete and re-add via the REST API (`POST /v10/projects/{id}/env`) instead.
- **Vercel function region must match the Supabase project's region** (pinned to `fra1` in `vercel.json` — Supabase is in Frankfurt/`eu-central-1`) or every request pays cross-Atlantic latency.
- Signal-type and channel are deliberately not a fixed enum: `distinct_values()` builds a `<select>` from past values plus a small seed list, and each has a free-text override field (`resolve_select_or_other()`) that takes precedence over the dropdown when non-empty. An earlier `<datalist>`-based version of this was replaced after it proved unreliable on iOS Safari (dropdown selection silently failed to populate the field) — don't reintroduce `<datalist>` for these fields, and don't hardcode a fixed taxonomy either.
