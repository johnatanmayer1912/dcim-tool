# Plugin: Device Time Check

**Plugin ID:** device_time  
**Current Version:** 1.0.0  
**Category:** Discovery  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Description

Retrieves system time, timezone, and NTP status from network devices. Useful for checking time synchronization across the network.

## Features

- Multi-platform support (Cisco IOS, NXOS, Juniper JunOS)
- NTP synchronization status check
- Command fallback system for older device versions
- Standardized JSON output

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| show_ntp | checkbox | No | True | Also retrieve NTP synchronization status |

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
    "device_time": "2026-04-20 10:00:00",
    "timezone": "UTC",
    "ntp_synced": true,
    "ntp_servers": ["10.1.1.1"],
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
