"""
modules/plugins/device_time_plugin.py
-------------------------------------
Device Time Retrieval Plugin for Network Swiss Tool Pro v6.0

Retrieves system clock and NTP status from network devices.
Useful for checking time synchronization across the network.
"""

METADATA = {
    "plugin_id": "device_time",
    "display_name": "Device Time Check",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Discovery",
    "description": "Retrieves system time, timezone, and NTP status from devices.",
    "min_platform_version": "6.0.0",
    
    "required_params": {
        "show_ntp": {
            "type": "checkbox",
            "label": "Include NTP Status",
            "default": True,
            "description": "Also retrieve NTP synchronization status"
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
    safe_node_name,
    resolve_hostname_from_prompt,
)
from utils.report_formatter import (
    format_device_time_report,
    save_plugin_report,
    append_to_master_report
)
from datetime import datetime


def _get_hostname(conn, device_type, host, log_func):
    try:
        return resolve_hostname_from_prompt(conn, host)
    except Exception:
        return host


def run(device, credentials, params, config, log_func):
    """
    Retrieve device time and NTP status.
    Supports: Cisco IOS, IOS-XE, NXOS, Juniper JunOS (older and newer versions)
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    show_ntp = params.get('show_ntp', True)
    dt_lower = device_type.lower()
    
    try:
        if log_func:
            log_func(f"[{host}] Retrieving device time...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            
            # Get hostname
            true_host = _get_hostname(conn, device_type, host, log_func)
            
            # Platform-specific commands with fallbacks for older versions
            time_output = ""
            ntp_output = ""
            timezone = "Unknown"
            
            if 'cisco' in dt_lower:
                # Cisco IOS/IOS-XE/NXOS time commands
                time_commands = [
                    "show clock detail",
                    "show clock",
                    "show calendar"
                ]
                
                for cmd in time_commands:
                    try:
                        time_output = conn.send_command(cmd)
                        if time_output and '%' not in time_output:
                            break
                    except:
                        continue
                
                # Try to extract timezone
                if time_output and 'zone' in time_output.lower():
                    tz_match = __import__('re').search(r'Timezone:\s*(\S+)|zone\s+(\S+)', time_output, __import__('re').IGNORECASE)
                    if tz_match:
                        timezone = tz_match.group(1) or tz_match.group(2)
                
                # NTP commands for Cisco
                if show_ntp:
                    ntp_commands = [
                        "show ntp status",
                        "show ntp associations",
                        "show ntp peer-status",
                        "show clock source"
                    ]
                    
                    for cmd in ntp_commands:
                        try:
                            ntp_output = conn.send_command(cmd)
                            if ntp_output and '%' not in ntp_output:
                                break
                        except:
                            continue
                            
            elif 'juniper' in dt_lower or 'junos' in dt_lower:
                # Juniper time commands
                time_commands = [
                    "show system uptime",
                    "show system information | match time"
                ]
                
                for cmd in time_commands:
                    try:
                        time_output = conn.send_command(cmd)
                        if time_output and 'error' not in time_output.lower():
                            break
                    except:
                        continue
                
                # NTP for Juniper
                if show_ntp:
                    ntp_commands = [
                        "show ntp associations",
                        "show ntp status",
                        "show system information | match NTP"
                    ]
                    
                    for cmd in ntp_commands:
                        try:
                            ntp_output = conn.send_command(cmd)
                            if ntp_output and 'error' not in ntp_output.lower():
                                break
                        except:
                            continue
            
            else:  # Generic fallback
                generic_commands = ["show clock", "show time"]
                for cmd in generic_commands:
                    try:
                        time_output = conn.send_command(cmd)
                        if time_output and '%' not in time_output:
                            break
                    except:
                        continue
                
                if show_ntp:
                    try:
                        ntp_output = conn.send_command("show ntp status")
                    except:
                        ntp_output = "NTP not available"
            
            if log_func:
                log_func(f"[{true_host}] Time retrieved successfully")
            
            # Parse time string
            time_str = "Unknown"
            if time_output:
                lines = time_output.strip().split('\n')
                for line in lines[:3]:  # Check first 3 lines
                    if line.strip() and not line.strip().startswith('%'):
                        time_str = line.strip()
                        break
            
            result_data = {
                "true_host": true_host,
                "device_time": time_str,
                "timezone": timezone,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat()
            }
            
            if show_ntp:
                result_data["ntp_status"] = ntp_output.strip()[:1000] if ntp_output else "Not available"
                
                # Multi-platform NTP sync detection
                ntp_lower = ntp_output.lower()
                if any(word in ntp_lower for word in ['sync', 'synchronized', 'sys.peer', 'selected']):
                    result_data["ntp_synced"] = True
                elif any(word in ntp_lower for word in ['unsync', 'unsynchronized', 'reject', 'rejecting']):
                    result_data["ntp_synced"] = False
                else:
                    result_data["ntp_synced"] = "Unknown"
            
            # Generate human-readable report
            report_path = save_plugin_report("device_time", host, result_data, format_device_time_report)
            result_data["report_path"] = report_path
            
            # Add to master execution summary
            ntp_summary = "NTP: " + ("Synced" if result_data.get("ntp_synced") == True else "Not Synced")
            append_to_master_report("device_time", host, "success", ntp_summary, report_path)
            
            if log_func:
                log_func(f"[{true_host}] Report saved: {report_path}")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        # Still try to log the failure
        try:
            append_to_master_report("device_time", host, "fail", str(e)[:40], "N/A")
        except:
            pass
        return build_json(host, "fail", {}, str(e))


if __name__ == "__main__":
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
    print(f"Parameters: {list(METADATA['required_params'].keys())}")
