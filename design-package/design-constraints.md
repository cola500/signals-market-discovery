# Design Constraints

The implementation already works and has been verified end-to-end,
including on a real mobile device flow (login → capture → save → return →
edit → save → close app → reopen → data still there → review). This
package exists so that verified behavior can stay exactly as it is while
the visual layer improves.

## Do NOT change

**Workflow.** The sequence — Login → Feed → Create → Save → Feed → Edit →
Save → Review — is fixed. Don't add steps (confirmation screens, onboarding
flows, wizards), don't remove steps, don't reorder them.

**Navigation.** Four destinations, always reachable, always in the same
place: Feed, "+ Ny signal" (New Signal), Hypoteser (Hypotheses),
Veckoöversikt (Weekly Review) — plus a Logga ut (Log out) control. Don't
introduce a different information architecture (e.g. tabs that hide one of
these, a hamburger menu, a bottom sheet). Restyling the nav is welcome;
changing what's *in* it is not.

**Data model.** Every field that appears on Create/Edit Signal exists for
a reason and is either required or deliberately optional — see
`screen-inventory.md` for the exact list. Don't propose removing a field,
merging fields, or adding new ones. If a field feels redundant or
confusing, say so as an *observation* (that's welcome, see `ui-review.md`)
rather than a instruction to cut it — that's a product decision, not a
design one.

**Terminology.** All copy is Swedish and specific. Do not rename, translate
differently, or "improve" the wording of the following — treat these as
fixed labels, not draft copy:

- Nav: **Feed**, **+ Ny signal**, **Hypoteser**, **Veckoöversikt**, **Logga ut**, **Logga in**
- Screen headings: **Signal Feed**, **Ny signal**, **Redigera signal**, **Hypoteser**, **Veckoöversikt**
- Form fields: **Datum**, **Person**, **Organisation**, **Signal-typ**, **Roll/möjlighet (valfritt)**, **Kanal**, **Vad hände?**, **Vad lärde jag mig?**, **Vilket problem/behov hörde jag?**, **Vad skapade intresse för min bakgrund?**, **Problem-taggar (kommaseparerat)**, **Roll-taggar (kommaseparerat)**, **Befintlig hypotes**, **Eller skriv en ny hypotes**, **Relation**, **Stödjer**, **Motsäger**, **Nästa steg (valfritt)**
- Buttons: **Spara signal**, **Spara ändringar**, **Klarmarkera**, **Redigera**
- In-feed labels: **Lärde mig:**, **Roll/möjlighet:**, **Problem/behov:**, **Skapade intresse:**, **Nästa steg:**, **(klar)**
- Hypothesis statuses: **exploring**, **strengthening**, **weakening**, **retired** (these are stored values, shown as-is — not translated)
- Empty states: **Inga signaler ännu.**, **Inga hypoteser ännu.**

If a redesign changes information architecture in a way that genuinely
requires new copy (e.g. a new empty-state message), flag it explicitly as
new/added copy rather than silently reworking existing labels.

## What IS in scope

Presentation, and only presentation:
- Layout, spacing, visual rhythm
- Typography (scale, weight, hierarchy)
- Color (there is almost none today — seeing `ui-review.md`)
- Component styling: buttons, tags, badges, form fields, cards
- Empty states (visual treatment, not wording)
- Micro-interactions and transitions, as long as they don't add a step to the workflow
- Iconography, if it clarifies rather than decorates

## One more thing

This is a five-table, one-user, server-rendered app on purpose (see
`README.md` for why). A design direction that implicitly assumes a richer
client-side app — animated list reordering, drag-and-drop, real-time
updates, offline sync — is out of scope for this round, even if it would
look good. Flag such ideas as future considerations rather than baking
them into the primary recommendation.
