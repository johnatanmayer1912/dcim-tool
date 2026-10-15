# Network Swiss Tool Pro - Build Process

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Operational guide for generating the production standalone executable. |
| **Scope** | PyInstaller build commands, specification files, and packaging workflows. |
| **Related Documents** | [Exact Rebuild Procedure](exact-rebuild-procedure.md), [Release History](../11-release-management/release-history.md) |
| **Update Responsibility** | Release Manager / DevOps Engineer |
| **Version Awareness** | v7.0.51 |

---

## 🚨 TL;DR - Quick Build (10 minutes)

```powershell
# 1. Pre-build gate (mandatory)
python _prebuild.py

# 2. Build offline EXE (v7.0.51)
pyinstaller --clean --noconfirm NetworkSwissToolPro_v7.0.51.spec

# Output: dist\NetworkSwissToolPro_v7.0.51_OFFLINE.exe
```

---

## Version awareness

| Item | Current (sync with `/VERSION`) |
|------|--------------------------------|
| Application | **7.0.51** |
| Spec file | `NetworkSwissToolPro_v7.0.51.spec` |
| Artifact | `dist/NetworkSwissToolPro_v7.0.51_OFFLINE.exe` |
| Smoke checklist | [exe-smoke-checklist.md](../07-operations/exe-smoke-checklist.md) |

---

## Legacy quick build (reference only)

```powershell
# Older spec example — use current version spec above
python -m PyInstaller NetworkSwissToolPro_v6.9.5_FINAL.spec --clean --noconfirm
```

---

## 📋 Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.14+ | Runtime and build environment |
| PyInstaller | 6.0+ | EXE generation |
| Windows | 10/11 | Build platform |

### Install Dependencies

```powershell
# Install PyInstaller
python -m pip install --upgrade pyinstaller

# Verify installation
python -m pyinstaller --version
```

---

## 🔨 Build Process

### Step 1: Pre-Build Verification

```powershell
# Clean previous builds
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build

# Verify source files exist
Test-Path "vlan_checker_web.py"          # Main entry point
Test-Path "modules/"                     # Modules directory
Test-Path "utils/"                       # Utilities directory
Test-Path "build_scripts/NetworkSwissToolPro_v6_5_1.spec"  # Spec file

# Run smoke test (optional but recommended)
python -c "from modules import network_base; print('✓ Imports OK')"
```

---

### Step 2: PyInstaller Build

```powershell
# Full build with logging
python -m PyInstaller build_scripts\NetworkSwissToolPro_v6_5_1.spec `
    --clean `
    --noconfirm `
    2>&1 | Tee-Object -FilePath "build_output_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
```

**Build Outputs:**
- `dist/NetworkSwissToolPro_v6_5_7.exe` - Main executable (~75MB)
- `build/` - Temporary build files (can be deleted)

**What the spec file includes:**
- All Python modules (modules/, utils/)
- Web templates (modules/web/templates/)
- Static assets (xterm.js, socket.io, vis.js)
- Policy files (policies/)
- Icon and version resources

---

### Step 3: Post-Build Packaging

```powershell
# Create distribution folder
$distDir = "dist_package_v6_5_8_FINAL"
New-Item -ItemType Directory -Force -Path $distDir

# Copy EXE with versioned name
Copy-Item "dist\NetworkSwissToolPro_v6_5_7.exe" `
    "$distDir\NetworkSwissToolPro_v6_5_8.exe" -Force

# Copy release notes
Copy-Item "docs\02_RELEASES\RELEASE_NOTES_6.5.8.md" $distDir

# Verify final package
Get-ChildItem $distDir
# Expected output:
# NetworkSwissToolPro_v6_5_8.exe
# RELEASE_NOTES_6.5.8.md
```

---

## 🎯 Build Verification Checklist

### Immediate Post-Build Tests

| Test | Command | Expected Result |
|------|---------|---------------|
| EXE exists | `Test-Path "dist_package_v6_5_8_FINAL\NetworkSwissToolPro_v6_5_8.exe"` | `True` |
| EXE size | `(Get-Item *.exe).Length / 1MB` | ~70-80 MB |
| EXE launches | `Start-Process *.exe` | Window opens, no errors |

### Functional Tests (Manual)

1. **Web UI Loads**
   - Open `http://127.0.0.1:5051`
   - Verify login page appears
   - Check console for errors

2. **CLI Terminal**
   - Open CLI Terminal tab
   - Try connecting to a test device
   - Verify connection timeout works (30s)

3. **Standards Validator**
   - Upload a policy file
   - Verify category checkboxes appear
   - Run validation on test device
   - Check consolidated report generation

4. **MAPS**
   - Generate topology map
   - Verify vPC visualization
   - Check interface descriptions in popups

---

## 🆘 Troubleshooting Build Issues

### Issue: "ModuleNotFoundError" during build

**Solution:**
```powershell
# Check if module is in spec file's Analysis
# Edit: build_scripts/NetworkSwissToolPro_v6_5_1.spec
# Add missing module to 'hiddenimports' list

# Example:
hiddenimports=['missing_module', 'another_module']
```

### Issue: EXE too large (>100MB)

**Solution:**
```powershell
# Check spec file for unnecessary includes
# Remove debug symbols:
# In spec file, ensure 'debug=False' in EXE()

# Use UPX compression (if installed)
# Add to spec: upx=True, upx_exclude=[]
```

### Issue: EXE won't start (missing DLLs)

**Solution:**
```powershell
# Run from command line to see errors
dist\NetworkSwissToolPro_v6_5_7.exe

# Check for missing dependencies
python -m pip install --upgrade pyinstaller

# Rebuild with --clean
python -m PyInstaller build_scripts\NetworkSwissToolPro_v6_5_1.spec --clean
```

---

## 📊 Build Checklist

| Step | Task | Status | Time |
|------|------|--------|------|
| 1 | Clean previous builds | ⬜ | 1m |
| 2 | Verify prerequisites | ⬜ | 2m |
| 3 | Run PyInstaller build | ⬜ | 5-8m |
| 4 | Package distribution | ⬜ | 1m |
| 5 | Verify EXE launches | ⬜ | 2m |
| 6 | Run QA suite | ⬜ | 15m |
| **Total** | | | **~30m** |

---

## 🧪 Final Verification Checklist

### Build Verification

- [ ] EXE file exists in `dist_package_v6_5_8_FINAL/`
- [ ] EXE size is 70-80 MB
- [ ] Release notes copied to distribution folder
- [ ] VERSION file shows `v6.5.8`

### Functional Verification

- [ ] Web UI starts on `http://127.0.0.1:5051`
- [ ] CLI Terminal connects without timeout errors
- [ ] Standards Validator loads all policies from file
- [ ] Standards Validator shows category checkboxes
- [ ] Standards bulk runs generate consolidated report
- [ ] vPC Map shows domain visualization
- [ ] Interface descriptions appear in MAPS popups
- [ ] Linux server SSH connection works

### QA Sign-off

- [ ] All tests in `docs/03_QA/QA_TESTING_CHECKLIST.txt` pass
- [ ] No console errors during operation
- [ ] Works in offline environment (no internet required)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| v6.5.8 | 2026-04-30 | Linux support, consolidated reports, category checkboxes |
| v6.5.7 | 2026-04-29 | CLI timeout fixes, policy loading fixes |
| v6.5.6 | 2026-04-28 | UI/UX improvements |
| v6.5.3 | 2026-04-25 | Standards Validator v2.0 |
| v6.2.2 | 2026-04-21 | ThreadPoolExecutor fix |

---

## 🚀 Ready to Build?

**Quick Start:**
```powershell
python -m PyInstaller build_scripts\NetworkSwissToolPro_v6_5_1.spec --clean --noconfirm
```

**Full Process:**
1. Verify prerequisites
2. Run build command
3. Package distribution
4. Run QA tests
5. Release!

**For detailed QA procedures:**
→ See `docs/03_QA/QA_TESTING_CHECKLIST.txt`

**For release procedures:**
→ See `docs/02_RELEASES/README.md`

---

## 📚 Additional Resources

| Document | Purpose |
|----------|---------|
| `build_scripts/NetworkSwissToolPro_v6_5_1.spec` | PyInstaller specification file |
| `docs/00_MASTER/00-MASTER-BRAIN.md` | Architecture overview |
| `docs/03_QA/QA_TESTING_CHECKLIST.txt` | QA procedures |
| `docs/04_TROUBLESHOOTING/06-TROUBLESHOOTING.md` | Common issues & fixes |
| `docs/02_RELEASES/RELEASE_NOTES_6.5.8.md` | Current version details |

---

## 🎓 Tips for Success

1. **Use --clean flag** - Ensures fresh build without cached issues
2. **Check spec file** - Verify all modules are included in hiddenimports
3. **Test immediately** - Don't wait to test the EXE
4. **Log output** - Use Tee-Object to capture build logs
5. **Version control** - Tag successful builds: `git tag v6.5.8`

---

## 🚀 Ready to Build?

**Quick Command:**
```powershell
python -m PyInstaller build_scripts\NetworkSwissToolPro_v6_5_1.spec --clean --noconfirm
```

**Full QA after build:**
→ See `docs/03_QA/QA_TESTING_CHECKLIST.txt`

**Good luck!**
