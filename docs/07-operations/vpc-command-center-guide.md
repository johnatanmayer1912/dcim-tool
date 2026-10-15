# VPC Command Center (v7.0.4)

Offline HTML report for vPC topology runs. Open the generated `.html` file in any modern browser (no internet required).

## Tabs

| Tab | What you see |
|-----|----------------|
| **1 Overview** | Engineering board (left) and topology map (right) at the same time |
| **2 Link inventory** | Sortable L2 table of collected edges |
| **3 Collected data** | Tables from presentation JSON: domains, member interfaces per switch, sample graph edges |
| **Print board** | Browser print of the engineering board |

## Reading the board

- Each **vPC domain** groups primary/secondary switches, peer-link, and member port-channels.
- Status colors: green = up, amber = partial, red = down/orphan.
- Click domain rows or map nodes for detail panels when data was collected.

## Reading the map

- The **topology map is on the left** of Overview (engineering board on the right).
- Use toolbar: **Fit view**, **All peers**, **L2 adjacency** (show/hide non-vPC CDP links), **Reset highlight**.
- Selecting a **vPC domain** in the board dropdown highlights peers on the map.
- Physics is **off** (fixed layout). Mouse wheel zooms; drag the background to pan.
- **Light / Dark** toggle stores preference in `localStorage` (`nst_vpc_theme`).
- If the map area is empty, wait ~1s for auto-init, click **Fit view**, or check the yellow empty-state banner.

## No vPC domain detected (v7.0.4+)

When `show vpc` does not return a domain (single switch, partial SSH, or non-NX-OS seeds):

- A yellow banner states that **physical adjacency** is shown instead of vPC-only edges.
- All nodes receive grid coordinates so the map is never empty.
- Swiss Tools status shows `0` vPC domains and may note adjacency fallback — review diagnostics `01` and `06`.

## Diagnostics folder

Alongside the HTML, `topology_diagnostics_<timestamp>/` contains:

- `06_pre_render_presentation.json` — source for **Collected data** tab
- `01_collection_summary.txt` — SSH/collection notes

If **Collected data** shows “No vPC domains”, verify NX-OS `show vpc` succeeded on both peers.

## Demo file

Run `python create_demo_map_v7.py` to produce `DEMO_VPC_TOPOLOGY_v7.0.4.html` for training and health-wizard smoke checks.
