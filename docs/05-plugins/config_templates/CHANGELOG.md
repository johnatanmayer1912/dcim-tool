# Changelog — Template-Based Configuration Generator Plugin

# Purpose
Maintains detailed change records of all revisions made to the Template-Based Configuration Generator plugin.

# Scope
Comprehensive historical ledger of modifications.

---

## [1.0.0] - 2026-05-26
### Added
- First public release of `config_templates` plugin.
- Added bootstrapped templates: `cisco_ios_ntp.j2`, `cisco_ios_syslog.j2`, and `juniper_junos_ntp.j2`.
- Built regex dynamic variable parser (`extract_template_variables()`).
- Added multi-environment Jinja2 renderer with raw regex string-replacement fallback mechanism.
- Created report generation and visual preview formatting layout.
