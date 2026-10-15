# P26: Packaging

| Field | Value |
|-------|-------|
| **Prompt ID** | P26 |
| **Phase** | 08-deployment |
| **Dependency Level** | 8 (Depends on P25) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct packaging process for distribution. This provides the packaging configuration for creating installers and distribution packages.

---

## Prerequisites

- P25: Build Process completed
- Executable built successfully
- Python environment set up

---

## Instructions

### Step 1: Create package.py

```python
"""
Packaging Script

Package executable for distribution.
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_distribution_package():
    """Create distribution package"""
    version = "7.0.10"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_name = f"NetworkSwissToolPro_v{version}_{timestamp}"
    
    # Create package directory
    package_dir = f"dist/{package_name}"
    os.makedirs(package_dir, exist_ok=True)
    
    # Copy executable
    shutil.copy("dist/NetworkSwissToolPro.exe", f"{package_dir}/NetworkSwissToolPro.exe")
    
    # Copy documentation
    shutil.copytree("docs", f"{package_dir}/docs")
    
    # Copy configuration files
    shutil.copy("config.yaml", f"{package_dir}/config.yaml")
    shutil.copy("config_logging.yaml", f"{package_dir}/config_logging.yaml")
    
    # Create README
    with open(f"{package_dir}/README.txt", "w") as f:
        f.write(f"Network Swiss Tool Pro v{version}\n")
        f.write("=" * 50 + "\n\n")
        f.write("Installation:\n")
        f.write("1. Extract this package to desired location\n")
        f.write("2. Run NetworkSwissToolPro.exe\n")
        f.write("3. Configure settings in config.yaml\n\n")
        f.write("Documentation:\n")
        f.write("See docs/ directory for comprehensive documentation\n")
    
    # Create ZIP archive
    zip_filename = f"dist/{package_name}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arcname)
    
    print(f"Package created: {zip_filename}")
    return zip_filename

def create_installer_script():
    """Create NSIS installer script"""
    script_content = """
; NSIS Installer Script
!define APPNAME "Network Swiss Tool Pro"
!define VERSION "7.0.10"
!define PUBLISHER "Network Swiss Tool Pro"

Name "${APPNAME} ${VERSION}"
OutFile "dist/NetworkSwissToolPro_Setup.exe"
InstallDir "$PROGRAMFILES\\${APPNAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Main Files"
    SetOutPath $INSTDIR
    File /r "dist\\NetworkSwissToolPro_v*\\*"
    
    CreateDirectory "$INSTDIR\\logs"
    
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\NetworkSwissToolPro.exe"
    CreateShortCut "$STARTMENU\\Programs\\${APPNAME}.lnk" "$INSTDIR\\NetworkSwissToolPro.exe"
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\\${APPNAME}.lnk"
    Delete "$STARTMENU\\Programs\\${APPNAME}.lnk"
    RMDir /r "$INSTDIR"
SectionEnd
"""
    
    with open("dist/installer.nsi", "w") as f:
        f.write(script_content)
    
    print("Installer script created: dist/installer.nsi")

if __name__ == '__main__':
    create_distribution_package()
    create_installer_script()
    print("Packaging complete!")
```

---

### Step 2: Create package_requirements.txt

```bash
cat > package_requirements.txt << 'EOF'
# Packaging requirements
pyinstaller==6.3.0
pywin32==306
EOF
```

---

### Step 3: Validate Packaging

```bash
# Run packaging
python package.py

# Verify package created
ls -lh dist/*.zip

# Verify installer script created
ls -lh dist/installer.nsi
```

---

## Validation Checklist

- [ ] package.py created
- [ ] Distribution package creation functional
- [ ] ZIP archive creation functional
- [ ] Installer script creation functional
- [ ] Documentation included in package
- [ ] Configuration files included
- [ ] README created
- [ ] Package validation successful
- [ ] Ready for deployment reconstruction

---

## Troubleshooting

### Issue: Package creation fails

**Solution:**
- Verify executable exists
- Check disk space
- Validate file paths

### Issue: ZIP creation fails

**Solution:**
- Check file permissions
- Verify disk space
- Test with smaller package

---

## Next Steps

After completing this prompt, proceed to P27: Deployment

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- BUILD_PROCESS.md: ../../10-rebuild/BUILD_PROCESS.md
