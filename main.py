"""
main.py
-------
Unified Entry Point for Network Swiss Tool Pro.

USAGE:
    python main.py gui      # Launches Desktop Interface (Default)
    python main.py web      # Launches Web Interface
    python main.py cli      # Entry to headless CLI tasks (Backup/Audit)
    python main.py test     # Run smoke tests
"""

# CRITICAL: Install telnetlib compatibility for Python 3.13+
# Must be before any netmiko/Paramiko imports
try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401

import argparse
import sys
import os

def _read_version():
    """Read version from VERSION file (single source of truth)."""
    try:
        base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, 'VERSION'), 'r', encoding='utf-8') as f:
            return f.read().strip().lstrip('v')
    except Exception:
        return "0.0.0-DEV"

VERSION = _read_version()

def check_environment():
    """Verify core system files exist before execution."""
    critical_files = ["inventory.txt"]
    missing = [f for f in critical_files if not os.path.exists(f)]
    
    from utils.output_paths import ensure_data_layout, get_data_root
    ensure_data_layout()
    print(f"[System] Output data root: {get_data_root()}")

    # Initialize structured logging
    from utils.structured_logger import get_logger
    logger = get_logger()
    logger.info(f"Network Swiss Tool Pro v{VERSION} starting", context={"version": VERSION})
            
    if missing:
        print(f"[FATAL] System initialization failed. Missing critical files: {', '.join(missing)}")
        print("Please ensure inventory.txt exists in the root directory.")
        sys.exit(1)

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

    # Load shared inventory parser (from vlan_checker_gui or similar)
    # Actually, main.py should have its own inventory loader or use the one in network_base.
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

def run_tests(category=None):
    """Run smoke test suite."""
    from tests.smoke_tests import run_tests as smoke_run
    
    print("[System] Running Smoke Tests...")
    summary = smoke_run(category=category, verbose=True)
    
    # Return exit code based on results
    return 0 if summary["failed"] == 0 and summary["errors"] == 0 else 1


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
            # Run startup backup check
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

if __name__ == "__main__":
    main()
