# main.py Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Lead Developer (R-ENG) |
| **Last Updated** | 2026-08-18 |
| **Application Version** | 7.0.85 |

> **Supported launch mode for operators:** `web`. `gui` (Tk) is legacy and out of scope. Do not extend `vlan_checker_gui.py`.

## Overview

`main.py` is the unified entry point for Network Swiss Tool Pro. Supported operator launch is **`web`**. `gui` (Tk) is legacy and out of scope. CLI and test modes remain for backup/audit and pytest.

## File Location

- **Path**: `main.py` (root directory)
- **Lines**: 156
- **Dependencies**: argparse, sys, os, telnetlib/telnetlib_compat

## Dependencies

### Internal Dependencies
- `utils.output_paths` - Data layout and path management
- `utils.structured_logger` - Logging initialization
- `modules.network_base` - Device inventory parsing
- `modules.adapters` - CLI task execution (connectivity, backup, audit)
- `utils.backup_util` - System backup utilities
- `tests.smoke_tests` - Test suite execution
- `vlan_checker_gui` - Desktop GUI (Tkinter)
- `vlan_checker_web` - Web interface (Flask)

### External Dependencies
- `argparse` - Command-line argument parsing
- `sys` - System operations
- `os` - File system operations
- `telnetlib` / `telnetlib_compat` - Telnet compatibility for Python 3.13+

## Functions

### `_read_version()`

**Purpose**: Read version from VERSION file (single source of truth)

**Returns**: `str` - Version string (e.g., "7.0.85")

**Implementation**:
```python
def _read_version():
    """Read version from VERSION file (single source of truth)."""
    try:
        base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, 'VERSION'), 'r', encoding='utf-8') as f:
            return f.read().strip().lstrip('v')
    except Exception:
        return "0.0.0-DEV"
```

**Behavior**:
- Checks if running from PyInstaller bundle (`sys.frozen`)
- Reads VERSION file from appropriate location
- Strips 'v' prefix if present
- Returns "0.0.0-DEV" if file not found

### `check_environment()`

**Purpose**: Verify core system files exist before execution

**Returns**: `None` (exits on failure)

**Implementation**:
```python
def check_environment():
    """Verify core system files exist before execution."""
    critical_files = ["inventory.txt"]
    missing = [f for f in critical_files if not os.path.exists(f)]
    
    from utils.output_paths import ensure_data_layout, get_data_root
    ensure_data_layout()
    print(f"[System] Output data root: {get_data_root()}")

    from utils.structured_logger import get_logger
    logger = get_logger()
    logger.info(f"Network Swiss Tool Pro v{VERSION} starting", context={"version": VERSION})
            
    if missing:
        print(f"[FATAL] System initialization failed. Missing critical files: {', '.join(missing)}")
        print("Please ensure inventory.txt exists in the root directory.")
        sys.exit(1)
```

**Behavior**:
- Checks for `inventory.txt` in root directory
- Ensures data layout is created
- Initializes structured logging
- Logs application startup
- Exits with error if critical files missing

### `run_cli_task(task, user=None, pwd=None, enb=None)`

**Purpose**: Execute specific tasks without a GUI/Web interface

**Parameters**:
- `task` (str): Task type - "connectivity", "backup", "audit", "sys-backup"
- `user` (str, optional): Username
- `pwd` (str, optional): Password
- `enb` (str, optional): Enable password

**Returns**: `None`

**Implementation**:
```python
def run_cli_task(task, user=None, pwd=None, enb=None):
    """Execute specific tasks without a GUI/Web interface."""
    from modules.adapters import run_connectivity, run_config_backup, run_network_audit
    import getpass
    
    # Prompt for credentials if not provided
    if not user:
        user = input("Username: ")
    if not pwd:
        pwd = getpass.getpass("Password: ")
    if not enb:
        enb = getpass.getpass("Enable Password (press Enter if none): ")

    from modules.network_base import get_devices_from_file
    devices = get_devices_from_file("inventory.txt")
    
    if not devices:
        print("[ERROR] No devices found in inventory.txt.")
        return

    log = lambda m: print(f"[CLI] {m}")

    if task == "connectivity":
        run_connectivity(devices, user, pwd, enb, log)
    elif task == "backup":
        run_config_backup(devices, user, pwd, enb, "", log)
    elif task == "audit":
        run_network_audit(devices, user, pwd, enb, log)
    elif task == "sys-backup":
        from utils.backup_util import create_backup
        create_backup()
    else:
        print(f"[ERROR] Unknown CLI task: {task}")
```

**Behavior**:
- Prompts for credentials if not provided
- Loads device inventory from `inventory.txt`
- Executes specified task via adapters module
- Supports: connectivity check, config backup, network audit, system backup

### `run_tests(category=None)`

**Purpose**: Run smoke test suite

**Parameters**:
- `category` (str, optional): Test category - "infrastructure", "data", "network", "integration"

**Returns**: `int` - Exit code (0 for success, 1 for failure)

**Implementation**:
```python
def run_tests(category=None):
    """Run smoke test suite."""
    from tests.smoke_tests import run_tests as smoke_run
    
    print("[System] Running Smoke Tests...")
    summary = smoke_run(category=category, verbose=True)
    
    return 0 if summary["failed"] == 0 and summary["errors"] == 0 else 1
```

**Behavior**:
- Invokes smoke test suite from `tests.smoke_tests`
- Returns exit code based on test results
- Supports category-specific test execution

### `main()`

**Purpose**: Main entry point - parses arguments and dispatches to appropriate mode

**Returns**: `None` (exits via sys.exit for test mode)

**Implementation**:
```python
def main():
    parser = argparse.ArgumentParser(description=f"Network Swiss Tool Pro v{VERSION}")
    subparsers = parser.add_subparsers(dest="mode", help="Execution mode")

    # GUI Mode (Default)
    gui_parser = subparsers.add_parser("gui", help="Launch Desktop GUI")
    
    # Web Mode
    web_parser = subparsers.add_parser("web", help="Launch Web Interface")

    # CLI Mode
    cli_parser = subparsers.add_parser("cli", help="Run Headless CLI Tasks")
    cli_parser.add_argument("--task", required=True, choices=["connectivity", "backup", "audit", "sys-backup", "backup-check"], help="Task to execute")
    cli_parser.add_argument("--user", help="Username")

    # Test Mode
    test_parser = subparsers.add_parser("test", help="Run Smoke Tests")
    test_parser.add_argument("--category", choices=["infrastructure", "data", "network", "integration"], help="Test category")

    args = parser.parse_args()

    check_environment()

    if args.mode == "web":
        print("[System] Launching Web Edition...")
        import vlan_checker_web
        vlan_checker_web.run_web()
    elif args.mode == "cli":
        print(f"[System] Executing CLI Task: {args.task}...")
        if args.task == "backup-check":
            from modules.network_base import get_devices_from_file
            from modules.adapters import run_startup_backup_check
            
            def log(msg):
                print(msg)
            
            devices = get_devices_from_file("inventory.txt")
            if devices:
                run_startup_backup_check(devices, log)
            else:
                print("[ERROR] No devices found in inventory.txt")
        else:
            run_cli_task(args.task, user=args.user)
    elif args.mode == "test":
        exit_code = run_tests(category=args.category)
        sys.exit(exit_code)
    else:
        # Default to GUI
        print("[System] Launching Desktop Edition...")
        import vlan_checker_gui
        vlan_checker_gui.run_gui()
```

**Behavior**:
- Parses command-line arguments
- Dispatches to appropriate mode:
  - `web`: Launch Flask web interface
  - `cli`: Execute headless CLI tasks
  - `test`: Run smoke tests
  - `gui` (default): Launch Tkinter desktop GUI

## Execution Modes

### GUI Mode (Default)
```bash
python main.py
python main.py gui
```
- Launches Tkinter desktop GUI
- Imports `vlan_checker_gui`
- Calls `vlan_checker_gui.run_gui()`

### Web Mode
```bash
python main.py web
```
- Launches Flask web interface
- Imports `vlan_checker_web`
- Calls `vlan_checker_web.run_web()`

### CLI Mode
```bash
python main.py cli --task connectivity --user admin
python main.py cli --task backup --user admin
python main.py cli --task audit --user admin
python main.py cli --task sys-backup
python main.py cli --task backup-check
```
- Executes headless tasks
- Supports: connectivity, backup, audit, sys-backup, backup-check
- Prompts for credentials if not provided

### Test Mode
```bash
python main.py test
python main.py test --category infrastructure
python main.py test --category data
python main.py test --category network
python main.py test --category integration
```
- Runs smoke test suite
- Supports category-specific tests
- Returns exit code based on results

## Data Structures

### VERSION File
- **Location**: `VERSION` (root directory)
- **Format**: Plain text version string (e.g., "7.0.85")
- **Purpose**: Single source of truth for version information

### inventory.txt
- **Location**: `inventory.txt` (root directory)
- **Format**: Device inventory (one per line)
- **Purpose**: List of network devices to manage
- **Required**: Critical file for CLI execution

## Error Handling

### Missing Critical Files
- **Error**: `inventory.txt` not found
- **Action**: Print error message and exit with code 1
- **Message**: "[FATAL] System initialization failed. Missing critical files: inventory.txt"

### Empty Device Inventory
- **Error**: No devices in `inventory.txt`
- **Action**: Print error message and return
- **Message**: "[ERROR] No devices found in inventory.txt."

### Unknown CLI Task
- **Error**: Invalid task specified
- **Action**: Print error message
- **Message**: "[ERROR] Unknown CLI task: {task}"

## Usage Examples

### Launch Desktop GUI
```bash
python main.py
```

### Launch Web Interface
```bash
python main.py web
```

### Run Connectivity Check
```bash
python main.py cli --task connectivity --user admin
```

### Run Config Backup
```bash
python main.py cli --task backup --user admin
```

### Run Network Audit
```bash
python main.py cli --task audit --user admin
```

### Run System Backup
```bash
python main.py cli --task sys-backup
```

### Run Smoke Tests
```bash
python main.py test
```

### Run Category-Specific Tests
```bash
python main.py test --category network
```

## Related Documentation

- `vlan_checker_gui.py.md` - Desktop GUI documentation
- `vlan_checker_web.py.md` - Web interface documentation
- `modules/network_base.py.md` - Network base module documentation
- `modules/adapters.py.md` - Adapters module documentation
- `tests/smoke_tests.py.md` - Smoke test documentation

## Cross-References

- References: `utils/output_paths.py` (data layout)
- References: `utils/structured_logger.py` (logging)
- References: `modules/network_base.py` (device inventory)
- References: `modules/adapters.py` (CLI tasks)
- References: `vlan_checker_gui.py` (desktop GUI)
- References: `vlan_checker_web.py` (web interface)
- Referenced by: All execution modes
