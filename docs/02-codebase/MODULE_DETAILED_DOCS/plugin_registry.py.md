# plugin_registry.py Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Lead Developer (R-ENG) |
| **Last Updated** | 2026-07-21 |
| **Application Version** | 7.0.85 |

## Overview

`modules/plugin_registry.py` is the plugin discovery and registry system for Network Swiss Tool Pro. It provides a singleton registry that scans plugins, validates metadata, manages execution, and supports hot-reloading. The system is designed for security, extensibility, and maintainability.

## File Location

- **Path**: `modules/plugin_registry.py`
- **Lines**: 488
- **Dependencies**: ast, importlib.util, shutil, types, concurrent.futures

## Dependencies

### External Dependencies
- `ast` - Abstract Syntax Tree for safe code analysis
- `importlib.util` - Dynamic module loading
- `shutil` - File operations for backup/restore
- `types` - Type checking
- `concurrent.futures` - Parallel execution
- `re` - Regular expressions for validation

### Internal Dependencies
- `utils.output_paths` - Data layout and path management
- `sys` - System operations and path management

## Architecture

### Singleton Pattern
The `PluginRegistry` class implements the singleton pattern to ensure only one registry instance exists:

```python
class PluginRegistry:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Plugin Directory Resolution
The registry supports multiple plugin directory locations:
1. **Dev Mode**: `modules/plugins/` relative to project root
2. **PyInstaller Bundle**: `sys._MEIPASS/modules/plugins/`
3. **Sidecar Directory**: `plugins/` next to executable
4. **Automatic Bootstrap**: Copies bundled plugins to sidecar if needed

## Key Components

### Security Controls

#### Banned Imports
```python
BANNED_IMPORTS = [
    'os.system', 'os.popen', 'subprocess.call', 'subprocess.Popen',
    'shutil.rmtree', 'eval', 'exec', 'compile', '__import__'
]
```

#### Required Metadata Keys
```python
REQUIRED_META_KEYS = ['plugin_id', 'display_name', 'version', 'category']
```

#### plugin_id Validation
- Must be snake_case: `^[a-z][a-z0-9_]*$`
- Prevents naming conflicts
- Ensures consistency

## Class: PluginRegistry

### Constructor

```python
def __init__(self, plugins_dir: str = None)
```

**Parameters**:
- `plugins_dir` (str, optional): Custom plugins directory path

**Behavior**:
- Resolves plugin directory (bundled or sidecar)
- Creates necessary directories (plugins, backup, scratch)
- Calls `reload()` to scan plugins
- Sets `_initialized` flag to prevent re-initialization

### Discovery Methods

#### `reload()`
**Purpose**: Re-scan plugins directory and rebuild registry

**Behavior**:
- Clears existing plugins and errors
- Lists all .py files in plugins directory
- Calls `_load_plugin()` for each file
- Logs success/failure for each plugin

#### `_load_plugin(file_path: str)`
**Purpose**: Load and validate a single plugin file

**Process**:
1. Read file content
2. Parse AST (syntax check)
3. Extract METADATA dictionary
4. Validate metadata structure
5. Check for duplicate plugin_id
6. Load module safely
7. Verify `run` function exists
8. Register plugin in `_plugins` dict

#### `_extract_metadata(tree: ast.AST, filename: str)`
**Purpose**: Extract METADATA dict from AST

**Returns**: `Optional[Dict]` - Metadata dictionary or None

**Process**:
- Walks AST nodes
- Finds assignment to `METADATA` variable
- Uses `ast.literal_eval()` for safe evaluation
- Returns None if METADATA not found

#### `_validate_metadata(metadata: Dict, filename: str)`
**Purpose**: Validate metadata has required keys

**Raises**: `ValueError` if validation fails

**Checks**:
- All required keys present
- plugin_id matches snake_case pattern

#### `_load_module_safely(file_path: str, plugin_id: str)`
**Purpose**: Load plugin module using importlib.util

**Returns**: `Optional[Any]` - Loaded module or None

**Process**:
1. Adds project root to sys.path
2. Adds _MEIPASS to sys.path (if bundled)
3. Creates module spec from file
4. Creates module from spec
5. Registers in sys.modules
6. Executes module
7. Cleans up on failure

### Query Methods

#### `get_all_metadata()`
**Returns**: `List[Dict]` - Metadata for all registered plugins

#### `get_plugin(plugin_id: str)`
**Returns**: `Optional[Dict]` - Full plugin record or None

#### `exists(plugin_id: str)`
**Returns**: `bool` - True if plugin exists

#### `get_errors()`
**Returns**: `List[Dict]` - List of loading errors

### Execution Methods

#### `execute(plugin_id: str, device: Dict, credentials: Dict, params: Dict, config: Dict, log_func: Optional[Callable] = None)`
**Purpose**: Execute a plugin on a single device

**Returns**: `Dict` - Result with status, error, data

**Process**:
1. Get plugin from registry
2. Call plugin's `run()` function
3. Validate return type (must be dict)
4. Return result or error

#### `execute_parallel(plugin_id: str, devices: List[Dict], credentials: Dict, params: Dict, config: Dict, log_func: Optional[Callable] = None, max_workers: int = 10)`
**Purpose**: Execute plugin on multiple devices in parallel

**Returns**: `List[Dict]` - Results for each device

**Process**:
1. Uses ThreadPoolExecutor with max_workers
2. Submits tasks for each device
3. Collects results as they complete
4. Handles exceptions per device

### Upload & Rollback Methods

#### `validate_upload(file_path: str)`
**Purpose**: Validate plugin file before promoting to production

**Returns**: `Tuple[bool, str]` - (is_valid, message)

**Checks**:
- Syntax validation (AST parsing)
- Indentation error detection
- METADATA presence
- Security violations (banned patterns)

#### `promote_plugin(source_path: str)`
**Purpose**: Promote validated plugin from scratch to production

**Returns**: `Tuple[bool, str]` - (success, message)

**Process**:
1. Backup existing plugin if present
2. Copy new plugin to production directory
3. Reload registry
4. Return success/failure

#### `rollback_plugin(plugin_id: str)`
**Purpose**: Rollback plugin to previous version

**Returns**: `Tuple[bool, str]` - (success, message)

**Process**:
1. Find backup file
2. Restore from backup
3. Reload registry
4. Return success/failure

## Plugin Contract

### Required Metadata
```python
METADATA = {
    'plugin_id': 'my_plugin',           # snake_case identifier
    'display_name': 'My Plugin',       # Human-readable name
    'version': '1.0.0',                # Semantic version
    'category': 'analysis',            # Plugin category
    'description': 'Plugin description'
}
```

### Required Function
```python
def run(device: Dict, credentials: Dict, params: Dict, config: Dict, log_func: Callable) -> Dict:
    """
    Execute plugin on device
    
    Returns:
        dict: {'status': 'success'|'fail', 'data': {...}, 'error': '...'}
    """
    pass
```

### Return Format
```python
{
    'status': 'success' or 'fail',
    'data': {...},           # Plugin-specific data
    'error': '...'           # Error message if failed
}
```

## Directory Structure

### Plugin Directory
```
modules/plugins/
├── base_template.py
├── config_templates.py
├── critical_logs_plugin.py
├── device_time_plugin.py
├── environment_status_plugin.py
├── interface_errors_plugin.py
├── interface_manager.py
├── network_discovery.py
├── serial_number_plugin.py
├── standards_validator.py
├── stp_topology_visualizer.py
├── unused_trunk_pruner.py
├── vlan_audit_plugin.py
└── vpc_domain_plugin.py
```

### Backup Directory
```
{data_root}/backups/plugins/
└── {plugin_id}_backup_{timestamp}.py
```

### Scratch Directory
```
{data_root}/scratch/plugins/
```

## Error Handling

### Loading Errors
- **Syntax Error**: Logged in `_errors` list, plugin not registered
- **Missing METADATA**: Logged, plugin not registered
- **Invalid Metadata**: Logged, plugin not registered
- **Duplicate ID**: Logged, plugin not registered
- **Missing run()**: Logged, plugin not registered
- **Import Error**: Logged, plugin not registered

### Execution Errors
- **Plugin Not Found**: Returns fail status with error message
- **Invalid Return Type**: Returns fail status
- **Runtime Exception**: Returns fail status with exception message

### Validation Errors
- **Syntax Error**: Returns False with detailed error message
- **Indentation Error**: Returns False with specific message
- **Missing METADATA**: Returns False with message
- **Security Violation**: Returns False with banned pattern

## Security Features

### AST-Based Metadata Extraction
- Uses `ast.literal_eval()` for safe evaluation
- No code execution during metadata extraction
- Prevents code injection via METADATA

### Banned Pattern Detection
- Scans for dangerous function calls
- Prevents os.system, subprocess, eval, exec
- Blocks during validation phase

### Import Context Control
- Manages sys.path explicitly
- Prevents import confusion
- Supports both dev and bundled modes

### Backup & Rollback
- Automatic backup before promotion
- Safe rollback mechanism
- Prevents data loss

## Performance Considerations

### Parallel Execution
- Uses ThreadPoolExecutor for parallel device execution
- Configurable max_workers (default: 10)
- Efficient for large device lists

### Hot-Reload Support
- `reload()` method for dynamic updates
- No application restart required
- Development-friendly

### Bounded Log Queue
- Prevents memory issues
- Auto-drops oldest messages
- Thread-safe operations

## Usage Examples

### Initialize Registry
```python
from modules.plugin_registry import PluginRegistry

registry = PluginRegistry()
plugins = registry.get_all_metadata()
```

### Execute Plugin on Single Device
```python
result = registry.execute(
    'network_discovery',
    device={'host': '192.168.1.1', 'device_type': 'cisco_ios'},
    credentials={'username': 'admin', 'password': 'secret'},
    params={},
    config={},
    log_func=print
)
```

### Execute Plugin on Multiple Devices
```python
results = registry.execute_parallel(
    'network_discovery',
    devices=[...],
    credentials={...},
    params={},
    config={},
    log_func=print,
    max_workers=10
)
```

### Validate and Promote Plugin
```python
is_valid, message = registry.validate_upload('/path/to/new_plugin.py')
if is_valid:
    success, message = registry.promote_plugin('/path/to/new_plugin.py')
```

### Rollback Plugin
```python
success, message = registry.rollback_plugin('my_plugin')
```

## Related Documentation

- `main.py.md` - Entry point documentation
- `vlan_checker_web.py.md` - Web server documentation
- `05-plugins/README.md` - Plugin documentation hub
- `04-automation/plugin-development-guide.md` - Plugin development guide

## Cross-References

- References: `utils/output_paths.py` (data layout)
- References: `modules/plugins/` (plugin implementations)
- Referenced by: `vlan_checker_web.py` (plugin execution)
- Referenced by: `modules/adapters.py` (plugin delegation)
