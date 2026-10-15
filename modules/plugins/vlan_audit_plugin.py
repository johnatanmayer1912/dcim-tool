"""
modules/plugins/vlan_audit_plugin.py
------------------------------------
VLAN Audit Plugin for Network Swiss Tool Pro v6.0

A complete plugin implementation of the VLAN audit feature.
This replaces the legacy modules/vlan_audit.py with a plugin-compatible version.
"""

METADATA = {
    "plugin_id": "vlan_audit",
    "display_name": "VLAN Audit",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Audit",
    "description": "Discovers and reports all VLANs configured on target devices.",
    "min_platform_version": "6.0.0",
    
    "required_params": {
        "include_details": {
            "type": "checkbox",
            "label": "Include VLAN Details",
            "default": True,
            "description": "Include VLAN names and status in report"
        },
        "max_vlans": {
            "type": "integer",
            "label": "Max VLANs to Display",
            "placeholder": "50",
            "default": 50,
            "required": False,
            "min": 1,
            "max": 1000
        }
    },
    
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": False
}

from modules.network_base import (
    connect_permissive,
    safe_connection,
    build_json,
    safe_node_name,
    resolve_hostname_from_prompt,
    parse_vlan_output
)
from utils.report_formatter import (
    format_vlan_audit_report,
    save_plugin_report,
    append_to_master_report
)
from datetime import datetime


def run(device, credentials, params, config, log_func):
    """
    Execute VLAN audit on a single device.
    
    Args:
        device: {'host': str, 'device_type': str, 'group': str, 'port': int}
        credentials: {'username': str, 'password': str, 'secret': str|None}
        params: {'include_details': bool, 'max_vlans': int}
        config: Global application settings
        log_func: Callable for UI logging
    
    Returns:
        {'status': 'success'|'fail', 'data': {...}, 'error': str|None}
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    conn = None
    
    try:
        include_details = params.get('include_details', True)
        max_vlans = params.get('max_vlans', 50)
        
        if log_func:
            log_func(f"[{host}] Starting VLAN audit...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            
            try:
                true_host = resolve_hostname_from_prompt(conn, host)
            except Exception:
                true_host = host
            
            if log_func:
                log_func(f"[{true_host}] Connected, retrieving VLANs...")
            
            # Send appropriate VLAN command for device type
            if 'juniper' in device_type.lower():
                output = conn.send_command("show vlans")
            elif 'nxos' in device_type.lower():
                output = conn.send_command("show vlan brief")
            else:
                output = conn.send_command("show vlan brief")
            
            if not output:
                return build_json(host, "fail", {}, "No output from VLAN command")
            
            # Parse VLAN output
            parsed_vlans = parse_vlan_output(output, device_type)
            vlans = []
            
            for vlan_tuple in parsed_vlans[:max_vlans]:
                if len(vlan_tuple) >= 2:
                    vlan_entry = {
                        "id": vlan_tuple[0],
                        "name": vlan_tuple[1]
                    }
                    if len(vlan_tuple) >= 3 and include_details:
                        vlan_entry["status"] = vlan_tuple[2]
                    vlans.append(vlan_entry)
            
            if log_func:
                log_func(f"[{true_host}] Found {len(vlans)} VLANs")
            
            result_data = {
                "true_host": true_host,
                "vlans": vlans,
                "vlan_count": len(vlans),
                "device_type": device_type,
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate human-readable report
            report_path = save_plugin_report("vlan_audit", host, result_data, format_vlan_audit_report)
            result_data["report_path"] = report_path
            
            # Add to master execution summary
            vlan_summary = f"{len(vlans)} VLANs discovered"
            append_to_master_report("vlan_audit", host, "success", vlan_summary, report_path)
            
            if log_func:
                log_func(f"[{true_host}] Report saved: {report_path}")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{host}] ERROR: {str(e)}")
        # Still try to log the failure
        try:
            append_to_master_report("vlan_audit", host, "fail", str(e)[:40], "N/A")
        except:
            pass
        return build_json(host, "fail", {}, str(e))
    
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass


if __name__ == "__main__":
    # Self-test
    print(f"Plugin: {METADATA['display_name']} v{METADATA['version']}")
    print(f"Category: {METADATA['category']}")
    print(f"Parameters: {list(METADATA['required_params'].keys())}")
