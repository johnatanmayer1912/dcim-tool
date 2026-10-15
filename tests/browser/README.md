# CLI / operator browser QA (Node Playwright)

**Do not use Python Playwright** (unsupported on some hosts; greenlet/Python 3.14).

This is **CI-browser**. It is **not** in the PyInstaller EXE and is **not** live-vendor or EXE E2E.

## Supported commands (repo root)

```bash
python3 scripts/run_cli_browser_qa.py
python3 scripts/run_operator_browser_qa.py
python3 scripts/run_offline_map_html_qa.py
python3 scripts/run_playwright_e2e.py
python3 scripts/run_ux_demo_qa.py
```

`run_cli_browser_qa.py` / `run_operator_browser_qa.py`: Node/npm → `npm ci` → `playwright install chromium` → mocked QA server → specs → teardown.

`run_offline_map_html_qa.py`: generates fixture Standard L2 + Discovery HTML, then `offline_map_html.spec.mjs` over `file://`.

`run_playwright_e2e.py`: all of the above. Set `NST_REVIEW_DIR` to copy logs/traces/screenshots.

## Manual split

```bash
cd tests/browser && npm ci && npx playwright install chromium
NST_CLI_BROWSER_QA_PORT=5051 BROWSER=/usr/bin/true python3 scripts/cli_browser_qa_server.py
# other terminal:
NST_BROWSER_BASE=http://127.0.0.1:5051 node cli_credential_id.spec.mjs
NST_BROWSER_BASE=http://127.0.0.1:5051 node operator_program_status.spec.mjs
NST_BROWSER_BASE=http://127.0.0.1:5051 node operator_swiss_tools_overlay.spec.mjs
```

Pinned: `playwright@1.49.1` (`package-lock.json`). `node_modules/` is gitignored.

## Operator console

`run_operator_browser_qa.py` runs:

- `operator_program_status.spec.mjs` — workspaces, Discovery Program Status, HARD STOP, related-surface jumps
- `operator_swiss_tools_overlay.spec.mjs` — Maps lede honesty; Live SSH without `credential_id` fails closed; overlay status does not clear `release_gate`

`run_ux_demo_qa.py` exercises `docs/11-ux/demos/09-offline-8vendor-lab.html` over `file://` (fixture lab buttons; not live-vendor).
