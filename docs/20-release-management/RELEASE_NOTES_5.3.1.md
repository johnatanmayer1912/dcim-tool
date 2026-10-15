# Network Swiss Tool Pro - Release Notes v5.3.1

## Date: 2026-04-19

### 🚨 Critical Bugfix Release

This is a precision patch release targeting the root causes of the CLI terminal being completely non-functional.

---

### Root Cause Analysis

Five compounding bugs were discovered and fixed:

| # | Bug | Impact |
|---|---|---|
| 1 | `flask-socketio` was **not installed** | CLI terminal silently disabled for ALL users |
| 2 | `telnetlib_compat` shim not loaded before `netmiko` in `cli_manager.py` | `ImportError` crash on Python 3.13+ |
| 3 | `disabled_algorithms` for Paramiko 4.x **missing** from `cli_manager.py` | SSH rejected by legacy devices even after fix in `network_base.py` |
| 4 | `socket.io.min.js` loaded from CDN | Terminal broken in air-gapped/offline environments |
| 5 | `initSocket()` called on every connect attempt | Multiple redundant WebSocket connections stacking up |

---

### 🔧 Fixes Applied

- **`modules/cli_manager.py`** — Complete rewrite:
  - `telnetlib_compat` shim loaded at module top before any netmiko import
  - `disabled_algorithms` applied to all `ConnectHandler` calls
  - `read_timeout=30` on `send_command` for reliable output capture
  - Connection drop detection on command errors (reconnect prompt shown)
  - Prompt-based hostname resolution (works on all platforms)
  - Structured Python `logging` integration

- **`modules/web/templates/cli_terminal.html`** — UI fixes:
  - `socket.io.min.js` now served from local `static/js/` (offline safe)
  - `initSocket()` guarded with `if (!socket)` to prevent duplicate connections
  - Connecting progress message shown in terminal immediately
  - Error details displayed directly in xterm terminal output

- **`static/js/socket.io.min.js`** — Downloaded offline copy (v4.7.5)

- **`requirements.txt`** — Added all missing dependencies:
  - `flask-socketio>=5.3.0`
  - `python-engineio>=4.3.0`
  - `simple-websocket>=0.10.0`

- **`NetworkSwissToolPro_v5_3_1_Offline.spec`** — Updated build manifest with `socket.io.min.js`, `bidict`, `engineio.async_drivers.threading`
