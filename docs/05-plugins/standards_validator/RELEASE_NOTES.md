# Release Notes: standards_validator

## Version 1.0.0 (2026-04-28)

### Summary
Initial release of the Standards Validator plugin. Compares live device configuration against a user-editable YAML policy library and produces human-readable gap reports with exact remediation commands.

### New Features
- 5 check types covering all common compliance patterns
- 20+ built-in policies (Security, NTP, SNMP, Logging, Banner, Naming, AAA)
- User-editable YAML policy library — no code changes to add standards
- Per-device remediation scripts ready to paste in config mode
- Severity and category filtering for targeted audits
- Multi-platform support with platform-specific remediation commands

### Known Issues
- None at release

### Testing
- Tested on: Cisco IOS 15.8, Cisco NXOS 9.3, Juniper JunOS 20.4
- Test results: [TEST_RESULTS.md](TEST_RESULTS.md)

### QA Sign-off
- [x] Code review completed
- [x] Syntax validation passed
- [x] Plugin loads with 0 errors
- [x] Documentation complete
- [x] Policy file validated
