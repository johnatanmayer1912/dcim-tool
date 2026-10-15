# Topology Map Diagnostic Package (v6.9.4+)

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Explain the per-run diagnostic folder created alongside vPC topology HTML maps. |
| **Scope** | File naming, data stages, and troubleshooting empty Member Interfaces panels. |
| **Related Documents** | [QA vPC Map](../09-qa/QA_VPC_MAP.md), [Visualization Pipeline](../01-architecture/visualization-pipeline.md) |
| **Update Responsibility** | Network Automation Engineer |
| **Version Awareness** | v6.9.4 |

---

## When the folder is created

Every **Topology Mapper** run (especially `map_mode=vpc`) creates:

`{app_working_directory}/topology_diagnostics_YYYYMMDD_HHMMSS/`

The HTML map is written **inside this folder**, not the project root.

---

## File guide (read in order)

| File | Stage | Contents |
|------|--------|----------|
| `00_README.txt` | — | Navigation index for humans |
| `vpc_map_data_TEMPLATE.json` | Template | Editable schema for lab/production data injection |
| `01_raw_node_metadata.json` | Post-SSH | Per-device `vpc_structured`, `vpc_member_interfaces`, `port_channel_detail` |
| `02_pre_transform_edges.json` | Pre-vPC | Raw CDP/LLDP adjacency |
| `03_post_transform_edges.json` | Post-vPC | `vpc_shared` / `vpc_orphan` edges with `bundled_links` |
| `04_final_map_data.json` | Pre-HTML | Exact `nodes` + `edges` embedded in Vis.js |
| `06_pre_render_presentation.json` | Pre-HTML | UI sections: `member_interfaces_by_switch`, `consistency_tables` |
| `07_post_render_manifest.json` | Post-HTML | File sizes, counts, presentation summary |
| `topology_map_vpc_*.html` | Output | Offline interactive map |

---

## Naming conventions (mandatory)

- Folder: `topology_diagnostics_{timestamp}` (no spaces)
- Stage files: `NN_descriptive_name.{json|txt}` where `NN` is `00`–`07`
- Template: `vpc_map_data_TEMPLATE.json` (camelCase keys inside JSON)
- Structured field on nodes: `vpc_member_interfaces` (per-switch map of `entries[]`)
- Physical correlation on edges: `bundled_links[]` with `from`, `f_port`, `to`, `t_port`, `f_int_data`

---

## Troubleshooting: empty Member Interfaces panel

1. Open `06_pre_render_presentation.json` → `member_interfaces_by_switch`.
2. If empty, open `01_raw_node_metadata.json` → device → `vpc_member_interfaces.entries`.
3. If still empty, verify NX-OS `show vpc` / `show vpc brief` returned a vPC table on the device.
4. If collection is good but UI empty, check `03_post_transform_edges.json` → `vpc_shared` → `bundled_links` (physical ports per switch).
5. Compare `04_final_map_data.json` edges: each `vpc_shared` edge must expose `type` and `bundled_links` at the top level (not only inside `edge_data`).

---

## Automated validation

```powershell
python tests/validate_vpc_member_interfaces.py
```

Exit code `0` confirms parsers, builders, demo HTML, and naming conventions.
