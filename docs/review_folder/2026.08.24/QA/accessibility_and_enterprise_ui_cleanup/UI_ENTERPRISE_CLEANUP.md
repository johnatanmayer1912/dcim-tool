# Enterprise UI cleanup — 2026-08-24

## Design intent

Calm, restrained, operational surfaces suitable for long NOC sessions. Removed marketing-style gradients, rainbow map CTAs, and purple discovery tinting.

## Operator console (`modules/web/templates/index.html`)

| Area | Before | After |
|------|--------|-------|
| `.btn-primary/secondary/success/danger` | Linear gradients + lift shadows | Flat semantic colors, light shadow |
| `.btn-mac` / `.btn-mac-primary` | Gradients + ripple pseudo-elements | Flat surfaces; ripple removed |
| Segmented control / active segment | Gradient track + gradient active pill | `#f1f5f9` track, solid `#3b82f6` active |
| Maps L2 hero | Dark `#0f172a` panel, rainbow inline button colors | White card, `btn-mac` / `btn-mac-primary` tiles |
| Map status / util strip / overlay empty | Dark translucent panels | Light `#f8fafc` / `#fffbeb` enterprise panels |
| Discovery seed box | Purple tint `rgba(139,92,246,…)` | White card, `#e2e8f0` border |
| Progress bars (MAC/desc/ping/disc) | Multi-stop gradients | Solid operational colors |
| Stop scan button | Custom dark red inline | `btn-danger` |
| Credential settings heading | h5 with emoji | h2, no emoji |

## Map / report shells

| File | Change |
|------|--------|
| `utils/l3_map_shell.py` | Header gradient → flat `#1e293b`; title `#f1f5f9` |
| `utils/combined_l2l3_shell.py` | Same header flattening |
| `utils/output_chrome.py` | Report header gradient → flat `#1e293b` |

## Motion

- Added `@media (prefers-reduced-motion: reduce)` — disables transitions/transforms on buttons.

## Intentionally retained

- Subtle window-header rule gradient (decorative 1px divider — not a CTA surface).
- vPC legend semantic color chips (operational meaning, not decorative chrome).
- Dark operator chrome bar (`#0b1220`) — functional status strip, not a marketing hero.

## Visual verification

After screenshots: `screenshots/after/{inventory,maps,find,change,settings}.png`

Pre-cleanup visual baseline: see `docs/review_folder/2026.08.23/QA/enterprise_validation_rendering_and_ship_readiness/` (7.2.3 polish pass).
