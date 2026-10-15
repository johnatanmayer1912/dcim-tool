# Plugin: STP Topology Visualizer

**Plugin ID:** stp_topology_visualizer  
**Current Version:** 1.0.1  
**Category:** Troubleshooting  
**Author:** Network Swiss Tool  

## Description

The STP Topology Visualizer plugin analyzes Spanning-Tree Protocol (STP) status across network devices to identify Root Bridge locations, VLAN STP roles, and blocked/forwarding port states. This plugin helps network engineers understand STP topology, detect potential loops, and verify loop prevention mechanisms are functioning correctly.

## Features

- **Root Bridge Detection**: Identifies whether a device is the Root Bridge for any VLAN
- **VLAN Root ID Mapping**: Maps VLANs to their respective Root Bridge IDs
- **Blocked Port Analysis**: Detects and reports blocked ports that prevent loops
- **Multi-Platform Support**: Works with Cisco IOS, Cisco NX-OS, and Juniper JunOS
- **Platform-Specific Commands**: Automatically selects appropriate STP commands for each device type
- **Human-Readable Reports**: Generates formatted reports with clear status indicators

## Required Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| vlan_id | integer | 0 | No | Specific VLAN to analyze (0 = all VLANs, 1-4094 for specific VLAN) |

## Usage

### Basic Usage (All VLANs)
```python
params = {
    "vlan_id": 0  # Analyze all VLANs
}
result = plugin.execute(device, credentials, params, config, log_func)
```

### Specific VLAN Analysis
```python
params = {
    "vlan_id": 100  # Analyze only VLAN 100
}
result = plugin.execute(device, credentials, params, config, log_func)
```

## Output Format

The plugin returns a JSON object with the following structure:

```json
{
  "true_host": "switch01.example.com",
  "is_root_any": true,
  "roots": [
    {
      "vlan": "1",
      "root_id": "32768.0011.2233.4455"
    },
    {
      "vlan": "100",
      "root_id": "32768.0011.2233.4455"
    }
  ],
  "summary": "This bridge is the root...",
  "blocked_ports": "None",
  "device_type": "cisco_ios",
  "timestamp": "2026-04-23T10:30:00",
  "report_path": "reports/stp_topology_visualizer/switch01_20260423_103000.txt"
}
```

## Report Format

The plugin generates a human-readable text report with the following sections:

- **Device Information**: Hostname, IP, device type, timestamp
- **Root Bridge Status**: Whether the device is a Root Bridge
- **VLAN Root ID Mapping**: Sample of VLAN to Root ID mappings
- **Blocked Ports**: List of blocked ports (if any)
- **STP Output Preview**: Sample of raw STP command output

## Platform-Specific Behavior

### Cisco IOS
- Summary command: `show spanning-tree summary`
- Root command: `show spanning-tree root` (or `show spanning-tree vlan <vlan_id> root`)
- Blocked ports command: `show spanning-tree blockedports`

### Cisco NX-OS
- Summary command: `show spanning-tree summary`
- Root command: `show spanning-tree root` (or `show spanning-tree vlan <vlan_id> root`)
- Blocked ports command: `show spanning-tree blocked-ports`

### Juniper JunOS
- Summary command: `show spanning-tree bridge`
- Root command: `show spanning-tree bridge`
- Blocked ports command: `show spanning-tree interface | match Blk`

## Use Cases

1. **STP Topology Verification**: Verify STP is configured correctly and Root Bridge placement is optimal
2. **Loop Detection**: Identify blocked ports that indicate loop prevention is active
3. **Root Bridge Analysis**: Determine which devices are Root Bridges for which VLANs
4. **Troubleshooting**: Diagnose STP-related connectivity issues
5. **Network Audits**: Document STP configuration across the network

## Limitations

- Requires enable mode (privilege level 15) on Cisco devices
- Blocked port detection may vary by platform and STP mode (PVST+, RSTP, MST)
- Large VLAN counts may result in truncated output (limited to 10 root mappings in JSON)
- Report output preview limited to first 20 lines of raw command output

## Dependencies

- `modules.network_base`: Core network functions (connect_permissive, safe_connection, build_json, safe_node_name, resolve_hostname_from_prompt)
- `utils.report_formatter`: Report generation functions (save_plugin_report, append_to_master_report)

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Compatibility

See [COMPATIBILITY.md](COMPATIBILITY.md) for platform support matrix.

## Test Results

See [TEST_RESULTS.md](TEST_RESULTS.md) for validation results.

## Release Notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for release information.
