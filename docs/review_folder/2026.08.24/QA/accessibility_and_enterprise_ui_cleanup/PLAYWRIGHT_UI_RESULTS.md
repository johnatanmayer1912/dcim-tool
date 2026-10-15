# Playwright / browser UI results — 2026-08-24

## Unified E2E (`scripts/run_playwright_e2e.py`)

**Verdict:** All browser specs **PASS**. Wrapper exited with `FileNotFoundError` writing `playwright/html/index.html` (missing directory — cosmetic report index only; specs themselves green).

| Spec | Result |
|------|--------|
| `cli_credential_id.spec.mjs` | PASS |
| `operator_program_status.spec.mjs` | PASS |
| `operator_swiss_tools_overlay.spec.mjs` | PASS |
| `operator_enterprise_shell.spec.mjs` | PASS |
| `offline_map_html.spec.mjs` | PASS |
| `ux_demo_09_8vendor.spec.mjs` | PASS |

Log: `playwright/unified_e2e.log`

## New accessibility sweep

| Command | Result |
|---------|--------|
| `node accessibility_enterprise_sweep.spec.mjs` (after) | 9 pages, 16 violations, **0 critical** |

Log: `accessibility/after_sweep_final.log`

## Pytest

```
tests/test_a11y_enterprise_7_2_4.py  — 13 passed
tests/test_polish_7_2_3.py         — 6 passed
Total: 19 passed
```

Log: `playwright/pytest_a11y_polish.log`

## Regressions observed

- None in Playwright operator contracts after UI/a11y changes.
- Maps lede honesty strings unchanged (replay / not SNMP).
- Swiss Tools overlay fail-closed behavior unchanged.

## Not run

- Full pytest suite (309+ tests) — out of scope for this focused pass.
- Windows EXE browser E2E.
- Live vendor device UI.
