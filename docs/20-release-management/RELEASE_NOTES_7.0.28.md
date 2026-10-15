# Release Notes — v7.0.28 (2026-06-10)

## Summary

Fixes three production issues: MAC Address Search failing on IOS-XE Catalyst L3 switches, Juniper QFX/Junos MAC trace gaps, and Interface Map not correlating physical (`xe-`/`ge-`) with logical (`ae`) interfaces.

## Fixed

### MAC Address Search — IOS-XE Catalyst L3
- Web search passed user MAC format (e.g. `00:11:22:33:44:55`) directly to `| include`, while CAM tables use Cisco dotted notation (`0011.2233.4455`).
- Now normalizes to dotted format plus partial-hex fallbacks before SSH command execution.

### MAC Address Search — Juniper EX/QFX (Junos 14)
- Added colon-format search tokens for `show ethernet-switching table | match`.
- Fallback commands: `show ethernet-switching mac-ip-table`, legacy `show bridge mac-table`, full-table local filter.
- Parser handles `xe-0/0/0.0`, `ae0.0`, `default-switch` routing-instance rows, and `*` suffixes.

### Interface Map — Juniper physical ↔ logical
- Interface Manager discovers LACP/AE bundles (`show lacp interfaces` / `show aggregated-ethernet detail`).
- Member ports (`xe-`, `ge-`) linked to parent `ae` bundle in discovery data.
- Port Interface Map correlates MAC table logical units (`.0`) to physical interface keys.
- Web UI renders ae bundles with member count and indented member ports.

## Added

- `utils/mac_utils.py` — MAC normalization and vendor search terms
- `utils/juniper_iface.py` — Junos unit/bundle correlation helpers
- `tests/test_mac_trace_parsing.py` — 17 regression cases

## Artifact

- `NetworkSwissToolPro_v7.0.28_OFFLINE.exe`

## Test plan

1. IOS-XE L3: Search MAC using `aa:bb:cc:dd:ee:ff` format — confirm FOUND with correct VLAN/port.
2. Junos QFX: Search MAC known on `xe-0/0/N.0` — confirm FOUND.
3. Interface Manager on Junos with ae bundle — confirm ae card shows members, physical ports show `↳ ae0`.
4. Offline EXE smoke: Network Search MAC trace + Interface discover on lab inventory.
