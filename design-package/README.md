# Signals — Design Package for Claude Design

This package hands off a functionally complete, verified application for
**visual refinement only**. Implementation is done. Nothing here should be
read as a request to change how the product works — only how it looks and
feels.

---

## 1. Product Summary

**Signals** is a personal field journal for one person's job search. Its
owner uses it to capture small, real signals from the market — a coffee
meeting, a recruiter's LinkedIn message, an interview, a lunch with a
former colleague — and to link those signals to evolving hypotheses about
what kind of role and organization would actually value his experience.

**Who it's for:** one person, on their phone, usually moments after a
real conversation has ended.

**Primary outcome:** better market hypotheses and better next actions —
*not* more applications sent or interviews booked. Success is measured in
insight, not activity.

**Primary workflow:** open the app on a phone right after a conversation,
capture what happened in under two minutes, save it, and trust it will
still be there — correct and findable — whenever it's revisited days or
weeks later.

**What makes it different from a CRM or job tracker:** those tools
optimize for pipeline and status ("what stage is this application in?").
Signals optimizes for learning ("what did this teach me?"). A conversation
that produced no job opportunity but a sharp insight is more valuable here
than an application with no signal attached. There is no pipeline, no
stage, no funnel — just a chronological journal and a small set of
hypotheses that signals either support or contradict.

---

## 8. Design Goals

Signals should feel like:
- a **field journal** — something you jot in right after the fact, not something you "manage"
- **calm** — low visual noise, nothing competing for attention
- **lightweight** — opens fast, asks little, gets out of the way
- **enjoyable to open** — a small daily/weekly ritual, not a chore

Signals should **not** feel like:
- enterprise software
- a CRM
- a project management tool

If a design choice makes the app feel more "serious" or "administrative,"
it's probably moving in the wrong direction — even if it looks more
polished in isolation.

---

## 9. Inspiration

These are reference points for *feeling*, not for literal UI copying:

- **Bear** — warm, typography-led, minimal chrome. The bar for "a text-heavy app that still feels good to open."
- **Apple Notes** — the platonic ideal of a low-friction capture tool. No ceremony between opening the app and writing something down.
- **Things** — proof that a task/list-shaped app can feel calm and considered rather than corporate, through restraint and typography rather than decoration.
- **Linear** — sharp, confident use of a *small* color palette and clear hierarchy without clutter. Relevant for how the tag/relation colors could feel more intentional.
- **Obsidian Mobile** — a personal knowledge tool that respects density (real content, real length) without feeling like a spreadsheet. Relevant because Signals' entries are genuinely text-heavy, like Obsidian's notes.
- **Field Notes** (the paper notebook brand) — the literal metaphor: a small, honest, no-frills capture ritual. Relevant to the *tone*, not the screen design.
- **Moleskine** — same instinct as Field Notes, slightly warmer/more considered. Useful for thinking about texture, warmth, and personal ownership rather than sterile utility.

---

## 10. What We're Asking Claude Design For

Please return:
- **Annotated mockups** for the core-flow screens (see `screen-inventory.md`)
- **Visual improvement recommendations** — what changes and why
- **Spacing recommendations**
- **Typography recommendations** (type scale, weight, hierarchy)
- **A color palette** (the app currently has almost none — see `ui-review.md`)
- **Component suggestions** (cards, tags, buttons, empty states, nav)
- **Interaction/micro-interaction improvements** (e.g. save confirmation, active-state feedback)

**Please do NOT return code.** This is a design-only handoff — implementation happens separately, informed by your recommendations.

See `design-constraints.md` before proposing anything — it lists what must not change.

---

## Package Contents

- `README.md` — this file
- `user-flow.md` — the complete user journey, with the core flow marked
- `screen-inventory.md` — every screen, its purpose and hierarchy
- `design-constraints.md` — what must not change, and the exact terminology to preserve
- `ui-review.md` — honest observations on what works and what feels unfinished (no proposed solutions)
- `screenshots/` — real screens, real (fictional) content, mobile viewport
- `mobile/` — the same key screens presented inside a phone frame
- `assets/` — a reference sheet of the colors/type/components the app currently actually uses
