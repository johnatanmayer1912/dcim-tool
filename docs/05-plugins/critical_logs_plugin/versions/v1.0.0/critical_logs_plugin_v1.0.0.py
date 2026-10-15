"""
modules/plugins/critical_logs_plugin.py
---------------------------------------
Critical Logs Retrieval Plugin for Network Swiss Tool Pro v6.0

Retrieves recent syslog entries, focusing on critical/error/warning messages.
Useful for troubleshooting and proactive monitoring.
"""

METADATA = {
    "plugin_id": "critical_logs",
    "display_name": "Critical Log Scanner",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Audit",
    "description": "Retrieves recent syslog entries, filtering for critical/error/warning messages.",
    "min_platform_version": "6.0.0",
    
    "required_params": {
        "log_count": {
            "type": "integer",
            "label": "Number of Log Entries",
            "placeholder": "20",
            "default": 20,
            "required": False,
            "min": 5,
            "max": 100
        },
        "severity_filter": {
            "type": "dropdown",
            "label": "Minimum Severity",
            "options": ["ALL", "EMERGENCY", "ALERT", "CRITICAL", "ERROR", "WARNING"],
            "default": "ERROR",
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


def _get_hostname_logs(conn, device_type, host):
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
    Retrieve and filter syslog entries.
    Supports: Cisco IOS (all versions), NXOS (all versions), Juniper JunOS (all versions)
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    log_count = params.get('log_count', 20)
    severity_filter = params.get('severity_filter', 'ERROR')
    dt_lower = device_type.lower()
    
    try:
        if log_func:
            log_func(f"[{host}] Retrieving last {log_count} log entries...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func
        ) as conn:
            
            # Get hostname
            true_host = _get_hostname_logs(conn, device_type, host)
            
            # Multi-platform log commands with fallbacks
            log_output = ""
            
            if 'cisco' in dt_lower:
                # Cisco NXOS commands (newer and older versions)
                if 'nxos' in dt_lower:
                    nxos_log_cmds = [
                        f"show logging last {log_count}",
                        f"show logg last {log_count}",
                        "show logging"
                    ]
                    for cmd in nxos_log_cmds:
                        try:
                            log_output = conn.send_command(cmd)
                            if log_output and '%' not in log_output and 'invalid' not in log_output.lower():
                                break
                        except:
                            continue
                else:
                    # Cisco IOS/IOS-XE commands (older versions may not support | include)
                    ios_log_cmds = [
                        "show logging",
                        "show log",
                        f"show logging | tail {log_count}",  # Some newer IOS
                        "show logging | include"
                    ]
                    for cmd in ios_log_cmds:
                        try:
                            log_output = conn.send_command(cmd)
                            if log_output and '%' not in log_output:
                                break
                        except:
                            continue
                    
            elif 'juniper' in dt_lower or 'junos' in dt_lower:
                # Juniper commands with fallbacks
                junos_log_cmds = [
                    f"show log messages | last {log_count}",
                    f"show log | last {log_count}",
                    "show log messages",
                    "show log"
                ]
                for cmd in junos_log_cmds:
                    try:
                        log_output = conn.send_command(cmd)
                        if log_output and 'error' not in log_output.lower():
                            break
                    except:
                        continue
                    
            else:  # Generic
                generic_cmds = ["show logging", "show log"]
                for cmd in generic_cmds:
                    try:
                        log_output = conn.send_command(cmd)
                        if log_output and '%' not in log_output:
                            break
                    except:
                        continue
            
            # Process and filter logs
            lines = log_output.split('\n') if log_output else []
            
            # Severity keywords for filtering
            severity_keywords = {
                'EMERGENCY': ['emergency', 'emerg'],
                'ALERT': ['alert'],
                'CRITICAL': ['critical', 'crit'],
                'ERROR': ['error', 'err', 'failed', 'failure'],
                'WARNING': ['warning', 'warn'],
            }
            
            filtered_logs = []
            severity_counts = {level: 0 for level in severity_keywords.keys()}
            severity_counts['INFO'] = 0
            
            # Determine which severities to include based on filter
            include_levels = []
            filter_reached = False
            for level in ['EMERGENCY', 'ALERT', 'CRITICAL', 'ERROR', 'WARNING']:
                if level == severity_filter or filter_reached:
                    include_levels.extend(severity_keywords[level])
                    filter_reached = True
            
            if severity_filter == 'ALL':
                include_levels = []  # Include everything
            
            for line in lines[:log_count * 3]:  # Check more lines than requested
                line = line.strip()
                if not line:
                    continue
                
                # Determine severity of this line
                line_severity = 'INFO'
                for severity, keywords in severity_keywords.items():
                    if any(keyword in line.lower() for keyword in keywords):
                        line_severity = severity
                        severity_counts[severity] += 1
                        break
                else:
                    severity_counts['INFO'] += 1
                
                # Apply filter
                if severity_filter == 'ALL' or line_severity in ['EMERGENCY', 'ALERT', 'CRITICAL', 'ERROR', 'WARNING']:
                    if severity_filter == 'ALL' or any(kw in line.lower() for kw in include_levels):
                        filtered_logs.append({
                            "line": line[:200],  # Truncate long lines
                            "severity": line_severity
                        })
                
                if len(filtered_logs) >= log_count:
                    break
            
            # Count total critical issues
            critical_count = (severity_counts['EMERGENCY'] + 
                            severity_counts['ALERT'] + 
                            severity_counts['CRITICAL'] + 
                            severity_counts['ERROR'])
            
            result_data = {
                "true_host": true_host,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
                "log_entries": filtered_logs,
                "severity_counts": severity_counts,
                "critical_issues": critical_count,
                "warning_issues": severity_counts['WARNING'],
                "total_checked": len(lines)
            }
            
            if log_func:
                log_func(f"[{true_host}] Found {critical_count} critical/error entries, {severity_counts['WARNING']} warnings")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        return build_json(host, "fail", {}, str(e))


if __name__ == "__main__":
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
