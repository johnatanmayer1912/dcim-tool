"""
modules/plugins/interface_vlan_reporter.py
----------------------------------------
Interface VLAN Reporter Plugin for Network Swiss Tool Pro v7.0

Connects to switches and reports interface VLAN configurations in beautiful
TXT and HTML formats. Shows switch hostname, interface, configured VLAN,
trunk allowed VLANs, and other interface options.

VERSION HISTORY:
- v1.3.0 (2026-07-22): Port descriptions & folder structure
  - Added interface description parsing (Cisco IOS/IOS-XE/NX-OS/Juniper)
  - Port descriptions now display in TXT and HTML reports
  - Updated to use output_paths for consistent folder structure
  - All reports now go to outputs/plugins/<date>/<timestamp>/
  - Consolidated HTML report now includes links to individual device reports
  - Summary table shows HTML/TXT links for each device
  - Device detail sections have prominent report open buttons
- v1.2.0 (2026-07-22): Enhanced debugging & logging
  - Added extensive logging for report generation steps
  - Added content length logging for TXT/HTML reports
  - Added traceback logging for report generation failures
  - Added path derivation logging for HTML reports
  - Enhanced error reporting with full stack traces
- v1.1.0 (2026-07-22): Enhanced parsing & multi-device support
  - Enhanced VLAN parsing for IOS/IOS-XE/NX-OS with comprehensive patterns
  - Added dynamic mode detection (dynamic auto/desirable)
  - Added port-security details (maximum count, violation type)
  - Added BPDU filter detection
  - Added STP guard types (loop, root, none)
  - Added STP link-type detection
  - Special value handling for allowed VLANs (all, none)
  - Multi-device HTML report with expandable sections
  - Defensive programming for NoneType handling
  - Fixed TXT report generation with direct file write
  - Removed security-violating imports (os-dependent modules)
  - Inline HTML/TXT generation to avoid dependencies
- v1.0.0 (2026-07-22): Initial release
  - Interface VLAN discovery for all supported vendors
  - Access VLAN detection
  - Trunk allowed VLANs detection
  - Beautiful TXT and HTML report generation
  - Multi-vendor support (Cisco IOS, IOS-XE, NX-OS, Juniper JunOS)

RELEASE NOTES:
v1.3.0:
  - Features: Port description parsing, unified folder structure, report links
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Ready for testing
v1.2.0:
  - Features: Enhanced debugging, extensive logging, error tracebacks
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Completed
v1.1.0:
  - Features: Enhanced VLAN parsing, multi-device reports, defensive error handling
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Completed
v1.0.0:
  - Features: Interface VLAN reporting, access/trunk detection, multi-vendor support
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Completed

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
    "plugin_id": "interface_vlan_reporter",
    "display_name": "Interface VLAN Reporter",
    "version": "1.3.0",
    "author": "Network Engineering Team",
    "category": "Reporting",
    "description": "Connects to switches and reports interface VLAN configurations in beautiful TXT and HTML formats. Shows switch hostname, interface, configured VLAN, trunk allowed VLANs, and other interface options. Supports multi-device unified reporting.",
    "min_platform_version": "7.0.0",
    
    "changelog": [
        {
            "version": "1.3.0",
            "date": "2026-07-22",
            "changes": [
                "Added interface description parsing (Cisco IOS/IOS-XE/NX-OS/Juniper)",
                "Port descriptions now display in TXT and HTML reports",
                "Updated to use output_paths for consistent folder structure",
                "All reports now go to outputs/plugins/<date>/<timestamp>/",
                "Consolidated HTML report now includes links to individual device reports",
                "Summary table shows HTML/TXT links for each device",
                "Device detail sections have prominent report open buttons"
            ]
        },
        {
            "version": "1.2.0",
            "date": "2026-07-22",
            "changes": [
                "Added extensive logging for report generation steps",
                "Added content length logging for TXT/HTML reports",
                "Added traceback logging for report generation failures",
                "Added path derivation logging for HTML reports",
                "Enhanced error reporting with full stack traces"
            ]
        },
        {
            "version": "1.1.0",
            "date": "2026-07-22",
            "changes": [
                "Enhanced VLAN parsing for IOS/IOS-XE/NX-OS with comprehensive patterns",
                "Added dynamic mode detection (dynamic auto/desirable)",
                "Added port-security details (maximum count, violation type)",
                "Added BPDU filter detection",
                "Added STP guard types (loop, root, none)",
                "Added STP link-type detection",
                "Special value handling for allowed VLANs (all, none)",
                "Multi-device HTML report with expandable sections",
                "Defensive programming for NoneType handling",
                "Fixed TXT report generation with direct file write",
                "Removed security-violating imports (os-dependent modules)",
                "Inline HTML/TXT generation to avoid dependencies"
            ]
        },
        {
            "version": "1.0.0",
            "date": "2026-07-22",
            "changes": "Initial release with interface VLAN reporting, access/trunk detection, multi-vendor support",
            "author": "Network Engineering Team",
            "qa_status": "completed"
        }
    ],
    
    "documentation": {
        "readme": "docs/plugins/interface_vlan_reporter/README.md",
        "release_notes": "docs/plugins/interface_vlan_reporter/RELEASE_NOTES.md",
        "prompt": "docs/plugins/interface_vlan_reporter/PROMPT.md",
        "changelog": "docs/plugins/interface_vlan_reporter/CHANGELOG.md",
        "test_results": "docs/plugins/interface_vlan_reporter/TEST_RESULTS.md",
        "compatibility": "docs/plugins/interface_vlan_reporter/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/interface_vlan_reporter/versions/",
        "current_version_folder": "docs/plugins/interface_vlan_reporter/versions/v1.0.0/"
    },
    
    "version_archive": {
        "v1.0.0": {
            "file": "docs/plugins/interface_vlan_reporter/versions/v1.0.0/interface_vlan_reporter_v1.0.0.py",
            "manifest": "docs/plugins/interface_vlan_reporter/versions/v1.0.0/manifest.json",
            "date": "2026-07-22",
            "status": "current"
        }
    },
    
    "required_params": {
        "interface_filter": {
            "type": "string",
            "label": "Interface Filter (Optional)",
            "placeholder": "e.g. Ethernet1/1 or leave empty for all",
            "required": False,
            "description": "Filter to specific interface name (optional)"
        },
        "include_shutdown": {
            "type": "checkbox",
            "label": "Include Shutdown Interfaces",
            "default": False,
            "description": "Include interfaces that are administratively shutdown"
        },
        "output_format": {
            "type": "dropdown",
            "label": "Output Format",
            "options": ["both", "txt", "html"],
            "default": "both",
            "required": True,
            "description": "Output format for the report"
        }
    },
    
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": False
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
    append_to_master_report,
    write_text_file
)
from utils.output_paths import (
    prepare_run_output,
    path_in_run,
    slugify,
    CAT_PLUGINS
)
from datetime import datetime
import html
import json
import re


def _html_esc(value):
    """Escape untrusted device/CLI strings for HTML reports."""
    return html.escape(str(value if value is not None else ''), quote=True)


# =============================================================================
# VENDOR-SPECIFIC COMMANDS
# =============================================================================
VENDOR_COMMANDS = {
    "cisco_nxos": {
        "interfaces": "show interface",
        "config": "show run interface {interface}",
        "vlan": "show vlan brief"
    },
    "cisco_ios": {
        "interfaces": "show interface",
        "config": "show run interface {interface}",
        "vlan": "show vlan brief"
    },
    "cisco_ios_xe": {
        "interfaces": "show interface",
        "config": "show run interface {interface}",
        "vlan": "show vlan brief"
    },
    "juniper_junos": {
        "interfaces": "show interfaces",
        "config": "show configuration interfaces {interface} | display set",
        "vlan": "show vlans"
    }
}


def _determine_vendor(device_type):
    """Determine vendor from device type string."""
    device_type_lower = (device_type or "").lower()
    
    if "nxos" in device_type_lower or "n9k" in device_type_lower:
        return "cisco_nxos"
    if "ios_xe" in device_type_lower or "ios-xe" in device_type_lower or "iosxe" in device_type_lower:
        return "cisco_ios_xe"
    if "juniper" in device_type_lower or "junos" in device_type_lower:
        return "juniper_junos"
    if "ios" in device_type_lower:
        return "cisco_ios"
    return "cisco_ios"  # Default


def _parse_interface_description(config_output):
    """Parse interface description from configuration output.
    
    Handles Cisco IOS, IOS-XE, NX-OS, and Juniper JunOS formats.
    """
    if not config_output:
        return ""
    
    description = ""
    
    # Cisco IOS/IOS-XE: description <text>
    desc_match = re.search(r'description\s+(.+?)(?:\r?\n|$)', config_output, re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()
    
    # NX-OS: description <text>
    if not description:
        desc_match = re.search(r'description\s+(.+?)(?:\r?\n|$)', config_output, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
    
    # Juniper JunOS: description "<text>";
    if not description:
        desc_match = re.search(r'description\s+"([^"]+)"', config_output, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
    
    # Clean up trailing quotes or semicolons
    description = description.rstrip('";').strip()
    
    return description


def _parse_interface_vlan_config(config_output, vendor):
    """
    Parse VLAN configuration from interface config output.
    Enhanced parsing for NXOS, IOS, IOS-XE with comprehensive pattern matching.
    
    Cisco IOS/IOS-XE patterns:
    - switchport access vlan <id>
    - switchport trunk allowed vlan <list>
    - switchport trunk native vlan <id>
    - switchport voice vlan <id>
    - switchport mode access|trunk|dynamic auto|dynamic desirable
    
    Cisco NX-OS patterns:
    - switchport access vlan <id> (same as IOS)
    - switchport trunk allowed vlan <list> (same as IOS)
    - switchport trunk native vlan <id> (same as IOS)
    - switchport mode access|trunk (same as IOS)
    - NX-OS may show: switchport access vlan 10 mode access (single line)
    
    Returns dict with:
    - mode: 'access', 'trunk', 'routed', 'dynamic', 'unknown'
    - access_vlan: VLAN ID for access ports
    - native_vlan: Native VLAN for trunks
    - allowed_vlans: List/string of allowed VLANs for trunks
    - voice_vlan: Voice VLAN if configured
    - other_options: List of additional features (port-security, portfast, etc.)
    """
    result = {
        "mode": "unknown",
        "access_vlan": None,
        "native_vlan": None,
        "allowed_vlans": None,
        "voice_vlan": None,
        "other_options": []
    }
    
    if not config_output:
        return result
    
    lines = config_output.split('\n')
    
    if vendor == "juniper_junos":
        # Juniper set format parsing
        for line in lines:
            line = line.strip()
            if "family ethernet-switching" in line:
                result["mode"] = "access"
            elif "family bridge" in line:
                result["mode"] = "trunk"
            elif "port-mode trunk" in line or "port-mode access" in line:
                if "trunk" in line:
                    result["mode"] = "trunk"
                else:
                    result["mode"] = "access"
            elif "vlan members" in line:
                vlan_match = re.search(r'vlan members\s+(\[.*?\]|\S+)', line)
                if vlan_match:
                    members = vlan_match.group(1)
                    if "[" in members:
                        result["allowed_vlans"] = members.strip("[]")
                    else:
                        result["access_vlan"] = members
            elif "native-vlan-id" in line:
                vlan_match = re.search(r'native-vlan-id\s+(\d+)', line)
                if vlan_match:
                    result["native_vlan"] = vlan_match.group(1)
    else:
        # Cisco parsing (IOS, IOS-XE, NX-OS)
        for line in lines:
            line = line.strip()
            
            # Detect mode - check for explicit mode setting first
            if "switchport mode access" in line:
                result["mode"] = "access"
            elif "switchport mode trunk" in line:
                result["mode"] = "trunk"
            elif "switchport mode dynamic auto" in line:
                result["mode"] = "dynamic"
            elif "switchport mode dynamic desirable" in line:
                result["mode"] = "dynamic"
            elif "switchport nonegotiate" in line:
                result["other_options"].append("nonegotiate")
            elif "no switchport" in line:
                result["mode"] = "routed"
            # NX-OS specific: switchport mode can be on same line as VLAN
            elif "switchport" in line and "access" in line and "vlan" in line and "mode" not in line:
                # NX-OS: switchport access vlan 10 (implies access mode)
                if result["mode"] == "unknown":
                    result["mode"] = "access"
            
            # Access VLAN - IOS/IOS-XE/NX-OS standard format
            if "switchport access vlan" in line:
                vlan_match = re.search(r'switchport access vlan\s+(\d+)', line)
                if vlan_match:
                    result["access_vlan"] = vlan_match.group(1)
            # NX-OS compact format: access vlan <id> (when switchport already on line)
            elif "access vlan" in line and "switchport" in line:
                vlan_match = re.search(r'access vlan\s+(\d+)', line)
                if vlan_match:
                    result["access_vlan"] = vlan_match.group(1)
            
            # Voice VLAN - IOS/IOS-XE/NX-OS standard format
            if "switchport voice vlan" in line:
                vlan_match = re.search(r'switchport voice vlan\s+(\d+)', line)
                if vlan_match:
                    result["voice_vlan"] = vlan_match.group(1)
            # NX-OS compact format: voice vlan <id>
            elif "voice vlan" in line and "switchport" in line:
                vlan_match = re.search(r'voice vlan\s+(\d+)', line)
                if vlan_match:
                    result["voice_vlan"] = vlan_match.group(1)
            
            # Native VLAN (trunk) - IOS/IOS-XE/NX-OS standard format
            if "switchport trunk native vlan" in line:
                vlan_match = re.search(r'switchport trunk native vlan\s+(\d+)', line)
                if vlan_match:
                    result["native_vlan"] = vlan_match.group(1)
            # NX-OS compact format: native vlan <id>
            elif "native vlan" in line and "switchport" in line:
                vlan_match = re.search(r'native vlan\s+(\d+)', line)
                if vlan_match:
                    result["native_vlan"] = vlan_match.group(1)
            
            # Allowed VLANs (trunk) - handle various formats
            # Standard IOS/IOS-XE/NX-OS: switchport trunk allowed vlan <list>
            if "switchport trunk allowed vlan" in line:
                vlan_match = re.search(r'switchport trunk allowed vlan\s+(.+)', line)
                if vlan_match:
                    allowed = vlan_match.group(1).strip()
                    # Handle special values
                    if allowed.lower() == "all":
                        result["allowed_vlans"] = "1-4094 (all)"
                    elif allowed.lower() == "none":
                        result["allowed_vlans"] = "none"
                    else:
                        result["allowed_vlans"] = allowed
            # NX-OS compact format: allowed vlan <list>
            elif "allowed vlan" in line and "switchport" in line:
                vlan_match = re.search(r'allowed vlan\s+(.+)', line)
                if vlan_match:
                    allowed = vlan_match.group(1).strip()
                    if allowed.lower() == "all":
                        result["allowed_vlans"] = "1-4094 (all)"
                    elif allowed.lower() == "none":
                        result["allowed_vlans"] = "none"
                    else:
                        result["allowed_vlans"] = allowed
            
            # Other security and STP options
            if "switchport port-security" in line:
                result["other_options"].append("port-security")
            if "switchport port-security maximum" in line:
                max_match = re.search(r'switchport port-security maximum\s+(\d+)', line)
                if max_match:
                    result["other_options"].append(f"port-security-max-{max_match.group(1)}")
            if "switchport port-security violation" in line:
                vio_match = re.search(r'switchport port-security violation\s+(\w+)', line)
                if vio_match:
                    result["other_options"].append(f"port-security-violation-{vio_match.group(1)}")
            if "spanning-tree" in line and "portfast" in line:
                result["other_options"].append("portfast")
            if "spanning-tree bpduguard" in line:
                result["other_options"].append("bpduguard")
            if "spanning-tree bpdufilter" in line:
                result["other_options"].append("bpdufilter")
            if "storm-control" in line:
                result["other_options"].append("storm-control")
            if "spanning-tree guard" in line:
                guard_match = re.search(r'spanning-tree guard\s+(\w+)', line)
                if guard_match:
                    result["other_options"].append(f"stp-guard-{guard_match.group(1)}")
            if "spanning-tree link-type" in line:
                link_match = re.search(r'spanning-tree link-type\s+(\w+)', line)
                if link_match:
                    result["other_options"].append(f"stp-link-{link_match.group(1)}")
    
    # Post-processing: infer mode from VLAN configuration if not explicitly set
    if result["mode"] == "unknown":
        if result["allowed_vlans"]:
            result["mode"] = "trunk"
        elif result["access_vlan"]:
            result["mode"] = "access"
        elif result["native_vlan"]:
            result["mode"] = "trunk"
    
    return result


def _parse_interfaces_list(output, vendor):
    """
    Parse interface list from 'show interface' command.
    Returns list of interface names with enhanced patterns for NXOS and IOS.
    """
    interfaces = []
    lines = output.split('\n')
    
    if vendor == "cisco_nxos":
        # NX-OS format: Ethernet1/1 is up, Ethernet1/1  is up (extra spaces), mgmt0
        for line in lines:
            line = line.strip()
            # Pattern 1: Standard "Ethernet1/1 is up"
            match = re.match(r'^([Ee]thernet\d+/\d+|[Pp]ort-channel\d+|[Mm]anagement\d+|[Ll]oopback\d+)\s+is\s+\w+', line)
            if match:
                interfaces.append(match.group(1))
                continue
            # Pattern 2: Extra spaces "Ethernet1/1  is up"
            match = re.match(r'^([Ee]thernet\d+/\d+|[Pp]ort-channel\d+|[Mm]anagement\d+)\s+\s+is\s+\w+', line)
            if match:
                interfaces.append(match.group(1))
                continue
            # Pattern 3: Just interface name
            match = re.match(r'^([Ee]thernet\d+/\d+|[Pp]ort-channel\d+|[Mm]anagement\d+)$', line)
            if match:
                interfaces.append(match.group(1))
    elif vendor == "juniper_junos":
        # Juniper format: ge-0/0/0, xe-0/0/0, et-0/0/0
        for line in lines:
            line = line.strip()
            # Match physical interfaces: ge-, xe-, et-, ae-
            match = re.match(r'^([a-z]{2}-\d+/\d+/\d+(\.\d+)?)', line)
            if match:
                interfaces.append(match.group(1))
                continue
            # Match bundle interfaces: ae-
            match = re.match(r'^(ae\d+)', line)
            if match:
                interfaces.append(match.group(1))
    else:
        # Cisco IOS/IOS-XE format: GigabitEthernet1/0/1, FastEthernet0/1, TenGigabitEthernet1/0/1
        for line in lines:
            line = line.strip()
            # Pattern 1: Full interface name with status
            match = re.match(r'^([A-Za-z]+\d+/\d+(/\d+)?)\s+is\s+(up|down|administratively down)', line, re.IGNORECASE)
            if match:
                interfaces.append(match.group(1))
                continue
            # Pattern 2: Short form (Gig, Ten, etc.)
            match = re.match(r'^([A-Za-z]+\d+/\d+(/\d+)?)\s+is\s+', line, re.IGNORECASE)
            if match:
                interfaces.append(match.group(1))
                continue
            # Pattern 3: Port-channel
            match = re.match(r'^(Port-channel\d+)\s+is\s+', line, re.IGNORECASE)
            if match:
                interfaces.append(match.group(1))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_interfaces = []
    for intf in interfaces:
        if intf not in seen:
            seen.add(intf)
            unique_interfaces.append(intf)
    
    return unique_interfaces


def _generate_html_report(result_data, host):
    """Generate beautiful HTML report inline to avoid dependency issues.
    Supports both single-device and multi-device reports."""
    
    # Check if this is a multi-device report
    if 'devices' in result_data:
        return _generate_multi_device_html_report(result_data)
    
    # Single device report
    true_host = _html_esc(result_data.get('true_host', host))
    interfaces = result_data.get('interfaces', [])
    device_type = _html_esc(result_data.get('device_type', 'unknown'))
    timestamp = _html_esc(result_data.get('timestamp', datetime.now().isoformat()))
    
    # Calculate statistics
    total = len(interfaces)
    up_count = sum(1 for i in interfaces if 'up' in i.get('status', '').lower())
    trunk_count = sum(1 for i in interfaces if i.get('vlan_info', {}).get('mode') == 'trunk')
    access_count = sum(1 for i in interfaces if i.get('vlan_info', {}).get('mode') == 'access')
    routed_count = sum(1 for i in interfaces if i.get('vlan_info', {}).get('mode') == 'routed')
    
    # Build interface table rows
    table_rows = ""
    for intf in interfaces:
        name = _html_esc(intf.get('name', 'N/A') or 'N/A')
        status = _html_esc(intf.get('status', 'unknown') or 'unknown')
        vlan_info = intf.get('vlan_info', {}) or {}
        mode = _html_esc(vlan_info.get('mode', 'unknown') or 'unknown')
        access_vlan = _html_esc(vlan_info.get('access_vlan', '-') or '-')
        native_vlan = _html_esc(vlan_info.get('native_vlan', '-') or '-')
        allowed_vlans = _html_esc(vlan_info.get('allowed_vlans', '-') or '-')
        voice_vlan = _html_esc(vlan_info.get('voice_vlan', '-') or '-')
        other_options_list = vlan_info.get('other_options', []) or []
        other_options = _html_esc(', '.join(str(o) for o in other_options_list) if other_options_list else '')
        
        # Status indicator
        status_lower = status.lower() if status else ''
        status_icon = '✓' if 'up' in status_lower else '✗' if 'down' in status_lower else '?'
        
        # Mode badge color
        mode_lower = mode.lower() if mode else ''
        mode_color = '#16a34a' if mode_lower == 'access' else '#dc2626' if mode_lower == 'trunk' else '#64748b'
        
        table_rows += f"""
        <tr>
            <td><code style="font-family:monospace;font-size:12px;background:#e0f2fe;color:#0369a1;padding:1px 6px;border-radius:4px;">{name}</code></td>
            <td><span style="color:{'#16a34a' if status_icon == '✓' else '#dc2626'};font-weight:600;">{status_icon}</span> {status}</td>
            <td><span style="background:{mode_color};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">{mode.upper()}</span></td>
            <td>{access_vlan}</td>
            <td>{native_vlan}</td>
            <td style="font-family:monospace;font-size:11px;">{allowed_vlans}</td>
            <td>{voice_vlan}</td>
            <td style="font-size:11px;color:#64748b;">{other_options}</td>
        </tr>
        """
    
    # Simple inline HTML without external dependencies
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Interface VLAN Report - {true_host}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f1f5f9; color: #0f172a; padding: 24px; }}
        .header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 16px; }}
        .header h1 {{ margin: 0; font-size: 20px; }}
        .header p {{ margin: 8px 0 0; opacity: 0.8; font-size: 14px; }}
        .stats {{ display: flex; gap: 12px; margin-bottom: 16px; }}
        .stat {{ flex: 1; padding: 16px; border-radius: 10px; text-align: center; color: white; }}
        .stat .val {{ font-size: 24px; font-weight: 700; }}
        .stat .lbl {{ font-size: 11px; margin-top: 4px; opacity: 0.9; text-transform: uppercase; }}
        .table {{ background: white; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #1e293b; color: #f8fafc; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; }}
        td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        tr:nth-child(even) td {{ background: #f8fafc; }}
        .footer {{ margin-top: 16px; font-size: 12px; color: #64748b; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Interface VLAN Report</h1>
        <p>Switch: {true_host} ({device_type}) &bull; Generated: {timestamp}</p>
    </div>
    <div class="stats">
        <div class="stat" style="background:#007aff;"><div class="val">{total}</div><div class="lbl">Total</div></div>
        <div class="stat" style="background:#10b981;"><div class="val">{up_count}</div><div class="lbl">Up</div></div>
        <div class="stat" style="background:#f59e0b;"><div class="val">{trunk_count}</div><div class="lbl">Trunk</div></div>
        <div class="stat" style="background:#6366f1;"><div class="val">{access_count}</div><div class="lbl">Access</div></div>
        <div class="stat" style="background:#64748b;"><div class="val">{routed_count}</div><div class="lbl">Routed</div></div>
    </div>
    <div class="table">
        <table>
            <thead>
                <tr>
                    <th>Interface</th>
                    <th>Status</th>
                    <th>Mode</th>
                    <th>Access VLAN</th>
                    <th>Native VLAN</th>
                    <th>Allowed VLANs</th>
                    <th>Voice VLAN</th>
                    <th>Options</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    <div class="footer">Network Swiss Tool Pro v7.0 &bull; Interface VLAN Reporter Plugin</div>
</body>
</html>"""
    
    return html_content


def _generate_multi_device_html_report(result_data):
    """Generate unified HTML report for multi-device scans.
    
    This creates a summary view with expandable device sections,
    cross-device VLAN consistency checking, and unified statistics.
    """
    devices = result_data.get('devices', [])
    timestamp = result_data.get('timestamp', datetime.now().isoformat())
    
    # Build summary table
    summary_rows = ""
    total_interfaces = 0
    total_trunks = 0
    total_access = 0
    
    for device in devices:
        host_raw = str(device.get('true_host', device.get('host', 'N/A')))
        host = _html_esc(host_raw)
        host_js = json.dumps(host_raw)
        device_type = _html_esc(device.get('device_type', 'unknown'))
        interfaces = device.get('interfaces', [])
        
        intf_count = len(interfaces)
        trunk_count = sum(1 for i in interfaces if i.get('vlan_info', {}).get('mode') == 'trunk')
        access_count = sum(1 for i in interfaces if i.get('vlan_info', {}).get('mode') == 'access')
        up_count = sum(1 for i in interfaces if 'up' in i.get('status', '').lower())
        
        total_interfaces += intf_count
        total_trunks += trunk_count
        total_access += access_count
        
        # Get individual report paths from device data
        txt_report = device.get('report_path', '')
        html_report = device.get('html_report_path', '')
        report_links = []
        if html_report:
            report_links.append(f'<a href="{_html_esc(html_report)}" target="_blank" style="color:#007aff;text-decoration:none;margin-right:8px;">HTML</a>')
        if txt_report:
            report_links.append(f'<a href="{_html_esc(txt_report)}" target="_blank" style="color:#64748b;text-decoration:none;">TXT</a>')
        links_html = ' | '.join(report_links) if report_links else 'N/A'
        
        summary_rows += f"""
        <tr>
            <td><strong>{host}</strong><br><small style="color:#64748b;">{device_type}</small></td>
            <td>{intf_count}</td>
            <td>{up_count}</td>
            <td>{trunk_count}</td>
            <td>{access_count}</td>
            <td style="font-size:12px;">{links_html} <button onclick="toggleDevice({host_js})" style="margin-left:8px;padding:4px 12px;background:#007aff;color:white;border:none;border-radius:4px;cursor:pointer;">View</button></td>
        </tr>
        """
    
    # Build device detail sections
    device_sections = ""
    for idx, device in enumerate(devices):
        host_raw = str(device.get('true_host', device.get('host', f'device_{idx}')))
        host = _html_esc(host_raw)
        interfaces = device.get('interfaces', [])
        device_type = _html_esc(device.get('device_type', 'unknown'))
        
        table_rows = ""
        for intf in interfaces:
            name = _html_esc(intf.get('name', 'N/A') or 'N/A')
            status = _html_esc(intf.get('status', 'unknown') or 'unknown')
            vlan_info = intf.get('vlan_info', {}) or {}
            description = _html_esc(intf.get('description', '') or '')
            mode = _html_esc(vlan_info.get('mode', 'unknown') or 'unknown')
            access_vlan = _html_esc(vlan_info.get('access_vlan', '-') or '-')
            native_vlan = _html_esc(vlan_info.get('native_vlan', '-') or '-')
            allowed_vlans = _html_esc(vlan_info.get('allowed_vlans', '-') or '-')
            voice_vlan = _html_esc(vlan_info.get('voice_vlan', '-') or '-')
            other_options_list = vlan_info.get('other_options', []) or []
            other_options = _html_esc(', '.join(str(o) for o in other_options_list) if other_options_list else '')
            
            status_lower = status.lower() if status else ''
            status_icon = '✓' if 'up' in status_lower else '✗' if 'down' in status_lower else '?'
            mode_lower = mode.lower() if mode else ''
            mode_color = '#16a34a' if mode_lower == 'access' else '#dc2626' if mode_lower == 'trunk' else '#64748b'
            
            description_row = f"<tr><td colspan='8' style='padding:4px 12px 4px 12px;font-size:11px;color:#64748b;font-style:italic;'>{description}</td></tr>" if description else ""
            
            table_rows += f"""
            <tr>
                <td><code style="font-family:monospace;font-size:12px;background:#e0f2fe;color:#0369a1;padding:1px 6px;border-radius:4px;">{name}</code></td>
                <td><span style="color:{'#16a34a' if status_icon == '✓' else '#dc2626'};font-weight:600;">{status_icon}</span> {status}</td>
                <td><span style="background:{mode_color};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">{mode.upper()}</span></td>
                <td>{access_vlan}</td>
                <td>{native_vlan}</td>
                <td style="font-family:monospace;font-size:11px;">{allowed_vlans}</td>
                <td>{voice_vlan}</td>
                <td style="font-size:11px;color:#64748b;">{other_options}</td>
            </tr>
            {description_row}
            """
        
        # Get individual report paths for device section
        txt_report = device.get('report_path', '')
        html_report = device.get('html_report_path', '')
        report_links = []
        if html_report:
            report_links.append(f'<a href="{_html_esc(html_report)}" target="_blank" style="color:#007aff;text-decoration:none;margin-right:12px;">📄 Open HTML Report</a>')
        if txt_report:
            report_links.append(f'<a href="{_html_esc(txt_report)}" target="_blank" style="color:#64748b;text-decoration:none;">📝 Open TXT Report</a>')
        links_html = ' '.join(report_links) if report_links else ''
        
        device_id = _html_esc(host_raw.replace('.', '-').replace(':', '-'))
        device_sections += f"""
        <div id="device-{device_id}" style="display:none;margin-bottom:24px;">
            <div style="background:white;border-radius:12px;padding:20px;border:1px solid #e2e8f0;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                    <h3 style="margin:0;color:#1e293b;">{host} ({device_type})</h3>
                    <div style="font-size:13px;">{links_html}</div>
                </div>
                <div class="table">
                    <table>
                        <thead>
                            <tr>
                                <th>Interface</th>
                                <th>Status</th>
                                <th>Mode</th>
                                <th>Access VLAN</th>
                                <th>Native VLAN</th>
                                <th>Allowed VLANs</th>
                                <th>Voice VLAN</th>
                                <th>Options</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Multi-Device Interface VLAN Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f1f5f9; color: #0f172a; padding: 24px; }}
        .header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 16px; }}
        .header h1 {{ margin: 0; font-size: 20px; }}
        .header p {{ margin: 8px 0 0; opacity: 0.8; font-size: 14px; }}
        .stats {{ display: flex; gap: 12px; margin-bottom: 16px; }}
        .stat {{ flex: 1; padding: 16px; border-radius: 10px; text-align: center; color: white; }}
        .stat .val {{ font-size: 24px; font-weight: 700; }}
        .stat .lbl {{ font-size: 11px; margin-top: 4px; opacity: 0.9; text-transform: uppercase; }}
        .table {{ background: white; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #1e293b; color: #f8fafc; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; }}
        td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        tr:nth-child(even) td {{ background: #f8fafc; }}
        .footer {{ margin-top: 16px; font-size: 12px; color: #64748b; text-align: center; }}
    </style>
    <script>
        function toggleDevice(host) {{
            var el = document.getElementById('device-' + host.replace(/\\./g, '-').replace(/:/g, '-'));
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>Multi-Device Interface VLAN Report</h1>
        <p>Devices: {len(devices)} &bull; Total Interfaces: {total_interfaces} &bull; Generated: {timestamp}</p>
    </div>
    <div class="stats">
        <div class="stat" style="background:#007aff;"><div class="val">{total_interfaces}</div><div class="lbl">Total Intf</div></div>
        <div class="stat" style="background:#f59e0b;"><div class="val">{total_trunks}</div><div class="lbl">Total Trunk</div></div>
        <div class="stat" style="background:#6366f1;"><div class="val">{total_access}</div><div class="lbl">Total Access</div></div>
        <div class="stat" style="background:#10b981;"><div class="val">{len(devices)}</div><div class="lbl">Devices</div></div>
    </div>
    <div class="table">
        <table>
            <thead>
                <tr>
                    <th>Device</th>
                    <th>Interfaces</th>
                    <th>Up</th>
                    <th>Trunk</th>
                    <th>Access</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {summary_rows}
            </tbody>
        </table>
    </div>
    {device_sections}
    <div class="footer">Network Swiss Tool Pro v7.0 &bull; Interface VLAN Reporter Plugin &bull; Multi-Device Report</div>
</body>
</html>"""
    
    return html_content


def _format_vlan_report(result_data, host):
    """Generate beautiful TXT report inline to avoid dependency issues.
    
    Defensive: Handles None values and missing fields gracefully.
    """
    
    true_host = str(result_data.get('true_host', host) or host)
    interfaces = result_data.get('interfaces', []) or []
    device_type = str(result_data.get('device_type', 'unknown') or 'unknown')
    timestamp = str(result_data.get('timestamp', datetime.now().isoformat()) or datetime.now().isoformat())
    
    # Summary statistics
    access_count = sum(1 for i in interfaces if (i.get('vlan_info', {}) or {}).get('mode') == 'access')
    trunk_count = sum(1 for i in interfaces if (i.get('vlan_info', {}) or {}).get('mode') == 'trunk')
    routed_count = sum(1 for i in interfaces if (i.get('vlan_info', {}) or {}).get('mode') == 'routed')
    up_count = sum(1 for i in interfaces if i.get('status') and 'up' in str(i.get('status')).lower())
    
    # Build simple inline header
    lines = []
    lines.append("=" * 72)
    lines.append("Network Swiss Tool Pro v7.0")
    lines.append("Interface VLAN Report")
    lines.append("=" * 72)
    lines.append(f"Generated: {timestamp}")
    lines.append("Fully offline — open this file in any browser or text editor")
    lines.append(f"Device: {true_host} ({device_type})")
    lines.append("")
    lines.append("HOW TO READ THIS REPORT:")
    lines.append("  • Access ports have a single access VLAN")
    lines.append("  • Trunk ports carry multiple VLANs (check allowed list)")
    lines.append("  • Native VLAN is untagged on trunks (default: VLAN 1)")
    lines.append("  • Voice VLAN is for IP phone traffic (CDP/LLDP-MED required)")
    lines.append("")
    lines.append("-" * 72)
    lines.append("")
    
    # Summary statistics
    lines.append("SUMMARY")
    lines.append("-" * 72)
    lines.append(f"  Total Interfaces:   {len(interfaces)}")
    lines.append(f"  Interfaces Up:      {up_count}")
    lines.append(f"  Access Ports:       {access_count}")
    lines.append(f"  Trunk Ports:        {trunk_count}")
    lines.append(f"  Routed Ports:      {routed_count}")
    lines.append("")
    
    # Interface details
    lines.append("INTERFACE DETAILS")
    lines.append("-" * 72)
    lines.append(f"  {'Interface':<20} {'Status':<12} {'Mode':<10} {'Access':<8} {'Native':<8} {'Allowed VLANs':<20} {'Voice':<8}")
    lines.append("-" * 72)
    
    for intf in interfaces:
        name = str(intf.get('name', 'N/A') or 'N/A')
        status = str(intf.get('status', 'unknown') or 'unknown')
        vlan_info = intf.get('vlan_info', {}) or {}
        mode = str(vlan_info.get('mode', 'unknown') or 'unknown')
        access_vlan = str(vlan_info.get('access_vlan', '-') or '-')
        native_vlan = str(vlan_info.get('native_vlan', '-') or '-')
        allowed_vlans = str(vlan_info.get('allowed_vlans', '-') or '-')
        voice_vlan = str(vlan_info.get('voice_vlan', '-') or '-')
        
        status_lower = status.lower() if status else ''
        status_icon = '✓' if 'up' in status_lower else '✗' if 'down' in status_lower else '?'
        
        lines.append(f"  {name:<20} {status_icon} {status:<10} {mode:<10} {access_vlan:<8} {native_vlan:<8} {allowed_vlans:<20} {voice_vlan:<8}")
        
        # Show other options if any
        other_options_list = vlan_info.get('other_options', []) or []
        if other_options_list:
            options_str = ', '.join(str(o) for o in other_options_list)
            lines.append(f"  {'':20} {'':12} {'':10} {'Options: ' + options_str}")
    
    # Footer
    lines.append("")
    lines.append("-" * 72)
    lines.append(f"End of report · {len(interfaces)} interfaces scanned on {true_host}")
    lines.append("-" * 72)
    
    return '\n'.join(lines)


# =============================================================================
# MAIN ENTRY POINT - The Contract
# =============================================================================
def run(device, credentials, params, config, log_func):
    """
    Main entry point for the interface VLAN reporter plugin.
    
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
    
    vendor = _determine_vendor(device_type)
    
    try:
        # Extract parameters
        interface_filter = params.get('interface_filter', '')
        include_shutdown = params.get('include_shutdown', False)
        output_format = params.get('output_format', 'both')
        
        # Log start of operation
        if log_func:
            log_func(f"[{host}] Starting {METADATA['display_name']}...")
        
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
            
            commands = VENDOR_COMMANDS.get(vendor, VENDOR_COMMANDS["cisco_ios"])
            
            # Get interface list
            if log_func:
                log_func(f"[{true_host}] Discovering interfaces...")
            
            try:
                interface_output = conn.send_command(commands["interfaces"], read_timeout=30)
            except Exception as e:
                if log_func:
                    log_func(f"[{true_host}] ERROR: Failed to get interface list: {str(e)}")
                return build_json(host, "fail", {}, f"Failed to get interface list: {str(e)}")
            
            if not interface_output or len(interface_output.strip()) < 10:
                if log_func:
                    log_func(f"[{true_host}] WARNING: Empty or invalid interface output")
                return build_json(host, "fail", {}, "Empty or invalid interface output")
            
            interface_names = _parse_interfaces_list(interface_output, vendor)
            
            if not interface_names:
                if log_func:
                    log_func(f"[{true_host}] WARNING: No interfaces parsed from output")
                return build_json(host, "fail", {}, "No interfaces parsed from output")
            
            if log_func:
                log_func(f"[{true_host}] Found {len(interface_names)} interfaces")
            
            # Apply filter if specified
            if interface_filter:
                interface_names = [i for i in interface_names if interface_filter.lower() in i.lower()]
                if log_func:
                    log_func(f"[{true_host}] Filtered to {len(interface_names)} interfaces")
            
            # Get VLAN configuration for each interface
            interfaces = []
            total_interfaces = len(interface_names)
            max_interfaces = min(total_interfaces, 100)  # Limit to prevent hanging
            
            if log_func:
                log_func(f"[{true_host}] Processing {max_interfaces} of {total_interfaces} interfaces...")
            
            for idx, intf_name in enumerate(interface_names[:max_interfaces]):
                if log_func and idx % 10 == 0:
                    log_func(f"[{true_host}] Processing interface {idx + 1}/{max_interfaces}: {intf_name}")
                
                try:
                    config_cmd = commands["config"].format(interface=intf_name)
                    config_output = conn.send_command(config_cmd, read_timeout=30)
                    
                    if log_func and idx < 3:  # Log first 3 interfaces for debugging
                        log_func(f"[{true_host}] Config output for {intf_name} (first 200 chars): {config_output[:200] if config_output else 'EMPTY'}")
                    
                    # Parse VLAN configuration
                    vlan_info = _parse_interface_vlan_config(config_output, vendor)
                    
                    if log_func and idx < 3:  # Log parsed VLAN info for debugging
                        log_func(f"[{true_host}] Parsed VLAN info for {intf_name}: mode={vlan_info.get('mode')}, access={vlan_info.get('access_vlan')}, native={vlan_info.get('native_vlan')}, allowed={vlan_info.get('allowed_vlans')}")
                    
                    # Get interface status from the interface list output
                    status = "unknown"
                    status_line = ""
                    for line in interface_output.split('\n'):
                        if intf_name in line:
                            status_line = line
                            if 'up' in line.lower() and 'down' not in line.lower():
                                status = "up"
                            elif 'down' in line.lower():
                                status = "down"
                            elif 'administratively down' in line.lower():
                                status = "admin-down"
                            break
                    
                    # Skip shutdown interfaces if requested
                    if not include_shutdown and ('down' in status.lower() or status == "admin-down"):
                        continue
                    
                    # Parse interface description from config
                    description = _parse_interface_description(config_output)
                    
                    interfaces.append({
                        "name": intf_name,
                        "status": status,
                        "vlan_info": vlan_info,
                        "description": description,
                        "config_preview": config_output[:200] if config_output else "",
                        "status_line": status_line
                    })
                    
                except Exception as e:
                    if log_func:
                        log_func(f"[{true_host}] Warning: Could not get VLAN info for {intf_name}: {str(e)}")
                    interfaces.append({
                        "name": intf_name,
                        "status": "error",
                        "vlan_info": {"mode": "error", "error": str(e)},
                        "description": "",
                        "error": str(e)
                    })
            
            if total_interfaces > max_interfaces and log_func:
                log_func(f"[{true_host}] Limited to {max_interfaces} interfaces (total: {total_interfaces})")
            
            if log_func:
                log_func(f"[{true_host}] Collected VLAN info for {len(interfaces)} interfaces")
            
            if len(interfaces) == 0:
                if log_func:
                    log_func(f"[{true_host}] WARNING: No interfaces collected after filtering")
                return build_json(host, "fail", {}, "No interfaces collected after filtering")
            
            result_data = {
                "true_host": true_host,
                "interfaces": interfaces,
                "interface_count": len(interfaces),
                "device_type": device_type,
                "vendor": vendor,
                "timestamp": datetime.now().isoformat(),
                "operation": "vlan_report"
            }
            
            if log_func:
                log_func(f"[{true_host}] Generating reports (format: {output_format})...")
            
            # Prepare output folder structure
            run_paths = prepare_run_output(CAT_PLUGINS, slugify(f'interface_vlan_report_{true_host}'))
            
            # Generate TXT report
            if output_format in ['both', 'txt']:
                try:
                    if log_func:
                        log_func(f"[{true_host}] Generating TXT report...")
                    
                    txt_report_path = path_in_run(run_paths, f'interface_vlan_report_{slugify(true_host)}.txt')
                    
                    if log_func:
                        log_func(f"[{true_host}] TXT report path: {txt_report_path}")
                    
                    txt_content = _format_vlan_report(result_data, host)
                    
                    if log_func:
                        log_func(f"[{true_host}] TXT content length: {len(txt_content)} characters")
                    
                    write_text_file(txt_report_path, txt_content)
                    
                    if log_func:
                        log_func(f"[{true_host}] TXT report written successfully")
                    
                    result_data["report_path"] = txt_report_path
                    result_data["run_folder"] = run_paths["run_dir"]
                    
                    if log_func:
                        log_func(f"[{true_host}] TXT report saved: {txt_report_path}")
                except Exception as txt_exc:
                    import traceback
                    if log_func:
                        log_func(f"[{true_host}] ERROR: Could not generate TXT report: {txt_exc}")
                        log_func(f"[{true_host}] Traceback: {traceback.format_exc()}")
                    return build_json(host, "fail", result_data, f"TXT report generation failed: {txt_exc}")
            
            # Generate HTML report
            if output_format in ['both', 'html']:
                try:
                    if log_func:
                        log_func(f"[{true_host}] Generating HTML report...")
                    
                    html_report_path = path_in_run(run_paths, f'interface_vlan_report_{slugify(true_host)}.html')
                    
                    if log_func:
                        log_func(f"[{true_host}] HTML report path: {html_report_path}")
                    
                    html_content = _generate_html_report(result_data, host)
                    
                    if log_func:
                        log_func(f"[{true_host}] HTML content length: {len(html_content)} characters")
                    
                    write_text_file(html_report_path, html_content)
                    
                    if log_func:
                        log_func(f"[{true_host}] HTML report written successfully")
                    
                    result_data["html_report_path"] = html_report_path
                    result_data["run_folder"] = run_paths["run_dir"]
                    
                    if log_func:
                        log_func(f"[{true_host}] HTML report saved: {html_report_path}")
                except Exception as html_exc:
                    import traceback
                    if log_func:
                        log_func(f"[{true_host}] WARNING: Could not write HTML report: {html_exc}")
                        log_func(f"[{true_host}] Traceback: {traceback.format_exc()}")
                    # Don't fail entire operation if HTML fails, just log it
            
            # Add to master execution summary
            try:
                summary = f"{len(interfaces)} interfaces reported"
                append_to_master_report(METADATA['plugin_id'], host, "success", summary, result_data.get("report_path", "N/A"))
                if log_func:
                    log_func(f"[{true_host}] Added to master execution summary")
            except Exception as summary_exc:
                if log_func:
                    log_func(f"[{true_host}] WARNING: Could not add to master summary: {summary_exc}")
            
            if log_func:
                log_func(f"[{true_host}] Plugin execution completed successfully")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        error_msg = str(e)
        if log_func:
            log_func(f"[{host}] ERROR: {error_msg}")
        # Include device type in error for debugging
        error_context = f"Device type: {device_type}, Vendor: {vendor if vendor else 'unknown'}"
        return build_json(host, "fail", {"error_context": error_context}, error_msg)


if __name__ == "__main__":
    # Self-test
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
    print(f"Parameters: {list(METADATA['required_params'].keys())}")
