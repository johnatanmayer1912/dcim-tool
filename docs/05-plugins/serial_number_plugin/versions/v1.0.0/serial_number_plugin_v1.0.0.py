"""
modules/plugins/serial_number_plugin.py
---------------------------------------
Serial Number/Hardware Info Plugin for Network Swiss Tool Pro v6.0

Retrieves chassis serial numbers, model numbers, and hardware info.
Essential for asset inventory and warranty tracking.
"""

METADATA = {
    "plugin_id": "serial_number",
    "display_name": "Serial Number Inventory",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Audit",
    "description": "Retrieves chassis serial numbers, model info, and hardware inventory.",
    "min_platform_version": "6.0.0",
    
    "required_params": {
        "include_modules": {
            "type": "checkbox",
            "label": "Include Module Details",
            "default": False,
            "description": "Retrieve line card/module serial numbers (slower)"
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


def _get_hostname_multiplatform(conn, device_type, host):
    """Get hostname with support for IOS, NXOS, and JunOS variants."""
    dt_lower = device_type.lower()
    try:
        if 'cisco' in dt_lower:
            # Multiple fallback commands for different IOS/NXOS versions
            hostname_cmds = [
                "show running-config | include hostname",
                "show run | inc hostname",
                "show hostname",
                "show ver | inc hostname"
            ]
        elif 'juniper' in dt_lower or 'junos' in dt_lower:
            hostname_cmds = [
                "show configuration system host-name",
                "show system information | match Hostname",
                "show host-name"
            ]
        else:
            hostname_cmds = ["show ver | inc hostname"]
        
        for cmd in hostname_cmds:
            try:
                output = conn.send_command(cmd)
                if output and '%' not in output and 'error' not in output.lower():
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
    Retrieve serial numbers and hardware info.
    Supports: Cisco IOS, IOS-XE, NXOS (all versions), Juniper JunOS (all versions)
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    include_modules = params.get('include_modules', False)
    dt_lower = device_type.lower()
    
    try:
        if log_func:
            log_func(f"[{host}] Retrieving hardware inventory...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func
        ) as conn:
            
            # Get hostname with multi-platform support
            true_host = _get_hostname_multiplatform(conn, device_type, host)
            
            # Version and inventory commands with fallbacks for older versions
            version_output = ""
            inventory_output = ""
            
            if 'cisco' in dt_lower:
                # Cisco version commands (multiple fallbacks)
                ver_commands = ["show version", "show ver"]
                for cmd in ver_commands:
                    try:
                        version_output = conn.send_command(cmd)
                        if version_output and '%' not in version_output:
                            break
                    except:
                        continue
                
                # Inventory for modules
                if include_modules:
                    inv_commands = ["show inventory", "show diag", "show module"]
                    for cmd in inv_commands:
                        try:
                            inventory_output = conn.send_command(cmd)
                            if inventory_output and '%' not in inventory_output:
                                break
                        except:
                            continue
                        
            elif 'juniper' in dt_lower or 'junos' in dt_lower:
                # Juniper version commands
                ver_commands = [
                    "show version",
                    "show version detail",
                    "show system information"
                ]
                for cmd in ver_commands:
                    try:
                        version_output = conn.send_command(cmd)
                        if version_output and 'error' not in version_output.lower():
                            break
                    except:
                        continue
                
                if include_modules:
                    hw_commands = [
                        "show chassis hardware",
                        "show chassis hardware detail",
                        "show chassis fpc"
                    ]
                    for cmd in hw_commands:
                        try:
                            inventory_output = conn.send_command(cmd)
                            if inventory_output and 'error' not in inventory_output.lower():
                                break
                        except:
                            continue
                    
            else:  # Generic
                try:
                    version_output = conn.send_command("show version")
                except:
                    version_output = ""
                if include_modules:
                    try:
                        inventory_output = conn.send_command("show inventory")
                    except:
                        inventory_output = ""
            
            # Parse serial numbers - comprehensive pattern matching
            result_data = {
                "true_host": true_host,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat()
            }
            
            # Extended serial number patterns for various platforms
            serial_patterns = [
                r'[Ss]erial\s*[Nn]umber\s*:?\s*(\S+)',
                r'[Cc]hassis\s+[Ss]erial\s*:?\s*(\S+)',
                r'[Ss]ystem\s+[Ss]erial\s*:?\s*(\S+)',
                r'[Pp]rocessor\s+[Bb]oard\s+[IDid]+\s*:?\s*(\S+)',
                r'[Hh]ardware\s+[Ss]erial\s*:?\s*(\S+)',
                r'SN:\s*(\S+)',  # Juniper format
                r'Serial\s*#?\s*:?\s*(\S+)',
                r'[Ff]rame\s+[Ss]erial\s*:?\s*(\S+)',  # Some older IOS
            ]
            
            serials_found = []
            for pattern in serial_patterns:
                matches = re.findall(pattern, version_output)
                serials_found.extend(matches)
            
            # Also check inventory for serial if not found in version
            if not serials_found and inventory_output:
                for pattern in serial_patterns:
                    matches = re.findall(pattern, inventory_output)
                    serials_found.extend(matches)
            
            if serials_found:
                # Filter out common false positives
                filtered_serials = [s for s in serials_found if len(s) > 3 and not s.lower() in ['none', 'n/a', 'unknown']]
                if filtered_serials:
                    result_data["chassis_serial"] = filtered_serials[0]
                    if len(filtered_serials) > 1:
                        result_data["all_serials"] = list(set(filtered_serials))
                else:
                    result_data["chassis_serial"] = "Not found"
            else:
                result_data["chassis_serial"] = "Not found"
            
            # Enhanced model extraction for multiple platforms
            model_patterns = [
                r'[Cc]isco\s+(\S+).*[Rr]evision',
                r'[Cc]isco\s+(\S+)\s+processor',
                r'[Mm]odel\s*(?:[Nn]umber\s*)?:?\s*(\S+)',
                r'[Hh]ardware\s*:?\s*(\S+)',
                r'[Hh]ostname:\s*(\S+)',  # Some platforms show model as hostname
                r'Model:\s*(\S+)',
                r'RE\s*0\s*\S*\s*(\S+)',  # Juniper routing engine
            ]
            
            model_found = None
            for pattern in model_patterns:
                match = re.search(pattern, version_output)
                if match:
                    model_found = match.group(1)
                    # Clean up model string
                    model_found = model_found.strip('()')
                    if model_found and len(model_found) > 2:
                        break
            
            result_data["model"] = model_found if model_found else "Unknown"
            
            # Module details if requested
            if include_modules and inventory_output:
                # Enhanced module counting for different platforms
                module_indicators = [
                    'SERIAL NUMBER', 'SN:', 'FPC', 'PIC', 'Module',
                    'Line card', 'Interface', 'Sub-module'
                ]
                module_count = 0
                for line in inventory_output.split('\n'):
                    line_upper = line.upper()
                    if any(ind.upper() in line_upper for ind in module_indicators):
                        if 'CHASSIS' not in line_upper and 'FAN' not in line_upper:
                            module_count += 1
                
                result_data["module_count"] = module_count
                result_data["has_module_data"] = True
                result_data["module_raw_summary"] = inventory_output[:500] + "..." if len(inventory_output) > 500 else inventory_output
            
            # Software version info
            sw_patterns = [
                r'Version\s*([^,\r\n]+)',
                r'IOS.*?(\d+\.\d+[^,\s]*)',
                r'Junos.*?(\d+\.\d+[^,\s]*)',
                r'NXOS.*?(\d+\.\d+[^,\s]*)',
            ]
            for pattern in sw_patterns:
                match = re.search(pattern, version_output, re.IGNORECASE)
                if match:
                    result_data["software_version"] = match.group(1).strip()
                    break
            
            if log_func:
                log_msg = f"[{true_host}] Serial: {result_data.get('chassis_serial', 'N/A')}, Model: {result_data.get('model', 'N/A')}"
                if include_modules:
                    log_msg += f", Modules: {result_data.get('module_count', 0)}"
                log_func(log_msg)
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        return build_json(host, "fail", {}, str(e))


if __name__ == "__main__":
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
