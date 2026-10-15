# Root-Level Scripts Documentation

## Overview

This document provides comprehensive documentation for all root-level Python scripts in Network Swiss Tool Pro.

**Generated:** 2026-06-02  
**Purpose:** Operations documentation for development and utility scripts  
**Scripts Location:** Root directory

---

## Script Summary

| Script | Purpose | Status | Dependencies |
|--------|---------|--------|--------------|
| main.py | Legacy main entry point | Deprecated | None |
| create_plugin.py | Plugin scaffolding | Active | None |
| generate_plugin_docs.py | Plugin documentation generation | Active | Jinja2 |
| make_bat.py | Batch file generation | Active | None |
| _prebuild.py | Pre-build checks | Active | None |
| _check_plugin_path.py | Plugin path validation | Active | None |
| _check_yaml.py | YAML validation | Active | PyYAML |
| _cli_diagnostic_server.py | CLI diagnostic server | Active | Flask, SocketIO |
| _fix_bugs.py | Bug fixing script | Development | None |
| _master_qa_test.py | Master QA test suite | Active | pytest |
| _test_v622.py | Version-specific tests | Legacy | pytest |
| create_demo_discovery_map_v7.py | Demo discovery map creation | Active | utils.discovery_graph |
| create_demo_map.py | Demo topology map creation | Active | utils.topo_map_shell |
| create_demo_map_v7.py | Demo topology map v7 | Active | utils.topo_map_shell |
| f5_manager_gui.py | F5 device manager GUI | Active | tkinter |
| test_plugins.py | Plugin testing | Active | modules.plugin_registry |
| test_socketio.py | SocketIO testing | Active | Flask, SocketIO |
| vlan_checker_gui.py | Legacy GUI | Deprecated | tkinter |

---

## main.py

### Purpose
Legacy main entry point for the application (deprecated).

### Status
**Deprecated** - Use `vlan_checker_web.py` instead.

### Usage
```bash
python main.py
```

### Dependencies
None

### Output
Application startup (deprecated)

### Notes
This script is kept for backward compatibility but should not be used. The current application uses `vlan_checker_web.py` as the main entry point.

---

## create_plugin.py

### Purpose
Plugin scaffolding script for creating new plugins.

### Status
**Active** - Used for plugin development.

### Usage
```bash
python create_plugin.py <plugin_name>
```

### Parameters
- `plugin_name`: Name of the plugin to create

### Dependencies
None

### Output
- Creates plugin file in `modules/plugins/<plugin_name>.py`
- Creates plugin METADATA structure
- Creates plugin run() function template

### Example
```bash
python create_plugin.py my_new_plugin
```

### Generated Plugin Structure
```python
METADATA = {
    "plugin_id": "my_new_plugin",
    "display_name": "My New Plugin",
    "version": "1.0.0",
    "author": "Author",
    "category": "Category",
    "description": "Plugin description",
    "min_platform_version": "6.0.0",
    "required_params": {},
    "supports_parallel": True,
    "supports_dry_run": False,
    "modifies_device": False,
    "requires_enable": True,
}

def run(device, credentials, params, config, log_func):
    """
    Execute plugin on device.
    
    Returns:
        JSON response with 'status', 'data', 'error' fields
    """
    # Plugin implementation here
    pass
```

### Notes
- Creates plugin with standard METADATA structure
- Includes run() function template
- Plugin must be manually implemented after scaffolding

---

## generate_plugin_docs.py

### Purpose
Generate documentation for plugins.

### Status
**Active** - Used for plugin documentation.

### Usage
```bash
python generate_plugin_docs.py <plugin_name>
```

### Parameters
- `plugin_name`: Name of the plugin to generate documentation for

### Dependencies
- Jinja2
- utils.report_formatter

### Output
- Creates `docs/plugins/<plugin_name>/README.md`
- Creates `docs/plugins/<plugin_name>/PROMPT.md`
- Creates `docs/plugins/<plugin_name>/CHANGELOG.md`
- Creates `docs/plugins/<plugin_name>/COMPATIBILITY.md`
- Creates `docs/plugins/<plugin_name>/TEST_RESULTS.md`
- Creates `docs/plugins/<plugin_name>/RELEASE_NOTES.md`

### Example
```bash
python generate_plugin_docs.py network_discovery
```

### Notes
- Extracts METADATA from plugin file
- Generates documentation following established patterns
- Documentation must be reviewed and edited after generation

---

## make_bat.py

### Purpose
Generate batch files for Windows.

### Status
**Active** - Used for Windows script generation.

### Usage
```bash
python make_bat.py <script_name>
```

### Parameters
- `script_name`: Name of the script to create batch file for

### Dependencies
None

### Output
- Creates `<script_name>.bat` file

### Example
```bash
python make_bat.py start_app
```

### Generated Batch File
```batch
@echo off
python start_app.py
pause
```

### Notes
- Simple batch file generation
- Includes pause for user to see output
- Useful for creating Windows launchers

---

## _prebuild.py

### Purpose
Pre-build checks and validation.

### Status
**Active** - Used before building EXE.

### Usage
```bash
python _prebuild.py
```

### Dependencies
None

### Output
- Validates build environment
- Checks for required dependencies
- Validates configuration files
- Reports any issues that would prevent build

### Checks Performed
- Python version validation
- Required packages installed
- Configuration files present
- Plugin files present
- Template files present

### Notes
- Run before PyInstaller build
- Helps identify build issues early
- Non-blocking (reports issues but doesn't fail)

---

## _check_plugin_path.py

### Purpose
Check plugin path configuration.

### Status
**Active** - Used for plugin path validation.

### Usage
```bash
python _check_plugin_path.py
```

### Dependencies
None

### Output
- Validates plugin path configuration
- Checks if modules/plugins/ directory exists
- Checks if plugin files are present
- Reports path configuration status

### Notes
- Useful for troubleshooting plugin loading issues
- Validates plugin registry can find plugins

---

## _check_yaml.py

### Purpose
Validate YAML configuration files.

### Status
**Active** - Used for YAML validation.

### Usage
```bash
python _check_yaml.py <yaml_file>
```

### Parameters
- `yaml_file`: Path to YAML file to validate

### Dependencies
- PyYAML

### Output
- Validates YAML syntax
- Reports any syntax errors
- Reports YAML structure

### Example
```bash
python _check_yaml.py policies/standards.yaml
```

### Notes
- Useful for validating policy files
- Checks YAML syntax before use
- Helps identify YAML errors early

---

## _cli_diagnostic_server.py

### Purpose
CLI diagnostic server for troubleshooting.

### Status
**Active** - Used for CLI troubleshooting.

### Usage
```bash
python _cli_diagnostic_server.py
```

### Dependencies
- Flask
- Flask-SocketIO

### Output
- Starts diagnostic server on port 5052
- Provides CLI diagnostic interface
- WebSocket support for real-time diagnostics

### Notes
- Separate from main application
- Used for CLI troubleshooting
- Runs on different port to avoid conflicts

---

## _fix_bugs.py

### Purpose
Bug fixing script (development tool).

### Status
**Development** - Used for bug identification and fixing.

### Usage
```bash
python _fix_bugs.py
```

### Dependencies
None

### Output
- Identifies potential bugs
- Suggests fixes
- Applies automated fixes where possible

### Notes
- Development tool only
- Not used in production
- Helps with code quality

---

## _master_qa_test.py

### Purpose
Master QA test suite.

### Status
**Active** - Used for comprehensive QA testing.

### Usage
```bash
python _master_qa_test.py
```

### Dependencies
- pytest
- modules.plugin_registry
- All operation modules

### Output
- Runs comprehensive QA tests
- Tests plugin loading
- Tests API endpoints
- Tests module functionality
- Generates test report

### Test Categories
- Plugin loading tests
- API endpoint tests
- Module integration tests
- Configuration validation tests
- Error handling tests

### Notes
- Comprehensive test suite
- Should be run before release
- Test results saved to reports/ directory

---

## _test_v622.py

### Purpose
Version 6.2.2 specific tests.

### Status
**Legacy** - Version-specific regression tests.

### Usage
```bash
python _test_v622.py
```

### Dependencies
- pytest

### Output
- Runs v6.2.2 specific tests
- Tests v6.2.2 features
- Regression testing

### Notes
- Legacy script for specific version
- May not be relevant for current version
- Kept for regression testing

---

## create_demo_discovery_map_v7.py

### Purpose
Create demo discovery map for v7.

### Status
**Active** - Used for demo data generation.

### Usage
```bash
python create_demo_discovery_map_v7.py
```

### Dependencies
- utils.discovery_graph
- utils.discovery_map_formatter

### Output
- Generates demo discovery data
- Creates demo discovery map HTML
- Saves to reports/discovery/demo/

### Notes
- Used for demo purposes
- Generates sample network topology
- Useful for testing and demonstrations

---

## create_demo_map.py

### Purpose
Create demo topology map.

### Status
**Legacy** - Use create_demo_map_v7.py instead.

### Usage
```bash
python create_demo_map.py
```

### Dependencies
- utils.topo_map_shell

### Output
- Generates demo topology data
- Creates demo topology map HTML
- Saves to reports/topology/demo/

### Notes
- Legacy script
- Use create_demo_map_v7.py for current version

---

## create_demo_map_v7.py

### Purpose
Create demo topology map for v7.

### Status
**Active** - Used for demo data generation.

### Usage
```bash
python create_demo_map_v7.py
```

### Dependencies
- utils.topo_map_shell

### Output
- Generates demo topology data
- Creates demo topology map HTML
- Saves to reports/topology/demo/

### Notes
- Used for demo purposes
- Generates sample network topology
- Useful for testing and demonstrations

---

## f5_manager_gui.py

### Purpose
F5 device manager GUI.

### Status
**Active** - F5 device management interface.

### Usage
```bash
python f5_manager_gui.py
```

### Dependencies
- tkinter

### Output
- Launches F5 device manager GUI
- Provides GUI interface for F5 management
- Supports F5 BIG-IP configuration

### Features
- F5 device connection
- Configuration management
- Pool and member management
- Virtual server configuration

### Notes
- Separate GUI application
- Uses tkinter for UI
- F5-specific functionality

---

## test_plugins.py

### Purpose
Plugin testing script.

### Status
**Active** - Used for plugin validation.

### Usage
```bash
python test_plugins.py
```

### Dependencies
- modules.plugin_registry

### Output
- Tests plugin loading
- Validates plugin METADATA
- Tests plugin execution
- Generates test report

### Test Categories
- Plugin loading tests
- METADATA validation tests
- Plugin execution tests
- Error handling tests

### Notes
- Should be run after plugin development
- Validates plugin structure
- Ensures plugin compliance

---

## test_socketio.py

### Purpose
SocketIO testing script.

### Status
**Active** - Used for WebSocket testing.

### Usage
```bash
python test_socketio.py
```

### Dependencies
- Flask
- Flask-SocketIO

### Output
- Tests SocketIO connection
- Tests WebSocket events
- Tests real-time communication
- Generates test report

### Test Categories
- Connection tests
- Event handling tests
- Message passing tests
- Error handling tests

### Notes
- Tests WebSocket functionality
- Validates SocketIO integration
- Should be run after SocketIO changes

---

## vlan_checker_gui.py

### Purpose
Legacy GUI application (deprecated).

### Status
**Deprecated** - Use web interface instead.

### Usage
```bash
python vlan_checker_gui.py
```

### Dependencies
- tkinter

### Output
- Launches legacy GUI application
- Provides GUI interface for VLAN checking
- Supports network operations

### Features
- VLAN checking
- Network operations
- Configuration management

### Notes
- Deprecated in favor of web interface
- Kept for backward compatibility
- Should not be used for new deployments

---

## Script Dependencies Summary

### No Dependencies
- main.py
- create_plugin.py
- make_bat.py
- _prebuild.py
- _check_plugin_path.py
- _fix_bugs.py

### Python Standard Library
- _check_yaml.py (PyYAML - third-party but common)

### Flask/SocketIO
- _cli_diagnostic_server.py
- test_socketio.py

### pytest
- _master_qa_test.py
- _test_v622.py

### Internal Modules
- generate_plugin_docs.py (utils.report_formatter)
- create_demo_discovery_map_v7.py (utils.discovery_graph, utils.discovery_map_formatter)
- create_demo_map.py (utils.topo_map_shell)
- create_demo_map_v7.py (utils.topo_map_shell)
- test_plugins.py (modules.plugin_registry)

### GUI Frameworks
- f5_manager_gui.py (tkinter)
- vlan_checker_gui.py (tkinter)

---

## Script Usage Patterns

### Development Scripts
- create_plugin.py - Plugin scaffolding
- generate_plugin_docs.py - Plugin documentation
- _fix_bugs.py - Bug identification
- test_plugins.py - Plugin testing
- test_socketio.py - SocketIO testing

### Build Scripts
- _prebuild.py - Pre-build validation
- make_bat.py - Batch file generation

### Validation Scripts
- _check_plugin_path.py - Plugin path validation
- _check_yaml.py - YAML validation
- _master_qa_test.py - Comprehensive QA testing
- _test_v622.py - Version-specific testing

### Demo Scripts
- create_demo_discovery_map_v7.py - Demo discovery map
- create_demo_map.py - Legacy demo map
- create_demo_map_v7.py - Demo topology map

### Diagnostic Scripts
- _cli_diagnostic_server.py - CLI diagnostics

### Application Scripts
- main.py - Legacy main entry point (deprecated)
- vlan_checker_web.py - Main web application (not documented here, see API docs)
- f5_manager_gui.py - F5 device manager GUI
- vlan_checker_gui.py - Legacy GUI (deprecated)

---

## Script Maintenance

### Adding New Scripts
1. Create script in root directory
2. Document script in this file
3. Add to script summary table
4. Test script functionality
5. Update CHANGELOG.md

### Updating Scripts
1. Update script functionality
2. Update documentation in this file
3. Test updated functionality
4. Update CHANGELOG.md

### Deprecating Scripts
1. Mark script as deprecated in documentation
2. Add deprecation notice in script
3. Update CHANGELOG.md
4. Remove from active use

---

## Best Practices

### Script Design
- Use clear script names
- Include docstrings
- Add command-line argument parsing
- Include error handling
- Provide usage help

### Script Documentation
- Document purpose and usage
- Document parameters and dependencies
- Document output format
- Include usage examples
- Document notes and limitations

### Script Testing
- Test scripts with valid inputs
- Test scripts with invalid inputs
- Test error handling
- Test edge cases

---

## Troubleshooting

### Common Issues

#### Script Import Error
**Symptom:** Script fails with import error  
**Solution:** Check script location, check PYTHONPATH, check dependencies installed

#### Script Permission Error
**Symptom:** Script fails with permission error  
**Solution:** Check file permissions, run with appropriate permissions

#### Script Dependency Error
**Symptom:** Script fails with missing dependency  
**Solution:** Install required dependencies using pip

#### Script Path Error
**Symptom:** Script fails to find files  
**Solution:** Check working directory, use absolute paths, check file exists

---

## References

- Python Documentation: https://docs.python.org/
- PyInstaller Documentation: https://pyinstaller.org/
- Flask Documentation: https://flask.palletsprojects.com/
- pytest Documentation: https://docs.pytest.org/
