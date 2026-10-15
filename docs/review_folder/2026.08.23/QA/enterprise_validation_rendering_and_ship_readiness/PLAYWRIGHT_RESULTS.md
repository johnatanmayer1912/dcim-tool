# Playwright results

**VERSION:** 7.2.2 · **Date:** 2026-08-23  
**Host:** Darwin CI-browser (Chromium via Playwright)  
**Not:** Windows EXE E2E · Not live device automation

## Runs

| Suite | Log | Result |
|---|---|---|
| Unified E2E (`run_playwright_e2e.py`) | `playwright/run_playwright_e2e.txt` | **PASS** |
| Offline map HTML (against this folder’s maps) | `playwright/offline_map_html.txt` | **PASS** |
| Operator screenshots (workspaces + maps + vPC demo) | `screenshots/` | Captured |

## Specs covered in unified E2E (excerpt)

- `cli_credential_id.spec.mjs` — credential_id only; no secret leakage; a11y names/focus  
- `operator_program_status.spec.mjs` — HARD STOP; `release_gate` BLOCKED; `may_claim_enterprise_ready` false  
- `operator_swiss_tools_overlay.spec.mjs` — overlay honesty; live SSH fail-closed  
- `operator_enterprise_shell.spec.mjs` — chrome, inventory, demoted Swiss Tools  
- `offline_map_html.spec.mjs` — Standard L2 + Discovery overlay contracts  
- `ux_demo_09_8vendor.spec.mjs` — 8-vendor demo honesty  

## Binding notes

Playwright runners require free **`:5051`** (ephemeral ports historically caused Werkzeug websocket 500 on Py3.14). Evidence logs show bind OK for this pass.

## Stability

Unified E2E completed green in this validation folder. No flake loop required after the recorded PASS. Screenshots re-taken after IM/VLAN polish with web restarted.

## Honesty

Playwright green ≠ EXE green ≠ live lab green.
