"""
modules/plugins/interface_errors_plugin.py
------------------------------------------
Interface Error Counters Plugin for Network Swiss Tool Pro v6.0

Retrieves interface error statistics (input/output errors, CRC, giants, etc.).
Essential for identifying problematic ports and cabling issues.
"""

METADATA = {
    "plugin_id": "interface_errors",
    "display_name": "Interface Error Check",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Audit",
    "description": "Retrieves interface error counters (CRC, giants, runts, input/output errors).",
    "min_platform_version": "6.0.0",
    
    "required_params": {
        "min_errors": {
            "type": "integer",
            "label": "Minimum Error Threshold",
            "placeholder": "1",
            "default": 1,
            "required": False,
            "min": 0,
            "max": 1000000
        },
        "interface_filter": {
            "type": "string",
            "label": "Interface Filter (regex)",
            "placeholder": "Gi|Te|Eth (optional)",
            "required": False
        }
    },
    
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": False
}

from modules.network_base import (
    safe_connection,
    build_json,
    safe_node_name
)
from datetime import datetime
import re


def _get_hostname_iface(conn, device_type, host):
    """Get hostname with multi-platform support."""
    dt_lower = device_type.lower()
    try:
        if 'cisco' in dt_lower:
            cmds = ["show run | inc hostname", "show hostname", "show ver | inc hostname"]
        elif 'juniper' in dt_lower or 'junos' in dt_lower:
            cmds = ["show configuration system host-name", "show system information | match Hostname"]
        else:
            cmds = ["show ver | inc hostname"]
        
        for cmd in cmds:
            try:
                output = conn.send_command(cmd)
                if output and '%' not in output:
                    hn = safe_node_name(output)
                    if hn and hn != 'unknown':
                        return hn
            except:
                continue
        return host
    except:
        return host


def run(device, credentials, params, config, log_func):
    """
    Retrieve interface error counters.
    Supports: Cisco IOS (all versions), NXOS (all versions), Juniper JunOS (all versions)
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    min_errors = params.get('min_errors', 1)
    interface_filter = params.get('interface_filter', '')
    dt_lower = device_type.lower()
    
    try:
        if log_func:
            log_func(f"[{host}] Checking interface error counters...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func
        ) as conn:
            
            # Get hostname
            true_host = _get_hostname_iface(conn, device_type, host)
            
            # Multi-platform interface error commands with fallbacks
            counters_output = ""
            interface_output = ""
            
            if 'cisco' in dt_lower:
                if 'nxos' in dt_lower:
                    # NXOS interface error commands (multiple fallbacks)
                    nxos_error_cmds = [
                        "show interface counters errors",
                        "show interface counters error",
                        "show interface brief"
                    ]
                    for cmd in nxos_error_cmds:
                        try:
                            counters_output = conn.send_command(cmd)
                            if counters_output and '%' not in counters_output:
                                break
                        except:
                            continue
                            
                    try:
                        interface_output = conn.send_command("show interface brief")
                    except:
                        pass
                else:  # IOS/IOS-XE
                    # IOS commands with fallbacks for older versions
                    ios_error_cmds = [
                        "show interfaces counters errors",
                        "show interfaces counter error",
                        "show controllers"
                    ]
                    for cmd in ios_error_cmds:
                        try:
                            counters_output = conn.send_command(cmd)
                            if counters_output and '%' not in counters_output:
                                break
                        except:
                            continue
                    
                    # Fallback: get detailed interface output for all IOS versions
                    if not counters_output or 'invalid' in counters_output.lower():
                        ios_fallback_cmds = [
                            "show interfaces",
                            "show ip interface brief",
                            "show int"
                        ]
                        for cmd in ios_fallback_cmds:
                            try:
                                counters_output = conn.send_command(cmd)
                                if counters_output and '%' not in counters_output:
                                    break
                            except:
                                continue
                        
            elif 'juniper' in dt_lower or 'junos' in dt_lower:
                # Juniper commands with fallbacks
                junos_error_cmds = [
                    "show interfaces extensive",
                    "show interfaces detail",
                    "show interface extensive",
                    "show interface detail"
                ]
                for cmd in junos_error_cmds:
                    try:
                        counters_output = conn.send_command(cmd)
                        if counters_output and 'error' not in counters_output.lower():
                            break
                    except:
                        continue
                
            else:  # Generic
                generic_cmds = ["show interfaces", "show int"]
                for cmd in generic_cmds:
                    try:
                        counters_output = conn.send_command(cmd)
                        if counters_output and '%' not in counters_output:
                            break
                    except:
                        continue
            
            # Parse interface errors
            interfaces_with_errors = []
            total_interfaces = 0
            
            lines = counters_output.split('\n') if counters_output else []
            current_interface = None
            current_errors = {}
            
            for line in lines:
                # Check for interface name
                if line.strip() and not line.startswith(' '):
                    if current_interface and current_errors:
                        total_errors = sum(current_errors.values())
                        if total_errors >= min_errors:
                            interfaces_with_errors.append({
                                "interface": current_interface,
                                "errors": current_errors,
                                "total_errors": total_errors
                            })
                    
                    # Start new interface
                    current_interface = line.strip().rstrip(':')
                    current_errors = {
                        "input_errors": 0,
                        "output_errors": 0,
                        "crc_errors": 0,
                        "giants": 0,
                        "runts": 0,
                        "collisions": 0
                    }
                    total_interfaces += 1
                
                # Parse error counters
                if current_interface:
                    line_lower = line.lower()
                    
                    # Various error patterns
                    if 'input error' in line_lower or 'input errors' in line_lower:
                        match = re.search(r'(\d+)', line)
                        if match:
                            current_errors["input_errors"] = int(match.group(1))
                    
                    if 'output error' in line_lower or 'output errors' in line_lower:
                        match = re.search(r'(\d+)', line)
                        if match:
                            current_errors["output_errors"] = int(match.group(1))
                    
                    if 'crc' in line_lower:
                        match = re.search(r'(\d+)', line)
                        if match:
                            current_errors["crc_errors"] = int(match.group(1))
                    
                    if 'giant' in line_lower:
                        match = re.search(r'(\d+)', line)
                        if match:
                            current_errors["giants"] = int(match.group(1))
                    
                    if 'runt' in line_lower:
                        match = re.search(r'(\d+)', line)
                        if match:
                            current_errors["runts"] = int(match.group(1))
                    
                    if 'collision' in line_lower:
                        match = re.search(r'(\d+)', line)
                        if match:
                            current_errors["collisions"] = int(match.group(1))
            
            # Check last interface
            if current_interface and current_errors:
                total_errors = sum(current_errors.values())
                if total_errors >= min_errors:
                    interfaces_with_errors.append({
                        "interface": current_interface,
                        "errors": current_errors,
                        "total_errors": total_errors
                    })
            
            # Apply interface filter if specified
            if interface_filter and interfaces_with_errors:
                try:
                    pattern = re.compile(interface_filter, re.IGNORECASE)
                    interfaces_with_errors = [
                        i for i in interfaces_with_errors 
                        if pattern.search(i["interface"])
                    ]
                except re.error:
                    log_func(f"[{true_host}] Warning: Invalid interface filter regex")
            
            # Calculate totals
            total_error_count = sum(i["total_errors"] for i in interfaces_with_errors)
            crc_total = sum(i["errors"]["crc_errors"] for i in interfaces_with_errors)
            
            result_data = {
                "true_host": true_host,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
                "total_interfaces_checked": total_interfaces,
                "interfaces_with_errors": len(interfaces_with_errors),
                "problematic_interfaces": interfaces_with_errors[:10],  # Limit output
                "total_error_count": total_error_count,
                "total_crc_errors": crc_total,
                "has_critical_errors": crc_total > 0 or total_error_count > 100
            }
            
            if log_func:
                log_func(f"[{true_host}] Checked {total_interfaces} interfaces, {len(interfaces_with_errors)} have errors")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        return build_json(host, "fail", {}, str(e))


if __name__ == "__main__":
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
