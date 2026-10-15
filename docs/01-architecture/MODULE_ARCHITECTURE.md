# Module Architecture Documentation

## Overview

The `modules/` directory contains 19 core modules that provide the foundational functionality for Network Swiss Tool Pro. These modules handle network operations, device connectivity, topology mapping, plugin management, and other core application features.

## Modules Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         vlan_checker_web.py                       │
│                         (Flask Application)                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        plugin_registry.py                         │
│                    (Plugin Management & Discovery)               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│      network_base.py         │  │       adapters.py             │
│   (Network Operations Core)   │  │   (Platform Adapters)         │
└──────────────────────────────┘  └──────────────────────────────┘
                    │                           │
        ┌───────────┼───────────┐               │
        ▼           ▼           ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ connectivity│ │ interfaces  │ │  vlan_audit  │ │ cli_manager │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
        │           │           │               │
        └───────────┼───────────┴───────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    topology_mapper.py                             │
│                 (Topology & vPC Analysis)                         │
└─────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│node_analyze │ │node_        │ │stp_swiss_   │
│             │ │interface_   │ │runner       │
│             │ │topology     │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│mac_trace    │ │description_ │ │config_backup│
│             │ │search       │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│network_audit │ │vlan_compare │ │save_config  │
│             │ │             │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              vlan_mgmt_production.py                             │
│              (VLAN Management Operations)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Design Patterns

### Singleton Pattern
- `plugin_registry.py` - PluginRegistry singleton for centralized plugin management

### Factory Pattern
- `adapters.py` - Platform-specific adapter factory for device operations
- `network_base.py` - Connection factory for different device types

### Strategy Pattern
- `topology_mapper.py` - Different topology mapping strategies (standard, vPC, discovery)

### Observer Pattern
- `cli_manager.py` - CLI terminal event handling and session management

---

## Core Modules

### network_base.py
**Purpose**: Core network operations foundation providing connection management, hostname resolution, and common network utilities.

**Key Classes/Functions**:
- `safe_connection(device, username, password, secret, log_func)` - Context manager for safe device connections
- `connect_permissive(device, username, password, secret, log_func)` - Permissive connection with error handling
- `build_json(host, status, data, error)` - Build standardized JSON response
- `safe_node_name(name)` - Sanitize node names for graph visualization
- `resolve_hostname_from_prompt(conn, host)` - Resolve hostname from device prompt
- `resolve_device_hostname(conn, host, device_type)` - Resolve device hostname with platform-specific logic

**Dependencies**: None (foundational module)

**Used By**: All operation modules (connectivity, interfaces, topology_mapper, etc.)

---

### plugin_registry.py
**Purpose**: Centralized plugin management including discovery, validation, loading, and backup/restore operations.

**Key Classes/Functions**:
- `PluginRegistry` - Singleton registry for plugin management
  - `discover_plugins()` - Discover plugins from modules/plugins/ directory
  - `validate_plugin(plugin_id, plugin_module)` - Validate plugin METADATA structure
  - `load_plugin(plugin_id)` - Load plugin module
  - `execute_plugin(plugin_id, device, credentials, params, config, log_func)` - Execute plugin
  - `backup_plugin(plugin_id)` - Backup plugin to archive
  - `restore_plugin(plugin_id, version)` - Restore plugin from backup
  - `get_errors()` - Get plugin loading errors

**Dependencies**: network_base.py, utils.report_formatter

**Used By**: vlan_checker_web.py (Flask routes)

---

### adapters.py
**Purpose**: Platform-specific adapters for device operations, providing unified interface across different network operating systems.

**Key Classes/Functions**:
- `CiscoIOSAdapter` - Cisco IOS specific operations
- `CiscoNXOSAdapter` - Cisco NX-OS specific operations
- `JuniperJunOSAdapter` - Juniper JunOS specific operations
- `get_adapter(device_type)` - Factory function to get appropriate adapter

**Dependencies**: network_base.py

**Used By**: network_base.py, operation modules

---

### connectivity.py
**Purpose**: Device connectivity testing and validation operations.

**Key Functions**:
- `test_connectivity(device, credentials, log_func)` - Test device connectivity
- `ping_device(host, count=3)` - Ping device to verify reachability
- `check_port(host, port, timeout=5)` - Check if port is open

**Dependencies**: network_base.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### interfaces.py
**Purpose**: Interface status and configuration operations.

**Key Functions**:
- `get_interface_status(device, credentials, log_func)` - Get interface status
- `get_interface_description(device, credentials, log_func)` - Get interface descriptions
- `parse_interface_output(output, device_type)` - Parse interface command output

**Dependencies**: network_base.py, adapters.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### vlan_audit.py
**Purpose**: VLAN audit and validation operations.

**Key Functions**:
- `audit_vlan_config(device, credentials, log_func)` - Audit VLAN configuration
- `compare_vlan_databases(device1, device2)` - Compare VLAN databases
- `validate_vlan_consistency(devices)` - Validate VLAN consistency across devices

**Dependencies**: network_base.py, adapters.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### topology_mapper.py
**Purpose**: Network topology mapping and vPC domain analysis.

**Key Classes/Functions**:
- `TopologyMapper` - Main topology mapping class
  - `map_topology(devices, credentials, log_func)` - Map network topology
  - `map_vpc_domain(devices, credentials, log_func)` - Map vPC domain
  - `generate_topology_html(data)` - Generate topology HTML visualization

**Dependencies**: network_base.py, adapters.py, node_analyze.py, node_interface_topology.py

**Used By**: vlan_checker_web.py (API endpoint), vpc_domain_plugin

---

### node_analyze.py
**Purpose**: Node analysis for topology mapping including device classification and neighbor detection.

**Key Functions**:
- `analyze_node(device, credentials, log_func)` - Analyze device node
- `classify_device(device_type)` - Classify device type
- `detect_neighbors(device, credentials, log_func)` - Detect CDP/LLDP neighbors

**Dependencies**: network_base.py, adapters.py

**Used By**: topology_mapper.py

---

### node_interface_topology.py
**Purpose**: Interface-level topology analysis for detailed network mapping.

**Key Functions**:
- `build_interface_topology(devices, credentials, log_func)` - Build interface-level topology
- `extract_link_information(interface_data)` - Extract link information
- `validate_topology_consistency(topology)` - Validate topology consistency

**Dependencies**: network_base.py, adapters.py

**Used By**: topology_mapper.py

---

### stp_swiss_runner.py
**Purpose**: STP Swiss Tools execution for STP topology analysis and visualization.

**Key Functions**:
- `run_stp_analysis(devices, credentials, params, log_func)` - Run STP analysis
- `generate_stp_map(stp_data)` - Generate STP topology map
- `validate_stp_configuration(stp_data)` - Validate STP configuration

**Dependencies**: network_base.py, adapters.py, utils.stp_map_formatter

**Used By**: vlan_checker_web.py (API endpoint), stp_topology_visualizer plugin

---

### mac_trace.py
**Purpose**: MAC address trace operations for tracking MAC address paths through the network.

**Key Functions**:
- `trace_mac_address(mac_address, devices, credentials, log_func)` - Trace MAC address path
- `parse_mac_table(output, device_type)` - Parse MAC address table
- `build_mac_path(mac_data)` - Build MAC address path

**Dependencies**: network_base.py, adapters.py, utils.mac_trace_formatter, **utils.mac_utils** (v7.0.28+ normalization)

**Used By**: vlan_checker_web.py (API endpoint)

**Related**: `utils/juniper_iface.py` used by interface map correlation (not direct dependency of mac_trace)

---

### description_search.py
**Purpose**: Interface description search operations for finding devices by interface descriptions.

**Key Functions**:
- `search_descriptions(search_term, devices, credentials, log_func)` - Search interface descriptions
- `parse_description_output(output, device_type)` - Parse description command output
- `filter_results(results, criteria)` - Filter search results

**Dependencies**: network_base.py, adapters.py, utils.description_search_formatter

**Used By**: vlan_checker_web.py (API endpoint)

---

### config_backup.py
**Purpose**: Configuration backup operations for network devices.

**Key Functions**:
- `backup_config(device, credentials, log_func)` - Backup device configuration
- `restore_config(device, backup_path, credentials, log_func)` - Restore configuration
- `compare_configs(config1, config2)` - Compare two configurations

**Dependencies**: network_base.py, adapters.py, utils.config_backup_system

**Used By**: vlan_checker_web.py (API endpoint)

---

### network_audit.py
**Purpose**: Network audit operations for comprehensive network analysis.

**Key Functions**:
- `run_network_audit(devices, credentials, log_func)` - Run comprehensive network audit
- `audit_security(devices, credentials, log_func)` - Audit security configuration
- `audit_performance(devices, credentials, log_func)` - Audit performance metrics

**Dependencies**: network_base.py, adapters.py, connectivity.py, interfaces.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### vlan_compare.py
**Purpose**: VLAN comparison operations for comparing VLAN configurations across devices.

**Key Functions**:
- `compare_vlan_configs(device1, device2, credentials, log_func)` - Compare VLAN configurations
- `find_vlan_differences(vlan1, vlan2)` - Find VLAN differences
- `generate_vlan_report(differences)` - Generate VLAN comparison report

**Dependencies**: network_base.py, adapters.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### save_config.py
**Purpose**: Save configuration operations for committing changes to devices.

**Key Functions**:
- `save_config(device, credentials, log_func)` - Save running configuration to startup
- `validate_save(output, device_type)` - Validate save operation output

**Dependencies**: network_base.py, adapters.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### vlan_mgmt_production.py
**Purpose**: Production VLAN management operations for VLAN creation, modification, and deletion.

**Key Functions**:
- `create_vlan(device, vlan_id, name, credentials, log_func)` - Create VLAN
- `delete_vlan(device, vlan_id, credentials, log_func)` - Delete VLAN
- `rename_vlan(device, vlan_id, new_name, credentials, log_func)` - Rename VLAN
- `add_vlan_to_trunk(device, vlan_id, trunk_port, credentials, log_func)` - Add VLAN to trunk
- `remove_vlan_from_trunk(device, vlan_id, trunk_port, credentials, log_func)` - Remove VLAN from trunk

**Dependencies**: network_base.py, adapters.py

**Used By**: vlan_checker_web.py (API endpoint)

---

### cli_manager.py
**Purpose**: CLI terminal management for interactive device sessions via WebSocket.

**Key Classes/Functions**:
- `CLISession` - CLI session manager
  - `connect(device, credentials)` - Connect to device
  - `send_command(command)` - Send command to device
  - `receive_output()` - Receive output from device
  - `resize_pty(cols, rows)` - Resize PTY
  - `disconnect()` - Disconnect from device

**Dependencies**: network_base.py, adapters.py

**Used By**: vlan_checker_web.py (WebSocket events)

---

## Module Boundaries

### Core Foundation Layer
- `network_base.py` - Foundational network operations (no dependencies on other modules)
- `plugin_registry.py` - Plugin management (depends on network_base.py)

### Adapter Layer
- `adapters.py` - Platform-specific adapters (depends on network_base.py)

### Operation Layer
- `connectivity.py` - Connectivity operations (depends on network_base.py)
- `interfaces.py` - Interface operations (depends on network_base.py, adapters.py)
- `vlan_audit.py` - VLAN audit operations (depends on network_base.py, adapters.py)
- `config_backup.py` - Configuration backup (depends on network_base.py, adapters.py)
- `save_config.py` - Save configuration (depends on network_base.py, adapters.py)

### Analysis Layer
- `topology_mapper.py` - Topology mapping (depends on network_base.py, adapters.py, node_analyze.py, node_interface_topology.py)
- `node_analyze.py` - Node analysis (depends on network_base.py, adapters.py)
- `node_interface_topology.py` - Interface topology (depends on network_base.py, adapters.py)
- `stp_swiss_runner.py` - STP analysis (depends on network_base.py, adapters.py)

### Search Layer
- `mac_trace.py` - MAC trace (depends on network_base.py, adapters.py)
- `description_search.py` - Description search (depends on network_base.py, adapters.py)

### Management Layer
- `network_audit.py` - Network audit (depends on network_base.py, adapters.py, connectivity.py, interfaces.py)
- `vlan_compare.py` - VLAN comparison (depends on network_base.py, adapters.py)
- `vlan_mgmt_production.py` - VLAN management (depends on network_base.py, adapters.py)

### Interaction Layer
- `cli_manager.py` - CLI terminal (depends on network_base.py, adapters.py)

---

## Data Flow

### Typical Operation Flow
1. **Request** → vlan_checker_web.py (Flask route)
2. **Validation** → network_base.py (build_json, safe_node_name)
3. **Connection** → network_base.py (safe_connection)
4. **Adapter Selection** → adapters.py (get_adapter)
5. **Operation Execution** → Operation module (e.g., connectivity.py)
6. **Result Formatting** → utils.report_formatter.py
7. **Response** → vlan_checker_web.py (JSON response)

### Plugin Execution Flow
1. **Plugin Discovery** → plugin_registry.py (discover_plugins)
2. **Plugin Validation** → plugin_registry.py (validate_plugin)
3. **Plugin Loading** → plugin_registry.py (load_plugin)
4. **Plugin Execution** → plugin_registry.py (execute_plugin)
5. **Result Formatting** → utils.report_formatter.py
6. **Response** → vlan_checker_web.py (JSON response)

---

## Dependencies Summary

### No Dependencies (Foundational)
- network_base.py

### Depends on network_base.py
- plugin_registry.py
- adapters.py
- connectivity.py
- interfaces.py
- vlan_audit.py
- config_backup.py
- save_config.py

### Depends on network_base.py + adapters.py
- topology_mapper.py
- node_analyze.py
- node_interface_topology.py
- stp_swiss_runner.py
- mac_trace.py
- description_search.py
- vlan_compare.py
- vlan_mgmt_production.py
- cli_manager.py

### Depends on network_base.py + adapters.py + other modules
- topology_mapper.py (depends on node_analyze.py, node_interface_topology.py)
- network_audit.py (depends on connectivity.py, interfaces.py)

---

## Module Interfaces

### Standard Interface Pattern
All operation modules follow this interface pattern:
```python
def operation_name(device, credentials, params, config, log_func):
    """
    Execute operation on device.
    
    Args:
        device: Device dictionary with 'host' and 'device_type'
        credentials: Dictionary with 'username', 'password', 'secret'
        params: Operation-specific parameters
        config: Application configuration
        log_func: Logging function for progress updates
    
    Returns:
        JSON response with 'status', 'data', 'error' fields
    """
```

### Plugin Interface Pattern
All plugins follow this interface pattern:
```python
METADATA = {
    "plugin_id": "plugin_name",
    "display_name": "Plugin Display Name",
    "version": "1.0.0",
    "author": "Author",
    "category": "Category",
    "description": "Plugin description",
    "min_platform_version": "6.0.0",
    "required_params": {...},
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": True,
}

def run(device, credentials, params, config, log_func):
    """
    Execute plugin on device.
    
    Returns:
        JSON response with 'status', 'data', 'error' fields
    """
```

---

## Error Handling

All modules include error handling:
- Connection errors are caught and returned in JSON response
- Parsing errors are logged and returned with descriptive messages
- Validation errors are returned with specific field information
- All errors include stack traces in logs for debugging

---

## Thread Safety

- `plugin_registry.py` - Singleton with thread-safe operations
- `cli_manager.py` - Session management with thread-safe operations
- Other modules - Stateless operations, thread-safe for concurrent use

---

## Extension Points

### Adding New Operations
1. Create new module in modules/ directory
2. Follow standard interface pattern
3. Use network_base.py for connections
4. Use adapters.py for platform-specific operations
5. Add Flask route in vlan_checker_web.py
6. Add UI integration in index.html

### Adding New Plugins
1. Create plugin in modules/plugins/ directory
2. Follow plugin interface pattern
3. Include METADATA dictionary
4. Implement run() function
5. Plugin will be auto-discovered by plugin_registry.py

---

## Complex Edge Cases

### 1. Device Connection Failures

**Edge Case:** Device connection fails during operation

**Scenarios:**
- Device unreachable (network timeout)
- Authentication failure (wrong credentials)
- SSH/Telnet port closed
- Device in maintenance mode
- Connection dropped mid-operation

**Handling Strategy:**
```python
try:
    with safe_connection(device, username, password, secret, log_func) as conn:
        # Execute operation
        pass
except ConnectionError as e:
    log_func(f"Connection failed: {e}")
    return build_json(device, "error", None, str(e))
except AuthenticationError as e:
    log_func(f"Authentication failed: {e}")
    return build_json(device, "error", None, str(e))
except TimeoutError as e:
    log_func(f"Connection timeout: {e}")
    return build_json(device, "error", None, str(e))
```

**Prevention:**
- Implement connection timeout (default: 30 seconds)
- Use permissive connection mode for initial connectivity test
- Implement retry logic with exponential backoff
- Validate credentials before operation
- Monitor device availability

---

### 2. CLI Output Parsing Failures

**Edge Case:** CLI output format changes or unexpected output

**Scenarios:**
- OS version changes output format
- Custom device configuration alters output
- Partial output due to device issues
- Multiline output with inconsistent formatting
- Unicode characters in output

**Handling Strategy:**
```python
try:
    output = conn.send_command(command)
    parsed = parse_output(output, device_type)
    if not parsed:
        log_func(f"Parse failed, using raw output")
        return build_json(device, "success", {"raw": output}, None)
except ParseError as e:
    log_func(f"Parse error: {e}")
    return build_json(device, "warning", {"raw": output}, str(e))
```

**Prevention:**
- Use multiple parsing strategies (TextFSM, regex, fallback)
- Validate parsed output structure
- Include raw output in response for debugging
- Test parsing against multiple OS versions
- Handle Unicode characters properly

---

### 3. Plugin Loading Conflicts

**Edge Case:** Plugin loading fails due to conflicts or errors

**Scenarios:**
- Duplicate plugin IDs
- Missing dependencies
- Invalid METADATA structure
- Import errors in plugin code
- Version incompatibility

**Handling Strategy:**
```python
def load_plugin(plugin_id):
    try:
        plugin_module = importlib.import_module(f"modules.plugins.{plugin_id}")
        validate_plugin(plugin_id, plugin_module)
        return plugin_module
except ImportError as e:
    log_plugin_error(plugin_id, f"Import failed: {e}")
    return None
except ValidationError as e:
    log_plugin_error(plugin_id, f"Validation failed: {e}")
    return None
```

**Prevention:**
- Validate plugin ID uniqueness before loading
- Check dependencies before loading
- Validate METADATA structure
- Test plugin in isolation
- Use plugin backup/restore for recovery

---

### 4. Concurrent Job Execution Conflicts

**Edge Case:** Multiple jobs accessing same device simultaneously

**Scenarios:**
- Two operations on same device at same time
- CLI session conflicts
- Configuration conflicts
- Resource exhaustion
- Lock contention

**Handling Strategy:**
```python
# Use device-level locking
device_locks = {}

def acquire_device_lock(device_ip):
    if device_ip in device_locks:
        return False
    device_locks[device_ip] = True
    return True

def release_device_lock(device_ip):
    if device_ip in device_locks:
        del device_locks[device_ip]
```

**Prevention:**
- Implement device-level locking
- Queue operations for same device
- Use job priority for scheduling
- Implement timeout for locks
- Monitor lock contention

---

### 5. Large-Scale Discovery Timeout

**Edge Case:** Network discovery takes too long or hangs

**Scenarios:**
- Large network with many devices
- Slow device responses
- Network latency
- Crawl depth too deep
- Discovery loop (circular topology)

**Handling Strategy:**
```python
def run_discovery(seed_hosts, crawl_depth, timeout):
    discovered = set()
    queue = seed_hosts[:]
    start_time = time.time()
    
    while queue and (time.time() - start_time) < timeout:
        if len(discovered) > MAX_DEVICES:
            break
        # Process next device
        # Add to discovered set
        # Add neighbors to queue if depth not exceeded
```

**Prevention:**
- Implement per-device timeout
- Limit crawl depth (default: 3)
- Limit total devices (default: 100)
- Track visited devices to prevent loops
- Implement progress monitoring

---

### 6. Memory Exhaustion with Large Datasets

**Edge Case:** Operations fail due to memory exhaustion

**Scenarios:**
- Large configuration files
- Many devices in single operation
- Large topology graphs
- Extensive log data
- Large report generation

**Handling Strategy:**
```python
def process_large_dataset(data, chunk_size=100):
    results = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        result = process_chunk(chunk)
        results.append(result)
        # Clear memory
        del chunk
    return results
```

**Prevention:**
- Process data in chunks
- Stream large files instead of loading all
- Use generators instead of lists
- Implement memory monitoring
- Set memory limits for operations

---

### 7. File System Errors

**Edge Case:** File operations fail due to file system issues

**Scenarios:**
- Disk full
- Permission denied
- File locked by another process
- Invalid file path
- Network drive unavailable

**Handling Strategy:**
```python
def write_report(content, filename):
    try:
        with open(filename, 'w') as f:
            f.write(content)
    except PermissionError:
        log_func("Permission denied, using temp file")
        temp_file = f"temp_{filename}"
        with open(temp_file, 'w') as f:
            f.write(content)
        return temp_file
    except OSError as e:
        log_func(f"File system error: {e}")
        return None
```

**Prevention:**
- Check disk space before writing
- Validate file permissions
- Use temporary files for large writes
- Implement file locking
- Handle network drive failures

---

### 8. WebSocket Connection Drops

**Edge Case:** CLI terminal WebSocket connection drops

**Scenarios:**
- Network interruption
- Browser tab closed
- Server restart
- Session timeout
- Device disconnect

**Handling Strategy:**
```python
class CLISession:
    def __init__(self):
        self.last_activity = time.time()
        self.timeout = 300  # 5 minutes
    
    def check_timeout(self):
        if time.time() - self.last_activity > self.timeout:
            self.disconnect()
            return True
        return False
```

**Prevention:**
- Implement session timeout
- Send keepalive messages
- Auto-reconnect on disconnect
- Save session state for recovery
- Monitor connection health

---

### 9. Policy Validation Errors

**Edge Case:** Policy file validation fails

**Scenarios:**
- Invalid YAML syntax
- Invalid regex patterns
- Invalid severity levels
- Invalid platform names
- Circular policy dependencies

**Handling Strategy:**
```python
def validate_policy(policy):
    try:
        # Validate YAML syntax
        yaml.safe_load(policy)
        # Validate structure
        validate_policy_structure(policy)
        # Validate regex patterns
        for p in policy['policies']:
            re.compile(p['pattern'])
        return True
except yaml.YAMLError as e:
    log_policy_error(f"YAML error: {e}")
    return False
except re.error as e:
    log_policy_error(f"Regex error: {e}")
    return False
```

**Prevention:**
- Use YAML validator before loading
- Test regex patterns
- Validate severity levels
- Validate platform names
- Check for circular dependencies

---

### 10. Template Rendering Failures

**Edge Case:** Jinja2 template rendering fails

**Scenarios:**
- Missing template variables
- Invalid variable types
- Template syntax errors
- Undefined variables
- Filter errors

**Handling Strategy:**
```python
def render_template(template_name, variables):
    try:
        template = jinja_env.get_template(template_name)
        return template.render(**variables)
except jinja2.TemplateNotFound:
    log_func(f"Template not found: {template_name}")
    return None
except jinja2.UndefinedError as e:
        log_func(f"Undefined variable: {e}")
        return None
except jinja2.TemplateSyntaxError as e:
    log_func(f"Template syntax error: {e}")
    return None
```

**Prevention:**
- Validate required variables before rendering
- Use default values for optional variables
- Test template syntax
- Handle undefined variables gracefully
- Validate variable types

---

### 11. STP Topology Inconsistencies

**Edge Case:** STP topology data is inconsistent or incomplete

**Scenarios:**
- Missing root bridge information
- Inconsistent bridge priorities
- Missing link information
- VLAN mismatch
- STP state conflicts

**Handling Strategy:**
```python
def validate_stp_topology(stp_data):
    if not stp_data.get('root_bridge'):
        log_func("Missing root bridge, inferring from data")
        stp_data['root_bridge'] = infer_root_bridge(stp_data)
    
    if not stp_data.get('bridges'):
        log_func("No bridges found, using default")
        stp_data['bridges'] = []
    
    return stp_data
```

**Prevention:**
- Validate STP data completeness
- Infer missing information when possible
- Use default values for optional fields
- Log inconsistencies for review
- Provide warnings for incomplete data

---

### 12. vPC Domain Inconsistencies

**Edge Case:** vPC domain data is inconsistent between peers

**Scenarios:**
- Peer keepalive mismatch
- Role conflict (both primary)
- Configuration inconsistency
- Peer link down
- vPC ID mismatch

**Handling Strategy:**
```python
def validate_vpc_domain(vpc_data):
    peers = vpc_data.get('vpc_peers', [])
    
    # Check for role conflicts
    primary_count = sum(1 for p in peers if p['role'] == 'primary')
    if primary_count > 1:
        log_func("Multiple primary peers detected, using lowest priority")
        peers.sort(key=lambda x: x.get('priority', 999))
        for i, p in enumerate(peers):
            p['role'] = 'primary' if i == 0 else 'secondary'
    
    return vpc_data
```

**Prevention:**
- Validate vPC peer roles
- Check configuration consistency
- Monitor peer link status
- Validate vPC ID consistency
- Implement role conflict resolution

---

### 13. MAC Address Trace Failures

**Edge Case:** MAC address trace fails to find complete path

**Scenarios:**
- MAC not found in any device
- Incomplete MAC table data
- MAC address moves during trace
- VLAN mismatch
- Device unreachable during trace

**Handling Strategy:**
```python
def trace_mac_address(mac, devices):
    path = []
    for device in devices:
        try:
            mac_entry = find_mac_on_device(device, mac)
            if mac_entry:
                path.append({
                    'device': device['host'],
                    'interface': mac_entry['interface'],
                    'vlan': mac_entry['vlan']
                })
        except DeviceError as e:
            log_func(f"Device error during trace: {e}")
            continue
    
    if not path:
        log_func(f"MAC {mac} not found on any device")
    
    return path
```

**Prevention:**
- Continue trace on device errors
- Log partial results
- Validate MAC address format
- Handle VLAN mismatches
- Implement timeout for trace

---

### 14. Configuration Backup Failures

**Edge Case:** Configuration backup fails or is incomplete

**Scenarios:**
- Device unreachable during backup
- Backup file write failure
- Configuration too large
- Special characters in configuration
- Backup interrupted

**Handling Strategy:**
```python
def backup_config(device, credentials):
    try:
        config = get_running_config(device, credentials)
        if not config:
            raise BackupError("Empty configuration")
        
        backup_file = save_backup(device, config)
        return backup_file
    except DeviceError as e:
        log_func(f"Device error during backup: {e}")
        return None
    except IOError as e:
        log_func(f"File error during backup: {e}")
        return None
```

**Prevention:**
- Validate configuration before saving
- Use checksums to verify backup integrity
- Implement backup retry logic
- Monitor disk space
- Use compression for large configurations

---

### 15. Health Check False Positives

**Edge Case:** Health checks report false positives or false negatives

**Scenarios:**
- Temporary network issues
- Resource spikes
- Timing issues
- Check logic errors
- Environmental differences

**Handling Strategy:**
```python
def run_health_check(check_name):
    # Run check multiple times for consistency
    results = []
    for _ in range(3):
        result = execute_check(check_name)
        results.append(result)
        time.sleep(1)
    
    # Use majority vote
    if results.count('pass') >= 2:
        return 'pass'
    elif results.count('fail') >= 2:
        return 'fail'
    else:
        return 'inconclusive'
```

**Prevention:**
- Run checks multiple times
- Use majority vote for consistency
- Implement check thresholds
- Monitor check history
- Adjust check sensitivity

---

## Boundary Conditions

### Device Count Limits
- **Minimum:** 1 device
- **Recommended:** 10-100 devices per operation
- **Maximum:** 1000 devices (with chunking)
- **Handling:** Process in chunks for large device counts

### Timeout Limits
- **Connection Timeout:** 30 seconds (configurable)
- **Operation Timeout:** 300 seconds (configurable)
- **Discovery Timeout:** 600 seconds (configurable)
- **CLI Session Timeout:** 300 seconds (configurable)

### Data Size Limits
- **Configuration File:** 10 MB maximum
- **Report File:** 50 MB maximum
- **Inventory File:** 1000 devices maximum
- **Policy File:** 5 MB maximum

### Concurrency Limits
- **Max Concurrent Connections:** 100 (configurable)
- **Max Concurrent Jobs:** 10 (configurable)
- **Max CLI Sessions:** 50 (configurable)
- **Max Plugin Executions:** 20 (configurable)

---

## Special Cases

### Demo Mode
- **Purpose:** Allow testing without real devices
- **Implementation:** Use mock data and simulated responses
- **Handling:** Check demo_mode flag before real operations
- **Validation:** Ensure demo data matches expected format

### Dry Run Mode
- **Purpose:** Preview operations without executing
- **Implementation:** Validate parameters and show expected changes
- **Handling:** Skip actual device commands
- **Validation:** Return expected results without execution

### Bulk Operations
- **Purpose:** Execute operation on multiple devices
- **Implementation:** Process devices in parallel with thread pool
- **Handling:** Aggregate results and handle partial failures
- **Validation:** Validate all device parameters before execution

### Rollback Operations
- **Purpose:** Undo changes made by operations
- **Implementation:** Store pre-operation state for rollback
- **Handling:** Execute reverse operations to restore state
- **Validation:** Verify rollback success with validation checks
