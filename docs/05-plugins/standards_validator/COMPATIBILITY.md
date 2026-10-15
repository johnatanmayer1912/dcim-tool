# Compatibility: standards_validator

## Platform Support Matrix

| Platform | Min Version | Tested | Status | Notes |
|----------|-------------|--------|--------|-------|
| Cisco IOS | 12.2 | ✅ | Supported | Full policy set |
| Cisco IOS-XE | 3.6 | ✅ | Supported | Full policy set |
| Cisco NXOS | 7.0 | ✅ | Supported | Full policy set |
| Juniper JunOS | 12.1 | ✅ | Supported | Juniper-specific remediation |
| HP Comware | 7.x | ⚠️ | Partial | Custom policies only |
| Arista EOS | 4.x | ⚠️ | Partial | Custom policies only |

## Policy Compatibility

Policies with a `platforms` list only run on matching devices. Policies without a `platforms` field run on all devices.

## Python Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| pyyaml | ≥6.0 | Policy file parsing |
| netmiko | ≥4.1 | SSH connectivity |

PyYAML is already included in requirements.txt. If not available, the plugin falls back to built-in policies.

## Platform Version: 6.5.4+
