"""
modules/plugins/environment_status_plugin.py
--------------------------------------------
Environment/Health Status Plugin for Network Swiss Tool Pro v6.0

Retrieves temperature, fan status, and power supply status.
Critical for monitoring device health and preventing hardware failures.
"""

METADATA = {
    "plugin_id": "environment_status",
    "display_name": "Environment Health Check",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Discovery",
    "description": "Retrieves temperature, fan status, and power supply status from devices.",
    "min_platform_version": "6.0.0",
    
    "required_params": {
        "alert_only": {
            "type": "checkbox",
            "label": "Show Alerts Only",
            "default": False,
            "description": "Only report items with warnings or failures"
        },
        "include_temp": {
            "type": "checkbox",
            "label": "Include Temperature",
            "default": True,
            "description": "Retrieve temperature sensors"
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


def _get_hostname_env(conn, device_type, host):
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
    Retrieve environment status (temperature, fans, power).
    Supports: Cisco IOS (all versions), NXOS (all versions), Juniper JunOS (all versions)
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    alert_only = params.get('alert_only', False)
    include_temp = params.get('include_temp', True)
    dt_lower = device_type.lower()
    
    try:
        if log_func:
            log_func(f"[{host}] Checking environment status...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func
        ) as conn:
            
            # Get hostname
            true_host = _get_hostname_env(conn, device_type, host)
            
            # Initialize results
            environment_data = {
                "temperature": {},
                "fans": [],
                "power_supplies": [],
                "alerts": []
            }
            
            health_status = "OK"
            alert_count = 0
            
            # Multi-platform environment commands with fallbacks
            if 'cisco' in dt_lower:
                if 'nxos' in dt_lower:
                    # NXOS environment (multiple fallbacks for different versions)
                    if include_temp:
                        nxos_temp_cmds = [
                            "show environment temperature",
                            "show env temperature",
                            "show temp"
                        ]
                        for cmd in nxos_temp_cmds:
                            try:
                                temp_output = conn.send_command(cmd)
                                if temp_output and '%' not in temp_output:
                                    environment_data["temperature"]["raw"] = temp_output[:500]
                                    if any(word in temp_output.lower() for word in ['warning', 'critical', 'alert', 'hot']):
                                        health_status = "WARNING"
                                        alert_count += 1
                                    break
                            except:
                                continue
                    
                    # Fan status
                    nxos_fan_cmds = ["show environment fan", "show env fan", "show fan"]
                    for cmd in nxos_fan_cmds:
                        try:
                            fan_output = conn.send_command(cmd)
                            if fan_output and '%' not in fan_output:
                                environment_data["fans"].append({"raw": fan_output[:300]})
                                if 'fail' in fan_output.lower() or 'error' in fan_output.lower():
                                    health_status = "CRITICAL"
                                    alert_count += 1
                                break
                        except:
                            continue
                    
                    # Power status
                    nxos_power_cmds = ["show environment power", "show env power", "show power"]
                    for cmd in nxos_power_cmds:
                        try:
                            power_output = conn.send_command(cmd)
                            if power_output and '%' not in power_output:
                                environment_data["power_supplies"].append({"raw": power_output[:300]})
                                if 'fail' in power_output.lower() or 'error' in power_output.lower():
                                    health_status = "CRITICAL"
                                    alert_count += 1
                                break
                        except:
                            continue
                        
                else:  # IOS/IOS-XE
                    # IOS environment with fallbacks for older versions
                    ios_env_cmds = [
                        "show environment",
                        "show env",
                        "show environment all"
                    ]
                    
                    env_output = ""
                    for cmd in ios_env_cmds:
                        try:
                            env_output = conn.send_command(cmd)
                            if env_output and '%' not in env_output:
                                break
                        except:
                            continue
                    
                    environment_data["raw_output"] = env_output[:1000] if env_output else "Environment data not available"
                    
                    # Parse environment for issues
                    if env_output:
                        env_lower = env_output.lower()
                        if 'critical' in env_lower or 'shutdown' in env_lower:
                            health_status = "CRITICAL"
                            alert_count += 1
                        elif 'warning' in env_lower or 'alert' in env_lower:
                            health_status = "WARNING"
                            alert_count += 1
                        
                        # Check for specific component failures
                        if any(word in env_lower for word in ['fan fail', 'power fail', 'temp fail']):
                            health_status = "CRITICAL"
                            alert_count += 1
                        
            elif 'juniper' in dt_lower or 'junos' in dt_lower:
                # Juniper environment with fallbacks
                if include_temp:
                    junos_temp_cmds = [
                        "show chassis temperature-thresholds",
                        "show chassis temp",
                        "show chassis environment"
                    ]
                    for cmd in junos_temp_cmds:
                        try:
                            temp_output = conn.send_command(cmd)
                            if temp_output and 'error' not in temp_output.lower():
                                environment_data["temperature"]["thresholds"] = temp_output[:500]
                                break
                        except:
                            continue
                
                # Fan status
                junos_fan_cmds = ["show chassis fan", "show chassis cooling"]
                for cmd in junos_fan_cmds:
                    try:
                        fan_output = conn.send_command(cmd)
                        if fan_output and 'error' not in fan_output.lower():
                            environment_data["fans"].append({"status": fan_output[:300]})
                            if 'fail' in fan_output.lower() or 'error' in fan_output.lower():
                                health_status = "CRITICAL"
                                alert_count += 1
                            break
                    except:
                        continue
                
                # Power status
                junos_power_cmds = ["show chassis power", "show chassis pem"]
                for cmd in junos_power_cmds:
                    try:
                        power_output = conn.send_command(cmd)
                        if power_output and 'error' not in power_output.lower():
                            environment_data["power_supplies"].append({"status": power_output[:300]})
                            if 'fail' in power_output.lower() or 'error' in power_output.lower():
                                health_status = "CRITICAL"
                                alert_count += 1
                            break
                    except:
                        continue
                        
            else:  # Generic - try common commands
                generic_env_cmds = ["show environment", "show env", "show chassis environment"]
                env_output = ""
                for cmd in generic_env_cmds:
                    try:
                        env_output = conn.send_command(cmd)
                        if env_output and '%' not in env_output:
                            break
                    except:
                        continue
                
                if env_output:
                    environment_data["raw_output"] = env_output[:1000]
                    if any(word in env_output.lower() for word in ['critical', 'fail', 'error', 'hot', 'alert']):
                        health_status = "WARNING"
                        alert_count += 1
                else:
                    environment_data["raw_output"] = "Environment command not supported"
            
            # If alert_only and no alerts, return minimal data
            if alert_only and health_status == "OK":
                result_data = {
                    "true_host": true_host,
                    "device_type": device_type,
                    "timestamp": datetime.now().isoformat(),
                    "health_status": "OK",
                    "message": "No environment alerts detected"
                }
            else:
                result_data = {
                    "true_host": true_host,
                    "device_type": device_type,
                    "timestamp": datetime.now().isoformat(),
                    "health_status": health_status,
                    "alert_count": alert_count,
                    "environment_data": environment_data
                }
            
            if log_func:
                log_func(f"[{true_host}] Environment status: {health_status} ({alert_count} alerts)")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        return build_json(host, "fail", {}, str(e))


if __name__ == "__main__":
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
