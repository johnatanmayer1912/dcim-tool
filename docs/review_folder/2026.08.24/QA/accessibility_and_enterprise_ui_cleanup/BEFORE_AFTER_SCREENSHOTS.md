# Before / after screenshots — 2026-08-24

## After (this pass)

Captured post-cleanup at 1440×900 (Playwright headless):

| File | Description |
|------|-------------|
| `screenshots/after/inventory.png` | Inventory workspace + parsed hosts |
| `screenshots/after/maps.png` | Maps → Swiss Tools, light L2 hero card |
| `screenshots/after/find.png` | Find / Network Search |
| `screenshots/after/change.png` | Change workspace |
| `screenshots/after/settings.png` | Settings / credentials |
| `screenshots/after/map_standard_l2.png` | Standard L2 map fixture (axe sweep) |
| `screenshots/after/map_discovery.png` | Discovery map fixture (axe sweep) |
| `screenshots/after/maps_discovery.png` | Discovery tab in operator UI |

## Before

True pre-cleanup screenshots were **not** captured in-repo (no git baseline available in this workspace). Visual before state for gradients/rainbow Maps hero is documented in:

`docs/review_folder/2026.08.23/QA/enterprise_validation_rendering_and_ship_readiness/UI_UX_REVIEW.md`

Axe **before** JSON (UI cleanup already applied, pre-a11y label patch): `accessibility/before_sweep_summary.json` — 35 violations.

Axe **after** JSON: `accessibility/after_sweep_summary.json` — 16 violations.

## Meaningful visual deltas (described)

1. **Maps Swiss Tools** — dark hero with cyan/orange/green/purple buttons → white card with standard blue/gray buttons.
2. **All primary actions** — gradient buttons → flat enterprise buttons across Inventory, Find, Change, Settings.
3. **Discovery seeds** — purple-tinted panel → neutral white card.
4. **Progress bars** — gradient fills → solid fills.
