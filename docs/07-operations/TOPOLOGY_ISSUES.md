# Topology Troubleshooting

> **Index:** [TS_ERROR_INDEX.md](TS_ERROR_INDEX.md) · [discovery-trust-validation.md](discovery-trust-validation.md) · [standard-map-shell.md](../06-ui-ux/standard-map-shell.md)

| Field | Value |
|-------|-------|
| **Application Version** | 7.0.51 |
| **Last Updated** | 2026-06-18 |

---

## Standard L2 Map (`map_mode=all`)

### Blank or white map (offline / older Chrome)

**Symptoms:** Empty white canvas, tiny map in corner, fallback never clears.

**Fix (v7.0.50+):** Explicit `#mynetwork` sizing, dark background, `nstBootStandardMap()` retry, keep fallback until Vis.js initializes. Re-export HTML from v7.0.50+ or use latest EXE.

**Verify:** Browser console (F12) — no undefined CSS var errors; `#mynetwork` has min-height ≥ 360px.

---

### Text overlap on edges

**Symptoms:** Long interface descriptions stacked on link labels.

**Fix (v7.0.51):** Canvas edge labels empty by default. Use edge tooltip or connection index. Optional **Show port labels** for short port names only.

---

### Legend unreadable (black on black)

**Symptoms:** Colored squares with dark text on dark background.

**Fix (v7.0.51):** Standard Map uses `nst-top-chrome` + `nst-legend-pill` (light text). Legacy `.legend` block is hidden. If you still see old legend, re-run topology export with v7.0.51+.

---

### Missing vPC peer-link

**Symptoms:** Two vPC peers connected but no purple peer-link edge.

**Fix (v7.0.51):** `_finalize_standard_map_edges()` upgrades existing inter-peer edges and synthesizes peer-link for two-member domains. Ensure `show vpc` / vPC metadata was collected. Check connection index for **Peer** badge row.

---

### Search does not highlight map

**Symptoms:** Search filters table but map unchanged.

**Fix (v7.0.51):** Top search calls `searchNodes()` via `nstFilterConnections()`. Use unified search in top chrome (not legacy toolbar — hidden in Standard Map).

---

## vPC Command Center (`map_mode=vpc`)

See [visualization-pipeline.md](../01-architecture/visualization-pipeline.md). Map container: `#mynetwork.vpc-map-pane` inside Command Center overview tab.

---

## General

- Re-export topology HTML after upgrading EXE.
- Diagnostics folder: `topology_diagnostics_*` under working directory.
- Tests: `python -m pytest tests/test_standard_map_v7049.py tests/test_vpc_map_html_contract.py -q`
