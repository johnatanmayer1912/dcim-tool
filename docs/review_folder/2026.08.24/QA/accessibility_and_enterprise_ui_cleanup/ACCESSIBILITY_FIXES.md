# Accessibility fixes applied — 2026-08-24

## Landmark & structure

- `#nst-main` promoted to `<main role="main">` (was `<div>`).
- Sidebar promoted to top-level `<aside aria-label="Scope and session">`.
- Parsed hosts panel changed from nested `<aside>` to `<div role="region" aria-label="Parsed inventory hosts">`.

## Forms & names

- `#target_mode` — `aria-labelledby="label-target-scope"` + visually hidden label.
- `#group_filter`, `#single_combo` — `aria-label` + visually hidden labels.
- `#disc-protocol`, `#disc-timeout` — `for` attributes on visible labels.
- `#import-file` — visually hidden label + `aria-label`.

## Contrast (operator chrome & copy)

- `#nst-freshness` — `#cbd5e1` on dark chrome.
- `#btn-chrome-stop` — `#fecaca` text/border on dark chrome.
- `.sidebar-about-label` / `.sidebar-brand-refined` — `#475569` on white sidebar.
- `.settings-label`, `.nst-hub .lede` — `#475569` for AA on light surfaces.

## Tooling added

- `tests/browser/accessibility_enterprise_sweep.spec.mjs` — workspace + map axe sweep.
- `@axe-core/playwright` dev dependency in `tests/browser/package.json`.
- `tests/test_a11y_enterprise_7_2_4.py` — static contracts for landmarks, labels, UI cleanup.

## Not fixed in this pass (see REMAINING_UI_A11Y_GAPS.md)

- Legacy tab panels still use `h5`/`h6` after workspace `h1` (heading-order moderate).
- Residual contrast inside Find/Change/Discovery colored section headers.
- Pre-generated map HTML fixtures (Aug-23) — require shell regeneration for `lang` / `main` / scrollable region fixes.
- `aria-prohibited-attr` on hidden legacy segment control (inert but present in DOM).
