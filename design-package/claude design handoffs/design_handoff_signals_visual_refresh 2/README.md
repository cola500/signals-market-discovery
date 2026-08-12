# Handoff: Signals visual refresh (v2 — mobile/PWA)

## Overview
Restyles the real app at `cola500/signals-market-discovery` with the Signals design system, and makes it feel like a native app when added to an iPhone home screen: app icon, splash, and the existing nav restyled as a bottom tab bar. The app is a single-file Flask app (`app.py`, `render_template_string`, no build step) — everything here is a **CSS + a few head lines** change, no template restructuring.

## Fidelity
High-fidelity — exact colors, radii, spacing are final.

## Steps

**1. Style block.** Replace the entire contents of the `STYLE` constant in `app.py` with `signals-style-block.html`'s contents. Every selector matches the class names already in `app.py`'s templates (`.feed`, `.tag.problem`, `.btn-primary`, `nav a`, etc.) — no HTML changes. This version also turns the existing `<nav>` into a **fixed bottom tab bar** purely via CSS (`position:fixed` + safe-area padding) — the nav's links and structure in `app.py` stay exactly as they are today.

**2. App icon.** Save `app-icon.svg` from this folder into a new `static/` folder next to `app.py` (Flask serves `/static/` automatically). A coral square with a white radar/signal-wave mark — the system's brand mark, no existing logo was replaced.

**3. Head tags.** Add the contents of `head-additions.html` inside `page()`'s `<head>...</head>` string in `app.py` (anywhere after `<meta name='viewport'...>` is fine).

**4. Splash screen.** Add the contents of `splash-markup.html` right after `<body>` in `page()` — shows the coral icon for ~0.4s while the page loads, then fades out. Pure HTML/CSS/JS, no extra assets.

## Design tokens
Coral `#FF6A47` (hover `#F04F28`, active `#C93B18`) primary; cream `#FFF9F0` background; ink `#1C1712`/`#5C5346` text; teal `#1E6A5F` role tags; rose `#D8365A` problem tags/errors/"contradicts"; green `#2E9E5B` "supports". Manrope + JetBrains Mono (Google Fonts — no brand font files exist). 10px input/button radius, 16px cards, full-pill tags. 120ms ease-out hover/press, 0.97 press-scale.

## Not covered
- No app-switcher/task-view treatment beyond the icon (iOS derives that from the page itself).
- Nav items aren't icon+label (original app has text-only links) — restyled as a bottom bar with labels only, to stay a CSS-only change. Icon labels would need template edits; ask if you want that as a v3.

## Files
- `signals-style-block.html` — full CSS (step 1).
- `app-icon.svg` — home-screen icon (step 2).
- `head-additions.html` — PWA meta tags (step 3).
- `splash-markup.html` — splash screen markup + script (step 4).
