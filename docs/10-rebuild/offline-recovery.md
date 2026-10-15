# Offline Recovery

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Procedures for recovering and operating NetworkSwissToolPro in air-gapped/offline environments without internet access. |
| **Scope** | Complete offline deployment, dependency restoration, wheel cache management, and air-gapped operations. |
| **Responsibilities** | Disaster recovery for environments with no internet connectivity. |
| **Dependencies** | Offline wheel cache (`paramiko_deps/`), pre-built EXE, or complete source code snapshot. |
| **Related Documents** | [from-zero-installation.md](from-zero-installation.md), [exact-rebuild-procedure.md](exact-rebuild-procedure.md), [dependency-restoration.md](dependency-restoration.md) |
| **Operational Impact** | Enables operations in secure air-gapped environments, SCADA networks, and isolated data centers. |
| **Failure Conditions** | Missing wheel cache, corrupted dependencies, incomplete source snapshot, missing policy files. |
| **Recovery Notes** | Use pre-built EXE for fastest recovery. Rebuild from source with wheel cache if EXE unavailable. |
| **Version Awareness** | v6.9.5 |
| **Last Synchronization Timestamp** | 2026-05-25 |
| **Maintainer** | LIBRARIAN / DevOps Lead |

---

# OFFLINE DEPLOYMENT SCENARIOS

## Scenario A: Pre-built EXE (Fastest Recovery)

**Use when:** You have the pre-built executable and need immediate deployment.

**Time:** 5 minutes

**Steps:**
1. Copy `NetworkSwissToolPro_v6.9.5_OFFLINE.exe` to target machine
2. Copy `policies/` directory to same location as EXE
3. Copy `inventory.txt` to same location as EXE
4. Launch EXE
5. Verify operation

---

## Scenario B: Source Code + Wheel Cache (Standard Recovery)

**Use when:** You have complete source code and dependency wheel cache.

**Time:** 15-20 minutes

**Steps:**
1. Copy entire source directory to target machine
2. Install Python 3.12+ (offline installer if needed)
3. Install dependencies from wheel cache
4. Launch application
5. Verify operation

---

## Scenario C: Source Code Only (Full Rebuild)

**Use when:** You have source code but no wheel cache or internet.

**Time:** 30-45 minutes (requires manual dependency transfer)

**Steps:**
1. Copy source code to target machine
2. Install Python 3.12+ (offline installer)
3. Manually transfer dependencies via USB/external media
4. Install dependencies
5. Launch application
6. Verify operation

---

# PRE-REQUISITES FOR OFFLINE RECOVERY

## Required Artifacts

### For Scenario A (EXE Only)
- `NetworkSwissToolPro_v6.9.5_OFFLINE.exe` (~75 MB)
- `policies/` directory (with `standards.yaml`)
- `inventory.txt` (or create new)

### For Scenario B (Source + Wheels)
- Complete source directory
- `paramiko_deps/` wheel cache directory
- Python 3.12+ offline installer (optional)

### For Scenario C (Source Only)
- Complete source directory
- Python 3.12+ offline installer
- External media for dependency transfer

---

# SCENARIO A: PRE-BUILT EXE DEPLOYMENT

## Step 1: Transfer Artifacts

```powershell
# On source machine (with internet)
# Copy to USB/external media
copy NetworkSwissToolPro_v6.9.5_OFFLINE.exe E:\
xcopy /E /I policies E:\policies
copy inventory.txt E:\

# On target machine (air-gapped)
# Copy from USB/external media
copy E:\NetworkSwissToolPro_v6.9.5_OFFLINE.exe C:\NetworkSwissToolPro\
xcopy /E /I E:\policies C:\NetworkSwissToolPro\policies
copy E:\inventory.txt C:\NetworkSwissToolPro\
```

## Step 2: Directory Structure Verification

```powershell
cd C:\NetworkSwissToolPro

# Verify structure
dir
# Expected:
# NetworkSwissToolPro_v6.9.5_OFFLINE.exe
# policies/
# inventory.txt

# Verify policies
dir policies
# Expected:
# standards.yaml
```

## Step 3: Launch Application

```powershell
# Launch EXE
.\NetworkSwissToolPro_v6.9.5_OFFLINE.exe

# Expected output:
# Application window opens
# Server starts on http://127.0.0.1:5051
# Browser opens automatically
```

## Step 4: Verification

```powershell
# Test web UI access
# Open browser to http://127.0.0.1:5051

# Test CLI Terminal
# Navigate to CLI Terminal tab
# Attempt connection to test device

# Test Standards Validator
# Navigate to Standards Validator tab
# Verify policies load correctly
```

---

# SCENARIO B: SOURCE CODE + WHEEL CACHE

## Step 1: Transfer Source and Dependencies

```powershell
# On source machine
# Copy entire source directory
xcopy /E /I "Net_mngmnt_tool - V6 - cursor" E:\source_backup

# On target machine
# Copy from external media
xcopy /E /I E:\source_backup "C:\Net_mngmnt_tool - V6 - cursor"
```

## Step 2: Install Python (Offline)

```powershell
# If Python not already installed
# Use offline installer from external media
E:\python-3.14.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

# Verify installation
python --version
# Expected: Python 3.14.0
```

## Step 3: Install Dependencies from Wheel Cache

```powershell
cd "C:\Net_mngmnt_tool - V6 - cursor"

# Install from local wheel cache
pip install --no-index --find-links=paramiko_deps -r requirements.txt

# Verify installation
pip list
```

## Step 4: Launch Application

```powershell
# Launch in development mode
python vlan_checker_web.py

# Expected output:
# Server starting on http://127.0.0.1:5051
# Browser opens automatically
```

## Step 5: Verification

```powershell
# Test imports
python -c "import netmiko; print('✓ netmiko OK')"
python -c "import flask; print('✓ flask OK')"
python -c "from modules import network_base; print('✓ network_base OK')"

# Test web UI
# Open browser to http://127.0.0.1:5051
```

---

# SCENARIO C: SOURCE CODE ONLY (FULL REBUILD)

## Step 1: Transfer Source Code

```powershell
# On source machine
xcopy /E /I "Net_mngmnt_tool - V6 - cursor" E:\source_backup

# On target machine
xcopy /E /I E:\source_backup "C:\Net_mngmnt_tool - V6 - cursor"
```

## Step 2: Install Python (Offline)

```powershell
# Use offline installer
E:\python-3.14.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

# Verify
python --version
```

## Step 3: Create Wheel Cache (On Connected Machine)

**This step must be done on a machine with internet access BEFORE air-gapping:**

```powershell
# On connected machine
cd "Net_mngmnt_tool - V6 - cursor"

# Download all dependencies to wheel cache
pip download -r requirements.txt -d paramiko_deps/

# Verify wheel cache
dir paramiko_deps
# Expected: 20-30 .whl files
```

## Step 4: Transfer Wheel Cache

```powershell
# Copy wheel cache to external media
xcopy /E /I paramiko_deps E:\wheel_cache

# On target machine
xcopy /E /I E:\wheel_cache "C:\Net_mngmnt_tool - V6 - cursor\paramiko_deps"
```

## Step 5: Install Dependencies

```powershell
cd "C:\Net_mngmnt_tool - V6 - cursor"

# Install from wheel cache
pip install --no-index --find-links=paramiko_deps -r requirements.txt

# Verify
pip list
```

## Step 6: Launch and Verify

```powershell
# Launch application
python vlan_checker_web.py

# Verify operation
# Open browser to http://127.0.0.1:5051
```

---

# WHEEL CACHE MANAGEMENT

## Creating Wheel Cache

```powershell
# Download all dependencies
pip download -r requirements.txt -d paramiko_deps/

# Include build dependencies
pip download pyinstaller -d paramiko_deps/

# Verify cache contents
dir paramiko_deps
```

## Wheel Cache Contents (v6.9.5)

Expected wheel files in `paramiko_deps/`:
- `netmiko-4.1.2-py3-none-any.whl`
- `Flask-3.1.3-py3-none-any.whl`
- `Flask_SocketIO-5.4.1-py3-none-any.whl`
- `python_socketio-5.12.1-py3-none-any.whl`
- `python_engineio-4.11.2-py3-none-any.whl`
- `simple_websocket-1.1.0-py3-none-any.whl`
- `wsproto-1.3.2-py3-none-any.whl`
- `bidict-0.23.1-py3-none-any.whl`
- `h11-0.16.0-py3-none-any.whl`
- `paramiko-3.4.0-py3-none-any.whl`
- `cryptography-46.0.3-cp312-cp312-win_amd64.whl`
- `bcrypt-5.0.0-cp39-abi3-win_amd64.whl`
- `cffi-2.0.0-cp312-cp312-win_amd64.whl`
- `pycparser-2.21-py2.py3-none-any.whl`
- `pyinstaller-6.19.0-py3-none-any.whl`

## Validating Wheel Cache

```powershell
# Check all required wheels exist
$required = @("netmiko", "Flask", "Flask_SocketIO", "paramiko", "cryptography")
foreach ($req in $required) {
    if (Get-ChildItem paramiko_deps -Filter "*$req*") {
        Write-Host "✓ $req found" -ForegroundColor Green
    } else {
        Write-Host "✗ $req MISSING" -ForegroundColor Red
    }
}
```

---

# AIR-GAPPED OPERATIONS

## Policy File Management

```powershell
# Policies must be in policies/ directory
# Verify policies directory
Test-Path "policies"

# Verify standards.yaml
Test-Path "policies\standards.yaml"

# If missing, copy from backup
copy E:\backup\policies\standards.yaml policies\
```

## Inventory Management

```powershell
# Create inventory file
notepad inventory.txt

# Format: IP,device_type,username,password
# Example:
# 192.168.1.1,cisco,admin,password
# 192.168.1.2,juniper,admin,password
```

## Logging Configuration

```powershell
# Logs directory must be writable
mkdir logs -ErrorAction SilentlyContinue

# Test logging
python -c "import os; open('logs\test.log', 'w').write('test')"

# Verify
Test-Path "logs\test.log"
```

---

# TROUBLESHOOTING OFFLINE ISSUES

## Issue: "No matching distribution found"

**Cause:** Wheel cache incomplete or corrupted

**Solution:**
```powershell
# Rebuild wheel cache on connected machine
pip download -r requirements.txt -d paramiko_deps/ --force-reinstall

# Transfer to air-gapped machine
# Reinstall dependencies
pip install --no-index --find-links=paramiko_deps -r requirements.txt --force-reinstall
```

## Issue: "Missing policy file"

**Cause:** `policies/` directory not copied

**Solution:**
```powershell
# Copy policies from backup
xcopy /E /I E:\backup\policies policies\

# Verify
Test-Path "policies\standards.yaml"
```

## Issue: "Cannot connect to PyPI"

**Cause:** pip trying to access internet

**Solution:**
```powershell
# Ensure --no-index flag is used
pip install --no-index --find-links=paramiko_deps -r requirements.txt
```

## Issue: "EXE won't launch"

**Cause:** Missing dependencies or corrupted file

**Solution:**
```powershell
# Verify EXE integrity
# Check file size (~75 MB)
Get-Item NetworkSwissToolPro_v6.9.5_OFFLINE.exe | Select-Object Length

# If corrupted, copy fresh EXE from backup
copy E:\backup\NetworkSwissToolPro_v6.9.5_OFFLINE.exe .
```

---

# VALIDATION CHECKLIST

## Pre-Deployment Validation

- [ ] All required artifacts transferred (EXE or source + wheels)
- [ ] Python 3.12+ installed (if using source)
- [ ] Wheel cache complete (if using source)
- [ ] Policies directory copied
- [ ] Inventory file created or copied
- [ ] Sufficient disk space available

## Post-Deployment Validation

- [ ] Application launches without errors
- [ ] Web UI accessible at http://127.0.0.1:5051
- [ ] CLI Terminal tab loads
- [ ] Standards Validator tab loads
- [ ] Policy files load correctly
- [ ] Logs directory writable
- [ ] No internet connection required for operation

## Functional Validation

- [ ] Can connect to network devices
- [ ] VLAN operations work
- [ ] Topology mapping generates
- [ ] Standards validation runs
- [ ] Reports generate correctly
- [ ] CLI Terminal functions

---

# OFFLINE RECOVERY KIT

## Recommended Recovery Kit Contents

Create a recovery kit USB drive with:

```
/NetworkSwissToolPro_Recovery_v6.9.5/
├── NetworkSwissToolPro_v6.9.5_OFFLINE.exe
├── policies/
│   └── standards.yaml
├── inventory.txt (template)
├── paramiko_deps/ (wheel cache)
├── python-3.14.0-amd64.exe (offline installer)
├── source_code/ (complete source backup)
├── README_OFFLINE_RECOVERY.txt
└── docs/
    └── 10-rebuild/
        ├── offline-recovery.md
        ├── from-zero-installation.md
        └── exact-rebuild-procedure.md
```

## Recovery Kit Creation Script

```powershell
# Create recovery kit on connected machine
$recoveryDir = "E:\NetworkSwissToolPro_Recovery_v6.9.5"
New-Item -ItemType Directory -Force -Path $recoveryDir

# Copy EXE
copy "dist\NetworkSwissToolPro_v6.9.5_OFFLINE.exe" $recoveryDir\

# Copy policies
xcopy /E /I policies $recoveryDir\policies\

# Copy wheel cache
xcopy /E /I paramiko_deps $recoveryDir\paramiko_deps\

# Copy source
xcopy /E /I . $recoveryDir\source_code\

# Copy Python installer (if available)
copy "E:\python-3.14.0-amd64.exe" $recoveryDir\

# Copy documentation
xcopy /E /I docs $recoveryDir\docs\

# Create README
"OFFLINE RECOVERY KIT v6.9.5" | Out-File "$recoveryDir\README_OFFLINE_RECOVERY.txt"
```

---

# ESTIMATED RECOVERY TIMES

| Scenario | Time | Complexity |
|----------|------|------------|
| EXE Only | 5 minutes | Low |
| Source + Wheels | 15-20 minutes | Medium |
| Source Only | 30-45 minutes | High |

---

# SUCCESS CRITERIA

Offline recovery is successful when:

1. Application launches without internet connection
2. Web UI accessible at http://127.0.0.1:5051
3. All critical features work (CLI, Standards Validator, MAPS)
4. No external dependencies required
5. Policy files load correctly
6. Device connections work
7. Reports generate successfully

---

# MAINTENANCE

## Updating Offline Recovery Kit

When new version is released:

1. Rebuild wheel cache with new dependencies
2. Create new EXE with updated version
3. Update policy files if changed
4. Test recovery procedures
5. Update recovery kit documentation
6. Label recovery kit with version number

## Periodic Validation

Every 6 months:

1. Test recovery procedures in isolated environment
2. Verify wheel cache integrity
3. Check Python installer compatibility
4. Validate EXE functionality
5. Update documentation if needed

---

**Document Status:** ACTIVE
**Classification:** TIER-0 DISASTER RECOVERY
**Enforcement:** MANDATORY
**Drift Tolerance:** ZERO
