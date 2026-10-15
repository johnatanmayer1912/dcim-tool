# MASTER RECOVERY PROCEDURE

> **"When shit hits the fan" - Complete rebuild from zero**

**Version:** 5.0.0  
**Recovery Time Objective (RTO):** 90 minutes  
**Last Tested:** 2026-04-19  
**Status:** PRODUCTION READY

---

## 🚨 When to Use This Document

### Emergency Scenarios
- [ ] Total system loss (hardware failure)
- [ ] Corrupted repository beyond repair
- [ ] Ransomware/malware infection
- [ ] Accidental deletion of entire codebase
- [ ] Need to onboard new environment from scratch
- [ ] Disaster recovery drill

### Non-Emergency Scenarios
- [ ] Setting up new developer workstation
- [ ] Migrating to new infrastructure
- [ ] Creating isolated test environment
- [ ] Forking project for customization

---

## ⏱️ Recovery Timeline

| Phase | Time | Checkpoint |
|-------|------|------------|
| **Phase 1: Environment** | 0-15 min | Python + dependencies installed |
| **Phase 2: Source Code** | 15-30 min | All source files restored |
| **Phase 3: Configuration** | 30-45 min | Config files in place |
| **Phase 4: Build** | 45-75 min | Executable compiled |
| **Phase 5: Verify** | 75-90 min | All tests pass |

---

## 📋 Phase 1: Environment Setup (0-15 min)

### 1.1 Verify Python Installation

```powershell
# Windows PowerShell
python --version  # Should show 3.9+
python -c "import sys; print(sys.version_info)"
```

**Checkpoint 1.1:** Python version ≥ 3.9
- [ ] Verified

### 1.2 Create Project Directory

```powershell
# Windows
$PROJECT_ROOT = "C:\NetworkSwissToolPro"
New-Item -ItemType Directory -Force -Path $PROJECT_ROOT
Set-Location $PROJECT_ROOT
```

**Checkpoint 1.2:** Directory created and accessible
- [ ] Verified

### 1.3 Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

**Checkpoint 1.3:** Virtual environment activated (prompt shows "venv")
- [ ] Verified

### 1.4 Install Core Dependencies

Create `requirements.txt`:

```
netmiko==4.1.2
flask
flask-socketio>=5.3.0
python-socketio>=5.7.0
pyinstaller
```

Install:
```powershell
pip install -r requirements.txt
```

**Checkpoint 1.4:** All packages installed without errors
- [ ] Verified

---

## 📋 Phase 2: Source Code Restoration (15-30 min)

### Option A: Git Repository (Preferred)

```powershell
git clone <repository-url> .
git checkout main  # or production branch
git log --oneline -5  # Verify recent commits
```

### Option B: Source Archive

```powershell
# If you have a zip backup
Expand-Archive -Path "NetworkSwissToolPro_v5.0.0_backup.zip" -DestinationPath . -Force
```

### Option C: Manual File Creation (Last Resort)

If you only have this document and the README, create files manually from:
1. The code examples in documentation
2. The specification files
3. The architecture diagrams

**Note:** This option is NOT recommended. Always maintain off-site backups.

### 2.1 Verify Project Structure

Required structure:
```
NetworkSwissToolPro/
├── vlan_checker_web.py          # Main Flask app
├── main.py                      # CLI entry point
├── telnetlib_compat.py          # Python 3.14 compatibility
├── modules/
│   ├── __init__.py
│   ├── adapters.py
│   ├── cli_manager.py           # v5.0 - CLI terminal
│   ├── config_backup.py
│   ├── connectivity.py
│   ├── interfaces.py
│   ├── mac_trace.py
│   ├── network_base.py
│   ├── save_config.py
│   ├── topology_mapper.py
│   ├── vlan_audit.py
│   ├── vlan_compare.py
│   ├── vlan_mgmt.py
│   └── web/
│       ├── __init__.py
│       ├── vis-network.min.js
│       └── templates/
│           ├── base.html
│           ├── cli_terminal.html    # v5.0 - CLI terminal
│           ├── index.html
│           └── topology_result.html
├── utils/
│   ├── __init__.py
│   ├── csv_formatter.py
│   ├── html_generator.py
│   └── report_formatter.py
└── docs/                        # Documentation (critical!)
```

**Checkpoint 2.1:** All required files present
- [ ] vlan_checker_web.py
- [ ] main.py
- [ ] telnetlib_compat.py
- [ ] modules/ directory complete
- [ ] utils/ directory complete
- [ ] docs/ directory complete

### 2.2 Verify File Integrity

```powershell
# Check for syntax errors
Get-ChildItem -Filter "*.py" -Recurse | ForEach-Object {
    $result = python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $($_.Name)"
    } else {
        Write-Host "✗ $($_.Name) - SYNTAX ERROR"
    }
}
```

**Checkpoint 2.2:** No syntax errors
- [ ] All files compile successfully

---

## 📋 Phase 3: Configuration (30-45 min)

### 3.1 Create VERSION File

```powershell
"5.0.0" | Out-File -FilePath "VERSION" -Encoding utf8
```

### 3.2 Create README.md

Copy content from documentation or create minimal:

```markdown
# Network Swiss Tool Pro v5.0.0

Network automation tool for VLAN management, MAC tracing, and topology mapping.

## Quick Start
1. Run `python vlan_checker_web.py`
2. Open browser to http://localhost:5000
3. Load inventory or add devices

## Features
- VLAN Audit & Management
- MAC Address Trace
- Network Topology Mapping
- CLI Terminal (v5.0)
- Multi-vendor support

See docs/ for complete documentation.
```

### 3.3 Verify Critical Configuration Files

Check existence of:
- [ ] VERSION
- [ ] README.md
- [ ] CHANGELOG.md
- [ ] requirements.txt
- [ ] NetworkSwissToolPro_v5_0_0_Web.spec (for builds)

### 3.4 Test Basic Functionality

```powershell
# Test 1: Import all modules
python -c "
from modules.network_base import *
from modules.vlan_audit import *
from modules.vlan_mgmt import *
from modules.mac_trace import *
from modules.topology_mapper import *
from modules.cli_manager import *  # v5.0
from modules.adapters import *
from modules.interfaces import *
from utils.report_formatter import *
print('✓ All imports successful')
"
```

**Checkpoint 3.4:** All modules import correctly
- [ ] Verified

---

## 📋 Phase 4: Build (45-75 min)

### 4.1 Prepare Build Environment

```powershell
# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### 4.2 Verify Spec File

Ensure `NetworkSwissToolPro_v5_0_0_Web.spec` exists and contains:
- All required hidden imports
- Data files paths (templates, etc.)
- Correct version references

**Checkpoint 4.2:** Spec file validated
- [ ] File exists
- [ ] Version shows 5.0.0
- [ ] All modules listed in hiddenimports
- [ ] Web templates included in datas

### 4.3 Execute Build

```powershell
pyinstaller --clean --noconfirm NetworkSwissToolPro_v5_0_0_Web.spec
```

**Expected Output:**
- Console shows build progress
- Multiple warnings (normal)
- Final message: "Building EXE completed successfully"

**Duration:** 15-30 minutes

**Checkpoint 4.3:** Build completed
- [ ] No fatal errors
- [ ] EXE file created in dist/

### 4.4 Verify Build Output

```powershell
# Check executable exists
$exe = "dist\NetworkSwissToolPro_v5_0_0_Web.exe"
if (Test-Path $exe) {
    $size = (Get-Item $exe).Length / 1MB
    Write-Host "✓ EXE created: $([math]::Round($size,1)) MB"
} else {
    Write-Host "✗ EXE not found"
}
```

**Expected Size:** 15-25 MB

**Checkpoint 4.4:** Executable size reasonable
- [ ] Size > 10 MB (indicates bundling worked)
- [ ] Size < 50 MB (indicates no bloat)

---

## 📋 Phase 5: Verification (75-90 min)

### 5.1 Basic Launch Test

```powershell
# Launch executable
dist\NetworkSwissToolPro_v5_0_0_Web.exe
```

**Expected:**
- Console window opens
- Shows Flask startup messages
- Message: "Running on http://127.0.0.1:5000"

**Wait 10 seconds then check:**
- [ ] Process running in Task Manager
- [ ] Port 5000 listening (if no conflicts)
- [ ] No crash dialogs

**Checkpoint 5.1:** Application launches
- [ ] Starts without errors
- [ ] Web server accessible

### 5.2 Web Interface Test

1. Open browser to `http://localhost:5000`
2. Verify UI loads:
   - [ ] Title shows "Network Swiss Tool Pro"
   - [ ] All dropdowns populated
   - [ ] Buttons clickable
   - [ ] No JavaScript errors in console

**Checkpoint 5.2:** Web interface functional
- [ ] Loads correctly
- [ ] All elements present

### 5.3 Core Functionality Test

#### Test 1: Inventory Loading
- [ ] Add test inventory file
- [ ] Verify devices appear in dropdown

#### Test 2: Connection Test
- [ ] Select device from inventory
- [ ] Click "Check Connection"
- [ ] Verify connection status displayed

#### Test 3: Feature Execution
- [ ] Run "VLAN Audit" on single device
- [ ] Verify output generates
- [ ] Check no Python errors in console

#### Test 4: CLI Terminal (v5.0)
- [ ] Click "Connect via CLI" button
- [ ] Verify new tab opens
- [ ] Check terminal loads with xterm.js
- [ ] Test connection dialog appears

**Checkpoint 5.3:** Core features working
- [ ] Inventory management OK
- [ ] Device connection OK
- [ ] VLAN Audit OK
- [ ] CLI Terminal loads

### 5.4 Create Distribution Package

```powershell
# Create distribution folder
New-Item -ItemType Directory -Force -Path "dist_package_web"

# Copy essential files
Copy-Item "dist\NetworkSwissToolPro_v5_0_0_Web.exe" "dist_package_web\"
Copy-Item "VERSION" "dist_package_web\"
Copy-Item "README.md" "dist_package_web\"
Copy-Item "CHANGELOG.md" "dist_package_web\"
Copy-Item "RELEASE_NOTES_5.0.0.md" "dist_package_web\"
Copy-Item "requirements.txt" "dist_package_web\"
Copy-Item -Recurse "docs" "dist_package_web\docs"

# Create archive
Compress-Archive -Path "dist_package_web\*" -DestinationPath "NetworkSwissToolPro_v5.0.0_Release.zip" -Force
```

**Checkpoint 5.4:** Distribution package ready
- [ ] All files in dist_package_web/
- [ ] Archive created
- [ ] Ready for deployment

---

## ✅ FINAL CHECKPOINT: Recovery Complete

**System Status:**
- [ ] Environment ready (15 min target) ⏱️
- [ ] Source code restored (30 min target) ⏱️
- [ ] Configuration complete (45 min target) ⏱️
- [ ] Build successful (75 min target) ⏱️
- [ ] Verification passed (90 min target) ⏱️

**Total Recovery Time:** _____ minutes

**If ≤ 90 minutes:** ✅ SUCCESS
**If > 90 minutes:** Document bottlenecks for future optimization

---

## 🔧 Post-Recovery Actions

### Immediate (Do Now)
1. [ ] Test on another machine
2. [ ] Run full QA suite (see `../03_QA_TESTING/MASTER_QA_SUITE.md`)
3. [ ] Create backup of successful build
4. [ ] Document any deviations from procedure

### Short-term (This Week)
1. [ ] Set up automated backups
2. [ ] Configure CI/CD pipeline
3. [ ] Update off-site repository
4. [ ] Schedule disaster recovery drill (monthly)

### Long-term (This Month)
1. [ ] Implement automated testing
2. [ ] Create deployment automation
3. [ ] Document lessons learned
4. [ ] Update this procedure with improvements

---

## 🆘 Troubleshooting Recovery Failures

### Build Fails
**Symptom:** PyInstaller errors
**Solution:** 
1. Check Python version (must be 3.9+)
2. Verify all imports in spec file
3. Delete `build/` and retry
4. Check `build/warn-*.txt` for missing modules

### Import Errors
**Symptom:** Module not found
**Solution:**
1. Verify file exists in modules/
2. Check `__init__.py` present
3. Add to spec file hiddenimports
4. Rebuild

### Web Interface Won't Load
**Symptom:** 404 or blank page
**Solution:**
1. Verify templates in spec file datas
2. Check template paths in code
3. Ensure vis-network.min.js bundled
4. Check browser console for errors

### CLI Terminal Won't Connect
**Symptom:** Connection fails
**Solution:**
1. Verify flask-socketio installed
2. Check browser WebSocket support
3. Test with simple SocketIO example
4. Review `modules/cli_manager.py`

---

## 📞 Emergency Contacts

**If Recovery Fails:**
1. **Check logs:** `build/warn-*.txt`, console output
2. **Review docs:** `04_TROUBLESHOOTING/`
3. **Ask team:** Post in #emergency Slack channel
4. **Escalate:** Contact Tech Lead if > 2 hours

---

## 📝 Recovery Log Template

```
Recovery Date: _______________
Performed By: ________________
Reason: ______________________

Phase 1 (Environment): ___ min
Phase 2 (Source Code): ___ min
Phase 3 (Configuration): ___ min
Phase 4 (Build): ___ min
Phase 5 (Verify): ___ min

Total Time: ___ min
Target: 90 min
Deviation: ___ min

Issues Encountered:
1. ___________________________
2. ___________________________

Resolution Applied:
1. ___________________________
2. ___________________________

Lessons Learned:
_________________________________
_________________________________

Recommended Procedure Updates:
_________________________________
_________________________________

Signed: _________________ Date: _________
```

---

## 🎯 Success Metrics

**Recovery is successful when:**
- ✅ Executable launches without errors
- ✅ Web interface loads completely
- ✅ Core features (VLAN, MAC, Topology) work
- ✅ CLI Terminal feature loads (v5.0)
- ✅ All QA tests pass
- ✅ Total time ≤ 90 minutes

---

**Remember:** This document is tested monthly. If it doesn't work, the document is broken, not the procedure.

**Document Owner:** Tech Lead  
**Last Full Test:** 2026-04-19  
**Next Scheduled Test:** 2026-05-19

---

*This document is the difference between a 90-minute recovery and a 3-day disaster.*
