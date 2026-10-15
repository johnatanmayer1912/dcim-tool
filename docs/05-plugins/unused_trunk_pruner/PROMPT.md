# Plugin Prompt: unused_trunk_pruner

## Purpose
Identify "Ghost" VLANs - VLANs that are allowed on trunk ports but are not defined in the device's VLAN database. These ghost VLANs can cause unnecessary broadcast traffic and potential security issues.

## Creation Prompt (v1.0.0)
```
Create a plugin called unused_trunk_pruner that:
1. Analyzes trunk configurations on network devices
2. Compares allowed VLANs on trunks against the device VLAN database
3. Identifies "Ghost" VLANs (allowed on trunk but missing from database)
4. Supports Cisco IOS, Cisco NX-OS, and Juniper JunOS
5. Handles complex VLAN range formats (e.g., "1,10-12,20")
6. Generates human-readable reports with pruning recommendations
7. Uses platform-specific commands for each device type
8. Requires no parameters (automatic analysis)
9. Returns JSON with true_host, defined_vlan_count, trunk_count, ghost_vlans dict, device_type, timestamp, report_path
10. Saves formatted report to reports/unused_trunk_pruner/ directory
11. Does not modify device configuration (read-only analysis)
12. Provides pruning command recommendations in report
```

## Implementation Requirements
- Use modules.network_base for connection and hostname resolution
- Use utils.report_formatter for report generation
- Platform-specific command mapping (IOS/NXOS/JUNOS)
- VLAN range parsing helper function for complex formats
- Robust parsing for "Vlans allowed on trunk" section
- Human-readable report formatting with recommendations
- Error handling and logging
