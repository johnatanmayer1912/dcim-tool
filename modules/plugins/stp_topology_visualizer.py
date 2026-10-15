"""
modules/plugins/stp_topology_visualizer.py
-----------------------------------------
Spanning-Tree (STP) Topology Visualizer for Network Swiss Tool Pro.
Identifies Root Bridge status, VLAN STP roles, and port states.

VERSION HISTORY:
- v1.0.1 (2026-04-23): Improved cross-platform support (IOS/NXOS/JUNOS)
  - Robust hostname detection using connection prompt.
  - Platform-specific command mapping.
- v1.0.0 (2026-04-23): Initial release
"""

METADATA = {
    "plugin_id": "stp_topology_visualizer",
    "display_name": "STP Topology Visualizer",
    "version": "1.0.1",
    "author": "Network Swiss Tool",
    "category": "Troubleshooting",
    "description": "Visualizes Spanning-Tree topology, Root Bridge location, and Blocked/Forwarding ports.",
    "min_platform_version": "6.0.0",
    
    "changelog": [
        {
            "version": "1.0.1",
            "date": "2026-04-23",
            "changes": "Improved cross-platform support and robust hostname detection.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        }
    ],
    
    "required_params": {
        "vlan_id": {
            "type": "integer",
            "label": "Specific VLAN (0 for all)",
            "default": 0,
            "required": False,
            "min": 0,
            "max": 4094
        }
    },
    
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": True,
}

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

def run(device, credentials, params, config, log_func):
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown').lower()
    target_vlan = params.get('vlan_id', 0)
    
    try:
        if log_func:
            log_func(f"[{host}] Starting STP Topology Scan...")
            
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            
            true_host = resolve_hostname_from_prompt(conn, host)
            
            # 2. Platform Command Mapping
            is_juniper = 'juniper' in device_type
            is_nxos = 'nxos' in device_type
            
            if is_juniper:
                summary_cmd = "show spanning-tree bridge"
                root_cmd = "show spanning-tree bridge"
                blocked_cmd = "show spanning-tree interface | match Blk"
            elif is_nxos:
                summary_cmd = "show spanning-tree summary"
                root_cmd = "show spanning-tree root" if target_vlan == 0 else f"show spanning-tree vlan {target_vlan} root"
                blocked_cmd = "show spanning-tree blocked-ports"
            else: # Default Cisco IOS
                summary_cmd = "show spanning-tree summary"
                root_cmd = "show spanning-tree root" if target_vlan == 0 else f"show spanning-tree vlan {target_vlan} root"
                blocked_cmd = "show spanning-tree blockedports"
            
            # 2. Execute Commands
            if log_func: log_func(f"[{true_host}] Gathering STP status...")
            summary_output = conn.send_command(summary_cmd)
            
            if log_func: log_func(f"[{true_host}] Analyzing Root Bridge locations...")
            root_output = conn.send_command(root_cmd)
            
            if log_func: log_func(f"[{true_host}] Checking for Blocked ports...")
            blocked_output = conn.send_command(blocked_cmd)
            
            # 3. Multi-platform Parsing Logic
            is_root_any = False
            roots = []
            
            if is_juniper:
                # Juniper parsing
                is_root_any = "root" in summary_output.lower()
                for line in root_output.splitlines():
                    if "Root ID" in line or "Bridge ID" in line:
                        # Extract Root ID from line like 'Root ID : 32768.0011.2233.4455'
                        match = re.search(r'ID\s+:\s+([0-9a-fA-F.]+)', line)
                        if match:
                            roots.append({"vlan": "All", "root_id": match.group(1)})
            else:
                # Cisco IOS/NXOS parsing
                is_root_any = "This bridge is the root" in summary_output or "this bridge is the root" in root_output
                for line in root_output.splitlines():
                    if "VLAN" in line and "Root ID" not in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            roots.append({"vlan": parts[0], "root_id": parts[2]})

            result_data = {
                "true_host": true_host,
                "is_root_any": is_root_any,
                "roots": roots[:10],
                "summary": summary_output[:800],
                "blocked_ports": blocked_output if (blocked_output and "None" not in blocked_output and "No blocked" not in blocked_output) else "None",
                "device_type": device_type,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save Report
            report_path = save_plugin_report(
                METADATA['plugin_id'], 
                host, 
                result_data, 
                _format_stp_report
            )
            result_data["report_path"] = report_path
            
            # Clean up blocked ports indicator for summary
            has_blocked = "None" not in result_data["blocked_ports"]
            summary_msg = f"Root: {'Yes' if is_root_any else 'No'}, Blocked: {'Detected' if has_blocked else 'None'}"
            append_to_master_report(METADATA['plugin_id'], host, "success", summary_msg, report_path)
            
            return build_json(host, "success", result_data)
            
    except Exception as e:
        if log_func: log_func(f"[{host}] ERROR: {str(e)}")
        return build_json(host, "fail", {}, str(e))

def _format_stp_report(data, host):
    lines = []
    lines.append("=" * 75)
    lines.append("SPANNING-TREE (STP) TOPOLOGY REPORT")
    lines.append("=" * 75)
    lines.append("")
    lines.append(f"Device Hostname:    {data.get('true_host', 'N/A')}")
    lines.append(f"Device IP:          {host}")
    lines.append(f"Device Type:        {data.get('device_type', 'N/A')}")
    lines.append(f"Report Generated:   {data.get('timestamp', 'N/A')}")
    lines.append("")
    
    lines.append("-" * 75)
    lines.append("ROOT BRIDGE STATUS")
    lines.append("-" * 75)
    if data.get('is_root_any'):
        lines.append("🌟 THIS DEVICE IS THE ROOT BRIDGE (for one or more VLANs)")
    else:
        lines.append("ℹ️ This device is NOT a Root Bridge.")
    lines.append("")
    
    roots = data.get('roots', [])
    if roots:
        lines.append("VLAN Root ID Mapping (Sample):")
        for r in roots:
            lines.append(f"  VLAN {r['vlan']:<10} -> Root ID: {r['root_id']}")
        lines.append("")

    lines.append("-" * 75)
    lines.append("BLOCKED PORTS (LOOP PREVENTION)")
    lines.append("-" * 75)
    blocked = data.get('blocked_ports', 'None')
    if "None" in blocked or not blocked.strip():
        lines.append("✅ No blocked ports detected. All active ports are Forwarding/Designated.")
    else:
        lines.append("⚠️ BLOCKED PORTS DETECTED:")
        for line in blocked.splitlines():
            if line.strip() and not line.startswith('--'):
                lines.append(f"  {line.strip()}")
    lines.append("")
    
    lines.append("-" * 75)
    lines.append("STP OUTPUT PREVIEW")
    lines.append("-" * 75)
    summary = data.get('summary', 'No data')
    for line in summary.splitlines()[:20]:
        if line.strip(): lines.append(f"  {line}")
    lines.append("")

    lines.append("=" * 75)
    lines.append("END OF REPORT")
    lines.append("=" * 75)
    
    return '\n'.join(lines)
