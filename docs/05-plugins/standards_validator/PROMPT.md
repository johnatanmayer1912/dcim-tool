# Plugin Prompt: standards_validator

## Purpose
Validate live device configuration against a user-defined YAML policy library. Report violations with exact remediation commands. Read-only.

## Creation Prompt (v1.0.0)
```
Create a plugin called standards_validator that:
1. Loads a YAML policy file (policies/standards.yaml)
2. For each policy: runs check_command, applies check_type logic
3. Reports violations with current value, expected value, remediation commands
4. Generates human-readable report (same style as VLAN missing report)
5. Generates per-device remediation scripts
6. Never pushes changes to devices
```

## Modification Guidelines
- To add a new check type: add a branch in _apply_check()
- To add new built-in policies: add to _builtin_policies()
- To change report format: modify _format_standards_report()
- Policy YAML changes require no code changes
