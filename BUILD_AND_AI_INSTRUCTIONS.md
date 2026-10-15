# Network Swiss Tool Pro — Build & AI Instructions
# Version 7.3.2 | Last updated 2026-09-03
# ─────────────────────────────────────────────────────────────────────────────
# THIS FILE IS THE AUTHORITATIVE PRE-BUILD AND AI-AGENT REFERENCE.
# Every AI IDE, CI runner, and human must follow this before touching the build.
# It is dummy-proof by design. Do not skip steps. Do not reorder steps.
# ─────────────────────────────────────────────────────────────────────────────

---

## 0. What this product is

**Network Swiss Tool Pro v7.3.2** is a 100% offline-first, single-file Windows EXE.

- Flask + Netmiko backend; vis.js topology maps; zero CDN dependencies.
- Users double-click `NetworkSwissToolPro_v7.3.2_OFFLINE.exe`. No Python required on the target machine.
- Default bind: `127.0.0.1:5051` — loopback only.
- Topology maps are standalone HTML files written to disk (no server required to view them).
- Source of truth for version: `VERSION` file. Ignore README banners.

---

## 1. Python version requirement

**Use Python 3.12.x exactly.**

This is the version the `.venv` is built against. PyInstaller produces stable single-file EXEs with Python 3.12.
Python 3.13+ changes the internal C API and causes PyInstaller boot failures.
Python 3.11 is acceptable but 3.12 is the validated target.

Verify before any build:

```
python --version   # Must print Python 3.12.x
```

If your system Python is different, create a venv with the correct version:

```
py -3.12 -m venv .venv
.venv\Scripts\activate
```

---

## 2. Setting up the virtual environment

```
# From the project root (same folder as vlan_checker_web.py)
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

All dependencies are pinned in `requirements.txt`. Do not upgrade without testing — netmiko, paramiko, and cryptography must be version-compatible.

---

## 3. Pre-build gate — MANDATORY before every build and every code change

Run this first. It catches import errors, broken module references, and test regressions:

```
python _prebuild.py
```

If `_prebuild.py` exits non-zero, **stop**. Fix the error. Do not run PyInstaller on a broken tree.

Then run the relevant tests:

```
# After any Python file change:
python -m pytest tests/ -q --tb=short

# After topology / map / parser changes:
python -m pytest tests/test_map_acceptance.py tests/test_topology_trust.py tests/test_network_discovery.py -q --tb=short

# Full pre-release gate:
python scripts/mandatory_release_qa.py
```

Tests must pass. The pytest-asyncio deprecation warning on stderr is noise — check the pass/fail count, not the exit code from stderr.

---

## 4. Building the EXE

```
.venv\Scripts\activate
python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.3.2.spec
```

Output: `dist\NetworkSwissToolPro_v7.3.2_OFFLINE.exe`

The spec file is `NetworkSwissToolPro_v7.3.2.spec`. It is a onefile build (`EXE` with no `COLLECT`). Do not change it to a one-folder build without updating the spec name and all frozen-path logic in the codebase.

**Do not run `build.py` instead of the spec.** `build.py` is a helper that copies plugins and QA files to `dist/`. Run it after PyInstaller if you need the sidecar:

```
python build.py
```

---

## 5. Offline integrity — mandatory checks before shipping any build

Every shipped EXE and every generated map HTML must be fully offline. These are non-negotiable:

### 5a. vis.js must be bundled — never fetched from CDN

The file `modules/web/vis-network.min.js` (vis-network v9.1.6, ~700 KB) is the only copy of vis.js used. It is inlined into every map HTML file at generation time by `utils/topo_map_shell.load_vis_script()`.

**Verify it exists before building:**

```
python -c "import os; p='modules/web/vis-network.min.js'; print('OK:', os.path.getsize(p), 'bytes') if os.path.exists(p) else print('MISSING - build will produce blank maps')"
```

Expected output: `OK: 701624 bytes` (or similar — must be > 500 000 bytes).

If missing, do NOT build. The EXE will produce blank topology maps silently.
Obtain vis-network.min.js v9.1.6 from the repo history or the vis-network npm package (offline copy).

### 5b. socket.io must be bundled

File: `static/js/socket.io.min.js` — Flask serves this for the operator UI. Must exist.

### 5c. No CDN references in any map output

The test `tests/test_map_acceptance.py` asserts this. Run it after any change to `utils/*_shell.py`:

```
python -m pytest tests/test_map_acceptance.py -q --tb=short
```

All 11 tests must pass.

### 5d. The `_cli_diagnostic_server.py` file contains a CDN reference

`_cli_diagnostic_server.py` line ~28 loads socket.io from `cdn.socket.io`. This file is a **developer-only diagnostic server on port 5052** and is **not bundled in the EXE** (not in `datas`, not in `hiddenimports`). It has no effect on the product. Do not "fix" it by adding it to the spec.

---

## 6. Map offline rendering — critical CSS rule

**This is the most important rule for AI agents touching map shell files.**

All topology map HTML files are standalone offline HTML. They are opened directly in a browser (`file:///...`). There is no Flask server involved when viewing them.

The layout uses:

```
body { display:flex; flex-direction:column; height:100vh; overflow:hidden; }
  └─ main.{map-class}  ← MUST have: display:flex; flex-direction:column; flex:1 1 0%; min-height:0; overflow:hidden;
       └─ .{map}-layout { display:flex; flex:1 1 0%; min-height:0; }
            └─ #{map}-network { flex:1; min-height:300px; position:relative; }
```

**The `<main>` element MUST have `flex:1 1 0%; min-height:0`.**
Without it, `height:100%` on the vis.js canvas resolves to 0px. vis.js draws to a zero-pixel container and the map appears empty. The data is present; only the rendering is broken. This bug is silent — the application reports "completed" correctly.

**Affected files and their main CSS class:**

| File | `<main>` class | Canvas ID |
|---|---|---|
| `utils/l3_map_shell.py` | `l3-map-main` | `#l3-network` |
| `utils/combined_l2l3_shell.py` | `combined-map-main` | `#combined-network` |
| `utils/l3_map_shell_enhanced.py` | (plain `main`) | `#l3-network` |

**Not affected** (use `calc(100vh - Npx)` which is chain-independent):

- `utils/discovery_map_shell.py`
- `utils/standard_map_shell.py`
- `utils/vpc_map_shell.py`

**Rule for AI agents:** Any time you add a new map shell file with `body { display:flex; flex-direction:column; height:100vh }`, you MUST add `display:flex; flex-direction:column; flex:1 1 0%; min-height:0; overflow:hidden` to every intermediate wrapper element between `body` and the vis.js container. Do not use `height:100%` on a flex child — use `flex:1 1 0%` instead.

**JS safety net** (already present in all three shells): If `container.offsetHeight < 10` at `vis.Network` init time, set `container.style.minHeight = '600px'`. This catches any future CSS regression.

---

## 7. Output paths — where map files are written

Maps are written to:

```
%USERPROFILE%\Documents\NetworkSwissToolPro\outputs\<category>\<YYYYMMDD>\<HHMMSS_slug>\report.html
```

Override with the `NST_DATA_DIR` environment variable (useful for USB/jump-host deployments):

```
set NST_DATA_DIR=D:\NST_Data
```

The EXE dir is never used for writes. Maps are self-contained HTML — copy the `.html` file to any machine, open in any browser, no server needed.

---

## 8. Deploying to an offline environment

### What to copy

You need ONE file:

```
dist\NetworkSwissToolPro_v7.3.2_OFFLINE.exe   (~50-80 MB, everything bundled)
```

Optional sidecar (created by `build.py`):

```
dist\plugins\        ← hot-reload plugins; EXE works without this
dist\inventory\      ← device inventory files
```

### What you do NOT need to copy

- No Python installation on the target
- No `dist\` folder — it is a onefile EXE
- No `node_modules`, `npm`, `yarn`, or any JS toolchain
- No internet connection at any point

### Air-gap validation checklist

Before declaring a build air-gap ready:

1. `python -m pytest tests/test_map_acceptance.py -q` → all pass (no CDN refs in maps)
2. `python _prebuild.py` → exits 0
3. Open a generated map HTML in a browser with network disconnected → nodes and edges visible
4. Confirm `modules/web/vis-network.min.js` exists and is > 500 KB
5. Confirm `static/js/socket.io.min.js` exists
6. Run `python scripts/mandatory_release_qa.py` → check for PASS/FAIL (not exit code)

---

## 9. Architecture rules for AI agents

Read these before making any code change.

### Never do

- Add CDN URLs (`cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com`, `fonts.googleapis.com`, etc.) to any Python file, HTML template, or generated map output.
- Change `modules/web/vis-network.min.js` to a CDN `<script src>` tag.
- Change the default bind from `127.0.0.1` to `0.0.0.0` without explicit security design and user confirmation.
- Add `height:100%` to a vis.js canvas container inside a flex layout without ensuring every ancestor up to `<body>` has an explicit height or `flex:1`.
- Add imports of `os.system`, `eval`, or `exec` in any plugin file.
- Add tkinter (`vlan_checker_gui.py`) features. That file is legacy and out of scope.
- Remove or weaken `utils/api_security.py` guards on credential/plugin/shutdown routes.
- Log passwords, enable secrets, SNMP communities, or vault keys anywhere.

### Required on every behavior change

1. Run `python _prebuild.py` — must exit 0.
2. Run `python -m pytest tests/ -q --tb=short` — must pass.
3. Add or extend a test in `tests/` or `tests/qa/` for the changed behavior.
4. Add a CHANGELOG entry in `CHANGELOG.md` (why the change, what it fixes).
5. For topology/map changes: add a test in `tests/test_map_acceptance.py` or the relevant fixture file.
6. For security-relevant changes: ADR entry in `.cursor/audits/decisions-log.md`.

### Product anchors (do not rename or move without updating all callers)

| Concern | File |
|---|---|
| Web API | `vlan_checker_web.py` |
| Operator UI | `modules/web/templates/index.html` |
| vis.js (offline) | `modules/web/vis-network.min.js` |
| L3 map HTML | `utils/l3_map_shell.py`, `utils/l3_map_shell_enhanced.py` |
| Combined map HTML | `utils/combined_l2l3_shell.py` |
| L2 discovery map HTML | `utils/discovery_map_shell.py` |
| Standard L2 map HTML | `utils/standard_map_shell.py` |
| vis.js loader | `utils/topo_map_shell.load_vis_script()` |
| Output paths | `utils/output_paths.py` |
| API security | `utils/api_security.py` |
| Credential vault | `modules/credential_manager.py` |
| L3 topology runner | `modules/l3_topology_runner.py` |
| L3 graph builder | `modules/routing_analyzer/` |

---

## 10. Known issues and do-not-fix items

| Item | Status | Note |
|---|---|---|
| Unsigned EXE (`B-SIGN-01`) | Open blocker | Controlled pilot only; do not auto-sign |
| `_cli_diagnostic_server.py` CDN ref | Won't fix | Dev-only, not in EXE |
| `vlan_checker_gui.py` (Tk) | Frozen | No new features; gap G-014 closed by design |
| `release_gate` BLOCKED | Open | Requires live vendor validation by a human |
| pytest-asyncio deprecation warning | Noise | Not a test failure; ignore exit code from stderr |

---

## 11. Quick reference — commands

```
# Setup
py -3.12 -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt

# Pre-build check
python _prebuild.py

# Tests
python -m pytest tests/ -q --tb=short
python -m pytest tests/test_map_acceptance.py -q       # offline map integrity
python -m pytest tests/test_topology_trust.py tests/test_network_discovery.py -q

# Build
python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.3.2.spec
python build.py   # copy plugins/QA files to dist/

# Run (dev mode, not EXE)
python vlan_checker_web.py web

# Full QA gate
python scripts/mandatory_release_qa.py
```

---

*End of BUILD_AND_AI_INSTRUCTIONS.md*
