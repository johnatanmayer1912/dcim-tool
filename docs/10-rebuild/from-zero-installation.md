# From Zero Installation

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Complete step-by-step instructions for installing NetworkSwissToolPro from scratch on a new machine with zero prior setup. |
| **Scope** | Fresh Windows machine setup, Python environment configuration, dependency installation, and initial application launch. |
| **Responsibilities** | Complete environment reconstruction from bare metal to running application. |
| **Dependencies** | Windows 10/11, internet connection (for initial setup), administrative privileges. |
| **Related Documents** | [exact-rebuild-procedure.md](exact-rebuild-procedure.md), [build-process.md](build-process.md), [offline-recovery.md](offline-recovery.md) |
| **Operational Impact** | Enables rapid deployment on new machines or disaster recovery scenarios. |
| **Failure Conditions** | Python installation fails, dependency conflicts, insufficient permissions, network connectivity issues. |
| **Recovery Notes** | If Python installation fails, use Windows Store or official installer. If dependencies fail, use offline wheel cache. |
| **Version Awareness** | v6.9.5 |
| **Last Synchronization Timestamp** | 2026-05-25 |
| **Maintainer** | LIBRARIAN / DevOps Lead |

---

# PREREQUISITES

## System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| Operating System | Windows 10 (1909+) | Windows 11 |
| RAM | 4 GB | 8 GB |
| Disk Space | 500 MB | 1 GB |
| Python Version | 3.12, 3.13, 3.14 | 3.14 |
| Internet | Required for initial setup | Not required after installation |

## Administrative Privileges

Required for:
- Python installation
- PyInstaller builds (if building from source)
- Firewall configuration (if needed)

---

# STEP 1: PYTHON INSTALLATION

## Option A: Official Installer (Recommended)

1. Download Python 3.14 from https://www.python.org/downloads/
2. Run installer with **IMPORTANT** settings:
   - ✅ **"Add Python to PATH"** (CRITICAL - must check this)
   - ✅ "Install for all users" (optional but recommended)
3. Verify installation:
   ```powershell
   python --version
   # Expected: Python 3.14.x
   ```

## Option B: Windows Store

```powershell
# Install from Microsoft Store
winget install Python.Python.3.14

# Verify
python --version
```

## Option C: Chocolatey

```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Python
choco install python3 -y

# Verify
python --version
```

---

# STEP 2: DEPENDENCY INSTALLATION

## Online Installation (With Internet)

```powershell
# Navigate to project directory
cd "c:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\Net_mngmnt_tool - V6 - cursor"

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Verify installation
pip list
```

## Offline Installation (Without Internet)

If you have the `paramiko_deps/` wheel cache:

```powershell
# Install from local wheel cache
pip install --no-index --find-links=paramiko_deps netmiko
pip install --no-index --find-links=paramiko_deps Flask
pip install --no-index --find-links=paramiko_deps Flask-SocketIO
pip install --no-index --find-links=paramiko_deps pandas
pip install --no-index --find-links=paramiko_deps openpyxl
pip install --no-index --find-links=paramiko_deps paramiko
pip install --no-index --find-links=paramiko_deps cryptography
```

---

# STEP 3: APPLICATION LAUNCH

## Development Mode (Source Code)

```powershell
# Navigate to project directory
cd "c:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\Net_mngmnt_tool - V6 - cursor"

# Launch application
python vlan_checker_web.py

# Expected output:
# Server starting on http://127.0.0.1:5051
# Browser should open automatically
```

## Production Mode (Pre-built EXE)

If you have the pre-built executable:

```powershell
# Navigate to distribution directory
cd "dist_package_v6.9.5"

# Launch application
.\NetworkSwissToolPro_v6.9.5_OFFLINE.exe

# Expected output:
# Application window opens
# Server starts on http://127.0.0.1:5051
```

---

# STEP 4: VERIFICATION

## Basic Health Check

1. **Web UI Access**
   - Open browser to `http://127.0.0.1:5051`
   - Verify login page loads
   - Check for console errors (F12)

2. **Directory Structure**
   ```powershell
   # Verify critical directories exist
   Test-Path "modules"
   Test-Path "utils"
   Test-Path "inventory"
   Test-Path "logs"
   Test-Path "plugins"
   ```

3. **Import Test**
   ```powershell
   # Test critical imports
   python -c "import netmiko; print('✓ netmiko OK')"
   python -c "import flask; print('✓ flask OK')"
   python -c "import paramiko; print('✓ paramiko OK')"
   python -c "from modules import network_base; print('✓ network_base OK')"
   ```

## Functional Verification

1. **Create Test Inventory**
   ```powershell
   # Create sample inventory file
   echo "192.168.1.1,cisco,admin,password" > inventory.txt
   ```

2. **Test CLI Terminal**
   - Open CLI Terminal tab
   - Attempt connection to test device
   - Verify timeout works (30s)

3. **Test Standards Validator**
   - Navigate to Standards Validator tab
   - Verify policy file loads
   - Check category checkboxes appear

---

# STEP 5: CONFIGURATION

## Inventory Setup

```powershell
# Create inventory file
notepad inventory.txt

# Format: IP,device_type,username,password
# Example:
# 192.168.1.1,cisco,admin,password
# 192.168.1.2,juniper,admin,password
```

## Policy Setup

```powershell
# Verify policies directory exists
Test-Path "policies"

# Verify standards.yaml exists
Test-Path "policies\standards.yaml"
```

## Logging Setup

```powershell
# Verify logs directory exists
Test-Path "logs"

# Verify logs can be written
python -c "import os; os.makedirs('logs', exist_ok=True); open('logs\test.log', 'w').write('test'); print('✓ Logging OK')"
```

---

# TROUBLESHOOTING

## Issue: "Python is not recognized"

**Cause:** Python not added to PATH during installation

**Solution:**
```powershell
# Add Python to PATH manually
$env:Path += ";C:\Python314;C:\Python314\Scripts"

# Or reinstall Python with "Add to PATH" checked
```

## Issue: "ModuleNotFoundError"

**Cause:** Dependencies not installed

**Solution:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Issue: "Permission denied"

**Cause:** Insufficient administrative privileges

**Solution:**
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell -> "Run as administrator"
```

## Issue: "Port 5051 already in use"

**Cause:** Another application using the port

**Solution:**
```powershell
# Find process using port 5051
netstat -ano | findstr :5051

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

# VALIDATION CHECKLIST

## Installation Validation

- [ ] Python 3.12+ installed and accessible
- [ ] All dependencies installed successfully
- [ ] Application launches without errors
- [ ] Web UI accessible at http://127.0.0.1:5051
- [ ] Critical directories exist (modules, utils, inventory, logs, plugins)
- [ ] Import tests pass for all critical modules

## Functional Validation

- [ ] CLI Terminal tab loads
- [ ] Standards Validator tab loads
- [ ] Inventory file can be created/edited
- [ ] Policy files load correctly
- [ ] Logs directory is writable
- [ ] No console errors on startup

## Configuration Validation

- [ ] inventory.txt created with proper format
- [ ] policies/standards.yaml accessible
- [ ] logs/ directory writable
- [ ] VERSION file reads correctly (6.9.5)

---

# NEXT STEPS

After successful installation:

1. **Configure Inventory**: Add your network devices to `inventory.txt`
2. **Test Connectivity**: Verify SSH access to devices
3. **Run QA Suite**: Execute smoke tests from `docs/09-qa/QA_TESTING_CHECKLIST.txt`
4. **Build Production EXE**: Follow [build-process.md](build-process.md) if needed
5. **Configure Policies**: Customize `policies/standards.yaml` for your environment

---

# ESTIMATED TIME

| Step | Time |
|------|------|
| Python Installation | 5-10 minutes |
| Dependency Installation | 3-5 minutes |
| Application Launch | 1 minute |
| Verification | 5 minutes |
| Configuration | 10 minutes |
| **Total** | **~25-30 minutes** |

---

# SUCCESS CRITERIA

Installation is successful when:

1. Application launches without errors
2. Web UI is accessible at http://127.0.0.1:5051
3. All critical imports succeed
4. CLI Terminal and Standards Validator tabs load
5. Inventory and policy files are accessible
6. Logs directory is writable
7. No console errors on startup

---

**Document Status:** ACTIVE
**Classification:** TIER-0 REBUILD PROCEDURE
**Enforcement:** MANDATORY
**Drift Tolerance:** ZERO
