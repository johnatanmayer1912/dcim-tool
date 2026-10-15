# Plugin: Unused Trunk VLAN Pruner

**Plugin ID:** unused_trunk_pruner  
**Current Version:** 1.0.1  
**Category:** Cleanup  
**Author:** Network Swiss Tool  

## Description

The Unused Trunk VLAN Pruner plugin identifies "Ghost" VLANs - VLANs that are allowed on trunk ports but are not defined in the device's VLAN database. These ghost VLANs can cause unnecessary broadcast traffic and potential security issues. The plugin analyzes trunk configurations and compares them against the active VLAN database to recommend pruning unnecessary VLANs.

## Features

- **Ghost VLAN Detection**: Identifies VLANs allowed on trunks but missing from the switch database
- **Multi-Platform Support**: Works with Cisco IOS, Cisco NX-OS, and Juniper JunOS
- **Platform-Specific Commands**: Automatically selects appropriate VLAN and trunk commands for each device type
- **VLAN Range Parsing**: Handles complex VLAN range formats (e.g., "1,10-12,20")
- **Human-Readable Reports**: Generates formatted reports with clear recommendations
- **Safety Analysis**: Read-only operation - does not modify device configuration

## Required Parameters

None - this plugin requires no parameters.

## Usage

### Basic Usage
```python
params = {}  # No parameters required
result = plugin.execute(device, credentials, params, config, log_func)
```

## Output Format

The plugin returns a JSON object with the following structure:

```json
{
  "true_host": "switch01.example.com",
  "defined_vlan_count": 25,
  "trunk_count": 8,
  "ghost_vlans": {
    "Gi0/1": ["10", "20", "30"],
    "Gi0/2": ["15", "25"]
  },
  "device_type": "cisco_ios",
  "timestamp": "2026-04-23T10:30:00",
  "report_path": "reports/unused_trunk_pruner/switch01_20260423_103000.txt"
}
```

## Report Format

The plugin generates a human-readable text report with the following sections:

- **Device Information**: Hostname, IP, device type, timestamp
- **Inventory Summary**: Count of defined VLANs and active trunks
- **Ghost VLANs**: List of interfaces with ghost VLANs (if any)
- **Recommendations**: Commands to prune ghost VLANs (if detected)

## Platform-Specific Behavior

### Cisco IOS
- VLAN command: `show vlan brief`
- Trunk command: `show interfaces trunk`
- Parsing: Extracts "Vlans allowed on trunk" section and compares with VLAN database

### Cisco NX-OS
- VLAN command: `show vlan brief`
- Trunk command: `show interface trunk`
- Parsing: Similar to IOS with NX-OS output format handling

### Juniper JunOS
- VLAN command: `show vlans`
- Trunk command: `show interfaces`
- Parsing: Simplified - Juniper trunk parsing is complex; focus on Cisco Ghost VLANs

## Use Cases

1. **Network Cleanup**: Identify and remove unnecessary VLANs from trunk configurations
2. **Security Hardening**: Reduce attack surface by limiting VLAN propagation
3. **Broadcast Domain Optimization**: Minimize unnecessary broadcast traffic
4. **Configuration Audit**: Verify trunk configurations match actual VLAN requirements
5. **Compliance**: Ensure VLAN configurations follow best practices

## Limitations

- Juniper support is simplified (focus on Cisco Ghost VLANs)
- Requires enable mode (privilege level 15) on Cisco devices
- VLAN range parsing may not handle all possible formats
- Does not automatically prune VLANs (read-only analysis only)
- May not detect dynamic VLAN assignments or voice VLANs

## Dependencies

- `modules.network_base`: Core network functions (connect_permissive, safe_connection, build_json, safe_node_name)
- `utils.report_formatter`: Report generation functions (save_plugin_report, append_to_master_report)

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Compatibility

See [COMPATIBILITY.md](COMPATIBILITY.md) for platform support matrix.

## Test Results

See [TEST_RESULTS.md](TEST_RESULTS.md) for validation results.

## Release Notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for release information.
