# Compatibility: vpc_domain

## Platform Support Matrix

| Platform | Support Level | Notes |
|----------|---------------|-------|
| Cisco NX-OS | ✅ Full | Tested with NX-OS 7.x, 9.x |
| Cisco IOS | ❌ Not Supported | vPC is NX-OS specific technology |
| Juniper JunOS | ❌ Not Supported | vPC is Cisco NX-OS specific technology |

## Minimum Platform Version

**Minimum Platform Version:** 6.0.0

## Platform-Specific Requirements

### Cisco NX-OS
- Requires appropriate permissions for vPC show commands
- Supports all vPC features (peer-link, keepalive, consistency parameters)
- Commands: `show vpc`, `show vpc peer-link`, `show vpc role`, `show interface brief`, `show vpc consistency-parameters`, `show vpc statistics`, `show vpc legacy`
- Tested with NX-OS 7.x and 9.x releases

## Known Limitations

1. **NX-OS Only**: vPC is Cisco NX-OS specific technology - not supported on IOS or JunOS
2. **Command Variations**: Verification commands may vary by NX-OS version
3. **Complex Configurations**: Large vPC domains may result in truncated output
4. **Parsing Complexity**: vPC output format may vary between NX-OS versions
5. **Verification Scope**: Verification commands may not cover all possible vPC configurations

## Dependencies

- Python 3.8+
- Netmiko library
- Network Swiss Tool Pro core modules (modules.network_base, utils.report_formatter)

## Tested Configurations

| Platform | OS Version | vPC Domain | Test Date | Result |
|----------|------------|------------|-----------|--------|
| Cisco NX-OS | 9.3(5) | Domain 1 | 2026-04-23 | ✅ Pass |
| Cisco NX-OS | 7.0(3) | Domain 100 | 2026-04-23 | ✅ Pass |

## Verification Commands

The plugin executes the following verification commands on NX-OS:

1. `show vpc peer-link` - Verify peer-link status
2. `show vpc role` - Verify vPC role
3. `show vpc consistency-parameters` - Verify Type-1 consistency
4. `show vpc consistency-parameters type-2` - Verify Type-2 consistency
5. `show vpc` - Verify per-vlan consistency
6. `show vlan brief` - Verify VLAN consistency
7. `show vpc` - Verify vPC consistency
8. `show cdp neighbors` - Verify CDP neighbors
9. `show interface brief` - Verify port-channel members
10. `show vpc statistics` - Verify vPC statistics
