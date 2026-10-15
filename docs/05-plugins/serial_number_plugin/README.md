# Plugin: Serial Number Inventory

**Plugin ID:** serial_number  
**Current Version:** 1.0.0  
**Category:** Discovery  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Description

Retrieves chassis serial numbers, model numbers, and hardware info. Essential for asset inventory and warranty tracking.

## Features

- Multi-platform support (Cisco IOS, NXOS, Juniper JunOS)
- Chassis and module serial number retrieval
- Model number and hardware version detection
- Software version extraction

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| include_modules | checkbox | No | False | Retrieve line card/module serial numbers (slower) |

## Platform Support

| Platform | Minimum Version | Tested | Status |
|----------|----------------|--------|--------|
| Cisco IOS | 12.2 | ✅ | Supported |
| Cisco IOS-XE | 3.6 | ✅ | Supported |
| Cisco NXOS | 7.0 | ✅ | Supported |
| Juniper JunOS | 12.1 | ✅ | Supported |

## Return Data

```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "chassis_serial": "ABC123456789",
    "model": "C9300-48P",
    "software_version": "17.3.4",
    "modules": [],
    "timestamp": "2026-04-20T10:00:00"
  }
}
```

## Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-20 | Initial release with multi-platform support | Current |

## See Also

- [Release Notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Test Results](TEST_RESULTS.md)
- [Compatibility](COMPATIBILITY.md)

---

**Documentation Status:** ✅ Complete
