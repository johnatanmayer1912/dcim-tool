# Code Inventory

## Overview

This document provides a comprehensive inventory of all code components in Network Swiss Tool Pro v7.0.29.

**Generated:** 2026-06-02 · **Last synced:** 2026-06-10  
**Purpose:** Code-to-documentation traceability for comprehensive documentation audit

---

## Root-Level Python Files

### vlan_checker_web.py
**Purpose:** Main Flask application with REST API and WebSocket endpoints  
**Lines:** ~2500+  
**Key Components:**
- Flask app initialization
- SocketIO integration
- 40+ REST API endpoints
- 4 WebSocket events (CLI terminal)
- Plugin management integration
- Standards validator integration
- Network discovery integration
- Health check integration
- Search_it operations (MAC trace, description search, ping scan)
- STP Swiss Tools integration
- Config templates integration
- Topology mapper integration

**Dependencies:** Flask, Flask-SocketIO, Netmiko, Paramiko, Jinja2, YAML, TextFSM, NTC Templates

---

### main.py
**Purpose:** Legacy main entry point (deprecated, use vlan_checker_web.py)  
**Lines:** ~50  
**Key Components:**
- Application launcher
- Configuration loading

---

### runtime_hook_telnetlib.py
**Purpose:** PyInstaller runtime hook for telnetlib compatibility (Python 3.13+)  
**Lines:** ~20  
**Key Components:**
- Telnetlib compatibility check
- Import telnetlib_compat as telnetlib

---

### telnetlib_compat.py
**Purpose:** Telnetlib compatibility module for Python 3.13+  
**Lines:** ~100  
**Key Components:**
- Telnet class implementation
- Telnet connection methods
- Compatibility layer for removed telnetlib

---

### create_plugin.py
**Purpose:** Plugin scaffolding script for creating new plugins  
**Lines:** ~100  
**Key Components:**
- Plugin template generation
- METADATA structure creation
- Plugin file creation

---

### generate_plugin_docs.py
**Purpose:** Generate documentation for plugins  
**Lines:** ~150  
**Key Components:**
- Plugin documentation generation
- README.md creation
- PROMPT.md creation
- CHANGELOG.md creation

---

### make_bat.py
**Purpose:** Generate batch files for Windows  
**Lines:** ~50  
**Key Components:**
- Batch file generation
- Windows script creation

---

### _prebuild.py
**Purpose:** Pre-build checks and validation  
**Lines:** ~100  
**Key Components:**
- Build validation
- Dependency checks
- Environment validation

---

### _check_plugin_path.py
**Purpose:** Check plugin path configuration  
**Lines:** ~50  
**Key Components:**
- Plugin path validation
- Path resolution

---

### _check_yaml.py
**Purpose:** Validate YAML configuration files  
**Lines:** ~50  
**Key Components:**
- YAML validation
- Syntax checking

---

### _cli_diagnostic_server.py
**Purpose:** CLI diagnostic server for troubleshooting  
**Lines:** ~100  
**Key Components:**
- Diagnostic server
- CLI testing
- Connection validation

---

### _fix_bugs.py
**Purpose:** Bug fixing script (development tool)  
**Lines:** ~100  
**Key Components:**
- Bug identification
- Automated fixes

---

### _master_qa_test.py
**Purpose:** Master QA test suite  
**Lines:** ~200  
**Key Components:**
- Comprehensive QA tests
- Integration tests
- Validation tests

---

### _test_v622.py
**Purpose:** Version 6.2.2 specific tests  
**Lines:** ~100  
**Key Components:**
- Version-specific tests
- Regression tests

---

### create_demo_discovery_map_v7.py
**Purpose:** Create demo discovery map for v7  
**Lines:** ~150  
**Key Components:**
- Demo data generation
- Discovery map creation
- Visualization generation

---

### create_demo_map.py
**Purpose:** Create demo topology map  
**Lines:** ~100  
**Key Components:**
- Demo topology generation
- Map visualization

---

### create_demo_map_v7.py
**Purpose:** Create demo topology map for v7  
**Lines:** ~150  
**Key Components:**
- Demo topology generation
- v7-specific features
- Map visualization

---

### f5_manager_gui.py
**Purpose:** F5 device manager GUI  
**Lines:** ~200  
**Key Components:**
- F5 device management
- GUI interface
- Configuration management

---

### test_plugins.py
**Purpose:** Plugin testing script  
**Lines:** ~100  
**Key Components:**
- Plugin validation
- Plugin testing
- Plugin loading tests

---

### test_socketio.py
**Purpose:** SocketIO testing script  
**Lines:** ~100  
**Key Components:**
- WebSocket testing
- SocketIO validation
- Connection testing

---

### vlan_checker_gui.py
**Purpose:** Legacy GUI application (deprecated)  
**Lines:** ~500  
**Key Components:**
- GUI interface
- VLAN checking
- Network operations

---

## Modules (modules/)

### network_base.py
**Purpose:** Core network operations foundation  
**Lines:** ~500  
**Key Components:**
- `safe_connection()` - Context manager for device connections
- `connect_permissive()` - Permissive connection with error handling
- `build_json()` - Build standardized JSON response
- `safe_node_name()` - Sanitize node names for graph visualization
- `resolve_hostname_from_prompt()` - Resolve hostname from device prompt
- `resolve_device_hostname()` - Resolve device hostname with platform-specific logic
- `_get_resource_path()` - Resource path resolution for EXE compatibility

**Dependencies:** None (foundational module)

---

### plugin_registry.py
**Purpose:** Centralized plugin management  
**Lines:** ~600  
**Key Components:**
- `PluginRegistry` class - Singleton registry
  - `discover_plugins()` - Discover plugins from modules/plugins/
  - `validate_plugin()` - Validate plugin METADATA structure
  - `load_plugin()` - Load plugin module
  - `execute_plugin()` - Execute plugin
  - `backup_plugin()` - Backup plugin to archive
  - `restore_plugin()` - Restore plugin from backup
  - `get_errors()` - Get plugin loading errors

**Dependencies:** network_base.py, utils.report_formatter

---

### adapters.py
**Purpose:** Platform-specific adapters for device operations  
**Lines:** ~400  
**Key Components:**
- `CiscoIOSAdapter` class - Cisco IOS specific operations
- `CiscoNXOSAdapter` class - Cisco NX-OS specific operations
- `JuniperJunOSAdapter` class - Juniper JunOS specific operations
- `get_adapter()` - Factory function to get appropriate adapter

**Dependencies:** network_base.py

---

### connectivity.py
**Purpose:** Device connectivity testing and validation  
**Lines:** ~200  
**Key Components:**
- `test_connectivity()` - Test device connectivity
- `ping_device()` - Ping device to verify reachability
- `check_port()` - Check if port is open

**Dependencies:** network_base.py

---

### interfaces.py
**Purpose:** Interface status and configuration operations  
**Lines:** ~300  
**Key Components:**
- `get_interface_status()` - Get interface status
- `get_interface_description()` - Get interface descriptions
- `parse_interface_output()` - Parse interface command output

**Dependencies:** network_base.py, adapters.py

---

### vlan_audit.py
**Purpose:** VLAN audit and validation operations  
**Lines:** ~300  
**Key Components:**
- `audit_vlan_config()` - Audit VLAN configuration
- `compare_vlan_databases()` - Compare VLAN databases
- `validate_vlan_consistency()` - Validate VLAN consistency across devices

**Dependencies:** network_base.py, adapters.py

---

### topology_mapper.py
**Purpose:** Network topology mapping and vPC domain analysis  
**Lines:** ~500  
**Key Components:**
- `TopologyMapper` class
  - `map_topology()` - Map network topology
  - `map_vpc_domain()` - Map vPC domain
  - `generate_topology_html()` - Generate topology HTML visualization

**Dependencies:** network_base.py, adapters.py, node_analyze.py, node_interface_topology.py

---

### node_analyze.py
**Purpose:** Node analysis for topology mapping  
**Lines:** ~300  
**Key Components:**
- `analyze_node()` - Analyze device node
- `classify_device()` - Classify device type
- `detect_neighbors()` - Detect CDP/LLDP neighbors

**Dependencies:** network_base.py, adapters.py

---

### node_interface_topology.py
**Purpose:** Interface-level topology analysis  
**Lines:** ~400  
**Key Components:**
- `build_interface_topology()` - Build interface-level topology
- `extract_link_information()` - Extract link information
- `validate_topology_consistency()` - Validate topology consistency

**Dependencies:** network_base.py, adapters.py

---

### stp_swiss_runner.py
**Purpose:** STP Swiss Tools execution  
**Lines:** ~400  
**Key Components:**
- `run_stp_analysis()` - Run STP analysis
- `generate_stp_map()` - Generate STP topology map
- `validate_stp_configuration()` - Validate STP configuration

**Dependencies:** network_base.py, adapters.py, utils.stp_map_formatter

---

### mac_trace.py
**Purpose:** MAC address trace operations  
**Lines:** ~300  
**Key Components:**
- `trace_mac_address()` - Trace MAC address path
- `parse_mac_table()` - Parse MAC address table
- `build_mac_path()` - Build MAC address path

**Dependencies:** network_base.py, adapters.py, utils.mac_trace_formatter

---

### description_search.py
**Purpose:** Interface description search operations  
**Lines:** ~300  
**Key Components:**
- `search_descriptions()` - Search interface descriptions
- `parse_description_output()` - Parse description command output
- `filter_results()` - Filter search results

**Dependencies:** network_base.py, adapters.py, utils.description_search_formatter

---

### config_backup.py
**Purpose:** Configuration backup operations  
**Lines:** ~300  
**Key Components:**
- `backup_config()` - Backup device configuration
- `restore_config()` - Restore configuration
- `compare_configs()` - Compare two configurations

**Dependencies:** network_base.py, adapters.py, utils.config_backup_system

---

### network_audit.py
**Purpose:** Network audit operations  
**Lines:** ~400  
**Key Components:**
- `run_network_audit()` - Run comprehensive network audit
- `audit_security()` - Audit security configuration
- `audit_performance()` - Audit performance metrics

**Dependencies:** network_base.py, adapters.py, connectivity.py, interfaces.py

---

### vlan_compare.py
**Purpose:** VLAN comparison operations  
**Lines:** ~300  
**Key Components:**
- `compare_vlan_configs()` - Compare VLAN configurations
- `find_vlan_differences()` - Find VLAN differences
- `generate_vlan_report()` - Generate VLAN comparison report

**Dependencies:** network_base.py, adapters.py

---

### save_config.py
**Purpose:** Save configuration operations  
**Lines**: ~200  
**Key Components:**
- `save_config()` - Save running configuration to startup
- `validate_save()` - Validate save operation output

**Dependencies:** network_base.py, adapters.py

---

### vlan_mgmt_production.py
**Purpose:** Production VLAN management operations  
**Lines:** ~500  
**Key Components:**
- `create_vlan()` - Create VLAN
- `delete_vlan()` - Delete VLAN
- `rename_vlan()` - Rename VLAN
- `add_vlan_to_trunk()` - Add VLAN to trunk
- `remove_vlan_from_trunk()` - Remove VLAN from trunk

**Dependencies:** network_base.py, adapters.py

---

### cli_manager.py
**Purpose:** CLI terminal management for WebSocket  
**Lines:** ~400  
**Key Components:**
- `CLISession` class
  - `connect()` - Connect to device
  - `send_command()` - Send command to device
  - `receive_output()` - Receive output from device
  - `resize_pty()` - Resize PTY
  - `disconnect()` - Disconnect from device

**Dependencies:** network_base.py, adapters.py

---

## Plugins (modules/plugins/)

### base_template.py
**Purpose:** Plugin base template for scaffolding  
**Lines:** ~100  
**Key Components:**
- METADATA structure template
- run() function template
- Plugin interface template

---

### network_discovery.py
**Purpose:** Network discovery and crawl plugin  
**Lines:** ~600  
**Key Components:**
- METADATA: plugin_id, display_name, version, category, description
- `run()` function
- CDP/LLDP neighbor discovery
- Platform-specific command mapping
- Graph generation
- HTML report generation

**Dependencies:** network_base.py, utils.discovery_graph, utils.discovery_map_formatter

---

### config_templates.py
**Purpose:** Configuration template management plugin  
**Lines:** ~400  
**Key Components:**
- METADATA structure
- `run()` function
- Template listing
- Template rendering
- Template saving
- Jinja2 integration

**Dependencies:** network_base.py, Jinja2

---

### critical_logs_plugin.py
**Purpose:** Critical logs analysis plugin  
**Lines:** ~300  
**Key Components:**
- METADATA structure
- `run()` function
- Log parsing
- Error identification
- Report generation

**Dependencies:** network_base.py

---

### device_time_plugin.py
**Purpose:** Device time and NTP analysis plugin  
**Lines:** ~300  
**Key Components:**
- METADATA structure
- `run()` function
- Time synchronization check
- NTP configuration analysis
- Report generation

**Dependencies:** network_base.py

---

### environment_status_plugin.py
**Purpose**: Environment status analysis plugin  
**Lines**: ~300  
**Key Components:**
- METADATA structure
- `run()` function
- Environment variables
- System status
- Report generation

**Dependencies:** network_base.py

---

### interface_errors_plugin.py
**Purpose**: Interface errors analysis plugin  
**Lines**: ~300  
**Key Components:**
- METADATA structure
- `run()` function
- Interface error parsing
- Error classification
- Report generation

**Dependencies:** network_base.py

---

### serial_number_plugin.py
**Purpose**: Serial number extraction plugin  
**Lines**: ~300  
**Key Components:**
- METADATA structure
- `run()` function
- Serial number parsing
- Asset tracking
- Report generation

**Dependencies:** network_base.py

---

### standards_validator.py
**Purpose**: Standards validation plugin  
**Lines**: ~500  
**Key Components:**
- METADATA structure
- `run()` function
- YAML policy loading
- Policy validation
- Compliance checking
- Report generation

**Dependencies:** network_base.py, YAML

---

### stp_topology_visualizer.py
**Purpose**: STP topology visualization plugin  
**Lines**: ~200  
**Key Components:**
- METADATA structure
- `run()` function
- STP data parsing
- Topology generation
- HTML report generation

**Dependencies:** network_base.py, utils.stp_map_formatter

---

### unused_trunk_pruner.py
**Purpose**: Unused trunk VLAN identification plugin  
**Lines**: ~250  
**Key Components:**
- METADATA structure
- `run()` function
- VLAN database comparison
- Ghost VLAN identification
- Pruning recommendations
- Report generation

**Dependencies:** network_base.py

---

### vlan_audit_plugin.py
**Purpose**: VLAN audit plugin  
**Lines**: ~300  
**Key Components:**
- METADATA structure
- `run()` function
- VLAN configuration audit
- Consistency validation
- Report generation

**Dependencies:** network_base.py

---

### vpc_domain_plugin.py
**Purpose**: vPC domain analysis plugin  
**Lines**: ~200  
**Key Components:**
- METADATA structure
- `run()` function
- vPC domain parsing
- Consistency parameter analysis
- Verification checks
- Report generation

**Dependencies:** network_base.py, utils.vpc_board_formatter

---

## Utilities (utils/)

### report_formatter.py
**Purpose**: Core report generation utilities  
**Lines**: ~3256  
**Key Components:**
- `write_text_file()` - Write text content to file
- `append_text_file()` - Append text to file
- `write_csv_file()` - Write CSV data to file
- `save_plugin_report()` - Save plugin report with formatted output
- `append_to_master_report()` - Append to master report file
- `init_vlan_parsed_report()` - Initialize VLAN parsed report
- `format_vlan_parsed_report()` - Format VLAN parsed report
- `format_mac_trace_report()` - Format MAC trace report
- `format_description_search_report()` - Format description search report
- `format_ping_scan_report()` - Format ping scan report
- `format_stp_report()` - Format STP report
- `format_vpc_report()` - Format vPC report
- `format_discovery_report()` - Format discovery report

**Dependencies:** os, csv, json, sys, webbrowser, datetime

---

### mac_trace_formatter.py
**Purpose**: MAC address trace result formatting  
**Lines**: ~200  
**Key Components:**
- `format_mac_trace_report()` - Format MAC trace data into text report
- `generate_mac_trace_html()` - Generate HTML visualization of MAC path

**Dependencies:** utils.report_formatter

---

### mac_utils.py
**Purpose**: MAC normalization and vendor-specific CLI search helpers (v7.0.28+)  
**Lines**: ~92  
**Key Components:**
- `normalize_mac_hex()` - Strip separators; validate hex
- `to_cisco_dotted()` / `to_junos_colon()` - Vendor CAM formats
- `cisco_search_terms()` / `junos_search_terms()` - Multi-token CLI filters
- `line_contains_mac()` / `extract_junos_interface()` - Parse helpers

**Dependencies:** re  
**Used by:** `modules/mac_trace.py`

---

### juniper_iface.py
**Purpose**: Juniper unit/bundle correlation and LACP discovery (v7.0.28+)  
**Lines**: ~102  
**Key Components:**
- `split_junos_unit()` / `resolve_junos_iface_key()` - Physical/logical mapping
- `collect_juniper_lag_detail()` - SSH LACP/AE fetch
- `enrich_interfaces_with_lag()` - Attach ae bundle metadata

**Dependencies:** `modules.topology_mapper._parse_juniper_lag_detail` (coupling note — see architecture review)  
**Used by:** `modules/plugins/interface_manager.py`, `modules/node_interface_topology.py`

---

### description_search_formatter.py
**Purpose**: Description search result formatting  
**Lines**: ~200  
**Key Components:**
- `format_description_search_report()` - Format description search results
- `generate_description_search_html()` - Generate HTML visualization

**Dependencies:** utils.report_formatter

---

### ping_scan_formatter.py
**Purpose**: Ping scan result formatting  
**Lines**: ~200  
**Key Components:**
- `format_ping_scan_report()` - Format ping scan results
- `generate_ping_scan_html()` - Generate HTML visualization

**Dependencies:** utils.report_formatter

---

### stp_map_formatter.py
**Purpose**: STP topology data formatting  
**Lines**: ~300  
**Key Components:**
- `generate_stp_html()` - Generate STP topology HTML visualization
- `format_stp_report()` - Format STP analysis report

**Dependencies:** utils.report_formatter

---

### vpc_board_formatter.py
**Purpose**: vPC domain data formatting  
**Lines**: ~300  
**Key Components:**
- `generate_vpc_board_html()` - Generate vPC engineering board HTML
- `format_vpc_report()` - Format vPC analysis report

**Dependencies:** utils.report_formatter

---

### discovery_map_formatter.py
**Purpose**: Network discovery data formatting  
**Lines**: ~300  
**Key Components:**
- `generate_discovery_html()` - Generate discovery topology HTML
- `format_discovery_report()` - Format discovery analysis report

**Dependencies:** utils.report_formatter

---

### discovery_map_shell.py
**Purpose**: Offline HTML shell for discovery map  
**Lines**: ~200  
**Key Components:**
- `generate_discovery_shell()` - Generate offline discovery map HTML
- `embed_visjs()` - Embed vis-network.js for offline use

**Dependencies:** utils.report_formatter

---

### discovery_graph.py
**Purpose**: Network discovery graph generation  
**Lines**: ~400  
**Key Components:**
- `build_discovery_graph()` - Build network topology graph
- `classify_os_family()` - Classify device OS family from platform string
- `generate_graph_json()` - Generate JSON representation of graph

**Dependencies:** networkx (if available), json

---

### topo_map_shell.py
**Purpose**: Unified topology map shell  
**Lines**: ~200  
**Key Components:**
- `generate_topo_shell()` - Generate topology map HTML
- `embed_visjs()` - Embed vis-network.js for offline use

**Dependencies:** utils.report_formatter

---

### vpc_map_shell.py
**Purpose**: vPC-specific topology map shell  
**Lines**: ~200  
**Key Components:**
- `generate_vpc_shell()` - Generate vPC topology map HTML
- `embed_visjs()` - Embed vis-network.js for offline use

**Dependencies:** utils.report_formatter

---

### search_report_output.py
**Purpose**: Generic search result formatting  
**Lines**: ~200  
**Key Components:**
- `format_search_results()` - Format search results into report
- `generate_search_html()` - Generate HTML visualization

**Dependencies:** utils.report_formatter

---

### search_it_progress.py
**Purpose**: Progress tracking for search_it operations  
**Lines**: ~150  
**Key Components:**
- `get_all_progress()` - Get progress for all search operations
- `set_progress()` - Set progress for operation
- `clear_progress()` - Clear progress for operation

**Dependencies:** threading

---

### health_check_runner.py
**Purpose**: System health check execution  
**Lines**: ~400  
**Key Components:**
- `run_health_checks()` - Run health checks
- `check_inventory()` - Validate inventory file
- `check_port()` - Validate port availability
- `check_plugins()` - Validate plugin loading
- `check_cli_smoke()` - Run CLI smoke test

**Dependencies:** network_base.py, modules.plugin_registry

---

### app_logger.py
**Purpose**: Application-level logging configuration  
**Lines**: ~100  
**Key Components:**
- `setup_logging()` - Configure application logging
- `get_logger()` - Get configured logger instance

**Dependencies:** logging

---

### structured_logger.py
**Purpose**: Structured logging with JSON format  
**Lines**: ~150  
**Key Components:**
- `log_structured()` - Log structured message with context
- `log_error()` - Log error with structured context

**Dependencies:** json, logging

---

### backup_util.py
**Purpose**: Generic backup utilities  
**Lines**: ~200  
**Key Components:**
- `backup_file()` - Backup file to backup directory
- `restore_file()` - Restore file from backup
- `rotate_backups()` - Rotate backup files to limit count

**Dependencies:** shutil, os

---

### config_backup_system.py
**Purpose**: Configuration backup system  
**Lines**: ~300  
**Key Components:**
- `backup_config()` - Backup device configuration
- `list_backups()` - List available backups for device
- `restore_config()` - Restore configuration from backup

**Dependencies:** utils.backup_util

---

### full_system_backup.py
**Purpose**: Full system backup  
**Lines**: ~300  
**Key Components:**
- `create_full_backup()` - Create full system backup
- `restore_full_backup()` - Restore full system backup
- `schedule_backup()` - Schedule automated backups

**Dependencies:** utils.backup_util, shutil

---

### debug_regex.py
**Purpose**: Regular expression debugging utilities  
**Lines**: ~100  
**Key Components:**
- `test_regex()` - Test regex pattern against string
- `debug_regex_match()` - Debug regex matching with details

**Dependencies:** re

---

## Web Templates (modules/web/templates/)

### index.html
**Purpose**: Main web application UI  
**Lines**: ~203945  
**Key Components:**
- Complete single-page application
- All UI components
- JavaScript logic
- CSS styling
- Plugin integration
- API integration
- WebSocket integration

**Dependencies:** vis-network.min.js, Flask templates

---

### cli_terminal.html
**Purpose**: CLI terminal UI component  
**Lines**: ~32960  
**Key Components:**
- Terminal emulation
- WebSocket integration
- PTY handling
- Command history
- Terminal styling

**Dependencies:** xterm.js (if used), WebSocket

---

## Jinja2 Templates (templates/)

### cisco_ios_ntp.j2
**Purpose**: Cisco IOS NTP configuration template  
**Lines**: ~277  
**Variables:** ntp_servers, timezone, source_interface

---

### cisco_ios_port_channel.j2
**Purpose**: Cisco IOS Port-Channel configuration template  
**Lines**: ~484  
**Variables:** port_channel_id, mode, members, description

---

### cisco_ios_syslog.j2
**Purpose**: Cisco IOS Syslog configuration template  
**Lines**: ~247  
**Variables:** syslog_servers, logging_level, source_interface

---

### cisco_ios_trunk.j2
**Purpose**: Cisco IOS Trunk configuration template  
**Lines**: ~333  
**Variables:** interface, allowed_vlans, native_vlan

---

### cisco_nxos_port_channel.j2
**Purpose**: Cisco NX-OS Port-Channel configuration template  
**Lines**: ~528  
**Variables:** port_channel_id, mode, members, description, vpc

---

### cisco_nxos_trunk.j2
**Purpose**: Cisco NX-OS Trunk configuration template  
**Lines**: ~321  
**Variables:** interface, allowed_vlans, native_vlan

---

### cisco_nxos_trunk_vpc.j2
**Purpose**: Cisco NX-OS vPC Trunk configuration template  
**Lines**: ~337  
**Variables:** interface, allowed_vlans, native_vlan, vpc_id

---

### juniper_junos_ntp.j2
**Purpose**: Juniper JunOS NTP configuration template  
**Lines**: ~242  
**Variables:** ntp_servers, timezone, source_interface

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Root-level Python files | 21 |
| Core modules | 19 |
| Plugins | 13 |
| Utilities | 20 |
| Web templates | 2 |
| Jinja2 templates | 8 |
| **Total Code Components** | **83** |

---

## Dependencies Summary

### Third-Party Libraries
- Flask
- Flask-SocketIO
- Netmiko
- Paramiko
- Jinja2
- PyYAML
- TextFSM
- NTC Templates
- Cryptography
- Bcrypt
- PyNaCl

### Internal Dependencies
- network_base.py (foundational)
- adapters.py (platform-specific)
- utils.report_formatter (report generation)
- utils.*_formatter.py (operation-specific formatting)

---

## Data Structures

### 1. Device Connection Structure

**Purpose:** Represents a network device connection configuration

**Format:**
```python
{
    "ip": "10.1.1.1",
    "device_type": "cisco_ios",
    "username": "admin",
    "password": "password",
    "enable_pwd": "enable_password",
    "port": 22,
    "timeout": 30
}
```

**Field Descriptions:**
- `ip` (string): Device IP address (required, valid IPv4/IPv6)
- `device_type` (string): Netmiko device type (required, must be supported)
- `username` (string): Device username (required, non-empty)
- `password` (string): Device password (required, non-empty)
- `enable_pwd` (string): Enable password (optional, for privilege escalation)
- `port` (integer): SSH/Telnet port (optional, default: 22, range: 1-65535)
- `timeout` (integer): Connection timeout in seconds (optional, default: 30, range: 1-300)

**Validation Rules:**
- IP address must be valid IPv4 or IPv6
- Device type must be supported by Netmiko
- Username and password must be non-empty
- Port must be in valid range
- Timeout must be positive integer

**Usage:** Used throughout the application for device connections in network_base.py, adapters.py, and all operation modules

---

### 2. Plugin Metadata Structure

**Purpose:** Metadata structure for plugin registration and validation

**Format:**
```python
METADATA = {
    "plugin_id": "network_discovery",
    "display_name": "Network Discovery & Crawl",
    "version": "1.4.0",
    "category": "Discovery",
    "description": "Automated network discovery and topology mapping",
    "author": "Network Team",
    "dependencies": ["network_base.py"],
    "enabled": True
}
```

**Field Descriptions:**
- `plugin_id` (string): Unique plugin identifier (required, alphanumeric with underscores)
- `display_name` (string): Human-readable plugin name (required, non-empty)
- `version` (string): Plugin version (required, semantic versioning format)
- `category` (string): Plugin category (required, predefined category)
- `description` (string): Plugin description (required, non-empty)
- `author` (string): Plugin author (optional)
- `dependencies` (list): List of required dependencies (optional, array of strings)
- `enabled` (boolean): Plugin enabled status (optional, default: True)

**Validation Rules:**
- plugin_id must be unique across all plugins
- plugin_id must be alphanumeric with underscores only
- version must follow semantic versioning (MAJOR.MINOR.PATCH)
- category must be one of predefined categories
- display_name and description must be non-empty

**Usage:** Used in plugin_registry.py for plugin discovery, validation, and loading

---

### 3. Inventory Entry Structure

**Purpose:** Single device entry in inventory.txt file

**Format:**
```python
{
    "ip": "10.1.1.1",
    "device_type": "cisco_ios",
    "group": "CoreSwitches"
}
```

**Field Descriptions:**
- `ip` (string): Device IP address (required, valid IPv4/IPv6)
- `device_type` (string): Netmiko device type (required, must be supported)
- `group` (string): Device group name (required, must match section header)

**Validation Rules:**
- IP address must be valid IPv4 or IPv6
- Device type must be supported by Netmiko
- Group must match section header in inventory file
- No duplicate IP addresses allowed

**Usage:** Used in inventory parsing and device selection for operations

---

### 4. Policy Structure (Standards Validator)

**Purpose:** Single policy definition in standards.yaml

**Format:**
```python
{
    "id": "telnet_disabled",
    "category": "Security",
    "description": "Telnet must be disabled on all VTY lines",
    "severity": "critical",
    "platforms": ["cisco_ios", "cisco_nxos", "cisco_xe"],
    "check_command": "show line vty 0 4",
    "check_type": "not_contains",
    "pattern": "transport input telnet",
    "remediation": "line vty 0 4\n transport input ssh"
}
```

**Field Descriptions:**
- `id` (string): Unique policy identifier (required, alphanumeric with underscores)
- `category` (string): Policy category (required, predefined category)
- `description` (string): Policy description (required, non-empty)
- `severity` (string): Severity level (required: critical, high, medium, low)
- `platforms` (list): Target platforms (optional, empty means all platforms)
- `check_command` (string): CLI command to execute (required, non-empty)
- `check_type` (string): Check type (required: contains, not_contains, regex_match, regex_extract, line_format)
- `pattern` (string): Pattern to match (required, valid string or regex)
- `remediation` (string): Remediation commands (required, valid CLI commands)

**Validation Rules:**
- Policy ID must be unique across all policies
- Severity must be one of: critical, high, medium, low
- Platforms must be supported device types or empty
- Check type must be one of predefined check types
- Pattern must be valid string or regex pattern
- Remediation must be valid CLI commands

**Usage:** Used in standards_validator.py for policy validation and compliance checking

---

### 5. Job Status Structure

**Purpose:** Background job status tracking

**Format:**
```python
{
    "job_id": "exec_job_123456",
    "status": "running",
    "progress": 45,
    "devices_completed": 5,
    "devices_total": 10,
    "current_device": "10.1.1.5",
    "result": {},
    "error": None,
    "timestamp": "2026-06-02T12:00:00Z"
}
```

**Field Descriptions:**
- `job_id` (string): Unique job identifier (required, generated by system)
- `status` (string): Job status (required: pending, running, complete, error)
- `progress` (integer): Progress percentage (optional, range: 0-100)
- `devices_completed` (integer): Number of devices completed (optional, non-negative)
- `devices_total` (integer): Total number of devices (optional, non-negative)
- `current_device` (string): Current device being processed (optional)
- `result` (object): Job result data (optional, populated when complete)
- `error` (string): Error message (optional, populated when error)
- `timestamp` (string): ISO 8601 timestamp (required)

**Validation Rules:**
- job_id must be unique across all jobs
- status must be one of: pending, running, complete, error
- progress must be between 0 and 100
- devices_completed and devices_total must be non-negative
- timestamp must be valid ISO 8601 format

**Usage:** Used throughout the application for background job tracking (discovery, STP, standards validator)

---

### 6. Discovery Device Structure

**Purpose:** Discovered device information from network discovery

**Format:**
```python
{
    "ip": "10.1.1.1",
    "hostname": "core-sw-01",
    "device_type": "cisco_ios",
    "vendor": "Cisco",
    "model": "Catalyst 3850",
    "serial": "FOC1234ABCD",
    "os_version": "16.9.4",
    "interfaces": [
        {
            "name": "GigabitEthernet0/1",
            "mac": "00:11:22:33:44:55",
            "status": "up",
            "description": "Uplink to core"
        }
    ],
    "neighbors": [
        {
            "ip": "10.1.1.2",
            "hostname": "core-sw-02",
            "local_interface": "GigabitEthernet0/1",
            "remote_interface": "GigabitEthernet0/1",
            "protocol": "LLDP"
        }
    ]
}
```

**Field Descriptions:**
- `ip` (string): Device IP address (required, valid IPv4/IPv6)
- `hostname` (string): Device hostname (required, non-empty)
- `device_type` (string): Netmiko device type (required, must be supported)
- `vendor` (string): Device vendor (optional)
- `model` (string): Device model (optional)
- `serial` (string): Device serial number (optional)
- `os_version` (string): OS version (optional)
- `interfaces` (list): Array of interface objects (optional)
- `neighbors` (list): Array of neighbor objects (optional)

**Interface Object Fields:**
- `name` (string): Interface name (required)
- `mac` (string): MAC address (optional, valid format)
- `status` (string): Interface status (optional: up, down, admin-down)
- `description` (string): Interface description (optional)

**Neighbor Object Fields:**
- `ip` (string): Neighbor IP address (required)
- `hostname` (string): Neighbor hostname (optional)
- `local_interface` (string): Local interface (optional)
- `remote_interface` (string): Remote interface (optional)
- `protocol` (string): Discovery protocol (optional: CDP, LLDP)

**Validation Rules:**
- IP address must be valid IPv4 or IPv6
- MAC address must be valid format (XX:XX:XX:XX:XX:XX)
- Status must be one of: up, down, admin-down
- Protocol must be one of: CDP, LLDP

**Usage:** Used in network_discovery.py for discovered device data and topology mapping

---

### 7. Topology Link Structure

**Purpose:** Link information for topology mapping

**Format:**
```python
{
    "source": "10.1.1.1",
    "source_interface": "GigabitEthernet0/1",
    "target": "10.1.1.2",
    "target_interface": "GigabitEthernet0/1",
    "link_type": "trunk",
    "protocol": "LLDP",
    "bandwidth": 1000,
    "status": "up"
}
```

**Field Descriptions:**
- `source` (string): Source device IP (required, valid IPv4/IPv6)
- `source_interface` (string): Source interface name (required, non-empty)
- `target` (string): Target device IP (required, valid IPv4/IPv6)
- `target_interface` (string): Target interface name (required, non-empty)
- `link_type` (string): Link type (optional: access, trunk, routed)
- `protocol` (string): Discovery protocol (optional: CDP, LLDP)
- `bandwidth` (integer): Link bandwidth in Mbps (optional, positive)
- `status` (string): Link status (optional: up, down)

**Validation Rules:**
- Source and target IP must be valid IPv4 or IPv6
- Interface names must be non-empty
- Link type must be one of: access, trunk, routed
- Bandwidth must be positive integer
- Status must be one of: up, down

**Usage:** Used in topology_mapper.py and discovery_graph.py for topology visualization

---

### 8. MAC Trace Result Structure

**Purpose:** MAC address trace result

**Format:**
```python
{
    "mac_address": "00:11:22:33:44:55",
    "path": [
        {
            "device": "10.1.1.1",
            "hostname": "access-sw-01",
            "interface": "GigabitEthernet0/1",
            "vlan": 100
        },
        {
            "device": "10.1.1.2",
            "hostname": "dist-sw-01",
            "interface": "GigabitEthernet0/2",
            "vlan": 100
        }
    ],
    "end_device": "10.1.1.3",
    "vlan": 100,
    "timestamp": "2026-06-02T12:00:00Z"
}
```

**Field Descriptions:**
- `mac_address` (string): MAC address being traced (required, valid format)
- `path` (list): Array of hop objects (required)
- `end_device` (string): End device IP (optional, valid IPv4/IPv6)
- `vlan` (integer): VLAN ID (optional, range: 1-4094)
- `timestamp` (string): ISO 8601 timestamp (required)

**Hop Object Fields:**
- `device` (string): Device IP (required, valid IPv4/IPv6)
- `hostname` (string): Device hostname (optional)
- `interface` (string): Interface name (optional)
- `vlan` (integer): VLAN ID (optional, range: 1-4094)

**Validation Rules:**
- MAC address must be valid format (XX:XX:XX:XX:XX:XX)
- Device IPs must be valid IPv4 or IPv6
- VLAN ID must be in range 1-4094
- Timestamp must be valid ISO 8601 format

**Usage:** Used in mac_trace.py and mac_trace_formatter.py for MAC address tracing

---

### 9. STP Topology Structure

**Purpose:** STP topology information

**Format:**
```python
{
    "vlan_id": 100,
    "root_bridge": "10.1.1.1",
    "root_priority": 32768,
    "bridges": [
        {
            "device": "10.1.1.1",
            "hostname": "core-sw-01",
            "priority": 32768,
            "role": "root",
            "state": "forwarding"
        },
        {
            "device": "10.1.1.2",
            "hostname": "core-sw-02",
            "priority": 32768,
            "role": "designated",
            "state": "forwarding"
        }
    ],
    "links": [
        {
            "source": "10.1.1.1",
            "target": "10.1.1.2",
            "cost": 19,
            "state": "forwarding",
            "role": "designated"
        }
    ]
}
```

**Field Descriptions:**
- `vlan_id` (integer): VLAN ID (required, range: 1-4094)
- `root_bridge` (string): Root bridge IP (required, valid IPv4/IPv6)
- `root_priority` (integer): Root bridge priority (required, valid STP priority)
- `bridges` (list): Array of bridge objects (required)
- `links` (list): Array of link objects (required)

**Bridge Object Fields:**
- `device` (string): Device IP (required, valid IPv4/IPv6)
- `hostname` (string): Device hostname (optional)
- `priority` (integer): STP priority (required, valid STP priority)
- `role` (string): STP role (required: root, designated, alternate, backup)
- `state` (string): STP state (required: forwarding, blocking, learning, listening)

**Link Object Fields:**
- `source` (string): Source device IP (required, valid IPv4/IPv6)
- `target` (string): Target device IP (required, valid IPv4/IPv6)
- `cost` (integer): STP path cost (required, positive)
- `state` (string): STP state (required: forwarding, blocking, learning, listening)
- `role` (string): STP role (required: designated, alternate, backup)

**Validation Rules:**
- VLAN ID must be in range 1-4094
- Device IPs must be valid IPv4 or IPv6
- STP priority must be valid (4096, 8192, 12288, ..., 32768, ..., 61440)
- Role must be one of: root, designated, alternate, backup
- State must be one of: forwarding, blocking, learning, listening
- Cost must be positive integer

**Usage:** Used in stp_swiss_runner.py and stp_map_formatter.py for STP analysis

---

### 10. vPC Domain Structure

**Purpose:** vPC domain information

**Format:**
```python
{
    "vpc_domain": 100,
    "peer_keepalive": "10.1.1.1",
    "peer_link": "Port-Channel1",
    "vpc_peers": [
        {
            "device": "10.1.1.2",
            "hostname": "core-sw-01",
            "role": "primary",
            "status": "peer-ok"
        },
        {
            "device": "10.1.1.3",
            "hostname": "core-sw-02",
            "role": "secondary",
            "status": "peer-ok"
        }
    ],
    "vpc_interfaces": [
        {
            "interface": "Port-Channel10",
            "vlan": 100,
            "state": "up",
            "consistency": "consistent"
        }
    ]
}
```

**Field Descriptions:**
- `vpc_domain` (integer): vPC domain ID (required, range: 1-4094)
- `peer_keepalive` (string): Peer keepalive IP (required, valid IPv4/IPv6)
- `peer_link` (string): Peer link interface (required, non-empty)
- `vpc_peers` (list): Array of vPC peer objects (required)
- `vpc_interfaces` (list): Array of vPC interface objects (required)

**vPC Peer Object Fields:**
- `device` (string): Device IP (required, valid IPv4/IPv6)
- `hostname` (string): Device hostname (optional)
- `role` (string): vPC role (required: primary, secondary)
- `status` (string): Peer status (required: peer-ok, peer-not-ok, peer-link-failed)

**vPC Interface Object Fields:**
- `interface` (string): Interface name (required, non-empty)
- `vlan` (integer): VLAN ID (optional, range: 1-4094)
- `state` (string): Interface state (optional: up, down, suspended)
- `consistency` (string): Consistency status (optional: consistent, inconsistent, suspended)

**Validation Rules:**
- vPC domain ID must be in range 1-4094
- Peer keepalive IP must be valid IPv4
- Peer link interface must be non-empty
- Role must be one of: primary, secondary
- Status must be one of: peer-ok, peer-not-ok, peer-link-failed
- VLAN ID must be in range 1-4094
- Consistency must be one of: consistent, inconsistent, suspended

**Usage:** Used in vpc_domain_plugin.py and vpc_board_formatter.py for vPC analysis

---

### 11. CLI Session Structure

**Purpose:** CLI terminal session information

**Format:**
```python
{
    "session_id": "cli_session_123",
    "host": "10.1.1.1",
    "device_type": "cisco_ios",
    "username": "admin",
    "status": "connected",
    "pty": None,
    "cols": 80,
    "rows": 24,
    "timestamp": "2026-06-02T12:00:00Z"
}
```

**Field Descriptions:**
- `session_id` (string): Unique session identifier (required, generated by system)
- `host` (string): Device IP (required, valid IPv4/IPv6)
- `device_type` (string): Netmiko device type (required, must be supported)
- `username` (string): Username (required, non-empty)
- `status` (string): Session status (required: connecting, connected, error, disconnected)
- `pty` (object): PTY object (optional, internal use)
- `cols` (integer): Terminal columns (optional, default: 80, range: 1-255)
- `rows` (integer): Terminal rows (optional, default: 24, range: 1-255)
- `timestamp` (string): ISO 8601 timestamp (required)

**Validation Rules:**
- Session ID must be unique across all sessions
- Host IP must be valid IPv4 or IPv6
- Device type must be supported by Netmiko
- Username must be non-empty
- Status must be one of: connecting, connected, error, disconnected
- Columns and rows must be in valid range
- Timestamp must be valid ISO 8601 format

**Usage:** Used in cli_manager.py for WebSocket CLI terminal sessions

---

### 12. Health Check Result Structure

**Purpose:** Health check result for a single check

**Format:**
```python
{
    "name": "inventory",
    "status": "pass",
    "message": "Inventory file found with 5 devices",
    "duration_ms": 5,
    "details": {}
}
```

**Field Descriptions:**
- `name` (string): Check name (required, predefined check name)
- `status` (string): Check status (required: pass, fail, skip)
- `message` (string): Check result message (required, non-empty)
- `duration_ms` (integer): Check duration in milliseconds (optional, non-negative)
- `details` (object): Additional details (optional)

**Validation Rules:**
- Check name must be one of predefined check names
- Status must be one of: pass, fail, skip
- Message must be non-empty
- Duration must be non-negative integer

**Usage:** Used in health_check_runner.py for system health checks

---

### 13. Template Variable Structure

**Purpose:** Variables for Jinja2 template rendering

**Format:**
```python
{
    "ntp_servers": ["10.1.1.1", "10.1.1.2"],
    "timezone": "UTC",
    "source_interface": "Loopback0",
    "port_channel_id": 1,
    "mode": "active",
    "members": ["GigabitEthernet0/1", "GigabitEthernet0/2"],
    "description": "Uplink to core",
    "interface": "GigabitEthernet0/1",
    "allowed_vlans": "10,20,30",
    "native_vlan": 1,
    "vpc": 10,
    "vpc_id": 100
}
```

**Field Descriptions:**
- `ntp_servers` (list): Array of NTP server IPs (optional, array of valid IPv4/IPv6)
- `timezone` (string): Timezone (optional, valid timezone string)
- `source_interface` (string): Source interface (optional, non-empty)
- `port_channel_id` (integer): Port-Channel ID (optional, range: 1-4096)
- `mode` (string): Port-Channel mode (optional: active, passive, on)
- `members` (list): Array of member interfaces (optional, array of non-empty strings)
- `description` (string): Interface description (optional, non-empty)
- `interface` (string): Interface name (optional, non-empty)
- `allowed_vlans` (string): Allowed VLANs (optional, VLAN range format)
- `native_vlan` (integer): Native VLAN ID (optional, range: 1-4094)
- `vpc` (integer): vPC ID (optional, range: 1-4094)
- `vpc_id` (integer): vPC domain ID (optional, range: 1-4094)

**Validation Rules:**
- NTP server IPs must be valid IPv4/IPv6
- Timezone must be valid timezone string
- Port-Channel ID must be in range 1-4096
- Mode must be one of: active, passive, on
- Member interfaces must be non-empty strings
- Native VLAN must be in range 1-4094
- Allowed VLANs must be valid VLAN range format
- vPC ID and vPC domain ID must be in range 1-4094

**Usage:** Used in config_templates.py for Jinja2 template rendering

---

### 14. Error Response Structure

**Purpose:** Standard error response format

**Format:**
```python
{
    "status": "error",
    "error": "Error message",
    "details": {
        "error_code": "ERR-001",
        "message": "Detailed error message",
        "field": "field_name",
        "timestamp": "2026-06-02T12:00:00Z"
    }
}
```

**Field Descriptions:**
- `status` (string): Always "error" (required)
- `error` (string): Human-readable error message (required, non-empty)
- `details` (object): Detailed error information (optional)
- `details.error_code` (string): Application error code (optional, format: ERR-XXX)
- `details.message` (string): Detailed error message (optional)
- `details.field` (string): Field that caused error (optional)
- `details.timestamp` (string): ISO 8601 timestamp (optional)

**Validation Rules:**
- Status must be "error"
- Error message must be non-empty
- Error code must follow format ERR-XXX (X is digit)
- Timestamp must be valid ISO 8601 format

**Usage:** Used throughout the application for error responses

---

### 15. Success Response Structure

**Purpose:** Standard success response format

**Format:**
```python
{
    "status": "success",
    "data": {}
}
```

**Field Descriptions:**
- `status` (string): Always "success" (required)
- `data` (object): Response data (optional, varies by endpoint)

**Validation Rules:**
- Status must be "success"
- Data structure varies by endpoint

**Usage:** Used throughout the application for success responses

---

## Data Structure Validation

### Validation Functions

**IP Address Validation:**
```python
import ipaddress

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
```

**MAC Address Validation:**
```python
import re

def validate_mac(mac):
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return re.match(pattern, mac) is not None
```

**VLAN ID Validation:**
```python
def validate_vlan(vlan):
    return isinstance(vlan, int) and 1 <= vlan <= 4094
```

**Semantic Version Validation:**
```python
import re

def validate_version(version):
    pattern = r'^\d+\.\d+\.\d+$'
    return re.match(pattern, version) is not None
```

---

## Data Transformation

### Data Format Conversions

**CLI Output to JSON:**
- TextFSM templates parse CLI output into structured data
- NTC Templates provide pre-built parsing templates
- Custom regex patterns for platform-specific parsing

**JSON to HTML:**
- Jinja2 templates for HTML generation
- Vis.js for topology visualization
- Custom formatters for operation-specific reports

**YAML to Python Dict:**
- PyYAML for policy file parsing
- Validation of YAML structure
- Error handling for malformed YAML

---

## Data Storage

### File-Based Storage

**Inventory File (inventory.txt):**
- Format: INI-style with sections
- Location: Root directory
- Validation: Check file existence and format

**Policy Files (policies/*.yaml):**
- Format: YAML
- Location: policies/ directory
- Validation: YAML syntax and structure validation

**Configuration Backups:**
- Format: Text files
- Location: backups/ directory
- Rotation: Keep last N backups per device

**Report Files:**
- Format: Text, CSV, HTML
- Location: reports/ directory
- Timestamp: Include timestamp in filename

---

## Data Flow

### Request Flow

1. **API Request** → JSON validation
2. **Parameter Extraction** → Data structure validation
3. **Device Connection** → Connection structure validation
4. **Command Execution** → Output parsing
5. **Data Transformation** → Format conversion
6. **Response Generation** → Response structure validation

### Background Job Flow

1. **Job Creation** → Job structure initialization
2. **Device Processing** → Progress updates
3. **Result Collection** → Data aggregation
4. **Report Generation** → Format conversion
5. **Job Completion** → Status update

---

## Data Integrity

### Integrity Checks

**Duplicate Prevention:**
- Unique job IDs
- Unique session IDs
- Unique plugin IDs
- No duplicate IP addresses in inventory

**Data Consistency:**
- VLAN ID validation
- Interface name validation
- Device type validation
- Platform compatibility checks

**Error Handling:**
- Validation before processing
- Error recovery procedures
- Data rollback on failure
- Logging of all data operations
