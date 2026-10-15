# Prompt P05: Create Topology Mapper Module

> **Objective:** Build topology mapping module with CDP/LLDP discovery and Vis.js visualization  
> **Version:** 6.1.1-BETA (includes Port Badges, Role Detection, Search & Path Highlighting)

---

## 🎯 Goal

Create `modules/topology_mapper.py` and `modules/node_interface_topology.py` that:
1. Collect CDP/LLDP neighbor data from devices
2. Gather interface status and descriptions
3. Detect vPC (virtual Port-Channel) configurations
4. Generate Vis.js network topology graphs with:
   - **Port Status Badges** on nodes (↑ up / ↓ down / ⚠ err-disabled counts)
   - **Device Role & Grouping** (auto-detect core/distribution/access, hierarchical layout)
   - **Search & Path Highlighting** (search box + BFS path tracing)

---

## ✅ Prerequisites

- P01 (Foundation) complete
- P02 (Network Base) complete
- `modules/network_base.py` exists with `connect_permissive`, `build_json`

---

## 📝 v6.1.1 Enhancements

### Priority 3: Port Status Badges

Each node label now shows a compact badge: `HOSTNAME\n24↑ 2↓ 1⚠`

- `↑` = ports up/connected
- `↓` = ports down/notconnect/disabled
- `⚠` = ports err-disabled
- Counts derived from `int_meta` collected during topology discovery
- Node tooltip includes a Port Status Summary bar with visual progress indicator

### Priority 7: Device Role & Grouping

`_detect_device_role(node_name, neighbor_count, int_meta)` in `modules/adapters.py`:

| Role | Color | Hostname Keywords | Neighbor Count |
|------|-------|-------------------|----------------|
| core | #c0392b (Red) | core, spine, backbone, agg | ≥4 |
| distribution | #e67e22 (Orange) | dist, leaf, border, wan | 2-3 |
| access | #2980b9 (Blue) | acc, floor, closet, edge | 1 |
| unknown | #607d8b (Grey) | — | 0 |

Standard Map uses hierarchical layout (UD direction); vPC Map retains physics layout.

### Priority 10: Search & Path Highlighting

Toolbar above the topology graph:
- **Search box**: Highlights matching nodes, dims others, auto-focuses first match
- **Path Trace**: BFS from source to destination, highlights path + hop count
- **Click-to-Fill**: Click nodes to auto-fill path fields
- **Reset**: One-click clear for both search and path highlights

---

## 📝 Step 1: Create topology_mapper.py

See current implementation in `modules/topology_mapper.py`.

Key data returned per device:
```python
{
    "true_host": hostname,
    "int_meta": {port: {"status": "up|down|err-disabled", "desc": "...", "macs": [...]}},
    "interface_macs": {port: [mac1, mac2]},
    "bundles": {member_port: "Po1"},
    "vpcs": ["Po1", "Po2"],
    "vpc_details": {"Po1": {"vpc_id": "1", "status": "up", "type": "vpc"}},
    "edges": [{"from": hostname, "f_port": "Gi0/1", "to": "peer", "t_port": "Gi0/2"}]
}
```

---

## 📝 Step 2: Adapter Layer (modules/adapters.py)

Key functions:
- `_detect_device_role(node_name, neighbor_count, int_meta)` → `(role, color)`
- `run_topology_mapper(devices, user, pwd, enb_pwd, log, map_mode='all')` → `(results, html_file)`

---

## 📝 Step 3: HTML Generation (utils/report_formatter.py)

`generate_topology_html(html_file, num_nodes, num_edges, nodes_str, edges_str, vis_js_content, extra_header="", map_mode="all")`

- `map_mode="all"` → hierarchical layout, role-based colors
- `map_mode="vpc"` → physics layout, vPC-focused colors

---

## 📝 Step 4: Update index.html (CRITICAL v4.5.8 FIX)

**⚠️ IMPORTANT:** When updating `modules/web/templates/index.html`, use **string parameters**, not objects:

```html
<!-- ✅ CORRECT (v4.5.8) -->
<button onclick="runAction('topology', 'all')">Standard Map</button>
<button onclick="runAction('topology', 'vpc')">vPC Map</button>

<!-- ❌ WRONG (causes 'dict has no upper' error) -->
<button onclick="runAction('topology', {map_mode: 'all'})">Standard Map</button>
```

---

## ✅ Verification

### Test 1: Module Import
```bash
python -c "from modules import topology_mapper; print('✓ topology_mapper OK')"
python -c "from modules import node_interface_topology; print('✓ node_interface_topology OK')"
python -c "from modules.adapters import _detect_device_role; print('✓ role detection OK')"
```

### Test 2: Role Detection
```python
from modules.adapters import _detect_device_role
role, color = _detect_device_role('core-sw-01', 5, {})
assert role == 'core', f"Expected core, got {role}"
role, color = _detect_device_role('acc-sw-01', 1, {})
assert role == 'access', f"Expected access, got {role}"
print("✓ Role detection OK")
```

### Test 3: HTML Generation
```python
from utils.report_formatter import generate_topology_html
import inspect
sig = inspect.signature(generate_topology_html)
assert 'map_mode' in sig.parameters, "map_mode param missing"
print("✓ generate_topology_html signature OK")
```

---

## 🎯 Success Criteria

- [x] `topology_mapper.py` collects int_meta with status counts
- [x] `_detect_device_role()` correctly classifies core/dist/access
- [x] Node labels show port status badges (↑↓⚠)
- [x] Standard Map uses hierarchical layout
- [x] vPC Map retains physics layout
- [x] Search box highlights matching nodes
- [x] Path trace uses BFS and highlights shortest path
- [x] Click-to-fill path fields from node clicks
- [x] Role legend displayed above graph

---

## 🚀 Next Step

When this prompt is complete and verified, proceed to:  
→ **P06-ADAPTERS.md** (Create adapter orchestration layer)

---

## 💾 Checkpoint

Before proceeding, commit this work:
```bash
git add .
git commit -m "v6.1.1: Enhanced topology - port badges, role detection, search & path highlighting"
```

---

## 📚 References

- **Release Notes:** `docs/02_RELEASES/RELEASE_NOTES_6.1.1.md`
- **Changelog:** `docs/02_RELEASES/CHANGELOG.md`
- **Architecture:** `docs/01_ARCHITECTURE/01-ARCHITECTURE.md`


---

## 🎯 Goal

Create `modules/topology_mapper.py` and `modules/node_interface_topology.py` that:
1. Collect CDP/LLDP neighbor data from devices
2. Gather interface status and descriptions
3. Detect vPC (virtual Port-Channel) configurations
4. Generate Vis.js network topology graphs

---

## ✅ Prerequisites

- P01 (Foundation) complete
- P02 (Network Base) complete
- `modules/network_base.py` exists with `connect_permissive`, `build_json`

---

## 📝 Step 1: Create topology_mapper.py

Create file: `modules/topology_mapper.py`

```python
"""
Topology Mapper Module
Collects CDP/LLDP topology data and generates Vis.js HTML graph.
"""
import re
from .network_base import connect_permissive, build_json


def normalize_port(port):
    """Normalize port name for comparison."""
    p = port.lower().replace(' ', '').replace('gigabitethernet', 'gi')
    p = p.replace('tengigabitethernet', 'te').replace('fastethernet', 'fa')
    p = p.replace('port-channel', 'po')
    return p


def run(device, user, pwd, enb_pwd="", log_func=None):
    """Collect topology data from device.
    
    Args:
        device: Dict with 'host', 'device_type', 'port'
        user: SSH username
        pwd: SSH password
        enb_pwd: Enable password (optional)
        log_func: Logging callback function (optional)
    
    Returns:
        Dict with 'status', 'data', 'error'
        data includes: neighbors, int_meta, bundles, vpcs
    """
    host = device['host']
    dtype = device.get('device_type', '').lower()
    conn = None
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting...")
        conn = connect_permissive(device, user, pwd, enb_pwd)
        
        # Get hostname
        hostname = conn.find_prompt().strip().replace('#', '').replace('>', '')
        if log_func:
            log_func(f"[{host}] Hostname: {hostname}")
        
        # Get neighbor data (CDP or LLDP)
        if "cisco" in dtype or "nxos" in dtype:
            if log_func:
                log_func(f"[{host}] Collecting CDP neighbors...")
            cdp_out = conn.send_command("show cdp neighbors detail")
            neighbors = parse_cdp_output(cdp_out)
        else:
            if log_func:
                log_func(f"[{host}] Collecting LLDP neighbors...")
            lldp_out = conn.send_command("show lldp neighbors detail")
            neighbors = parse_lldp_output(lldp_out)
        
        if log_func:
            log_func(f"[{host}] Found {len(neighbors)} neighbors")
        
        # Get interface status
        stat_cmd = "show interface status" if "cisco" in dtype or "nxos" in dtype else "show interfaces terse"
        if log_func:
            log_func(f"[{host}] Getting interface status...")
        stat_out = conn.send_command(stat_cmd)
        
        # Get interface descriptions
        desc_cmd = "show interfaces description" if "cisco" in dtype or "nxos" in dtype else "show interfaces detail | match Description"
        desc_out = conn.send_command(desc_cmd)
        
        # Parse interface metadata
        int_meta = {}
        
        # Parse descriptions
        for line in desc_out.splitlines():
            match = re.match(r'^(\S+)\s+(.*)$', line.strip())
            if match:
                iname, desc = match.groups()
                int_meta[iname] = {"desc": desc.strip(), "status": "unknown"}
        
        # Parse status
        for line in stat_out.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                iname = parts[0]
                status = parts[1].lower()
                if iname in int_meta:
                    int_meta[iname]["status"] = status
        
        # Get vPC info (NXOS only)
        vpcs = []
        if "nxos" in dtype:
            if log_func:
                log_func(f"[{host}] Collecting vPC information...")
            vpc_out = conn.send_command("show vpc")
            vpcs = parse_vpc_output(vpc_out)
        
        # Disconnect
        if log_func:
            log_func(f"[{host}] Disconnecting...")
        conn.disconnect()
        conn = None
        
        return build_json(host, "success", {
            "true_host": hostname,
            "neighbors": neighbors,
            "int_meta": int_meta,
            "vpcs": vpcs
        })
        
    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        return build_json(host, "fail", {}, error_msg)
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass


def parse_cdp_output(output):
    """Parse Cisco CDP neighbors detail output."""
    neighbors = []
    current = {}
    
    for line in output.splitlines():
        line_stripped = line.strip()
        
        if "Device ID:" in line_stripped:
            if current:
                neighbors.append(current)
            current = {"device_id": line_stripped.split("Device ID:")[1].strip()}
        elif "IP address:" in line_stripped:
            current["ip"] = line_stripped.split("IP address:")[1].strip()
        elif "Platform:" in line_stripped:
            current["platform"] = line_stripped.split("Platform:")[1].split(",")[0].strip()
        elif "Interface:" in line_stripped and "Port ID" in line_stripped:
            # Format: "Interface: Gig0/1, Port ID (outgoing port): Gig0/2"
            parts = line_stripped.split(",")
            for part in parts:
                if "Interface:" in part:
                    current["local_interface"] = part.split("Interface:")[1].strip()
                elif "Port ID" in part and "outgoing" in part:
                    current["remote_interface"] = part.split(":")[-1].strip()
    
    if current:
        neighbors.append(current)
    
    return neighbors


def parse_lldp_output(output):
    """Parse Juniper LLDP neighbors detail output."""
    neighbors = []
    current = {}
    
    for line in output.splitlines():
        line_stripped = line.strip()
        
        if "System name:" in line_stripped:
            if current:
                neighbors.append(current)
            current = {"device_id": line_stripped.split("System name:")[1].strip()}
        elif "System description:" in line_stripped:
            current["platform"] = line_stripped.split("System description:")[1].strip()
        elif "Local interface:" in line_stripped:
            current["local_interface"] = line_stripped.split("Local interface:")[1].strip()
        elif "Remote port ID:" in line_stripped or "Port ID:" in line_stripped:
            current["remote_interface"] = line_stripped.split(":")[-1].strip()
    
    if current:
        neighbors.append(current)
    
    return neighbors


def parse_vpc_output(output):
    """Parse NXOS vPC output."""
    vpcs = []
    # Simplified parsing - can be enhanced
    return vpcs
```

---

## 📝 Step 2: Create node_interface_topology.py

Create file: `modules/node_interface_topology.py`

```python
"""
Node Interface Topology Module
Generates per-node interface topology with Vis.js.
"""
import re
from .network_base import connect_permissive, build_json


def run(device, user, pwd, enb_pwd="", log_func=None):
    """Generate interface topology for a single device."""
    host = device['host']
    dtype = device.get('device_type', '').lower()
    conn = None
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting...")
        conn = connect_permissive(device, user, pwd, enb_pwd)
        
        hostname = conn.find_prompt().strip().replace('#', '').replace('>', '')
        
        # Get interface data
        if "cisco" in dtype or "nxos" in dtype:
            int_out = conn.send_command("show interface status")
            desc_out = conn.send_command("show interfaces description")
        else:
            int_out = conn.send_command("show interfaces terse")
            desc_out = conn.send_command("show interfaces detail | match Description")
        
        # Parse interfaces
        interfaces = []
        for line in int_out.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                interfaces.append({
                    "name": parts[0],
                    "status": parts[1] if len(parts) > 1 else "unknown"
                })
        
        # Disconnect
        if log_func:
            log_func(f"[{host}] Disconnecting...")
        conn.disconnect()
        conn = None
        
        return build_json(host, "success", {
            "true_host": hostname,
            "interfaces": interfaces
        })
        
    except Exception as e:
        return build_json(host, "fail", {}, str(e))
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass
```

---

## 📝 Step 3: Update index.html (CRITICAL v4.5.8 FIX)

**⚠️ IMPORTANT:** When updating `modules/web/templates/index.html`, use **string parameters**, not objects:

```html
<!-- ✅ CORRECT (v4.5.8) -->
<button onclick="runAction('topology', 'all')">Standard Map</button>
<button onclick="runAction('topology', 'vpc')">vPC Map</button>

<!-- ❌ WRONG (causes 'dict has no upper' error) -->
<button onclick="runAction('topology', {map_mode: 'all'})">Standard Map</button>
<button onclick="runAction('topology', {map_mode: 'vpc'})">vPC Map</button>
```

---

## ✅ Verification

### Test 1: Module Import
```bash
python -c "from modules import topology_mapper; print('✓ topology_mapper OK')"
python -c "from modules import node_interface_topology; print('✓ node_interface_topology OK')"
```

### Test 2: Function Signatures
```python
from modules import topology_mapper
help(topology_mapper.run)
# Should show: run(device, user, pwd, enb_pwd="", log_func=None)
```

### Test 3: HTML Fix
```bash
Select-String -Path "modules/web/templates/index.html" -Pattern "runAction\('topology', 'all'\)"
# Should return match
Select-String -Path "modules/web/templates/index.html" -Pattern "\{map_mode:"
# Should NOT return match (old buggy pattern)
```

---

## 🎯 Success Criteria

- [ ] `topology_mapper.py` created with all functions
- [ ] `node_interface_topology.py` created
- [ ] CDP parsing works
- [ ] LLDP parsing works
- [ ] JavaScript uses string params ('all', 'vpc') NOT objects
- [ ] Imports work without errors

---

## 🚀 Next Step

When this prompt is complete and verified, proceed to:  
→ **P06-ADAPTERS.md** (Create adapter orchestration layer)

---

## 💾 Checkpoint

Before proceeding, commit this work:
```bash
git add .
git commit -m "P05: Created topology mapper modules with v4.5.8 JS fix"
```

---

## 📚 References

- **Bug Fix Details:** `docs/VALIDATION.md` (v4.5.8 section)
- **Rebuild Guide:** `docs/HOW-TO-REBUILD.md`
- **Troubleshooting:** `docs/06-TROUBLESHOOTING.md`
