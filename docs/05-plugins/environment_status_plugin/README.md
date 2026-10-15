# Plugin: Environment Health Check

**Plugin ID:** environment_status  
**Current Version:** 1.0.0  
**Category:** Discovery  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Description

Retrieves temperature, fan status, and power supply status from devices. Critical for monitoring device health and preventing hardware failures.

## Features

- Multi-platform support (Cisco IOS, NXOS, Juniper JunOS)
- Temperature sensor monitoring
- Fan status checking
- Power supply status
- Alert-only filtering mode

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| alert_only | checkbox | No | False | Only report items with warnings or failures |
| include_temp | checkbox | No | True | Retrieve temperature sensors |

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
    "health_status": "OK",
    "temperature": {"status": "normal", "value": "35C"},
    "fans": [{"status": "OK"}],
    "power_supplies": [{"status": "OK"}],
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
