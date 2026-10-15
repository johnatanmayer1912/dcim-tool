# Compatibility: stp_topology_visualizer

## Platform Support Matrix

| Platform | Support Level | Notes |
|----------|---------------|-------|
| Cisco IOS | ✅ Full | Tested with IOS 12.x, 15.x, 17.x |
| Cisco NX-OS | ✅ Full | Tested with NX-OS 7.x, 9.x |
| Juniper JunOS | ✅ Full | Tested with JunOS 18.x, 20.x, 22.x |

## Minimum Platform Version

**Minimum Platform Version:** 6.0.0

## Platform-Specific Requirements

### Cisco IOS
- Requires privilege level 15 (enable mode)
- Supports PVST+, RSTP, MST modes
- Commands: `show spanning-tree summary`, `show spanning-tree root`, `show spanning-tree blockedports`

### Cisco NX-OS
- Requires privilege level 15 (enable mode)
- Supports RSTP, MST modes
- Commands: `show spanning-tree summary`, `show spanning-tree root`, `show spanning-tree blocked-ports`

### Juniper JunOS
- Requires appropriate permissions for operational commands
- Supports RSTP, MSTP, VSTP modes
- Commands: `show spanning-tree bridge`, `show spanning-tree interface | match Blk`

## Known Limitations

1. **VLAN Count**: Large VLAN counts may result in truncated output (limited to 10 root mappings in JSON)
2. **STP Mode Variations**: Blocked port detection may vary by STP mode (PVST+, RSTP, MST)
3. **Output Preview**: Report output preview limited to first 20 lines of raw command output
4. **Root ID Parsing**: Complex Root ID formats may not be parsed correctly on all platforms

## Dependencies

- Python 3.8+
- Netmiko library
- Network Swiss Tool Pro core modules (modules.network_base, utils.report_formatter)

## Tested Configurations

| Platform | OS Version | STP Mode | Test Date | Result |
|----------|------------|----------|-----------|--------|
| Cisco IOS | 15.2(2)E7 | PVST+ | 2026-04-23 | ✅ Pass |
| Cisco NX-OS | 9.3(5) | RSTP | 2026-04-23 | ✅ Pass |
| Juniper JunOS | 22.3R1 | RSTP | 2026-04-23 | ✅ Pass |
