# Compatibility: unused_trunk_pruner

## Platform Support Matrix

| Platform | Support Level | Notes |
|----------|---------------|-------|
| Cisco IOS | ✅ Full | Tested with IOS 12.x, 15.x, 17.x |
| Cisco NX-OS | ✅ Full | Tested with NX-OS 7.x, 9.x |
| Juniper JunOS | ⚠️ Limited | Simplified support - focus on Cisco Ghost VLANs |

## Minimum Platform Version

**Minimum Platform Version:** 6.0.0

## Platform-Specific Requirements

### Cisco IOS
- Requires privilege level 15 (enable mode)
- Supports standard trunk configurations
- Commands: `show vlan brief`, `show interfaces trunk`

### Cisco NX-OS
- Requires privilege level 15 (enable mode)
- Supports NX-OS trunk configurations
- Commands: `show vlan brief`, `show interface trunk`

### Juniper JunOS
- Requires appropriate permissions for operational commands
- Simplified parsing - Juniper trunk configuration is complex
- Commands: `show vlans`, `show interfaces`
- Note: Juniper support is limited; focus is on Cisco Ghost VLAN detection

## Known Limitations

1. **Juniper Support**: Simplified - Juniper trunk parsing is complex; plugin focuses on Cisco Ghost VLANs
2. **VLAN Range Formats**: May not handle all possible VLAN range formats
3. **Dynamic VLANs**: Does not detect dynamic VLAN assignments or voice VLANs
4. **Read-Only**: Plugin does not automatically prune VLANs (analysis only)
5. **Multi-Line Output**: VLAN strings spanning multiple lines may not be parsed correctly in all cases

## Dependencies

- Python 3.8+
- Netmiko library
- Network Swiss Tool Pro core modules (modules.network_base, utils.report_formatter)

## Tested Configurations

| Platform | OS Version | Trunk Type | Test Date | Result |
|----------|------------|------------|-----------|--------|
| Cisco IOS | 15.2(2)E7 | 802.1Q | 2026-04-23 | ✅ Pass |
| Cisco NX-OS | 9.3(5) | 802.1Q | 2026-04-23 | ✅ Pass |
| Juniper JunOS | 22.3R1 | 802.1Q | 2026-04-23 | ⚠️ Limited |
