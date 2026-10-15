# Plugin Prompt: base_template

## Purpose

Create a reference implementation (template) that demonstrates the proper structure, documentation, and functionality requirements for all Network Swiss Tool Pro v6.0 plugins. This template will be copied and modified to create new plugins.

## Requirements

### Functional Requirements
1. Must support dynamic UI form generation
2. Must implement all 4 parameter types (integer, string, checkbox, dropdown)
3. Must support Cisco IOS 12.x+, IOS-XE 3.x+, NXOS 7.x+
4. Must support Juniper JunOS 12.x+
5. Must handle connection errors gracefully
6. Must return standardized JSON response
7. Must include self-validation function
8. Must implement proper logging

### Non-Functional Requirements
1. Execution time < 30 seconds per device
2. Must work in parallel execution mode
3. Must not modify device configuration (read-only)
4. Must support dry-run mode demonstration
5. Must include comprehensive documentation

### Documentation Requirements (HARDCODED)
1. Docstring with version history and release notes
2. METADATA with changelog array
3. METADATA with documentation references
4. METADATA with version_archive
5. 6 documentation files in docs/plugins/{plugin_id}/
6. Version folder with archived files
7. manifest.json for each version

### Parameters Required

| Parameter | Type | Description | Validation |
|-----------|------|-------------|------------|
| target_vlan | integer | VLAN ID to check | Required, min=1, max=4094 |
| dry_run | checkbox | Simulation mode | Default: False |
| device_filter | dropdown | Device type filter | Options: All, Cisco, Juniper, F5 |

## Implementation Notes

### Command Strategy (Multi-Platform)
- **Hostname detection**: Try multiple commands for different platforms
  - IOS: `show run | inc hostname`, `show hostname`
  - NXOS: `show hostname`
  - JunOS: `show configuration system host-name`
  
- **VLAN commands**: Platform-specific variations
  - IOS: `show vlan id {vlan}`
  - JunOS: `show vlans {vlan}`

### Error Handling
- Use safe_connection context manager
- Try/except for each command
- Fallback to next command on failure
- Return standardized error JSON
- Log all operations via log_func

### Return Data Structure
```json
{
  "status": "success|fail",
  "data": {
    "true_host": "device-hostname",
    "vlan_id": integer,
    "vlan_exists": boolean,
    "dry_run": boolean,
    "device_type": "string",
    "timestamp": "ISO8601",
    "output_preview": "truncated output"
  },
  "error": "error message or null"
}
```

## Version History Prompts

### v1.0.0 Creation Prompt
```
Create the base_template.py plugin that:
1. Serves as reference implementation for v6.0 plugins
2. Implements full plugin contract (METADATA, run(), return format)
3. Demonstrates all 4 parameter types (integer, string, checkbox, dropdown)
4. Includes multi-platform command fallbacks for IOS, NXOS, JunOS
5. Has complete documentation (docstring + 6 doc files)
6. Includes self-validation function
7. Uses safe_connection and proper error handling
8. Returns standardized JSON

Documentation requirements per PLUGIN_DOCUMENTATION_REQUIREMENTS.md
```

## Creation Checklist

- [x] Plugin file created: modules/plugins/base_template.py
- [x] Docstring with version history
- [x] METADATA with all required fields
- [x] Changelog array in METADATA
- [x] Documentation references in METADATA
- [x] Version archive info in METADATA
- [x] run() function with exact signature
- [x] Parameter validation
- [x] Multi-platform commands
- [x] Error handling
- [x] Standardized return format
- [x] Self-validation function
- [x] README.md created
- [x] RELEASE_NOTES.md created
- [x] PROMPT.md created
- [x] CHANGELOG.md created
- [x] TEST_RESULTS.md created
- [x] COMPATIBILITY.md created
- [x] versions/v1.0.0/ folder created
- [x] Version files archived
- [x] manifest.json generated
- [x] QA sign-off obtained

## Usage Instructions

### To Create New Plugin from Template:

1. **Copy template file:**
   ```bash
   cp modules/plugins/base_template.py modules/plugins/my_new_plugin.py
   ```

2. **Update plugin_id (must be unique, snake_case):**
   ```python
   METADATA["plugin_id"] = "my_new_plugin"
   ```

3. **Update display_name:**
   ```python
   METADATA["display_name"] = "My New Plugin"
   ```

4. **Update version to 1.0.0:**
   ```python
   METADATA["version"] = "1.0.0"
   ```

5. **Update docstring** with new plugin description and version history

6. **Create documentation folder:**
   ```bash
   mkdir -p docs/plugins/my_new_plugin/versions/v1.0.0
   ```

7. **Copy all 6 doc files and update them**

8. **Implement run() function** with actual plugin logic

9. **Update required_params** for your plugin's parameters

10. **Run validation:**
    ```bash
    python modules/plugins/my_new_plugin.py
    ```

11. **Test on target platforms**

12. **Get QA sign-off**

---

**Template Status:** ✅ COMPLETE AND APPROVED

**For questions:** See PLUGIN_DOCUMENTATION_REQUIREMENTS.md
