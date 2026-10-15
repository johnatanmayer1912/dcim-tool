# Network Swiss Tool Pro - Plugin Development Guide

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Mandatory standards and workflows for developing and documenting platform plugins. |
| **Scope** | Code structure, metadata requirements, folder hierarchy, and versioning rules. |
| **Related Documents** | [Plugin System Architecture](plugin-system.md), [Foundation Guide](../02-codebase/foundation.md) |
| **Update Responsibility** | Plugin Platform Lead / Senior Developer |
| **Version Awareness** | v6.9.1 (NOC Dashboard Edition) |

---

## 🚨 MANDATORY REQUIREMENTS (NON-NEGOTIABLE)

### 1. PLUGIN FILE VERSION REQUIREMENTS

Every plugin file MUST contain these EXACT elements:

```python
"""
modules/plugins/YOUR_PLUGIN.py
-------------------------------------
[Brief description of plugin purpose]

VERSION HISTORY (MUST BE MAINTAINED):
- v1.0.0 (2026-04-20): Initial release
- v1.0.1 (2026-04-21): Bug fix for XYZ
- v1.1.0 (2026-04-22): Added ABC feature

RELEASE NOTES:
v1.0.0:
  - Feature 1 description
  - Feature 2 description
  - Known issues: None

v1.0.1:
  - Fixed: Issue with X on Cisco IOS 12.x
  - Changed: Improved error handling

AUTHOR: [Your Name/Team]
REVIEWED BY: [Reviewer Name]
APPROVED FOR: [Environment/Release]
"""

METADATA = {
    "plugin_id": "your_plugin_name",  # REQUIRED: snake_case, unique
    "display_name": "Your Plugin Display Name",  # REQUIRED: Human readable
    "version": "1.0.0",  # REQUIRED: SemVer format (MAJOR.MINOR.PATCH)
    "author": "Your Name/Team",  # REQUIRED
    "category": "Audit|Management|Discovery|Template",  # REQUIRED
    "description": "Detailed description of what this plugin does.",  # REQUIRED
    "min_platform_version": "6.0.0",  # REQUIRED: Minimum platform version
    
    # CHANGELOG in METADATA (MUST BE UPDATED ON EVERY CHANGE)
    "changelog": [
        {"version": "1.0.0", "date": "2026-04-20", "changes": "Initial release"},
        {"version": "1.0.1", "date": "2026-04-21", "changes": "Bug fix for XYZ"}
    ],
    
    # DOCUMENTATION REFERENCES (REQUIRED)
    "documentation": {
        "readme": "docs/plugins/your_plugin_name/README.md",
        "release_notes": "docs/plugins/your_plugin_name/RELEASE_NOTES.md",
        "prompt": "docs/plugins/your_plugin_name/PROMPT.md",
        "versions": "docs/plugins/your_plugin_name/versions/"
    },
    
    "required_params": {
        # ... parameter definitions
    }
}
```

---

## 📁 MANDATORY FOLDER STRUCTURE

For EVERY plugin, this EXACT structure MUST exist:

```
docs/plugins/{plugin_id}/
├── README.md                    # Current version documentation
├── RELEASE_NOTES.md            # All release notes history
├── PROMPT.md                   # Creation/modification instructions
├── CHANGELOG.md               # Detailed changelog
├── TEST_RESULTS.md            # Test results by version
├── COMPATIBILITY.md           # Platform compatibility matrix
├── KNOWN_ISSUES.md           # Current known issues
├── BACKUP_RESTORE.md         # Rollback/recovery procedures
├── versions/                 # ARCHIVED VERSIONS
│   ├── v1.0.0/
│   │   ├── your_plugin_v1.0.0.py      # Exact file backup
│   │   ├── README_v1.0.0.md           # Version-specific docs
│   │   ├── RELEASE_NOTES_v1.0.0.md      # Version-specific notes
│   │   ├── TEST_RESULTS_v1.0.0.md       # Version test results
│   │   └── manifest.json               # Version manifest
│   │
│   ├── v1.0.1/
│   │   ├── your_plugin_v1.0.1.py
│   │   ├── README_v1.0.1.md
│   │   ├── RELEASE_NOTES_v1.0.1.md
│   │   ├── TEST_RESULTS_v1.0.1.md
│   │   └── manifest.json
│   │
│   └── v1.1.0/
│       ├── your_plugin_v1.1.0.py
│       ├── README_v1.1.0.md
│       ├── RELEASE_NOTES_v1.1.0.md
│       ├── TEST_RESULTS_v1.1.0.md
│       └── manifest.json
│
└── archive/                   # DEPRECATED VERSIONS
    ├── v0.9.0/               # Beta/deprecated versions
    └── v0.9.1/
```

----

## 📊 HUMAN-READABLE OUTPUT REQUIREMENT (HARDCODED v6.0)

### All Plugins MUST Generate Readable Reports

**CRITICAL:** All plugins must generate human-readable text reports in addition to JSON output.

#### Why This Matters
- Raw JSON is difficult for humans to read quickly
- Network engineers need clear, scannable output
- Reports should be self-contained and portable
- Visual indicators (✅ ❌ 🔴) speed up analysis

#### Requirements

1. **MUST create formatted text reports** (not JSON dumps)
2. **MUST save to `reports/` folder** with device IP in filename
3. **MUST return report path** in `result_data["report_path"]`
4. **MUST log to master summary** `reports/PLUGIN_EXECUTION_SUMMARY.txt`
5. **MUST use visual indicators:**
   - ✅ Success/OK
   - ❌ Failure/Not Found
   - 🔴 Critical issues
   - 🟠 Errors
   - 🟡 Warnings
   - 🔵 Info

#### Report Filename Format
```
reports/{plugin_id}_{device_ip}_{timestamp}.txt
Example: reports/device_time_192_168_1_1_20260420_120000.txt
```

#### Report Structure Template
```
======================================================================
PLUGIN NAME REPORT
======================================================================

Device Hostname:    switch01
Device IP:          192.168.1.1
Device Type:        cisco_ios
Report Generated:   2026-04-20T12:00:00

----------------------------------------------------------------------
SECTION TITLE
----------------------------------------------------------------------
✅ Status: OK
Key:       Value

======================================================================
END OF REPORT
======================================================================
```

#### Implementation Example
```python
from utils.report_formatter import (
    save_plugin_report,
    append_to_master_report,
    format_device_time_report  # or your plugin's formatter
)

# In your plugin's run() function:
result_data = {
    "true_host": true_host,
    "device_time": time_str,
    # ... other data
}

# Generate human-readable report (REQUIRED)
report_path = save_plugin_report(
    "your_plugin_id",
    host,
    result_data,
    format_your_plugin_report  # Function from report_formatter.py
)
result_data["report_path"] = report_path

# Add to master summary (REQUIRED)
summary = f"Time: {time_str[:20]}..."
append_to_master_report("your_plugin_id", host, "success", summary, report_path)
```

#### Available Format Functions

All formatters are in `utils/report_formatter.py`:

| Function | Plugin | Output Style |
|----------|--------|--------------|
| `format_vlan_audit_report()` | vlan_audit | VLAN table + ID ranges |
| `format_device_time_report()` | device_time | Time + NTP status with icons |
| `format_serial_number_report()` | serial_number | Hardware inventory |
| `format_critical_logs_report()` | critical_logs | Severity summary + log entries |
| `format_interface_errors_report()` | interface_errors | Error counters table |
| `format_environment_status_report()` | environment_status | Health status by component |

#### Creating a New Format Function

If your plugin needs a custom formatter, add it to `utils/report_formatter.py`:

```python
def format_your_plugin_report(data, host):
    """
    Format your plugin results in human-readable format.
    
    Args:
        data: Result dictionary from your plugin
        host: Device IP address
    
    Returns:
        str: Formatted report text
    """
    lines = []
    lines.append("=" * 70)
    lines.append("YOUR PLUGIN REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Device Hostname:    {data.get('true_host', 'N/A')}")
    lines.append(f"Device IP:          {host}")
    lines.append("")
    
    # Your plugin-specific formatting
    lines.append("-" * 70)
    lines.append("RESULTS")
    lines.append("-" * 70)
    lines.append(f"Status: {'✅ OK' if data.get('success') else '❌ FAILED'}")
    
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)
    
    return '\n'.join(lines)
```

#### Best Practices

1. **Use consistent headers** (70 chars wide)
2. **Truncate long values** to prevent line wrapping
3. **Group related data** under section headers
4. **Sort lists/tables** for easier scanning
5. **Include units** for numeric values
6. **Highlight anomalies** with warning icons

----

## 📝 REQUIRED DOCUMENTATION FILES

### 1. README.md (REQUIRED)

```markdown
# Plugin: {display_name}

**Plugin ID:** {plugin_id}  
**Current Version:** {version}  
**Category:** {category}  
**Author:** {author}  
**Last Updated:** {date}  
**Status:** Active/Deprecated/Beta

---

## Description

[Detailed description]

## Features

- Feature 1
- Feature 2
- Feature 3

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| param1 | string | Yes | - | Description |
| param2 | integer | No | 10 | Description |

## Platform Support

| Platform | Minimum Version | Tested | Status |
|----------|----------------|--------|--------|
| Cisco IOS | 12.2 | ✅ | Supported |
| Cisco NXOS | 7.0 | ✅ | Supported |
| Juniper JunOS | 12.1 | ✅ | Supported |

## Return Data

```json
{
  "status": "success",
  "data": {
    "field1": "description",
    "field2": "description"
  }
}
```

## Usage Examples

### Example 1: Basic Usage
```python
# Code example
```

### Example 2: With Parameters
```python
# Code example with parameters
```

## Known Issues

- Issue 1: Description and workaround
- Issue 2: Description and workaround

## See Also

- [Release Notes](../05-plugins/base_template/RELEASE_NOTES.md)
- [Changelog](../05-plugins/base_template/CHANGELOG.md)
- [Test Results](../05-plugins/base_template/TEST_RESULTS.md)
```

### 2. RELEASE_NOTES.md (REQUIRED)

```markdown
# Release Notes: {plugin_id}

## Version 1.1.0 (2026-04-22)

### New Features
- Added support for XYZ
- Improved performance by 50%

### Bug Fixes
- Fixed issue with ABC on Cisco IOS 12.x
- Fixed memory leak in error handling

### Changes
- Updated command syntax for NXOS 10.x
- Deprecated parameter 'old_param', use 'new_param'

### Breaking Changes
- None

### Known Issues
- Issue with very old IOS versions (see #123)

### Testing
- Tested on: IOS 15.8, NXOS 9.3, JunOS 20.4
- Test results: [TEST_RESULTS.md](../05-plugins/base_template/TEST_RESULTS.md)

---

## Version 1.0.1 (2026-04-21)

### Bug Fixes
- Fixed error handling for timeout scenarios

### Changes
- Improved error messages

---

## Version 1.0.0 (2026-04-20)

### Initial Release
- Basic functionality implemented
- Supports Cisco IOS, NXOS, Juniper JunOS
- Parameters: param1, param2, param3

### Known Issues (at release)
- None

### QA Sign-off
- [x] Code review completed
- [x] Unit tests passed
- [x] Integration tests passed
- [x] Documentation complete
- [x] Platform testing complete
```

### 3. PROMPT.md (REQUIRED)

```markdown
# Plugin Prompt: {plugin_id}

## Purpose

[What this plugin does and why it exists]

## Requirements

### Functional Requirements
1. Must support Cisco IOS 12.x+
2. Must support Cisco NXOS 7.x+
3. Must support Juniper JunOS 12.x+
4. Must handle errors gracefully
5. Must return standardized JSON

### Non-Functional Requirements
1. Execution time < 30 seconds per device
2. Must work in parallel execution
3. Must not modify device configuration
4. Must support dry-run mode (if applicable)

### Parameters Required

| Parameter | Type | Description | Validation |
|-----------|------|-------------|------------|
| param1 | string | Description | Required, max 50 chars |
| param2 | integer | Description | 1-4096 range |

## Implementation Notes

### Command Strategy
- Primary command: `show version`
- Fallback 1: `show ver`
- Fallback 2: `show system information`

### Error Handling
- Handle connection timeouts
- Handle privilege level issues
- Handle unsupported commands

### Testing Strategy
1. Test on each supported platform
2. Test with valid and invalid inputs
3. Test error conditions
4. Test parallel execution

## Version History Prompts

### v1.0.0 Creation Prompt
```
Create a plugin that retrieves X from network devices.
Requirements:
- Support IOS, NXOS, JunOS
- Parameter: include_details (boolean)
- Return: JSON with fields...
```

### v1.0.1 Bug Fix Prompt
```
Fix the following issue in {plugin_id}:
- Issue: Timeout on slow devices
- Solution: Add timeout parameter
- Testing: Verify with 10s delay simulation
```

### v1.1.0 Feature Add Prompt
```
Add the following feature to {plugin_id}:
- Feature: Support for additional platforms
- Implementation: Add new command variations
- Testing: Test on new platforms
```
```

### 4. CHANGELOG.md (REQUIRED)

```markdown
# Changelog: {plugin_id}

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Feature X
- Improvement Y

---

## [1.1.0] - 2026-04-22

### Added
- New feature A
- Support for platform B

### Changed
- Improved error handling
- Updated documentation

### Fixed
- Bug with command timeout
- Issue with NXOS 9.x

### Deprecated
- Parameter 'old_name' (use 'new_name')

### Removed
- None

### Security
- None

---

## [1.0.1] - 2026-04-21

### Fixed
- Timeout handling improved
- Error message clarity

---

## [1.0.0] - 2026-04-20

### Added
- Initial release
- Basic functionality
- Platform support: IOS, NXOS, JunOS
```

### 5. TEST_RESULTS.md (REQUIRED)

```markdown
# Test Results: {plugin_id}

## Current Version: 1.1.0

### Test Date: 2026-04-22
### Tester: [Name]
### Status: ✅ PASSED

---

## Unit Tests

| Test | Status | Notes |
|------|--------|-------|
| Import test | ✅ PASS | No import errors |
| Metadata validation | ✅ PASS | All required keys present |
| Parameter validation | ✅ PASS | Types correct |
| Security scan | ✅ PASS | No banned imports |

## Platform Tests

### Cisco IOS 15.8(3)

| Test Case | Result | Notes |
|-----------|--------|-------|
| Basic execution | ✅ PASS | Response time: 2.3s |
| With all parameters | ✅ PASS | All params processed |
| Error handling | ✅ PASS | Graceful failure |
| Empty result | ✅ PASS | Handled correctly |

### Cisco NXOS 9.3(8)

| Test Case | Result | Notes |
|-----------|--------|-------|
| Basic execution | ✅ PASS | Response time: 1.8s |
| With all parameters | ✅ PASS | All params processed |
| Error handling | ✅ PASS | Graceful failure |

### Juniper JunOS 20.4R3

| Test Case | Result | Notes |
|-----------|--------|-------|
| Basic execution | ✅ PASS | Response time: 3.1s |
| With all parameters | ✅ PASS | All params processed |
| Error handling | ✅ PASS | Graceful failure |

## Integration Tests

| Test | Status | Notes |
|------|--------|-------|
| Parallel execution (5 devices) | ✅ PASS | No conflicts |
| Parallel execution (10 devices) | ✅ PASS | No conflicts |
| Registry reload | ✅ PASS | Loads correctly |
| Plugin upload | ✅ PASS | Validates and loads |

## Sign-off

- [x] All unit tests passed
- [x] All platform tests passed
- [x] All integration tests passed
- [x] Documentation updated
- [x] Ready for release
```

### 6. manifest.json (REQUIRED - Generated)

```json
{
  "plugin_id": "your_plugin",
  "version": "1.0.0",
  "created_date": "2026-04-20T10:00:00Z",
  "author": "Developer Name",
  "checksum": "sha256:abc123...",
  "file_size": 12345,
  "lines_of_code": 150,
  "platforms_tested": [
    "cisco_ios_15.8",
    "cisco_nxos_9.3",
    "juniper_junos_20.4"
  ],
  "dependencies": [
    "modules.network_base",
    "datetime"
  ],
  "backwards_compatible": true,
  "requires_platform_update": false,
  "qa_status": "approved",
  "approved_by": "QA Team Lead",
  "approval_date": "2026-04-20"
}
```

---

## 🔨 REQUIRED WORKFLOW

### When Creating NEW Plugin:

1. **Create plugin file** in `modules/plugins/`
2. **Run validation**: `python -m modules.plugins.your_plugin`
3. **Create docs folder**: `docs/plugins/{plugin_id}/`
4. **Create all 6 required docs**
5. **Create version folder**: `docs/plugins/{plugin_id}/versions/v1.0.0/`
6. **Copy all files to version folder**
7. **Generate manifest.json**
8. **Run full test suite**
9. **Get QA sign-off**
10. **Commit with version tag**

### When Updating EXISTING Plugin:

1. **Update version in METADATA** (SemVer rules)
2. **Update docstring** version history
3. **Update CHANGELOG.md**
4. **Update RELEASE_NOTES.md**
5. **Run tests** - Update TEST_RESULTS.md
6. **Create new version folder** `versions/vX.Y.Z/`
7. **Copy updated files to version folder**
8. **Generate new manifest.json**
9. **Update PROMPT.md** with change description
10. **Get QA sign-off**
11. **Commit with new version tag**
12. **Backup previous version** to backups/plugins/

### When Rolling BACK Plugin:

1. **Check version folder**: `docs/plugins/{plugin_id}/versions/vX.Y.Z/`
2. **Verify manifest.json** - Check compatibility
3. **Copy file from version folder** to `modules/plugins/`
4. **Update registry**: Click "Reload Registry" in UI
5. **Verify functionality**
6. **Document rollback** in CHANGELOG.md

---

## 🎯 HARDCODED VERSION RULES

### Semantic Versioning (MUST FOLLOW)

```
Version: MAJOR.MINOR.PATCH

MAJOR (X.0.0):
- Breaking changes
- API changes
- Parameter removal
- Return format changes
- New required dependencies

MINOR (x.Y.0):
- New features
- New parameters (optional)
- New platform support
- Performance improvements
- Non-breaking enhancements

PATCH (x.y.Z):
- Bug fixes
- Security fixes
- Documentation updates
- Error handling improvements
- Logging improvements
```

### Version Update Checklist

**For PATCH (bug fix):**
- [ ] Bug is fixed
- [ ] Tests pass
- [ ] No API changes
- [ ] CHANGELOG.md updated
- [ ] RELEASE_NOTES.md updated

**For MINOR (feature):**
- [ ] Feature works
- [ ] Tests pass
- [ ] Backwards compatible
- [ ] Documentation updated
- [ ] New parameters documented
- [ ] CHANGELOG.md updated
- [ ] RELEASE_NOTES.md updated
- [ ] README.md updated

**For MAJOR (breaking):**
- [ ] All breaking changes documented
- [ ] Migration guide created
- [ ] All tests pass
- [ ] All docs updated
- [ ] QA sign-off obtained
- [ ] User notification prepared
- [ ] Rollback plan documented

---

## ⚠️ NON-COMPLIANCE CONSEQUENCES

Plugins WITHOUT proper documentation:
- ❌ Will NOT be approved for production
- ❌ Will NOT be accepted in plugin registry
- ❌ Will NOT be backed up automatically
- ❌ Will NOT be eligible for rollback support
- ❌ May be removed from system during audits

---

## ✅ VERIFICATION CHECKLIST

Before marking plugin as complete:

- [ ] Plugin file has version in docstring
- [ ] Plugin file has version history
- [ ] Plugin file has release notes
- [ ] METADATA has version field
- [ ] METADATA has changelog array
- [ ] METADATA has documentation references
- [ ] README.md exists and is complete
- [ ] RELEASE_NOTES.md exists and is complete
- [ ] PROMPT.md exists and is complete
- [ ] CHANGELOG.md exists and is complete
- [ ] TEST_RESULTS.md exists and is complete
- [ ] Version folder exists with all files
- [ ] manifest.json generated
- [ ] All files backed up to version folder
- [ ] QA sign-off obtained

---

**END OF MANDATORY REQUIREMENTS**

For questions or clarifications, see:  
- Plugin System Architecture: [plugin-system.md](plugin-system.md)
- Example Plugin: `modules/plugins/base_template.py`
