# Network Swiss Tool Pro

Offline-first **web** operator console (Flask + browser at `127.0.0.1:5051`). Tkinter desktop GUI is **out of scope**.

**Made by AI IDE**

## Quick Start

| Edition | Executable | How it works |
|---------|-----------|--------------|
| **Web (supported)** | `dist/NetworkSwissToolPro_v7.0.87_OFFLINE.exe` (build from `VERSION` 7.0.87) | Starts Flask, opens browser at `http://127.0.0.1:5051` |

**Prerequisites:** Place an `inventory.txt` in the same directory as the `.exe`.

## Inventory Format

```
# Lines starting with # are comments
# Format: IP,device_type[,group]

[CoreSwitches]
10.1.1.1,cisco_ios,CoreSwitches
10.1.1.2,cisco_ios,CoreSwitches

[AccessLayer]
10.2.1.1,cisco_ios,AccessLayer
10.3.1.1,juniper_junos,AccessLayer
```

- **GUI** uses `[GroupName]` headers OR 3rd CSV column for grouping
- **Web** uses `[GroupName]` headers OR 3rd CSV column for grouping (Added v2.5)
- Supported device types: `cisco_ios`, `cisco_nxos`, `cisco_xe`, `juniper_junos`

## Features

### 🔍 Diagnostics & Health
| Feature | Description | Output |
|---------|-------------|--------|
| Connectivity Check | ICMP Ping + SSH Auth test per device | Log output |
| VLAN Audit | Pulls VLAN database from each switch | Raw + Parsed report files |
| MAC Trace | Searches CAM/MAC tables for a specific MAC | Log output with VLAN/Interface |

### 🔌 Interface Management
| Feature | Description | Output |
|---------|-------------|--------|
| Interface Status | `show interfaces status` / `show interfaces terse` | Report file |
| Interface Description | `show interfaces description` | Report file |
| Custom Filters | Presets (connected, notconnect, etc.) or custom regex | Filtered output |

### 🏷️ VLAN Provisioning
| Feature | Description | Safety |
|---------|-------------|--------|
| Add VLAN | Creates VLAN with ID and Name | Checks if exists first |
| Rename VLAN | Changes VLAN name | Confirmation dialog |
| Delete VLAN | Removes VLAN from config | ⚠️ Warning + confirmation |
| Save Config | Persists active config to startup/commit | Works with Single/Bulk/Group scope |

### 📊 VLAN Compare
Automatically identifies a "golden baseline" (union of all VLANs across devices) and generates a report showing which VLANs are missing on each switch. Forces Bulk mode.

### 🛠️ Swiss Tools
| Feature | Description | Output |
|---------|-------------|--------|
| Topology Mapper | CDP/LLDP neighbor discovery → interactive Vis.js diagram | `topology_map_*.html` |
| Network Audit | Extracts Hostname, OS, Serial, Model, Uptime | `network_audit_*.csv` |
| Config Backup | Bulk `show running-config` with optional filter | `config_backups_*/` folder |

### 🎯 Target Scope Engine
- **Bulk Mode**: All devices, optionally filtered by Group or text search
- **Single Device**: Target exactly one device from a dropdown
- **Group Filter**: Filter by inventory group (3rd column or `[Header]`)

## Architecture

**Supported operator UI is web only.** Tkinter (`vlan_checker_gui.py`) is out of scope. The architecture box and GUI build script below are historical.

```
┌─────────────────────────────┐    ┌──────────────────────────────┐
│  VlanCheckerGUI.exe         │    │  VlanCheckerWeb.exe          │
│  (Tkinter Desktop)          │    │  (Flask + HTML/JS Frontend)  │
│                             │    │                              │
│  vlan_checker_gui.py        │    │  vlan_checker_web.py         │
│  ├─ UI: Tkinter Notebook    │    │  ├─ Backend: Flask API       │
│  ├─ Threads: per-operation  │    │  ├─ Frontend: index.html     │
│  ├─ Logging: Queue + File   │    │  ├─ Logging: Queue + File   │
│  └─ Netmiko SSH engine      │    │  └─ Netmiko SSH engine      │
└─────────────────────────────┘    └──────────────────────────────┘
```

Both editions share identical Netmiko logic and produce identical output files.

## Logging

Every session creates a persistent log file: `app_session_log_YYYYMMDD_HHMMSS.txt`

- **GUI**: Thread-safe Queue → Tkinter ScrolledText + file write
- **Web**: Python list → polled via `/api/logs` endpoint + file write

## Build Instructions

```bash
# Supported: Web Edition
build_web_exe.bat

# Historical Desktop GUI (out of scope — do not ship as the operator UI)
build_exe.bat
```

Both scripts use PyInstaller to create standalone `.exe` files in `dist/`.

## Version History

### v6.9.28 — 2026-05-31 (Current)
**Discovery + Templates**
- **[FIX]** BUG-0006: NX-OS discovery hostname (banner no longer used as label).
- **[NEW]** Discovery link inventory map + static topology (offline).
- **[NEW]** Config template presets (trunk, Po, vPC) + web builder.
- **Artifact:** `dist/NetworkSwissToolPro_v6.9.28_OFFLINE.exe` — see [RELEASE_NOTES_6.9.28.md](RELEASE_NOTES_6.9.28.md).

### v6.9.27 — 2026-05-31
**vPC Engineering Board**
- **[NEW]** vPC map opens on offline Engineering Board (tables) + Simplified Map tab.
- **[FIX]** NX-OS peer/keepalive parsing; `port_channels` in payload; global consistency in board/panel.
- **Artifact:** `dist/NetworkSwissToolPro_v6.9.27_OFFLINE.exe` — see [RELEASE_NOTES_6.9.27.md](RELEASE_NOTES_6.9.27.md).

### v6.9.26 — 2026-05-31
**Bug sweep fixes**
- **[FIX]** Discovery job status matches plugin outcome (BUG-0002).
- **[FIX]** Discovery job store capped at 50 entries (BUG-0005).
- **[FIX]** Documentation version sync (BUG-0001).
- **Artifact:** `dist/NetworkSwissToolPro_v6.9.26_OFFLINE.exe` — see [RELEASE_NOTES_6.9.26.md](RELEASE_NOTES_6.9.26.md).

### v6.9.25 — 2026-05-31
**Discovery live-crawl fix**
- **[FIX]** Network Discovery on single/multi seed: `not enough values to unpack (expected 3, got 2)`.
- **Artifact:** `dist/NetworkSwissToolPro_v6.9.25_OFFLINE.exe` — see [RELEASE_NOTES_6.9.25.md](RELEASE_NOTES_6.9.25.md).

### v3.1 — 2026-02-26
**Topology Sanitization & Infographic UX**
- **[NEW]** Node Blacklist: Automatically filters out non-hostname strings (e.g., `password`, `login`, `username`) from the topology map.
- **[NEW]** Premium Node Dashboards: Redesigned infographic popups with status icons (✅/❌), connection summaries (Active/Total), and improved typography.
- **[FIX]** Prompt Sanitization: Hardened hostname extraction to strip trailing punctuation (`#`, `>`, `:`) ensuring clean node labels.
- **[NEW]** Multi-Link Grouping: Improved table layout for nodes with multiple logical and physical connections.

### v4.5.1 — 2026-04-13
**Change Safety & Verification Controls**
- **[NEW]** VLAN Dry-Run: Add/Rename/Delete VLAN workflows now support simulation mode to preview CLI command plans with zero device mutation.
- **[NEW]** Pre-Change Snapshot: Automatic per-device VLAN configuration snapshot is captured before every mutating VLAN workflow.
- **[NEW]** Post-Change Verification: Live VLAN changes now validate resulting device state and log verified outcomes for operator confidence.

### v4.4 — 2026-04-13
**Configuration Persistence & Operational Logging**
- **[NEW]** Save Config Action: Added explicit `Save Device Config` operation in GUI and Web with full scope support (Single/Bulk/Group).
- **[NEW]** VLAN Config-State Logging: VLAN add/rename/delete now logs whether changes are persisted (`commit`) or running-only (`startup save required`).
- **[FIX]** Web Template Loading: Web app now resolves templates from `modules/web/templates` in development mode and bundles correctly for PyInstaller.

### v3.0 — 2026-02-26
**Juniper & Cisco Command Refined**
**Robust Interface Metadata Parsing**
**Infographic Topology & Dual-View**
**vPC & Enhanced Topology Mapping**
**Topology & UX Overhaul**

### v2.5 — 2026-02-26
**Web Focused Enhancements**

### v2.4 — 2026-02-26
**Code Audit & Documentation Release**
- Full code review of both editions (2230 combined lines)
- Created `QA_TESTING_CHECKLIST.txt` for manual testing
- Created `README.md` with architecture, features, and version history
- Removed duplicate `import os` in web backend

### v2.3 — 2026-02-26
**Session 4 Bug Fixes**
- **[FIX]** Added Group dropdown filter to Web UI (parity with Desktop)
- **[FIX]** Restored missing `connectivity`, `vlan_check`, `mac_check` in web thread router
- **[FIX]** Fixed stale variable references (`enb`→`enb_pwd`, `d`→`data`) in web API handler
- **[FIX]** Fixed `NameError: unique_nodes` in GUI topology mapper (should be `uniq_nodes`)
- **[FIX]** Fixed web topology: `uniq_nodes` was overwritten with empty `set()` after population

### v2.2 — 2026-02-26
**Session 3 Bug Fixes**
- **[FIX]** Flask template routing for PyInstaller bundles (`sys._MEIPASS`)
- **[FIX]** CSV audit now uses `conn.find_prompt()` for real hostname extraction
- **[FIX]** Full regex parsing for OS Version, Serial Number, Model in web audit
- **[FIX]** Topology mapper injects target node regardless of CDP/LLDP response

### v2.1 — 2026-02-25
**Web UI Overhaul**
- MacOS-inspired glassmorphism design (Inter font, segmented controls, dark console)
- Complete feature parity: all 11 actions available in web edition
- Target Scope Engine with Bulk/Single/Group/Text filtering
- VLAN Compare, Interfaces tab, Config Backup added to web

### v2.0 — 2026-02-25
**Web Edition Created**
- Flask-based web application with HTML/JS frontend
- Separate PyInstaller build (`VlanCheckerWeb.exe`)
- Auto-launches browser on startup
- Session file logging

### v1.9 — 2026-02-08
**Desktop Enhancements**
- Topology Mapper with Vis.js interactive physics diagrams
- Network Audit exporting to CSV
- `safe_node_name()` for IP/hostname deduplication
- VLAN Compare Analysis with global baseline

### v1.8 — 2026-02-01
**VLAN Operations**
- Add/Rename/Delete VLAN with pre-check and confirmation dialogs
- Cisco config save and Juniper commit after changes
- Detailed per-device logging for all CRUD operations

### v1.7 — 2026-02-01
**Foundation**
- Connectivity & Authentication checker
- VLAN database audit with raw + parsed reports
- MAC Address tracer across network
- Group-based inventory filtering
- Enable Password support for Cisco IOS privilege escalation
- Thread-safe GUI with Queue-based logging

## Regression Safety

All future changes MUST verify the regression checks in `QA_TESTING_CHECKLIST.txt` Section C.
These cover all previously fixed bugs and MUST NOT be reintroduced.

## Files

| File | Purpose |
|------|---------|
| `vlan_checker_gui.py` | Legacy Tk source (out of scope) |
| `vlan_checker_web.py` | Web backend source (Flask) |
| `templates/index.html` | Web frontend (HTML/CSS/JS) |
| `inventory.txt` | Device inventory (user-maintained) |
| `build_exe.bat` | PyInstaller build script for GUI |
| `build_web_exe.bat` | PyInstaller build script for Web |
| `QA_TESTING_CHECKLIST.txt` | Manual testing checklist |
| `README.md` | This file |
