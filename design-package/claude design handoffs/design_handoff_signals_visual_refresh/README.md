# Handoff: Signals visual refresh

## Overview
Applies the new Signals design system (warm coral/cream palette, Manrope + JetBrains Mono type, rounded cards, pill tags) to the real app at `cola500/signals-market-discovery`. The app is a single-file Flask app (`app.py`) that renders plain HTML via `render_template_string` — **no build step, no React** — so this is a drop-in CSS swap, not a framework migration.

## About the design files
The design-system project (React/JSX components, HTML cards) is a set of **design references** — they show the intended look, not code to paste into this Flask app. The one exception is `signals-style-block.html` in this folder: it's plain CSS, written to slot directly into `app.py`.

## Fidelity
**High-fidelity.** Exact colors, radii, shadows and type are final — implement pixel-for-pixel.

## The one change to make
In `app.py`, the `STYLE` constant currently holds a `<style>...</style>` string. Replace its **entire contents** with the contents of `signals-style-block.html` in this folder. Every CSS selector in it (`nav a`, `.feed li`, `.tag.problem`, `.btn-primary`, `.error`, etc.) matches the class names already used in `app.py`'s Jinja templates exactly — no template/HTML changes needed.

```python
STYLE = """
<style>
... paste contents of signals-style-block.html here ...
</style>
"""
```

That's it — every route (`/login`, `/`, `/signals/new`, `/hypotheses`, `/review`) restyles automatically since they all render through the shared `page()` wrapper.

## Design tokens used
- **Colors**: cream `#FFF9F0` background, ink `#1C1712`/`#5C5346` text, coral `#FF6A47` primary (hover `#F04F28`, active `#C93B18`), teal `#1E6A5F`/`#D9F1EC` for role tags, rose `#D8365A`/`#FBE3E8` for problem tags + errors + "contradicts", green `#2E9E5B` for "supports".
- **Type**: Manrope (headings 700, body 400–600), JetBrains Mono available for dates/ids if you add any — both loaded via the `@import` at the top of the style block (Google Fonts substitution — no brand font files exist yet).
- **Radius**: 10px inputs/buttons, 16px cards, full-pill tags/badges.
- **Shadow**: one soft warm shadow (`--shadow-sm`) on feed cards; nothing else.
- **Motion**: 120ms ease-out on hover/press, buttons scale to 0.97 on click.

## Not covered by this pass
- No logo exists — the app has no header wordmark to restyle.
- No new screens or fields — this is styling only, matching the app's current structure exactly.
- The fuller design system (component variants, a richer interactive prototype, review/hypothesis card layouts) lives in the design-system project if `app.py` ever grows beyond inline Jinja strings into real templates/components — treat that as a future reference, not something to implement now.

## Files
- `signals-style-block.html` — the full CSS, ready to paste into `STYLE` in `app.py`.
