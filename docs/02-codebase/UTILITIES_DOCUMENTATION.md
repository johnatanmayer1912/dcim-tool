# Utilities Documentation

## Overview

The `utils/` directory contains 22 utility modules that provide helper functions for report formatting, logging, backup operations, discovery visualization, health checking, MAC normalization, Juniper interface correlation, and other common operations across the Network Swiss Tool Pro application.

**Last updated:** 2026-06-18 · **Application version:** 7.0.51

## Utilities Architecture

Utilities are organized by functional area:
- **Formatters**: Report and data formatting for various operations
- **Loggers**: Application and structured logging
- **Backup**: Configuration and system backup operations
- **Discovery**: Network discovery visualization and graph generation
- **Health**: System health checking and validation
- **Search**: Search operations and progress tracking
- **Topology**: Topology map generation and visualization

---

## Formatters

### report_formatter.py
**Purpose**: Core report generation and file writing utilities for all plugin operations.

**Key Functions**:
- `write_text_file(filename, lines)` - Write text content to file
- `append_text_file(filename, text)` - Append text to file
- `write_csv_file(filename, fieldnames, data_rows)` - Write CSV data to file
- `save_plugin_report(plugin_id, host, data, format_func)` - Save plugin report with formatted output
- `append_to_master_report(plugin_id, host, status, message, report_path)` - Append to master report file

**Usage Example**:
```python
from utils.report_formatter import save_plugin_report

report_path = save_plugin_report(
    'network_discovery',
    '10.1.1.1',
    result_data,
    format_discovery_report
)
```

---

### mac_trace_formatter.py
**Purpose**: Format MAC address trace results into human-readable reports and HTML.

**Key Functions**:
- `format_mac_trace_report(data, host)` - Format MAC trace data into text report
- `generate_mac_trace_html(data, host)` - Generate HTML visualization of MAC path

**Usage Example**:
```python
from utils.mac_trace_formatter import generate_mac_trace_html

html_path = generate_mac_trace_html(mac_trace_data, 'switch01')
```

---

### description_search_formatter.py
**Purpose**: Format interface description search results into reports and HTML.

**Key Functions**:
- `format_description_search_report(data, host)` - Format description search results
- `generate_description_search_html(data, host)` - Generate HTML visualization

**Usage Example**:
```python
from utils.description_search_formatter import generate_description_search_html

html_path = generate_description_search_html(search_results, 'switch01')
```

---

### ping_scan_formatter.py
**Purpose**: Format ping scan results into reports and HTML.

**Key Functions**:
- `format_ping_scan_report(data, subnet)` - Format ping scan results
- `generate_ping_scan_html(data, subnet)` - Generate HTML visualization

**Usage Example**:
```python
from utils.ping_scan_formatter import generate_ping_scan_html

html_path = generate_ping_scan_html(ping_results, '10.1.1.0/24')
```

---

### stp_map_formatter.py
**Purpose**: Format STP topology data into HTML maps and reports.

**Key Functions**:
- `generate_stp_html(data, host)` - Generate STP topology HTML visualization
- `format_stp_report(data, host)` - Format STP analysis report

**Usage Example**:
```python
from utils.stp_map_formatter import generate_stp_html

html_path = generate_stp_html(stp_data, 'switch01')
```

---

### vpc_board_formatter.py
**Purpose**: Format vPC domain data into engineering board HTML visualization.

**Key Functions**:
- `generate_vpc_board_html(data, host)` - Generate vPC engineering board HTML
- `format_vpc_report(data, host)` - Format vPC analysis report

**Usage Example**:
```python
from utils.vpc_board_formatter import generate_vpc_board_html

html_path = generate_vpc_board_html(vpc_data, 'nexus01')
```

---

### discovery_map_formatter.py
**Purpose**: Format network discovery data into topology maps and reports.

**Key Functions**:
- `generate_discovery_html(data, host)` - Generate discovery topology HTML
- `format_discovery_report(data, host)` - Format discovery analysis report

**Usage Example**:
```python
from utils.discovery_map_formatter import generate_discovery_html

html_path = generate_discovery_html(discovery_data, 'switch01')
```

---

### search_report_output.py
**Purpose**: Generic search result formatting for various search operations.

**Key Functions**:
- `format_search_results(results, search_type)` - Format search results into report
- `generate_search_html(results, search_type)` - Generate HTML visualization

**Usage Example**:
```python
from utils.search_report_output import format_search_results

report = format_search_results(search_results, 'description')
```

---

## Loggers

### app_logger.py
**Purpose**: Application-level logging configuration and utilities.

**Key Functions**:
- `setup_logging(log_level='INFO')` - Configure application logging
- `get_logger(name)` - Get configured logger instance

**Usage Example**:
```python
from utils.app_logger import setup_logging, get_logger

setup_logging('DEBUG')
logger = get_logger(__name__)
logger.info('Application started')
```

---

### structured_logger.py
**Purpose**: Structured logging with JSON format for log aggregation and analysis.

**Key Functions**:
- `log_structured(level, message, context)` - Log structured message with context
- `log_error(message, error, context)` - Log error with structured context

**Usage Example**:
```python
from utils.structured_logger import log_structured

log_structured('INFO', 'Device connected', {'device': 'switch01', 'ip': '10.1.1.1'})
```

---

## Backup

### backup_util.py
**Purpose**: Generic backup utilities for file and directory operations.

**Key Functions**:
- `backup_file(source_path, backup_dir)` - Backup file to backup directory
- `restore_file(backup_path, target_path)` - Restore file from backup
- `rotate_backups(backup_dir, max_count)` - Rotate backup files to limit count

**Usage Example**:
```python
from utils.backup_util import backup_file

backup_path = backup_file('config.txt', 'backups/')
```

---

### config_backup_system.py
**Purpose**: Configuration backup system for network device configurations.

**Key Functions**:
- `backup_config(device, config_data)` - Backup device configuration
- `list_backups(device)` - List available backups for device
- `restore_config(device, backup_id)` - Restore configuration from backup

**Usage Example**:
```python
from utils.config_backup_system import backup_config

backup_id = backup_config('switch01', config_data)
```

---

### full_system_backup.py
**Purpose**: Full system backup including configurations, reports, and application data.

**Key Functions**:
- `create_full_backup(backup_dir)` - Create full system backup
- `restore_full_backup(backup_path)` - Restore full system backup
- `schedule_backup(schedule)` - Schedule automated backups

**Usage Example**:
```python
from utils.full_system_backup import create_full_backup

backup_path = create_full_backup('backups/full/')
```

---

## Discovery

### discovery_graph.py
**Purpose**: Network discovery graph generation and topology analysis.

**Key Functions**:
- `build_discovery_graph(devices, links)` - Build network topology graph
- `classify_os_family(platform)` - Classify device OS family from platform string
- `generate_graph_json(graph)` - Generate JSON representation of graph

**Usage Example**:
```python
from utils.discovery_graph import build_discovery_graph, classify_os_family

graph = build_discovery_graph(devices, links)
os_family = classify_os_family('Nexus-9000')
```

---

### discovery_map_shell.py
**Purpose**: Offline HTML shell for discovery map visualization.

**Key Functions**:
- `generate_discovery_shell(data, output_path)` - Generate offline discovery map HTML
- `embed_visjs(output_path)` - Embed vis-network.js for offline use

**Usage Example**:
```python
from utils.discovery_map_shell import generate_discovery_shell

generate_discovery_shell(discovery_data, 'discovery_map.html')
```

---

### discovery_map_formatter.py
**Purpose**: Format discovery data for map visualization (see Formatters section).

---

## Health

### health_check_runner.py
**Purpose**: System health check execution and validation.

**Key Functions**:
- `run_health_checks(quick=False, full=False, include_cli=False)` - Run health checks
- `check_inventory()` - Validate inventory file
- `check_port()` - Validate port availability
- `check_plugins()` - Validate plugin loading
- `check_cli_smoke()` - Run CLI smoke test

**Usage Example**:
```python
from utils.health_check_runner import run_health_checks

result = run_health_checks(quick=True, full=False, include_cli=False)
```

---

## Search

### mac_utils.py
**Purpose**: Shared MAC address normalization and vendor-specific CLI search term generation.

**Key Functions**:
- `normalize_mac_hex(mac)` — Strip separators; return lowercase hex (supports partial MACs)
- `to_cisco_dotted(mac)` — Cisco CAM notation `aabb.ccdd.eeff`
- `to_junos_colon(mac)` — Junos colon notation `aa:bb:cc:dd:ee:ff`
- `cisco_search_terms(mac)` — Tokens for `show mac address-table | include`
- `junos_search_terms(mac)` — Tokens for `show ethernet-switching table | match`
- `line_contains_mac(line, mac)` — Match MAC in any common format within a line
- `extract_junos_interface(line)` — Pull Junos interface name from MAC table row

**Used by**: `modules/mac_trace.py`, web MAC trace thread (via `mac_trace`)

**Usage Example**:
```python
from utils.mac_utils import cisco_search_terms, junos_search_terms

for term in cisco_search_terms('00:11:22:33:44:55'):
    conn.send_command(f"show mac address-table | include {term}")
```

---

### juniper_iface.py
**Purpose**: Juniper physical vs logical (unit) interface correlation and LACP/AE bundle discovery.

**Key Functions**:
- `split_junos_unit(name)` — Split `ge-0/0/0.0` into physical and logical keys
- `resolve_junos_iface_key(name, int_meta_keys)` — Map MAC-table interface to `int_meta` key
- `collect_juniper_lag_detail(conn)` — Fetch LACP/AE membership via SSH
- `enrich_interfaces_with_lag(interfaces, lag_detail)` — Attach `port_channel` / member lists

**Used by**: `modules/plugins/interface_manager.py`, `modules/node_interface_topology.py`

---

### search_it_progress.py
**Purpose**: Progress tracking for search_it operations (MAC trace, description search, ping scan).

**Key Functions**:
- `get_all_progress()` - Get progress for all search operations
- `set_progress(operation, status, progress)` - Set progress for operation
- `clear_progress(operation)` - Clear progress for operation

**Usage Example**:
```python
from utils.search_it_progress import set_progress, get_all_progress

set_progress('mac_trace', 'running', 50)
progress = get_all_progress()
```

---

### search_report_output.py
**Purpose**: Generic search result formatting (see Formatters section).

---

## Topology

### standard_map_shell.py (v7.0.49+)
**Purpose:** Standard L2 Map NOC split-pane shell — offline CSS, top chrome, connection index, map style controls (Tier/Radial/Focus/Schematic).

**Key Functions:**
- `standard_map_shell_css()` — offline-safe layout and legend pills
- `embed_standard_map_top_chrome()` — unified header (search, legend, port-label toggle)
- `embed_standard_map_pane_html()` — connection index panel
- `embed_standard_map_js()` — client-side map styles, table sync, focus mode
- `build_briefing_stats()` — KPI strip (devices, links, Po/vPC, asymmetric, mismatch)
- `enrich_link_rows_from_vis_edges()` — connection rows from Vis.js edge payloads

**Related:** `modules/adapters._finalize_standard_map_edges()` (v7.0.51 peer-link upgrade/synthesis)

**Doc:** [standard-map-shell.md](../06-ui-ux/standard-map-shell.md)

---

### topo_map_shell.py
**Purpose:** Link inventory helpers and connection index row builder for topology maps.

**Key Functions:**
- `link_rows_from_edges(edges, nodes)` — WHO/HOW/WHAT rows (VLAN, speed, type, roles)
- `embed_link_inventory_html()` / `embed_link_inventory_js()` — legacy tab shell (non–Standard Map)
- `shell_css()` — shared topo toolbar styles

**Usage Example:**
```python
from utils.topo_map_shell import link_rows_from_edges

rows = link_rows_from_edges(edges_json, nodes_json)
```

---

### vpc_map_shell.py
**Purpose:** vPC Command Center HTML shell — overview split (map + engineering board), tabs, light/dark theme.

**Key Functions:**
- `vpc_command_center_tabs_html()` — overview / links / data tabs; `#mynetwork.vpc-map-pane`
- `vpc_shell_js()` — `vpcBootMap`, tab switching, theme toggle
- `vpc_light_css()` — Command Center styling

**Usage:** Wired from `generate_topology_html(..., map_mode='vpc')` in `report_formatter.py`.

---

## Other Utilities

### debug_regex.py
**Purpose**: Regular expression debugging and testing utilities.

**Key Functions**:
- `test_regex(pattern, test_string)` - Test regex pattern against string
- `debug_regex_match(pattern, string)` - Debug regex matching with details

**Usage Example**:
```python
from utils.debug_regex import test_regex

match = test_regex(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '10.1.1.1')
```

---

## When to Use Each Utility

### Report Generation
- Use `report_formatter.py` for all plugin report generation
- Use specific formatters (mac_trace_formatter, etc.) for operation-specific formatting
- Use formatters to generate both text reports and HTML visualizations

### Logging
- Use `app_logger.py` for standard application logging
- Use `structured_logger.py` for JSON-formatted structured logging

### Backup Operations
- Use `backup_util.py` for generic file backup operations
- Use `config_backup_system.py` for device configuration backups
- Use `full_system_backup.py` for complete system backups

### Discovery Visualization
- Use `discovery_graph.py` for graph generation and OS classification
- Use `discovery_map_shell.py` for offline discovery map HTML
- Use `discovery_map_formatter.py` for discovery data formatting

### Health Checking
- Use `health_check_runner.py` for all health check operations
- Use specific check functions for individual validation

### Search Operations
- Use `search_it_progress.py` for progress tracking
- Use specific formatters for search result formatting

### Topology Visualization
- Use `standard_map_shell.py` for Standard L2 Map (`map_mode=all`) exports
- Use `topo_map_shell.py` for link row enrichment and legacy link inventory tab
- Use `vpc_map_shell.py` for vPC Command Center maps
- Use `vpc_board_formatter.py` for vPC engineering board visualization

---

## Dependencies

All utilities depend on:
- Python standard library (os, sys, json, csv, datetime, re, etc.)
- Network Swiss Tool Pro core modules (modules.*)
- Third-party libraries (vis-network.js for HTML maps, etc.)

---

## Error Handling

All utility functions include error handling:
- File operations log errors to stderr
- Report formatting handles None and malformed data gracefully
- Backup operations validate paths and permissions before execution
- Health checks return structured error information

---

## File Paths

Utilities use `_get_resource_path()` for consistent path resolution:
- Development mode: Resolves relative to project root
- EXE mode: Checks bundled resources first, then program directory
- Ensures compatibility with PyInstaller builds
