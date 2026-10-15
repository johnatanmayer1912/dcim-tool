# Plugin Prompt: stp_topology_visualizer

## Purpose
Analyze Spanning-Tree Protocol (STP) status across network devices to identify Root Bridge locations, VLAN STP roles, and blocked/forwarding port states.

## Creation Prompt (v1.0.0)
```
Create a plugin called stp_topology_visualizer that:
1. Analyzes STP status on network devices
2. Identifies Root Bridge locations and VLAN mappings
3. Detects blocked ports that prevent loops
4. Supports Cisco IOS, Cisco NX-OS, and Juniper JunOS
5. Generates human-readable reports with clear status indicators
6. Uses platform-specific commands for each device type
7. Accepts optional vlan_id parameter (0 = all VLANs, 1-4094 = specific VLAN)
8. Returns JSON with true_host, is_root_any, roots list, summary, blocked_ports, device_type, timestamp, report_path
9. Saves formatted report to reports/stp_topology_visualizer/ directory
10. Does not modify device configuration (read-only)
```

## Implementation Requirements
- Use modules.network_base for connection and hostname resolution
- Use utils.report_formatter for report generation
- Platform-specific command mapping (IOS/NXOS/JUNOS)
- Robust parsing for Root ID extraction
- Blocked port detection with clear indicators
- Human-readable report formatting
- Error handling and logging
