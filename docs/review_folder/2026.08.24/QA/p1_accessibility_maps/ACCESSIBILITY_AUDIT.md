# Accessibility audit (P1) — 2026-08-24

**Tooling:** `@axe-core/playwright` 4.10.x — tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `best-practice`.  
**Spec:** `tests/browser/accessibility_enterprise_sweep.spec.mjs`  
**Server:** `scripts/cli_browser_qa_server.py` on `127.0.0.1:5051`.  
**Maps:** freshly generated under `generated_outputs/maps/` (not the 2026-08-23 frozen fixtures).

## Coverage

| Surface | Notes |
|---------|--------|
| Inventory | Default landing |
| Maps | Swiss Tools |
| Maps / Discovery | Seed form |
| Find | Network Search |
| Change | VLAN / IM host |
| Evidence | Job index |
| Settings | Vault copy |
| Standard L2 HTML | `file://` replay overlay |
| Discovery Command Center | `file://` light CC |

## Sweep totals

| Phase | Pages | Violations | Critical |
|-------|-------|------------|----------|
| Prior cleanup (same day, 16 residual) | 9 | 16 | 0 |
| After P1 heading/contrast/map pass (`axe_after2.log`) | 9 | **0** | **0** |

Inventory, Find, Change, Evidence, Settings, Maps, Discovery, Standard L2, and Discovery CC: **0** definite violations.

## Closed classes

- `heading-order` — no `h5`/`h6` in `index.html`; tab titles `h2`, sections `h3`.
- `color-contrast` definite nodes — chrome version/vault/cred/scope (light-on-dark); muted body text; success/primary buttons; Discovery freshness and related-surface note.
- `html-has-lang`, `landmark-one-main`, `scrollable-region-focusable` on **current** Standard L2 generation.
- Discovery CC `landmark-one-main` / region wrappers from prior shell work, verified on regenerated HTML.

## Incomplete (axe could not decide)

Recorded in `after_sweep_summary.json`. Typical: 1 `aria-prohibited-attr` node and occasionally 1 `color-contrast` node per page. These are **not** counted as violations and are **not** claimed fixed. Likely hidden/inert dialog or overlay chrome axe cannot fully compute.

## Honesty

Automated sweep only. Does not certify keyboard-only mutation dialogs, VoiceOver/NVDA, or WCAG AA for every dynamic plugin form.
