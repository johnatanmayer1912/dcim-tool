# Interface Configuration Manager Plugin

## Overview

The Interface Configuration Manager plugin provides enterprise-grade interface configuration management for Network Swiss Tool Pro. It enables discovery, validation, and deployment of interface configurations across multiple network device vendors with comprehensive safety mechanisms.

**Current Version:** 1.0.17  
**Platform Version:** 7.0.29+  
**Release Date:** 2026-06-10

### v7.0.29 — Junos same-line Physical interface status (BUG-0009)
- `_apply_junos_line_status()` parses `Physical interface: xe-0/0/0, Enabled, Physical link is Up` on the header line
- NX-OS `status: connected` and interface name-only lines parsed correctly
- Restores green pytest for interface discovery contracts

### v7.0.28 — Juniper ae bundle correlation
- Discovers LACP/AE membership via `show lacp interfaces` / `show aggregated-ethernet detail` (`utils/juniper_iface.py`)
- Links physical `xe-`/`ge-` ports to logical `ae` bundles in the interface map
- Web UI shows bundle cards with member lists and `↳ ae0` badges on member ports

## Features

- **Interface Discovery**: Automatically discovers all interfaces on a device with comprehensive metadata
- **Vendor Support**: Cisco NX-OS, IOS, IOS-XE, and Juniper JUNOS
- **Configuration Validation**: Multi-step validation including dry-run, syntax, platform, and conflict checks
- **Deployment Safety**: Pre-change backups, post-change verification, and rollback capability
- **Offline Operation**: Fully functional without external dependencies
- **Edge Case Handling**: Comprehensive fallback mechanisms for malformed output and legacy device versions
- **Deep Dive Enhancements**: Enhanced Junos interface status detection with Physical link Up/Down patterns

## Supported Operations

### 1. Discover
Discovers all interfaces on a device with the following information:
- Interface name and status
- Port-channel membership
- VLAN membership
- Interface descriptions
- L2/L3 mode
- MAC address
- MTU, duplex, and speed
- Current running configuration

### 2. Validate
Validates proposed interface configuration with multi-step checks:
- Dry-run validation (simulates command execution)
- Vendor syntax validation (checks syntax errors)
- Platform validation (verifies compatibility)
- Conflict validation (detects configuration conflicts)

### 3. Deploy
Deploys interface configuration with safety mechanisms:
- Pre-change automatic backup
- Command execution with error handling
- Post-change verification
- Rollback capability

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| operation | dropdown | Yes | Operation to perform: discover, validate, deploy |
| interface_filter | string | No | Filter to specific interface name |
| proposed_config | textarea | No | Configuration to validate or deploy |
| dry_run | checkbox | No | Dry run mode (default: True) |

## Usage Examples

### Discover All Interfaces
```python
params = {
    "operation": "discover",
    "interface_filter": "",
    "dry_run": False
}
```

### Validate Configuration
```python
params = {
    "operation": "validate",
    "interface_filter": "Ethernet1/1",
    "proposed_config": """
interface Ethernet1/1
  description Server Uplink
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30
  spanning-tree portfast trunk
""",
    "dry_run": True
}
```

### Deploy Configuration
```python
params = {
    "operation": "deploy",
    "interface_filter": "Ethernet1/1",
    "proposed_config": """
interface Ethernet1/1
  description Server Uplink
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30,40
  spanning-tree portfast trunk
""",
    "dry_run": False
}
```

## Vendor-Specific Notes

### Cisco NX-OS
- Uses `show interface` for discovery
- Uses `show run interface` for configuration
- Supports modern NX-OS syntax
- No encapsulation commands needed

### Cisco IOS
- Uses `show interface` for discovery
- Uses `show run interface` for configuration
- Supports legacy IOS syntax
- May require `switchport trunk encapsulation dot1q` on older versions

### Cisco IOS-XE
- Uses `show interface` for discovery
- Uses `show run interface` for configuration
- Similar to IOS with enhanced features
- Supports modern IOS-XE syntax

### Juniper JUNOS
- Uses `show interfaces` for discovery
- Uses `show configuration interfaces` for configuration
- Uses hierarchical configuration syntax
- Different command structure than Cisco

## Safety Mechanisms

### Pre-Change Backup
Before any deployment, the system automatically creates a backup of the current running configuration. The backup includes:
- Full running configuration capture
- Vendor-specific command execution (e.g., `show running-config` for Cisco, `show configuration` for Junos)
- Metadata including timestamp, device type, and vendor
- Storage in `backups/<hostname>/config_YYYYMMDD_HHMMSS.txt`
- File size tracking for validation

### Validation Pipeline
All configurations must pass a multi-step validation pipeline before deployment:
1. **Dry-run validation**: Simulates command execution without applying changes
2. **Vendor syntax validation**: Checks for syntax errors, invalid VLAN IDs, IP addresses, and legacy command warnings
3. **Platform compatibility validation**: Verifies device version and platform compatibility
4. **Conflict detection**: Detects VLAN conflicts, mode changes, and configuration conflicts with existing config

### Post-Change Verification
After deployment, the system performs comprehensive verification:
- **Interface status check**: Verifies interface is up/connected using vendor-specific commands
- **Configuration check**: Validates that configuration was applied correctly
- **VLAN database check**: Ensures VLAN database is accessible (non-critical)
- Returns detailed verification results with pass/fail status for each check

### Rollback Capability
If deployment fails or verification fails, the system provides rollback functionality:
- Reads backup configuration from file
- Extracts configuration commands (skipping header comments)
- Applies configuration using vendor-specific methods
- Supports both Cisco and Juniper rollback approaches
- Returns rollback success/failure status with error details

## Output Format

### Discovery Output
```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "interfaces": [
      {
        "name": "Ethernet1/1",
        "status": "connected",
        "port_channel": "Port-channel1",
        "vlan_membership": [10, 20, 30],
        "description": "Server Uplink",
        "l2_l3_mode": "layer2",
        "mac_address": "00:11:22:33:44:55",
        "mtu": 1500,
        "duplex": "full",
        "speed": "1000",
        "current_config": "...",
        "vendor": "cisco_nxos",
        "capabilities": {...},
        "errors": [],
        "warnings": []
      }
    ],
    "interface_count": 48,
    "device_type": "cisco_nxos",
    "vendor": "cisco_nxos",
    "timestamp": "2026-06-03T12:00:00",
    "operation": "discover"
  }
}
```

### Validation Output
```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "validation_results": {
      "dry_run": {"passed": true, "commands": [...], "warnings": [], "errors": []},
      "vendor_syntax": {"passed": true, "errors": [], "warnings": [...]},
      "platform": {"passed": true, "platform": "cisco_nxos", "version": "9.3(5)", "compatibility": "full"},
      "conflicts": {"passed": true, "conflicts": [], "warnings": []}
    },
    "overall_status": "ready_for_deployment",
    "recommendation": "Safe to deploy",
    "risk_level": "low",
    "device_type": "cisco_nxos",
    "vendor": "cisco_nxos",
    "timestamp": "2026-06-03T12:00:00",
    "operation": "validate"
  }
}
```

### Deployment Output
```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "deployment_results": {
      "pre_backup": {
        "path": "backups/switch01/config_20260603_120000.txt",
        "timestamp": "2026-06-03T12:00:00",
        "size": 15234
      },
      "deployment": {
        "commands_executed": ["interface Ethernet1/1", "..."],
        "success_count": 5,
        "failure_count": 0,
        "execution_time": 3.5
      },
      "post_verification": {
        "passed": true,
        "verification_commands": [...],
        "verification_results": [...]
      }
    },
    "rollback_available": true,
    "rollback_path": "backups/switch01/config_20260603_120000.txt",
    "deployment_status": "success",
    "device_type": "cisco_nxos",
    "timestamp": "2026-06-03T12:00:00",
    "operation": "deploy"
  }
}
```

## Error Handling

The plugin provides detailed error messages for common issues:
- Connection failures
- Authentication errors
- Invalid configuration syntax
- Platform incompatibility
- Configuration conflicts

All errors are logged through the log_func callback for real-time UI updates.

## Requirements

- Minimum platform version: 7.0.29
- Requires enable password for configuration changes
- Supports single device operations (not parallel)

## Limitations

- Currently supports single device operations only
- Does not support interface range configuration (e.g., Ethernet1/1-10)
- Port-channel member discovery is basic and may need enhancement
- Conflict detection is placeholder and needs enhancement

## Future Enhancements

- Support for interface range configuration
- Enhanced port-channel member discovery
- Advanced conflict detection
- Configuration templates
- Bulk interface operations
- Interface state monitoring

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Support

For issues or questions, refer to:
- [PROMPT.md](PROMPT.md) - Development instructions
- [COMPATIBILITY.md](COMPATIBILITY.md) - Platform compatibility
- [TEST_RESULTS.md](TEST_RESULTS.md) - Test results

## License

Part of Network Swiss Tool Pro v7.0.29
