# Plugin: Critical Log Scanner

**Plugin ID:** critical_logs  
**Current Version:** 1.0.0  
**Category:** Audit  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Description

Retrieves recent syslog entries, filtering for critical/error/warning messages. Useful for troubleshooting and proactive monitoring.

## Features

- Multi-platform support (Cisco IOS, NXOS, Juniper JunOS)
- Severity-based filtering (EMERGENCY to WARNING)
- Configurable log entry count
- Multiple log command fallbacks

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| log_count | integer | No | 20 | Number of log entries to retrieve (5-100) |
| severity_filter | dropdown | No | ERROR | Minimum severity level (ALL, EMERGENCY, ALERT, CRITICAL, ERROR, WARNING) |

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
    "log_count": 20,
    "filtered_entries": [
      {"severity": "ERROR", "message": "Interface down", "timestamp": "..."}
    ],
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
