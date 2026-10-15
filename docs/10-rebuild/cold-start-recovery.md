# Cold Start Recovery

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Emergency procedures for recovering NetworkSwissToolPro from complete system failure, corrupted installation, or catastrophic data loss. |
| **Scope** | Disaster recovery from zero-state, corrupted files, missing dependencies, and complete environment reconstruction. |
| **Responsibilities** | Critical incident response and system restoration from failure states. |
| **Dependencies** | Backup artifacts, source code repository, recovery kit, or offline installation media. |
| **Related Documents** | [offline-recovery.md](offline-recovery.md), [from-zero-installation.md](from-zero-installation.md), [exact-rebuild-procedure.md](exact-rebuild-procedure.md) |
| **Operational Impact** | Enables recovery from catastrophic failures, corrupted installations, and data loss scenarios. |
| **Failure Conditions** | No backup available, source repository inaccessible, recovery kit missing, hardware failure. |
| **Recovery Notes** | Use recovery kit if available. Rebuild from source if repository accessible. Contact maintainers if all recovery options fail. |
| **Version Awareness** | v6.9.5 |
| **Last Synchronization Timestamp** | 2026-05-25 |
| **Maintainer** | LIBRARIAN / DevOps Lead |

---

# COLD START SCENARIOS

## Scenario A: Application Corruption (Partial Recovery)

**Symptoms:**
- Application won't launch
- Import errors on startup
- Missing modules or files
- Corrupted configuration

**Recovery Time:** 10-15 minutes

**Severity:** Medium

---

## Scenario B: Complete Installation Loss (Full Recovery)

**Symptoms:**
- Application directory deleted
- Python environment corrupted
- All dependencies missing
- No executable available

**Recovery Time:** 30-45 minutes

**Severity:** High

---

## Scenario C: System Failure + Data Loss (Catastrophic Recovery)

**Symptoms:**
- Operating system reinstalled
- All data lost
- No backup available
- Hardware replacement

**Recovery Time:** 1-2 hours

**Severity:** Critical

---

# SCENARIO A: APPLICATION CORRUPTION

## Step 1: Diagnose Corruption

```powershell
# Check application directory
cd "C:\Net_mngmnt_tool - V6 - cursor"
dir

# Check for missing files
Test-Path "vlan_checker_web.py"
Test-Path "modules"
Test-Path "utils"
Test-Path "inventory.txt"

# Check Python environment
python --version
pip list
```

## Step 2: Identify Corrupted Components

```powershell
# Test imports
python -c "import netmiko" 2>&1
python -c "import flask" 2>&1
python -c "from modules import network_base" 2>&1

# Check for import errors
# Note which modules fail to import
```

## Step 3: Restore from Backup

```powershell
# If backup available
copy E:\backup\Net_mngmnt_tool\vlan_checker_web.py .
xcopy /E /I E:\backup\Net_mngmnt_tool\modules modules\
xcopy /E /I E:\backup\Net_mngmnt_tool\utils utils\
copy E:\backup\Net_mngmnt_tool\inventory.txt .
```

## Step 4: Reinstall Dependencies

```powershell
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
pip list
```

## Step 5: Verify Recovery

```powershell
# Launch application
python vlan_checker_web.py

# Test web UI
# Open browser to http://127.0.0.1:5051
```

---

# SCENARIO B: COMPLETE INSTALLATION LOSS

## Step 1: Assess Available Recovery Options

```powershell
# Check for backup artifacts
Test-Path "E:\backup\Net_mngmnt_tool"
Test-Path "E:\NetworkSwissToolPro_Recovery_v6.9.5"

# Check for source repository access
# Can you access Git repository?
# Can you download from backup location?
```

## Option B1: Recovery from Backup Kit (Fastest)

```powershell
# Copy from recovery kit
xcopy /E /I E:\NetworkSwissToolPro_Recovery_v6.9.5 "C:\Net_mngmnt_tool - V6 - cursor"

# Launch EXE
cd "C:\Net_mngmnt_tool - V6 - cursor"
.\NetworkSwissToolPro_v6.9.5_OFFLINE.exe
```

## Option B2: Rebuild from Source (Standard)

```powershell
# Copy source code
xcopy /E /I E:\backup\source "C:\Net_mngmnt_tool - V6 - cursor"

# Install Python
# (See from-zero-installation.md)

# Install dependencies
cd "C:\Net_mngmnt_tool - V6 - cursor"
pip install -r requirements.txt

# Launch application
python vlan_checker_web.py
```

## Option B3: Download from Repository (If Available)

```powershell
# Clone repository (if internet available)
git clone <repository-url> "C:\Net_mngmnt_tool - V6 - cursor"

# Checkout correct version
cd "C:\Net_mngmnt_tool - V6 - cursor"
git checkout v6.9.5

# Install dependencies
pip install -r requirements.txt

# Launch application
python vlan_checker_web.py
```

---

# SCENARIO C: SYSTEM FAILURE + DATA LOSS

## Step 1: Hardware/OS Recovery

```powershell
# Reinstall operating system if needed
# Install drivers
# Configure network
# Set up user accounts
```

## Step 2: Install Python Environment

```powershell
# Install Python 3.12+
# (See from-zero-installation.md for detailed steps)

python --version
# Expected: Python 3.12+
```

## Step 3: Obtain Recovery Artifacts

**Priority Order:**
1. Recovery kit USB (fastest)
2. Cloud backup download
3. Network file share copy
4. Source repository clone
5. Contact maintainers for artifacts

## Step 4: Restore Application

```powershell
# Using recovery kit
xcopy /E /I E:\NetworkSwissToolPro_Recovery_v6.9.5 "C:\Net_mngmnt_tool - V6 - cursor"

# Or from source
git clone <repository-url> "C:\Net_mngmnt_tool - V6 - cursor"
git checkout v6.9.5
```

## Step 5: Install Dependencies

```powershell
cd "C:\Net_mngmnt_tool - V6 - cursor"

# If wheel cache available
pip install --no-index --find-links=paramiko_deps -r requirements.txt

# If internet available
pip install -r requirements.txt
```

## Step 6: Restore Configuration

```powershell
# Restore inventory
copy E:\backup\inventory.txt inventory.txt

# Restore policies
xcopy /E /I E:\backup\policies policies\

# Restore custom configurations
copy E:\backup\config.yaml config.yaml
```

## Step 7: Verify Complete Recovery

```powershell
# Launch application
python vlan_checker_web.py

# Comprehensive testing
# - Web UI loads
# - CLI Terminal works
# - Standards Validator loads
# - Device connections work
# - Reports generate
```

---

# EMERGENCY RECOVERY PROCEDURES

## Emergency Procedure 1: Quick EXE Launch

**Use when:** Immediate access needed, no time for full recovery

```powershell
# Copy EXE to any location
copy E:\NetworkSwissToolPro_v6.9.5_OFFLINE.exe C:\Temp\

# Launch from temp location
cd C:\Temp
.\NetworkSwissToolPro_v6.9.5_OFFLINE.exe

# Note: Will use default configuration
```

## Emergency Procedure 2: Portable Mode

**Use when:** No installation privileges available

```powershell
# Copy to USB drive
copy E:\NetworkSwissToolPro_v6.9.5_OFFLINE.exe F:\Portable\

# Launch from USB
cd F:\Portable
.\NetworkSwissToolPro_v6.9.5_OFFLINE.exe

# Note: Runs entirely from USB, no system installation
```

## Emergency Procedure 3: Minimal Source Recovery

**Use when:** Only critical files needed

```powershell
# Copy only essential files
copy vlan_checker_web.py C:\Temp\
xcopy /E /I modules C:\Temp\modules\
xcopy /E /I utils C:\Temp\utils\
copy inventory.txt C:\Temp\

# Install dependencies
pip install netmiko flask flask-socketio

# Launch
cd C:\Temp
python vlan_checker_web.py
```

---

# DATA RECOVERY

## Inventory Recovery

```powershell
# If inventory.txt lost
# Check backups:
# - E:\backup\inventory.txt
# - logs/ (may contain device IPs)
# - Previous reports

# Rebuild from logs
# Search logs for device IPs
Select-String -Path logs\*.log -Pattern "192\.168\." | Select-Object -First 20
```

## Policy Recovery

```powershell
# If policies lost
# Copy from backup
xcopy /E /I E:\backup\policies policies\

# Or use default policies
# Check repository for original standards.yaml
```

## Configuration Recovery

```powershell
# If configuration lost
# Check for config.yaml in backup
copy E:\backup\config.yaml config.yaml

# Or use defaults
# Application will use built-in defaults
```

## Log Recovery

```powershell
# If logs lost
# Logs are non-critical for operation
# New logs will be created on next launch

# Historical logs can be recovered from backup if needed
xcopy /E /I E:\backup\logs logs\
```

---

# VALIDATION CHECKLIST

## Post-Recovery Validation

### Application Validation
- [ ] Application launches without errors
- [ ] Web UI accessible at http://127.0.0.1:5051
- [ ] No import errors in console
- [ ] All tabs load correctly
- [ ] No console errors (F12)

### Dependency Validation
- [ ] Python version correct (3.12+)
- [ ] All required packages installed
- [ ] pip list shows expected versions
- [ ] Import tests pass for all modules

### Configuration Validation
- [ ] inventory.txt exists and valid
- [ ] policies/ directory exists
- [ ] standards.yaml accessible
- [ ] logs/ directory writable
- [ ] VERSION file reads correctly

### Functional Validation
- [ ] CLI Terminal connects to devices
- [ ] Standards Validator loads policies
- [ ] VLAN operations work
- [ ] Topology mapping generates
- [ ] Reports export correctly

### Data Validation
- [ ] Historical inventory preserved
- [ ] Custom policies preserved
- [ ] Configuration settings preserved
- [ ] Backup procedures work

---

# RECOVERY TIME ESTIMATES

| Scenario | Best Case | Worst Case | Average |
|----------|-----------|------------|---------|
| Application Corruption | 10 min | 20 min | 15 min |
| Complete Installation Loss | 20 min | 60 min | 40 min |
| System Failure + Data Loss | 45 min | 120 min | 90 min |
| Emergency Quick Launch | 2 min | 5 min | 3 min |

---

# FAILURE POINT ANALYSIS

## Common Failure Points

### 1. Missing Python Installation
**Symptom:** `python: command not found`
**Solution:** Install Python 3.12+ (see from-zero-installation.md)

### 2. Corrupted Dependencies
**Symptom:** Import errors, module not found
**Solution:** Reinstall dependencies with `--force-reinstall`

### 3. Missing Configuration Files
**Symptom:** Application won't start, config errors
**Solution:** Restore from backup or use defaults

### 4. Permission Issues
**Symptom:** Access denied, cannot write files
**Solution:** Run as administrator, check directory permissions

### 5. Port Conflicts
**Symptom:** Port 5051 already in use
**Solution:** Kill conflicting process or change port

### 6. Missing Inventory
**Symptom:** No devices available for scanning
**Solution:** Restore inventory.txt or create new one

---

# PREVENTIVE MEASURES

## Regular Backup Schedule

### Daily
- [ ] Backup inventory.txt
- [ ] Backup custom policies
- [ ] Backup configuration files

### Weekly
- [ ] Backup entire source directory
- [ ] Backup logs directory
- [ ] Test recovery procedures

### Monthly
- [ ] Create recovery kit update
- [ ] Update wheel cache
- [ ] Test cold start recovery

### Per Release
- [ ] Create version-specific recovery kit
- [ ] Archive release artifacts
- [ ] Document any recovery procedure changes

## Backup Verification

```powershell
# Verify backup integrity
# Test backup can be restored
# Test restored application works
# Document any issues
```

---

# CONTACT PROCEDURES

## When Self-Recovery Fails

1. **Check documentation**
   - Review all recovery procedures
   - Check troubleshooting guides
   - Review error logs

2. **Check for known issues**
   - Review TS_ERROR_INDEX.md
   - Check release notes
   - Search issue tracker

3. **Contact maintainers**
   - Document failure symptoms
   - List recovery attempts made
   - Include error logs
   - Specify version (v6.9.5)

## Information to Provide

When requesting assistance:

- Version: v6.9.5
- Python version: `python --version`
- OS version: Windows version
- Error messages: Exact error text
- Recovery attempts: What you tried
- Logs: Relevant log files
- Backup status: What backups are available

---

# SUCCESS CRITERIA

Cold start recovery is successful when:

1. Application launches without errors
2. Web UI accessible at http://127.0.0.1:5051
3. All critical features operational
4. Configuration restored or recreated
5. Data preserved (inventory, policies, logs)
6. Dependencies correctly installed
7. No residual errors or warnings

---

# DOCUMENTATION UPDATES

After any recovery event:

1. Document what failed
2. Document recovery steps taken
3. Document any issues encountered
4. Update procedures if needed
5. Share lessons learned

---

**Document Status:** ACTIVE
**Classification:** TIER-0 DISASTER RECOVERY
**Enforcement:** MANDATORY
**Drift Tolerance:** ZERO
