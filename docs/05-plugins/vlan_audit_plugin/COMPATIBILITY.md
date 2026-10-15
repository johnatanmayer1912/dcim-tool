# Platform Compatibility: vlan_audit

**Plugin Version:** 1.0.0  
**Last Updated:** 2026-04-20  
**Status:** 🚧 In Development

---

## Planned Platform Support

| Vendor | Platform | Minimum Version | Status |
|--------|----------|----------------|--------|
| Cisco | IOS | 12.2 | ⏳ Planned |
| Cisco | IOS-XE | 3.6 | ⏳ Planned |
| Cisco | NXOS | 7.0 | ⏳ Planned |
| Juniper | JunOS | 12.1 | ⏳ Planned |

---

## Command Mapping

| Platform | Primary Command | Fallback |
|----------|----------------|----------|
| Cisco IOS | `show vlan brief` | `show vlan` |
| Cisco NXOS | `show vlan brief` | `show vlan` |
| Juniper JunOS | `show vlans` | - |

---

## Device Type Mapping

| Platform | device_type |
|----------|-------------|
| Cisco IOS | `cisco_ios` |
| Cisco IOS-XE | `cisco_xe` |
| Cisco NXOS | `cisco_nxos` |
| Juniper JunOS | `juniper_junos` |

---

**Status:** 🚧 Testing Required

Complete testing and update this file.
