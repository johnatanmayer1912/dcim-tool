# Plugin: Base Plugin Template

**Plugin ID:** base_template  
**Current Version:** 1.0.0  
**Category:** Template  
**Author:** Network Swiss Tool Team  
**Last Updated:** 2026-04-20  
**Status:** Active - Reference Implementation

---

## Description

The Base Plugin Template serves as the Golden Standard reference implementation for all Network Swiss Tool Pro v6.0 plugins. It demonstrates proper plugin structure, documentation requirements, and multi-platform command handling.

This template should be copied and modified when creating new plugins to ensure compliance with v6.0 plugin contract and documentation standards.

## Features

- ✅ Complete plugin contract implementation
- ✅ Dynamic form generation (integer, string, checkbox, dropdown)
- ✅ Parameter validation with min/max constraints
- ✅ Multi-platform command fallbacks (IOS, NXOS, JunOS)
- ✅ Proper error handling and logging
- ✅ Safe connection context manager usage
- ✅ Standardized JSON return format
- ✅ Self-validation included

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| target_vlan | integer | Yes | - | Target VLAN ID (1-4094) |
| dry_run | checkbox | No | False | Show what would happen without making changes |
| device_filter | dropdown | No | "All" | Filter devices by type (All, Cisco, Juniper, F5) |

## Platform Support

| Platform | Minimum Version | Tested | Status |
|----------|----------------|--------|--------|
| Cisco IOS | 12.2 | ✅ v1.0.0 | Supported |
| Cisco IOS-XE | 3.6 | ✅ v1.0.0 | Supported |
| Cisco NXOS | 7.0 | ✅ v1.0.0 | Supported |
| Juniper JunOS | 12.1 | ✅ v1.0.0 | Supported |

## Return Data

### JSON Output (API/Programmatic)
```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "vlan_id": "100",
    "vlan_exists": true,
    "dry_run": false,
    "device_type": "cisco_ios",
    "timestamp": "2026-04-20T10:00:00",
    "output_preview": "...",
    "report_path": "reports/base_template_192_168_1_1_20260420_120000.txt"
  }
}
```

### Human-Readable Report Output (REQUIRED)
All plugins generate a human-readable text report saved to the `reports/` folder:

**Filename format:** `reports/{plugin_id}_{device_ip}_{timestamp}.txt`

**Example report content:**
```
======================================================================
BASE TEMPLATE REPORT
======================================================================

Device Hostname:    switch01
Device IP:          192.168.1.1
Device Type:        cisco_ios
Report Generated:   2026-04-20T12:00:00

----------------------------------------------------------------------
VLAN CHECK RESULTS
----------------------------------------------------------------------
VLAN ID:            100
VLAN Status:        ✅ EXISTS
Dry Run Mode:       No

======================================================================
END OF REPORT
======================================================================
```

**Report Features:**
- Clear visual indicators (✅ ❌ 🔴 🟠 🟡 🔵)
- Device identification (hostname, IP, type)
- Timestamp for audit trail
- Formatted sections with headers
- No raw JSON - fully human readable

## Usage Examples

### Example 1: Basic VLAN Check
```python
from modules.plugin_registry import get_registry

registry = get_registry()
params = {
    "target_vlan": 100,
    "dry_run": False,
    "device_filter": "All"
}

result = registry.execute(
    "base_template",
    device={"host": "192.168.1.1", "device_type": "cisco_ios", "group": "Core"},
    credentials={"username": "admin", "password": "secret", "secret": "enable"},
    params=params,
    config={},
    log_func=print
)
```

### Example 2: Dry Run Mode
```python
params = {
    "target_vlan": 200,
    "dry_run": True,  # Will show what would happen
    "device_filter": "Cisco"
}
# Plugin will log but not make changes
```

## Known Issues

- None in current version

## Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-20 | Initial release | Current |

## See Also

- [Release Notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Test Results](TEST_RESULTS.md)
- [Compatibility](COMPATIBILITY.md)
- [Prompt](PROMPT.md)

## Documentation Standards

This plugin follows the mandatory documentation requirements defined in:
`docs/00_MASTER/PLUGIN_DOCUMENTATION_REQUIREMENTS.md`

---

**© 2026 Network Swiss Tool Team**
