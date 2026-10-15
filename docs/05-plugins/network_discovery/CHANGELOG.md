# Changelog — Network Discovery & Crawl Plugin

# Purpose
Maintains detailed change records of all revisions made to the Network Discovery & Crawl plugin.

# Scope
Comprehensive historical ledger of modifications.

---

## [1.1.1] - 2026-05-31
### Fixed
- **Live crawl seed init**: `for host, dtype, _ in seeds` → `for host, dtype in seeds` (seeds are 2-tuples; depth is queue-only). Fixes Discovery on a single device with real SSH.

## [1.1.0] - 2026-05-31
### Added
- Multi-seed BFS, demo mode, Discovery tab API, IOS/NX-OS/Junos parsers (shipped with app v6.9.23).

## [1.0.0] - 2026-05-26
### Added
- First public release of `network_discovery` plugin.
- Added Cisco IOS/NXOS CDP parsing (`_parse_cisco_cdp_detail`).
- Added Cisco IOS/NXOS LLDP parsing (`_parse_cisco_lldp_detail`).
- Added Juniper Junos LLDP parsing (`_parse_juniper_lldp_detail`).
- Built Vis.js offline-bundled HTML graph rendering under `reports/discovery/`.
- Created dynamic JSON backup `discovered_inventory.json` inside the application root directory.
