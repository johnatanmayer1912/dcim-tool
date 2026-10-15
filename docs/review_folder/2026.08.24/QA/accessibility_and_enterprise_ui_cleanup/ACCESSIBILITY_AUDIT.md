# Accessibility audit — 2026-08-24

**Scope:** Offline localhost operator console (`index.html`), six workspaces, Swiss Tools / Discovery panels, and frozen map HTML fixtures from enterprise validation (`standard_l2_overlay_replay.html`, `discovery_command_center.html`).

**Tooling:** `@axe-core/playwright` 4.10.1 — tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `best-practice`.

**Spec:** `tests/browser/accessibility_enterprise_sweep.spec.mjs`

## Sweep coverage

| Surface | States exercised |
|---------|------------------|
| Inventory | Default landing, parsed hosts table |
| Maps | Workspace + Swiss Tools (L2 hero) |
| Maps / Discovery | Discovery seed form, filters |
| Find | Network Search tab |
| Change | VLAN + Interface Manager tabs |
| Evidence | Program Status overview |
| Settings | Credentials + vault |
| Standard L2 map HTML | file:// replay overlay fixture |
| Discovery map HTML | file:// command center fixture |

## Results summary

| Phase | Pages | Total violations | Critical | Notes |
|-------|-------|------------------|----------|-------|
| Before (UI cleanup applied, pre-a11y patch) | 9 | **35** | 2 rules (`select-name`, `label`) | JSON: `accessibility/before_sweep_summary.json` |
| After (UI + a11y patch) | 9 | **16** | **0** | JSON: `accessibility/after_sweep_summary.json` |

**Inventory workspace:** 4 → **0** violations after patch.

## Issues found (representative)

### Operator console (before)

- **Critical:** `#target_mode`, `#group_filter` missing accessible names (all workspaces — sidebar always present).
- **Critical:** `#disc-protocol` label not associated; `#disc-timeout` label not associated; `#import-file` unlabeled.
- **Serious:** Chrome freshness line, Stop EXE button, sidebar About link, settings labels, workspace ledes — contrast on dark/light surfaces.
- **Moderate:** Nested `<aside>` for parsed hosts inside `<main>`; sidebar content not in top-level landmark; heading skips (h5/h6 after workspace h1).

### Generated map HTML (before + after — fixture age)

- Standard L2 fixture: missing `lang` on `<html>`, no `main` landmark, scrollable panel keyboard access, region containment.
- Discovery fixture: dark-map toolbar contrast, landmark structure.

### Incomplete (axe could not fully verify)

- `aria-prohibited-attr` on hidden/inert legacy segments (1–2 nodes).
- Additional `color-contrast` nodes inside complex tab panels (8+ incomplete on Inventory).

## Honesty

This is an **automated** sweep only. It does **not** certify WCAG 2.1 AA compliance, keyboard-only walkthrough of every mutation dialog, or screen-reader validation on live maps. Manual review of Interface Manager deploy modals and dynamic plugin forms remains out of scope for this pass.
