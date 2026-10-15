# Plugin: vPC Domain Analysis

**Plugin ID:** vpc_domain  
**Current Version:** 2.3.1  
**Category:** Audit  
**Author:** Network Swiss Tool  

## Description

The vPC Domain Analysis plugin provides comprehensive analysis of Virtual Port Channel (vPC) configurations on Cisco NX-OS devices. It extracts vPC domain information, peer-link status, keepalive status, consistency parameters (Type-1, Type-2, per-VLAN), and executes actual verification commands for all 10 vPC recommendations. The plugin includes defensive programming to handle missing or malformed data gracefully and provides human-readable error reporting with mismatch detection.

## Features

- **Domain ID Extraction**: Identifies vPC domain ID from device configuration
- **Role Detection**: Determines vPC role (primary/secondary)
- **Peer-Link Status**: Monitors peer-link connectivity status
- **Keepalive Status**: Tracks vPC keepalive health
- **Consistency Parameters**: Analyzes Type-1, Type-2, and per-VLAN consistency
- **vPC Member Display**: Shows all vPC Port-Channels with status and consistency
- **10 Verification Checks**: Executes actual verification commands for all recommendations
- **Human-Readable Reports**: Generates formatted reports with PASS/FAIL/WARN indicators
- **Domain Peer Correlation**: Correlates vPC domain information across multiple switches
- **Defensive Programming**: Handles missing or malformed data gracefully without crashing

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
  "true_host": "nexus01.example.com",
  "domain_id": "1",
  "role": "primary",
  "peer_status": "up",
  "keepalive_status": "up",
  "config_consistency": "success",
  "per_vlan_consistency": "success",
  "config_inconsistency_reason": "",
  "type2_inconsistency_reason": "",
  "present": true,
  "vpcs": [
    {
      "id": "10",
      "port": "Po10",
      "status": "up",
      "consistency": "success"
    }
  ],
  "cdp_neighbors": [...],
  "domain_peers": [...],
  "verification_results": {
    "peer_link": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "keepalive": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "type1_consistency": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "type2_consistency": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "per_vlan_consistency": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "vlan_consistency": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "vpc_consistency": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "cdp_neighbors": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "port_channel_members": {"status": "pass", "message": "...", "impact": "...", "action": "..."},
    "vpc_statistics": {"status": "pass", "message": "...", "impact": "...", "action": "..."}
  },
  "device_type": "cisco_nxos",
  "timestamp": "2026-04-23T10:30:00",
  "report_path": "reports/vpc_domain/nexus01_20260423_103000.txt"
}
```

## Report Format

The plugin generates a human-readable text report with the following sections:

- **Device Information**: Hostname, IP, device type, timestamp
- **vPC Domain Status**: Domain ID, role, peer-link status, keepalive status
- **Consistency Parameters**: Type-1, Type-2, per-VLAN consistency status
- **vPC Members**: List of vPC Port-Channels with status and consistency
- **CDP Neighbors**: CDP neighbor information
- **Domain Peer Correlation**: vPC domain information across switches
- **vPC Verification Results**: 10 verification checks with PASS/FAIL/WARN indicators, impact descriptions, and recommended actions

## Platform-Specific Behavior

### Cisco NX-OS
- Primary platform for vPC analysis
- Commands: `show vpc`, `show vpc peer-link`, `show vpc role`, `show interface brief`, `show vpc consistency-parameters`, `show vpc statistics`, `show vpc legacy`
- Parses NX-OS specific output formats for vPC information
- Executes verification commands for all 10 recommendations

### Other Platforms
- Not supported - vPC is Cisco NX-OS specific technology

## Verification Checks

The plugin executes 10 verification checks:

1. **Peer-link**: Verifies peer-link status and configuration
2. **Keepalive**: Verifies keepalive connectivity and configuration
3. **Type-1 Consistency**: Verifies global consistency parameters
4. **Type-2 Consistency**: Verifies interface-level consistency parameters
5. **Per-VLAN Consistency**: Verifies VLAN-specific consistency
6. **VLAN Consistency**: Verifies VLAN membership consistency
7. **vPC Consistency**: Verifies overall vPC configuration consistency
8. **CDP Neighbors**: Verifies CDP neighbor discovery
9. **Port-Channel Members**: Verifies port-channel member configuration
10. **vPC Statistics**: Verifies vPC statistics and counters

## Use Cases

1. **vPC Health Monitoring**: Monitor vPC domain health and status
2. **Troubleshooting**: Diagnose vPC-related connectivity issues
3. **Configuration Audit**: Verify vPC configuration follows best practices
4. **Consistency Verification**: Ensure Type-1, Type-2, and per-VLAN consistency
5. **Network Documentation**: Document vPC configuration across the network

## Limitations

- Cisco NX-OS only (vPC is NX-OS specific)
- Requires appropriate permissions for vPC show commands
- Complex vPC configurations may require manual interpretation
- Verification commands may vary by NX-OS version
- Large vPC domains may result in truncated output

## Dependencies

- `modules.network_base`: Core network functions (safe_connection, build_json, safe_node_name, resolve_hostname_from_prompt)
- `utils.report_formatter`: Report generation functions (save_plugin_report, append_to_master_report)

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Compatibility

See [COMPATIBILITY.md](COMPATIBILITY.md) for platform support matrix.

## Test Results

See [TEST_RESULTS.md](TEST_RESULTS.md) for validation results.

## Release Notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for release information.
