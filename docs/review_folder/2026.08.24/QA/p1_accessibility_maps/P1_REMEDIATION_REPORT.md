# P1 accessibility + map HTML — 2026-08-24

**Scope (user-narrowed):** operator accessibility, heading order, contrast, map landmarks/lang/scroll.  
**Out of scope:** SSO, RBAC, multi-user identity, Zero Trust plugin-sandbox / credential-API security items.

**Roles:** ux-operator-analyst, topology-architect, test-engineer.  
**Skills:** `nst-orchestrator` → `accessibility-reviewer` + `topology-map-excellence` → `safe-refactor-and-fix` → `exhaustive-test-and-validate`.

## Result

| ID | Issue | Status |
|----|--------|--------|
| **B-05** (axe residual) | Automated axe on operator console + generated maps | **CLOSED as code residual** — 16 → **0** violations, **0 critical**. Not a WCAG/VPAT certification. |
| Heading-order (Find/Change/Maps/Settings) | `h5`/`h6` after workspace `h1` | **CLOSED** |
| Operator contrast (section titles, buttons, muted text, dark chrome) | AA fails on light panels and dark header | **CLOSED** for previously listed nodes |
| Map `lang` / `<main>` / scrollable region | Frozen Aug-23 fixtures | **CLOSED** on freshly generated shells |
| SSO / RBAC / multi-user | — | **REMOVED FROM SCOPE** (unchanged) |

## What changed

- Operator UI (`modules/web/templates/index.html`): workspace `h1` → tab `h2` → section `h3`; muted text `#475569`; primary buttons `#1d4ed8`; success `#047857`; dark chrome meta `#cbd5e1`.
- Legacy tab strip: `hidden inert` only (no stacked `tabindex` / `aria-hidden` on first paint).
- Confirm modals: closed state is `hidden inert` without first-paint `tabindex`.
- Map shells: Discovery light CC freshness/layer-switch tokens; Standard L2 already had `lang`, `<main>`, keyboard-focusable connection table.

## Gates (this folder)

| Gate | Result |
|------|--------|
| `_prebuild.py` | **READY TO BUILD** (`prebuild.log`) |
| `pytest` (full) | **1930 passed**, 1 skipped (`pytest_full2.log`) |
| `mandatory_release_qa.py --phase every_code_change` | **PASS** (`mandatory_qa2.log`) |
| `run_playwright_e2e.py` (6 specs + demo maps) | **PASS** (`playwright_e2e2.log`, `playwright/summary.json`) |
| axe `@axe-core/playwright` 9 pages | **0 violations** (`accessibility/after_sweep_summary.json`, `axe_after2.log`) |

## Honest verdict

P1 **operator-visible accessibility and map HTML structure** is closed with automated proof.

This is **not** WCAG 2.1 AA certification, not a screen-reader sign-off, and **does not** clear `release_gate` (still **BLOCKED** — live lab / vendor evidence). SSO and multi-user remain absent by product design.

See `REMAINING_GAPS.md` for axe **incomplete** (not counted as pass or fail).
