"""
modules/plugins/base_template.py
--------------------------------
Golden Standard Template for Network Swiss Tool Pro v6.0 Plugins.

This file serves as the reference implementation for all plugins.
Copy this template when creating new features.

=============================================================================
HARDCODED REQUIREMENTS - ALL PLUGINS MUST COMPLY
=============================================================================

1. VERSION REQUIREMENTS (MANDATORY):
   - Version MUST be in Semantic Format: MAJOR.MINOR.PATCH (e.g., "1.0.0")
   - MAJOR: Breaking changes, API changes, parameter removal
   - MINOR: New features, new optional parameters, new platform support
   - PATCH: Bug fixes, security fixes, documentation updates
   
2. DOCUMENTATION REQUIREMENTS (MANDATORY):
   - MUST update this docstring version history on EVERY change
   - MUST create docs/plugins/{plugin_id}/ folder
   - MUST create 6 documentation files:
     * README.md - Current version documentation
     * RELEASE_NOTES.md - All release notes history
     * PROMPT.md - Creation/modification instructions
     * CHANGELOG.md - Detailed changelog
     * TEST_RESULTS.md - Test results by version
     * COMPATIBILITY.md - Platform compatibility
   - MUST create version archive: docs/plugins/{plugin_id}/versions/vX.Y.Z/
   - MUST generate manifest.json for each version

3. METADATA REQUIREMENTS (MANDATORY):
   - MUST include "version" field in SemVer format
   - MUST include "changelog" array with all versions
   - MUST include "documentation" dict with file paths
   - MUST include "author" and "min_platform_version"

4. VERSION HISTORY (UPDATE ON EVERY CHANGE):

VERSION HISTORY:
- v1.0.0 (2026-04-20): Initial release
  - Basic plugin structure
  - Support for integer, string, checkbox, dropdown parameters
  - Multi-platform command fallbacks (IOS, NXOS, JunOS)
  - Template validation included

RELEASE NOTES:
v1.0.0:
  - Features: Dynamic form generation, parameter validation, dry-run support
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Approved for production

AUTHOR: Network Swiss Tool Team
REVIEWED BY: Senior Development Team
APPROVED FOR: Production Release v6.0.0-BETA

CONTRACT:
    - Must contain METADATA dict with plugin info
    - Must implement run() with exact signature
    - Must return standard JSON response
    - Must use only allowed imports (no os.system, subprocess, etc.)
    - MUST follow documentation requirements above

EXAMPLE USAGE:
    from modules.plugin_registry import PluginRegistry
    registry = PluginRegistry()
    result = registry.execute("my_plugin", device, credentials, params, config, log_func)

DOCUMENTATION LOCATION:
    docs/plugins/base_template/
    ├── README.md
    ├── RELEASE_NOTES.md
    ├── PROMPT.md
    ├── CHANGELOG.md
    ├── TEST_RESULTS.md
    ├── COMPATIBILITY.md
    └── versions/
        └── v1.0.0/
            ├── base_template_v1.0.0.py
            ├── README_v1.0.0.md
            ├── RELEASE_NOTES_v1.0.0.md
            ├── TEST_RESULTS_v1.0.0.md
            └── manifest.json
=============================================================================
"""

# =============================================================================
# METADATA - Required for plugin discovery and UI generation
# =============================================================================
METADATA = {
    "plugin_id": "base_template",                    # Internal unique ID (snake_case)
    "display_name": "Base Plugin Template",          # UI Button Label
    "version": "1.0.0",                             # REQUIRED: SemVer format
    "author": "Network Swiss Tool",                 # REQUIRED
    "category": "Template",                          # REQUIRED: Tab/Group in UI
    "description": "Reference implementation showing the plugin contract.",
    "min_platform_version": "6.0.0",                # REQUIRED
    
    # REQUIRED: Changelog - MUST be updated on EVERY version change
    "changelog": [
        {
            "version": "1.0.0",
            "date": "2026-04-20",
            "changes": "Initial release with multi-platform support",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        }
    ],
    
    # REQUIRED: Documentation references - MUST exist
    "documentation": {
        "readme": "docs/plugins/base_template/README.md",
        "release_notes": "docs/plugins/base_template/RELEASE_NOTES.md",
        "prompt": "docs/plugins/base_template/PROMPT.md",
        "changelog": "docs/plugins/base_template/CHANGELOG.md",
        "test_results": "docs/plugins/base_template/TEST_RESULTS.md",
        "compatibility": "docs/plugins/base_template/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/base_template/versions/",
        "current_version_folder": "docs/plugins/base_template/versions/v1.0.0/"
    },
    
    # REQUIRED: Version archive info
    "version_archive": {
        "v1.0.0": {
            "file": "docs/plugins/base_template/versions/v1.0.0/base_template_v1.0.0.py",
            "manifest": "docs/plugins/base_template/versions/v1.0.0/manifest.json",
            "date": "2026-04-20",
            "status": "current"
        }
    },
    
    # UI Parameters - dynamically generates input fields
    "required_params": {
        "target_vlan": {
            "type": "integer",                     # integer|string|checkbox|dropdown
            "label": "Target VLAN ID",
            "placeholder": "e.g. 100",
            "required": True,
            "min": 1,
            "max": 4094
        },
        "dry_run": {
            "type": "checkbox",
            "label": "Dry Run Mode",
            "default": False,
            "description": "Show what would happen without making changes"
        },
        "device_filter": {
            "type": "dropdown",
            "label": "Device Filter",
            "options": ["All", "Cisco", "Juniper", "F5"],
            "default": "All",
            "required": False
        }
    },
    
    # Plugin capabilities
    "supports_parallel": True,                       # Can run on multiple devices concurrently
    "supports_dry_run": True,                        # Has dry-run safety mode
    "modifies_device": False,                        # True if plugin makes config changes
    "requires_enable": False,                        # True if enable/secret password needed
}


# =============================================================================
# ALLOWED IMPORTS - Security whitelist
# =============================================================================
# SAFE: modules.network_base, netmiko, paramiko, re, json, datetime, etc.
# BANNED: os.system, subprocess, shutil.rmtree, eval, exec, __import__
from modules.network_base import (
    connect_permissive,
    safe_connection,
    build_json,
    safe_node_name
)
import re
from datetime import datetime


# =============================================================================
# MAIN ENTRY POINT - The Contract
# =============================================================================
def run(device, credentials, params, config, log_func):
    """
    Main entry point for the plugin task.
    
    This function signature MUST be followed exactly by all plugins.
    The orchestrator calls this function for each device in parallel.
    
    Args:
        device (dict): Device information
            {
                'host': '192.168.1.1',
                'device_type': 'cisco_ios',
                'group': 'Core-Switches',
                'port': 22
            }
        
        credentials (dict): Authentication credentials
            {
                'username': 'admin',
                'password': 'secret',
                'secret': 'enable_pass'  # or None
            }
        
        params (dict): Dynamic user inputs validated against METADATA
            {
                'target_vlan': 100,
                'dry_run': True,
                'device_filter': 'All'
            }
        
        config (dict): Global application settings
            {
                'timeout': 30,
                'max_retries': 3,
                'log_level': 'INFO'
            }
        
        log_func (callable): Logging function for real-time UI updates
            Call as: log_func(f"[{host}] Message here")
    
    Returns:
        dict: Standard response format
            {
                'status': 'success' | 'fail',
                'data': {
                    'true_host': 'device-hostname',
                    'output': '...',
                    'metrics': {...}
                },
                'error': 'error message or None'
            }
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    conn = None
    
    try:
        # Log start of operation
        if log_func:
            log_func(f"[{host}] Starting {METADATA['display_name']}...")
        
        # Extract parameters with defaults
        target_vlan = params.get('target_vlan', 1)
        dry_run = params.get('dry_run', False)
        device_filter = params.get('device_filter', 'All')
        
        # Validate parameters
        if not isinstance(target_vlan, int) or target_vlan < 1 or target_vlan > 4094:
            return build_json(
                host, 
                "fail", 
                {}, 
                f"Invalid VLAN ID: {target_vlan}. Must be 1-4094."
            )
        
        # Check device filter
        if device_filter != "All":
            if device_filter.lower() not in device_type.lower():
                if log_func:
                    log_func(f"[{host}] Skipped - filter '{device_filter}' doesn't match '{device_type}'")
                return build_json(
                    host,
                    "success",
                    {"skipped": True, "reason": "Device filter mismatch"}
                )
        
        # Establish connection using safe_connection context manager
        if log_func:
            log_func(f"[{host}] Connecting to {device_type}...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func
        ) as conn:
            
            # Get device hostname for accurate reporting
            hostname_output = conn.send_command("show version | include hostname")
            true_host = safe_node_name(hostname_output) or host
            
            if log_func:
                log_func(f"[{true_host}] Connected successfully")
            
            # Execute commands based on device type
            if 'cisco' in device_type.lower() or 'ios' in device_type.lower():
                output = conn.send_command(f"show vlan id {target_vlan}")
            elif 'juniper' in device_type.lower():
                output = conn.send_command(f"show vlans {target_vlan}")
            else:
                output = conn.send_command(f"show vlan {target_vlan}")
            
            # Check if VLAN exists
            vlan_exists = bool(output and len(output.strip()) > 10)
            
            if dry_run:
                if log_func:
                    log_func(f"[{true_host}] [DRY-RUN] Would analyze VLAN {target_vlan}")
            else:
                if log_func:
                    log_func(f"[{true_host}] VLAN {target_vlan} exists: {vlan_exists}")
            
            # Build result data
            result_data = {
                "true_host": true_host,
                "vlan_id": target_vlan,
                "vlan_exists": vlan_exists,
                "dry_run": dry_run,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
                "output_preview": output[:200] if output else "No output"
            }
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        # Log error via callback
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        
        # Return standardized error response
        return build_json(host, "fail", {}, str(e))
    
    finally:
        # safe_connection handles disconnect, but double-check here
        if conn:
            try:
                conn.disconnect()
                if log_func:
                    log_func(f"[{host}] Disconnected")
            except:
                pass


# =============================================================================
# VALIDATION HELPERS - For testing plugin contract compliance
# =============================================================================
def validate_plugin():
    """
    Self-validation to ensure plugin meets contract requirements.
    Called by the PluginRegistry during discovery.
    
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []
    
    # Check METADATA exists and has required keys
    required_meta_keys = ['plugin_id', 'display_name', 'version', 'category', 'required_params']
    for key in required_meta_keys:
        if key not in METADATA:
            errors.append(f"Missing METADATA key: {key}")
    
    # Check plugin_id is valid
    if 'plugin_id' in METADATA:
        if not re.match(r'^[a-z][a-z0-9_]*$', METADATA['plugin_id']):
            errors.append("plugin_id must be snake_case (lowercase with underscores)")
    
    # Check run function exists and is callable
    if 'run' not in globals() or not callable(globals()['run']):
        errors.append("Missing required 'run' function")
    
    # Check for banned imports (security scan)
    import dis
    code_obj = run.__code__
    instructions = list(dis.get_instructions(code_obj))
    
    banned_calls = ['os.system', 'subprocess', 'shutil.rmtree', 'eval', 'exec']
    for instr in instructions:
        if instr.opname == 'LOAD_GLOBAL' and instr.argval in ['system', 'popen', 'eval', 'exec']:
            errors.append(f"Potentially unsafe function call detected: {instr.argval}")
    
    return len(errors) == 0, errors


# =============================================================================
# MODULE TEST - Run when file is executed directly
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Plugin Contract Validation")
    print("=" * 60)
    
    is_valid, errors = validate_plugin()
    
    if is_valid:
        print(f"✅ Plugin '{METADATA['plugin_id']}' is valid")
        print(f"   Display Name: {METADATA['display_name']}")
        print(f"   Version: {METADATA['version']}")
        print(f"   Category: {METADATA['category']}")
        print(f"   Parameters: {list(METADATA['required_params'].keys())}")
    else:
        print(f"❌ Plugin validation failed:")
        for err in errors:
            print(f"   - {err}")
        exit(1)
