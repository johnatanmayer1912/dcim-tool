# P25: Build Process

| Field | Value |
|-------|-------|
| **Prompt ID** | P25 |
| **Phase** | 08-deployment |
| **Dependency Level** | 7 (Depends on Phases 1, 4) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct PyInstaller build process for creating executable. This provides the build configuration for packaging the application as a standalone executable.

---

## Prerequisites

- Phase 1 (Foundation) completed
- Phase 4 (Web Interface) completed
- PyInstaller installed
- Python environment set up

---

## Instructions

### Step 1: Create vlan_checker_web.spec

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['vlan_checker_web.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('modules', 'modules'),
        ('policies', 'policies'),
        ('config.yaml', '.'),
        ('config_logging.yaml', '.')
    ],
    hiddenimports=[
        'flask',
        'flask_socketio',
        'netmiko',
        'paramiko',
        'textfsm',
        'yaml',
        'jinja2',
        'eventlet',
        'gevent',
        'gevent.monkey',
        'geventwebsocket',
        'websocket'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='NetworkSwissToolPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
```

---

### Step 2: Create build.py

```python
"""
Build Script

Build executable using PyInstaller.
"""

import subprocess
import sys
import os
from datetime import datetime

def build_executable():
    """Build executable using PyInstaller"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'vlan_checker_web.spec'
    ]
    
    print(f"Building executable: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("Build successful!")
        print(f"Executable location: dist/NetworkSwissToolPro.exe")
        return 0
    else:
        print("Build failed!")
        return result.returncode

if __name__ == '__main__':
    exit_code = build_executable()
    sys.exit(exit_code)
```

---

### Step 3: Create build_requirements.txt

```bash
cat > build_requirements.txt << 'EOF'
PyInstaller==6.3.0
pywin32==306
EOF
```

---

### Step 4: Validate Build Process

```bash
# Install build requirements
pip install -r build_requirements.txt

# Run build
python build.py

# Verify executable exists
ls -lh dist/NetworkSwissToolPro.exe
```

---

## Validation Checklist

- [ ] vlan_checker_web.spec created
- [ ] build.py created
- [ ] build_requirements.txt created
- [ ] PyInstaller configuration validated
- [ ] Hidden imports specified
- [ ] Data files included
- [ ] Build script functional
- [ ] Executable builds successfully
- [ ] Ready for packaging reconstruction

---

## Troubleshooting

### Issue: Build fails with import errors

**Solution:**
- Add missing imports to hiddenimports
- Verify all dependencies installed
- Check module paths

### Issue: Data files not included

**Solution:**
- Verify datas tuple in spec file
- Check file paths
- Validate file existence

---

## Next Steps

After completing this prompt, proceed to P26: Packaging

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- BUILD_PROCESS.md: ../../10-rebuild/BUILD_PROCESS.md
