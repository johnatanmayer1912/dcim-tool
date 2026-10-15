# Plugin: Interface Error Check

**Plugin ID:** interface_errors  
**Current Version:** 1.0.0  
**Category:** Audit  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-20  
**Status:** Active

---

## Description

Retrieves interface error statistics (input/output errors, CRC, giants, runts, etc.). Essential for identifying problematic ports and cabling issues.

## Features

- Multi-platform support (Cisco IOS, NXOS, Juniper JunOS)
- CRC, giants, runts, input/output error detection
- Configurable error threshold filtering
- Interface regex filtering

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| min_errors | integer | No | 1 | Minimum error threshold (0-1000000) |
| interface_filter | string | No | - | Interface filter regex (e.g., Gi\|Te\|Eth) |

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
    "interfaces_with_errors": [
      {"interface": "Gi0/1", "input_errors": 5, "crc": 2}
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
