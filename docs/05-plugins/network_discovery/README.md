# Network Discovery & Crawl Plugin

**Plugin version:** bundled with platform **7.0.29+**  
**Last doc sync:** 2026-06-10

### v7.0.29 parser fixes
- Cisco LLDP brief: correct column order (`Local Intf` / `Neighbor` / `Vlan`)
- Cisco LLDP detail: `_lldp_resolve_remote_port()` normalizes MAC-as-port-id to interface name
- Junos LLDP: removed bare `:` fallback; safe `xe-`/`ge-` header regex after `Local Interface` split (NEW-H5)
- `merge_nodes()`: serial-number union prevents short-hostname collisions (NEW-M2)

# Purpose
The **Network Discovery & Crawl Plugin** is designed to recursively crawl and discover network devices and physical neighbor connections starting from a single seed device. It automatically builds a physical neighbor inventory and creates a high-fidelity Vis.js topology map of the crawled scope.

# Scope
- **Platforms**: Cisco IOS, IOS-XE, NX-OS, and Juniper Junos.
- **Protocols**: CDP, LLDP, or Both.
- **Crawl Depth**: 1 to 3 hops.

# Dependencies
- **modules/network_base.py**: Connection management and authentication hooks.
- **utils/report_formatter.py**: Saving reports and registration.
- **vis-network.min.js**: Local/Offline JavaScript topology visualizer.

# Related Documents
- [Plugin System Mandate](../../05-plugins/ui-philosophy.md)
- [LIBRARIAN Prime Directive](../../00-overview/LIBRARIAN_MANDATE.md)

# Operational Impact
- **Safe Operations**: Read-only command execution (`show cdp neighbors detail`, `show lldp neighbors detail`). Does not modify running configuration.
- **Credential Reuse**: Uses the active credentials in the user sidebar to connect to all hops.

# Failure Conditions
- **Authentication Failures**: Skipped automatically with error logs to prevent account lockout.
- **Routing/Unreachable Neighbors**: Logged and skipped gracefully.

# UI (Discovery tab)
- **Tab**: Discovery in main web UI (`modules/web/templates/index.html` → `#tab-discovery`).
- **Demo mode**: Checkbox runs synthetic IOS/NX-OS/Junos lab without SSH (offline validation).
- **Live crawl**: Seeds + sidebar credentials → `/api/discovery/run` → poll status → table + topology map.
- **Hostname (v1.2.0)**: `resolve_device_hostname()` — SSH prompt and NX-OS `Device name:` / `switchname`, not full `show version` banner.
- **Map report (v6.9.28+)**: HTML opens on **Link Inventory**; **Topology Map** tab uses fixed layout, physics off (`utils/discovery_map_formatter.py` → `utils/topo_map_shell.py`).
- **Trust (v1.3.0 / app v7.0.1)**: `utils/discovery_graph.py` merges duplicate devices (IP/hostname aliases) and classifies OS without the `ex`-in-`nexus` bug (BUG-0007). Map labels: `NX-OS · model`. See [`discovery-trust-validation.md`](../../08-operations/discovery-trust-validation.md).

# Last Synchronization Timestamp
- **Date**: 2026-06-07
- **Version**: 1.8.0 (app **v7.0.29** — LLDP/parser fixes v7.0.29)
- **Maintainer**: Network Swiss Tool UI/UX & Automation Engineering Team

# Recent Changes (v1.8.0)
- **Critical JUNOS LLDP Fix**: Changed command order for Juniper devices to try 'show lldp neighbors' (brief) first, then 'show lldp neighbors detail' if needed. This fixes discovery failures on older Junos versions that don't support the detail command. Research from Juniper documentation confirmed that some versions only support the brief format.

# Recent Changes (v1.7.0)
- **Deep Dive Enhancements**: Added comprehensive parser regression testing for edge cases, enhanced offline environment validation with health check integration, improved duplicate device detection for VPC peer correlation, added user error prevention documentation, enhanced fallback mechanisms for weird scenarios including malformed output, non-standard formats, and legacy device versions
- **Parser Regression Tests**: Added test_parser_regression.py with comprehensive test cases for CDP, LLDP, interface parsers, and VPC parsers
- **Offline Validation**: Enhanced health check system with offline validation checks and parser regression testing
- **VPC Duplicate Detection**: Added VPC peer correlation cache for automatic duplicate device merging
- **User Error Prevention**: Added comprehensive USER_ERROR_PREVENTION.md guide with instructions for safe operation

# Recent Changes (v1.6.0)
- **JUNOS LLDP and Interface Fixes**: Fixed 0 links found issue with table format parser for xe- interfaces
- **Comprehensive Fallbacks**: Added 4-tier fallback chain (standard→brief→table→alternative) for maximum compatibility
- **Interface Status Fix**: Fixed interface status unknown issue with Physical link Up/Down detection
- **xe- Interface Support**: Improved xe- interface support across all parsers for 10GbE interfaces
