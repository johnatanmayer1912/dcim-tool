# UI/UX Documentation

| Field | Value |
|-------|-------|
| **Application Version** | 7.0.51 |
| **Last Updated** | 2026-06-18 |
| **Owner** | UI/UX + R-LIB |

---

## Shipped features (code-synced)

| Feature | Document | Status |
|---------|----------|--------|
| **Standard L2 Map shell** | [standard-map-shell.md](standard-map-shell.md) | **Canonical** — v7.0.49–7.0.51 |
| Visualization pipeline | [../01-architecture/visualization-pipeline.md](../01-architecture/visualization-pipeline.md) | vPC + Standard Map |
| UI philosophy | [ui-philosophy.md](ui-philosophy.md) | Design principles |
| Topology troubleshooting | [../07-operations/TOPOLOGY_ISSUES.md](../07-operations/TOPOLOGY_ISSUES.md) | Standard Map + vPC |

---

## Design mockups (pre-ship exploration)

Static HTML concepts in [`mockups/`](mockups/):

| Index | Purpose |
|-------|---------|
| [standard-map-demo-index.html](mockups/standard-map-demo-index.html) | Briefing board, twin-pane, connection index concepts |
| [standard-map-viz-demo-index.html](mockups/standard-map-viz-demo-index.html) | Tier, Radial, Focus, Schematic (+ matrix — **not shipped**) |

**Shipped implementation:** Briefing + Tier default + twin-pane + connection index (see [standard-map-shell.md](standard-map-shell.md)).

---

## Legacy design options (Swiss Tools shell)

Historical alternatives for the main web UI — not the topology export shell:

- `option-1-modern-minimalist.html` through `option-6-topology-focused.html`

See folder README sections below for option summaries.

---

## Design philosophy

- **Enterprise-first:** Professional, clean, efficient interfaces for NOC/NetEng
- **Accessibility:** High-contrast legend pills, offline-safe explicit colors (Standard Map v7.0.51)
- **Offline:** No CDN dependency in exported topology HTML
- **User-centric:** Map + connection index side-by-side; descriptions in index, not on canvas

---

## Next steps for contributors

1. Read [standard-map-shell.md](standard-map-shell.md) before changing `utils/standard_map_shell.py`
2. Update [visualization-pipeline.md](../01-architecture/visualization-pipeline.md) on export behavior changes
3. Run `tests/test_standard_map_v7049.py` after UI contract changes
