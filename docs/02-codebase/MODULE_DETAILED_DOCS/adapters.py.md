# adapters.py Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Lead Developer (R-ENG) |
| **Last Updated** | 2026-08-18 |
| **Application Version** | 7.0.85 |

> **Operator UI:** web only (`vlan_checker_web.py`). Tk (`vlan_checker_gui.py`) is out of scope. Adapters remain the shared task layer for the web console (and leftover CLI), not a dual GUI/web product.

## Overview

The adapter layer is the shared implementation of network workflow loops used by the **web** operator console (`vlan_checker_web.py`). Tkinter (`vlan_checker_gui.py`) is out of scope and is not a supported operator UI.

## File Location

- **Path**: `modules/adapters.py`
- **Lines**: 4142
- **Dependencies**: os, json, datetime, sys

## Purpose

The adapter layer serves as the bridge between:
- **UI Layer** (web operator console)
- **Feature Modules** (network operations)
- **Report Formatters** (output generation)

## Contract

All adapter functions follow this contract:
- **Input**: Accept a `log` callable: `log(msg: str)`
- **Output**: Return a list of structured JSON results (per device)
- **File I/O**: Delegated to `utils/report_formatter.py`
- **Network I/O**: Delegated to `/modules/` feature modules

## Output Format (Per Device)

```python
{
    "device": "x.x.x.x",
    "status": "success|fail",
    "data": {},
    "error": null
}
```

## Helper Functions

### `_abort_if_cancelled(log)`

**Purpose**: Cooperative cancel for long-running multi-device loops

**Returns**: `bool` - True if task should be cancelled

**Behavior**:
- Checks `utils.task_control_plane.should_abort()`
- Logs cancellation message if abort requested
- Returns True to signal cancellation

### `_device_progress(idx: int, total: int, host: str = '')`

**Purpose**: Report devices_done / devices_total to control-plane task registry

**Behavior**:
- Calls `utils.task_control_plane.update_task_progress()`
- Formats progress message with hostname
- Used for progress tracking in UI

### `_get_resource_path(relative_path)`

**Purpose**: Get absolute path to resource (dev or PyInstaller)

**Returns**: `str` - Absolute path

**Behavior**:
- Checks `sys._MEIPASS` for bundled resources
- Falls back to current directory for dev mode

### `_get_app_working_dir()`

**Purpose**: Get writable data root for reports/logs

**Returns**: `str` - Data root directory

**Behavior**:
- Delegates to `utils.output_paths.get_data_root()`
- Ensures writable location (never install directory)

## VPC-Specific Functions

### `_build_vpc_member_interfaces(member_name, meta)`

**Purpose**: Build per-switch vPC interface registry for HTML sidebar

**Parameters**:
- `member_name` (str): Switch hostname
- `meta` (dict): Device metadata with vPC data

**Returns**: `dict` - Structured vPC interface data

**Behavior**:
- Merges `show vpc` table rows with port-channel physical members
- Deduplicates entries using (vpc_id, port_channel, members) key
- Includes peer-link port-channel
- Returns switch, interface_count, entries

### `_build_html_presentation_payload(nodes_json, edges_json, map_mode)`

**Purpose**: Flatten nodes/edges into sections that match HTML sidebar

**Parameters**:
- `nodes_json` (list): Topology nodes
- `edges_json` (list): Topology edges
- `map_mode` (str): Map mode ('vpc', etc.)

**Returns**: `dict` - HTML presentation payload

**Sections**:
- `vpc_domains` - List of VPC domains
- `member_interfaces_by_switch` - Interface data per switch
- `consistency_tables` - VPC consistency tables
- `graph_edges` - Graph edge data
- `board_sections` - Engineering board data (vpc mode only)

### `_extract_global_consistency_raw(vpc_details)`

**Purpose**: Pull raw CLI text from vpc_details metadata blob

**Parameters**:
- `vpc_details` (dict): VPC details metadata

**Returns**: `str` - Raw consistency text

### `_build_vpc_board_sections(nodes_json, edges_json, presentation)`

**Purpose**: Build structured data for offline Engineering Board

**Parameters**:
- `nodes_json` (list): Topology nodes
- `edges_json` (list): Topology edges
- `presentation` (dict): HTML presentation payload

**Returns**: `list` - Structured board sections

**Behavior**:
- Extracts domain information
- Builds peer data with role, status, keepalive
- Extracts downstream connections
- Includes trust chains and alerts

## Core Workflow Functions

### `run_connectivity(devices, user, pwd, enb_pwd, log)`

**Purpose**: Execute connectivity check on multiple devices

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function

**Returns**: `list` - Results per device

**Behavior**:
- Iterates through devices
- Checks SSH connectivity
- Reports progress
- Handles cancellation
- Returns structured results

### `run_config_backup(devices, user, pwd, enb_pwd, comment, log)`

**Purpose**: Execute configuration backup on multiple devices

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `comment` (str): Backup comment
- `log` (callable): Log function

**Returns**: `list` - Results per device

**Behavior**:
- Delegates to appropriate backup module
- Saves configurations to backup directory
- Generates backup reports
- Returns structured results

### `run_network_audit(devices, user, pwd, enb_pwd, log)`

**Purpose**: Execute network audit on multiple devices

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function

**Returns**: `list` - Results per device

**Behavior**:
- Runs comprehensive network audit
- Checks configuration compliance
- Generates audit reports
- Returns structured results

### `run_startup_backup_check(devices, log)`

**Purpose**: Check if recent backups exist for devices

**Parameters**:
- `devices` (list): Device list
- `log` (callable): Log function

**Returns**: `None`

**Behavior**:
- Checks backup directory for recent backups
- Reports devices needing backup
- No network connections required

## Topology Functions

### `run_topology_generation(devices, user, pwd, enb_pwd, log, options)`

**Purpose**: Generate network topology map

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function
- `options` (dict): Topology generation options

**Returns**: `dict` - Topology data (nodes, edges)

**Behavior**:
- Collects device information
- Discovers connections
- Builds topology graph
- Generates nodes and edges
- Returns structured topology data

### `run_l3_topology(devices, user, pwd, enb_pwd, log)`

**Purpose**: Generate L3 topology with routing information

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function

**Returns**: `dict` - L3 topology data

**Behavior**:
- Collects routing tables
- Identifies gateways
- Builds L3 graph
- Includes protocol information
- Returns structured L3 topology

## VLAN Functions

### `run_vlan_audit(devices, user, pwd, enb_pwd, log)`

**Purpose**: Execute VLAN audit on multiple devices

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function

**Returns**: `list` - Results per device

**Behavior**:
- Collects VLAN information
- Identifies VLAN inconsistencies
- Generates VLAN reports
- Returns structured results

### `run_vlan_compare(devices, user, pwd, enb_pwd, log)`

**Purpose**: Compare VLAN configurations between devices

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function

**Returns**: `dict` - VLAN comparison results

**Behavior**:
- Compares VLAN configurations
- Identifies differences
- Generates comparison reports
- Returns structured comparison data

## Interface Functions

### `run_interface_errors(devices, user, pwd, enb_pwd, log)`

**Purpose**: Analyze interface errors on multiple devices

**Parameters**:
- `devices` (list): Device list
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log` (callable): Log function

**Returns**: `list` - Results per device

**Behavior**:
- Collects interface error statistics
- Identifies problematic interfaces
- Generates error reports
- Returns structured results

## Data Structures

### Device Object
```python
{
    "host": "device_ip_or_hostname",
    "device_type": "cisco_ios|cisco_nxos|juniper|etc",
    "port": 22,
    "group": "group_name"
}
```

### Result Object
```python
{
    "device": "device_ip_or_hostname",
    "status": "success|fail",
    "data": {},
    "error": "error_message_if_failed"
}
```

### VPC Domain Object
```python
{
    "domain_id": "domain_id",
    "node_id": "node_id",
    "members": ["switch1", "switch2"],
    "health": {},
    "vpc_details": {},
    "vpc_structured": [],
    "vpc_member_interfaces": {}
}
```

## Error Handling

### Cancellation Handling
- Checks `should_abort()` before each device
- Logs cancellation message
- Stops processing remaining devices
- Returns partial results

### Connection Errors
- Logs connection failure
- Marks device as failed
- Continues with next device
- Includes error in result

### Module Errors
- Logs module execution error
- Marks device as failed
- Continues with next device
- Includes error traceback

## Progress Tracking

### Device Progress
- Calls `_device_progress()` for each device
- Updates control-plane task registry
- Includes hostname in progress message
- Format: "hostname (idx/total)"

### Task Cancellation
- Cooperative cancellation via `_abort_if_cancelled()`
- Checks before each device operation
- Graceful shutdown
- Partial results returned

## Usage Examples

### Connectivity Check
```python
from modules.adapters import run_connectivity

devices = [{'host': '192.168.1.1', 'device_type': 'cisco_ios'}]
results = run_connectivity(devices, 'admin', 'password', 'enable', print)
```

### Config Backup
```python
from modules.adapters import run_config_backup

results = run_config_backup(
    devices, 'admin', 'password', 'enable', 'Weekly backup', print
)
```

### Topology Generation
```python
from modules.adapters import run_topology_generation

topology = run_topology_generation(
    devices, 'admin', 'password', 'enable', print, {'mode': 'l2'}
)
```

## Related Documentation

- `main.py.md` - Entry point documentation
- `vlan_checker_web.py.md` - Web server documentation
- `vlan_checker_gui.py.md` - Desktop GUI documentation
- `modules/network_base.py.md` - Network base documentation

## Cross-References

- References: `utils/task_control_plane.py` (task management)
- References: `utils/report_formatter.py` (report generation)
- References: `modules/network_base.py` (device operations)
- Referenced by: `vlan_checker_web.py` (web operations)
- Referenced by: `vlan_checker_gui.py` (GUI operations)
