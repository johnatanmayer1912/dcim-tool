# vlan_checker_web.py Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Lead Developer (R-ENG) |
| **Last Updated** | 2026-07-21 |
| **Application Version** | 7.0.85 |

## Overview

`vlan_checker_web.py` is the Flask web server for Network Swiss Tool Pro. It provides the web interface for network management operations including VLAN auditing, MAC tracing, topology mapping, and various network analysis tasks. The file is 3830 lines and contains comprehensive web functionality with WebSocket support for real-time CLI terminal operations.

## File Location

- **Path**: `vlan_checker_web.py` (root directory)
- **Lines**: 3830
- **Dependencies**: Flask, Flask-SocketIO, werkzeug, telnetlib/telnetlib_compat

## Dependencies

### External Dependencies
- `flask` - Web framework
- `flask_socketio` - WebSocket support for real-time communication
- `werkzeug` - WSGI utilities (secure_filename)
- `telnetlib` / `telnetlib_compat` - Telnet compatibility for Python 3.13+
- `ipaddress` - IP address manipulation
- `re` - Regular expressions
- `threading` - Multi-threading support
- `collections` - Thread-safe data structures

### Internal Dependencies
- `utils.output_paths` - Data layout and path management
- `utils.structured_logger` - Logging initialization
- `utils.session_cred_cache` - Session credential caching
- `modules.credential_manager` - Secure credential storage
- `modules.adapters` - Network operation adapters
- `modules.vlan_audit` - VLAN auditing functionality
- `modules.mac_trace` - MAC address tracing
- `utils.report_formatter` - Report formatting utilities
- `utils.task_control_plane` - Task control and cancellation

## Global Configuration

### Flask App Initialization
```python
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, "modules", "web", "templates")
    app = Flask(__name__, template_folder=template_folder)
else:
    local_template_folder = os.path.join(os.path.dirname(__file__), "modules", "web", "templates")
    app = Flask(__name__, template_folder=local_template_folder)
```

### Flask-SocketIO Initialization
```python
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        manage_session=False,
        logger=False,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=15,
        allow_upgrades=True
    )
```

### Global State
- `log_queue` - Thread-safe deque for log collection (max 5000 messages)
- `session_log_file` - Persistent session log file path
- `credential_manager` - Credential manager instance for secure storage

## Key Functions

### `_get_resource_path(relative_path)`

**Purpose**: Get absolute path to resource, works for dev and PyInstaller

**Returns**: `str` - Absolute path to resource

**Behavior**:
- Checks `sys._MEIPASS` first for bundled resources
- Falls back to program directory for writable files
- Resolves relative to project root in dev mode

### `_read_version()`

**Purpose**: Read version from VERSION file (single source of truth)

**Returns**: `str` - Version string

### `_require_json_body()`

**Purpose**: Validate and parse JSON POST body

**Returns**: `(data_dict, error_response)` - Parsed data or error response

**Behavior**:
- Validates Content-Type is application/json
- Parses JSON body
- Returns error tuple if validation fails

### `_parse_bounded_int(value, default, field_name, min_val=None, max_val=None)`

**Purpose**: Parse integer with bounds validation

**Returns**: `int` - Parsed and validated integer

**Raises**: `ValueError` if invalid or out of bounds

### `filter_inventory(inv_str, target_mode, filter_str, single_host, group_filter="All")`

**Purpose**: Filter device inventory based on mode and filters

**Parameters**:
- `inv_str` (str): Inventory string from inventory.txt
- `target_mode` (str): 'single' or 'bulk'
- `filter_str` (str): Text filter for host/device_type
- `single_host` (str): Specific host for single mode
- `group_filter` (str): Group filter for bulk mode

**Returns**: `list` - Filtered device list

**Behavior**:
- Parses inventory.txt format (host,type,port,group)
- Supports [Group] headers for grouping
- Applies group filter first, then text filter
- Supports partial matching for single host mode

### `add_log(msg)`

**Purpose**: Add message to log queue and persistent file

**Parameters**:
- `msg` (str): Log message (can contain HTML)

**Behavior**:
- Appends to thread-safe log_queue
- Mirrors to console
- Strips HTML tags for text log file
- Writes to session_log_file with timestamp

## Core Operation Threads

### `_connectivity_check_thread(devices, user, pwd, enb_pwd)`

**Purpose**: Execute connectivity check in background thread

**Delegates to**: `modules.adapters.run_connectivity()`

### `_vlan_check_thread(devices, user, pwd, enb_pwd)`

**Purpose**: Execute VLAN audit in background thread

**Delegates to**: `modules.vlan_audit.run()`

**Output**: Generates VLAN audit report (txt) in run directory

### `_find_missing_vlan_thread(devices, user, pwd, enb_pwd, vlan_id)`

**Purpose**: Find devices missing specific VLAN

**Delegates to**: `modules.vlan_audit.run()`

**Output**: Generates missing VLAN report (txt + html)

### `_mac_check_thread(devices, user, pwd, enb_pwd, target_mac)`

**Purpose**: Trace MAC address across devices

**Delegates to**: `modules.mac_trace.run()`

**Output**: Generates MAC trace report (txt + html) with path hops

## Main API Routes

### System Routes

#### `@app.route('/health')`
**Purpose**: HTTP health check
**Returns**: "OK", 200

#### `@app.route('/favicon.ico')`
**Purpose**: Serve favicon
**Returns**: favicon_program.png or 404

#### `@app.route('/debug_status')`
**Purpose**: Return dependency status for troubleshooting
**Returns**: JSON with version and library versions

### Main Web Interface

#### `@app.route('/')`
**Purpose**: Serve main web interface
**Template**: `index.html`
**Context**: Version, update date, socketio availability

#### `@app.route('/cli_terminal')`
**Purpose**: Serve CLI terminal interface
**Template**: `cli_terminal.html`
**Context**: Version, socketio availability

### API Endpoints

#### VLAN Operations
- `/api/vlan/validate` - Validate VLAN configuration
- `/api/vlan/audit` - Run VLAN audit
- `/api/vlan/missing` - Find missing VLAN
- `/api/vlan/compare` - Compare VLANs between devices

#### MAC Operations
- `/api/mac/trace` - Trace MAC address
- `/api/mac/search` - Search for MAC address

#### Topology Operations
- `/api/topology/generate` - Generate topology map
- `/api/topology/l3` - Generate L3 topology
- `/api/topology/discovery` - Network discovery

#### Interface Operations
- `/api/interface/manager` - Interface management
- `/api/interface/errors` - Interface error analysis

#### Config Operations
- `/api/config/backup` - Backup device configurations
- `/api/config/compare` - Compare configurations
- `/api/config/restore` - Restore configuration

#### Credential Operations
- `/api/credentials/save` - Save credentials securely
- `/api/credentials/load` - Load saved credentials
- `/api/credentials/delete` - Delete saved credentials

## WebSocket Events (Flask-SocketIO)

### Client → Server Events
- `connect` - Client connection
- `disconnect` - Client disconnection
- `cli_command` - Execute CLI command
- `cli_input` - Send input to CLI process

### Server → Client Events
- `log_message` - Send log message to client
- `cli_output` - Send CLI output to client
- `task_progress` - Send task progress update
- `task_complete` - Send task completion notification

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

### Log Queue
- **Type**: `collections.deque` (maxlen=5000)
- **Purpose**: Thread-safe log collection
- **Content**: Log messages (can contain HTML)

### Session Log File
- **Location**: `{data_root}/logs/session_{timestamp}.log`
- **Format**: `[HH:MM:SS] message`
- **Purpose**: Persistent log storage

## Error Handling

### Missing Resources
- **Error**: Resource file not found
- **Action**: Return 404 for favicon, use fallback for templates

### Invalid JSON
- **Error**: Invalid JSON body in POST request
- **Action**: Return 400 with error message

### Thread Errors
- **Error**: Exception in background thread
- **Action**: Log error with traceback, continue operation

### Credential Manager Errors
- **Error**: Credential manager initialization failure
- **Action**: Set credential_manager to None, log warning, continue

## Configuration

### Template Location
- **Dev Mode**: `modules/web/templates/`
- **PyInstaller**: `sys._MEIPASS/modules/web/templates/`

### Data Root
- **Location**: Configured via `utils.output_paths.get_data_root()`
- **Purpose**: Centralized data storage (logs, credentials, reports)

### SocketIO Configuration
- **CORS**: Allowed from all origins
- **Async Mode**: Threading
- **Ping Timeout**: 60 seconds
- **Ping Interval**: 15 seconds

## Security Features

### Credential Management
- Secure credential storage via `CredentialManager`
- Credentials stored in encrypted format
- Session-based credential caching

### Session Management
- Session log files with timestamps
- Session credential cache lifecycle
- Automatic credential cleanup

### Input Validation
- JSON body validation for API endpoints
- Integer bounds validation
- File upload validation (secure_filename)

## Performance Considerations

### Thread-Safe Logging
- Uses `collections.deque` for thread-safe operations
- Bounded queue (5000 messages) to prevent memory issues
- Oldest messages auto-dropped when full

### Background Operations
- All network operations run in background threads
- Non-blocking web server
- Progress updates via WebSocket

### Resource Management
- Template caching by Flask
- Static file serving via Flask
- Session log rotation

## Usage Examples

### Start Web Server
```bash
python main.py web
```

### Access Health Check
```bash
curl http://localhost:5000/health
```

### Access Debug Status
```bash
curl http://localhost:5000/debug_status
```

### Run VLAN Audit via API
```bash
curl -X POST http://localhost:5000/api/vlan/audit \
  -H "Content-Type: application/json" \
  -d '{"devices": [...], "credentials": {...}}'
```

## Related Documentation

- `main.py.md` - Entry point documentation
- `modules/adapters.py.md` - Adapters module documentation
- `modules/vlan_audit.py.md` - VLAN audit documentation
- `modules/mac_trace.py.md` - MAC trace documentation
- `modules/credential_manager.py.md` - Credential manager documentation
- `06-ui-ux/WEB_TEMPLATES_DOCUMENTATION.md` - Web templates documentation

## Cross-References

- References: `utils/output_paths.py` (data layout)
- References: `modules/adapters.py` (network operations)
- References: `modules/credential_manager.py` (credential storage)
- References: `modules/web/templates/index.html` (main UI)
- Referenced by: `main.py` (web mode launch)
