# Network Swiss Tool Pro

Offline-first **web** operator console for Cisco IOS/IOS-XE/NX-OS and Juniper Junos. Flask + Netmiko, typical bind `127.0.0.1:5051`. Frozen as a PyInstaller EXE.

The supported operator UI is **web only**. Tkinter (`vlan_checker_gui.py`) is out of scope.

**Made by AI IDE**

## Quick Start

| Edition | Executable | How it works |
|---------|-----------|--------------|
| **Web (supported)** | `dist/NetworkSwissToolPro_v7.4.18_OFFLINE.exe` | Starts Flask, opens browser at `http://127.0.0.1:5051` |

**Prerequisites:** Place an `inventory.txt` in the same directory as the `.exe`.

## 📚 Documentation
The project documentation is organized under the **LIBRARIAN v1.0** mandate:
- [Project Overview](docs/00-overview/project-overview.md)
- [Quick Walkthrough](docs/00-overview/walkthrough.md)
- [System Architecture](docs/01-architecture/system-architecture.md)
- [Operational Workflows](docs/07-operations/operational-workflows.md)
- [Rebuild Procedure](docs/06-build-rebuild/exact-rebuild-procedure.md)
- [Troubleshooting Index](docs/07-operations/TS_ERROR_INDEX.md)

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

- Inventory grouping: `[GroupName]` headers OR 3rd CSV column
- Supported device types: `cisco_ios`, `cisco_nxos`, `cisco_xe`, `juniper_junos`

## Features

### 🔍 Diagnostics & Health
| Feature | Description | Output |
|---------|-------------|--------|
| Connectivity Check | ICMP Ping + SSH Auth test per device | Log output |
| VLAN Audit | Pulls VLAN database from each switch | Raw + Parsed report files |
| MAC Trace | Searches CAM/MAC tables for a specific MAC | Log output with VLAN/Interface |
| Health Check | Comprehensive system validation | Health report with status |

### 🔌 Interface Management
| Feature | Description | Output |
|---------|-------------|--------|
| Interface Status | `show interfaces status` / `show interfaces terse` | Report file |
| Interface Description | `show interfaces description` | Report file |
| Custom Filters | Presets (connected, notconnect, etc.) or custom regex | Filtered output |
| Interface Map | Visual interface topology with status indicators | Interactive map |

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
| Network Discovery | CDP/LLDP neighbor discovery → interactive Vis.js diagram | `topology_map_*.html` |
| Network Audit | Extracts Hostname, OS, Serial, Model, Uptime | `network_audit_*.csv` |
| Config Backup | Bulk `show running-config` with optional filter | `config_backups_*/` folder |
| vPC Domain Analysis | Comprehensive vPC domain analysis with 10 verification checks | `vpc_domain_*.txt` |
| STP Topology | Spanning Tree topology visualization | `stp_map_*.html` |
| **Cisco Asset & Warranty** | **Asset inventory with EOL/EOS enrichment** | **HTML + CSV reports** |

### 🔬 Cisco Asset & Warranty Plugin
**NEW in v7.4.14** - Comprehensive Cisco lifecycle management with official EoX data.

**Features:**
- **Asset Collection**: Gathers hostname, PID, serial number, software version from Cisco devices
- **EOL/EOS Enrichment**: Automatically enriches assets with official Cisco End-of-Life and End-of-Support dates
- **Warranty Status Calculation**: Calculates warranty status (Active, Expired, Expiring Soon, Unknown) based on EOL/EOS dates
- **Interactive Catalog**: Click any PID to open the full Cisco EOL/EOS model catalog (114+ models)
- **Comprehensive Database**: Includes complete families:
  - Catalyst 3850 Series (32 models with official EOL dates)
  - Catalyst 2960-X Series (10 models)
  - Catalyst 2960-S Series (10 models)
  - Catalyst 2960 Series (6 models)
  - Catalyst 9000 Series (11 models)
  - Nexus 9000 Series (15+ models)
  - ISR/ASR Routers (9 models)

**Warranty Status Logic:**
- **Active**: Model is in database with no EOL/EOS dates (current product)
- **Expired**: End-of-Support date has passed
- **Expiring Soon**: End-of-Support within 1 year
- **Unknown**: Model not found in database

**Report Format:**
- **HTML**: Interactive table with clickable PIDs, warranty status badges, EOL/EOS columns, and searchable modal catalog
- **CSV**: Comma-separated export with all enrichment fields for spreadsheet analysis

### 🎯 Target Scope Engine
- **Bulk Mode**: All devices, optionally filtered by Group or text search
- **Single Device**: Target exactly one device from a dropdown
- **Group Filter**: Filter by inventory group (3rd column or `[Header]`)

### 🔐 Security & Offline Support
- **Credential Management**: Fernet encryption for offline environments
- **Multiple Credentials**: Support for multiple credential sets with deduplication
- **Export/Import**: Credential migration between versions
- **Demo Mode**: Offline validation without real devices

## Architecture

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
# Build Desktop GUI
build_exe.bat

# Build Web Edition
build_web_exe.bat
```

Both scripts use PyInstaller to create standalone `.exe` files in `dist/`.

## Version History

### v7.4.14 — 2026-09-07 (Current)
**Cisco EOL Database Expansion & Enrichment Fix**
- **[FIX]** Cisco EOL enrichment: Models in database with no EOL dates now show 'active' instead of 'unknown'
- **[ADDED]** Complete Catalyst 3850 family (32 models) with official EOL dates from Cisco EoX announcement
- **[ADDED]** Extended Catalyst 2960-X family (10 models) with complete coverage
- **[ADDED]** Extended Catalyst 2960-S family (10 models) with complete coverage
- **[ADDED]** Updated N9K-C9348GC-FXP with official EOL data (EOL: 2020-08-31, EOS: 2021-03-01)
- **[CHANGED]** Database now contains 114 Cisco models (up from 82)
- **[CHANGED]** Warranty status calculation logic distinguishes between active products (no EOL) and unknown models (not in database)
- **[UPDATED]** Documentation: Added Cisco Asset & Warranty Plugin section to README with feature details and warranty status logic

### v7.4.13 — 2026-09-07
**Credential Recognition Debug Build**
- **[ADDED]** Debug logging to nstRequireTaskCredentials() to track credential values
- **[ADDED]** Debug logging to onSidebarCredChange() to track credential selection
- **[CHANGED]** Greyed out secondary and third credential dropdowns in sidebar
- **[CHANGED]** Updated version to 7.4.13 for credential debug build
**Enterprise Bug-Fix Release — Full QA Green**
- **[FIX]** BUG-0009: Junos `Physical interface: xe-0/0/0, Enabled, Physical link is Up` same-line status parsing
- **[FIX]** BUG-0010: All 146 pytest tests pass (LLDP brief/detail, NX-OS interfaces, merge by serial/IP, HTML contracts)
- **[FIX]** NEW-H5: Junos LLDP local port — safe `xe-`/`ge-` header extraction (no bare `:` capture)
- **[FIX]** NEW-C1: Frozen EXE uses bundled `_MEIPASS` plugins when install dir is read-only
- **[FIX]** NEW-M2: `merge_nodes` unions devices sharing serial number across hostnames
- **[QA]** Pre-build gate PASS · pytest **146/146** · CLI smoke 11/11

### v7.0.28 — 2026-06-10
**MAC Trace & Juniper Interface Map Fixes**
- **[FIX]** MAC Address Search (web): IOS-XE Catalyst L3 switches now normalize colon/dash MAC input to Cisco dotted format (`0011.2233.4455`) before `show mac address-table | include` — fixes false "not found" when manual CLI search worked.
- **[FIX]** Juniper MAC trace (EX/QFX, Junos 14+): Multi-syntax search (`ethernet-switching table`, `mac-ip-table`, legacy `bridge mac-table`) with colon-format match tokens; improved VLAN/port parsing for `xe-`/`ge-`/`ae0.0` interfaces.
- **[FIX]** Juniper Interface Map: Physical↔logical correlation — ae bundles discovered via LACP, members linked to `ae0`, map UI shows bundle hierarchy with member lists.
- **[ADDED]** `utils/mac_utils.py`, `utils/juniper_iface.py` — shared normalization; regression tests in `tests/test_mac_trace_parsing.py`.

### v7.0.27 — 2026-06-07
**Critical JUNOS LLDP Discovery Fix**
- **[FIX]** JUNOS LLDP discovery: Fixed discovery failure on older Junos versions by changing command order to try 'show lldp neighbors' (brief) first, then 'show lldp neighbors detail' if needed. Research from Juniper documentation confirmed that some versions only support the brief format.
- **[CHANGED]** network_discovery plugin v1.8.0 — Changed LLDP command order for Juniper devices for compatibility
- **[ADDED]** Deep dive enhancements: Parser regression testing, offline validation, duplicate device detection for VPC, user error prevention documentation

### v7.0.26 — 2026-06-07
**JUNOS LLDP and Interface Fixes**
- **[FIX]** JUNOS LLDP discovery: Fixed 0 links found issue with table format parser for xe- interfaces, added comprehensive 4-tier fallback (standard→brief→table→alternative), fixed interface status unknown issue with Physical link Up/Down detection, improved xe- interface support across all parsers
- **[FIX]** Interface Manager: Fixed JUNOS interface status detection with Physical link Up/Down patterns, enhanced status parsing for all Junos interface types
- **[CHANGED]** network_discovery plugin v1.6.0 — Added _parse_juniper_lldp_table function, enhanced fallback chain
- **[CHANGED]** interface_manager plugin v1.0.14 — Enhanced Junos interface status detection

### v7.0.25 — 2026-06-04
**JUNOS LLDP Discovery Fix**
- **[FIX]** JUNOS LLDP discovery: Fixed 0 devices scanned issue with multi-pattern parsing, added fallback mechanisms for older Junos 13.X versions, added brief format fallback, added alternative parsing for non-standard output, improved error handling and logging for troubleshooting
- **[CHANGED]** network_discovery plugin v1.5.0 — Enhanced _parse_juniper_lldp_detail with multi-pattern parsing

### v7.0.24 — 2026-06-03
**Interface Discovery Enhancements**
- **[FIX]** Interface discovery: Fixed Junos 13.X discovery failure with multi-pattern parsing and fallback mechanisms, added IOS older version support with fallback parsing, added NXOS older version support with fallback parsing, improved error handling for rendering issues on older devices
- **[CHANGED]** interface_manager plugin v1.0.14 — Enhanced interface discovery with fallback mechanisms

### v7.0.10 — 2026-05-31
**Discovery NX-OS LLDP Link Parsing Fixes**
- **[FIX]** Discovery NX-OS LLDP links: Parsers now handle `Local Port id` (not only `Local Intf`), `System Name: not advertised`, blocks without system name (chassis/MAC identity), and `Port id` carrying a MAC when `Port Description` has the real interface. Neighbor dedupe prefers detail over brief; link inventory shows `n/a` instead of JSON `null` for missing remote ports.
- **[CHANGED]** network_discovery plugin v1.4.0 — `_finalize_neighbor`, `_dedupe_neighbors`, improved `_parse_cisco_lldp_detail` / brief.

### v7.0.9 — 2026-05-31
**Sidebar Branding & UI Polish**
- **[NEW]** Sidebar branding (UX refined): Logo, product name, version pill, short Updated date (full string in tooltip), Made by AI IDE — top of sidebar; click opens About & Help.
- **[NEW]** UI polish: Chrome header bar, refined tab strip, accent content cards, monospace SYS · Task Logs console header.
- **[NEW]** Docs: network-search-workflow.md, network-search-reports-guide.md; librarian audit LIBRARIAN_AUDIT_v7.0.9.md.
- **[CHANGED]** Network Search tab (renamed from search_it in UI); internal APIs unchanged.
- **[CHANGED]** Header: Title, version, date, and branding removed from top bar (moved to sidebar).
- **[REMOVED]** Mid-sidebar logo block (v7.0.8 placement between filters and Import).

### v7.0.8 — 2026-05-31
**Sidebar Brand Logo & Topology Fixes**
- **[NEW]** Sidebar brand logo: App icon shown in Target Scope (above Import/Browse) on a synced light card + dark icon plate. Updated favicon asset.
- **[REMOVED]** Center workspace watermark (replaced by sidebar logo placement).
- **[FIX]** Topology HTML map not rendering: Container id was `mynetwork-legacy` while vis.js targeted `#mynetwork` — maps now attach correctly.
- **[FIX]** Topology default view: Standard CDP/LLDP maps open on Topology Map (not hidden behind Link Inventory). vPC Command Center unchanged (Overview map pane).

### v7.0.7 — 2026-05-24
**search_it Live Progress & Tab Refresh**
- **[NEW]** search_it live progress bars: Discovery-style indication bars for MAC trace, Description search, and Network ping scan.
- **[NEW]** search_it tab refresh: Opening search_it (or page load) re-syncs progress, restores last-run summaries, resumes polling for in-flight scans, and shows View report (HTML) when a server-side last result exists.
- **[NEW]** search_it tab badge: `● running` / `✓ ready` on the search_it segment when a scan is active or complete.
- **[CHANGED]** Background scans continue when switching tabs; returning to search_it no longer loses progress or report buttons.

### v7.0.6 — 2026-05-24
**search_it Organized Reports**
- **[NEW]** search_it organized reports: MAC trace, Description search, and Network ping scan write report.txt, report.html, and manifest.json under reports/<category>/<YYYYMMDD>/<run_id>/.
- **[NEW]** search_it HTML + browser: Description search and ping scan match MAC trace — summary panels and View report (HTML) buttons.
- **[NEW]** Ops: search-it-reports-guide.md.
- **[CHANGED]** MAC trace no longer drops mac_trace_*.txt/html in the application root; uses the same reports/mac_trace/ layout.

### v7.0.5 — 2026-05-24
**MAC Trace HTML Hostnames & VPC Map Fixes**
- **[FIX]** MAC trace HTML hostnames: Reject SSH login prompts (Password:, Username:, etc.) as device names; MAC trace uses show version / switchname resolution. Fixes wrong labels (e.g. password) on large multi-vendor inventories.
- **[CHANGED]** VPC Command Center map: Map-first Overview layout, reliable vis.js boot (pane sizing + retries), toolbar (fit / peers / L2 / reset), board↔map domain highlight, node deduplication before render, default hide of non-vPC L2 edges.

### v7.0.4 — 2026-05-24
**Discovery Command Center & VPC Topology Fixes**
- **[NEW]** Discovery Command Center: Light-theme offline HTML — Overview (device table + map), Link inventory, Summary; hop/scan-state visuals in discovery_map_formatter.
- **[NEW]** Discovery in-app: Live crawl progress (current host, hop, counts, log ring buffer), filters, scan-state badges, Open Discovery Command Center button.
- **[NEW]** Ops guide: discovery-command-center-guide.md.
- **[FIX]** VPC topology map: Universal fixed x/y via `_ensure_vpc_nodes_positioned`; when no vPC domain is detected, physical adjacency fallback with banner (edges no longer hidden); map empty-state guards and Swiss Tools status counts (nodes / edges / vpc domains).
- **[FIX]** Demo: DEMO_VPC_TOPOLOGY_v7.0.4.html, DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html.

### v7.0.3 — 2026-05-24
**VPC Command Center Hotfix & Audit Fixes**
- **[FIX]** Legacy Engineering Board / Simplified Map tabs no longer break the Command Center (removed duplicate init, fixed board mount + vis.js boot retry).
- **[FIX]** Domain dropdown and topology map render together on Overview.
- **[NEW]** VPC Command Center: Offline light-theme shell — Overview split (engineering board + simplified map), Link inventory, Collected data tab from 06_pre_render_presentation.json, deferred vis.js init.
- **[NEW]** Ops guide: vpc-command-center-guide.md.
- **[FIX]** Audit NEW-C1–NEW-M9: Frozen EXE plugin bootstrap from _MEIPASS; discovery visited/dry_run; CLI session lock through connect; job-store locks + STP prune; Junos LLDP local port; MAC trace platform rows; edge dedup with ports; safer hostname merge; case-insensitive graph validation; per-job inventory files; MAC trace string matches; silent JSON parse; STP poll UI restore; health ok for full mode; tighter IOS classifier.

### v7.0.2 — 2026-05-24
**Health Wizard Blocking Startup Fix**
- **[FIX]** Health wizard blocking startup: Removed auto-run of discovery demo and CLI smoke on first launch; Continue to program dismisses immediately.
- **[FIX]** Plugin health false negative: Uses `get_all_metadata()` (≥10 plugins), shows loaded plugin IDs; no reliance on private _plugins count ≥11 with zero errors.
- **[CHANGED]** utils/health_check_runner.py: quick / full / optional CLI smoke modes; default API quick-only.
- **[CHANGED]** Diagnostics MAC copy clarifies inventory-wide trace vs CDP hop-by-hop.
- **[NEW]** Ops: health-wizard.md, mac-trace-howto.md.

### v7.0.1 — 2026-05-24
**Discovery Platform Misclassification & Duplicate Nodes Fix**
- **[FIX]** BUG-0007: Discovery CDP platform Nexus* misclassified as JunOS ('ex' in 'nexus'); replaced with token-based `classify_os_family()` in utils/discovery_graph.py.
- **[FIX]** Duplicate discovery nodes: Canonical merge by IP/hostname before map/HTML; edges rewired to canonical ids.
- **[CHANGED]** Discovery map labels: OS family + model; sidebar shows os_family / device_type.
- **[CHANGED]** Topology Swiss Tools: neighbor endpoint normalization on collected edges.
- **[CHANGED]** Plugin network_discovery 1.3.0.

### v7.0.0 — 2026-05-24
**NOC Efficiency Bundle & Major Features**
- **[NEW]** NOC Efficiency Bundle: Centralized hostname resolution (resolve_hostname_from_prompt / resolve_device_hostname) across core modules and plugins.
- **[NEW]** Unified map shell (utils/topo_map_shell.py): Link Inventory (default), static topology map, adjacency sidebar, and search — used by Discovery, standard/vPC maps, and STP reports.
- **[NEW]** First-launch health wizard: /api/health-check/run validates inventory, port, plugins, offline discovery + vPC demos, and CLI smoke.
- **[NEW]** In-app release notes: /api/release-notes and About tab "What's new in v7.0.0".
- **[NEW]** MAC trace path report: Structured path_hops, HTML summary (utils/mac_trace_formatter.py), Diagnostics UI table + "View path report".
- **[NEW]** STP Swiss Tools tab: Background job API (/api/stp/run), demo lab, offline map via modules/stp_swiss_runner.py.
- **[CHANGED]** Standard and vPC simplified maps embed Link Inventory + enhanced search (hostname, IP, port, Po, vPC domain).
- **[CHANGED]** VERSION bumped to 7.0.0.

### v6.9.28 — 2026-05-31
**Discovery Map UX & Config Template Presets**
- **[NEW]** Discovery map UX: Link Inventory tab (default) + static topology map; adjacency sidebar; offline (no Google Fonts).
- **[NEW]** Config template presets: NX-OS/IOS trunk, port-channel, trunk+vPC .j2 files + web preset builder (/api/templates/presets).
- **[FIX]** BUG-0006: Network Discovery NX-OS hostname — no longer uses show version banner as device name (resolve_device_hostname in network_base.py).

### v6.9.27 — 2026-05-31
**vPC Engineering Board & Simplified Map**
- **[NEW]** vPC Engineering Board (offline-first): vPC map HTML opens on a fixed-layout Engineering Board tab — domain selector, peer strip, vPC Port-Channel table, downstream links, global consistency CLI, and alerts — no Vis.js physics required to read telemetry.
- **[NEW]** Simplified Map tab: Static coordinates, physics off, short edge labels, non-vPC links hidden by default (toggle on map tab).
- **[FIX]** NX-OS vPC parsing: Peer status / vPC keep-alive status labels in show vpc (topology mapper aligned with vpc_domain plugin).
- **[FIX]** Payload gaps: port_channels embedded on topology nodes; peer-link Po and global consistency parameters shown in board and side panel.
- **[FIX]** Presentation: Per-vPC vs global consistency sections separated in VPC detail panel.

### v6.9.26 — 2026-05-31
**Discovery Job Status & Memory Fixes**
- **[FIX]** Discovery job status (BUG-0002): API and UI no longer report success when the plugin returns status: error.
- **[FIX]** Discovery jobs memory (BUG-0005): Prune in-memory job store to the 50 most recent runs.
- **[FIX]** QA: Discovery parser tests close fixture files; vPC validation reads VERSION dynamically (semver) instead of hardcoding.
- **[NEW]** Documentation: BUG-0001: Synced version-awareness fields and walkthrough to v6.9.26 / current OFFLINE EXE and port 5051.

### v6.9.25 — 2026-05-31
**Network Discovery Seed Unpacking Fix**
- **[FIX]** Network Discovery (live crawl): Fixed ValueError: not enough values to unpack (expected 3, got 2) when running Discovery on one or more seed devices. Seed tuples are (host, device_type); the initializer loop incorrectly expected a third depth field (queue-only).
- **[NEW]** Tests: Regression coverage in tests/test_network_discovery.py for seed unpacking and mocked single-seed crawl entry.

### v6.9.24 — 2026-05-31
**Swiss Tools Topology UX & Topology API**
- **[NEW]** Swiss Tools — topology UX: Redesigned map panel with Standard vs vPC actions, color legend, live status polling (/api/topology/status), Open Map in Browser and Open Diagnostics Folder after completion.
- **[NEW]** Topology API: /api/topology/open and /api/topology/open-diagnostics for the last completed map job; thread tracks _last_topology with device OK counts.
- **[NEW]** vPC infographic: Domain summary header and engineer-oriented copy in generate_topology_html; [TOPOLOGY_READY] JSON log for console and UI poller.
- **[FIX]** Topology HTML CSS: Removed stray }} in report_formatter.py that broke side-panel styles on vPC maps.

### v6.9.23 — 2026-05-31
**Discovery Tab & API Fixes**
- **[FIX]** Discovery tab blank page: Added missing tab-discovery HTML panel (navbar and JavaScript existed without content). Restored Config Templates tab-templates panel the same way.
- **[FIX]** Discovery API: Implemented NetworkDiscoveryPlugin class (API previously imported a non-existent class). Multi-seed BFS, demo mode, and /api/discovery/report/<job_id> for topology HTML.
- **[NEW]** Network Discovery v1.1.0: IOS/NX-OS/Junos device-type detection, serial extraction, CDP brief fallback for legacy IOS, endpoint filters for phones/APs, demo lab topology for offline validation.
- **[NEW]** Tests: tests/test_network_discovery.py with CDP/LLDP/Junos parser fixtures and demo-mode plugin test.

### v6.9.22 — 2026-05-31
**Master Prompt Governance v3.0**
- **[NEW]** Master Prompt Governance v3.0: Added docs/13-master-prompts/ hub (INDEX_PROMPT.md, PROMPT_REGISTRY.md, policies, role/escalation matrices, usage guides, action logs). Verbatim archive of PLATFORM_PROMPTS under archive/platform-prompts-original/. Root pointer: INDEX_PROMPT.md.
- **[NEW]** PROMPT_REGISTRY v3.1.0: Full required-fields schema (prompt_id, source_prompt, dependencies, status, versioning); Quick Index; platform/archive/linked-doc entries; draft usage slots for eight platform roles.
- **[NEW]** PROMPT_USAGE_MANUAL v3.0: Council role activation rules, resync/escalation/documentation/quality gates, example workflows, success criteria; nine council usage guides + standard template; ROLE_MATRIX v3.1.
- **[NEW]** PROMPT_ACTIVATION_POLICY v3.0 (G-13): Mandatory automatic role activation matrix, dependency chain, Team Meeting escalation, activation logging; INDEX read order §5.
- **[NEW]** ROLE_USAGE_STANDARD v3.0 (G-14): 12-section role prompt standard, 7-section usage guide standard, structured output format, action log template; INDEX §5.
- **[NEW]** PROMPT_EXECUTION_RULES v3.0 (G-15): Mandatory 15-step read/execute sequence, no-skip rules, logging requirements; INDEX Phase A/B reorganized.
- **[NEW]** PROMPT_GOVERNANCE_POLICY v3.0 (G-03): Managed-asset rules, traceability, change/retirement review, governance action log requirements; conflict precedence includes G-15.
- **[NEW]** ROLE_MATRIX v3.0 (G-04): Full coordination map (mission, domain, collaborators, reviews, escalation, output artifacts); council + domain specialist tables.
- **[NEW]** ESCALATION_MATRIX v3.0 (G-05): Issue-type escalation table (prompt drift, security, QA, conflicts, etc.); blocker conditions; L0–L4 severity retained.
- **[NEW]** DOCUMENTATION_POLICY v3.0 (G-06): Mandatory doc review triggers, ownership matrix, documentation action log fields; aligns with LIBRARIAN mandate.
- **[NEW]** QUALITY_GATE_POLICY v3.0 (G-07): Eleven review gates, risk-profile rules, no bypass without Team Meeting; quality-gate action log; project test hooks retained.
- **[NEW]** CHANGE_MANAGEMENT_POLICY v3.0 (G-08): Eight-phase lifecycle (problem through approval), required artifacts, change-management action log; council role mapping.
- **[NEW]** RELEASE_MANAGEMENT_POLICY v3.0 (G-09): Rollout rules, seven required checks, release action log (scope, approvals, rollback, validation, deployment, post-release watch).
- **[NEW]** COMPETITIVE_ADVANTAGE_POLICY v3.0 (G-10): Eight review domains, strategic rules, six required outputs, invest/avoid pillars for Network Swiss Tool Pro.
- **[NEW]** PROMPT_MIGRATION_SYNC v3.0 (G-16): Migration workflow (10 steps), sync versioning rules, six output requirements; archive-first traceability.
- **[NEW]** ROLE: Prompt Librarian v3.0 (R-GOV-LIB): Master-hub role prompt with full G-14 sections; PROMPT_LIBRARIAN_USAGE.md (ROLE USAGE) — invoke, best practices, scenarios, expected result.
- **[NEW]** ROLE: System Architect v3.0 (R-ARCH): Master-hub role prompt; SYSTEM_ARCHITECT_USAGE.md (ROLE USAGE); Architect Review gate alignment.
- **[NEW]** ROLE: Lead Developer v3.0 (R-ENG): Council master role; ENGINEER_USAGE.md (ROLE USAGE); linked to platform ENGINEER.md (P-ENG).
- **[NEW]** ROLE: QA Engineer v3.0 (R-QA): Validation, regression, compatibility; release block authority; QA_ENGINEER_USAGE.md (ROLE USAGE).
- **[NEW]** ROLE: Security Reviewer v3.0 (R-SEC): Trust boundaries, approve/block release; SECURITY_REVIEWER_USAGE.md (ROLE USAGE).
- **[NEW]** ROLE: Observability Engineer v3.0 (R-OBS): Diagnostics, telemetry gaps, block visibility regression; OBSERVABILITY_ENGINEER_USAGE.md (ROLE USAGE).
- **[NEW]** ROLE: Documentation Steward v3.0 (R-LIB): Doc/code/prompt parity, require updates before completion; DOCUMENTATION_STEWARD_USAGE.md (ROLE USAGE); LIBRARIAN_USAGE.md alias.
- **[NEW]** ROLE: Release / Change Manager v3.0 (R-REL): Readiness, rollback, block release; RELEASE_MANAGER_USAGE.md (ROLE USAGE); G-09 gate consolidation.
- **[NEW]** ROLE: Product / Platform Strategist v3.0 (R-PROD): Mission, competitive advantage, prioritization; PRODUCT_STRATEGIST_USAGE.md (ROLE USAGE); G-10 alignment.
- **[NEW]** ROLE: Team Meeting Council v3.0 (R-COUNCIL): Cross-functional review, required issue schema, exact AI prompts; TEAM_MEETING_COUNCIL_USAGE.md; G-11 template updated.
- **[NEW]** FINAL OPERATING INSTRUCTION v3.0 (G-17): Binding IDE contract — preserve/sync prompts, auto-activate roles, enforce policy chain and gates, success criteria; INDEX read order step 7.
- **[NEW]** Combined council prompts (roles/combined/): One file per role merging R-* master + U-* usage (e.g. ROLE_LIBRARIAN_USAGE_PROMPT.md, ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md); registry C-* entries v3.1.31.
- **[NEW]** GLOBAL MASTER PROMPT RULES v4.0 (G-18): 20 absolute rules, mission, vision, engineering principles; INDEX_PROMPT v4.0; G-03 precedence #1; read order step 3.
- **[NEW]** INDEX_PROMPT v4.0 (user spec): Numbered read order 00–26, simple commands table, mandatory rules 1–14; stubs 00_GLOBAL_RULES through 25_ROLE_*; 26_CHECK_SYSTEM_FOR_BUGS.md; bugs/_TEMPLATE/ fix and validation prompts.
- **[NEW]** Hub consolidation (registry 4.0.3): Council roles canonical only in roles/combined/ROLE_*_USAGE_PROMPT.md; removed duplicate split R/U files, C-* registry rows, numbered hub stubs, and bugs/_TEMPLATE/ (use docs/14-bug-reports/_SCAFFOLD/). INDEX, registry, activation policy, and role matrix aligned to canonical paths.
- **[NEW]** PROMPT_REGISTRY v4.0: Preamble aligned to required fields, status values, rules, versioning, sync policy; G-01 document version 4.0.0 (entry data release 3.1.33 in change log).
- **[NEW]** CHECK_SYSTEM_FOR_BUGS v4.0 (roles/CHECK_SYSTEM_FOR_BUGS.md): Full-team bug sweep; docs/14-bug-reports/ structure; copy-paste fix/validation/doc/version prompts; _SCAFFOLD/ templates.
- **[NEW]** FINAL_OPERATING_INSTRUCTION v4.0 (G-17): Simple user commands table; IDE must list; success criteria including continuous development UX.
- **[FIX]** [P0] Jinja2 TemplateSyntaxError — Application Fail-to-Start: Fixed a critical crash in modules/web/templates/index.html (line 2668) that caused every HTTP request to return 500 Internal Server Error, rendering the entire web application completely non-functional.

### v6.9.21 — 2026-05-26
**Network Discovery & Config Templates Plugins**
- **[NEW]** Network Discovery Plugin v1.0.0: New plugin for recursive CDP/LLDP neighbor discovery starting from seed devices. Supports multi-platform parsing (Cisco IOS, IOS-XE, NXOS, Juniper JunOS), duplicate detection by MAC/UID, topology graph visualization using vis-network.js, and JSON inventory export. Includes root password support for Juniper devices and configurable crawl depth (1-3 hops).
- **[NEW]** Config Templates Plugin v1.0.0: New Jinja2-based configuration template generator with safe read-only rendering. Bootstraps example templates on startup in program directory templates/ folder. Features variable extraction from templates, dynamic form generation for variable input, preview rendering (no automatic push), and template save/load functionality. Includes error indications for template syntax errors.
- **[NEW]** Discovery Tab: New UI tab for Network Discovery with seed host input, crawl depth configuration, real-time job status polling, discovered devices table with hostname/IP/platform/serial/depth/reachability, topology visualization button, and JSON export functionality.
- **[NEW]** Templates Tab: New UI tab for Configuration Templates with template list dropdown, template editor with syntax highlighting, automatic variable scanning and form generation, render preview panel, copy to clipboard, and save functionality.
- **[FIX]** Favicon Display: Fixed favicon not displaying in HTML by adding Flask routes /favicon.ico and /static/favicon_program.png using send_file with _get_resource_path() for proper path resolution in both dev and EXE modes.
- **[FIX]** Standards Folder in EXE Mode: Fixed standards folder creation to use program directory instead of home directory. On application startup, creates standards/ folder in program directory with bundled standards.json and standards.yaml files, plus category subdirectories (Security, NTP, SNMP, Logging, Naming, Interface, AAA, Routing, QoS, Redundancy, Management, Health, Crypto, Compliance). Updated upload endpoint to save to this folder and plugin to check this folder for uploaded files.
- **[FIX]** Path Resolution: Updated _get_resource_path() in both vlan_checker_web.py and standards_validator.py to check program directory for writable files (standards/, templates/) after checking bundled resources in EXE mode. Updated list_available_policies() to scan both bundled policies/ and program directory standards/ folders.
- **[CHANGED]** Standards Validator Plugin v2.1.0: Updated path resolution to check program directory standards folder for uploaded files in EXE mode. Enhanced policy file discovery to scan both bundled and custom policy locations.

### v6.9.20 — 2026-05-26
**Standards Validator Plugin Fixes & Favicon Integration**
- **[FIX]** Standards Validator Plugin v2.1.0: Fixed critical file reading issue where uploaded policy files could not be found/read by the plugin, causing scan failures. Added _get_resource_path() helper function to plugin for PyInstaller EXE compatibility. Updated _load_policies() to use consistent path resolution. Updated upload endpoint to save files to writable location in EXE mode (user's home directory) instead of read-only _MEIPASS. Plugin now checks both bundled resources and home directory for uploaded files in EXE mode.
- **[NEW]** Favicon Integration: Added favicon_program.png to HTML head for browser tab display. Added favicon to PyInstaller spec file datas and as window icon for EXE. Favicon is now mandatory and hardcoded in the application.
- **[CHANGED]** Standards Validator: Created standards.json file alongside standards.yaml for JSON policy support. Both YAML and JSON formats are now fully supported with 65+ policies covering security, NTP, SNMP, logging, naming, interface standards, AAA, routing, QoS, redundancy, interface hardening, management plane, health indicators, crypto, compliance, and Juniper-specific checks.

### v6.9.19 — 2026-05-26
**vPC Domain Plugin Defensive Programming**
- **[FIX]** vPC Domain Plugin v2.3.1: Added defensive programming fixes to prevent AttributeError and crashes when verification functions encounter None values or non-string inputs. Added isinstance() checks before all string operations (.lower(), .splitlines(), etc.). Added type validation for VLAN lists, members lists, and output strings. All verification functions now handle missing or malformed data gracefully without crashing.

### v6.9.18 — 2026-05-26
**vPC Domain Plugin Verification Enhancement**
- **[CHANGED]** vPC Domain Plugin v2.3.0: Major enhancement - executes actual verification commands for all 10 recommendations. Added verification logic for peer-link, keepalive, Type-1/Type-2 consistency, per-vlan consistency, VLAN consistency, CDP neighbors, port-channel members, and vPC statistics. Implemented human-readable verification results section with PASS/FAIL/WARN indicators, impact descriptions, and recommended actions for each verification. Added verification summary showing total checks, passed, failed, warnings, and unknown counts. Enhanced command set with show vpc peer-link, show vpc role, show interface brief, and show vpc legacy. Replaced static recommendations with dynamic verification results that show actual mismatches/errors. Added clear indication when vPC domain is healthy with no errors or mismatches detected.

### v6.9.17 — 2026-05-25
**vPC Domain Plugin Parsing Bug Fix**
- **[FIX]** vPC Domain Plugin v2.2.1: Fixed critical parsing bug where vPC entries with "peer-link" in reason field (e.g., "Peer-link is down") caused premature termination of parsing. Changed section break detection to only break on section headers (lines starting with "peer-link" or "vpc peer-link") rather than containing the text. Added validation to skip error messages containing "error", "please", or "check". Added validation to ensure vPC ID is numeric, port-channel matches pattern, status and consistency are valid. Added validation in report formatting to only render valid vPC entries. Added warning message when vPC data is detected but cannot be parsed correctly.

### v6.9.16 — 2026-05-25
**vPC Domain Plugin Comprehensive Enhancement**
- **[CHANGED]** vPC Domain Plugin v2.2.0: Comprehensive enhancement for network engineers. Fixed vPC entries parsing to handle NXOS table format correctly (now displays all vPCs with port-channels). Added consistency parameter parsing: Type-1 (global), Type-2 (interface), per-vlan consistency status. Added configuration inconsistency reason and type-2 inconsistency reason parsing. Enhanced command set with "show vpc consistency-parameters" and "show vpc statistics". Improved port-channel parsing to extract VLAN membership and member interfaces. Enhanced report formatting with dedicated consistency parameters section. Added vPC member details including port-channel, status, consistency, reason, and active VLANs. Added troubleshooting recommendations for consistency issues.

### v6.9.1 — 2026-05-14
**LIBRARIAN Hardening & Topology Stability**
- **[NEW]** LIBRARIAN Documentation: Reorganized all project knowledge into a strict, enterprise-grade hierarchy (00-10 structure).
- **[FIX]** vPC Topology Mapper: Resolved critical `'str' object has no attribute 'get'` crash during vPC summary generation.
- **[NEW]** Air-Gapped Asset Embedding: Natively bundled `vis-network.min.js` into the executable for offline topology rendering.
- **[NEW]** NOC Intelligence Dashboard: Final polish on the high-fidelity UI v8.5 with improved vPC role logic.

### v6.9.0 — 2026-05-14
**NOC Observability & Telemetry Enrichment**
- **[NEW]** Apple-Style UI (v8.5): Complete visual overhaul with glassmorphism, fluid animations, and Hi-Tech aesthetic.
- **[NEW]** Enriched Topology: Edge labels now show Speed, Status, and Description for instant visual correlation.
- **[NEW]** Structured Telemetry: Deep LACP, vPC, and Port-Channel correlation for Nexus platforms.
- **[NEW]** Connection Intelligence: UI now distinguishes between Single-homed and Shared-risk infrastructure.

### v6.6.0 — 2026-04-30
**vPC Topology Premium Pass & CLI Stability**
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
| `vlan_checker_gui.py` | Desktop GUI source (Tkinter) |
| `vlan_checker_web.py` | Web backend source (Flask) |
| `templates/index.html` | Web frontend (HTML/CSS/JS) |
| `inventory.txt` | Device inventory (user-maintained) |
| `build_exe.bat` | PyInstaller build script for GUI |
| `build_web_exe.bat` | PyInstaller build script for Web |
| `QA_TESTING_CHECKLIST.txt` | Manual testing checklist |
| `README.md` | This file |
#   n e t _ m n g _ t o o l _ c a r t o g r a p h y 
 
 #   n e t _ m n g _ t o o l _ c a r t o g r a p h y 
 
 