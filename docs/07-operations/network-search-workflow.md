# Network Search — operational workflow (v7.0.9+)

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Operational guide for the **Network Search** tab (UI; internal pane id `diag`). |
| **Former name** | `search_it` (renamed v7.0.9 for clarity). |
| **Version Awareness** | v7.0.29 |

## Tab: Network Search

First tab in the web UI. Tools:

- **MAC Address Search** — trace MAC across inventory (`mac_check` / MAC trace module).
- **Description Search** — regex or substring on interface descriptions/names (`description_search`).
- **Network Ping Scan** — subnet ping sweep (`ping_scan`).

### Description Search

- **Action API:** `description_search`
- **Input:** String or regex in the Description Search box
- **Behavior:** Regex (case-insensitive) with substring fallback; searches descriptions and interface names on NX-OS, IOS, JunOS; command fallback per platform (see v6.9.x notes in CHANGELOG).
- **Reports:** `reports/description_search/<YYYYMMDD>/<run_id>/` — see [network-search-reports-guide.md](network-search-reports-guide.md).

### MAC Address Search

See [mac-trace-howto.md](mac-trace-howto.md).

### Network Ping Scan

Writes under `reports/ping_scan/`. Progress and last-run APIs match MAC/Description search.

## Related

- [Network Search reports layout](network-search-reports-guide.md)
- [MAC trace how-to](mac-trace-howto.md)
