# Standard L2 Map — NOC Shell (v7.0.49–7.0.51)

| Field | Value |
|-------|-------|
| **Purpose** | Canonical UX/behavior reference for Standard Map (`map_mode=all`) |
| **Scope** | Split-pane layout, map styles, connection index, offline HTML export |
| **Application Version** | **7.0.51** |
| **Last Updated** | 2026-06-18 |
| **Owner** | R-LIB + UI/UX |
| **Code** | `utils/standard_map_shell.py`, `utils/report_formatter.py`, `modules/adapters.py` |

---

## Product rules

1. **Map + connection index always visible** — no tab-only link inventory for Standard Map.
2. **Map styles:** Tier (default), Radial, Focus (1–2 hop), Schematic. **No matrix view.**
3. **Offline-safe** — Vis.js embedded inline; explicit CSS colors (no undefined CSS variables).
4. **Descriptions off canvas** — full WHO/HOW/WHAT in tooltips and connection index detail panel.

---

## Layout

```
┌─ nst-top-chrome ─────────────────────────────────────────┐
│ Title · stats · search · Show port labels · legend pills │
└──────────────────────────────────────────────────────────┘
┌─ map column (60%) ────────┬─ nst-conn-panel (40%) ───────┐
│ Map style bar             │ Briefing KPIs                 │
│ Vis.js #mynetwork         │ Connection index table        │
│                           │ Selected link detail          │
└───────────────────────────┴───────────────────────────────┘
```

---

## Key modules

| Module | Role |
|--------|------|
| `standard_map_shell.py` | CSS, top chrome HTML, connection panel, client JS (`nstBootStandardMap`, `nstSetMapStyle`, …) |
| `report_formatter.py` | `generate_topology_html()` — injects shell when `map_mode=='all'` |
| `topo_map_shell.py` | `link_rows_from_edges()` — connection index rows |
| `adapters.py` | `run_topology_mapper()`, `_finalize_standard_map_edges()` — peer-link upgrade/synthesis |

---

## Map canvas labels (v7.0.51)

| Element | Default on canvas | Full detail |
|---------|-------------------|-------------|
| Nodes | Hostname only | Tooltip: role, port badges |
| Edges | Empty label | Tooltip + connection index; toggle **Show port labels** for short port text |
| Peer-link | Purple thick edge (`#a55eea`, width 10) | Type badge **Peer** in index |

---

## Peer-link pipeline

1. Phase 2 edges built from CDP/LLDP + vPC metadata.
2. `_finalize_standard_map_edges()` (Standard Map only):
   - Upgrade edges between same-domain peers when port matches `vpc_details` peer-link or `vpc_structured.peer_link_po`.
   - Upgrade or synthesize for two-member domains missing a dedicated peer-link edge.

---

## Connection index columns

Local · Port · Remote · Port · **Type** · VLAN · Speed

Type badges: Peer, Po, vPC, L2, Uni (asymmetric).

---

## Search

- Top chrome `#searchInput` and panel `#nst-conn-filter` stay in sync.
- Filters connection table and calls `searchNodes()` for map dim/highlight.

---

## Mockups (design exploration)

Pre-ship concepts in [`mockups/standard-map-demo-index.html`](mockups/standard-map-demo-index.html) and [`mockups/standard-map-viz-demo-index.html`](mockups/standard-map-viz-demo-index.html). **Shipped implementation** follows Briefing + Tier + twin-pane + connection index (no matrix).

---

## Related documents

- [visualization-pipeline.md](../01-architecture/visualization-pipeline.md)
- [TOPOLOGY_ISSUES.md](../07-operations/TOPOLOGY_ISSUES.md)
- [UTILITIES_DOCUMENTATION.md](../02-codebase/UTILITIES_DOCUMENTATION.md)
- [RELEASE_NOTES_7.0.51.md](../20-release-management/RELEASE_NOTES_7.0.51.md)

---

## QA

- `python -m pytest tests/test_standard_map_v7049.py -q`
- Manual: offline EXE → Standard L2 Map → verify legend contrast, peer-link visibility, no description clutter.
