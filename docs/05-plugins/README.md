# Plugin Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.1 |
| **Status** | active |
| **Owner** | Lead Developer (R-ENG) |
| **Last Updated** | 2026-06-04 |

---

## Purpose

This folder contains canonical plugin documentation for Network Swiss Tool Pro. Each plugin has its own subdirectory with comprehensive documentation including README, PROMPT, CHANGELOG, COMPATIBILITY, TEST_RESULTS, and RELEASE_NOTES.

---

## Folder Structure

```
plugins/
├── base_template/
├── config_templates/
├── critical_logs_plugin/
├── device_time_plugin/
├── environment_status_plugin/
├── interface_errors_plugin/
├── interface_manager/
├── network_discovery/
├── serial_number_plugin/
├── standards_validator/
├── stp_topology_visualizer/
├── unused_trunk_pruner/
├── vlan_audit_plugin/
└── vpc_domain/
```

---

## Plugin Documentation Structure

Each plugin subdirectory contains:

| Document | Purpose |
|----------|---------|
| README.md | Plugin overview and usage |
| PROMPT.md | Original creation prompt |
| CHANGELOG.md | Version history |
| COMPATIBILITY.md | Platform compatibility |
| TEST_RESULTS.md | Test results |
| RELEASE_NOTES.md | Release notes |

---

## Navigation

### For Plugin Developers

Start here:
1. **04-automation/plugin-development-guide.md** - Plugin development guide
2. **04-automation/plugin-development-template.md** - Plugin development template
3. Individual plugin README.md files

### For Plugin Users

Start here:
1. Individual plugin README.md files
2. Individual plugin COMPATIBILITY.md files
3. Individual plugin RELEASE_NOTES.md files

---

## Cross-References

- References: 04-automation/plugin-development-guide.md
- Referenced by: 04-automation/installed-plugins/README.md (redirect)

---

## Maintenance

### Update Triggers

Update plugin documentation when:
- Plugin is added or removed
- Plugin version changes
- Plugin compatibility changes
- Plugin test results change
- Plugin release notes are added

### Validation

Validate plugin documentation against:
- 04-automation/plugin-development-guide.md (consistency)
- Actual plugin code (accuracy)
- DOCUMENTATION_VALIDATION_CHECKLIST.md (quality standards)

---

## See Also

- **DOCUMENTATION_MASTER_INDEX.md** - Master documentation index
- **DOCUMENTATION_MAINTENANCE_GUIDE.md** - Documentation maintenance guide
- **04-automation/plugin-development-guide.md** - Plugin development guide
