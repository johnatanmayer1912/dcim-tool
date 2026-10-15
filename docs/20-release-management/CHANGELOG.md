# Network Swiss Tool Pro - Changelog

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Chronological record of all notable changes, features, and fixes implemented in the platform. |
| **Scope** | Version history, release notes, bug fixes, and feature additions since project inception. |
| **Related Documents** | [Release History](release-history.md), [Project Overview](../00-overview/project-overview.md) |
| **Update Responsibility** | Release Manager / Lead Developer |
| **Version Awareness** | v7.0.51 |

---

## [v7.0.51] - 2026-06-18

See root [CHANGELOG.md](../../CHANGELOG.md) — Standard Map UI polish, peer-link fix, legend contrast, `NetworkSwissToolPro_v7.0.51_OFFLINE.exe`.

## [v7.0.50] - 2026-06-21

See root [CHANGELOG.md](../../CHANGELOG.md) — Standard Map offline/older-Chrome map render fix.

## [v7.0.49] - 2026-06-18

See root [CHANGELOG.md](../../CHANGELOG.md) — Standard Map NOC split-pane redesign.

## [v6.9.5] - 2026-05-24

See root [CHANGELOG.md](../../CHANGELOG.md) — search_it tab, description search, vPC Domain plugin, topology UI/keepalive fixes.

## [v6.9.4] - 2026-05-24

### Added
- Per-switch `vpc_member_interfaces` collection and HTML sidebar population.
- Mandatory `topology_diagnostics_*` folder at app working directory with staged JSON (`01`–`07`), `vpc_map_data_TEMPLATE.json`, and offline HTML map.
- Automated test: `tests/validate_vpc_member_interfaces.py`.

### Fixed
- `bundled_links` promoted to Vis.js edge payload; `edge_data` fallback in UI.
- `show vpc brief` parser when main vPC table is empty.
- Static map rendering (no continuous edge animation; physics off after stabilize).
- Edge categorization when `type` exists only under `edge_data`.

See root [CHANGELOG.md](../../CHANGELOG.md) for full detail.

## [v6.9.1] - 2026-05-14

### Added
- **Apple-Style UI Overhaul**: Transitioned the entire observability dashboard to a "Glassmorphism" / Hi-Tech NOC aesthetic (v8.5), featuring premium shadows, SF Pro typography, and Apple-inspired color palettes.
- **Human-Readable Link Enrichment**: Connection edges now display physical interface speed, operational status, and truncated descriptions directly on the graph for instant troubleshooting without clicking.
- **Enterprise Rebranding**: Standardized all UI headers and metadata to reflect the "Made by AI IDE" identity.

### Fixed
- **Offline Topology Viewer**: Resolved critical "Map Cannot Be Viewed" errors in air-gapped environments by natively embedding the `vis-network.min.js` dependency into the generated HTML reports.
- **Topology Mapper Hardening**: Fixed a critical `'str' object has no attribute 'get'` crash during vPC summary table generation by implementing defensive type-checking for internal metadata strings.
- **Demo Generator Stability**: Updated `create_demo_map.py` to correctly load local assets and support the new enriched data structures.

## [v6.9.0] - 2026-05-14


### Added
- **Structured Telemetry Enrichment**: Integrated deep network metadata collection for Port-Channels, vPCs, and LACP partners across NX-OS, IOS, and JunOS.
- **Cross-Platform Correlation**: Implemented CDP/LLDP cross-validation mechanisms and LACP partner verification to ensure high confidence network mapping.
- **Connection Intelligence Panel**: Added advanced frontend analytics detecting shared versus single-homed (orphan) VPC connections with risk validation badges.
- **LACP State Validation**: Edge info panels now display rich LACP partner system ID and port state for detailed troubleshooting.

### Enhanced
- **VPC Operational Summary**: Redesigned VPC Detail Panel natively supports real-time visibility into active VLANs, Keepalive status, Domain roles, and consistency checks per member.
- **Topology Parsing Architecture**: Replaced brittle regex patterns in Phase 1 (`topology_mapper.py`) with 6 new enterprise-grade structured parsers (`_parse_vpc_full`, `_parse_lacp_neighbors_nxos`, etc.).
- **Defensive Rendering Pipeline**: The UI now gracefully handles incomplete or inferred edge topology by leveraging the new `cdp_validation_map` for explicit confidence scores.

## [v6.8.1] - 2026-05-10

### Fixed
- **[CRITICAL] VPC Map Blank Issue**: Fixed blank map when scanning 2 devices in vPC domain.
  - **Root Cause**: VPC transformation removed internal peer-links but never created replacement edges.
  - **Fix**: Added placeholder edge creation between VPC domain node and members when no downstream links exist.
  - **Location**: `modules/adapters.py:1037-1088`
  - **Impact**: vPC maps now display correctly for 2-device scenarios.

- **HTML Fallback Content**: Added visible fallback content when JavaScript fails to render.
  - Users will see "Initializing visualization..." message instead of blank white canvas.
  - Message includes version and instructions to check browser console (F12).
  - Fallback is cleared automatically when Vis.js renders successfully.

### Enhanced
- **MAP-PIPELINE Logging**: Updated to v6.8.1 for consistent version tracking.
- **Console Diagnostics**: Added more detailed logging for edge creation events.

## [v6.8.0] - 2026-05-07

### Added
- **Architectural Hardening**: Implementation of a "Defensive Rendering Pipeline" for vPC topology.
- **Orphan Edge Filtering**: Runtime sanitization in the browser to prevent crashes caused by inconsistent graph data.
- **Physics Stabilization**: Explicit mass and gravity constants for vPC nodes to prevent "coordinate explosion" in large hierarchies.

### Fixed
- **[P1] Empty Map Syndrome**: Resolved edge-case silent script terminations that previously left the topology canvas blank despite successful data collection.
- **Event Handling**: Wrapped event listener management in try/catch blocks for improved resilience in restricted browser environments.

## [v6.7.7] - 2026-05-06

### Fixed

- **[P1] vPC Map Empty / Blank UI:** `modules/adapters.py`, `utils/report_formatter.py` — Resolved critical rendering issues where topology maps appeared blank.
  - **Deep ES5 Compatibility**: Performed a full audit and "De-ES6-ification" of all browser-side JavaScript. Replaced arrow functions (`=>`), template literals (backticks), and ES6 methods (`startsWith`) with ES5 equivalents to ensure compatibility with legacy browser engines.
  - **Asset Portability**: Improved `vis-network.min.js` embedding logic to ensure the library is bundled directly into the HTML for air-gapped/offline use.
  - **Self-Loop Removal**: Eliminated internal self-loop edges for vPC domains which caused hierarchical layout stabilization failures in Vis.js.
  - **HTML Structure**: Fixed a dangling `</div>` in the vPC summary template that broke browser rendering of the map container.
  - **JS Resilience**: Re-implemented `network.fit()` with a multi-stage approach (IterationsDone + Stabilized events) plus a 1-second safety fallback.
  - **Metadata Fix**: Added fallback description extraction in `toggleDescriptions` to prevent JS errors when edge metadata is partially nested.

## [v6.7.6] - 2026-05-04

### Fixed

- **[P1] vPC Map Empty After Generation:** `utils/report_formatter.py` — vPC layout uses `physics: { enabled: true }` with hierarchical repulsion. After stabilization, Vis.js positioned nodes off-screen and never auto-fitted the viewport. Added `network.once('stabilizationIterationsDone', network.fit)` and a 300ms fallback `setTimeout(network.fit)`.

- **[P1] Interface Map: No Descriptions in Popup:** `modules/node_interface_topology.py` — Description parser only matched lines where the second token was a status keyword. `show interfaces description` uses a tabular format where description is the 4th column. Added multi-strategy parser: full regex → simplified regex → tab-split fallback.

- **[P1] Interface Map: Missing MACs on Port-Channels:** `modules/node_interface_topology.py` — MAC matching used loose substring logic causing false matches and missed port-channel entries. Rewrote to use exact `norm_int()` match with proper skip logic for MAC addresses, VLAN numbers, and type keywords.

## [v6.7.5] - 2026-05-06

### Fixed
- **2-Device VPC Map Blank Issue**: Fixed blank map when scanning exactly 2 devices in vPC domain.
  - **Root Cause**: VPC transformation logic only created edges for shared downstream links, not internal peer-links.
  - **Fix**: Added explicit peer-link edge creation for 2-device vPC scenarios where no downstream shared links exist.
  - **Logging**: Added [MAP-PIPELINE] phase logging for better debugging.

- **Version String Synchronization**: Fixed hardcoded v6.2.4 version strings in CLI connectivity HTML template.
  - Updated `modules/web/templates/cli_terminal.html` to show v6.7.5.

### Enhanced
- **5-Phase Validation Pipeline**: Added structured logging for map generation:
  - Phase 1: Device Collection (validates successful connections)
  - Phase 2: Edge Processing (validates edge detection)
  - Phase 3: VPC Transformation (validates domain clustering)
  - Phase 4: Node Building (validates node metadata)
  - Phase 5: HTML Generation (validates file creation)

- **Interface Traffic Statistics**: Added upload/download rate display in Interface Map tooltips.
  - Collects `input_rate` and `output_rate` from `show interface` command for NXOS/IOS/JUNOS.
  - Displays formatted traffic rates (e.g., "↓1.5 Mbps ↑2.3 Mbps") in port tooltips.
  - Supports human-readable formatting (Kbps, Mbps, Gbps).

## [v6.7.4] - 2026-05-06

### Fixed
- **DEMO VPC Map Blank Issue**: Fixed critical issue where DEMO topology map failed to render.
  - **Root Cause**: DEMO file used external `<script src="modules/web/vis-network.min.js">` which fails when file opened directly in browser.
  - **Fix**: Embedded vis.js library inline in DEMO file (702KB) for standalone offline functionality.
  - **Error Handling**: Added JavaScript error handling with try-catch around network initialization and diagnostic console logging.
- **Generated Maps Error Handling**: Added defensive error handling in `utils/report_formatter.py` for network initialization failures.

### Enhanced
- **Interface Descriptions**: Enhanced interface description display in VPC detail panels and edge tooltips for better network documentation visibility.

## [v6.7.3] - 2026-05-04

### Fixed
- **Blank VPC Map Issue**: Resolved critical bug where VPC topology maps appeared blank/empty.
  - **Root Cause**: `vpc_members` field was only added to node metadata, not to the actual node objects passed to JavaScript frontend.
  - **Fix**: Added `vpc_members` field to node objects in `modules/adapters.py` (line 1182).
  - **JavaScript Hardening**: Added data validation and fallback member extraction in `utils/report_formatter.py` to handle edge cases.
  - **Diagnostics**: Added debug logging in both backend and frontend to trace VPC data flow.

## [v6.7.2] - 2026-05-04

### Added
- **VPC Visualization Layer v7.0**: Complete redesign of VPC topology visualization with 3-View Progressive Disclosure System.
  - **Global Topology View**: VPC domains displayed as large, prominent indigo nodes with drop shadows. Shared connections = thick blue edges, Orphan connections = dashed red edges.
  - **VPC Detail Panel**: Slide-out panel showing peer-link visualization, member device grid (Primary/Secondary), and interface listings.
  - **Connection Intelligence Panel**: Categorized view of shared (dual-homed) vs orphan (single-homed) connections with risk badges and export functionality.
- **Modern CSS Design System**: CSS custom properties for VPC colors, 8px spacing grid, card-based layouts, smooth 150-250ms transitions.
- **DEMO VPC Topology**: Standalone `DEMO_VPC_TOPOLOGY_v7.0.html` with sample 6-device network (2 VPC domains, 2 servers) for testing visualization without real devices.
- **Navigation History Stack**: Back/close buttons maintain view state for intuitive navigation between Global → Detail → Intelligence views.

### Changed
- **VPC Node Styling**: VPC domains now use indigo gradient (#6366f1 → #8b5cf6), larger size (60px), white text, prominent shadow for instant visual recognition.
- **Panel Architecture**: Replaced single side panel with dedicated VPC Detail and Connection Intelligence panels.

## [v6.7.1] - 2026-05-04

### Fixed
- **CLI Crash (AttributeError)**: Resolved a critical server-side crash in `Flask-SocketIO` when using Flask 3.1.x by disabling automatic session management.
- **Resilient CLI Routing**: Re-implemented robust Room + SID hybrid routing for CLI WebSocket traffic. Initial ACKs use SID for zero-latency feedback, while subsequent data streams use Room-based routing to ensure stability across browser reconnections.
- **Improved Background Handshake**: Standardized the background connection lifecycle with consistent progress reporting and definitive TCP/SSH error delivery.

## [v6.7.0] - 2026-05-04

### Added
- VPC logical topology rendering: Transforms vPC pairs into single logical domains on the map.
- Interface description visualization: Shows interface descriptions on link tooltips and optionally on labels.

### Fixed
- WebSocket CLI connectivity: Formalized state machine to prevent race conditions during SSH connection rendering.
- Missing interface descriptions: Handled extraction of `desc` from interface data into Vis.js tooltips.
- Incorrect VPC pairing logic: Replaced outdated domain mapping to now cleanly identify overlapping redundant links as single shared paths or orphan links.

### Improved
- Map clarity: Removed cluttered redundant links from vPC pairs to downstream devices.
- Data model: `VPCDomain` node restructuring allows standard Vis.js rendering without hacky node duplication.

## [6.6.0] - 2026-04-30

### Added
- **vPC Topology Premium Pass**: Enhanced peer-clustering via `vis.Network` groups, enabling logical side-by-side alignment for vPC domain members without manual coordinates.
- **Glow & Shadow Edge Styling**: Implemented high-visibility orange glows for vPC member links and purple shadows for peer-links to improve architectural clarity.
- **Glassmorphism Intelligence Dashboard**: Redesigned the vPC summary side-panel with a modern slate theme, backdrop-blur (8px), and Inter typography.
- **Hardened CLI Connectivity**: Resolved persistent "Stuck on Connecting" state by eliminating redundant WebSocket SID emits and implementing immediate backend-to-frontend diagnostics.
- **Immediate Console Diagnostics**: Added real-time print statements in `vlan_checker_web.py` for terminal connection handshakes to facilitate air-gapped troubleshooting.

### Fixed
- **CLI character doubling**: Removed double-emit logic (Room + SID) in `vlan_checker_web.py` that caused redundant output rendering in high-latency environments.
- **Stale vPC Summary styles**: Replaced inline white/orange table styles with a cohesive dark-mode glassmorphism palette.
- **Topology Font Scaling**: Standardized on the Inter font family across all Vis.js nodes for improved readability at high zoom levels.

## [6.5.5] - 2026-04-28

### Added
- **Standards Validator Plugin** (`modules/plugins/standards_validator.py`): Compares live device config against a user-editable YAML policy library. Reports violations with exact remediation commands. Read-only.
- **Expanded Policy Library** (`policies/standards.yaml`): 40+ policies across 10 categories — Security, NTP, SNMP, Logging, Banner, Naming, Routing, QoS, Redundancy, Interface, Management, Health, Crypto, Compliance, Juniper-specific.
- **`policies/` bundled in EXE**: Policy library is now included in the offline distribution package and PyInstaller spec. The EXE reads `policies/standards.yaml` from the folder next to the executable.
- **CLI Smoke Test** (`tests/test_cli_smoke.py`): Mandatory mock-SSH test that proves the CLI terminal connection flow works before every build. 11 steps covering connect, prompt receipt, write, disconnect.
- **`_prebuild.py` gate**: All builds now require syntax check + plugin load + CLI smoke test + safety checks to pass before PyInstaller runs.



### Fixed (CLI Terminal + MAPS Interface Data + M-Bugs)

- **[P0] CLI Terminal stuck on "Connecting":** `modules/cli_manager.py` completely rewritten with full inline documentation. Root causes: (1) `_do_connect()` never forwarded progress to `log_callback` — frontend saw nothing during the 10–45s SSH handshake. (2) `self.hostname` was never updated from the initial IP — stayed as IP forever. Fixed: every SSH handshake step now emits progress via `log_callback`; initial prompt is read after shell open to extract real hostname; buffered prompt bytes forwarded to frontend immediately so device prompt appears without delay.

- **[P0] MAPS side panel: no interfaces / speed / VLAN / MACs:** Four root causes fixed: (1) `topology_mapper.py` desc parser created `int_meta` entries without `speed`/`vlan`/`duplex`/`macs` keys — JS got `undefined`. Fixed: all four fields initialised to empty string/list in every code path. (2) MAC normalization mismatch — `_parse_mac_table` used `norm_int()` but `valid_interfaces` check was case-sensitive exact match. Fixed: added case-insensitive fallback. (3) Edge panel `f_int_data` lookup used raw CDP port name (`GigabitEthernet0/1`) but `int_meta` keys are normalized (`Gi0/1`) — always showed `unknown`. Fixed: `norm_int()` applied before lookup with raw-name fallback. (4) `adapters.py` MAC merge block didn't guarantee all fields exist. Fixed: `setdefault()` for all display fields before passing to frontend.

- **[P1] MAPS side panel: neighbor-only nodes show nothing:** Nodes discovered via CDP/LLDP but not directly scanned had empty `interfaces` dict — side panel was blank. Fixed: added "Interface Data Unavailable" message explaining the device needs to be in inventory to see interface details.

- **[P1] M-Bug: `network_audit.py` no `log_func`, no `finally` disconnect:** Added `log_func=None` parameter and `finally: conn.disconnect()` to prevent SSH session leaks on exception.

- **[P1] M-Bug: `config_backup.py` no `log_func`, no `finally` disconnect:** Same fix applied.

- **[P1] M-Bug: `save_config.py` no `log_func`, no `finally` disconnect:** Same fix applied.

- **[P1] M-Bug: `vlan_compare.py` no `log_func`, no `finally` disconnect:** Same fix applied.

- **[P1] Removed `restore_backup()`:** `utils/config_backup_system.py` — the experimental config restore method was unsafe (blind line-by-line paste corrupts NX-OS configs). Removed entirely along with `rollback_vlan_change()` in `vlan_mgmt_production.py` and the `/api/plugins/rollback` route in `vlan_checker_web.py`.

- **[P2] Added `utils/app_logger.py`:** Production-grade structured logging with rotating JSON files, audit trail, GUI callback support, and `export_logs()` for AI/support analysis.



### Fixed (Plugin System, VLAN Scope & Topology)

- **[P0] Plugin Registry Syntax Error:** `modules/plugin_registry.py` — `_validate_metadata()` had a double-colon `::` syntax error that prevented the entire module from importing. All 9 plugins were silently failing to load on every startup. Fixed to single colon.

- **[P0] Missing Plugin Report Functions:** `utils/report_formatter.py` — All 9 plugins import `save_plugin_report`, `append_to_master_report`, and plugin-specific `format_*_report` functions that did not exist in the file. Added all missing functions: `save_plugin_report`, `append_to_master_report`, `generate_consolidated_plugin_report`, `format_vlan_audit_report`, `format_serial_number_report`, `format_device_time_report`, `format_critical_logs_report`, `format_interface_errors_report`, `format_environment_status_report`. All 9 plugins now load with 0 errors.

- **[P1] Single Device VLAN Operations Return 0 Targets:** `vlan_checker_web.py` — `filter_inventory()` applied the group filter before the single-host match. When the group dropdown showed a non-matching group from a previous bulk session, the selected host was filtered out, returning 0 devices and the error "Filtered scope resulted in 0 target devices." Group filter is now skipped entirely in single mode.

- **[P1] vPC Topology Map Disorganized:** `modules/adapters.py`, `utils/report_formatter.py` — vPC map used `barnesHut` physics producing a chaotic, unreadable layout. Replaced with hierarchical `UD` layout (same as standard topology). vPC summary panel replaced with a structured table showing Device, vPC ID, Port-Channel, Status, and Peer-Link columns.

- **[P1] Topology Side Panel Missing Speed/VLAN/MAC:** `modules/topology_mapper.py` — `show interface status` was parsed for link state only; Speed, VLAN, and Duplex columns were never extracted. Added `_parse_status_line_fields()` helper. Interface data in the side panel now shows speed (1G/10G/etc.), VLAN assignment, duplex, and MAC addresses per interface.

## [6.4.0] - 2026-04-27

### Added
- **Intelligent Topology Mapping**: Complete re-engineering of the correlation engine and visualization.
- **Troubleshooting Side Panel**: Interactive panel for real-time device info, port stats, and MAC address correlation.
- **Link Confidence Scoring**: Visual indicators for bidirectional (Green), asymmetric (Yellow), and mismatch (Red) links.
- **vPC Styling**: Dedicated rendering for vPC Peer-Links and Member ports.
- **MAC Transparency**: Correlation of learned endpoint MAC addresses to inter-switch trunk links.

## [6.2.6] - 2026-04-26

### Fixed (Sprint 1 Audit Remediation — Production Hardening)

- **[P0] SSH Algorithm Mismatch:** `modules/network_base.py` — `connect_permissive()` completely
  rewritten with a two-pass strategy matching the proven approach in `cli_manager.py`.
  Pass 1 uses modern default Paramiko algorithms (works on IOS-XE 17.3+, NX-OS 9.3+, Juniper 21.x+).
  Pass 2 falls back to legacy `disabled_algorithms` for older hardware (IOS 12.x, NX-OS 7.x).
  Previously, ALL connections were forced to legacy mode, causing silent failures on modern devices.

- **[P0] Missing Plugins in PyInstaller Spec:** `build_scripts/NetworkSwissToolPro_v6_2_5_BETA.spec` —
  Added `modules.plugins.stp_topology_visualizer` and `modules.plugins.unused_trunk_pruner`
  to `hiddenimports`. These two plugins were copied to the dist folder but not declared,
  risking load failures in the compiled EXE.

- **[P0] Dependency Version Pinning:** `requirements.txt` — All 9 dependencies now have exact
  version pins (`==`). Previously only `netmiko` was pinned; all Flask/SocketIO deps used `>=`
  ranges, creating offline build reproducibility risk. Added `wsproto`, `bidict`, and `h11`
  which were already used in the spec but not declared in requirements.

- **[P1] Silent Report Failures:** `utils/report_formatter.py` — All file-writing functions
  (`write_text_file`, `write_csv_file`, `append_text_file`, etc.) now log errors to stderr
  instead of silently swallowing exceptions. Failed report writes are now visible in the
  operations log.

- **[P1] Version Single Source of Truth:** `main.py` and `vlan_checker_web.py` — Hardcoded
  `VERSION = "6.2.5-BETA"` strings replaced with `_read_version()` helpers that read the
  `VERSION` file at startup. Eliminates all future version drift across entry points.

- **[P1] MAC Address Input Validation:** `modules/mac_trace.py` — Added `_validate_mac()`
  with a strict safe-character regex before the MAC is concatenated into a device CLI command.
  Prevents potential command injection via malformed MAC strings.

- **[P1] Plugin Manifest Accuracy:** `PLUGINS_INCLUDED.txt` —
  - Updated header from `v6.0.0-BETA` to `v6.2.5-BETA`
  - Corrected "BUNDLED PLUGINS (7 TOTAL)" to "(9 TOTAL)"
  - Added full entries for `stp_topology_visualizer` (v1.0.1) and `unused_trunk_pruner` (v1.0.1)
  - Fixed stale `build_v6_0_0_beta.bat` reference to current spec file name
  - Updated validation instructions to reference 9 plugins
  - Updated MANIFEST DATE to 2026-04-26



### Added (Enhanced Plugin Reporting)

- **Improved:** Consolidated plugin reporting that aggregates results from multiple devices into a single, high-quality "human-readable" document.
- **Improved:** Visual formatting for plugin outputs (Serial Number, VLAN Audit, etc.) including status emojis (✅/❌) and aligned table layouts.
- **Improved:** Indicative report filenames that now include the device IP or hostname for single-device scans.
- **Hardened:** Centralized report orchestration in `report_formatter.py` to ensure all future plugins benefit from consistent, visual output formatting.

## [6.2.4] - 2026-04-23

### Fixed (CLI Terminal "Stuck on Connecting")

- **Fixed:** Critical race condition in CLI handshake where the frontend was stuck on "Connecting" despite a successful WebSocket link.
- **Fixed:** Implementation of "Handshake Delay" (100ms) and "Double-Emit Enforcement" to ensure the client PTY is fully ready before the session status is sent.
- **Improved:** Standardized versioning across `main.py`, `vlan_checker_web.py`, `cli_manager.py`, and the frontend.
- **Hardened:** Offline dependency bundling verified in the build spec for air-gapped production use.

## [5.5.0] - 2026-04-19

### Fixed (XHR Poll Error / Transport Error)

- **Fixed:** XHR poll errors and transport errors preventing CLI terminal from connecting to server.
- **Added:** Comprehensive startup logging to `logs/startup.log` for diagnosing EXE startup issues.
- **Added:** Server health check (`checkServerHealth()`) in CLI terminal before Socket.IO connection.
- **Added:** Enhanced error messages in terminal showing possible causes (firewall, antivirus, server not ready).
- **Improved:** Socket.IO configuration with longer timeouts (30s) for EXE cold start scenarios.
- **Improved:** Increased reconnection attempts (15) with exponential backoff for better reliability.
- **Improved:** Server startup with detailed logging of Socket.IO initialization and port availability.
- **Changed:** `initSocket()` is now async and performs health check before attempting Socket.IO connection.
- **Changed:** DOMContentLoaded event handler is now async to support await on `initSocket()`.

## [5.4.9] - 2026-04-19

### Fixed (CLI Terminal Connectivity)

- **Fixed:** Critical bug where CLI terminal was stuck in "Connecting" state because `initSocket()` was never called.
- **Fixed:** ImportError for missing `list_cli_sessions()` function in `cli_manager.py`.
- **Improved:** Socket.IO connection now initializes immediately on page load, ensuring reliable server communication.

## [5.4.8] - 2026-04-19

### Fixed (Connectivity Handshake Hardening)

- **Fixed:** Handshake failures caused by ambiguous `localhost`/IPv6 resolution by forcing `127.0.0.1` binding.
- **Added:** Technical Handshake Log UI (Debug toggle) for real-time frontend troubleshooting.
- **Added:** `/health` and `/debug_status` HTTP endpoints for definitive service isolation.
- **Improved:** Resilience in high-latency environments by increasing ping timeouts to 60s.

## [5.4.7] - 2026-04-19

### Fixed (Absolute Bundle & Crash Protection)

- **Fixed:** Startup crashes (Unhandled Exception) caused by unsafe imports in the diagnostic logger.
- **Fixed:** Missing root packages in the bundle by switching to `collect_all` PyInstaller hooks.
- **Improved:** Application resilience by implementing "Safe Imports" for all background components.

## [5.4.6] - 2026-04-19

### Fixed (Deep Dependency Bundling)

- **Fixed:** Missing `wsproto`, `bidict`, and `h11` libraries in standalone binaries by implementing deep collection hooks.
- **Improved:** Build system reliability by recursively collecting all sub-modules for the SocketIO stack.
- **Added:** Tracking for `wsproto` and `bidict` in the startup "Dependency Splash" log.

## [5.4.5] - 2026-04-19

### Changed (Port Diversification)

- **Changed:** Migration of all application network traffic from Port 5000 to Port 5051 to avoid system conflicts.
- **Fixed:** "Server Offline" issues caused by port occupation on common developer ports.
- **Improved:** Auto-launcher reliability by specifically targetting the new dedicated port range.

## [5.4.4] - 2026-04-19

### Fixed (Total Infrastructure Stabilization)

- **Added:** Diagnostic Splash at boot (Logs all library versions to `operations.log`).
- **Added:** Port Probe (Verifies Port 5000 is free before server start).
- **Added:** Frontend-visible error codes for SocketIO handshake failures.
- **Improved:** Protocol stability by hardening ping/pong timeouts and intervals.
- **Fixed:** Missing EngineIO hidden imports in the build spec for enhanced binary stability.

## [5.4.3] - 2026-04-19

### Fixed (Transport & "Server Offline" Issues)

- **Fixed:** "Server Offline" state by forcing Long Polling as a base transport layer.
- **Added:** UI feedback for the active transport method (Polling/WebSocket).
- **Added:** Deep diagnostics logging for Engine.IO/SocketIO in `logs/operations.log`.
- **Improved:** Server bootstrap stability with `allow_unsafe_werkzeug` for bundled EXEs.

## [5.4.2] - 2026-04-19

### Fixed (Handshake & Socket Stabilization)

- **Fixed:** Race condition in "Connecting..." state by moving WebSocket initialization to page-load.
- **Added:** "Server Status" visual indicator to verify backend health before allowing CLI operations.
- **Fixed:** Handshake message loss by implementing "Double-Emit" logic (Room + SID).
- **Improved:** UX by safety-locking the "Connect" button until the server is confirmed ready.

## [5.4.1] - 2026-04-19

### Fixed (Resilience & "Connecting" Hangs)

- **Fixed:** Eternal "Connecting..." state by implementing stable SocketIO Rooms based on `session_id`.
- **Added:** Pre-Flight TCP Probe with 2s timeout to catch host/firewall issues instantly.
- **Improved:** Handshake speed by explicitly disabling GSSAPI and DNS lookups in Paramiko.
- **Improved:** Connection resiliency across socket stutters/reconnects.

## [5.4.0] - 2026-04-19

### Changed (Major Architectural Overhaul — "Streaming Shell")

- **Replaced:** Netmiko Scripting Engine with raw Paramiko `invoke_shell()` for the CLI Terminal.
- **Added:** Bi-directional byte streaming for zero-latency interactivity (keystroke passthrough).
- **Added:** Background `ShellReader` thread per session to handle real-time terminal output.
- **Added:** Terminal resize synchronization (PTY resize) to match xterm.js dimensions.
- **Removed:** Synchronous "wait for prompt" logic that caused terminal hangs.

## [5.3.3] - 2026-04-19

### Fixed (Critical — "Infinite Spin" Resolved)

- **Fixed:** Resolved a `NameError` in the background connection task that caused the thread to die silently.
- **Added:** Background watchdog to intercept crashes and report them to the UI.
- **Added:** Real-time log streaming from Netmiko handshake to the terminal window.
- **Added:** Detailed SSH session logging to `logs/ssh_debug_[session_id].log` for deep troubleshooting.

## [5.3.2] - 2026-04-19

### Fixed (CLI Connection Hangs & Progress UX)

- **Fixed:** SSH connection "stuck on connecting" by wrapping the handshake in a hard 45-second wall-clock timeout via `ThreadPoolExecutor`.
- **Fixed:** Eliminated `find_prompt()` and `enable()` during initial connection to prevent infinite hangs on unusual banners or MOTDs.
- **Fixed:** Enabled `fast_cli=True` to reduce `netmiko` internal polling delays.
- **Fixed:** Removed invalid `read_timeout` from `send_command()` which was causing crashes in `netmiko 4.1.2`.
- **Added:** Real-time `cli_progress` status updates streamed to the terminal UI during the connection phase.

## [5.3.1] - 2026-04-19

### Fixed (Critical — CLI Terminal Fully Non-Functional)

- **Root cause #1:** `flask-socketio` was never installed. CLI WebSocket layer silently disabled on startup; terminal appeared to connect but no SSH was ever initiated.
- **Root cause #2:** `telnetlib_compat` shim not loaded before `netmiko` in `cli_manager.py` — caused silent `ImportError` on Python 3.13+.
- **Root cause #3:** `disabled_algorithms` override for Paramiko 4.x missing from `cli_manager.py` ConnectHandler — SSH rejected by legacy devices.
- **Root cause #4:** `socket.io.min.js` loaded from CDN — terminal broken in offline/air-gapped environments.
- **Root cause #5:** `initSocket()` called on every connect attempt — multiple stacked WS connections.
- **Fix:** `modules/cli_manager.py` fully rewritten with all corrections applied.
- **Fix:** `socket.io.min.js` now bundled locally in `static/js/`.
- **Fix:** `requirements.txt` updated with `flask-socketio`, `python-engineio`, `simple-websocket`.

## [5.3.0] - 2026-04-19

### Fixed

#### CLI Terminal Synchronization Fix
- **Fixed:** The "Phantom Disconnect" bug. Refactored the core Flask-SocketIO `cli_connect` and `cli_command` handlers to execute as strictly asynchronous background tasks (`socketio.start_background_task`). This decisively prevents the 30-second SSH negotiations from blocking the primary server event thread, ending the starvation of WebSocket heartbeat PINGs that forced the browser to incorrectly drop the connection early.
- **Fixed:** The stubborn `v5.1.0` web header label is resolved. The hardcoded version parameter deep in the `vlan_checker_web.py` render template has been unlinked from past builds.

## [5.2.0] - 2026-04-19

### Fixed

#### Deep CLI Terminal Stability
- **Fixed:** Instant crash caused by uninstantiated `self.device_type` when `cli_manager.py` spawns SSH processes. The CLI interface is now fully functional across all generic connections regardless of network platform type.
- **Fixed/Retained:** Legacy Paramiko backward compat overrides for offline switches.

### Internal & Cleanups
- **Removed:** Deep workspace cleanup. Cleared over 100MB of legacy specs (`v4.x` configs), duplicate `dist_backup` zips, and excessive QA log JSON dumps that littered the workspace.
- **Added:** Formal roadmap established in `docs/08_HISTORY/ROADMAP.md` covering subnets, monitoring, and compliance scanning for iteration v6.
- **Updated:** Compiled `NetworkSwissToolPro_v5_2_0_Offline.exe` build from SCRATCH.

## [5.1.0] - 2026-04-19

### Fixed

#### CLI Terminal Connection
- **Fixed:** Device type now correctly read from inventory file and passed to CLI connection
- **Fixed:** Connection dialog pre-populated with correct device type from inventory
- **Fixed:** Multi-platform support (NXOS, IOS, JUNOS) working correctly with platform-specific connection parameters
- **Fixed:** Encryption errors handled gracefully with automatic retry using legacy settings
- **Fixed:** Backwards compatibility for older OS versions (IOS 12.x, JUNOS 12.x, etc.)
- **Fixed:** Connection timeout and error handling improved

#### UI/UX
- **Fixed:** "Made by AI IDE" branding now properly visible in header with professional styling
- **Fixed:** Branding appears on all pages (main UI and CLI terminal)
- **Fixed:** Connection feedback messages added for better user experience

#### Metadata
- **Fixed:** Compile date updated to 2026-04-19
- **Updated:** Version to 5.1.0 across all files

### Added

#### API
- **Added:** `/api/get_device_type` endpoint to fetch device type from inventory
- **Added:** Inventory parsing function with support for section headers

#### Technical
- **Added:** Platform-specific connection parameters (NXOS, IOS, JUNOS)
- **Added:** Automatic encryption error detection and legacy mode retry
- **Added:** Connection logging and status feedback

**Full details in [RELEASE_NOTES_5.1.0.md](RELEASE_NOTES_5.1.0.md)**

## [5.0.0] - 2026-04-17

### Added

#### CLI Terminal Interface (Major Feature)
- **Web-based SSH terminal** for interactive device access
- **"Connect via CLI" button** in Single Device mode
- **Real-time terminal** using xterm.js via CDN
- **WebSocket communication** via Flask-SocketIO
- **Multiple concurrent sessions** - one per device
- **Privacy-first design** - terminal content NOT logged
- **Auto-disconnect** after 10 minutes idle
- **Session recovery** with reconnect option

**New Files:**
- `modules/cli_manager.py` - SSH session management
- `modules/web/templates/cli_terminal.html` - Terminal UI

**Modified Files:**
- `vlan_checker_web.py` - Added WebSocket routes and SocketIO
- `modules/web/templates/index.html` - Added CLI button
- `requirements.txt` - Added flask-socketio dependency

### Fixed

#### Syntax Error in vlan_mgmt.py
- **Fixed:** Unclosed parenthesis in JUNOS ELS detection (line 22)
- Changed nested double quotes to single quotes for command string

#### Topology Mapper HTML Generation
- **Fixed:** `generate_topology_html()` missing `extra_header` parameter
- Added `extra_header=""` default parameter and template usage

### Improved

#### JUNOS Compatibility
- **Enhanced:** ELS/Non-ELS VLAN syntax detection
- **Added:** SRX firewall MAC trace support (`show arp`)
- **Validated:** Full compatibility across EX, QFX, SRX, MX series
- **Documented:** Complete JUNOS compatibility matrix

## [4.5.8] - 2026-04-16

### Fixed

#### Topology Mapper JavaScript Bug
- **Fixed:** "dict object has no attribute 'upper'" error in Standard Map and vPC Map
- **Root Cause:** JavaScript in `index.html` was passing object `{map_mode: 'all'}` instead of string `'all'`
- **Fix:** Changed `onclick="runAction('topology', {map_mode: 'all'})"` to `onclick="runAction('topology', 'all')"`
- **Files Modified:** `modules/web/templates/index.html` (lines 477, 482)
- **Both buttons fixed:** Standard Map (`'all'`) and vPC Map (`'vpc'`)

## [4.5.7] - 2026-04-14

### Fixed

#### Thread Error Handling
- **Fixed:** Tasks getting stuck immediately (ping/SSH check, MAC search, maps)
- Added try-except wrappers around all thread functions in `vlan_checker_web.py`
- Added explicit "Starting..." and "Complete" logging for all operations
- Added critical error logging with full traceback for debugging

#### Connection Disconnect Logging
- **Added:** Explicit disconnect logging across all network operations
- New `safe_connection()` context manager in `network_base.py` for guaranteed cleanup
- All modules now log "Connecting to device...", "Successfully connected", "Logging out...", "Successfully logged out"
- `vlan_audit.py` - Added `log_func` parameter with full disconnect logging
- `mac_trace.py` - Added `log_func` parameter with full disconnect logging
- Proper try-finally blocks ensure disconnect always happens even on errors

### Added

#### Connection Context Manager
- **New:** `safe_connection()` context manager in `modules/network_base.py`
- Ensures connections are always properly closed
- Provides consistent logging for all connection lifecycle events

## [4.5.2] - 2026-04-14

### Added - Production Hardening Release

#### Structured Logging System
- **New Module**: `utils/structured_logger.py` - Production-grade JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Operation tracing with device context and parameters
- Config state tracking (PENDING → PUSHED → VERIFIED → COMMITTED)
- Three log streams: operations.log, errors.log, audit.log
- Legacy-compatible adapter for GUI/Web integration

#### Configuration Backup System
- **New Module**: `utils/config_backup_system.py` - Automatic config backup management
- Per-device backup storage: `backups/devices/{hostname}/`
- Automatic pre-change backups for all VLAN mutations
- Backup manifest with metadata (hash, size, trigger reason)
- 24-hour backup health monitoring with CLI check
- Diff comparison and rollback capability
- Keeps last 50 backups per device (auto-cleanup)

#### Production VLAN Management
- **New Module**: `modules/vlan_mgmt_production.py` - Enterprise-grade VLAN operations
- Idempotent operations (skips if desired state already exists)
- VLAN ID validation (1-4094, reserved VLAN detection)
- Post-change verification (automatic validation)
- Enhanced dry-run mode with exact command preview
- Config state logging and backup tracking
- Rollback suggestion on failure

#### Smoke Test Framework
- **New Module**: `tests/smoke_tests.py` - Automated test suite
- 11 test categories: infrastructure, data, network, integration
- CLI test runner: `python main.py test`
- Category-based test selection
- Result validation and reporting

#### CLI Enhancements
- New command: `python main.py test` - Run smoke tests
- New command: `python main.py cli --task backup-check` - Check backup health
- Integrated startup logging initialization

#### Documentation Updates
- Updated `docs/MASTER_DOCUMENTATION.md` with new architecture
- Created `RELEASE_NOTES_4.5.2.md` with comprehensive release details

### Changed
- `modules/adapters.py` - Integrated structured logging and production VLAN module
- `main.py` - Added test mode and backup-check task, initialized structured logging
- `VERSION` - Updated to 4.5.2

### Backward Compatibility
- **100% backward compatible** - No breaking changes
- All existing CLI commands work unchanged
- Existing GUI/Web interfaces function identically
- Legacy logging continues to work alongside new structured logging

## [4.5.1] - 2026-04-13
### Fixed
- Added visible Save Device Config quick-access button directly in the GUI VLAN Management tab.
- Verified Web runtime version banner/API reports 4.5.1 and includes save_config action in UI payload.

## [4.5.0] - 2026-04-13
### Added
- **VLAN Dry-Run Mode**: Added dry-run execution for VLAN add/rename/delete in both GUI and Web UI to preview commands without sending configuration changes.
- **Pre-Change Snapshot**: VLAN mutating operations now automatically capture per-device pre-change VLAN configuration snapshots into timestamped directories.
- **Post-Change Verification**: VLAN mutating operations now validate expected state after execution (present after add/rename, absent after delete) and log explicit verification results.

### Changed
- **VLAN Adapter Pipeline**: Enhanced shared adapter workflow to log command plans, dry-run behavior, verification status, and snapshot output paths.
- **Version Update**: Bumped runtime and release version to `4.5.0`.

## [4.4.0] - 2026-04-13
### Added
- **Save Config Feature**: Added a dedicated `save_config` workflow to persist device config using the active scope model (Single/Bulk/Group) in both GUI and Web editions.
- **Config Persistence Module**: Added `modules/save_config.py` to centralize Cisco/NX-OS startup save and Juniper commit behavior under the standard JSON contract.

### Changed
- **VLAN Operational Logging**: VLAN add/rename/delete now clearly logs whether changes are already persisted (Junos commit) or still running-only (Cisco startup save pending).
- **Web Version Alignment**: Updated web backend runtime version metadata to `4.4.0`.
- **Template Path Reliability**: Updated web app and build script to use `modules/web/templates` for local runtime and PyInstaller bundling.

## [4.3.0] - 2026-04-12
### Added
- **Centralized Router (`main.py`)**: Introduced a unified entry point for the entire system supporting GUI, Web, and CLI modes.
- **Headless CLI Core**: Enabled non-interactive task execution (Backup, Audit, Connectivity) via `python main.py cli`.
- **System Environment Validation**: Added pre-boot checks to ensure critical inventory and directory structures exist.
- **Dependency Consolidation**: Centralized inventory parsing logic into `modules/network_base.py`.

### Changed
- **Refactored Entry Points**: `vlan_checker_gui.py` and `vlan_checker_web.py` are now modular and importable as libraries.
- **Updated Dependencies**: Added Flask to `requirements.txt` and pinned Netmiko for production stability.

## [4.2.0] - 2026-04-12
### Changed
- **Major Architectural Refactor**: Fully decoupled business logic from the GUI (`vlan_checker_gui.py`) and Web (`vlan_checker_web.py`) monoliths.
- **Adapter Layer Implementation**: Centralized all workflow orchestration into `modules/adapters.py`, eliminating ~1,000 lines of duplicated networking code.
- **Side Effect Isolation**: Moved all file I/O, report formatting, and HTML/CSV generation to `utils/report_formatter.py`.
- **Standardized JSON Contract**: Enforced strict adherence to JSON-based communication between the UI and the network modules.
- **Cleaned Codebase**: Removed all Netmiko/Paramiko imports and monolithic thread bodies from the main interface scripts.

## [4.1.1] - 2026-04-09
### Added
- **Operational Master Prompts (OPMP)**: Initialized core operations framework in `docs/OPERATIONAL_PROMPTS/` with `QA.md`, `BUILD.md`, and `BACKUP.md`.
- **System Governance**: Enforced strict production engineering lifecycle rules including mandatory backups, versioning, and changelog maintenance.

## [4.0.0] - 2026-04-09
### Internal
- Conducted full system code audit.
- Created `docs/MASTER_DOCUMENTATION.md` to serve as the single source of truth for architecture and usage.
- Enforced system lifecycle governance policies.

## [3.1.0] - 2026-02-26
### Added
- **Node Blacklist**: Automatically filters out non-hostname strings (e.g., `password`, `login`, `username`) from the topology map.
- **Premium Node Dashboards**: Redesigned infographic popups with status icons (✅/❌), connection summaries (Active/Total), and improved typography.
- **Multi-Link Grouping**: Improved table layout for nodes with multiple logical and physical connections.

### Fixed
- **Prompt Sanitization**: Hardened hostname extraction to strip trailing punctuation (`#`, `>`, `:`) ensuring clean node labels.

## [3.0.0] - 2026-02-26
### Changed
- Juniper & Cisco Command Refined
- Robust Interface Metadata Parsing
- Infographic Topology & Dual-View
- vPC & Enhanced Topology Mapping
- Topology & UX Overhaul

## [2.5.0] - 2026-02-26
### Changed
- Web Focused Enhancements

## [2.4.0] - 2026-02-26
### Added
- Code Audit & Documentation Release
- Created `QA_TESTING_CHECKLIST.txt` for manual testing
- Created `README.md` with architecture, features, and version history
### Removed
- Removed duplicate `import os` in web backend

## [2.3.0] - 2026-02-26
### Added
- Added Group dropdown filter to Web UI (parity with Desktop)
### Fixed
- Restored missing `connectivity`, `vlan_check`, `mac_check` in web thread router
- Fixed stale variable references (`enb`→`enb_pwd`, `d`→`data`) in web API handler
- Fixed `NameError: unique_nodes` in GUI topology mapper (should be `uniq_nodes`)
- Fixed web topology: `uniq_nodes` was overwritten with empty `set()` after population

## [2.2.0] - 2026-02-26
### Fixed
- Flask template routing for PyInstaller bundles (`sys._MEIPASS`)
- CSV audit now uses `conn.find_prompt()` for real hostname extraction
- Full regex parsing for OS Version, Serial Number, Model in web audit
- Topology mapper injects target node regardless of CDP/LLDP response

## [2.1.0] - 2026-02-25
### Changed
- Web UI Overhaul: MacOS-inspired glassmorphism design
- Complete feature parity: all 11 actions available in web edition
- Target Scope Engine with Bulk/Single/Group/Text filtering
- VLAN Compare, Interfaces tab, Config Backup added to web

## [2.0.0] - 2026-02-25
### Added
- Web Edition Created: Flask-based web application with HTML/JS frontend
- Separate PyInstaller build (`VlanCheckerWeb.exe`)
- Auto-launches browser on startup
- Session file logging

## [1.9.0] - 2026-02-08
### Added
- Topology Mapper with Vis.js interactive physics diagrams
- Network Audit exporting to CSV
- `safe_node_name()` for IP/hostname deduplication
- VLAN Compare Analysis with global baseline

## [1.8.0] - 2026-02-01
### Added
- VLAN Operations: Add/Rename/Delete VLAN with pre-check and confirmation dialogs
- Cisco config save and Juniper commit after changes
- Detailed per-device logging for all CRUD operations

## [1.7.0] - 2026-02-01
### Added
- Foundation: Connectivity & Authentication checker
- VLAN database audit with raw + parsed reports
- MAC Address tracer across network
- Group-based inventory filtering
- Enable Password support for Cisco IOS privilege escalation
- Thread-safe GUI with Queue-based logging
