# Changelog: standards_validator

All notable changes to this plugin will be documented in this file.

## [1.0.0] - 2026-04-28

### Added
- Initial release
- 5 check types: contains, not_contains, regex_match, regex_extract, line_format
- 20+ built-in policies covering Security, NTP, SNMP, Logging, Banner, Naming, AAA
- User-editable YAML policy library (policies/standards.yaml)
- Severity filtering (critical/high/medium/low)
- Category filtering (comma-separated)
- Per-device remediation commands
- Per-device remediation scripts (ready-to-paste)
- Human-readable report (same style as VLAN missing report)
- Multi-platform support: Cisco IOS/NX-OS/XE, Juniper JunOS
- Platform-specific remediation (remediation_juniper field)
- Placeholder detection ({VARIABLE}) with MANUAL ACTION REQUIRED flag
- Fallback to built-in policies when YAML file not found
- Master report integration (plugin_master_report.txt)

---

**Current Version:** 1.0.0
