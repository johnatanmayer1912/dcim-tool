# Complete Build and Deployment Guide

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Release Manager (R-REL) |
| **Last Updated** | 2026-07-21 |
| **Application Version** | 7.0.85 |

## Purpose

This document provides complete instructions for building and deploying Network Swiss Tool Pro from source, including all dependencies, build procedures, troubleshooting, and offline deployment. This guide enables 1:1 reconstruction of the program from documentation alone.

## Prerequisites

### System Requirements
- **OS**: Windows 10 or Windows 11
- **Python**: Python 3.8 or higher (recommended: 3.10 or 3.11)
- **Disk Space**: 2GB+ for build artifacts
- **Memory**: 4GB+ RAM recommended
- **Privileges**: Administrator privileges for some operations

### Python Version Compatibility
- **Python 3.8-3.12**: Fully supported
- **Python 3.13+**: Requires telnetlib compatibility hook (included)
- **Python 3.7**: Not supported (deprecated)

## Complete Dependency Manifest

### Core Dependencies (requirements.txt)
```
flask==3.0.0
flask-socketio==5.3.6
netmiko==4.3.0
paramiko==3.4.0
cryptography==42.0.0
bcrypt==4.1.2
pyyaml==6.0.1
jinja2==3.1.3
textfsm==2.1.1
ntc-templates==2.2.0
```

### WebSocket Dependencies
```
python-socketio==5.11.0
python-engineio==4.7.1
simple-websocket==1.0.0
wsproto==1.2.0
bidict==0.23.4
```

### Build Dependencies
```
pyinstaller==6.3.0
```

### Development Dependencies (Optional)
```
pytest==8.0.0
pytest-cov==4.1.0
black==24.1.1
flake8==7.0.0
mypy==1.8.0
```

## Installation Procedure

### Step 1: Clone Repository
```bash
git clone <repository_url>
cd net_mng_tool_cartography
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import flask; print(flask.__version__)"
python -c "import netmiko; print(netmiko.__version__)"
python -c "import paramiko; print(paramiko.__version__)"
```

## Build Process

### Step 1: Update Version Information

#### Update VERSION File
```
7.0.85
```

#### Update Spec File
Copy previous spec file and update:
```bash
copy NetworkSwissToolPro_v7.0.84.spec NetworkSwissToolPro_v7.0.85.spec
```

Update in spec file:
- Line 3: Version description
- Line 122: `name='NetworkSwissToolPro_v7.0.85_OFFLINE'`
- Line 135: Icon path if needed

#### Update CHANGELOG.md
Add new version entry:
```markdown
## v7.0.85 (2026-07-21)
- Documentation enhancements
- Proposed features integration
```

### Step 2: Run Build Command
```bash
pyinstaller NetworkSwissToolPro_v7.0.85.spec
```

Or use batch file:
```bash
build_exe.bat
```

### Step 3: Verify Build Output

Check `dist/` directory for:
- `NetworkSwissToolPro_v7.0.85_OFFLINE.exe` (50-100MB)
- Verify no build errors in console output

### Step 4: Test Executable

#### Basic Functionality Test
```bash
dist\NetworkSwissToolPro_v7.0.85_OFFLINE.exe
```

Verify:
- Application starts without errors
- Web interface loads at http://127.0.0.1:5051
- Health check passes: http://127.0.0.1:5051/health
- Plugins load correctly

#### Smoke Test
```bash
dist\NetworkSwissToolPro_v7.0.85_OFFLINE.exe test
```

## Spec File Structure

### Complete Spec File Template
```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Network Swiss Tool Pro v7.0.85

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('modules', 'modules'),
        ('utils', 'utils'),
        ('templates', 'templates'),
        ('static', 'static'),
        ('standards', 'standards'),
        ('inventory.txt', '.'),
        ('VERSION', '.'),
        ('favicon_program.png', '.'),
    ],
    hiddenimports=[
        'flask_socketio',
        'socketio',
        'engineio',
        'simple_websocket',
        'wsproto',
        'bidict',
        'telnetlib_compat',
        'netmiko.ssh_exception',
        'netmiko.base_connection',
        'paramiko',
        'cryptography',
        'bcrypt',
        'yaml',
        'textfsm',
        'ntc_templates',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_telnetlib.py'],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NetworkSwissToolPro_v7.0.85_OFFLINE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon_program.ico',
)
```

### Key Spec File Sections

#### Data Files
- `modules` - All feature modules and plugins
- `utils` - Utility functions and helpers
- `templates` - Jinja2 templates for web interface
- `static` - Static assets (CSS, JS, images)
- `standards` - Configuration standards
- `inventory.txt` - Device inventory
- `VERSION` - Version file
- `favicon_program.png` - Application icon

#### Hidden Imports
- WebSocket libraries (flask_socketio, socketio, engineio)
- Telnetlib compatibility (telnetlib_compat)
- Network libraries (netmiko, paramiko)
- Security libraries (cryptography, bcrypt)
- Parsing libraries (yaml, textfsm, ntc_templates)

#### Excludes
- Data science libraries (matplotlib, numpy, pandas)
- Image processing (PIL)
- Reduces executable size

#### Runtime Hooks
- `runtime_hook_telnetlib.py` - Telnetlib compatibility for Python 3.13+

## Deployment Procedure

### Step 1: Prepare Deployment Package

#### Create Deployment Directory
```bash
mkdir deployment_v7.0.85
copy dist\NetworkSwissToolPro_v7.0.85_OFFLINE.exe deployment_v7.0.85\
copy inventory.txt deployment_v7.0.85\
copy README.md deployment_v7.0.85\
```

#### Optional: Include Documentation
```bash
xcopy docs deployment_v7.0.85\docs\ /E /I
```

### Step 2: Test Deployment Package

#### Test on Clean System
1. Copy deployment package to target system
2. Run executable
3. Verify all functionality
4. Test with sample inventory

### Step 3: Distribute

#### Distribution Methods
- **Direct Download**: Host on internal server
- **Package Manager**: Create MSI installer (optional)
- **USB Drive**: For air-gapped environments

## Offline Build Procedure

### Prerequisites for Offline Build

1. **Download Dependencies**:
```bash
pip download -r requirements.txt -d dependencies/
```

2. **Download PyInstaller**:
```bash
pip download pyinstaller -d dependencies/
```

3. **Package Dependencies**:
```bash
# Create dependencies archive
powershell Compress-Archive -Path dependencies\ -DestinationPath dependencies.zip
```

### Offline Build Steps

1. **Extract Dependencies**:
```bash
Expand-Archive -Path dependencies.zip -DestinationPath dependencies\
```

2. **Install Dependencies Offline**:
```bash
pip install --no-index --find-links=dependencies/ -r requirements.txt
pip install --no-index --find-links=dependencies/ pyinstaller
```

3. **Run Build**:
```bash
pyinstaller NetworkSwissToolPro_v7.0.85.spec
```

## Troubleshooting

### Build Errors

#### Error: "Module not found"
**Solution**: Add to hiddenimports in spec file
```python
hiddenimports=['missing_module_name']
```

#### Error: "RecursionError"
**Solution**: Add to excludes in spec file
```python
excludes=['problematic_module']
```

#### Error: "File not found"
**Solution**: Add to datas in spec file
```python
datas=[('missing_file', 'destination')]
```

### Runtime Errors

#### Error: "Telnetlib not found"
**Solution**: Ensure runtime_hook_telnetlib.py is included
```python
runtime_hooks=['runtime_hook_telnetlib.py']
```

#### Error: "Plugin not loading"
**Solution**: Verify modules/plugins/ directory is included in datas
```python
datas=[('modules/plugins', 'modules/plugins')]
```

#### Error: "Template not found"
**Solution**: Verify modules/web/templates is included
```python
datas=[('modules/web/templates', 'modules/web/templates')]
```

### Performance Issues

#### Large Executable Size
**Solution**: Add more excludes
```python
excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'tkinter']
```

#### Slow Startup
**Solution**: Disable UPX compression
```python
upx=False
```

## Verification Checklist

### Pre-Build Verification
- [ ] Python version correct (3.8+)
- [ ] All dependencies installed
- [ ] VERSION file updated
- [ ] Spec file updated
- [ ] CHANGELOG.md updated

### Post-Build Verification
- [ ] Executable created in dist/
- [ ] Executable size reasonable (50-100MB)
- [ ] No build errors in console
- [ ] Executable runs without errors
- [ ] Web interface loads correctly
- [ ] Health check passes
- [ ] Plugins load correctly
- [ ] Sample inventory works

### Deployment Verification
- [ ] Deployment package complete
- [ ] Tested on clean system
- [ ] Documentation included
- [ ] README included
- [ ] License included

## Build Automation

### Automated Build Script (build_automation.py)
```python
import subprocess
import sys
import os

def run_command(cmd):
    """Run command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    version = "7.0.85"
    
    # Update version file
    with open('VERSION', 'w') as f:
        f.write(version)
    
    # Run build
    spec_file = f"NetworkSwissToolPro_v{version}.spec"
    if not os.path.exists(spec_file):
        print(f"Error: {spec_file} not found")
        return 1
    
    if not run_command(f"pyinstaller {spec_file}"):
        print("Build failed")
        return 1
    
    # Verify build
    exe_path = f"dist/NetworkSwissToolPro_v{version}_OFFLINE.exe"
    if not os.path.exists(exe_path):
        print(f"Error: {exe_path} not found")
        return 1
    
    print("Build successful")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Usage
```bash
python build_automation.py
```

## Related Documentation

- `BUILD_PROCESS.md` - Original build process documentation
- `from-zero-installation.md` - From-zero installation guide
- `exact-rebuild-procedure.md` - Exact rebuild procedure
- `offline-recovery.md` - Offline recovery procedures

## Cross-References

- References: `requirements.txt` (dependency list)
- References: `NetworkSwissToolPro_v7.0.85.spec` (PyInstaller spec)
- References: `runtime_hook_telnetlib.py` (telnetlib compatibility)
- Referenced by: `20-release-management/README.md` (release management)
