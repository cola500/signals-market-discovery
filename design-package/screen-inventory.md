# Screen Inventory

Seven screens total. Two states of the Signal Feed (empty and populated)
are documented separately since they're visually very different and both
matter (empty state is a new user's — or a fresh week's — first
impression).

---

## 1. Login

**Purpose:** the only gate in the app. Email + password, no public
sign-up (accounts are created for the one user by hand).

**Primary action:** submit email + password → "Logga in"

**Secondary actions:** none. No "forgot password" link, no "create
account" link. This is intentional for v1 — see `design-constraints.md`.

**Information hierarchy:** heading ("Logga in") → email field → password
field → submit button. Nothing else on the screen. This is the simplest
screen in the app and should probably stay that way — but it's also the
very first thing seen, so its tone sets expectations for everything after.

**Screenshot:** `screenshots/01-login.png`, framed: `mobile/framed-01-login.png`

---

## 2. Signal Feed — empty state

**Purpose:** what a brand-new account (or an account with a fresh 7-day
window) sees. Currently: nav, "Signal Feed" heading, a "+ Ny signal" link,
and the line "Inga signaler ännu." ("No signals yet.")

**Primary action:** "+ Ny signal" (Create Signal) — the only thing to do here.

**Secondary actions:** none.

**Information hierarchy:** nav → heading → create-link → empty message.
Very sparse — arguably the screen most in need of personality, since it's
what greets a slow week or a new user.

**Screenshot:** `screenshots/11-feed-empty.png`

---

## 3. Signal Feed — populated

**Purpose:** the default landing screen and the core "browse what I know"
view. Chronological, newest first. Doubles as the detail view (see
`user-flow.md`) — every entry shows its full captured content inline, not
a summary.

**Primary action:** "+ Ny signal" (Create Signal) — placed at the top, above the list.

**Secondary actions, per entry:**
- "Redigera" (Edit) — always present
- "Klarmarkera" (Mark done) — only present if the entry has an open next
  step (`next_action` set and not yet done)

**Information hierarchy, per entry (top to bottom):**
1. Date + person + organization (bolded date, plain name)
2. Signal type + channel (small gray badges)
3. The note — what happened (the longest, most-read text on the screen)
4. Optional fields, each with an italic label: Lärde mig (Learning), Roll/möjlighet (Role/opportunity), Problem/behov (Problem heard), Skapade intresse (What created interest)
5. Tags (colored pills — pink for "problem" category, blue for "role" category)
6. Linked hypothesis, if any (colored text — green "Stödjer"/supports, red "Motsäger"/contradicts — followed by the hypothesis statement)
7. Next step, if any, with its Klarmarkera button, or struck-through with "(klar)" if already done
8. Redigera link

Every field above is optional except date, person, signal type, and note
— so real entries vary a lot in length and shape. Design should handle a
4-line entry and a 20-line entry equally gracefully.

**Screenshots:** `screenshots/02-feed-top.png`, `03-feed-scrolled.png`; framed: `mobile/framed-02-feed-top.png`

---

## 4. Create Signal

**Purpose:** the single most important screen — this is what gets opened
within minutes of a real conversation ending. Speed and low friction here
matter more than on any other screen.

**Primary action:** "Spara signal" (Save), full-width button at the bottom.

**Secondary actions:** none — no cancel button (back navigation serves that).

**Information hierarchy (top to bottom), all in one long form:**
1. Datum (date, defaults to today) *required*
2. Person *required*
3. Organisation
4. Signal-typ (dropdown of past values + "kaffe/lunch/rekryterarkontakt/..." seed suggestions, plus a free-text override field directly below it) *required*
5. Roll/möjlighet (role/opportunity, free text)
6. Kanal (channel — same dropdown + free-text-override pattern as Signal-typ)
7. Vad hände? (what happened — the main note) *required*
8. Vad lärde jag mig? (what I learned)
9. Vilket problem/behov hörde jag? (what problem/need I heard)
10. Vad skapade intresse för min bakgrund? (what created interest in my background)
11. Problem-taggar / Roll-taggar (two comma-separated free-text tag fields)
12. A boxed sub-section: link to an existing hypothesis (dropdown) OR type a new one, plus Stödjer/Motsäger (supports/contradicts) relation
13. Nästa steg (next step, free text)
14. Save button

Fields 2, 4, 7 are required; everything else is optional. The form is
long — 13 inputs — by design (see `design-constraints.md`), so visual
grouping/rhythm matters more here than almost anywhere else in the app.

**Screenshots:** `screenshots/04-create-top.png`, `05-create-bottom.png`; framed: `mobile/framed-04-create-top.png`

---

## 5. Edit Signal

**Purpose:** correcting or expanding a past entry. Structurally identical
to Create Signal — same fields, same order — but pre-filled with the
entry's current values, heading reads "Redigera signal," and the button
reads "Spara ändringar" (Save changes).

**Primary action:** "Spara ändringar"

**Secondary actions:** none (again, back navigation is "cancel").

**Information hierarchy:** identical to Create Signal. The only visual
difference today is the heading and button text — worth knowing, since a
design that makes Create and Edit look distinct from each other should
still keep them recognizably the same *kind* of screen.

**Screenshots:** `screenshots/06-edit-top.png`, `07-edit-bottom.png`; framed: `mobile/framed-06-edit-top.png`

---

## 6. Hypotheses List

**Purpose:** browse every hypothesis the user has formed, each with a
running tally of supporting vs. contradicting signals.

**Primary action:** tap a hypothesis to open its detail.

**Secondary actions:** none on this screen (hypotheses are only created
from within Create/Edit Signal, never here directly).

**Information hierarchy, per row:** hypothesis statement (as a link) →
status badge (exploring / strengthening / weakening / retired, set
manually by the user) → supports count → contradicts count.

**Screenshot:** `screenshots/08-hypotheses-list.png`

---

## 7. Hypothesis Detail

**Purpose:** inspect the actual evidence behind one hypothesis — every
signal that supports or contradicts it, and change its status.

**Primary action:** change Status via a dropdown (auto-submits on change — no separate save button).

**Secondary actions:** "← Alla hypoteser" back link.

**Information hierarchy:** back link → hypothesis statement as page
heading → status dropdown → "Stödjande signaler (N)" with a bulleted list
(date — person: note) → "Motsägande signaler (N)" with the same format.

**Screenshot:** `screenshots/09-hypothesis-detail.png`; framed: `mobile/framed-09-hypothesis-detail.png`

---

## 8. Weekly Review

**Purpose:** a once-a-week (or so) reflection view. Pure aggregation —
no AI, nothing computed beyond counts and groupings.

**Primary action:** none — this is a read-only reflection screen.

**Secondary actions:** links into Hypothesis Detail from the "new
evidence" list.

**Information hierarchy (top to bottom):**
1. "N signaler senaste 7 dagarna" (signal count, last 7 days)
2. "Mest frekventa problem-taggar" (most frequent problem tags, with counts)
3. "Mest frekventa roll-taggar" (most frequent role tags, with counts)
4. "Hypoteser med ny evidens denna vecka" (hypotheses with new evidence this week, with +supports/+contradicts deltas)
5. "Obehandlade nästa steg" (outstanding next actions — not time-boxed to the week, shows all open ones regardless of age)

Any of sections 2–5 can be empty (e.g. a week with no signals shows empty
lists under still-present headings) — worth designing an intentional
empty/sparse state for this screen specifically.

**Screenshot:** `screenshots/10-review.png`

---

## Not a screen: the validation alert

Signal-typ is required, but is filled via either a dropdown or a
free-text override field — neither of which the browser's native
`required` attribute can express well as an either/or. Today this is
enforced with a plain JavaScript `alert()` if you try to save with both
empty. It's a native browser dialog, visually disconnected from
everything else in the app. Worth knowing about even though it isn't a
"screen" — see `ui-review.md`.
