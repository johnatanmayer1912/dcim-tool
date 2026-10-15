# Network Swiss Tool Pro - Visualization Pipeline

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Documentation of the hierarchical visualization engine and vPC progressive disclosure system. |
| **Scope** | CSS design system, HTML structure for 3-view display, and JavaScript application layer logic. |
| **Related Documents** | [System Architecture](system-architecture.md), [UI Philosophy](../05-ui-ux/ui-philosophy.md) |
| **Update Responsibility** | UI/UX Lead / Frontend Engineer |
| **Version Awareness** | v7.0.51 (v6.9.27+ vPC Command Center; v7.0.49+ Standard Map shell) |

---

## Overview

This document describes the visualization pipeline for Network Swiss Tool Pro. **v6.9.27** adds a **dual-view vPC experience**:

| View | Module | Purpose |
|------|--------|---------|
| **Standard L2 Map** (`map_mode=all`) | `utils/standard_map_shell.py` + `utils/report_formatter.py` | **v7.0.49+** NOC split-pane: map + connection index; Tier/Radial/Focus/Schematic; offline-safe chrome (v7.0.51) |
| **Engineering Board** (default) | `utils/vpc_board_formatter.py` | Fixed CSS grid tables — peer strip, vPC Po table, downstream, global consistency — offline, no physics |
| **Simplified Map** | `utils/report_formatter.py` | Vis.js with preset `x,y`, physics off, collapsed downstream hosts |

`modules/adapters.py` builds `board_sections` inside `06_pre_render_presentation.json` and passes `board_payload_json` into `generate_topology_html()`.

The earlier **3-View Progressive Disclosure System** (domain → peers → downstream) remains on the map tab for spatial context.

---

## Standard L2 Map shell (v7.0.49–7.0.51)

**Canonical UX doc:** [standard-map-shell.md](../06-ui-ux/standard-map-shell.md)

| Component | File | Notes |
|-----------|------|-------|
| Shell CSS/JS/HTML | `utils/standard_map_shell.py` | `nst-top-chrome`, connection panel, map style bar |
| HTML assembly | `utils/report_formatter.py` | `use_standard_split` when `map_mode=='all'` |
| Link rows | `utils/topo_map_shell.py` | `link_rows_from_edges()` |
| Peer-link finalize | `modules/adapters.py` | `_finalize_standard_map_edges()` |

**Pipeline:** `run_topology_mapper(..., map_mode='all')` → Phase 2 edges → `_finalize_standard_map_edges()` → Vis.js JSON with empty canvas labels → `generate_topology_html()` embeds split pane + `nstBootStandardMap()`.

---

## vPC dual-view (v6.9.27+)

| File | Location | Changes |
|------|----------|---------|
| `report_formatter.py` | `utils/` | Complete visualization layer rewrite |

### Hard Isolation Verified
- ✅ No CLI connectivity code modified
- ✅ No WebSocket implementation modified
- ✅ No device communication layer modified
- ✅ No authentication/session logic modified
- ✅ No backend transport code modified

---

## Implementation Details

### 1. CSS Design System (Lines 403-1041)

**CSS Custom Properties Added:**
```css
/* VPC Domain Colors */
--vpc-primary: #6366f1 (Indigo-500)
--vpc-primary-dark: #4338ca (Indigo-700)
--vpc-accent: #8b5cf6 (Violet-500)

/* Connection Status */
--shared-link: #3b82f6 (Blue-500)
--orphan-link: #ef4444 (Red-500)
--peer-link: #a855f7 (Purple-500)

/* Spacing (8px grid) */
--space-xs: 4px, --space-sm: 8px, --space-md: 16px
--space-lg: 24px, --space-xl: 32px
```

**Component Primitives:**
- `.vpc-domain-node` - Large, prominent VPC domain visualization
- `.vpc-member-card` - Grid-based member device cards
- `.peer-link-section` - Visual peer-link representation
- `.connection-card` - Shared/Orphan connection cards
- `.side-panel` - Slide-out panel with animations

### 2. HTML Structure - 3-View System (Lines 1071-1171)

**VIEW 1: Global Topology (Default)**
- Vis.js network canvas with VPC domain nodes
- Standard node/edge detail panel (`#side-panel`)

**VIEW 2: VPC Detail Panel (`#vpc-detail-panel`)**
- Gradient header with domain ID badge
- Peer-link visual representation
- 2-column member device grid
- Interface & vPC listing by member
- Action buttons: "Connection Intelligence", "Highlight on Map"

**VIEW 3: Connection Intelligence Panel (`#connection-intelligence-panel`)**
- Shared connections list (dual-homed) with ✅ indicators
- Non-shared connections list (single-homed) with ⚠️ risk badges
- Export report button

### 3. JavaScript Application Layer (Lines 1594-1996)

**Core `app` Object:**
```javascript
app = {
    currentView: 'global' | 'vpc_detail' | 'intelligence',
    viewHistory: [],
    selectedVPCDomain: null,
    vpcData: {},  // Extracted domain structures
    
    init(),
    extractVPCData(),        // Parse nodes/edges into VPC structures
    enhanceVPCNodes(),       // Apply visual styling
    showVPCDetail(),         // Render View 2
    showConnectionIntelligence(),  // Render View 3
    switchView(),            // State management
    goBack(),                // Navigation
    highlightVPCDomain(),    // Map focus
    exportConnectionReport() // TXT download
}
```

**VPC Data Extraction Algorithm:**
1. Scan `nodes_raw` for `VPC_Domain_X` nodes
2. Extract members from `vpc_members` property
3. Categorize edges by type (reads `edge.type` or `edge.edge_data.type`):
   - `vpc-peer-link` → `domain.peerLink`
   - `vpc_shared` → `domain.sharedConnections[]`
   - `vpc_orphan` → `domain.orphanConnections[]`

**Member Interfaces panel (`renderVPCInterfaces`):**
1. Primary: `bundled_links` on `vpc_shared` / `vpc_orphan` edges (top-level or `edge_data`)
2. Fallback: `vpc_member_interfaces` on the domain node (from `show vpc` table + port-channel members)
3. Rows are deduplicated by local port + remote device + vPC label

**Diagnostic export:** See [Topology Diagnostics Guide](../07-operations/topology-diagnostics-guide.md).

**Enhanced Event Handlers:**
- Click on VPC domain node → `app.showVPCDetail()`
- Click on standard node → Original `renderNodePanel()`
- Back/Close buttons → `app.goBack()` with history stack

### 4. Vis.js Configuration Updates

**New Group Definition:**
```javascript
groups: {
    vpc_domain: {
        shape: 'box',
        color: { background: '#6366f1', border: '#4338ca' },
        font: { size: 16, color: '#ffffff', weight: 600 },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(99, 102, 241, 0.5)', size: 20 },
        margin: 16
    }
}
```

---

## Visual Behavior

### Global Topology View
```
┌─────────────────────────────────────────────────────────────┐
│  VPC Domain Nodes = Large indigo boxes (60px, shadow)       │
│  Regular Nodes = Standard size                              │
│  Shared Links = Thick blue edges                            │
│  Orphan Links = Dashed red edges                            │
│                                                             │
│  [Click VPC Domain → Opens Detail Panel]                   │
└─────────────────────────────────────────────────────────────┘
```

### VPC Detail Panel
```
┌────────────────────────────────────────┐
│  VPC Domain 10                         │
│  Domain ID: 10                         │
├────────────────────────────────────────┤
│  Peer Link: Leaf1 ←────→ Leaf2         │
│             Port: Po1                  │
├────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐             │
│  │  Leaf1  │  │  Leaf2  │             │
│  │ Primary │  │Secondary│             │
│  └─────────┘  └─────────┘             │
├────────────────────────────────────────┤
│  Member Interfaces:                   │
│  Leaf1: Po10 (vPC 10)                  │
│  Leaf2: Po10 (vPC 10)                  │
├────────────────────────────────────────┤
│  [Connection Intelligence] [Highlight]  │
└────────────────────────────────────────┘
```

### Connection Intelligence Panel
```
┌────────────────────────────────────────┐
│  Connection Intelligence               │
├────────────────────────────────────────┤
│  ✅ SHARED CONNECTIONS                 │
│  ├─ Server1 (dual-homed)               │
│  ├─ Server2 (dual-homed)               │
├────────────────────────────────────────┤
│  ⚠️ NON-SHARED (RISK)                  │
│  ├─ FW1 [Not redundant]                │
│  ├─ IDS1 [Not redundant]               │
├────────────────────────────────────────┤
│  [Export Report] [Close]               │
└────────────────────────────────────────┘
```

---

## Navigation Flow

```
[VIEW 1: Global Topology]
      │ Click VPC Domain
      ▼
[VIEW 2: VPC Detail Panel]
      │ Click "Connection Intelligence"
      ▼
[VIEW 3: Intelligence Panel]
      │ Click "Back" or "Close"
      ▼
[Return to Previous View]
```

**View State Management:**
- History stack tracks navigation path
- Back button returns to previous view
- Close buttons return to Global view
- ESC key support (can be added)

---

## Responsive Design

**Desktop (>1200px):**
- Side panel: 460px fixed width
- Network canvas: Flexible remaining space

**Tablet (900-1200px):**
- Side panel: 400px fixed width

**Mobile (<900px):**
- Side panel: Full width, 50% height
- Bottom sheet style (slides up from bottom)
- Network canvas: Top 50%

---

## Success Metrics Validation

| Criterion | Implementation |
|-----------|---------------|
| **5-Second Comprehension** | ✅ VPC domains prominently styled; shared/orphan links visually distinct |
| **No Overlapping Edges** | ✅ Hierarchical layout with `hierarchicalRepulsion` physics |
| **VPC Grouping Obvious** | ✅ Single consolidated node per domain; indigo color; shadow |
| **No Shared Link Duplication** | ✅ Merged into single edges with bundled link data |
| **No Raw Graph Clutter** | ✅ 3-view progressive disclosure; detail panels |

---

## Technical Implementation Notes

### CSS Architecture
- **BEM-like naming**: `.vpc-member-card`, `.connection-card`
- **CSS Custom Properties**: Full design system via variables
- **Container queries**: Not used (responsive via media queries)
- **Transitions**: 150ms fast, 250ms base (as specified)

### JavaScript Architecture
- **Single global `app` object**: Namespaced to prevent conflicts
- **Data-driven views**: Render functions accept domain objects
- **Event delegation**: Panel buttons use inline onclick handlers
- **No external dependencies**: Pure vanilla JS + Vis.js

### Performance Considerations
- **Edge categorization**: O(n) scan on init (acceptable for n<1000)
- **DOM updates**: Batched via innerHTML (not per-element)
- **Animation**: CSS-based for 60fps (slideIn keyframe)

---

## Future Enhancements (Out of Scope)

The following were considered but not implemented to maintain focus:

1. **Keyboard Navigation**: Arrow keys to navigate between VPC domains
2. **Filter Bar**: Dropdown to filter by VPC domain
3. **Mini Map**: Overview + detail pattern for large topologies
4. **Export SVG**: Save topology as vector graphic
5. **Dark Mode Toggle**: Switch between light/dark themes

---

## Testing Checklist

Before deployment, verify:

- [ ] VPC domain nodes appear larger than regular nodes
- [ ] Clicking VPC domain opens detail panel
- [ ] Peer link visual appears in detail panel
- [ ] Member devices shown in 2-column grid
- [ ] "Connection Intelligence" button opens third panel
- [ ] Shared connections show ✅ icon
- [ ] Orphan connections show ⚠️ + "RISK" badge
- [ ] Export button downloads TXT report
- [ ] Back button returns to previous view
- [ ] Close button clears selection
- [ ] Responsive layout works at various screen sizes
- [ ] No JavaScript errors in console
- [ ] Original node/edge panels still work for non-VPC nodes

---

## Backward Compatibility

✅ **Fully Backward Compatible**
- Standard node/edge panels unchanged
- Original search functionality preserved
- Description toggle still works
- No breaking changes to data format

---

## Lines of Code Summary

| Component | Lines Added |
|-----------|-------------|
| CSS Design System | ~650 lines |
| HTML Panel Structure | ~100 lines |
| JavaScript Application | ~400 lines |
| **Total** | **~1150 lines** |

---

*Implementation Complete - Ready for Integration Testing*
