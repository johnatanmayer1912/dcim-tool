# Discovery trust validation (v7.0.1)

Use this checklist after a Discovery crawl or before field deployment.

## Automated

```text
python tests/test_discovery_platform_classifier.py
python tests/test_discovery_graph_dedup.py
python tests/test_network_discovery.py
python _prebuild.py
```

## Map vs inventory

1. Open the latest `reports/discovery/discovered_inventory_*.json` (path logged at end of discovery).
2. Count unique `id` values in `nodes` — must match the Discovery map node count.
3. Every `edges[].from` / `edges[].to` must exist in `nodes[].id`.

## Platform labels

| Expectation | Check |
|-------------|--------|
| Scanned NX-OS | Map label shows `NX-OS · <model>`, not JunOS |
| Scanned IOS | `IOS · <model>` |
| Scanned JunOS | `JunOS · <chassis>` |
| Unscanned neighbor | Gray node; OS from CDP/LLDP until scanned |

## NX-OS LLDP link quality (v7.0.10+)

After scanning one Nexus seed, open **Link inventory** in the discovery report:

| Expectation | Bad (old parser) |
|-------------|------------------|
| **Local** = `Eth1/n` | `unknown` |
| **Remote** = peer interface or `n/a` | `null`, raw MAC in Remote column |
| **To** = hostname or normalized chassis MAC | `not` (from “not advertised”) |

Common NX-OS cases now handled: `Local Port id`, `System Name: not advertised`, missing system name (chassis id), `Port id` = MAC with `Port Description` = real interface.

## Duplicate device test

Three switches with two parallel links between a pair should show **3 nodes**, not 4+. Link Inventory may list multiple rows (one per port).

## Offline / low-spec PC

- Map opens on **Link Inventory**; switch to **Topology Map** only when needed.
- No external fonts; physics disabled (`enabled: false` in HTML source).

## Demo mode (no SSH)

Discovery tab → **Demo mode** → Run. Confirms offline HTML and classifier without lab hardware.

## EXE and audit cross-links

- Bare EXE plugin smoke: [`exe-smoke-checklist.md`](exe-smoke-checklist.md)
- Missing automated tests: [`audit-test-gaps.md`](audit-test-gaps.md)
- Full sweep: [`../14-bug-reports/W-BUG-SWEEP-2026-05-31-v702.md`](../14-bug-reports/W-BUG-SWEEP-2026-05-31-v702.md)
