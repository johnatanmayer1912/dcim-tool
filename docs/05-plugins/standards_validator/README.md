# Plugin: Standards Validator

**Plugin ID:** standards_validator  
**Current Version:** 1.0.0  
**Category:** Compliance  
**Author:** Network Swiss Tool  
**Last Updated:** 2026-04-28  
**Status:** Active

---

## Description

Compares live device configuration against your organization's standards policy library (YAML file). Reports violations with exact remediation commands per device. Read-only — never pushes changes.

## Features

- **User-editable policy library** — no code changes needed to add new standards
- **Multi-platform support** — Cisco IOS/NX-OS/XE, Juniper JunOS
- **5 check types** — contains, not_contains, regex_match, regex_extract, line_format
- **Severity filtering** — critical, high, medium, low
- **Category filtering** — Security, NTP, SNMP, Naming, Banner, etc.
- **Remediation commands** — exact commands to fix each violation
- **Per-device remediation scripts** — ready-to-paste fix scripts
- **Human-readable reports** — same style as VLAN missing report
- **CSV export** — compliance matrix for spreadsheet analysis

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| policy_file | string | No | policies/standards.yaml | Path to YAML policy library |
| severity_filter | dropdown | No | all | Minimum severity: all/low/medium/high/critical |
| category_filter | string | No | (blank) | Comma-separated categories (Security, NTP, etc.) |
| generate_remediation_script | checkbox | No | True | Write per-device fix scripts |

## Platform Support

| Platform | Minimum Version | Tested | Status |
|----------|----------------|--------|--------|
| Cisco IOS | 12.2 | ✅ | Supported |
| Cisco IOS-XE | 3.6 | ✅ | Supported |
| Cisco NXOS | 7.0 | ✅ | Supported |
| Juniper JunOS | 12.1 | ✅ | Supported |

## Policy File Format

See `policies/standards.yaml` for the full policy library with inline documentation.

Example policy:
```yaml
- id: telnet_disabled
  category: Security
  description: "Telnet must be disabled on all VTY lines"
  severity: critical
  platforms: [cisco_ios, cisco_nxos]
  check_command: "show line vty 0 4"
  check_type: not_contains
  pattern: "transport input telnet"
  remediation: |
    line vty 0 4
     transport input ssh
```

## Return Data

```json
{
  "status": "success",
  "data": {
    "true_host": "switch01",
    "compliant": false,
    "violations": [
      {
        "policy_id": "telnet_disabled",
        "description": "Telnet must be disabled",
        "severity": "critical",
        "current": "transport input telnet ssh",
        "expected": "Must NOT contain: transport input telnet",
        "remediation": "line vty 0 4\n transport input ssh"
      }
    ],
    "policies_checked": 18,
    "skipped": 2,
    "report_path": "reports/compliance/standards_10.1.1.1_20260428_143022.txt"
  }
}
```

## Output Files

| File | Description |
|------|-------------|
| `reports/compliance/standards_{host}_{ts}.txt` | Human-readable report per device |
| `reports/compliance/remediation_{host}_{ts}.txt` | Ready-to-paste fix script per device |
| `plugin_master_report.txt` | One-line summary per device |

## Usage Example

### Basic Usage
1. Open Plugin Tools tab
2. Select "Standards Validator"
3. Leave policy_file blank (uses default)
4. Click "Execute Plugin"
5. Review the report for each device

### Filter by Severity
1. Set severity_filter = "critical"
2. Only critical violations will be checked
3. Faster scan, focused on security risks

### Filter by Category
1. Set category_filter = "Security, NTP"
2. Only Security and NTP policies will be checked
3. Useful for targeted audits

### Custom Policy File
1. Create `policies/datacenter.yaml` with site-specific standards
2. Set policy_file = "policies/datacenter.yaml"
3. Run the plugin
4. Policies from your custom file will be used

## Adding New Policies

Edit `policies/standards.yaml` and add a new block:

```yaml
- id: my_new_standard
  category: MyCategory
  description: "Description of what must be true"
  severity: medium
  platforms: [cisco_ios]
  check_command: "show running-config | section my-feature"
  check_type: contains
  pattern: "my-feature enabled"
  remediation: "my-feature enable"
```

No code changes required. The plugin reloads the YAML on every run.

## Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-28 | Initial release with 20+ built-in policies | Current |

## See Also

- [Release Notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Test Results](TEST_RESULTS.md)
- [Compatibility](COMPATIBILITY.md)
- [Policy Library](../../../policies/standards.yaml)

---

**Documentation Status:** ✅ Complete
