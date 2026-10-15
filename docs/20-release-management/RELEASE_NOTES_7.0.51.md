# Release Notes — v7.0.51

| Field | Value |
|-------|-------|
| **Version** | 7.0.51 |
| **Date** | 2026-06-18 |
| **Artifact** | `NetworkSwissToolPro_v7.0.51_OFFLINE.exe` |
| **Spec** | `NetworkSwissToolPro_v7.0.51.spec` |

---

## Summary

Standard L2 Map UI/UX polish for NOC and NetEng: readable legend, no text overlap on the canvas, reliable vPC peer-link rendering, and unified search across map and connection index.

---

## Fixed

- **Missing vPC peer-link** — `_finalize_standard_map_edges()` upgrades inter-peer edges and synthesizes peer-links for two-member domains.
- **Text overlap** — Descriptions removed from canvas; tooltips + connection index hold full detail; optional **Show port labels**.
- **Black-on-black legend** — `nst-top-chrome` with high-contrast `nst-legend-pill` swatches; legacy legend hidden in Standard Map mode.
- **Duplicate chrome** — Legacy header/toolbar no longer render alongside the new Standard Map shell.
- **VPC Command Center** — Header build order fixed so `vpc-map-pane` embeds correctly.

---

## Changed

- Unified top chrome: search, device/link stats, legend, port-label toggle.
- Connection index: **Type** column with badges; peer-link rows highlighted.
- Search syncs map highlight (`searchNodes`) and connection table filter.
- Node canvas labels: hostname only; ports in tooltip.

---

## Tests

- `tests/test_standard_map_v7049.py` — peer-link finalize, HTML contract, link rows.

---

## Documentation

- [standard-map-shell.md](../06-ui-ux/standard-map-shell.md)
- [visualization-pipeline.md](../01-architecture/visualization-pipeline.md) (Standard Map section)
- Root [CHANGELOG.md](../../CHANGELOG.md)

---

## Upgrade

Replace prior offline EXE with `dist/NetworkSwissToolPro_v7.0.51_OFFLINE.exe`. No config migration required. Re-export Standard L2 Map HTML to pick up new shell.
