# User Flow

## Complete journey

```
Open app (phone, usually right after a real conversation)
      ↓
Login  ⟵ only if session has expired; normally skipped, session persists ~30 days
      ↓
Signal Feed  ⟵ default landing screen, chronological, newest first
      ↓
Tap "+ Ny signal"
      ↓
Create Signal (form)
      ↓
Save
      ↓
Return to Signal Feed  ⟵ new entry visible immediately at the top
      ↓
(days/weeks later) Open Signal Feed again
      ↓
Read a past entry directly in the feed  ⟵ no separate "detail" screen — see note below
      ↓
Tap "Redigera" (Edit) on that entry
      ↓
Edit Signal (same form, pre-filled)
      ↓
Save changes
      ↓
Return to Signal Feed
      ↓
(separately, anytime) Review Hypotheses  or  Weekly Review
```

## Core flow (the five screens that matter most)

1. **Login**
2. **Signal Feed**
3. **Create Signal**
4. **Edit Signal**
5. **Weekly Review**

These five are where visual design effort should concentrate first. Hypotheses List and Hypothesis Detail are real, used screens but secondary — reached deliberately, not part of the every-time loop.

## Important structural note

**There is no separate "Signal Detail" screen.** The feed itself *is* the
detail view — each entry in the Signal Feed shows its full content
(everything typed at capture time: what happened, what was learned, tags,
linked hypothesis, next step) directly inline, not truncated behind a
"view more" tap. Tapping an entry does not navigate anywhere; only
"Redigera" (Edit) does. This is a deliberate product decision (see
`design-constraints.md`) — don't introduce a detail screen or make the
feed a list of summaries that require a tap to expand.

## Entry points

- **Normal case:** phone home screen / browser bookmark → Login (if needed) → Signal Feed. This is the path that must be fastest and calmest — it's used dozens of times over the life of the app, usually within two minutes of a real conversation ending.
- **Reflection case:** opening Hypotheses or Weekly Review deliberately, seated, not rushed — a different mental mode (reviewing/thinking, not capturing). Fine for this to feel slightly more "considered" or slower-paced than the capture flow.

## What happens on save

Both Create and Edit redirect to the Signal Feed on save, where the
saved/edited entry is immediately visible (new entries at the top, since
the feed sorts newest-first). There is currently no separate confirmation
message beyond the entry's presence in the feed — see `ui-review.md`.
