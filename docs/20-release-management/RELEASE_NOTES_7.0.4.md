# Release Notes — Network Swiss Tool Pro v7.0.4

**Date:** 2026-05-24  
**Artifact:** `NetworkSwissToolPro_v7.0.4_OFFLINE.exe`

## Highlights

1. **Discovery Command Center** — Offline light-theme HTML with Overview (device table + topology map), Link inventory, and Summary.
2. **Discovery tab (in-app)** — Live crawl progress, scan-state badges, hop/state filters, crawl log viewer.
3. **VPC topology fix** — Maps always receive fixed coordinates; no-vPC-domain runs show physical adjacency with a clear banner.

## Discovery

- New module `utils/discovery_map_shell.py`.
- Vis payload encodes scan state (scanned / seed / neighbor-only / failed), hop labels, CDP vs LLDP edge colors.
- Demo: `python create_demo_discovery_map_v7.py` → `DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html`.

## VPC

- `_ensure_vpc_nodes_positioned` grid layout when domain anchors are missing.
- Adjacency fallback when `vpc_domains` is empty (edges visible, banner in header).
- Swiss Tools status shows node/edge/domain counts and adjacency-fallback warning.
- Demo: `python create_demo_map_v7.py` → `DEMO_VPC_TOPOLOGY_v7.0.4.html`.

## Upgrade

Replace prior EXE; `VERSION` file reads `7.0.4`. No database migration.

## QA gates

- `_prebuild.py` (includes discovery + VPC node position contracts)
- `_master_qa_test.py`
- `tests/test_discovery_map_html_contract.py`
- `tests/test_vpc_map_html_contract.py`
