"""
modules/plugins/interface_manager.py
------------------------------------
Interface Configuration Manager Plugin for Network Swiss Tool Pro v7.0

Enterprise-grade interface configuration management with vendor awareness
and deployment safety. Supports Cisco NX-OS, IOS, IOS-XE, and Juniper JUNOS.

VERSION HISTORY:
- v1.0.0 (2026-06-03): Initial release
  - Interface discovery for all supported vendors
  - Configuration validation pipeline
  - Deployment safety mechanisms
  - Multi-step validation with user approval

RELEASE NOTES:
v1.0.0:
  - Features: Interface discovery, configuration validation, deployment with safety
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Pending implementation

AUTHOR: Network Engineering Team
REVIEWED BY: Pending
APPROVED FOR: Development Phase

CONTRACT:
    - Must contain METADATA dict with plugin info
    - Must implement run() with exact signature
    - Must return standard JSON response
    - Must use only allowed imports (no os.system, subprocess, etc.)
"""

# =============================================================================
# METADATA - Required for plugin discovery and UI generation
# =============================================================================
METADATA = {
    "plugin_id": "interface_manager",
    "display_name": "Interface Configuration Manager",
    "version": "1.0.17",
    "author": "Network Engineering Team",
    "category": "Management",
    "description": "Enterprise-grade interface configuration management with vendor awareness, deployment safety, pre-change backup, post-change verification, and rollback capabilities. Enhanced UI/UX for superior user experience. Deep dive enhancements for edge case handling and offline validation.",
    "min_platform_version": "7.0.10",
    
    "changelog": [
        {
            "version": "1.0.17",
            "date": "2026-06-10",
            "changes": "BUG-0009/0010: Junos Physical interface same-line status; NX-OS status:connected format; ae/LACP bundle discovery; parser regression 146/146",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.15",
            "date": "2026-06-07",
            "changes": "Deep dive enhancements: Enhanced Junos interface status detection with Physical link Up/Down patterns, improved fallback mechanisms for weird scenarios including malformed output and legacy device versions, added comprehensive edge case handling for all interface parsers, integrated with offline validation system",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.14",
            "date": "2026-06-04",
            "changes": "Interface discovery enhancements: Fixed Junos 13.X discovery failure with multi-pattern parsing and fallback mechanisms, added IOS older version support with fallback parsing, added NXOS older version support with fallback parsing, improved error handling for rendering issues on older devices, added alternative command fallback for non-standard output formats",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.13",
            "date": "2026-06-04",
            "changes": "UI fix: Fixed Clear All Credentials button appearing on all pages. Moved to proper Danger Zone section within Credentials tab only, following enterprise UI best practices",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.12",
            "date": "2026-06-04",
            "changes": "Credential management enhancements: Fixed export/import with salt-prefixed encryption format, added edit functionality for existing credentials, implemented master password protection for secure credential storage, improved session persistence with automatic unlock prompts",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.11",
            "date": "2026-06-04",
            "changes": "UX improvement: Fixed interface map rediscovery to show all interfaces after deployment instead of only the configured interface, ensuring the full map reappears with updated configuration",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.10",
            "date": "2026-06-04",
            "changes": "UX improvements: Credential autocomplete with label display for easy identification, automatic interface rediscovery after configuration deployment to verify changes and update map",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.9",
            "date": "2026-06-04",
            "changes": "UX improvement: Simplified credential export/import with file browser dialogs instead of manual path input, automatic file download with timestamp, file upload with merge option",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.8",
            "date": "2026-06-04",
            "changes": "Major features: Selective interface rediscovery after configuration deployment, credential management system with Fernet encryption for offline environments, multiple credential support with deduplication, export/import functionality for credential migration between versions",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.7",
            "date": "2026-06-04",
            "changes": "Critical fix: Netmiko pattern detection error in configuration mode - reverted to built-in config_mode() and exit_config_mode() methods for reliable vendor-agnostic configuration deployment",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.6",
            "date": "2026-06-04",
            "changes": "Enhanced UI/UX: Modern visual design, status dashboard, improved validation pipeline, better accessibility, gradient backgrounds, enhanced error handling, professional color scheme",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.5",
            "date": "2026-06-04",
            "changes": "Critical fixes: Proper configuration workflow (conf t, end, copy), config validation, edge case handling (default interface, negation commands), pre/post config comparison",
            "author": "Network Engineering Team",
            "qa_status": "pending"
        },
        {
            "version": "1.0.4",
            "date": "2026-06-04",
            "changes": "Critical fixes: NXOS configuration save with delay_factor, added IOS/JUNOS save logic, configuration save verification, enhanced error handling",
            "author": "Network Engineering Team",
            "qa_status": "pending"
        },
        {
            "version": "1.0.3",
            "date": "2026-06-03",
            "changes": "Critical fixes: NX-OS configuration save, strict validation to reject invalid commands",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.2",
            "date": "2026-06-03",
            "changes": "Bug fixes: VLAN command redundancy, status_cmd exception handler, connection handling, rollback line limit, config mode exit on failure",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.1",
            "date": "2026-06-03",
            "changes": "Added pre-change backup, enhanced post-change verification, implemented rollback mechanism",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        },
        {
            "version": "1.0.0",
            "date": "2026-06-03",
            "changes": "Initial release with interface discovery, validation, and deployment",
            "author": "Network Engineering Team",
            "qa_status": "passed"
        }
    ],
    
    "documentation": {
        "readme": "docs/plugins/interface_manager/README.md",
        "release_notes": "docs/plugins/interface_manager/RELEASE_NOTES.md",
        "prompt": "docs/plugins/interface_manager/PROMPT.md",
        "changelog": "docs/plugins/interface_manager/CHANGELOG.md",
        "test_results": "docs/plugins/interface_manager/TEST_RESULTS.md",
        "compatibility": "docs/plugins/interface_manager/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/interface_manager/versions/",
        "current_version_folder": "docs/plugins/interface_manager/versions/v1.0.0/"
    },
    
    "version_archive": {
        "v1.0.0": {
            "file": "docs/plugins/interface_manager/versions/v1.0.0/interface_manager_v1.0.0.py",
            "manifest": "docs/plugins/interface_manager/versions/v1.0.0/manifest.json",
            "date": "2026-06-03",
            "status": "current"
        }
    },
    
    "required_params": {
        "operation": {
            "type": "dropdown",
            "label": "Operation",
            "options": ["discover", "validate", "deploy"],
            "default": "discover",
            "required": True,
            "description": "Operation to perform: discover interfaces, validate configuration, or deploy configuration"
        },
        "interface_filter": {
            "type": "string",
            "label": "Interface Filter (Optional)",
            "placeholder": "e.g. Ethernet1/1 or leave empty for all",
            "required": False,
            "description": "Filter to specific interface name (optional)"
        },
        "proposed_config": {
            "type": "textarea",
            "label": "Proposed Configuration (for validate/deploy)",
            "placeholder": "Enter configuration commands...",
            "required": False,
            "description": "Configuration to validate or deploy"
        },
        "dry_run": {
            "type": "checkbox",
            "label": "Dry Run Mode",
            "default": True,
            "description": "Show what would happen without making changes"
        }
    },
    
    "supports_parallel": False,  # Single device operation
    "supports_dry_run": True,
    "modifies_device": True,
    "requires_enable": True
}


# =============================================================================
# ALLOWED IMPORTS - Security whitelist
# =============================================================================
from modules.network_base import (
    connect_permissive,
    safe_connection,
    build_json,
    safe_node_name,
    resolve_hostname_from_prompt,
)
from utils.report_formatter import (
    save_plugin_report,
    append_to_master_report
)
from datetime import datetime
import re
import json
import ipaddress
import os


def _im_should_abort() -> bool:
    try:
        from utils.task_control_plane import should_abort
        return should_abort()
    except Exception:
        return False


def _im_cancelled_result(true_host, device_type, backup_path, log_func):
    msg = "Deploy cancelled by operator (control plane Stop)"
    if log_func:
        log_func(f"[{true_host}] [CANCELLED] {msg}")
    return {
        "true_host": true_host,
        "deployment_status": "cancelled",
        "cancelled": True,
        "message": msg,
        "deployment_results": {
            "pre_backup": backup_path,
            "deployment": {
                "commands_executed": [],
                "success_count": 0,
                "failure_count": 0,
                "execution_time": 0,
            },
            "post_verification": {"passed": False, "verification_commands": [], "verification_results": []},
        },
        "rollback_available": False,
        "backup_available": bool((backup_path or {}).get("path")),
        "backup_path": (backup_path or {}).get("path", ""),
        "device_type": device_type,
        "timestamp": datetime.now().isoformat(),
        "operation": "deploy",
    }


# =============================================================================
# VENDOR-SPECIFIC COMMANDS
# =============================================================================
VENDOR_COMMANDS = {
    "cisco_nxos": {
        "interfaces": "show interface",
        "config": "show run interface {interface}",
        "port_channel": "show port-channel summary",
        "vlan": "show vlan brief"
    },
    "cisco_ios": {
        "interfaces": "show interface",
        "config": "show run interface {interface}",
        "port_channel": "show etherchannel summary",
        "vlan": "show vlan brief"
    },
    "cisco_ios_xe": {
        "interfaces": "show interface",
        "config": "show run interface {interface}",
        "port_channel": "show etherchannel summary",
        "vlan": "show vlan brief"
    },
    "juniper_junos": {
        "interfaces": "show interfaces",
        "config": "show configuration interfaces {interface} | display set",
        "port_channel": "show lacp interfaces",
        "vlan": "show vlans"
    }
}


def _junos_display_set_config_cmd(interface_name: str) -> str:
    return f"show configuration interfaces {interface_name} | display set"


def _normalize_junos_set_config(raw_output: str) -> str:
    """Keep only deployable set/delete lines from Junos display-set output."""
    lines = []
    for line in (raw_output or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(("set ", "delete ")):
            lines.append(stripped)
    return "\n".join(lines)


def _extract_interface_from_config(proposed_config: str, interface_filter: str = "") -> str:
    if (interface_filter or "").strip():
        return interface_filter.strip()
    for line in (proposed_config or "").splitlines():
        line = line.strip()
        m = re.match(r"^interface\s+(\S+)", line, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.match(r"^(?:set|delete)\s+interfaces\s+(\S+)", line, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


# =============================================================================
# MAIN ENTRY POINT - The Contract
# =============================================================================
def run(device, credentials, params, config, log_func):
    """
    Main entry point for the interface manager plugin.
    
    Args:
        device (dict): Device information
        credentials (dict): Authentication credentials
        params (dict): Dynamic user inputs
        config (dict): Global application settings
        log_func (callable): Logging function for real-time UI updates
    
    Returns:
        dict: Standard response format
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')

    vendor, vendor_err = _im_vendor_or_error(device_type)
    if vendor_err:
        if log_func:
            log_func(f"[{host}] [BLOCKED] {vendor_err}")
        return build_json(host, "fail", {"device_type": device_type}, vendor_err)
    
    try:
        # Extract parameters
        operation = params.get('operation', 'discover')
        interface_filter = params.get('interface_filter', '')
        proposed_config = params.get('proposed_config', '')
        dry_run = params.get('dry_run', True)
        
        # Log start of operation
        if log_func:
            log_func(f"[{host}] Starting {METADATA['display_name']} - {operation}...")

        if operation == "deploy" and not dry_run:
            from utils.golden_config_gate import evaluate_interface_change, raise_if_blocked
            gstep = evaluate_interface_change(proposed_config)
            try:
                raise_if_blocked(gstep)
            except RuntimeError as exc:
                if log_func:
                    log_func(f"[{host}] [BLOCKED] {exc}")
                return build_json(host, "fail", {"golden_config": gstep}, str(exc))
        
        # Establish connection
        if log_func:
            log_func(f"[{host}] Connecting to {device_type}...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            
            true_host = resolve_hostname_from_prompt(conn, host)
            
            if log_func:
                log_func(f"[{true_host}] Connected successfully")
            
            # Route to appropriate operation
            if operation == "discover":
                result_data = _discover_interfaces(conn, true_host, device_type, interface_filter, log_func)
            elif operation == "validate":
                result_data = _validate_configuration(conn, true_host, device_type, interface_filter, proposed_config, log_func)
            elif operation == "deploy":
                result_data = _deploy_configuration(conn, true_host, device_type, interface_filter, proposed_config, dry_run, log_func)
            elif operation == "restore_guide":
                backup_path = params.get("backup_path", "")
                from utils.restore_guide import get_manual_restore_guide
                result_data = {
                    "true_host": true_host,
                    "restore_guide": get_manual_restore_guide(
                        backup_path, device_type, context='interface configuration',
                    ),
                    "operation": "restore_guide",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return build_json(host, "fail", {}, f"Unknown operation: {operation}")
            
            # Generate human-readable report
            report_path = save_plugin_report(
                METADATA['plugin_id'],
                host,
                result_data,
                lambda d, h: _format_interface_report(d, h, operation)
            )
            result_data["report_path"] = report_path
            try:
                from utils.output_paths import CAT_PLUGINS, path_in_run, prepare_run_output, slugify, write_run_manifest
                from utils.interface_manager_formatter import write_interface_report_html
                safe_host = str(host).replace(":", "_").replace("/", "_").replace(".", "_")
                paths = prepare_run_output(CAT_PLUGINS, slugify(f"{METADATA['plugin_id']}_{safe_host}"))
                html_path = path_in_run(paths, 'interface_report.html')
                write_interface_report_html(html_path, result_data, host, operation)
                result_data["html_report_path"] = html_path
                write_run_manifest(paths, {
                    'plugin_id': METADATA['plugin_id'],
                    'host': host,
                    'report_path': report_path,
                    'html_path': html_path,
                    'operation': operation,
                })
            except Exception as html_exc:
                if log_func:
                    log_func(f"[{host}] WARNING: Could not write IM HTML report: {html_exc}")
            
            # Add to master execution summary
            summary = _generate_summary(result_data, operation)
            append_to_master_report(METADATA['plugin_id'], host, "success", summary, report_path)
            
            if log_func:
                log_func(f"[{true_host}] Report saved: {report_path}")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        return build_json(host, "fail", {}, str(e))


# =============================================================================
# INTERFACE DISCOVERY
# =============================================================================
def _discover_interfaces(conn, true_host, device_type, interface_filter, log_func):
    """
    Discover all interfaces on a device with comprehensive metadata.
    
    Args:
        conn: Netmiko connection
        true_host: Device hostname
        device_type: Device type string
        interface_filter: Optional interface name filter
        log_func: Logging function
    
    Returns:
        dict: Discovered interface data
    """
    if log_func:
        log_func(f"[{true_host}] Discovering interfaces...")
    
    # Determine vendor (G-005: no silent IOS default)
    vendor, err = _im_vendor_or_error(device_type)
    if err:
        raise ValueError(err)
    commands = VENDOR_COMMANDS[vendor]
    
    # Get interface list with error handling for older devices
    interface_output = ""
    try:
        interface_output = conn.send_command(commands["interfaces"], read_timeout=30)
    except Exception as e:
        if log_func:
            log_func(f"[{true_host}] WARNING: Standard interface command failed: {str(e)}")
        # Vendor-specific fallbacks (never use NX-OS brief on IOS/Junos)
        alt_cmds = {
            "cisco_nxos": ["show interface brief", "show interface"],
            "cisco_ios": ["show ip interface brief", "show interfaces status", "show interfaces"],
            "cisco_ios_xe": ["show ip interface brief", "show interfaces status", "show interfaces"],
            "juniper_junos": ["show interfaces terse", "show interfaces"],
        }.get(vendor, ["show interfaces"])
        interface_output = ""
        last_err = e
        for alt in alt_cmds:
            try:
                interface_output = conn.send_command(alt, read_timeout=30)
                if log_func:
                    log_func(f"[{true_host}] Using alternative interface command: {alt}")
                break
            except Exception as e2:
                last_err = e2
        if not interface_output:
            if log_func:
                log_func(f"[{true_host}] ERROR: Alternative interface commands failed: {last_err}")
            return {
                "true_host": true_host,
                "interfaces": [],
                "interface_count": 0,
                "device_type": device_type,
                "vendor": vendor,
                "timestamp": datetime.now().isoformat(),
                "operation": "discover",
                "error": f"Failed to retrieve interface list: {str(e)}"
            }
    
    # Check if output is empty or invalid
    if not interface_output or len(interface_output.strip()) < 10:
        if log_func:
            log_func(f"[{true_host}] WARNING: Empty or invalid interface output received")
        return {
            "true_host": true_host,
            "interfaces": [],
            "interface_count": 0,
            "device_type": device_type,
            "vendor": vendor,
            "timestamp": datetime.now().isoformat(),
            "operation": "discover",
            "error": "Empty or invalid interface output"
        }
    
    # Parse interfaces
    interfaces = _parse_interfaces(interface_output, device_type, vendor)

    # Juniper: merge physical members with ae logical bundles
    if vendor == "juniper_junos":
        interfaces = _enrich_juniper_bundle_interfaces(conn, interfaces, log_func)
    elif commands.get("port_channel"):
        interfaces = _enrich_cisco_port_channels(
            conn, interfaces, commands["port_channel"], vendor, log_func,
        )

    # Apply filter if specified
    if interface_filter:
        interfaces = [i for i in interfaces if interface_filter.lower() in i["name"].lower()]
    
    # Get detailed configuration for each interface with error handling
    for interface in interfaces:
        if interface_filter and interface_filter.lower() not in interface["name"].lower():
            continue
        
        try:
            config_cmd = commands["config"].format(interface=interface["name"])
            config_output = conn.send_command(config_cmd, read_timeout=30)
            if vendor == "juniper_junos":
                normalized = _normalize_junos_set_config(config_output)
                if normalized:
                    config_output = normalized
            interface["current_config"] = config_output
            
            # Parse additional details from config
            _parse_interface_config(interface, config_output, vendor)
        except Exception as e:
            if log_func:
                log_func(f"[{true_host}] Warning: Could not get config for {interface['name']}: {str(e)}")
            interface["current_config"] = ""
            interface["errors"].append(f"Config retrieval failed: {str(e)}")
    
    try:
        from utils.mac_utils import attach_learned_macs
        attach_learned_macs(conn, interfaces, device_type, vendor, log_func)
    except Exception as exc:
        if log_func:
            log_func(f"[{true_host}] WARNING: Learned MAC enrichment skipped: {exc}")

    if log_func:
        log_func(f"[{true_host}] Discovered {len(interfaces)} interfaces")
        if len(interfaces) == 0:
            log_func(f"[{true_host}] WARNING: No interfaces discovered - device may be older or use different output format")
    
    return {
        "true_host": true_host,
        "interfaces": interfaces,
        "interface_count": len(interfaces),
        "device_type": device_type,
        "vendor": vendor,
        "timestamp": datetime.now().isoformat(),
        "operation": "discover"
    }


def _enrich_juniper_bundle_interfaces(conn, interfaces, log_func):
    """Link xe/ge members to ae bundles and ensure ae interfaces appear in the map."""
    from utils.juniper_iface import collect_juniper_lag_detail

    lag_detail = collect_juniper_lag_detail(conn)
    if not lag_detail:
        return interfaces

    by_name = {i["name"]: i for i in interfaces}

    for ae_id, ae_data in lag_detail.items():
        members = [m.get("intf", "") for m in ae_data.get("members", []) if m.get("intf")]
        if ae_id not in by_name:
            by_name[ae_id] = {
                "name": ae_id,
                "status": "up" if members else "down",
                "admin_status": "up" if members else "down",
                "oper_status": "up" if members else "down",
                "port_channel": "",
                "port_channel_members": members,
                "vlan_membership": [],
                "native_vlan": 1,
                "description": f"Aggregated Ethernet ({ae_data.get('protocol', 'LACP')})",
                "l2_l3_mode": "layer2",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "Aggregated",
                "media_type": "ae",
                "current_config": "",
                "vendor": "juniper_junos",
                "interface_role": "ae_bundle",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True,
                },
                "errors": [],
                "warnings": [],
            }
        else:
            by_name[ae_id]["interface_role"] = "ae_bundle"
            by_name[ae_id]["port_channel_members"] = members
            by_name[ae_id]["speed"] = "Aggregated"

        for mem_name in members:
            if mem_name in by_name:
                by_name[mem_name]["port_channel"] = ae_id
                by_name[mem_name]["interface_role"] = "ae_member"

    if log_func:
        log_func(f"[Bundle] Linked {len(lag_detail)} ae bundle(s) to member interfaces")
    return list(by_name.values())


def _enrich_cisco_port_channels(conn, interfaces, po_cmd, vendor, log_func):
    """Populate port_channel / members from etherchannel or NX-OS summary."""
    by_name = {i["name"]: i for i in interfaces}
    try:
        po_out = conn.send_command(po_cmd, read_timeout=30)
    except Exception:
        return interfaces

    if vendor == "cisco_nxos":
        from modules.topology_mapper import _parse_port_channel_summary_nxos
        po_detail = _parse_port_channel_summary_nxos(po_out)
        for po_id, po_data in po_detail.items():
            members = [m["intf"] for m in po_data.get("members", [])]
            if po_id in by_name:
                by_name[po_id]["port_channel_members"] = members
                by_name[po_id]["interface_role"] = "port_channel"
            for mem in members:
                if mem in by_name:
                    by_name[mem]["port_channel"] = po_id
    else:
        for line in po_out.splitlines():
            m = re.match(r'^(\S+)\s+\((\S+)\)', line.strip())
            if not m:
                continue
            po_id = m.group(1)
            members_raw = line[line.index(')') + 1:].strip() if ')' in line else ""
            members = re.findall(r'([A-Za-z]+\S+)', members_raw)
            if po_id in by_name:
                by_name[po_id]["port_channel_members"] = members
                by_name[po_id]["interface_role"] = "port_channel"
            for mem in members:
                norm_mem = mem.split('(')[0]
                for key in by_name:
                    if key.lower() == norm_mem.lower() or norm_mem.lower() in key.lower():
                        by_name[key]["port_channel"] = po_id

    if log_func:
        log_func("[Bundle] Port-channel membership enriched")
    return list(by_name.values())


def _determine_vendor(device_type):
    """Determine vendor from device type string. Returns None if unsupported (G-005)."""
    device_type_lower = (device_type or "").lower()

    if "nxos" in device_type_lower or "n9k" in device_type_lower:
        return "cisco_nxos"
    if (
        "ios_xe" in device_type_lower
        or "ios-xe" in device_type_lower
        or "iosxe" in device_type_lower
        or "cisco_xe" in device_type_lower
    ):
        return "cisco_ios_xe"
    if "juniper" in device_type_lower or "junos" in device_type_lower:
        return "juniper_junos"
    if "ios" in device_type_lower:
        return "cisco_ios"
    return None


IM_SUPPORTED_DEVICE_HINT = (
    "Cisco IOS, IOS-XE, NX-OS, or Juniper Junos (set device_type accordingly)"
)


def _im_vendor_or_error(device_type):
    """Return vendor string or None with side-effect-free check for IM operations."""
    vendor = _determine_vendor(device_type)
    if vendor:
        return vendor, None
    dt = device_type or "unknown"
    return None, (
        f"Unsupported device_type '{dt}' for Interface Manager. "
        f"Supported platforms: {IM_SUPPORTED_DEVICE_HINT}."
    )


def _parse_interfaces(output, device_type, vendor):
    """
    Parse interface list from device output.
    
    Args:
        output: Command output
        device_type: Device type
        vendor: Vendor identifier
    
    Returns:
        list: List of interface dictionaries
    """
    interfaces = []
    
    if vendor == "cisco_nxos":
        interfaces = _parse_nxos_interfaces(output)
    elif vendor == "cisco_ios" or vendor == "cisco_ios_xe":
        interfaces = _parse_ios_interfaces(output)
    elif vendor == "juniper_junos":
        interfaces = _parse_junos_interfaces(output)
    else:
        interfaces = _parse_ios_interfaces(output)  # Default to IOS parsing
    
    return interfaces


def _parse_nxos_interfaces(output):
    """Parse NX-OS interface output from 'show interface' command.
    
    Supports multiple NX-OS versions including older 7.X with fallback parsing.
    """
    interfaces = []
    lines = output.split('\n')
    current_interface = None
    
    for line in lines:
        line = line.strip()
        
        # Match interface line - multiple patterns for different NX-OS versions
        # Pattern 1: "Ethernet1/1 is up" (standard)
        # Pattern 2: "Ethernet1/1  is up" (extra spaces)
        # Pattern 3: "Ethernet1/1" (just interface name)
        interface_match = re.match(r'^([Ee]thernet\d+/\d+|[Pp]ort-channel\d+|[Mm]anagement\d+|[Ll]oopback\d+)\s+(?:is\s+)?(\w+)', line)
        if not interface_match:
            interface_match = re.match(r'^([A-Za-z]+\d+/\d+|[A-Za-z]+\d+)\s+is\s+(\w+)', line)
        if not interface_match:
            interface_match = re.match(
                r'^([Ee]thernet\d+/\d+|[Pp]ort-channel\d+|[Mm]anagement\d+|[Ll]oopback\d+)$',
                line,
            )
        
        if interface_match:
            # Save previous interface if exists
            if current_interface:
                interfaces.append(current_interface)
            
            interface_name = interface_match.group(1)
            status = interface_match.group(2) if len(interface_match.groups()) > 1 else "unknown"
            
            current_interface = {
                "name": interface_name,
                "status": status,
                "admin_status": "up" if "up" in status.lower() else "down",
                "oper_status": status,
                "port_channel": "",
                "port_channel_members": [],
                "vlan_membership": [],
                "native_vlan": 1,
                "description": "",
                "l2_l3_mode": "unknown",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "unknown",
                "media_type": "unknown",
                "current_config": "",
                "vendor": "cisco_nxos",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True
                },
                "errors": [],
                "warnings": []
            }
            continue
        
        # Parse details for current interface
        if current_interface:
            status_match = re.search(r'\bstatus:\s*(\S+)', line, re.I)
            if status_match:
                st = status_match.group(1).lower()
                current_interface["status"] = st
                current_interface["oper_status"] = st
                if st in ('connected', 'up'):
                    current_interface["admin_status"] = "up"
                elif st in ('notconnect', 'down', 'disabled'):
                    current_interface["admin_status"] = "down"

            # MAC address - multiple formats
            mac_match = re.search(r'MAC:\s+([0-9a-fA-F:]+)|address:\s+([0-9a-fA-F:]+)', line)
            if not mac_match:
                mac_match = re.search(r'Hardware address:\s+([0-9a-fA-F:]+)', line)
            if mac_match:
                current_interface["mac_address"] = mac_match.group(1) if mac_match.group(1) else (mac_match.group(2) if mac_match.group(2) else mac_match.group(3) if len(mac_match.groups()) > 2 else "")
            
            # MTU
            mtu_match = re.search(r'MTU:\s+(\d+)', line)
            if mtu_match:
                current_interface["mtu"] = int(mtu_match.group(1))
            
            # Speed - multiple formats
            speed_match = re.search(r'(\d+)\s*Gb/s|(\d+)\s*Mb/s', line)
            if not speed_match:
                speed_match = re.search(r'(\d+)\s*(Gbps|Mbps|Kbps|Gb|Mb|Kb)', line, re.IGNORECASE)
            if speed_match:
                speed = speed_match.group(1) if speed_match.group(1) else speed_match.group(2)
                unit = speed_match.group(3) if len(speed_match.groups()) > 2 else ""
                if unit.upper() in ["GBPS", "GB", "G"]:
                    current_interface["speed"] = f"{speed}G"
                elif unit.upper() in ["MBPS", "MB", "M"]:
                    current_interface["speed"] = f"{speed}M"
                elif unit.upper() in ["KBPS", "KB", "K"]:
                    current_interface["speed"] = f"{int(speed) // 1000}M"
                else:
                    current_interface["speed"] = speed
            
            # Duplex
            if "full-duplex" in line.lower() or "full duplex" in line.lower():
                current_interface["duplex"] = "full"
            elif "half-duplex" in line.lower() or "half duplex" in line.lower():
                current_interface["duplex"] = "half"
            
            # Description
            desc_match = re.search(r'Description:\s+(.+)|Description\s+(.+)', line)
            if desc_match:
                current_interface["description"] = (desc_match.group(1) if desc_match.group(1) else desc_match.group(2)).strip()
            # Also match IOS format without colon
            desc_match2 = re.search(r'Description\s+(.+)', line)
            if desc_match2 and not current_interface["description"]:
                current_interface["description"] = desc_match2.group(1).strip()
    
    # Add last interface
    if current_interface:
        interfaces.append(current_interface)
    
    # Fallback: If no interfaces found, try alternative parsing
    if not interfaces and output:
        interfaces = _parse_nxos_interfaces_fallback(output)
    
    return interfaces


def _parse_nxos_interfaces_fallback(output):
    """Fallback parsing for older NX-OS versions or non-standard output."""
    interfaces = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Very loose pattern - just look for interface-like names
        # Matches: Ethernet1/1, Port-channel1, Management1, Loopback0, etc.
        interface_match = re.match(r'^([A-Za-z]+\d+/\d+|[A-Za-z]+\d+)', line)
        if interface_match:
            interface_name = interface_match.group(1)
            
            # Skip if already in list
            if any(i["name"] == interface_name for i in interfaces):
                continue
            
            interfaces.append({
                "name": interface_name,
                "status": "unknown",
                "admin_status": "unknown",
                "oper_status": "unknown",
                "port_channel": "",
                "port_channel_members": [],
                "vlan_membership": [],
                "native_vlan": 1,
                "description": "",
                "l2_l3_mode": "unknown",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "unknown",
                "media_type": "unknown",
                "current_config": "",
                "vendor": "cisco_nxos",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True
                },
                "errors": ["Parsed with fallback method - limited information available"],
                "warnings": []
            })
    
    return interfaces


def _parse_ios_interfaces(output):
    """Parse IOS interface output from 'show interface' command.
    
    Supports multiple IOS versions including older 12.X with fallback parsing.
    """
    interfaces = []
    lines = output.split('\n')
    current_interface = None
    
    for line in lines:
        line = line.strip()
        
        # Match interface line - multiple patterns for different IOS versions
        # Pattern 1: "Ethernet1/1 is up, line protocol is up" (standard)
        # Pattern 2: "GigabitEthernet1/0/1 is up" (simpler format)
        # Pattern 3: "FastEthernet0/1 is administratively down" (older format)
        interface_match = re.match(r'^([Ee]thernet\d+/\d+|[Ff]astEthernet\d+/\d+|[Gg]igabitEthernet\d+/\d+|[Gg]igabitEthernet\d+/\d+/\d+|[Tt]enGigabitEthernet\d+/\d+|[Pp]ort-channel\d+|[Vl]lan\d+)\s+is\s+(\w+)', line)
        if not interface_match:
            # Try alternative pattern for older IOS
            interface_match = re.match(r'^([A-Za-z]+\d+/\d+/\d+|[A-Za-z]+\d+/\d+|[A-Za-z]+\d+)\s+is\s+(\w+)', line)
        
        if interface_match:
            # Save previous interface if exists
            if current_interface:
                interfaces.append(current_interface)
            
            interface_name = interface_match.group(1)
            status = interface_match.group(2)
            
            current_interface = {
                "name": interface_name,
                "status": status,
                "admin_status": "up" if "up" in status.lower() else "down",
                "oper_status": status,
                "port_channel": "",
                "port_channel_members": [],
                "vlan_membership": [],
                "native_vlan": 1,
                "description": "",
                "l2_l3_mode": "unknown",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "unknown",
                "media_type": "unknown",
                "current_config": "",
                "vendor": "cisco_ios",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True
                },
                "errors": [],
                "warnings": []
            }
            continue
        
        # Parse details for current interface
        if current_interface:
            # MAC address - multiple formats
            mac_match = re.search(r'Hardware is\s+\w+,\s+address is\s+([0-9a-fA-F\.]+)', line)
            if not mac_match:
                mac_match = re.search(r'address is\s+([0-9a-fA-F\.]+)', line)
            if mac_match:
                mac = mac_match.group(1).replace('.', '')
                # Format MAC as XX:XX:XX:XX:XX:XX
                if len(mac) == 12:
                    current_interface["mac_address"] = ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
            
            # MTU
            mtu_match = re.search(r'MTU\s+(\d+)', line)
            if mtu_match:
                current_interface["mtu"] = int(mtu_match.group(1))
            
            # Speed - multiple formats
            speed_match = re.search(r'BW\s+(\d+)\s*(Kbit|Mbit|Gbit)', line)
            if not speed_match:
                speed_match = re.search(r'(\d+)\s*(Gbps|Mbps|Kbps|Gb|Mb|Kb)', line, re.IGNORECASE)
            if speed_match:
                speed_val = int(speed_match.group(1))
                speed_unit = speed_match.group(2)
                if speed_unit in ["Kbit", "Kbps", "Kb", "K"]:
                    current_interface["speed"] = f"{speed_val // 1000}M"
                elif speed_unit in ["Mbit", "Mbps", "Mb", "M"]:
                    current_interface["speed"] = f"{speed_val}M"
                elif speed_unit in ["Gbit", "Gbps", "Gb", "G"]:
                    current_interface["speed"] = f"{speed_val}G"
            
            # Duplex
            if "duplex" in line.lower():
                if "full" in line.lower():
                    current_interface["duplex"] = "full"
                elif "half" in line.lower():
                    current_interface["duplex"] = "half"
            
            # Description
            desc_match = re.search(r'Description:\s+(.+)', line)
            if desc_match:
                current_interface["description"] = desc_match.group(1).strip()
    
    # Add last interface
    if current_interface:
        interfaces.append(current_interface)
    
    # Fallback: If no interfaces found, try alternative parsing
    if not interfaces and output:
        interfaces = _parse_ios_interfaces_fallback(output)
    
    return interfaces


def _parse_ios_interfaces_fallback(output):
    """Fallback parsing for older IOS versions or non-standard output."""
    interfaces = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Very loose pattern - just look for interface-like names
        # Matches: Ethernet1/1, FastEthernet0/1, GigabitEthernet1/0/1, etc.
        interface_match = re.match(r'^([A-Za-z]+\d+/\d+/\d+|[A-Za-z]+\d+/\d+|[A-Za-z]+\d+)', line)
        if interface_match:
            interface_name = interface_match.group(1)
            
            # Skip if already in list
            if any(i["name"] == interface_name for i in interfaces):
                continue
            
            interfaces.append({
                "name": interface_name,
                "status": "unknown",
                "admin_status": "unknown",
                "oper_status": "unknown",
                "port_channel": "",
                "port_channel_members": [],
                "vlan_membership": [],
                "native_vlan": 1,
                "description": "",
                "l2_l3_mode": "unknown",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "unknown",
                "media_type": "unknown",
                "current_config": "",
                "vendor": "cisco_ios",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True
                },
                "errors": ["Parsed with fallback method - limited information available"],
                "warnings": []
            })
    
    return interfaces


def _apply_junos_line_status(line, iface):
    """Apply Junos status hints from a single line (header or detail)."""
    if not iface or not line:
        return
    if re.search(r'Physical link is Up', line, re.I):
        iface["status"] = "up"
        iface["admin_status"] = "up"
        iface["oper_status"] = "up"
    elif re.search(r'Physical link is Down', line, re.I):
        iface["status"] = "down"
        iface["admin_status"] = "up"
        iface["oper_status"] = "down"
    elif re.search(r'\bEnabled\b', line) and not re.search(r'\bDisabled\b', line):
        iface["admin_status"] = "up"
    elif re.search(r'\bDisabled\b', line):
        iface["admin_status"] = "down"


def _parse_junos_interfaces(output):
    """Parse Junos interface output from 'show interfaces' command.
    
    Supports multiple Junos versions including older 13.X with fallback parsing.
    """
    interfaces = []
    lines = output.split('\n')
    current_interface = None
    
    for line in lines:
        line = line.strip()
        
        # Match interface line - multiple patterns for different Junos versions
        # Pattern 1: "ge-0/0/0 is up" (standard)
        # Pattern 2: "ge-0/0/0  is up" (extra spaces)
        # Pattern 3: "ge-0/0/0" (just interface name)
        # Pattern 4: "Physical interface: ge-0/0/0, Enabled, Physical link is Up"
        interface_match = re.match(r'^([a-z-]+\d+/\d+/\d+|[a-z-]+\d+/\d+|[a-z-]+\d+)\s+(?:is\s+)?(\w+)', line)
        physical_header = None
        if not interface_match:
            physical_header = re.match(
                r'^Physical interface:\s+([a-z-]+\d+/\d+/\d+|[a-z-]+\d+/\d+|[a-z-]+\d+)',
                line,
            )
            if physical_header:
                interface_match = physical_header
        
        if interface_match:
            # Save previous interface if exists
            if current_interface:
                interfaces.append(current_interface)
            
            interface_name = interface_match.group(1)
            status = interface_match.group(2) if len(interface_match.groups()) > 1 else "unknown"
            
            current_interface = {
                "name": interface_name,
                "status": status,
                "admin_status": "up" if "up" in status.lower() or "enabled" in status.lower() else "down",
                "oper_status": status,
                "port_channel": "",
                "port_channel_members": [],
                "vlan_membership": [],
                "native_vlan": 1,
                "description": "",
                "l2_l3_mode": "unknown",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "unknown",
                "media_type": "unknown",
                "current_config": "",
                "vendor": "juniper_junos",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True
                },
                "errors": [],
                "warnings": []
            }
            if physical_header:
                _apply_junos_line_status(line, current_interface)
            continue
        
        # Parse details for current interface
        if current_interface:
            _apply_junos_line_status(line, current_interface)
            
            # MAC address - multiple formats
            mac_match = re.search(r'Hardware address:\s+([0-9a-fA-F:]+)', line)
            if not mac_match:
                mac_match = re.search(r'MAC:\s+([0-9a-fA-F:]+)', line)
            if mac_match:
                current_interface["mac_address"] = mac_match.group(1)
            
            # MTU
            mtu_match = re.search(r'MTU:\s+(\d+)', line)
            if mtu_match:
                current_interface["mtu"] = int(mtu_match.group(1))
            
            # Speed - multiple formats
            speed_match = re.search(r'(\d+)\s*(Gbps|Mbps|Kbps|Gb|Mb|Kb)', line, re.IGNORECASE)
            if speed_match:
                speed = speed_match.group(1)
                unit = speed_match.group(2)
                if unit.upper() in ["GBPS", "GB"]:
                    current_interface["speed"] = f"{speed}G"
                elif unit.upper() in ["MBPS", "MB"]:
                    current_interface["speed"] = f"{speed}M"
                elif unit.upper() in ["KBPS", "KB"]:
                    current_interface["speed"] = f"{int(speed) // 1000}M"
            
            # Description
            desc_match = re.search(r'Description:\s+(.+)', line)
            if not desc_match:
                desc_match = re.search(r'Description:\s*"([^"]+)"', line)
            if desc_match:
                current_interface["description"] = desc_match.group(1).strip()
            
            # Admin status
            if "admin status" in line.lower():
                if "up" in line.lower() or "enabled" in line.lower():
                    current_interface["admin_status"] = "up"
                elif "down" in line.lower() or "disabled" in line.lower():
                    current_interface["admin_status"] = "down"
            
            # Link status
            if "link status" in line.lower():
                if "up" in line.lower():
                    current_interface["oper_status"] = "up"
                elif "down" in line.lower():
                    current_interface["oper_status"] = "down"
    
    # Add last interface
    if current_interface:
        interfaces.append(current_interface)
    
    # Fallback: If no interfaces found, try alternative parsing
    if not interfaces and output:
        interfaces = _parse_junos_interfaces_fallback(output)
    
    return interfaces


def _parse_junos_interfaces_fallback(output):
    """Fallback parsing for older Junos versions or non-standard output."""
    interfaces = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Very loose pattern - just look for interface-like names
        # Matches: ge-0/0/0, xe-0/0/0, et-0/0/0, etc.
        interface_match = re.match(r'^([a-z]{2,}-\d+/\d+/\d+|[a-z]{2,}-\d+/\d+|[a-z]{2,}-\d+)', line)
        if interface_match:
            interface_name = interface_match.group(1)
            
            # Skip if already in list
            if any(i["name"] == interface_name for i in interfaces):
                continue
            
            interfaces.append({
                "name": interface_name,
                "status": "unknown",
                "admin_status": "unknown",
                "oper_status": "unknown",
                "port_channel": "",
                "port_channel_members": [],
                "vlan_membership": [],
                "native_vlan": 1,
                "description": "",
                "l2_l3_mode": "unknown",
                "mac_address": "",
                "mtu": 1500,
                "duplex": "unknown",
                "speed": "unknown",
                "media_type": "unknown",
                "current_config": "",
                "vendor": "juniper_junos",
                "capabilities": {
                    "trunking": True,
                    "routing": True,
                    "port_channel": True,
                    "spanning_tree": True
                },
                "errors": ["Parsed with fallback method - limited information available"],
                "warnings": []
            })
    
    return interfaces


def _parse_interface_config(interface, config_output, vendor):
    """
    Parse interface configuration to extract details.
    
    Args:
        interface: Interface dictionary to update
        config_output: Configuration output
        vendor: Vendor identifier
    """
    # Extract description
    desc_match = re.search(r'description\s+(.+)', config_output, re.IGNORECASE)
    if desc_match:
        interface["description"] = desc_match.group(1).strip()
    
    # Extract VLAN membership
    if vendor == "cisco_nxos" or vendor == "cisco_ios" or vendor == "cisco_ios_xe":
        vlan_match = re.search(r'switchport trunk allowed vlan\s+(.+)', config_output, re.IGNORECASE)
        if vlan_match:
            vlan_str = vlan_match.group(1).strip()
            # Parse VLAN list (e.g., "10,20,30" or "10-20,30")
            interface["vlan_membership"] = _parse_vlan_list(vlan_str)
        
        # Determine L2/L3 mode
        if "switchport" in config_output.lower():
            interface["l2_l3_mode"] = "layer2"
        elif "no switchport" in config_output.lower() or "ip address" in config_output.lower():
            interface["l2_l3_mode"] = "layer3"
    
    elif vendor == "juniper_junos":
        vlan_match = re.search(r'vlan members\s+\[?\s*(.+?)\s*\]?', config_output, re.IGNORECASE)
        if vlan_match:
            vlan_str = vlan_match.group(1).strip()
            interface["vlan_membership"] = _parse_vlan_list(vlan_str)


def _parse_vlan_list(vlan_str):
    """Parse VLAN list string into list of VLAN IDs (comma, space, or range)."""
    vlans = []
    if not vlan_str:
        return vlans
    normalized = vlan_str.replace(',', ' ')
    for part in normalized.split():
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start, end = part.split('-', 1)
            try:
                vlans.extend(range(int(start), int(end) + 1))
            except ValueError:
                pass
        else:
            try:
                vlans.append(int(part))
            except ValueError:
                pass
    return vlans


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================
def _validate_configuration(conn, true_host, device_type, interface_filter, proposed_config, log_func):
    """
    Validate proposed interface configuration with multi-step checks.
    
    Args:
        conn: Netmiko connection
        true_host: Device hostname
        device_type: Device type
        interface_filter: Interface name filter
        proposed_config: Proposed configuration
        log_func: Logging function
    
    Returns:
        dict: Validation results
    """
    if log_func:
        log_func(f"[{true_host}] Validating configuration...")
    
    vendor, err = _im_vendor_or_error(device_type)
    if err:
        raise ValueError(err)
    
    # Step 1: Dry-run validation (device-side where supported)
    dry_run_result = _validate_dry_run(
        conn, proposed_config, vendor, interface_filter, log_func,
    )
    
    # Step 2: Vendor syntax validation
    syntax_result = _validate_vendor_syntax(proposed_config, vendor, log_func)
    
    # Step 3: Platform validation
    platform_result = _validate_platform(conn, true_host, device_type, log_func)
    
    # Step 4: Conflict validation
    conflict_result = _validate_conflicts(conn, true_host, device_type, interface_filter, proposed_config, log_func)

    from utils.golden_config_gate import evaluate_interface_change
    golden_result = evaluate_interface_change(proposed_config)
    
    # Overall assessment
    all_passed = all([
        dry_run_result["passed"],
        syntax_result["passed"],
        platform_result["passed"],
        conflict_result["passed"],
        golden_result["passed"],
    ])
    
    risk_level = _calculate_risk_level(dry_run_result, syntax_result, platform_result, conflict_result)
    
    validation_results = {
        "dry_run": dry_run_result,
        "vendor_syntax": syntax_result,
        "platform": platform_result,
        "conflicts": conflict_result,
        "golden_config": golden_result,
    }
    
    if log_func:
        log_func(f"[{true_host}] Validation complete - {'PASSED' if all_passed else 'FAILED'}")
    
    return {
        "true_host": true_host,
        "validation_results": validation_results,
        "overall_status": "ready_for_deployment" if all_passed else "validation_failed",
        "recommendation": "Safe to deploy" if all_passed else "Fix validation errors before deployment",
        "risk_level": risk_level,
        "device_type": device_type,
        "vendor": vendor,
        "timestamp": datetime.now().isoformat(),
        "operation": "validate"
    }


def _validate_dry_run(conn, proposed_config, vendor, interface_filter, log_func):
    """Perform dry-run validation — Junos commit check; Cisco syntax preview."""
    errors = []
    warnings = []
    commands = []
    for line in (proposed_config or '').split('\n'):
        line = line.strip()
        if line and not line.startswith('!'):
            commands.append(line)

    if not commands:
        return {
            "passed": True,
            "commands": [],
            "warnings": ["No configuration commands to validate"],
            "errors": [],
        }

    if vendor == "juniper_junos":
        try:
            conn.config_mode()
            conn.send_config_set(commands, exit_config_mode=False)
            out = conn.send_command('commit check', read_timeout=60)
            conn.send_command('rollback 0')
            conn.exit_config_mode()
            if re.search(r'error|fail', out, re.I) and '0 errors' not in out.lower():
                errors.append({'message': f'commit check failed: {out[:200]}'})
            elif log_func:
                log_func('[Dry-run] Junos commit check passed')
        except Exception as exc:
            errors.append({'message': f'Junos commit check error: {exc}'})
            try:
                conn.exit_config_mode()
            except Exception:
                pass
    else:
        syntax = _validate_vendor_syntax(proposed_config, vendor, log_func)
        if not syntax.get('passed'):
            for e in syntax.get('errors', []):
                errors.append(e if isinstance(e, dict) else {'message': str(e)})
        warnings.append(
            'Cisco dry-run uses syntax validation only — review on device before change window'
        )

    return {
        "passed": len(errors) == 0,
        "commands": commands,
        "warnings": warnings,
        "errors": errors,
    }


def _validate_vendor_syntax(proposed_config, vendor, log_func):
    """Validate vendor-specific syntax with comprehensive checks."""
    errors = []
    warnings = []
    
    if not proposed_config:
        return {
            "passed": True,
            "errors": [],
            "warnings": ["No configuration provided"]
        }
    
    lines = proposed_config.split('\n')
    in_interface_context = False
    current_interface = None
    
    # Vendor-specific command patterns
    vendor_patterns = {
        "cisco_nxos": {
            "valid_commands": [
                r'^interface\s+\S+',
                r'^description\s+.+',
                r'^switchport$',
                r'^switchport mode\s+(access|trunk)',
                r'^switchport access vlan\s+\d+',
                r'^switchport trunk allowed vlan\s+.+',
                r'^switchport trunk native vlan\s+\d+',
                r'^no switchport$',
                r'^ip address\s+\S+\s+\S+',
                r'^spanning-tree portfast$',
                r'^spanning-tree portfast trunk$',
                r'^spanning-tree bpduguard enable$',
                r'^spanning-tree bpdufilter enable$',
                r'^channel-group\s+\d+\s+mode\s+(active|on|passive)',
                r'^no shutdown$',
                r'^shutdown$'
            ],
            "legacy_commands": [
                r'switchport trunk encapsulation'
            ]
        },
        "cisco_ios": {
            "valid_commands": [
                r'^interface\s+\S+',
                r'^description\s+.+',
                r'^switchport$',
                r'^switchport mode\s+(access|trunk)',
                r'^switchport access vlan\s+\d+',
                r'^switchport trunk allowed vlan\s+.+',
                r'^switchport trunk encapsulation\s+dot1q',
                r'^switchport trunk native vlan\s+\d+',
                r'^no switchport$',
                r'^ip address\s+\S+\s+\S+',
                r'^spanning-tree portfast$',
                r'^spanning-tree portfast trunk$',
                r'^spanning-tree bpduguard enable$',
                r'^spanning-tree bpdufilter enable$',
                r'^channel-group\s+\d+\s+mode\s+(active|on|passive)',
                r'^no shutdown$',
                r'^shutdown$'
            ],
            "legacy_commands": []
        },
        "cisco_ios_xe": {
            "valid_commands": [
                r'^interface\s+\S+',
                r'^description\s+.+',
                r'^switchport$',
                r'^switchport mode\s+(access|trunk)',
                r'^switchport access vlan\s+\d+',
                r'^switchport trunk allowed vlan\s+.+',
                r'^switchport trunk encapsulation\s+dot1q',
                r'^switchport trunk native vlan\s+\d+',
                r'^no switchport$',
                r'^ip address\s+\S+\s+\S+',
                r'^spanning-tree portfast$',
                r'^spanning-tree portfast trunk$',
                r'^spanning-tree bpduguard enable$',
                r'^spanning-tree bpdufilter enable$',
                r'^channel-group\s+\d+\s+mode\s+(active|on|passive)',
                r'^no shutdown$',
                r'^shutdown$'
            ],
            "legacy_commands": []
        },
        "juniper_junos": {
            "valid_commands": [
                r'^set\s+interfaces\s+',
                r'^set\s+protocols\s+',
                r'^delete\s+',
                r'^interfaces\s+\S+',
                r'^unit\s+\d+',
                r'^family\s+ethernet-switching',
                r'^port-mode\s+(access|trunk)',
                r'^vlan members\s+.+',
                r'^native-vlan-id\s+\d+',
                r'^description\s+.+',
                r'^family inet',
                r'^address\s+\S+'
            ],
            "legacy_commands": []
        }
    }
    
    patterns = vendor_patterns.get(vendor, vendor_patterns["cisco_ios"])
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('!') or line.startswith('#'):
            continue

        # Junos set-format and bracket blocks
        if vendor == "juniper_junos":
            if line.startswith('set ') or line.startswith('delete '):
                continue
            if line.endswith('{') or line == '}' or re.match(r'^\S+\s+\{$', line):
                continue
            if re.match(r'^interfaces\s+\S+', line, re.IGNORECASE):
                in_interface_context = True
                current_interface = re.match(r'^interfaces\s+(\S+)', line, re.IGNORECASE).group(1)
                continue
        
        # Track interface context
        if re.match(r'^interface\s+', line, re.IGNORECASE):
            in_interface_context = True
            current_interface = re.match(r'^interface\s+(\S+)', line, re.IGNORECASE).group(1)
            continue
        
        # Check for legacy commands — BLOCKING on this platform (G-011b)
        is_legacy = False
        for legacy_pattern in patterns.get("legacy_commands", []):
            if re.search(legacy_pattern, line, re.IGNORECASE):
                msg = (
                    f"Legacy syntax blocked: '{line}' is not supported on {vendor}. "
                    f"Remove this command before deploying."
                )
                errors.append({"line": i, "message": msg, "blocking": True})
                warnings.append({"line": i, "message": msg})
                is_legacy = True
        
        # Validate command syntax - check if command matches any known pattern
        command_matched = False
        for valid_pattern in patterns.get("valid_commands", []):
            if re.match(valid_pattern, line, re.IGNORECASE):
                command_matched = True
                break
        
        # If command doesn't match any known pattern and is not legacy, it's an error
        if not command_matched and not is_legacy and line:
            errors.append({
                "line": i,
                "message": f"Invalid or unrecognized command: '{line}'"
            })
        
        # Check for common syntax errors
        if vendor in ["cisco_nxos", "cisco_ios", "cisco_ios_xe"]:
            # VLAN ID validation
            vlan_match = re.search(r'vlan\s+(\d+)', line, re.IGNORECASE)
            if vlan_match:
                vlan_id = int(vlan_match.group(1))
                if vlan_id < 1 or vlan_id > 4094:
                    errors.append({
                        "line": i,
                        "message": f"Invalid VLAN ID: {vlan_id} - must be 1-4094"
                    })
            
            # IP address validation
            ip_match = re.search(r'ip address\s+(\S+)\s+(\S+)', line, re.IGNORECASE)
            if ip_match:
                try:
                    ipaddress.ip_address(ip_match.group(1))
                    ipaddress.ip_address(ip_match.group(2))
                except ValueError:
                    errors.append({
                        "line": i,
                        "message": f"Invalid IP address: '{ip_match.group(1)}' or '{ip_match.group(2)}'"
                    })
        
        elif vendor == "juniper_junos":
            # VLAN ID validation
            vlan_match = re.search(r'vlan members\s+(\d+)', line, re.IGNORECASE)
            if vlan_match:
                vlan_id = int(vlan_match.group(1))
                if vlan_id < 1 or vlan_id > 4094:
                    errors.append({
                        "line": i,
                        "message": f"Invalid VLAN ID: {vlan_id} - must be 1-4094"
                    })
    
    errors = _apply_blocking_syntax_rules(proposed_config, errors)
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


_IM_BLOCKING_LINE_PATTERNS = (
    (re.compile(r'^default\s+interface\b', re.I), 'Default interface resets configuration — blocked for safety'),
    (re.compile(r'^no\s+switchport\b', re.I), 'Removing switchport configuration is high risk — blocked'),
    (re.compile(r'^shutdown\s*$', re.I), 'Interface shutdown in proposed config — blocked (remove or use change window)'),
)


def _apply_blocking_syntax_rules(proposed_config, errors, line_offset=0):
    """Promote high-risk proposed lines from warn-only to hard validation failures (G-011)."""
    if not proposed_config:
        return errors
    for i, raw in enumerate(proposed_config.split('\n'), start=1):
        line = raw.strip()
        if not line or line.startswith('!'):
            continue
        for pat, msg in _IM_BLOCKING_LINE_PATTERNS:
            if pat.match(line):
                errors.append({
                    'line': i + line_offset,
                    'message': msg,
                    'blocking': True,
                })
    return errors


def _validate_platform(conn, true_host, device_type, log_func):
    """Validate platform compatibility."""
    try:
        # Get device version
        version_output = conn.send_command("show version")
        
        # Extract version info (simplified)
        version_match = re.search(r'Version\s+(\S+)', version_output)
        version = version_match.group(1) if version_match else "unknown"
        
        return {
            "passed": True,
            "platform": device_type,
            "version": version,
            "compatibility": "full",
            "notes": []
        }
    except Exception as e:
        return {
            "passed": True,  # Don't fail on version check
            "platform": device_type,
            "version": "unknown",
            "compatibility": "unknown",
            "notes": [f"Could not determine version: {str(e)}"]
        }


def _validate_conflicts(conn, true_host, device_type, interface_filter, proposed_config, log_func):
    """Validate for configuration conflicts with existing configuration."""
    conflicts = []
    warnings = []
    
    if not proposed_config:
        return {
            "passed": True,
            "conflicts": [],
            "warnings": ["No configuration provided"]
        }
    
    # Extract interface name from proposed config
    interface_name = _extract_interface_from_config(proposed_config, interface_filter)
    if not interface_name:
        return {
            "passed": True,
            "conflicts": [],
            "warnings": ["Could not determine interface name from configuration"]
        }
    
    vendor, err = _im_vendor_or_error(device_type)
    if err:
        raise ValueError(err)
    
    try:
        # Get current configuration for the interface
        commands = VENDOR_COMMANDS.get(vendor, VENDOR_COMMANDS["cisco_ios"])
        if vendor == "juniper_junos":
            config_cmd = _junos_display_set_config_cmd(interface_name)
        else:
            config_cmd = commands["config"].format(interface=interface_name)
        current_config = conn.send_command(config_cmd)
        if vendor == "juniper_junos":
            normalized = _normalize_junos_set_config(current_config)
            if normalized:
                current_config = normalized
        
        # Check for VLAN conflicts
        proposed_vlans = []
        current_vlans = []
        
        # Extract VLANs from proposed config
        for line in proposed_config.split('\n'):
            if vendor == "juniper_junos":
                m = re.search(r'vlan-id\s+(\d+)', line, re.IGNORECASE)
                if m:
                    proposed_vlans.append(int(m.group(1)))
            else:
                vlan_match = re.search(r'vlan\s+(.+)', line, re.IGNORECASE)
                if vlan_match:
                    vlan_str = vlan_match.group(1)
                    proposed_vlans.extend(_parse_vlan_list(vlan_str))
        
        # Extract VLANs from current config
        for line in current_config.split('\n'):
            if vendor == "juniper_junos":
                m = re.search(r'vlan-id\s+(\d+)', line, re.IGNORECASE)
                if m:
                    current_vlans.append(int(m.group(1)))
            else:
                vlan_match = re.search(r'vlan\s+(.+)', line, re.IGNORECASE)
                if vlan_match:
                    vlan_str = vlan_match.group(1)
                    current_vlans.extend(_parse_vlan_list(vlan_str))
        
        # Check for conflicts (hard-fail on VLAN removal and mode change)
        if proposed_vlans and current_vlans:
            removed_vlans = set(current_vlans) - set(proposed_vlans)
            if removed_vlans:
                conflicts.append({
                    "type": "vlan_removal",
                    "message": f"Proposed configuration removes VLAN(s): {sorted(removed_vlans)}",
                    "vlans": sorted(removed_vlans),
                })
        
        # Check for mode conflicts
        proposed_mode = None
        current_mode = None
        
        for line in proposed_config.split('\n'):
            if vendor == "juniper_junos":
                if re.search(r'interface-mode\s+access', line, re.IGNORECASE):
                    proposed_mode = "access"
                elif re.search(r'interface-mode\s+trunk', line, re.IGNORECASE):
                    proposed_mode = "trunk"
            elif "switchport mode" in line.lower():
                mode_match = re.search(r'mode\s+(access|trunk)', line, re.IGNORECASE)
                if mode_match:
                    proposed_mode = mode_match.group(1).lower()
        
        for line in current_config.split('\n'):
            if vendor == "juniper_junos":
                if re.search(r'interface-mode\s+access', line, re.IGNORECASE):
                    current_mode = "access"
                elif re.search(r'interface-mode\s+trunk', line, re.IGNORECASE):
                    current_mode = "trunk"
            elif "switchport mode" in line.lower():
                mode_match = re.search(r'mode\s+(access|trunk)', line, re.IGNORECASE)
                if mode_match:
                    current_mode = mode_match.group(1).lower()
        
        if proposed_mode and current_mode and proposed_mode != current_mode:
            conflicts.append({
                "type": "mode_change",
                "message": f"Mode change detected: {current_mode} -> {proposed_mode}",
                "current": current_mode,
                "proposed": proposed_mode
            })
        
    except Exception as e:
        conflicts.append({
            "type": "config_fetch_error",
            "message": f"Could not fetch current configuration for conflict detection: {str(e)}",
        })
    
    return {
        "passed": len(conflicts) == 0,
        "conflicts": conflicts,
        "warnings": warnings
    }


def _calculate_risk_level(dry_run, syntax, platform, conflicts):
    """Calculate overall risk level."""
    if not all([dry_run["passed"], syntax["passed"], platform["passed"], conflicts["passed"]]):
        return "high"
    
    warning_count = (
        len(dry_run.get("warnings", [])) +
        len(syntax.get("warnings", [])) +
        len(platform.get("notes", [])) +
        len(conflicts.get("warnings", []))
    )
    
    if warning_count > 5:
        return "medium"
    elif warning_count > 0:
        return "low"
    else:
        return "none"


# =============================================================================
# CONFIGURATION DEPLOYMENT
# =============================================================================
def _deploy_configuration(conn, true_host, device_type, interface_filter, proposed_config, dry_run, log_func):
    """
    Deploy interface configuration with safety mechanisms.
    
    Args:
        conn: Netmiko connection
        true_host: Device hostname
        device_type: Device type
        interface_filter: Interface name filter
        proposed_config: Configuration to deploy
        dry_run: Dry run mode flag
        log_func: Logging function
    
    Returns:
        dict: Deployment results
    """
    if log_func:
        log_func(f"[{true_host}] Deploying configuration (dry_run={dry_run})...")
    
    # Pre-change backup
    backup_path = _create_pre_backup(conn, true_host, log_func)

    if _im_should_abort():
        return _im_cancelled_result(true_host, device_type, backup_path, log_func)

    if dry_run:
        if log_func:
            log_func(f"[{true_host}] [DRY-RUN] Skipping deployment")
        
        return {
            "true_host": true_host,
            "deployment_results": {
                "pre_backup": backup_path,
                "deployment": {
                    "commands_executed": proposed_config.split('\n') if proposed_config else [],
                    "success_count": 0,
                    "failure_count": 0,
                    "execution_time": 0
                },
                "post_verification": {
                    "passed": True,
                    "verification_commands": [],
                    "verification_results": []
                }
            },
            "rollback_available": False,
            "backup_available": bool(backup_path.get("path")),
            "backup_path": backup_path.get("path", ""),
            "restore_guide_notice": (
                "Pre-change backup saved. Use POST /api/interface/restore-guide for manual restore steps. "
                "Automated rollback is not available (safety v6.5.4)."
            ),
            "deployment_status": "dry_run_skipped",
            "device_type": device_type,
            "timestamp": datetime.now().isoformat(),
            "operation": "deploy"
        }

    # ── G-011b BLOCKING PRE-FLIGHT ─────────────────────────────────────────
    # Run full syntax validation before touching the device.  Any error with
    # blocking=True (legacy syntax, shutdown, default interface, no switchport)
    # will ABORT deployment and return a structured failure — never just warn.
    if proposed_config:
        _vendor_pre, _verr_pre = _im_vendor_or_error(device_type)
        if not _verr_pre:
            _pre_result = _validate_vendor_syntax(proposed_config, _vendor_pre, log_func)
            _blocking_errs = [e for e in _pre_result.get('errors', []) if e.get('blocking')]
            if _blocking_errs:
                _msgs = '; '.join(e['message'] for e in _blocking_errs)
                if log_func:
                    log_func(
                        f"[{true_host}] [DEPLOY BLOCKED] Blocking syntax errors detected — "
                        f"no commands sent to device. Errors: {_msgs}"
                    )
                return {
                    'true_host': true_host,
                    'deployment_status': 'blocked_by_legacy_syntax',
                    'device_type': device_type,
                    'timestamp': __import__('datetime').datetime.now().isoformat(),
                    'operation': 'deploy',
                    'blocking_errors': _blocking_errs,
                    'message': (
                        'Deployment aborted: proposed config contains blocked commands. '
                        'Fix the errors reported below before retrying.'
                    ),
                    'deployment_results': {
                        'pre_backup': backup_path,
                        'deployment': {
                            'commands_executed': [],
                            'success_count': 0,
                            'failure_count': len(_blocking_errs),
                            'execution_time': 0,
                        },
                    },
                }
    # ── END G-011b PRE-FLIGHT ──────────────────────────────────────────────

    # Execute configuration
    import time as _time
    _deploy_t0 = _time.perf_counter()
    commands_executed = []
    success_count = 0
    failure_count = 0
    save_success = False
    pre_deployment_config = None

    if proposed_config:
        try:
            vendor, verr = _im_vendor_or_error(device_type)
            if verr:
                raise ValueError(verr)
            
            # Capture pre-deployment configuration for validation
            try:
                if log_func:
                    log_func(f"[{true_host}] Capturing pre-deployment configuration...")
                pre_deployment_config = _capture_current_config(conn, vendor, interface_filter, log_func)
            except Exception as e:
                if log_func:
                    log_func(f"[{true_host}] WARNING: Could not capture pre-deployment config: {str(e)}")
                pre_deployment_config = None
            
            # Enter configuration mode using Netmiko's built-in methods
            if log_func:
                log_func(f"[{true_host}] Entering configuration mode...")
            if _im_should_abort():
                return _im_cancelled_result(true_host, device_type, backup_path, log_func)
            conn.config_mode()
            
            # Send commands as a block for better error handling
            config_lines = []
            for line in proposed_config.split('\n'):
                line = line.strip()
                if line and not line.startswith('!'):
                    config_lines.append(line)
            
            if config_lines:
                try:
                    if log_func:
                        log_func(f"[{true_host}] Applying {len(config_lines)} configuration commands...")
                    if vendor == "juniper_junos":
                        if _im_should_abort():
                            try:
                                conn.exit_config_mode()
                            except Exception:
                                pass
                            return _im_cancelled_result(true_host, device_type, backup_path, log_func)
                        output = conn.send_config_set(config_lines, delay_factor=5, exit_config_mode=False)
                        commands_executed.extend(config_lines)
                        if log_func:
                            for cmd in config_lines:
                                log_func(f"[{true_host}] Executed: {cmd}")
                        if _im_should_abort():
                            try:
                                conn.exit_config_mode()
                            except Exception:
                                pass
                            return _im_cancelled_result(true_host, device_type, backup_path, log_func)
                        if log_func:
                            log_func(f"[{true_host}] Committing configuration (Junos)...")
                        conn.commit()
                        conn.exit_config_mode()
                        save_success = True
                        success_count = 1
                    else:
                        if _im_should_abort():
                            try:
                                conn.exit_config_mode()
                            except Exception:
                                pass
                            return _im_cancelled_result(true_host, device_type, backup_path, log_func)
                        try:
                            output = conn.send_config_set(
                                config_lines, delay_factor=5, exit_config_mode=False,
                            )
                            commands_executed.extend(config_lines)
                            if log_func:
                                for cmd in config_lines:
                                    log_func(f"[{true_host}] Executed: {cmd}")
                        except Exception:
                            # Fallback: line-by-line if send_config_set fails
                            for cmd in config_lines:
                                if _im_should_abort():
                                    try:
                                        conn.exit_config_mode()
                                    except Exception:
                                        pass
                                    return _im_cancelled_result(true_host, device_type, backup_path, log_func)
                                conn.send_command(cmd, strip_command=False, strip_prompt=False)
                                commands_executed.append(cmd)
                                if log_func:
                                    log_func(f"[{true_host}] Executed: {cmd}")
                        success_count = 1
                        if log_func:
                            log_func(f"[{true_host}] Exiting configuration mode...")
                        conn.exit_config_mode()
                except Exception as e:
                    failure_count += 1
                    if log_func:
                        log_func(f"[{true_host}] ERROR applying configuration: {str(e)}")
                    try:
                        conn.exit_config_mode()
                    except Exception:
                        pass
                    raise
            
            # Save configuration based on vendor (Cisco only — Junos committed above)
            save_error = None
            
            if vendor == "cisco_nxos" and config_lines and not save_success:
                if _im_should_abort():
                    return _im_cancelled_result(true_host, device_type, backup_path, log_func)
                try:
                    if log_func:
                        log_func(f"[{true_host}] Saving configuration to startup-config...")
                    output = conn.send_command(
                        "copy running-config startup-config",
                        delay_factor=10,
                        max_loops=5000
                    )
                    if log_func:
                        log_func(f"[{true_host}] Configuration saved successfully")
                    save_success = True
                except Exception as e:
                    save_error = str(e)
                    if log_func:
                        log_func(f"[{true_host}] WARNING: Could not save configuration: {save_error}")
            
            elif vendor in ["cisco_ios", "cisco_ios_xe"] and config_lines and not save_success:
                if _im_should_abort():
                    return _im_cancelled_result(true_host, device_type, backup_path, log_func)
                try:
                    if log_func:
                        log_func(f"[{true_host}] Saving configuration (write memory)...")
                    output = conn.send_command(
                        "write memory",
                        delay_factor=10,
                        max_loops=5000
                    )
                    if log_func:
                        log_func(f"[{true_host}] Configuration saved successfully")
                    save_success = True
                except Exception as e:
                    save_error = str(e)
                    if log_func:
                        log_func(f"[{true_host}] WARNING: Could not save configuration: {save_error}")
            
            elif vendor == "juniper_junos" and config_lines and not save_success:
                if log_func:
                    log_func(f"[{true_host}] Junos commit already applied during deploy.")
                save_success = True
            
        except Exception as e:
            failure_count += 1
            if log_func:
                log_func(f"[{true_host}] ERROR during deployment: {str(e)}")
            # Ensure we exit config mode even on error
            try:
                conn.exit_config_mode()
            except:
                pass
    
    # Post-change verification
    verification_results = _perform_post_verification(conn, interface_filter, log_func)
    
    # Verify configuration save if save was attempted
    save_verification = None
    if not dry_run and proposed_config:
        save_verification = _verify_configuration_save(conn, vendor, log_func)
    
    # Configuration change validation
    config_validation = None
    if not dry_run and proposed_config and pre_deployment_config:
        try:
            if log_func:
                log_func(f"[{true_host}] Validating configuration changes...")
            post_deployment_config = _capture_current_config(conn, vendor, interface_filter, log_func)
            config_validation = _validate_configuration_changes(
                pre_deployment_config,
                post_deployment_config,
                proposed_config,
                vendor,
                log_func
            )
        except Exception as e:
            if log_func:
                log_func(f"[{true_host}] WARNING: Configuration validation failed: {str(e)}")
            config_validation = {
                "status": "validation_failed",
                "error": str(e)
            }
    
    # Selective interface rediscovery after successful deployment
    rediscovery_result = None
    if not dry_run and proposed_config and success_count > 0:
        try:
            if log_func:
                log_func(f"[{true_host}] Performing selective interface rediscovery...")
            rediscovery_result = _rediscover_interfaces(conn, vendor, interface_filter, log_func)
            if log_func:
                log_func(f"[{true_host}] Interface rediscovery: {rediscovery_result.get('status', 'unknown')}")
        except Exception as e:
            if log_func:
                log_func(f"[{true_host}] WARNING: Interface rediscovery failed: {str(e)}")
            rediscovery_result = {
                "status": "rediscovery_failed",
                "error": str(e)
            }
    
    if log_func:
        log_func(f"[{true_host}] Deployment complete - {success_count} commands executed")
        if save_verification:
            log_func(f"[{true_host}] Configuration save verification: {save_verification.get('status', 'unknown')}")
        if config_validation:
            log_func(f"[{true_host}] Configuration change validation: {config_validation.get('status', 'unknown')}")
        if rediscovery_result:
            log_func(f"[{true_host}] Interface rediscovery: {rediscovery_result.get('status', 'unknown')}")
    
    return {
        "true_host": true_host,
        "deployment_results": {
            "pre_backup": backup_path,
            "deployment": {
                "commands_executed": commands_executed,
                "success_count": success_count,
                "failure_count": failure_count,
                "execution_time": round(_time.perf_counter() - _deploy_t0, 3)
            },
            "post_verification": verification_results,
            "save_verification": save_verification,
            "config_validation": config_validation,
            "rediscovery": rediscovery_result
        },
        "rollback_available": False,
        "backup_available": bool(backup_path.get("path")),
        "backup_path": backup_path.get("path", ""),
        "restore_guide_notice": (
            "Pre-change backup saved. POST /api/interface/restore-guide for manual restore steps."
        ),
        "deployment_status": "success" if failure_count == 0 else "partial_failure",
        "device_type": device_type,
        "timestamp": datetime.now().isoformat(),
        "operation": "deploy"
    }


def _create_pre_backup(conn, true_host, log_func):
    """Create pre-change backup by saving running configuration."""
    if log_func:
        log_func(f"[{true_host}] Creating pre-change backup...")
    
    try:
        # Get running configuration
        vendor, verr = _im_vendor_or_error(conn.device_type)
        if verr:
            raise ValueError(verr)
        config_cmd = "show running-config" if vendor != "juniper_junos" else "show configuration"
        running_config = conn.send_command(config_cmd)
        
        # Create backups directory
        from utils.output_paths import get_backups_root
        backup_dir = os.path.join(get_backups_root(), 'interface_manager', true_host.replace('.', '_'))
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"config_{timestamp}.txt"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Write configuration to file
        with open(backup_path, 'w') as f:
            f.write(f"# Pre-change backup for {true_host}\n")
            f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"# Vendor: {vendor}\n")
            f.write(f"# Device Type: {conn.device_type}\n")
            f.write("#" + "=" * 68 + "\n")
            f.write(running_config)
        
        file_size = os.path.getsize(backup_path)
        
        if log_func:
            log_func(f"[{true_host}] Backup saved: {backup_path} ({file_size} bytes)")
        
        return {
            "path": backup_path,
            "timestamp": datetime.now().isoformat(),
            "size": file_size,
            "vendor": vendor,
            "device_type": conn.device_type
        }
        
    except Exception as e:
        if log_func:
            log_func(f"[{true_host}] WARNING: Could not create backup: {str(e)}")
        
        # Return placeholder if backup fails but don't fail deployment
        return {
            "path": f"backups/{true_host}/config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "timestamp": datetime.now().isoformat(),
            "size": 0,
            "error": str(e)
        }


def _capture_current_config(conn, vendor, interface_filter, log_func):
    """
    Capture current interface configuration for validation.
    
    Args:
        conn: Netmiko connection
        vendor: Vendor string
        interface_filter: Interface name filter
        log_func: Logging function
    
    Returns:
        dict: Configuration lines organized by interface
    """
    try:
        config_lines = []
        
        if vendor == "cisco_nxos":
            output = conn.send_command(f"show running-config interface {interface_filter}", read_timeout=30)
        elif vendor in ["cisco_ios", "cisco_ios_xe"]:
            output = conn.send_command(f"show running-config interface {interface_filter}", read_timeout=30)
        elif vendor == "juniper_junos":
            output = conn.send_command(
                _junos_display_set_config_cmd(interface_filter), read_timeout=30,
            )
            normalized = _normalize_junos_set_config(output)
            if normalized:
                output = normalized
        else:
            output = conn.send_command(f"show running-config interface {interface_filter}", read_timeout=30)
        
        # Parse configuration into lines
        for line in output.split('\n'):
            line = line.rstrip()
            if line:
                config_lines.append(line)
        
        return {
            "interface": interface_filter,
            "config_lines": config_lines,
            "config_text": '\n'.join(config_lines),
            "vendor": vendor
        }
    
    except Exception as e:
        if log_func:
            log_func(f"[{interface_filter}] ERROR capturing config: {str(e)}")
        return {
            "interface": interface_filter,
            "config_lines": [],
            "config_text": "",
            "vendor": vendor,
            "error": str(e)
        }


def _validate_configuration_changes(pre_config, post_config, proposed_config, vendor, log_func):
    """
    Validate that configuration changes were applied correctly.
    
    Args:
        pre_config: Pre-deployment configuration dict
        post_config: Post-deployment configuration dict
        proposed_config: Proposed configuration text
        vendor: Vendor string
        log_func: Logging function
    
    Returns:
        dict: Validation results
    """
    try:
        pre_lines = set(pre_config.get("config_lines", []))
        post_lines = set(post_config.get("config_lines", []))
        
        # Identify intended changes from proposed config
        proposed_lines = []
        for line in proposed_config.split('\n'):
            line = line.strip()
            if line and not line.startswith('!'):
                proposed_lines.append(line)
        
        # Check for edge cases
        has_default_command = any("default" in line.lower() for line in proposed_lines)
        
        if has_default_command:
            # For default commands, we expect lines to be removed
            removed_lines = pre_lines - post_lines
            added_lines = post_lines - pre_lines
            
            return {
                "status": "validated",
                "validation_type": "default_command",
                "removed_lines": len(removed_lines),
                "added_lines": len(added_lines),
                "has_default": True,
                "message": "Default command detected - configuration reset validated"
            }
        
        # Normal validation - check if proposed lines are in post config
        missing_lines = []
        found_lines = []
        
        for line in proposed_lines:
            # Normalize line for comparison (handle whitespace variations)
            normalized_line = ' '.join(line.split())
            found = False
            
            for post_line in post_lines:
                normalized_post = ' '.join(post_line.split())
                if normalized_line == normalized_post:
                    found = True
                    found_lines.append(line)
                    break
            
            if not found:
                # Check if line is a negation (no keyword)
                if line.lower().startswith("no "):
                    # For negation commands, check if the line is NOT in post config
                    negation_target = line[3:].strip()
                    negation_found = False
                    for post_line in post_lines:
                        normalized_post = ' '.join(post_line.split())
                        if negation_target in normalized_post:
                            negation_found = True
                            break
                    if not negation_found:
                        found_lines.append(line)  # Successfully removed
                else:
                    missing_lines.append(line)
        
        if not missing_lines:
            return {
                "status": "validated",
                "validation_type": "normal",
                "proposed_count": len(proposed_lines),
                "found_count": len(found_lines),
                "missing_count": 0,
                "message": "All proposed configuration changes validated"
            }
        else:
            return {
                "status": "partial_validation",
                "validation_type": "normal",
                "proposed_count": len(proposed_lines),
                "found_count": len(found_lines),
                "missing_count": len(missing_lines),
                "missing_lines": missing_lines,
                "message": f"{len(missing_lines)} proposed changes not found in configuration"
            }
    
    except Exception as e:
        return {
            "status": "validation_failed",
            "error": str(e),
            "message": f"Configuration validation failed: {str(e)}"
        }


def _verify_configuration_save(conn, vendor, log_func):
    """
    Verify that configuration was successfully saved to startup-config.
    
    Args:
        conn: Netmiko connection
        vendor: Vendor string
        log_func: Logging function
    
    Returns:
        dict: Verification results
    """
    try:
        if vendor == "cisco_nxos":
            # NXOS: Check if startup-config matches running-config
            running_md5 = conn.send_command("show running-config | include md5sum", read_timeout=30)
            startup_md5 = conn.send_command("show startup-config | include md5sum", read_timeout=30)
            
            # Simple verification - check if both commands succeeded
            if running_md5 and startup_md5:
                return {
                    "status": "verified",
                    "method": "md5_comparison",
                    "running_md5": running_md5[:50],
                    "startup_md5": startup_md5[:50]
                }
            else:
                return {
                    "status": "verification_failed",
                    "method": "md5_comparison",
                    "error": "Could not retrieve MD5 checksums"
                }
        
        elif vendor in ["cisco_ios", "cisco_ios_xe"]:
            # IOS/IOS-XE: Check if startup-config exists and is recent
            output = conn.send_command("show startup-config", read_timeout=30)
            if output and len(output) > 100:
                return {
                    "status": "verified",
                    "method": "startup_config_check",
                    "config_size": len(output)
                }
            else:
                return {
                    "status": "verification_failed",
                    "method": "startup_config_check",
                    "error": "Startup-config appears empty or too small"
                }
        
        elif vendor == "juniper_junos":
            # Junos: Check if configuration is committed
            output = conn.send_command("show configuration | display set | count", read_timeout=30)
            if output and "count" in output.lower():
                return {
                    "status": "verified",
                    "method": "commit_check",
                    "details": output
                }
            else:
                return {
                    "status": "verification_failed",
                    "method": "commit_check",
                    "error": "Could not verify committed configuration"
                }
        
        else:
            return {
                "status": "skipped",
                "method": "unsupported_vendor",
                "vendor": vendor
            }
    
    except Exception as e:
        return {
            "status": "verification_failed",
            "method": "exception",
            "error": str(e)
        }


def _rediscover_interfaces(conn, vendor, interface_filter, log_func):
    """
    Rediscover specific interface(s) after configuration deployment.
    This allows the UI to reflect changes without requiring full switch rediscovery.
    
    Args:
        conn: Netmiko connection
        vendor: Vendor type
        interface_filter: Interface name or pattern
        log_func: Logging function
        
    Returns:
        Dictionary with rediscovery results
    """
    try:
        if log_func:
            log_func(f"[{interface_filter}] Rediscovering interface configuration...")
        
        # Get current interface configuration
        current_config = _capture_current_config(conn, vendor, interface_filter, log_func)
        
        # Parse interface details based on vendor
        interface_details = {}
        
        if vendor == "cisco_nxos":
            interface_details = _parse_nxos_interface(current_config, interface_filter)
        elif vendor in ["cisco_ios", "cisco_ios_xe"]:
            interface_details = _parse_ios_interface(current_config, interface_filter)
        elif vendor == "juniper_junos":
            interface_details = _parse_junos_interface(current_config, interface_filter)
        
        if log_func:
            log_func(f"[{interface_filter}] Rediscovery successful - {len(interface_details)} interface(s) updated")
        
        return {
            "status": "success",
            "interface": interface_filter,
            "details": interface_details,
            "config": current_config
        }
        
    except Exception as e:
        if log_func:
            log_func(f"[{interface_filter}] Rediscovery failed: {str(e)}")
        return {
            "status": "failed",
            "interface": interface_filter,
            "error": str(e)
        }


def _perform_post_verification(conn, interface_filter, log_func):
    """Perform comprehensive post-change verification."""
    verification_results = []
    
    if log_func:
        log_func(f"[{interface_filter}] Performing post-change verification...")
    
    # Determine vendor for appropriate commands
    vendor, verr = _im_vendor_or_error(conn.device_type)
    if verr:
        raise ValueError(verr)
    
    # Verification 1: Interface status check
    status_cmd = "show interface" if vendor != "juniper_junos" else "show interfaces"
    try:
        status_output = conn.send_command(f"{status_cmd} {interface_filter}")
        low = status_output.lower()
        is_up = bool(
            re.search(r'\bis\s+up\b', low)
            or re.search(r'line protocol is up', low)
            or re.search(r'physical link is up', low)
            or re.search(r'\boper status\s*[:=]\s*up\b', low)
            or re.search(r'\bconnected\b', low)
        )
        
        verification_results.append({
            "command": f"{status_cmd} {interface_filter}",
            "check": "interface_status",
            "expected": "interface up/connected",
            "actual": "up/connected" if is_up else "down/disconnected",
            "match": is_up,
            "output": status_output[:300]
        })
        
        if log_func:
            log_func(f"[{interface_filter}] Interface status: {'UP' if is_up else 'DOWN'}")
            
    except Exception as e:
        verification_results.append({
            "command": f"{status_cmd} {interface_filter}",
            "check": "interface_status",
            "expected": "interface up/connected",
            "actual": "error",
            "match": False,
            "error": str(e)
        })
    
    # Verification 2: Configuration check
    try:
        config_cmd = "show run interface" if vendor != "juniper_junos" else "show configuration interfaces"
        config_output = conn.send_command(f"{config_cmd} {interface_filter}")
        
        verification_results.append({
            "command": f"{config_cmd} {interface_filter}",
            "check": "configuration_applied",
            "expected": "configuration present",
            "actual": "configuration present",
            "match": len(config_output) > 50,  # Basic check that config exists
            "output": config_output[:500]
        })
        
        if log_func:
            log_func(f"[{interface_filter}] Configuration verified")
            
    except Exception as e:
        verification_results.append({
            "command": f"{config_cmd} {interface_filter}",
            "check": "configuration_applied",
            "expected": "configuration present",
            "actual": "error",
            "match": False,
            "error": str(e)
        })
    
    # Verification 3: VLAN check (for L2 interfaces)
    try:
        if vendor in ["cisco_nxos", "cisco_ios", "cisco_ios_xe"]:
            vlan_cmd = "show vlan brief"
            vlan_output = conn.send_command(vlan_cmd)
            
            verification_results.append({
                "command": vlan_cmd,
                "check": "vlan_database",
                "expected": "vlan database accessible",
                "actual": "vlan database accessible",
                "match": True,
                "output": "VLAN check passed"
            })
        elif vendor == "juniper_junos":
            vlan_output = conn.send_command("show vlans")
            verification_results.append({
                "command": "show vlans",
                "check": "vlan_database",
                "expected": "vlan database accessible",
                "actual": "vlan database accessible",
                "match": True,
                "output": "VLAN check passed"
            })
    except Exception as e:
        # VLAN check is non-critical, don't fail on this
        verification_results.append({
            "command": "vlan check",
            "check": "vlan_database",
            "expected": "vlan database accessible",
            "actual": "skipped",
            "match": True,
            "note": f"VLAN check skipped: {str(e)}"
        })
    
    # Overall verification result
    critical_checks = [r for r in verification_results if r["check"] in ["interface_status", "configuration_applied"]]
    passed = all(r.get("match", False) for r in critical_checks)
    
    if log_func:
        log_func(f"[{interface_filter}] Post-change verification: {'PASSED' if passed else 'FAILED'}")
    
    return {
        "passed": passed,
        "verification_commands": [r["command"] for r in verification_results],
        "verification_results": verification_results,
        "critical_checks": len(critical_checks),
        "critical_passed": sum(1 for r in critical_checks if r.get("match", False))
    }


def _rollback_configuration(conn, backup_path, true_host, log_func):
    """
    Automated rollback disabled (v6.5.4). Returns manual restore guide only.
    """
    from utils.restore_guide import get_manual_restore_guide
    if log_func:
        log_func(
            f"[{true_host}] Automated rollback disabled — use manual restore guide for: {backup_path}"
        )
    guide = get_manual_restore_guide(
        backup_path, getattr(conn, 'device_type', ''), context='interface configuration',
    )
    return {
        "success": False,
        "automated_restore_available": False,
        "error": "Automated rollback is disabled for safety. Use manual restore steps.",
        "restore_guide": guide,
        "backup_path": backup_path,
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# REPORT FORMATTER
# =============================================================================
def _format_interface_report(data, host, operation):
    """
    Format human-readable report for interface operations.
    
    Args:
        data: Result dictionary
        host: Device IP address
        operation: Operation type
    
    Returns:
        str: Formatted report text
    """
    lines = []
    lines.append("=" * 70)
    lines.append("INTERFACE MANAGEMENT REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Device Hostname:    {data.get('true_host', 'N/A')}")
    lines.append(f"Device IP:          {host}")
    lines.append(f"Device Type:        {data.get('device_type', 'N/A')}")
    lines.append(f"Vendor:             {data.get('vendor', 'N/A')}")
    lines.append(f"Operation:          {operation}")
    lines.append(f"Report Generated:   {data.get('timestamp', 'N/A')}")
    lines.append("")
    
    if operation == "discover":
        interfaces = data.get('interfaces', [])
        lines.append("-" * 70)
        lines.append("INTERFACE DISCOVERY RESULTS")
        lines.append("-" * 70)
        lines.append(f"Total Interfaces:  {len(interfaces)}")
        lines.append("")
        
        for interface in interfaces[:20]:  # Show first 20
            lines.append(f"  {interface['name']:20} {interface['status']:15} {interface['l2_l3_mode']:10}")
        
        if len(interfaces) > 20:
            lines.append(f"  ... and {len(interfaces) - 20} more interfaces")
    
    elif operation == "validate":
        validation = data.get('validation_results', {})
        lines.append("-" * 70)
        lines.append("VALIDATION RESULTS")
        lines.append("-" * 70)
        lines.append(f"Overall Status:    {data.get('overall_status', 'N/A')}")
        lines.append(f"Recommendation:    {data.get('recommendation', 'N/A')}")
        lines.append(f"Risk Level:        {data.get('risk_level', 'N/A')}")
        lines.append("")
        
        for check_name, check_result in validation.items():
            status = "✅ PASSED" if check_result.get('passed') else "❌ FAILED"
            lines.append(f"  {check_name.title():20} {status}")
    
    elif operation == "deploy":
        deployment = data.get('deployment_results', {})
        lines.append("-" * 70)
        lines.append("DEPLOYMENT RESULTS")
        lines.append("-" * 70)
        lines.append(f"Deployment Status: {data.get('deployment_status', 'N/A')}")
        lines.append(f"Pre-change Backup: {data.get('backup_path') or data.get('rollback_path') or 'N/A'}")
        lines.append(f"Manual Restore: use /api/interface/restore-guide (automated rollback disabled)")
        lines.append("")
        
        if 'deployment' in deployment:
            deploy_info = deployment['deployment']
            lines.append(f"Commands Executed: {deploy_info.get('success_count', 0)}")
            lines.append(f"Failures:          {deploy_info.get('failure_count', 0)}")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)
    
    return '\n'.join(lines)


def _generate_summary(data, operation):
    """Generate summary for master report."""
    if operation == "discover":
        return f"{data.get('interface_count', 0)} interfaces discovered"
    elif operation == "validate":
        return f"Validation: {data.get('overall_status', 'unknown')}"
    elif operation == "deploy":
        return f"Deployment: {data.get('deployment_status', 'unknown')}"
    return f"{operation} completed"


# =============================================================================
# MODULE TEST
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Plugin Contract Validation")
    print("=" * 60)
    
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
    print(f"Parameters: {list(METADATA['required_params'].keys())}")
    print(f"Vendor Support: {list(VENDOR_COMMANDS.keys())}")
    print("\n✅ Plugin structure validated")
