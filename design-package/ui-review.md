# Current UI Review

Observations only — no proposed fixes. These are things noticed while
building, verifying, and stress-testing the app across several rounds,
including a dedicated mobile-first usability pass. Take them as "here's
what's actually true about the interface today," for Claude Design to
interpret.

## What already works well

- **Touch targets are properly sized.** Buttons, nav links, and form
  controls all measure at or above the ~44px mobile guideline — this was
  specifically measured and fixed in an earlier pass, not accidental.
- **No zoom problems.** Viewport is configured correctly, form field font
  size is 16px everywhere (avoids the iOS Safari auto-zoom-on-focus
  behavior), and nothing requires pinch-zooming to read or tap.
- **The primary action is unambiguous on the two screens that need it
  most.** "Spara signal" / "Spara ändringar" is a full-width button at the
  bottom of the form — there's no competing action nearby.
- **Content-dense entries are still readable.** The feed renders
  multi-paragraph entries (some captured signals run to 500+ characters)
  without truncation, scrollbars-within-scrollbars, or layout breakage.
- **Empty states exist and are handled gracefully** — an empty feed, an
  empty hypothesis list, and a sparse weekly review all render sensible
  (if plain) messages rather than looking broken.
- **Fast.** Every screen is a simple server-rendered page — no client-side
  framework, no loading spinners, no skeleton states needed because
  there's essentially no perceptible wait.
- **Consistent field behavior.** Every optional field is either shown with
  its content or omitted entirely — there's no visual clutter from empty
  labels or "N/A" placeholders anywhere in the feed.

## Where the interface feels unfinished

- **Almost no color.** Outside of two tag-pill background colors (pale
  pink/blue) and two text colors for hypothesis relation (green/red),
  the entire app is black text on white, with gray for secondary
  elements. Nothing currently signals "this app has a personality."
- **Flat visual hierarchy.** Headings, labels, and body text are
  differentiated mostly by size and bold/italic — there's one typeface
  throughout (the system default), one weight scale, and no use of color,
  spacing rhythm, or type scale to create a clear sense of "this matters
  more than that" beyond H1 > H2 > body.
- **No active/current-page indication in navigation.** The four nav links
  look identical regardless of which screen you're on.
- **Buttons don't visually distinguish importance beyond one case.**
  "Spara signal" is full-width; every other button (Klarmarkera, Logga ut,
  the hypothesis status select) uses the same plain gray button style
  with no visual signal for primary vs. secondary vs. destructive.
- **Feed entries are dense text blocks.** Separation between entries is a
  single thin horizontal line; within an entry, up to seven optional
  fields stack directly on top of each other with no visual grouping,
  card treatment, or breathing room beyond default paragraph spacing.
  Scanning several entries quickly (the actual use case for "review
  previous signals") takes real reading effort right now.
- **The long form (13 fields) has one visual grouping and twelve
  ungrouped fields.** Only the hypothesis section is boxed
  (`<fieldset>`); everything else is a flat, undifferentiated list from
  top to bottom.
- **Tags and badges use color inconsistently.** Signal-type/channel
  badges are neutral gray; problem/role tags are colored; hypothesis
  relation is colored text, not a badge. Three different visual treatments
  for what are conceptually similar "small labeled chip" elements.
- **No iconography anywhere.** Every action and every piece of metadata
  (date, tag, relation) is communicated through text alone.
- **No brand mark.** No logo, no app icon treatment, no favicon — the
  browser tab and any future home-screen icon currently have nothing.
- **Native form controls look inconsistent with everything else.** The
  `<select>` dropdowns and date picker render with the OS/browser's
  default styling, which visually clashes with the custom-styled text
  inputs and buttons around them — most noticeable on iOS.
- **No save confirmation.** After Save, the only feedback that anything
  happened is landing back on the feed and seeing the new/edited entry at
  the top. There's no toast, checkmark, or transition marking the save
  itself.
- **One native browser dialog exists.** A JavaScript `alert()` fires if
  Signal-typ is left empty in both its dropdown and free-text-override
  form — this is unstyled OS chrome, visually disconnected from the rest
  of the app, and the only "dialog" of any kind in the product.
- **The empty states are functional but plain.** "Inga signaler ännu." is
  accurate but has no warmth, illustration, or invitation — for a "field
  journal" tone, this is probably the single highest-leverage moment (a
  new user's or a quiet week's very first impression) that currently gets
  the least design attention.
