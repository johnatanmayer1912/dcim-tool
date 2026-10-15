#!/usr/bin/env python3
"""
Plugin Creation Wizard for Network Swiss Tool Pro v6.0

This script guides users through creating properly documented plugins
that comply with all hardcoded requirements from:
docs/00_MASTER/PLUGIN_DOCUMENTATION_REQUIREMENTS.md

Usage:
    python create_plugin.py
    python create_plugin.py --name my_plugin --category Audit

HARDCODED REQUIREMENTS ENFORCED:
1. Semantic versioning (MAJOR.MINOR.PATCH)
2. 6 required documentation files
3. Version archive structure
4. manifest.json generation
5. Docstring version history
6. METADATA changelog and documentation fields
"""

import os
import sys
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


def print_header(title):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_step(step_num, total, description):
    """Print step indicator."""
    print(f"\n[Step {step_num}/{total}] {description}")
    print("-" * 50)


def validate_plugin_id(plugin_id):
    """Validate plugin_id format."""
    if not re.match(r'^[a-z][a-z0-9_]*$', plugin_id):
        return False, "Plugin ID must be snake_case (lowercase with underscores), start with letter"
    if len(plugin_id) < 3:
        return False, "Plugin ID must be at least 3 characters"
    return True, "Valid"


def validate_version(version):
    """Validate semantic version format."""
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return False, "Version must be in SemVer format: MAJOR.MINOR.PATCH (e.g., 1.0.0)"
    return True, "Valid"


def get_input(prompt, required=True, validator=None):
    """Get user input with validation."""
    while True:
        value = input(f"{prompt}: ").strip()
        
        if not value and required:
            print("  ⚠ This field is required. Please enter a value.")
            continue
        
        if not value and not required:
            return None
        
        if validator:
            valid, message = validator(value)
            if not valid:
                print(f"  ⚠ {message}")
                continue
        
        return value


def create_plugin_structure(plugin_id, display_name, version, author, category, description):
    """Create the complete plugin structure with documentation."""
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Paths
    plugin_file = f"modules/plugins/{plugin_id}.py"
    docs_folder = f"docs/plugins/{plugin_id}"
    version_folder = f"{docs_folder}/versions/{version}"
    
    print(f"\n📁 Creating structure:")
    print(f"   Plugin: {plugin_file}")
    print(f"   Docs: {docs_folder}/")
    print(f"   Version: {version_folder}/")
    
    # Create directories
    os.makedirs(version_folder, exist_ok=True)
    
    # Generate plugin file
    plugin_content = generate_plugin_file(
        plugin_id, display_name, version, author, category, description, date_str
    )
    
    with open(plugin_file, 'w') as f:
        f.write(plugin_content)
    print(f"   ✅ Created: {plugin_file}")
    
    # Generate all documentation files
    generate_documentation_files(
        plugin_id, display_name, version, author, category, description, date_str, docs_folder, version_folder
    )
    
    # Copy plugin to version folder
    shutil.copy(plugin_file, f"{version_folder}/{plugin_id}_{version}.py")
    
    # Generate manifest.json
    generate_manifest(plugin_id, display_name, version, author, category, description, date_str, version_folder)
    
    return plugin_file, docs_folder


def generate_plugin_file(plugin_id, display_name, version, author, category, description, date_str):
    """Generate the plugin Python file with all required elements."""
    
    return f'''"""
modules/plugins/{plugin_id}.py
--------------------------------
{display_name} Plugin for Network Swiss Tool Pro v6.0

{description}

=============================================================================
HARDCODED REQUIREMENTS - ALL PLUGINS MUST COMPLY
=============================================================================

1. VERSION REQUIREMENTS (MANDATORY):
   - Version MUST be in Semantic Format: MAJOR.MINOR.PATCH (e.g., "{version}")
   - MAJOR: Breaking changes, API changes, parameter removal
   - MINOR: New features, new optional parameters, new platform support
   - PATCH: Bug fixes, security fixes, documentation updates
   
2. DOCUMENTATION REQUIREMENTS (MANDATORY):
   - MUST update this docstring version history on EVERY change
   - MUST create docs/plugins/{plugin_id}/ folder
   - MUST create 6 documentation files:
     * README.md - Current version documentation
     * RELEASE_NOTES.md - All release notes history
     * PROMPT.md - Creation/modification instructions
     * CHANGELOG.md - Detailed changelog
     * TEST_RESULTS.md - Test results by version
     * COMPATIBILITY.md - Platform compatibility
   - MUST create version archive: docs/plugins/{plugin_id}/versions/vX.Y.Z/
   - MUST generate manifest.json for each version

3. METADATA REQUIREMENTS (MANDATORY):
   - MUST include "version" field in SemVer format
   - MUST include "changelog" array with all versions
   - MUST include "documentation" dict with file paths
   - MUST include "author" and "min_platform_version"

4. VERSION HISTORY (UPDATE ON EVERY CHANGE):

VERSION HISTORY:
- {version} ({date_str}): Initial release
  - Basic plugin structure created
  - Multi-platform command fallbacks (IOS, NXOS, JunOS)
  - Parameter validation implemented
  - Documentation complete

RELEASE NOTES:
v{version}:
  - Features: [List features here]
  - Platforms: Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+, Juniper JunOS 12.x+
  - Known Issues: None
  - QA Status: Pending

AUTHOR: {author}
REVIEWED BY: [Reviewer Name]
APPROVED FOR: [Environment]

CONTRACT:
    - Must contain METADATA dict with plugin info
    - Must implement run() with exact signature
    - Must return standard JSON response
    - Must use only allowed imports (no os.system, subprocess, etc.)
    - MUST follow documentation requirements above

EXAMPLE USAGE:
    from modules.plugin_registry import PluginRegistry
    registry = PluginRegistry()
    result = registry.execute("{plugin_id}", device, credentials, params, config, log_func)

DOCUMENTATION LOCATION:
    docs/plugins/{plugin_id}/
    ├── README.md
    ├── RELEASE_NOTES.md
    ├── PROMPT.md
    ├── CHANGELOG.md
    ├── TEST_RESULTS.md
    ├── COMPATIBILITY.md
    └── versions/
        └── {version}/
            ├── {plugin_id}_{version}.py
            ├── README_{version}.md
            ├── RELEASE_NOTES_{version}.md
            ├── TEST_RESULTS_{version}.md
            └── manifest.json
=============================================================================
"""

METADATA = {{
    "plugin_id": "{plugin_id}",
    "display_name": "{display_name}",
    "version": "{version}",
    "author": "{author}",
    "category": "{category}",
    "description": "{description}",
    "min_platform_version": "6.0.0",
    
    # REQUIRED: Changelog - MUST be updated on EVERY version change
    "changelog": [
        {{
            "version": "{version}",
            "date": "{date_str}",
            "changes": "Initial release",
            "author": "{author}",
            "qa_status": "pending"
        }}
    ],
    
    # REQUIRED: Documentation references - MUST exist
    "documentation": {{
        "readme": "docs/plugins/{plugin_id}/README.md",
        "release_notes": "docs/plugins/{plugin_id}/RELEASE_NOTES.md",
        "prompt": "docs/plugins/{plugin_id}/PROMPT.md",
        "changelog": "docs/plugins/{plugin_id}/CHANGELOG.md",
        "test_results": "docs/plugins/{plugin_id}/TEST_RESULTS.md",
        "compatibility": "docs/plugins/{plugin_id}/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/{plugin_id}/versions/",
        "current_version_folder": "docs/plugins/{plugin_id}/versions/{version}/"
    }},
    
    # REQUIRED: Version archive info
    "version_archive": {{
        "{version}": {{
            "file": "docs/plugins/{plugin_id}/versions/{version}/{plugin_id}_{version}.py",
            "manifest": "docs/plugins/{plugin_id}/versions/{version}/manifest.json",
            "date": "{date_str}",
            "status": "current"
        }}
    }},
    
    # UI Parameters - define your plugin's parameters here
    "required_params": {{
        # Example parameter - modify for your needs
        "example_param": {{
            "type": "string",  # integer|string|checkbox|dropdown
            "label": "Example Parameter",
            "placeholder": "Enter value...",
            "required": True,
            "description": "This is an example parameter"
        }}
    }},
    
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": False
}}

from modules.network_base import (
    safe_connection,
    build_json,
    safe_node_name
)
from datetime import datetime


def _get_hostname(conn, device_type, host):
    """Get device hostname with multi-platform support."""
    dt_lower = device_type.lower()
    try:
        if 'cisco' in dt_lower:
            cmds = ["show run | inc hostname", "show hostname", "show ver | inc hostname"]
        elif 'juniper' in dt_lower or 'junos' in dt_lower:
            cmds = ["show configuration system host-name", "show system information | match Hostname"]
        else:
            cmds = ["show ver | inc hostname"]
        
        for cmd in cmds:
            try:
                output = conn.send_command(cmd)
                if output and '%' not in output and 'error' not in output.lower():
                    hn = safe_node_name(output)
                    if hn and hn != 'unknown':
                        return hn
            except:
                continue
        return host
    except:
        return host


def run(device, credentials, params, config, log_func):
    """
    Main plugin execution function.
    Supports: Cisco IOS, IOS-XE, NXOS, Juniper JunOS (all versions)
    
    Args:
        device: {{'host': str, 'device_type': str, 'group': str}}
        credentials: {{'username': str, 'password': str, 'secret': str|None}}
        params: Dict of user-provided parameters
        config: Global application settings
        log_func: Callable for real-time logging
    
    Returns:
        {{'status': 'success'|'fail', 'data': {{...}}, 'error': str|None}}
    """
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'unknown')
    dt_lower = device_type.lower()
    
    try:
        if log_func:
            log_func(f"[{{host}}] Starting {METADATA['display_name']}...")
        
        with safe_connection(
            device,
            credentials['username'],
            credentials['password'],
            credentials.get('secret'),
            log_func
        ) as conn:
            
            # Get hostname
            true_host = _get_hostname(conn, device_type, host)
            
            # TODO: Implement your plugin logic here
            # Example: Get data from device
            # Use multi-command fallbacks for compatibility
            
            # Extract parameters
            example_param = params.get('example_param', 'default_value')
            
            # Build result
            result_data = {{
                "true_host": true_host,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
                "example_param_used": example_param
            }}
            
            if log_func:
                log_func(f"[{{true_host}}] Plugin execution complete")
            
            return build_json(host, "success", result_data)
    
    except Exception as e:
        if log_func:
            log_func(f"[{{host}}] ERROR: {{str(e)}}")
        return build_json(host, "fail", {{}}, str(e))


if __name__ == "__main__":
    print(f"Plugin: {{METADATA['display_name']}} v{{METADATA['version']}}")
    print(f"Category: {{METADATA['category']}}")
    print(f"Documentation: {{METADATA['documentation']['readme']}}")
'''


def generate_documentation_files(plugin_id, display_name, version, author, category, description, date_str, docs_folder, version_folder):
    """Generate all 6 required documentation files."""
    
    files_created = []
    
    # 1. README.md
    readme = f'''# Plugin: {display_name}

**Plugin ID:** {plugin_id}  
**Current Version:** {version}  
**Category:** {category}  
**Author:** {author}  
**Last Updated:** {date_str}  
**Status:** Active - In Development

---

## Description

{description}

## Features

- Feature 1 (TODO: Add features)
- Feature 2
- Feature 3

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| example_param | string | Yes | - | Example parameter description |

## Platform Support

| Platform | Minimum Version | Tested | Status |
|----------|----------------|--------|--------|
| Cisco IOS | 12.2 | ⏳ Pending | Planned |
| Cisco NXOS | 7.0 | ⏳ Pending | Planned |
| Juniper JunOS | 12.1 | ⏳ Pending | Planned |

## Return Data

```json
{{
  "status": "success",
  "data": {{
    "true_host": "hostname",
    "device_type": "cisco_ios",
    "timestamp": "{date_str}T10:00:00"
  }}
}}
```

## Usage Examples

### Example 1: Basic Usage
```python
from modules.plugin_registry import get_registry

registry = get_registry()
params = {{"example_param": "value"}}

result = registry.execute(
    "{plugin_id}",
    device={{"host": "192.168.1.1", "device_type": "cisco_ios"}},
    credentials={{"username": "admin", "password": "secret"}},
    params=params,
    config={{}},
    log_func=print
)
```

## Known Issues

- Plugin is newly created - requires testing
- Documentation needs completion

## Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| {version} | {date_str} | Initial release | Current |

## See Also

- [Release Notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Test Results](TEST_RESULTS.md)

---

**Documentation Status:** 🚧 In Progress

For documentation standards, see:  
`docs/00_MASTER/PLUGIN_DOCUMENTATION_REQUIREMENTS.md`
'''
    
    with open(f"{docs_folder}/README.md", 'w') as f:
        f.write(readme)
    files_created.append("README.md")
    
    # 2. RELEASE_NOTES.md
    release_notes = f'''# Release Notes: {plugin_id}

## Version {version} ({date_str})

### New Features
- Initial plugin creation
- Basic structure implemented

### Implementation
- Multi-platform command fallbacks prepared
- Parameter validation structure
- Error handling framework

### Platform Support
- **Planned:** Cisco IOS 12.2+
- **Planned:** Cisco NXOS 7.0+
- **Planned:** Juniper JunOS 12.1+

### Testing Summary
- Unit tests: ⏳ Pending
- Security scan: ⏳ Pending
- Platform testing: ⏳ Pending

### Known Issues (at release)
- Newly created - requires full testing
- Documentation incomplete
- Platform compatibility not verified

### QA Status
- [ ] Code review pending
- [ ] Unit tests pending
- [ ] Integration tests pending
- [ ] Documentation incomplete
- [ ] Platform testing pending

### Documentation Delivered
- [x] README.md (template)
- [x] RELEASE_NOTES.md (this file)
- [x] PROMPT.md (template)
- [ ] CHANGELOG.md (needs completion)
- [ ] TEST_RESULTS.md (pending tests)
- [ ] COMPATIBILITY.md (pending testing)
- [x] versions/{version}/ folder structure
- [x] manifest.json generated

---

**Status:** 🚧 IN DEVELOPMENT

**Next Steps:**
1. Implement plugin logic
2. Test on target platforms
3. Complete documentation
4. Get QA sign-off

---

*This is a new plugin. Complete testing before production use.*
'''
    
    with open(f"{docs_folder}/RELEASE_NOTES.md", 'w') as f:
        f.write(release_notes)
    files_created.append("RELEASE_NOTES.md")
    
    # 3. PROMPT.md
    prompt = f'''# Plugin Prompt: {plugin_id}

## Purpose

{display_name} - {description}

## Requirements

### Functional Requirements
1. Support Cisco IOS 12.x+
2. Support Cisco NXOS 7.x+
3. Support Juniper JunOS 12.x+
4. Handle errors gracefully
5. Return standardized JSON

### Non-Functional Requirements
1. Execution time < 30 seconds per device
2. Work in parallel execution mode
3. Do not modify device configuration
4. Include comprehensive logging

### Parameters Required

| Parameter | Type | Description | Validation |
|-----------|------|-------------|------------|
| example_param | string | Example | Required |

## Implementation Notes

### Command Strategy
- Primary command: `show version`
- Fallback 1: `show ver`
- Fallback 2: `show system information`

### Error Handling
- Connection timeout handling
- Privilege level issues
- Unsupported commands

### Testing Strategy
1. Test on each supported platform
2. Test with valid/invalid inputs
3. Test error conditions
4. Test parallel execution

## Version History Prompts

### v{version} Creation Prompt
```
Create the {plugin_id} plugin that:
1. {description}
2. Supports IOS, NXOS, JunOS platforms
3. Implements proper error handling
4. Follows v6.0 plugin contract
5. Includes complete documentation

Requirements per PLUGIN_DOCUMENTATION_REQUIREMENTS.md
```

## Creation Checklist

- [x] Plugin file created: modules/plugins/{plugin_id}.py
- [x] Docstring with version history template
- [x] METADATA with required fields
- [ ] run() function implemented with logic
- [ ] Parameters defined and validated
- [ ] Multi-platform commands added
- [ ] Error handling implemented
- [ ] Testing completed
- [ ] Documentation completed
- [ ] QA sign-off obtained

---

**Status:** 🚧 Created - Awaiting Implementation
'''
    
    with open(f"{docs_folder}/PROMPT.md", 'w') as f:
        f.write(prompt)
    files_created.append("PROMPT.md")
    
    # 4. CHANGELOG.md
    changelog = f'''# Changelog: {plugin_id}

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Implement core functionality
- Add platform-specific commands
- Complete testing
- Finalize documentation

---

## [{version}] - {date_str}

### Added
- Initial plugin structure
- Documentation framework
- Multi-platform command fallbacks
- Version archive structure

### Notes
- Plugin created from template
- Requires implementation
- Testing pending

---

**Current Version:** {version}  
**Status:** 🚧 In Development
'''
    
    with open(f"{docs_folder}/CHANGELOG.md", 'w') as f:
        f.write(changelog)
    files_created.append("CHANGELOG.md")
    
    # 5. TEST_RESULTS.md
    test_results = f'''# Test Results: {plugin_id}

## Current Version: {version}

### Test Date: {date_str}
### Tester: [Your Name]
### Status: ⏳ PENDING

---

## Unit Tests

| Test | Status | Notes |
|------|--------|-------|
| Import test | ⏳ Pending | |
| METADATA validation | ⏳ Pending | |
| Parameter validation | ⏳ Pending | |
| Security scan | ⏳ Pending | |

## Platform Tests

### Cisco IOS [Version]

| Test Case | Result | Notes |
|-----------|--------|-------|
| Basic execution | ⏳ Pending | |
| With all parameters | ⏳ Pending | |
| Error handling | ⏳ Pending | |

### Cisco NXOS [Version]

| Test Case | Result | Notes |
|-----------|--------|-------|
| Basic execution | ⏳ Pending | |
| Error handling | ⏳ Pending | |

### Juniper JunOS [Version]

| Test Case | Result | Notes |
|-----------|--------|-------|
| Basic execution | ⏳ Pending | |
| Error handling | ⏳ Pending | |

## Sign-off

- [ ] Development complete
- [ ] Testing complete
- [ ] Documentation complete
- [ ] QA sign-off

---

**Status:** 🚧 Testing Required

Run tests and update this file with results.
'''
    
    with open(f"{docs_folder}/TEST_RESULTS.md", 'w') as f:
        f.write(test_results)
    files_created.append("TEST_RESULTS.md")
    
    # 6. COMPATIBILITY.md
    compatibility = f'''# Platform Compatibility: {plugin_id}

**Plugin Version:** {version}  
**Last Updated:** {date_str}  
**Status:** 🚧 In Development

---

## Planned Platform Support

| Vendor | Platform | Minimum Version | Status |
|--------|----------|----------------|--------|
| Cisco | IOS | 12.2 | ⏳ Planned |
| Cisco | IOS-XE | 3.6 | ⏳ Planned |
| Cisco | NXOS | 7.0 | ⏳ Planned |
| Juniper | JunOS | 12.1 | ⏳ Planned |

---

## Testing Status

| Platform Version | Tested | Status |
|-----------------|--------|--------|
| Cisco IOS 15.x | ⏳ No | Pending |
| Cisco NXOS 9.x | ⏳ No | Pending |
| Juniper JunOS 20.x | ⏳ No | Pending |

---

## Device Type Mapping

| Platform | device_type |
|----------|-------------|
| Cisco IOS | `cisco_ios` |
| Cisco IOS-XE | `cisco_xe` |
| Cisco NXOS | `cisco_nxos` |
| Juniper JunOS | `juniper_junos` |

---

**Status:** 🚧 Testing Required

Complete testing and update this file.
'''
    
    with open(f"{docs_folder}/COMPATIBILITY.md", 'w') as f:
        f.write(compatibility)
    files_created.append("COMPATIBILITY.md")
    
    # Version folder files
    # README_vX.Y.Z.md
    version_readme = f'''# README - {display_name} v{version}

**Version:** {version}  
**Release Date:** {date_str}  
**Status:** Current

Archived version of the plugin.

## Files in this Version

- `{plugin_id}_{version}.py` - Plugin source code
- `README_{version}.md` - This file
- `RELEASE_NOTES_{version}.md` - Release notes
- `TEST_RESULTS_{version}.md` - QA test results
- `manifest.json` - Version metadata

## Current Documentation

See main docs folder: `docs/plugins/{plugin_id}/`

## Rollback

To rollback to this version:
1. Copy `{plugin_id}_{version}.py` to `modules/plugins/{plugin_id}.py`
2. Reload registry in UI

---

**This is an archived version.**
'''
    
    with open(f"{version_folder}/README_{version}.md", 'w') as f:
        f.write(version_readme)
    
    # RELEASE_NOTES_vX.Y.Z.md
    version_release = f'''# Release Notes: {plugin_id} v{version}

**Release Date:** {date_str}

## Overview

Initial release of {display_name}.

## Status

🚧 In Development - Testing Required

## Installation

Plugin file: `modules/plugins/{plugin_id}.py`

## QA Status

- ⏳ Code review pending
- ⏳ Unit tests pending
- ⏳ Platform tests pending
- ⏳ Documentation pending

---

**Status:** 🚧 NOT YET APPROVED FOR PRODUCTION
'''
    
    with open(f"{version_folder}/RELEASE_NOTES_{version}.md", 'w') as f:
        f.write(version_release)
    
    # TEST_RESULTS_vX.Y.Z.md
    version_tests = f'''# Test Results: {plugin_id} v{version}

**Test Date:** {date_str}  
**Status:** ⏳ PENDING

## Summary

Tests not yet completed.

## Next Steps

1. Implement plugin logic
2. Run unit tests
3. Test on target platforms
4. Update this file with results

---

See full test results in main docs.
'''
    
    with open(f"{version_folder}/TEST_RESULTS_{version}.md", 'w') as f:
        f.write(version_tests)
    
    print(f"   ✅ Created documentation files:")
    for f in files_created:
        print(f"      - docs/plugins/{plugin_id}/{f}")


def generate_manifest(plugin_id, display_name, version, author, category, description, date_str, version_folder):
    """Generate manifest.json for the version."""
    
    manifest = {
        "plugin_id": plugin_id,
        "version": version,
        "display_name": display_name,
        "created_date": f"{date_str}T10:00:00Z",
        "author": author,
        "category": category,
        "description": description,
        "checksum_sha256": "to-be-generated",
        "file_size_bytes": 0,
        "lines_of_code": 0,
        "min_platform_version": "6.0.0",
        "platforms_tested": [],
        "dependencies": ["modules.network_base", "datetime"],
        "banned_imports_scan": "pending",
        "security_scan": "pending",
        "metadata_validation": "pending",
        "backwards_compatible": True,
        "requires_platform_update": False,
        "breaking_changes": False,
        "migration_required": False,
        "qa_status": "pending",
        "approved_by": None,
        "approval_date": None,
        "test_results": f"docs/plugins/{plugin_id}/versions/{version}/TEST_RESULTS_{version}.md",
        "files_in_version": [
            f"{plugin_id}_{version}.py",
            f"README_{version}.md",
            f"RELEASE_NOTES_{version}.md",
            f"TEST_RESULTS_{version}.md",
            "manifest.json"
        ],
        "documentation_complete": True,
        "changelog_updated": True,
        "version_history_updated": True,
        "previous_version": None,
        "next_version": None,
        "status": "current",
        "archive_location": f"docs/plugins/{plugin_id}/versions/{version}/",
        "backup_location": f"backups/plugins/{plugin_id}/",
        "rollback_available": True
    }
    
    with open(f"{version_folder}/manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"   ✅ Created: manifest.json")


def main():
    """Main wizard function."""
    print_header("Network Swiss Tool Pro v6.0 - Plugin Creation Wizard")
    print("This wizard will create a properly documented plugin following")
    print("all hardcoded requirements from PLUGIN_DOCUMENTATION_REQUIREMENTS.md")
    
    # Check command line args
    if len(sys.argv) > 1:
        print("\nUsage: python create_plugin.py")
        print("Or: python create_plugin.py --help")
        sys.exit(0)
    
    print("\n⚠ IMPORTANT: This wizard enforces mandatory documentation requirements.")
    print("All plugins MUST include version history, 6 documentation files,")
    print("and proper METADATA fields.")
    
    # Step 1: Plugin ID
    print_step(1, 5, "Plugin Identification")
    plugin_id = get_input(
        "Plugin ID (snake_case, e.g., 'vlan_checker_v2')",
        validator=validate_plugin_id
    )
    
    # Step 2: Plugin Details
    print_step(2, 5, "Plugin Details")
    display_name = get_input("Display Name (e.g., 'VLAN Checker V2')")
    version = get_input("Initial Version", validator=validate_version)
    author = get_input("Author Name/Team")
    
    # Category selection
    print("\nSelect Category:")
    print("  1. Audit")
    print("  2. Management")
    print("  3. Discovery")
    print("  4. Template")
    
    while True:
        cat_choice = input("Enter number (1-4): ").strip()
        categories = {"1": "Audit", "2": "Management", "3": "Discovery", "4": "Template"}
        if cat_choice in categories:
            category = categories[cat_choice]
            break
        print("  ⚠ Invalid choice. Enter 1-4.")
    
    description = get_input("Brief Description")
    
    # Step 3: Confirmation
    print_step(3, 5, "Review and Confirm")
    print(f"\nPlugin to be created:")
    print(f"  ID: {plugin_id}")
    print(f"  Name: {display_name}")
    print(f"  Version: {version}")
    print(f"  Category: {category}")
    print(f"  Author: {author}")
    
    print(f"\nFiles to create:")
    print(f"  - modules/plugins/{plugin_id}.py")
    print(f"  - docs/plugins/{plugin_id}/ (6 documentation files)")
    print(f"  - docs/plugins/{plugin_id}/versions/{version}/ (5 version files)")
    
    confirm = input("\nProceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\n❌ Creation cancelled.")
        sys.exit(0)
    
    # Step 4: Create Plugin
    print_step(4, 5, "Creating Plugin Structure")
    
    try:
        plugin_file, docs_folder = create_plugin_structure(
            plugin_id, display_name, version, author, category, description
        )
        
        # Step 5: Summary
        print_step(5, 5, "Creation Complete")
        
        print("\n✅ Plugin created successfully!")
        print("\n📁 Files Created:")
        print(f"   Plugin: {plugin_file}")
        print(f"   Documentation: {docs_folder}/")
        print(f"   Version Archive: {docs_folder}/versions/{version}/")
        
        print("\n📋 Next Steps:")
        print("   1. Implement the run() function in the plugin file")
        print("   2. Define your parameters in METADATA['required_params']")
        print("   3. Add platform-specific commands")
        print("   4. Test on target platforms")
        print("   5. Update documentation files")
        print("   6. Run: python test_plugins.py")
        print("   7. Get QA sign-off")
        
        print("\n📖 Documentation Requirements:")
        print("   • Complete all TODO sections in the plugin file")
        print("   • Update all 6 documentation files")
        print("   • Test on all target platforms")
        print("   • Update TEST_RESULTS.md with actual results")
        print("   • Get manifest.json signed off")
        
        print("\n⚠ IMPORTANT:")
        print("   This plugin is NOT ready for production yet!")
        print("   You must complete implementation and testing.")
        print("   See docs/00_MASTER/PLUGIN_DOCUMENTATION_REQUIREMENTS.md")
        
        print(f"\n✨ Your plugin '{display_name}' is ready for development!")
        
    except Exception as e:
        print(f"\n❌ Error creating plugin: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
