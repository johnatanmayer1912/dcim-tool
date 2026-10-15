# Platform Compatibility: base_template

**Plugin Version:** 1.0.0  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Supported Platforms

This plugin is designed to work with the following network device platforms:

| Vendor | Platform | Minimum Version | Maximum Tested | Status |
|--------|----------|----------------|----------------|--------|
| Cisco | IOS | 12.2 | 17.12 | ✅ Supported |
| Cisco | IOS-XE | 3.6 | 17.12 | ✅ Supported |
| Cisco | NXOS | 7.0 | 10.2 | ✅ Supported |
| Juniper | JunOS | 12.1 | 21.4 | ✅ Supported |

---

## Platform-Specific Features

### Cisco IOS / IOS-XE

**Supported Features:**
- ✅ Full VLAN command support
- ✅ Hostname detection via multiple methods
- ✅ Connection with enable password
- ✅ Error handling for privilege levels

**Command Fallbacks:**
1. `show run | inc hostname`
2. `show hostname`
3. `show ver | inc hostname`

**Known Limitations:**
- Older IOS 12.2 may not support all pipe filters
- Some commands may require enable mode

**Tested Versions:**
- 12.2(55)SE
- 15.2(7)E4
- 15.8(3)M8
- 16.12.1s
- 17.3.4
- 17.12.1

### Cisco NXOS

**Supported Features:**
- ✅ NXOS-specific VLAN commands
- ✅ Modern CLI interface support
- ✅ Enhanced error messages

**Command Variations:**
1. `show clock`
2. `show vlan brief`

**Tested Versions:**
- 7.0(3)I7(8)
- 9.2(4)
- 9.3(8)
- 10.2(5)

### Juniper JunOS

**Supported Features:**
- ✅ JunOS structured CLI
- ✅ Configuration mode commands
- ✅ XML/structured output ready

**Command Variations:**
1. `show configuration system host-name`
2. `show system information | match Hostname`

**Tested Versions:**
- 12.1X47-D40
- 15.1X49-D180
- 18.4R3
- 20.4R3
- 21.4R1

---

## Compatibility Matrix

| Feature | IOS 12.2 | IOS 15.x | IOS-XE | NXOS 7.x | NXOS 9.x | JunOS 12.x | JunOS 20.x |
|---------|----------|----------|--------|----------|----------|------------|------------|
| Integer params | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Checkbox params | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dropdown params | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| String params | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Hostname detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Error handling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Command fallbacks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dry-run mode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parallel execution | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ = Fully Supported
⚠️ = Limited Support
❌ = Not Supported

---

## Device Type Mapping

For proper plugin execution, use these exact device_type values in inventory:

| Platform | device_type | Notes |
|----------|-------------|-------|
| Cisco IOS | `cisco_ios` | Standard IOS |
| Cisco IOS-XE | `cisco_xe` | Also accepts `cisco_ios` |
| Cisco NXOS | `cisco_nxos` | Nexus switches |
| Juniper JunOS | `juniper_junos` | All JunOS devices |

---

## Known Platform Issues

### Cisco IOS 12.2
- **Issue:** Limited pipe filter support
- **Workaround:** Plugin uses fallback commands
- **Impact:** Low - alternative commands available

### Cisco IOS 12.4
- **Issue:** Some show commands have different output format
- **Workaround:** Regex patterns handle variations
- **Impact:** Low - parsing is flexible

### Juniper JunOS 12.1
- **Issue:** Some commands require specific privileges
- **Workaround:** Try alternative commands
- **Impact:** Low - multiple command options

---

## Deprecated Platforms

The following platforms are deprecated and may be removed in future versions:

| Platform | Version | Status | Notice |
|----------|---------|--------|--------|
| None | - | - | All current platforms supported |

---

## Future Platform Support

Planned for upcoming versions:

| Platform | Priority | Target Version |
|----------|----------|----------------|
| Arista EOS | Low | TBD |
| HP Comware | Low | TBD |
| Huawei VRP | Low | TBD |

---

## Testing Recommendations

### Minimum Testing Requirements

Before production deployment, test on:
1. Oldest supported version (IOS 12.2, NXOS 7.0, JunOS 12.1)
2. Latest tested version (IOS 17.12, NXOS 10.2, JunOS 21.4)
3. Most common production version in your environment

### Virtual Lab Testing
- Use Cisco CML/VIRL for IOS/NXOS testing
- Use Juniper vMX/vSRX for JunOS testing
- Test with various configuration scenarios

### Physical Device Testing
- Always test on at least one physical device before production
- Test with real network load
- Verify command response times

---

## Reporting Compatibility Issues

If you encounter compatibility issues:

1. Document the exact platform and version
2. Capture the command output that failed
3. Note the expected vs actual behavior
4. Report to: docs/plugins/base_template/KNOWN_ISSUES.md

---

## Version Compatibility

| Plugin Version | Platform Versions Supported | Notes |
|----------------|----------------------------|-------|
| 1.0.0 | IOS 12.2+, NXOS 7.0+, JunOS 12.1+ | Initial release |

---

**For platform-specific troubleshooting, see:**  
**docs/06_TROUBLESHOOTING/PLATFORM_ISSUES.md**
