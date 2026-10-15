# Troubleshooting Guide

> **Common issues, solutions, and recovery procedures**

---

## 🚨 Emergency Contacts & Resources

**Before you start troubleshooting:**
1. Check `logs/` folder for session logs
2. Check `backups/` folder for pre-change backups
3. Review last operation in browser console (F12)

---

## Common Issues

### 1. "ModuleNotFoundError" on Startup

**Symptoms:**
```
Traceback (most recent call last):
  File "vlan_checker_web.py", line 5, in <module>
    import netmiko
ModuleNotFoundError: No module named 'netmiko'
```

**Solutions:**
```bash
# Install missing dependencies
pip install netmiko flask

# Or install all requirements
pip install -r requirements.txt
```

**Prevention:**
- Run `pip install -r requirements.txt` after fresh clone
- Use virtual environment

---

### 2. "Connection Refused" or "Connection Timeout"

**Symptoms:**
```
[10.1.1.1] ERROR: Connection to device timed-out
[10.1.1.1] ERROR: TCP connection to device refused
```

**Solutions:**

**Check 1: Device Reachability**
```bash
ping 10.1.1.1
```
- If ping fails: Network issue, not application issue

**Check 2: SSH Port**
```bash
telnet 10.1.1.1 22
# or
Test-NetConnection -ComputerName 10.1.1.1 -Port 22
```
- If port closed: SSH not enabled on device

**Check 3: Credentials**
- Verify username/password in web UI
- Try manual SSH: `ssh user@10.1.1.1`
- Check if enable password required

**Check 4: Device Type**
- Wrong device_type = connection failures
- Verify: `cisco_ios` vs `cisco_nxos` vs `juniper_junos`

---

### 3. "Authentication Failed"

**Symptoms:**
```
[10.1.1.1] ERROR: Authentication failure: unable to connect
```

**Solutions:**

**Step 1: Manual SSH Test**
```bash
ssh admin@10.1.1.1
# Enter password when prompted
```
- If fails: Credentials wrong
- If works: Device type might be wrong

**Step 2: Enable Password**
- Some devices require enable password for privileged commands
- Check "Enable Password" field in web UI

**Step 3: Account Lockout**
- Too many failed attempts may lock account
- Wait 15 minutes or unlock from device console

---

### 4. Tasks Get "Stuck" (No Output)

**Symptoms:**
- Operation started but no log output
- Browser shows "Running..." indefinitely
- No new log entries in `/api/logs`

**Solutions:**

**Check 1: Thread Status**
```python
# In Python console (if running from source)
import threading
print(threading.active_count())
print(threading.enumerate())
```

**Check 2: Module Import Errors**
```bash
# Test module imports
python -c "from modules import vlan_audit; print('OK')"
python -c "from modules import adapters; print('OK')"
```

**Check 3: Restart Application**
```bash
# Kill and restart
Ctrl+C  # or close console
python vlan_checker_web.py
```

**Prevention (v4.5.7+):**
- All thread functions now have try-except wrappers
- Check session log file for traceback

---

### 5. "Template Not Found" Error

**Symptoms:**
```
jinja2.exceptions.TemplateNotFound: index.html
```

**Solutions:**

**Check 1: Template Location**
- Dev mode: `modules/web/templates/index.html`
- Bundled: Templates embedded in executable

**Check 2: PyInstaller Bundle**
```bash
# Rebuild executable
pyinstaller --clean --noconfirm NetworkSwissToolPro_v4_5_3_Web.spec
```

**Check 3: Template Path Resolution**
```python
# Debug code
import os, sys
print(f"Frozen: {getattr(sys, 'frozen', False)}")
print(f"MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
print(f"CWD: {os.getcwd()}")
```

---

### 6. VLAN Operation Failed Mid-Way

**Symptoms:**
```
[10.1.1.1] SUCCESS: VLAN 100 added
[10.1.1.2] ERROR: Connection timeout
[10.1.1.3] Waiting...
```

**What Happened:**
- One device failed (network issue)
- Other devices waiting in queue

**Solutions:**

**Check 1: Verify Partial Changes**
- Check devices that reported SUCCESS
- Verify VLAN actually added: `show vlan`

**Check 2: Rerun for Failed Devices**
- Filter to just the failed device(s)
- Rerun operation

**Check 3: Rollback (if needed)**
- Find pre-change backup in `backups/{hostname}/`
- Manually restore or use restore function

**Design Note:**
- Application isolates failures per-device by design
- One failure doesn't stop others
- This is intentional for partial success scenarios

---

### 7. MAC Address Not Found

**Symptoms:**
```
[RESULT] MAC 00:11:22:33:44:55 not found in any device.
```

**Solutions:**

**Check 1: MAC Format**
- Supported: `00:11:22:33:44:55`, `0011.2233.4455`, `00-11-22-33-44-55`
- Application normalizes automatically

**Check 2: MAC Table Aging**
```bash
# On switch, check MAC table
show mac address-table
# or
show mac address-table aging-time
```
- If MAC not in table: Device hasn't sent traffic recently

**Check 3: Different VLAN**
- MAC might be in different VLAN
- Check VLAN-specific MAC tables

**Check 4: Behind Router**
- If target is behind a router, MAC won't be in switch tables
- Check router ARP table instead

---

### 8. Topology Map Shows No Connections

**Symptoms:**
- HTML file generated but empty or isolated nodes
- No links between devices

**Solutions:**

**Check 1: CDP/LLDP Enabled**
```bash
# Cisco - Check if CDP enabled
show cdp
# Enable if needed:
cdp run
cdp enable

# Juniper - Check if LLDP enabled
show lldp
# Enable if needed:
set protocols lldp interface all
```

**Check 2: Discovery Protocol Mismatch**
- Cisco uses CDP
- Juniper uses LLDP
- Mixed networks may need both enabled

**Check 3: Timers**
- CDP/LLDP advertisements take time
- Default: 60 seconds between updates
- Wait 2-3 minutes after enabling

---

### 9. Build/Packaging Failures

**Symptoms:**
```
PyInstaller: Failed to execute script
# or
ImportError: No module named 'X' in bundled app
```

**Solutions:**

**Step 1: Clean Build**
```bash
# Remove build artifacts
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build, __pycache__
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue modules\__pycache__, utils\__pycache__

# Rebuild
pyinstaller --clean --noconfirm NetworkSwissToolPro_v4_5_3_Web.spec
```

**Step 2: Check Spec File**
- Verify `NetworkSwissToolPro_v4_5_3_Web.spec` exists
- Check `pathex`, `binaries`, `datas` entries

**Step 3: Hidden Imports**
```python
# In .spec file, add if needed:
hiddenimports=['telnetlib_compat', 'netmiko', 'jinja2']
```

---

### 10. Python 3.13+ Compatibility Issues

**Symptoms:**
```
ModuleNotFoundError: No module named 'telnetlib'
```

**Solutions:**

**For Bundled Executable:**
- v4.5.7+ includes `telnetlib_compat.py` and runtime hook
- Should work automatically

**For Development:**
```bash
# Ensure telnetlib_compat.py is in project root
# Import order matters in vlan_checker_web.py:

try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401
```

---

## Recovery Procedures

### Recover from Failed VLAN Change

**Scenario:** VLAN operation partially failed, network in unknown state

**Recovery Steps:**

1. **Identify Changed Devices**
   ```bash
   # Check session log
   grep "SUCCESS" app_session_log_*.txt
   ```

2. **Find Pre-Change Backups**
   ```
   backups/
   └── {hostname}/
       └── config_YYYYMMDD_HHMMSS.txt
   ```

3. **Manual Rollback (per device)**
   ```bash
   # SSH to device
   ssh admin@device
   
   # For Cisco - restore from backup file
   copy tftp://server/backup_file running-config
   # or manually revert changes
   
   # For Juniper
   load replace /var/tmp/backup_file.conf
   commit
   ```

4. **Verify Rollback**
   ```bash
   show vlan
   # Verify VLAN state matches pre-change
   ```

---

### Recover from Complete Application Failure

**Scenario:** Application won't start at all

**Recovery Steps:**

1. **Fresh Clone/Rebuild**
   ```bash
   # Backup your inventory.txt!
   cp inventory.txt ../inventory-backup.txt
   
   # Rebuild from prompts
   # Follow docs/prompts/00-PROMPT-INDEX.md
   ```

2. **Use Standalone Executable**
   - Download from `dist_package_web/`
   - No Python dependencies needed
   - Just run `.exe` file

3. **Use CLI Mode for Emergency**
   ```bash
   # Even if web UI broken, CLI might work
   python main.py cli --task connectivity --user admin
   ```

---

### Database/State Corruption

**Scenario:** Logs, backups, or state files corrupted

**Recovery:**

1. **Reset Session State**
   ```bash
   # Remove session logs (keeps backups)
   Remove-Item app_session_log_*.txt
   
   # Restart - fresh session
   python vlan_checker_web.py
   ```

2. **Reset All State**
   ```bash
   # WARNING: Loses all logs
   Remove-Item -Recurse logs/, reports/, backups/
   New-Item -ItemType Directory logs/, reports/, backups/
   ```

---

## Debugging Techniques

### Enable Debug Logging

```python
# Add to vlan_checker_web.py temporarily
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Netmiko Debug

```python
# In module code, before connection:
import logging
logging.basicConfig(filename='netmiko.log', level=logging.DEBUG)
```

### Manual Module Testing

```python
# Test individual module
from modules import vlan_audit

device = {'host': '10.1.1.1', 'device_type': 'cisco_ios', 'port': 22}
result = vlan_audit.run(device, 'admin', 'password', '', print)
print(result)
```

---

## Prevention Checklist

Before running operations:

- [ ] **Connectivity Check** - All devices reachable?
- [ ] **Dry-Run** - Preview changes first
- [ ] **Backup Status** - Recent backups available?
- [ ] **Inventory** - Correct device types?
- [ ] **Scope** - Correct target devices selected?
- [ ] **Maintenance Window** - Is this a good time?

---

## Getting More Help

### Information to Gather

When asking for help, provide:

1. **Version:** `cat VERSION`
2. **Python:** `python --version`
3. **OS:** Windows/Mac/Linux?
4. **Error message:** Full traceback
5. **Operation:** What were you trying to do?
6. **Device type:** `cisco_ios`, `juniper_junos`, etc.
7. **Session log:** `app_session_log_*.txt`

### Log Locations

| Log Type | Location |
|----------|----------|
| Session Logs | `app_session_log_YYYYMM*.txt` (root) |
| Structured Logs | `logs/*.log` |
| Backups | `backups/{hostname}/*.txt` |
| Reports | `reports/*.txt`, `reports/*.csv`, `reports/*.html` |

---

## Emergency Contacts

**Internal:**
- Network Operations Center: [your NOC contact]
- Senior Network Engineer: [your senior contact]

**Tool Issues:**
- Check `docs/` folder
- Review `CHANGELOG.md` for known issues
- Check session logs

---

## Quick Command Reference

```bash
# Test connectivity to all devices
python main.py cli --task connectivity --user admin

# Emergency config backup
python main.py cli --task backup

# Check backup status
python main.py cli --task backup-check

# Verify installation
python -c "import modules.vlan_audit; import modules.mac_trace; print('OK')"
```
