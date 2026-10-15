# Network Swiss Tool Pro v6.1.1-BETA Release Notes

**Release Date:** 2026-04-21  
**Build Target:** Offline / Air-gapped Environments  
**Priority:** Feature Enhancement — Topology Visualization Quick Wins

---

## Summary

Version 6.1.1-BETA delivers three high-impact topology visualization improvements that give network engineers faster, clearer insight into their network topology without requiring any additional device commands or configuration.

---

## New Features

### Priority 3: Port Status Badges on Nodes

**What it does:**  
Every node in the topology map now displays a compact status badge directly on the node label showing the count of up, down, and err-disabled ports:

```
CORE-SW-01
24↑ 2↓ 1⚠
```

**How it works:**
- Counts are derived from `show interface status` data already collected during topology discovery
- `↑` = ports in "up/connected" state
- `↓` = ports in "down/notconnect/disabled" state  
- `⚠` = ports in "err-disabled" state
- Node tooltip includes a full Port Status Summary bar with a visual progress indicator (% ports up)

**Why it matters:**  
A network engineer can instantly see which switches have port problems without clicking into each node. A node showing `48↑ 0↓ 0⚠` is healthy; one showing `20↑ 5↓ 3⚠` needs attention.

---

### Priority 7: Device Role & Grouping

**What it does:**  
The topology mapper now automatically detects each device's role in the network hierarchy and applies role-based colors and a hierarchical layout:

| Role | Color | Layout Level |
|------|-------|-------------|
| Core | 🔴 Red (#c0392b) | Top |
| Distribution | 🟠 Orange (#e67e22) | Middle |
| Access | 🔵 Blue (#2980b9) | Bottom |
| Unknown | ⚫ Grey (#607d8b) | Middle |

**Detection heuristics (in priority order):**
1. **Hostname keywords** — `core`, `spine`, `backbone`, `agg` → Core; `dist`, `leaf`, `border`, `wan` → Distribution; `acc`, `floor`, `closet`, `edge` → Access
2. **CDP neighbor count** — ≥4 neighbors → Core; 2-3 → Distribution; 1 → Access
3. **Interface count** — ≥48 ports → Access; ≥24 → Distribution

**Layout:**  
Standard Map now uses Vis.js hierarchical layout (top-down, UD direction) instead of physics-based force layout. This produces a clean, readable diagram that mirrors how network engineers draw their own diagrams. vPC Map retains the physics layout for better vPC relationship visualization.

**Role Legend:**  
A color-coded legend bar above the graph shows device counts per role (e.g., "🔴 Core: 2  🟠 Distribution: 4  🔵 Access: 12").

---

### Priority 10: Search & Path Highlighting

**What it does:**  
A toolbar above the topology graph provides two powerful navigation tools:

#### Device Search
- Type any device name, role, or partial hostname in the search box
- Matching nodes are highlighted in yellow; non-matching nodes are dimmed
- The view automatically focuses on the first match
- Click "✕ Clear" to reset

#### Path Trace (BFS)
- Enter a "From" device and a "To" device
- Click "⚡ Trace Path" to run Breadth-First Search (BFS) and find the shortest path
- The path is highlighted in orange/green; all other nodes and links are dimmed
- Hop count is displayed (e.g., "Path: CORE-01 → DIST-01 → ACC-01 (2 hops)")
- Click "↺ Reset" to clear the highlight

#### Click-to-Fill
- Click any node in the graph to auto-fill the "From" field
- Click a second node to auto-fill the "To" field
- Then click "Trace Path" — no typing required

**Why it matters:**  
In large topologies with 20+ devices, finding a specific switch or tracing a path between two endpoints used to require manually scanning the graph. Now it's instant.

---

## Files Modified

| File | Change |
|------|--------|
| `modules/adapters.py` | Added `_detect_device_role()` helper; enhanced `run_topology_mapper()` with port badge counting, role detection, hierarchical levels, and role legend |
| `utils/report_formatter.py` | Updated `generate_topology_html()` with `map_mode` param, hierarchical layout option, search toolbar, BFS path tracing JS |
| `vlan_checker_web.py` | Version bumped to 6.1.1-BETA |
| `VERSION` | Updated to 6.1.1-BETA |
| `docs/02_RELEASES/CHANGELOG.md` | Added v6.1.1 entry |
| `docs/prompts/P05-TOPOLOGY.md` | Updated with v6.1.1 features |

---

## Backward Compatibility

- **100% backward compatible** — all existing topology features (Standard Map, vPC Map, Port Interface Map) work unchanged
- vPC Map retains its original physics-based layout and color scheme
- All existing node tooltips and edge labels are preserved and enhanced
- The `generate_topology_html()` function signature change is backward compatible (`map_mode` defaults to `"all"`)

---

## How to Verify

1. Run the application in dev mode: `python vlan_checker_web.py`
2. Navigate to the **Swiss Tools** tab
3. Click **Standard Map** — verify:
   - Nodes show port status badges (e.g., `24↑ 2↓`)
   - Nodes are color-coded by role (red/orange/blue)
   - Layout is hierarchical (core at top, access at bottom)
   - Role legend appears above the graph
   - Search toolbar is visible
4. Type a device name in the search box — verify matching nodes highlight
5. Enter two device names in the Path fields and click Trace Path — verify path highlights
6. Click **vPC Map** — verify original vPC colors and physics layout are preserved

---

## Architecture Notes

### Role Detection Algorithm

```python
def _detect_device_role(node_name, neighbor_count, int_meta):
    # 1. Hostname keyword match (highest priority)
    # 2. CDP neighbor count threshold
    # 3. Interface count heuristic
    # Returns: (role_str, color_hex)
```

### BFS Path Algorithm (JavaScript)

The path tracing uses client-side BFS on the adjacency list built from the edge data embedded in the HTML. No server round-trip required — works fully offline.

```javascript
function bfsPath(startId, endId) {
    // Builds adjacency list from edges_raw
    // Returns { nodes: [...], edges: [...] } or null
}
```

---

**Built with PyInstaller for offline deployment.**  
**Made by AI IDE**
