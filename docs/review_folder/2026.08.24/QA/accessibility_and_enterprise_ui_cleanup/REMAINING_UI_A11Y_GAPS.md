# Remaining UI & accessibility gaps — 2026-08-24

## Accessibility (automated residual — 16 violations)

| ID | Impact | Where | Notes |
|----|--------|-------|-------|
| `heading-order` | Moderate | Find, Change, Maps, Settings tab panels | Legacy `h5`/`h6` section titles under workspace `h1`; needs systematic demotion to `h2`/`p.nst-section-title` |
| `color-contrast` | Serious | Find/Change/Discovery section headers | Colored h6 titles (`#92400e`, `#4338ca`, etc.) on white — some below 4.5:1 |
| `color-contrast` | Serious | Discovery map HTML (dark theme toolbar) | Fixture + dark map chrome — separate pass on `utils/discovery_map_shell.py` / `utils/topo_map_shell.py` |
| `html-has-lang` | Serious | Standard L2 **frozen** fixture | Regenerate from `utils/topo_map_shell.py` (already has `lang="en"` in source — stale fixture) |
| `landmark-one-main` | Moderate | Map HTML files | Add `<main>` wrapper in map shell templates; regenerate outputs |
| `region` | Moderate | Map HTML | Side panels / toolbars outside landmarks |
| `scrollable-region-focusable` | Serious | Standard L2 fixture | Scrollable legend/panel needs `tabindex="0"` in shell |

## axe incomplete (not counted as pass)

- Hidden legacy `.nst-legacy-segments` — `aria-prohibited-attr` on inert segment (low operator impact).
- 8+ contrast nodes inside collapsed/hidden tab content — manual spot-check advised.

## UI polish residual

| Item | Severity | Location |
|------|----------|----------|
| `report_formatter.py` gradient panels | P2 | Generated vPC / diagnostics HTML reports |
| `l3_map_shell_enhanced.py` dark hero gradients | P2 | Enhanced L3 shell (if enabled) |
| Tab `h5` titles with emoji (About, plugins) | P3 | Various tab-view headers |
| Window-header decorative gradient rule | P4 | Acceptable divider |

## Out of scope (unchanged blockers)

- Live lab / vendor validation — `release_gate` stays **BLOCKED**
- WCAG certification / VPAT
- SSO / RBAC
- Windows EXE UI E2E

## Recommended follow-up

1. Regenerate map fixtures after `topo_map_shell` landmark/lang/scroll fixes.
2. Batch-replace tab section `h6` → `h2` or styled `<p role="heading" aria-level="2">` with design tokens.
3. Normalize Find/Change section title colors to `#475569` / `#1e293b` only.
4. Run full `pytest` + `mandatory_release_qa.py --phase every_code_change` before VERSION bump.
