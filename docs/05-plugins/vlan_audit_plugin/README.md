# Plugin: VLAN Audit

**Plugin ID:** vlan_audit  
**Current Version:** 1.0.0  
**Category:** Audit  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Description

The VLAN Audit plugin discovers and reports all VLANs configured on target network devices. It retrieves VLAN databases from Cisco IOS, NXOS, and Juniper JunOS devices, providing both raw and parsed output for analysis.

This plugin replaces the legacy `modules/vlan_audit.py` with a plugin-compatible version for v6.0.

## Features

- Multi-platform VLAN discovery (IOS, NXOS, JunOS)
- VLAN name and status reporting
- Configurable maximum VLAN display limit
- Detailed or summary output modes
- CSV report generation support

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| include_details | checkbox | No | True | Include VLAN names and status in report |
| max_vlans | integer | No | 50 | Maximum number of VLANs to display (1-1000) |

## Platform Support

| Platform | Minimum Version | Tested | Status |
|----------|----------------|--------|--------|
| Cisco IOS | 12.2 | ⏳ Pending | Planned |
| Cisco NXOS | 7.0 | ⏳ Pending | Planned |
| Juniper JunOS | 12.1 | ⏳ Pending | Planned |

## Return Data

```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "vlan_count": 25,
    "vlans": [
      {"id": 1, "name": "default", "status": "active"},
      {"id": 100, "name": "VLAN0100", "status": "active"}
    ],
    "timestamp": "2026-04-20T10:00:00"
  }
}
```

## Usage Examples

### Example 1: Basic VLAN Discovery
```python
from modules.plugin_registry import get_registry

registry = get_registry()
params = {
    "include_details": True,
    "max_vlans": 50
}

result = registry.execute(
    "vlan_audit",
    device={"host": "192.168.1.1", "device_type": "cisco_ios"},
    credentials={"username": "admin", "password": "secret"},
    params=params,
    config={},
    log_func=print
)
```

### Example 2: Summary Mode
```python
params = {
    "include_details": False,
    "max_vlans": 100
}
# Returns VLAN IDs only, faster execution
```

## Known Issues

- None reported

## Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-20 | Initial release | Current |

## See Also

- [Release Notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Test Results](TEST_RESULTS.md)
- [Compatibility](COMPATIBILITY.md)

---

**Documentation Status:** ✅ Complete

For documentation standards, see:  
`docs/00_MASTER/PLUGIN_DOCUMENTATION_REQUIREMENTS.md`
