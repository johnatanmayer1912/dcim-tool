# Discovery Command Center (v7.0.4)

Offline HTML report for network discovery crawls. Open the generated `.html` in any modern browser (vis.js embedded; no CDN required).

## Opening the report

- **In-app:** Discovery tab → **Open Discovery Command Center** (after crawl completes).
- **Filesystem:** `reports/discovery/discovery_map_<timestamp>.html` from the crawl job.

## Tabs

| Tab | Content |
|-----|---------|
| **1 Overview** | Device table (hostname, IP, hop, scan state) + topology map |
| **2 Link inventory** | Sortable CDP/LLDP link table |
| **3 Summary** | Counts: scanned vs neighbor-only, hops, protocols |

## Visual legend

| Element | Meaning |
|---------|---------|
| Blue solid box | SSH scanned device |
| Purple / seed | Seed device |
| Gray dashed border | Neighbor-only (not SSH-scanned) |
| Amber border | SSH failed on that device |
| `H0:` / `H1:` label prefix | Hop depth from seed |
| Indigo edge | CDP |
| Teal edge | LLDP |
| Dashed edge | At least one endpoint not scanned |

Click a row in the device table to highlight the matching map node.

## In-app crawl (same release)

- Progress bar shows current host, hop, device/link counts, queue depth.
- **View crawl log** shows the last 20 log lines from the job.
- Filter results by hop, scan state, or search string.

## Demo

```bash
python create_demo_discovery_map_v7.py
```

Produces `DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html` for training and health-wizard checks.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Empty map | Ensure crawl found devices; open Overview tab and wait for `discBootMap` |
| All gray nodes | Normal if max depth reached before SSH to neighbors |
| Failed (amber) nodes | Credentials, ACL, or wrong `device_type` on seed line |
