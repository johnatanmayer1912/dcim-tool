# Build Process Documentation

## Overview

Network Swiss Tool Pro uses PyInstaller to create standalone Windows executables for offline deployment. This document describes the complete build process, prerequisites, spec file structure, and troubleshooting.

## Current Build Configuration

**Current Version:** 7.0.10  
**Current Spec File:** `NetworkSwissToolPro_v7.0.10.spec`  
**Output Executable:** `NetworkSwissToolPro_v7.0.10_OFFLINE.exe`

---

## Prerequisites

### Python Version
- **Required:** Python 3.8 or higher
- **Recommended:** Python 3.10 or 3.11
- **Note:** Python 3.13+ requires telnetlib compatibility hook

### Required Packages
```bash
pip install pyinstaller flask flask-socketio netmiko paramiko cryptography bcrypt pyyaml jinja2 textfsm ntc_templates
```

### System Requirements
- Windows 10 or Windows 11
- Administrator privileges (for some build operations)
- 2GB+ free disk space for build artifacts

---

## Build Steps

### 1. Update Spec File for New Version

When creating a new version, update the spec file:

1. **Copy previous spec file:**
   ```bash
   copy NetworkSwissToolPro_v7.0.10.spec NetworkSwissToolPro_v7.0.11.spec
   ```

2. **Update version references:**
   - Line 3: Update comment with new version description
   - Line 122: Update `name='NetworkSwissToolPro_v7.0.11_OFFLINE'`
   - Line 135: Update icon if needed

3. **Update VERSION file:**
   ```
   7.0.11
   ```

4. **Update CHANGELOG.md:**
   Add new version entry with changes

### 2. Run Build Command

```bash
pyinstaller NetworkSwissToolPro_v7.0.10.spec
```

Or use the provided batch file:
```bash
build_exe.bat
```

### 3. Verify Build Output

Check the `dist/` directory for:
- `NetworkSwissToolPro_v7.0.10_OFFLINE.exe` - Main executable
- Verify file size (typically 50-100MB)

### 4. Test Executable

1. **Run the executable:**
   ```bash
   dist\NetworkSwissToolPro_v7.0.10_OFFLINE.exe
   ```

2. **Verify functionality:**
   - Application starts without errors
   - Web interface loads at http://127.0.0.1:5051
   - All plugins load correctly
   - Health check passes

---

## Spec File Structure

### Header Section
```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Network Swiss Tool Pro v7.0.10
# v7.0.10 - NX-OS LLDP discovery link parsing fixes
```

### Metadata Collection
```python
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

# Collect metadata for Flask-SocketIO dependencies
flask_meta = copy_metadata('flask')
flask_socketio_meta = copy_metadata('flask-socketio')
# ... (other metadata collections)
```

### Hidden Imports
Critical for ensuring all modules are included in the EXE:

```python
hiddenimports = [
    'telnetlib_compat',  # Python 3.13+ telnetlib compatibility
    'utils.report_formatter',
    'utils.vpc_board_formatter',
    # ... (all utility modules)
    'modules.cli_manager',
    'modules.plugin_registry',
    'modules.network_base',
    # ... (all core modules)
    'modules.plugins.network_discovery',
    'modules.plugins.config_templates',
    # ... (all plugins)
    'netmiko', 'paramiko', 'cryptography', 'bcrypt',
    # ... (third-party packages)
] + collect_submodules('flask') + collect_submodules('flask_socketio')
```

### Data Files
Files and directories bundled into the EXE:

```python
datas = [
    ('modules/web/templates', 'modules/web/templates'),  # HTML templates
    ('modules/web/vis-network.min.js', 'modules/web'),  # Vis.js library
    ('static', 'static'),  # Static assets
    ('modules/plugins', 'modules/plugins'),  # Plugin code
    ('policies', 'policies'),  # Standards policies
    ('standards', 'standards'),  # Standards files
    ('templates', 'templates'),  # Jinja2 templates
    ('inventory', 'inventory'),  # Inventory folder
    ('config', 'config'),  # Configuration folder
    ('docs', 'docs'),  # Documentation
    ('utils', 'utils'),  # Utility modules
    ('modules', 'modules'),  # Core modules
    ('README.md', '.'),  # README
    ('VERSION', '.'),  # Version file
    ('CHANGELOG.md', '.'),  # Changelog
    ('telnetlib_compat.py', '.'),  # Telnetlib compatibility
    ('favicon_program.png', '.'),  # Application icon
]
```

### Runtime Hooks
```python
runtime_hooks=['runtime_hook_telnetlib.py']
```

This hook ensures telnetlib compatibility for Python 3.13+.

### EXE Configuration
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NetworkSwissToolPro_v7.0.10_OFFLINE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX compression
    console=False,  # No console window
    hide_console='hide-early',
    icon='favicon_program.ico',  # Application icon
)
```

---

## Runtime Hooks

### runtime_hook_telnetlib.py

**Purpose:** Provides telnetlib compatibility for Python 3.13+ where telnetlib was removed from the standard library.

**Location:** `build_scripts/runtime_hook_telnetlib.py`

**Functionality:**
- Checks if telnetlib is available
- If not, imports telnetlib_compat as telnetlib
- Ensures code using telnetlib continues to work

---

## Adding New Plugins to Build

When adding a new plugin, update the spec file:

1. **Add to hiddenimports:**
   ```python
   'modules.plugins.new_plugin_name',
   ```

2. **Verify plugin is in modules/plugins/ directory:**
   The datas section already includes the entire modules/plugins/ directory.

3. **Rebuild the EXE:**
   ```bash
   pyinstaller NetworkSwissToolPro_v7.0.10.spec
   ```

---

## Adding New Utility Modules

When adding a new utility module, update the spec file:

1. **Add to hiddenimports:**
   ```python
   'utils.new_utility_module',
   ```

2. **Verify utility is in utils/ directory:**
   The datas section already includes the entire utils/ directory.

3. **Rebuild the EXE:**
   ```bash
   pyinstaller NetworkSwissToolPro_v7.0.10.spec
   ```

---

## Build Artifacts

### Directory Structure After Build
```
NetworkSwissToolPro_v6 - cursor/
├── build/
│   └── NetworkSwissToolPro_v7.0.10_OFFLINE/
│       ├── Analysis-00.toc
│       ├── COLLECT-00.toc
│       ├── EXE-00.toc
│       ├── PKG-00.toc
│       ├── PYZ-00.pyz
│       ├── SPLASH-00.toc
│       ├── Tree-00.toc
│       ├── xref-00.toc
│       └── warn-*.txt
├── dist/
│   └── NetworkSwissToolPro_v7.0.10_OFFLINE.exe
└── NetworkSwissToolPro_v7.0.10.spec
```

### Cleaning Build Artifacts
```bash
rmdir /s /q build
rmdir /s /q dist
```

---

## Common Build Issues

### Issue: ModuleNotFoundError
**Symptom:** EXE crashes with "ModuleNotFoundError: No module named 'X'"

**Solution:** Add missing module to hiddenimports in spec file:
```python
hiddenimports = [
    # ... existing imports
    'missing_module_name',
]
```

### Issue: File Not Found in EXE
**Symptom:** EXE crashes with "FileNotFoundError: [Errno 2] No such file or directory: 'X'"

**Solution:** Add missing file/directory to datas in spec file:
```python
datas = [
    # ... existing datas
    ('missing_directory', 'missing_directory'),
]
```

### Issue: Telnetlib Import Error (Python 3.13+)
**Symptom:** "ModuleNotFoundError: No module named 'telnetlib'"

**Solution:** Ensure runtime_hook_telnetlib.py is included:
```python
runtime_hooks=['runtime_hook_telnetlib.py']
```

### Issue: Flask-SocketIO Not Working
**Symptom:** WebSocket connections fail

**Solution:** Ensure Flask-SocketIO metadata and submodules are collected:
```python
flask_socketio_meta = copy_metadata('flask-socketio')
hiddenimports += collect_submodules('flask_socketio')
```

### Issue: EXE Size Too Large
**Symptom:** EXE file is excessively large (>200MB)

**Solution:**
- Verify UPX compression is enabled: `upx=True`
- Check for unnecessary data files in datas section
- Review excludes list for missing exclusions

---

## Version History of Spec Files

The project maintains spec files for each version:
- `NetworkSwissToolPro_v6.9.20_OFFLINE.spec` through `NetworkSwissToolPro_v7.0.10.spec`
- Each spec file is versioned with the application version
- Old spec files are kept for reference and rollback capability

**Current Spec File:** `NetworkSwissToolPro_v7.0.10.spec`

---

## EXE Naming Convention

**Pattern:** `NetworkSwissToolPro_v{VERSION}_OFFLINE.exe`

**Examples:**
- `NetworkSwissToolPro_v7.0.10_OFFLINE.exe`
- `NetworkSwissToolPro_v7.0.11_OFFLINE.exe`

**Suffix:** `_OFFLINE` indicates the executable is self-contained and works without internet connection.

---

## Testing the Built EXE

### 1. Basic Startup Test
```bash
dist\NetworkSwissToolPro_v7.0.10_OFFLINE.exe
```
Verify:
- Application starts
- No console errors
- Browser opens to http://127.0.0.1:5051

### 2. Health Check Test
- Navigate to http://127.0.0.1:5051
- Run health check from the UI
- Verify all checks pass

### 3. Plugin Test
- Navigate to Plugins tab
- Verify all plugins load
- Test a plugin operation

### 4. Offline Test
- Disconnect network cable
- Run application
- Verify all features work without internet

---

## Automated Build Script

The project includes `build_exe.bat` for automated building:

```batch
@echo off
echo Building Network Swiss Tool Pro...
pyinstaller NetworkSwissToolPro_v7.0.10.spec
echo Build complete.
pause
```

**Usage:**
```bash
build_exe.bat
```

---

## Archive and Rollback

### Archiving Old Builds
```bash
mkdir archives\v7.0.10
move dist\NetworkSwissToolPro_v7.0.10_OFFLINE.exe archives\v7.0.10\
move NetworkSwissToolPro_v7.0.10.spec archives\v7.0.10\
```

### Rollback to Previous Version
1. Copy spec file from archive:
   ```bash
   copy archives\v7.0.9\NetworkSwissToolPro_v7.0.9.spec NetworkSwissToolPro_v7.0.10.spec
   ```

2. Rebuild:
   ```bash
   pyinstaller NetworkSwissToolPro_v7.0.10.spec
   ```

3. Update VERSION file to previous version

---

## Continuous Integration Considerations

For CI/CD pipelines:

1. **Version Management:**
   - Read VERSION file dynamically
   - Update spec file name based on VERSION

2. **Build Verification:**
   - Run automated tests after build
   - Verify EXE starts without errors
   - Run health check on built EXE

3. **Artifact Management:**
   - Archive builds with version tags
   - Keep last N builds for rollback capability
   - Upload to artifact repository

---

## Troubleshooting

### Build Fails with "PyInstaller cannot find"
**Solution:** Verify PyInstaller is installed:
```bash
pip install --upgrade pyinstaller
```

### EXE Runs but Shows Blank Page
**Solution:** Verify templates are included in datas:
```python
datas = [
    ('modules/web/templates', 'modules/web/templates'),
]
```

### EXE Crashes on Startup
**Solution:** Check logs in `dist/logs/` directory for error details

### Plugins Don't Load in EXE
**Solution:** Verify plugins are in hiddenimports:
```python
hiddenimports = [
    'modules.plugins.network_discovery',
    'modules.plugins.config_templates',
    # ... all plugins
]
```

---

## References

- **PyInstaller Documentation:** https://pyinstaller.org/en/stable/
- **Flask-SocketIO Documentation:** https://flask-socketio.readthedocs.io/
- **Netmiko Documentation:** https://netmiko.readthedocs.io/
