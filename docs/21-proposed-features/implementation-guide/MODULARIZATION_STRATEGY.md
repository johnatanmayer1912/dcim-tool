# Modularization Strategy for Proposed Features

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | System Architect (R-ARCH) |
| **Last Updated** | 2026-07-21 |
| **Application Version** | 7.0.85 |

## Purpose

This document outlines the modularization strategy for implementing proposed network visualization features. The strategy leverages NST's existing plugin system to ensure minimal core code changes and maximum maintainability.

## Architecture Overview

### Existing Plugin System
NST already has a sophisticated plugin system (`modules/plugin_registry.py`) that:
- Scans `modules/plugins/` for .py files
- Extracts METADATA without executing unsafe code
- Validates plugin contracts
- Supports hot-reloading
- Manages plugin execution

### Modular Components

#### 1. Visualization Plugin
**File**: `modules/plugins/advanced_topology_plugin.py`

**Purpose**: Core visualization logic and topology generation

**Responsibilities**:
- Generate multi-view topology data (Network Flows, L2 Map, L3 Map, Combined)
- Implement C4 zoom level logic
- Handle device and edge data transformation
- Support progressive disclosure

**Interface**:
```python
METADATA = {
    'plugin_id': 'advanced_topology_viz',
    'display_name': 'Advanced Topology Visualization',
    'version': '1.0.0',
    'category': 'visualization',
    'description': 'Multi-view topology with C4 zoom, flows, L2/L3 combined'
}

def execute(devices, credentials, options):
    """
    Generate topology visualization data
    
    Args:
        devices: List of device objects from inventory
        credentials: Credential dictionary
        options: Visualization options (view_type, zoom_level, etc.)
    
    Returns:
        dict: Topology data with nodes, edges, metadata
    """
    pass
```

#### 2. Web Template Extension
**File**: `modules/web/templates/advanced_viz.html`

**Purpose**: UI components for advanced visualization

**Components**:
- Scenario switcher (Network Flows, L2 Map, L3 Map, Combined)
- Interactive device detail modals
- Real-time simulation controls
- Keyboard shortcuts overlay
- Search and filter UI

**Integration**:
- Extend existing `index.html` or create standalone template
- Use Flask/Jinja2 templating
- Include CSS/JS from EXPERT_DEMO_MEGAPLAN.html
- Integrate with existing Flask routes

#### 3. API Endpoints
**File**: `vlan_checker_web.py` (extended)

**Purpose**: REST API for visualization data

**Endpoints**:
```python
@app.route('/api/topology/advanced')
def get_advanced_topology():
    """
    Get topology data for specified view
    
    Query params:
        view_type: 'flows', 'l2', 'l3', 'combined'
        zoom_level: 'context', 'container', 'component', 'code'
    
    Returns:
        JSON: Topology data with nodes, edges, metadata
    """
    pass

@app.route('/api/topology/device/<device_id>')
def get_device_details(device_id):
    """
    Get detailed device information for modal
    
    Args:
        device_id: Device identifier
    
    Returns:
        JSON: Device details (overview, interfaces, routing, alerts, neighbors)
    """
    pass

@app.route('/api/topology/realtime')
def get_realtime_updates():
    """
    Get real-time topology updates
    
    Returns:
        JSON: Live status changes, flow data, alerts
    """
    pass
```

#### 4. Data Adapter
**File**: `modules/topology_adapter.py`

**Purpose**: Transform NST data structures to visualization format

**Responsibilities**:
- Convert device inventory to node format
- Map interfaces to port-channel structure
- Extract routing data for L3 visualization
- Transform protocol information
- Handle VRF data mapping

**Interface**:
```python
class TopologyAdapter:
    """Adapter for transforming NST data to visualization format"""
    
    def __init__(self, devices):
        self.devices = devices
    
    def to_nodes(self, view_type):
        """Convert devices to node format for specified view"""
        pass
    
    def to_edges(self, view_type):
        """Generate edges based on device relationships"""
        pass
    
    def get_device_details(self, device_id):
        """Get detailed device information"""
        pass
    
    def get_routing_data(self, device_id):
        """Extract routing table data"""
        pass
    
    def get_interface_data(self, device_id):
        """Extract interface data with port-channel info"""
        pass
```

## Integration Points

### Plugin System Integration
- Follow existing plugin METADATA contract
- Use plugin registry for discovery
- Support hot-reloading for development
- Maintain plugin compatibility matrix

### Web Server Integration
- Extend Flask app in `vlan_checker_web.py`
- Add new routes without breaking existing routes
- Use existing authentication/authorization
- Maintain session management consistency

### Data Flow Integration
```
Inventory → Network Base → Topology Adapter → Visualization Plugin → API → Web Template
```

### Template Integration
- Extend existing Jinja2 templates
- Use existing CSS framework
- Integrate with existing JavaScript libraries (vis.js)
- Maintain responsive design patterns

## Implementation Phases

### Phase 1: Data Layer (Foundation)
1. Create `modules/topology_adapter.py`
2. Implement device-to-node transformation
3. Implement edge generation logic
4. Add unit tests for data transformation

### Phase 2: Plugin Layer (Core Logic)
1. Create `modules/plugins/advanced_topology_plugin.py`
2. Implement topology generation logic
3. Add C4 zoom level support
4. Implement multi-view generation
5. Add plugin tests

### Phase 3: API Layer (Data Serving)
1. Extend `vlan_checker_web.py` with new routes
2. Implement topology data endpoint
3. Implement device details endpoint
4. Add real-time updates endpoint
5. Add API tests

### Phase 4: UI Layer (User Interface)
1. Create `modules/web/templates/advanced_viz.html`
2. Integrate CSS/JS from EXPERT_DEMO_MEGAPLAN.html
3. Implement scenario switcher
4. Add interactive modals
5. Integrate with Flask routes

### Phase 5: Integration (End-to-End)
1. Integrate all components
2. Add end-to-end tests
3. Performance testing
4. Browser compatibility testing
5. Documentation updates

## Minimal Core Code Changes

### Files to Modify
- `vlan_checker_web.py` - Add API routes (10-20 lines)
- `modules/web/templates/index.html` - Add navigation link (1 line)

### Files to Create (No Core Changes)
- `modules/plugins/advanced_topology_plugin.py` - New plugin
- `modules/topology_adapter.py` - New adapter
- `modules/web/templates/advanced_viz.html` - New template

### Zero Changes Required
- `main.py` - No changes
- `modules/plugin_registry.py` - No changes
- `modules/network_base.py` - No changes
- All existing plugins - No changes
- All existing templates - No changes

## Benefits of This Approach

### Maintainability
- Isolated components for easy updates
- Plugin system for hot-reloading
- Clear separation of concerns
- Minimal core code changes

### Testability
- Each component independently testable
- Plugin tests separate from core tests
- API tests separate from UI tests
- Data transformation tests isolated

### Extensibility
- Easy to add new visualization views
- Plugin system supports custom plugins
- Adapter pattern for data sources
- Template system for UI customization

### Rollback
- Disable plugin if issues arise
- Revert API routes easily
- Template changes isolated
- No core code corruption risk

## Testing Strategy

### Unit Tests
- Topology adapter data transformation tests
- Plugin logic tests
- API endpoint tests
- Template rendering tests

### Integration Tests
- Plugin system integration
- API to adapter integration
- Template to API integration
- End-to-end workflow tests

### Performance Tests
- Large topology rendering (50+ devices)
- Real-time update performance
- Memory usage validation
- API response time validation

### Compatibility Tests
- Browser compatibility (Chrome, Firefox, Edge, Safari)
- Plugin compatibility with existing plugins
- Template compatibility with existing templates
- API compatibility with existing routes

## Related Documentation

- `../competitive-analysis/FEATURE_REVIEW_PROPOSED.md` - Feature requirements
- `../competitive-analysis/EXPERT_DEMO_MEGAPLAN.html` - UI reference
- `../../05-plugins/` - Plugin system documentation
- `../../06-ui-ux/` - UI/UX documentation
- `../../02-codebase/plugin_registry.py.md` - Plugin registry docs

## Cross-References

- References: `modules/plugin_registry.py` (plugin system)
- References: `vlan_checker_web.py` (web server)
- References: `modules/network_base.py` (data structures)
- Referenced by: `INTEGRATION_CHECKLIST.md` (integration steps)
