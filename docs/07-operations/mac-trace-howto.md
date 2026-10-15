# MAC trace — how to use (v7.0.29+)

## What it is

**Inventory-wide MAC trace**: for each device in your selected scope, the tool runs `show mac address-table` (or platform equivalent) and records where the MAC appears.

This is **not** automatic CDP/LLDP hop-by-hop tracing to the core router. It is a **per-switch path table** across devices you already manage.

## Where in the UI

1. Open **Network Search** tab (`#tab-diag`). v7.0.7+: live progress bar, tab badge, and last-report restore when you return to this tab.
2. Section **MAC Address Search**.
3. Enter MAC (formats like `aa:bb:cc:dd:ee:ff`, `aabb.ccdd.eeff`, etc.).
4. Click **Trace Address** (runs `mac_check` action).

## After the trace

- Live log shows progress; on **MAC Trace Complete**, the **Path summary** table loads.
- **View path report (HTML)** → `/api/mac-trace/report` (offline file from `utils/mac_trace_formatter.py`).
- JSON: `GET /api/mac-trace/last`
- Files are saved under `reports/mac_trace/<YYYYMMDD>/<run_id>/` (`report.txt`, `report.html`, `manifest.json`). See [network-search-reports-guide.md](network-search-reports-guide.md).

## How to test (offline / lab)

1. Ensure `inventory.txt` lists lab switches (or use demo inventory).
2. Set sidebar targets (All / group / selected hosts).
3. Enter a MAC known on one access port.
4. Run trace; confirm one row with switch hostname, VLAN, interface.
5. Open HTML report and verify `path_hops` order matches inventory scan order.

## Platform notes (v7.0.29+)

Backend normalization lives in `utils/mac_utils.py` (`cisco_search_terms`, `junos_search_terms`, `normalize_mac_hex`).

| Platform | Command(s) | MAC format used in filter |
|----------|------------|---------------------------|
| Cisco IOS / IOS-XE | `show mac address-table \| include` | Cisco dotted `aabb.ccdd.eeff` (auto-converted from colon/dash input) |
| Juniper EX/QFX | `show ethernet-switching table \| match` (+ fallbacks) | Colon `aa:bb:cc:dd:ee:ff` |
| Juniper SRX | `show arp \| match` | Colon or hex |
| NX-OS / IOS-XR | `show mac address-table \| include` | Cisco dotted |

Input formats accepted: `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`, `aabb.ccdd.eeff`, partial hex.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| MAC found manually on IOS-XE but not in web search | Pre-v7.0.28: colon format not converted to dotted. Upgrade to v7.0.28+. |
| Juniper QFX shows MAC in CLI but trace fails | Ensure `device_type` is `juniper_junos`. v7.0.28+ tries `ethernet-switching`, `mac-ip-table`, and legacy `bridge mac-table`. |
| Hostname column shows `password`, `username`, or other login words | Stale SSH prompt text was used as the hostname (v7.0.4+ uses `show version` / switchname and rejects auth prompts; re-run trace on current build). |
| Wrong name after many devices | Same as above, or prompt not ready — row should show management IP if parse fails. |

## Code references

- `modules/mac_trace.py` — SSH collection per device
- `utils/mac_utils.py` — MAC normalization and vendor search terms
- `vlan_checker_web.py` — `_mac_check_thread`, APIs
- `utils/mac_trace_formatter.py` — HTML report
