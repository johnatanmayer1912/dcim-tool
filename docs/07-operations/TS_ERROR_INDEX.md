# Error Index & Troubleshooting Guide

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Quick lookup for all error messages, symptoms, and documented solutions. |
| **Scope** | Connectivity, authentication, platform-specific, and UI/UX error codes. |
| **Related Documents** | [Operational Workflows](operational-workflows.md), [QA Test Suite](../09-qa/ST_MASTER_QA_SUITE.md) |
| **Update Responsibility** | Support Team / Lead Developer |
| **Version Awareness** | v7.0.29 |

---

---

## 🔍 How to Use This Index

1. **Search by error message** - Use Ctrl+F to search
2. **Search by error code** - If your error has a code
3. **Search by symptom** - What you're experiencing
4. **Follow the link** to detailed troubleshooting

---

## 📂 Error Categories

- [Connection Errors](#connection-errors) - SSH, Telnet, network issues
- [Authentication Errors](#authentication-errors) - Login, credentials
- [Device Platform Errors](#device-platform-errors) - Vendor-specific
- [Module/Feature Errors](#modulefeature-errors) - VLAN, MAC, Topology
- [Web Interface Errors](#web-interface-errors) - UI, templates, Flask
- [CLI Terminal Errors](#cli-terminal-errors) - v5.0 WebSocket/SSH
- [Build/Deployment Errors](#builddeployment-errors) - PyInstaller, EXE
- [Performance/Timeout Errors](#performancetimeout-errors)

---

## 🔌 Connection Errors

### Error: "Connection timeout"
**Symptoms:** Application hangs, then shows timeout message
**Error Codes:** CONN-001, NET-001

**Causes:**
1. Device unreachable (network issue)
2. Wrong IP address
3. Firewall blocking port 22
4. Device powered off

**Solutions:**
1. Ping device: `ping [IP]`
2. Verify IP in inventory
3. Check firewall rules
4. Verify device powered on

**Detailed Guide:** [Connection Troubleshooting](CONNECTION_ISSUES.md)

---

### Error: "Connection refused"
**Symptoms:** Immediate connection failure
**Error Codes:** CONN-002, NET-002

**Causes:**
1. SSH not enabled on device
2. Wrong port (not 22)
3. Device has SSH disabled

**Solutions:**
1. Verify SSH enabled: `show ip ssh` (Cisco)
2. Check SSH port configuration
3. Enable SSH on device if needed

---

### Error: "No route to host"
**Symptoms:** Cannot reach device at all
**Error Codes:** CONN-003, NET-003

**Causes:**
1. Network routing issue
2. Wrong subnet
3. VLAN mismatch

**Solutions:**
1. Verify network connectivity from your machine
2. Check routing tables
3. Verify same VLAN or routed access

---

## 🔐 Authentication Errors

### Error: "Authentication failed"
**Symptoms:** Connection established but login fails
**Error Codes:** AUTH-001

**Causes:**
1. Wrong username
2. Wrong password
3. Account locked
4. AAA server unreachable

**Solutions:**
1. Verify username (case sensitive)
2. Re-enter password carefully
3. Check if account locked on device
4. Verify AAA/RADIUS server

**Detailed Guide:** [Authentication Issues](AUTH_ISSUES.md)

---

### Error: "Enable password required"
**Symptoms:** Login succeeds but privileged mode fails
**Error Codes:** AUTH-002

**Causes:**
1. Enable password not provided
2. Wrong enable password
3. Device requires enable secret

**Solutions:**
1. Enter enable password in dialog
2. Verify enable password with device admin
3. Check for enable secret vs enable password

---

## 🖥️ Device Platform Errors

### Error: "dict object has no attribute 'upper'"
**Symptoms:** Topology mapper fails
**Error Codes:** TOPO-001
**Fixed In:** v4.5.8

**Cause:** Passing dict instead of string to string method

**Solution:** Update to v4.5.8+ or check topology data format

**See Also:** [Topology Troubleshooting](TOPOLOGY_ISSUES.md)

---

### Error: "generate_topology_html() got an unexpected keyword argument 'extra_header'"
**Symptoms:** Topology generation fails
**Error Codes:** TOPO-002
**Fixed In:** v5.0.0

**Cause:** Function signature mismatch

**Solution:** Update to v5.0.0 or check function call

---

### Error: "JUNOS ELS detection failed"
**Symptoms:** VLAN operations fail on Juniper devices
**Error Codes:** JUNOS-001
**Fixed In:** v5.0.0

**Cause:** Syntax error in vlan_mgmt.py line 22 (unclosed parenthesis)

**Solution:** Update to v5.0.0 which includes syntax fix

**See Also:** [JUNOS Compatibility Guide](../01-architecture/JUNOS_COMPATIBILITY.md)

---

### Error: "show ethernet-switching table not found"
**Symptoms:** MAC trace fails on SRX firewall
**Error Codes:** MAC-001
**Fixed In:** v5.0.0

**Cause:** SRX uses different command (`show arp`)

**Solution:** v5.0.0 includes SRX fallback to `show arp`

---

## 📦 Module/Feature Errors

### Error: "Topology mapper failed"
**Symptoms:** Topology generation crashes
**Error Codes:** TOPO-003

**Causes:**
1. No LLDP/CDP neighbors found
2. Invalid device data
3. Permission issues

**Solutions:**
1. Verify LLDP/CDP enabled on devices
2. Check device connectivity
3. Verify SNMP/read permissions

---

### Error: "'str' object has no attribute 'get'"
**Symptoms:** Topology mapper fails during vPC summary generation.
**Error Codes:** TOPO-004
**Fixed In:** v6.9.1

**Cause:** vPC summary generation loop iterates over all `vpc_details` entries, including internal metadata strings (e.g., `_vpc_brief`), and calls `.get()` on them.

**Solution:** Update to v6.9.1 or ensure dictionary type-checking before calling `.get()` in the vPC summary loop.

---

### Error: "VLAN audit returned no data"
**Symptoms:** VLAN audit runs but empty results
**Error Codes:** VLAN-001

**Causes:**
1. No VLANs configured
2. Command parsing failed
3. Wrong device type selected

**Solutions:**
1. Verify VLANs exist on device
2. Check device type matches platform
3. Review command output format

---

## 🌐 Web Interface Errors

### Error: "Template not found"
**Symptoms:** 404 error on web page
**Error Codes:** WEB-001

**Causes:**
1. Missing HTML template file
2. Wrong template path
3. Build didn't include templates

**Solutions:**
1. Check `modules/web/templates/` exists
2. Verify template filenames match
3. Rebuild with PyInstaller including templates

**Detailed Guide:** [Web Interface Issues](WEB_INTERFACE_ISSUES.md)

---

### Error: "Flask server not starting"
**Symptoms:** Application fails to launch
**Error Codes:** WEB-002

**Causes:**
1. Port 5000 in use
2. Permission denied
3. Flask not installed

**Solutions:**
1. Kill process on port 5000: `lsof -ti:5000 | xargs kill -9`
2. Run as administrator (if permission issue)
3. Reinstall requirements: `pip install -r requirements.txt`

---

### Error: "vis-network.min.js not found"
**Symptoms:** Topology map doesn't display
**Error Codes:** WEB-003

**Cause:** JavaScript library not bundled

**Solution:** Ensure `vis-network.min.js` included in PyInstaller spec

---

## 💻 CLI Terminal Errors (v5.0)

### Error: "WebSocket connection failed"
**Symptoms:** CLI terminal loads but can't connect
**Error Codes:** CLI-001

**Causes:**
1. flask-socketio not installed
2. Firewall blocking WebSocket
3. Browser doesn't support WebSocket

**Solutions:**
1. Install: `pip install flask-socketio`
2. Open firewall for port 5000
3. Use modern browser (Chrome/Firefox/Edge)

**Detailed Guide:** [CLI Terminal Issues](CLI_TERMINAL_ISSUES.md)

---

### Error: "SSH session timeout"
**Symptoms:** CLI terminal disconnects after 10 min
**Error Codes:** CLI-002
**Status:** By Design (v5.0)

**Cause:** 10-minute idle timeout (security feature)

**Solution:** Click "Reconnect" button to re-establish session

---

### Error: "Cannot create multiple sessions"
**Symptoms:** Second CLI tab doesn't work
**Error Codes:** CLI-003

**Cause:** Session ID collision or resource limit

**Solution:** Each tab should have unique session - check browser console for errors

---

### Error: "CLI commands visible in logs"
**Symptoms:** Terminal commands appearing in application logs
**Error Codes:** CLI-004
**Status:** Security Issue
**Fixed In:** v5.0.0

**Cause:** Old version without privacy fix

**Solution:** Update to v5.0.0 - commands should NOT be logged

---

## 🔨 Build/Deployment Errors

### Error: "PyInstaller failed"
**Symptoms:** Build process errors
**Error Codes:** BUILD-001

**Causes:**
1. Missing hidden imports
2. Syntax errors in code
3. Missing dependencies

**Solutions:**
1. Check `warn-*.txt` in build folder
2. Run `python -m py_compile` on all files
3. Verify requirements.txt complete

**Detailed Guide:** [Build Issues](recovery/BUILD_PROCEDURES.md)

---

### Error: "EXE file too small"
**Symptoms:** Generated EXE < 10MB
**Error Codes:** BUILD-002

**Cause:** PyInstaller didn't bundle dependencies

**Solution:** Check spec file has all hidden imports and datas

---

### Error: "Missing modules in EXE"
**Symptoms:** "No module named X" when running EXE
**Error Codes:** BUILD-003

**Solution:** Add missing module to spec file hiddenimports list

---

## ⏱️ Performance/Timeout Errors

### Error: "Request timeout"
**Symptoms:** Operation takes too long, times out
**Error Codes:** PERF-001

**Causes:**
1. Slow network connection
2. Device overloaded
3. Too many devices in inventory

**Solutions:**
1. Reduce inventory size for testing
2. Check device CPU/memory usage
3. Increase timeout values (if applicable)

---

### Error: "Out of memory"
**Symptoms:** Application crashes, system slow
**Error Codes:** PERF-002

**Causes:**
1. Large topology data
2. Memory leak
3. Too many concurrent operations

**Solutions:**
1. Process devices in smaller batches
2. Restart application
3. Check for memory leaks in code

---

## 🔍 Quick Diagnostic Commands

### Test Python Environment
```bash
python --version
python -c "import netmiko; print('Netmiko OK')"
python -c "import flask; print('Flask OK')"
python -c "from modules import vlan_audit; print('Modules OK')"
```

### Test Device Connectivity
```bash
ping [DEVICE_IP]
telnet [DEVICE_IP] 22  # Test SSH port
ssh [USER]@[DEVICE_IP]  # Test SSH manually
```

### Test Application
```bash
python -m py_compile modules/*.py
python vlan_checker_web.py
# Check http://localhost:5000
```

### Check Logs
```bash
# Application logs
cat logs/vlan_checker_*.log

# Build logs
cat build/warn-*.txt

# System logs
eventvwr  # Windows
journalctl  # Linux
```

---

## 📊 Error Frequency Report

Based on support tickets (last 90 days):

| Error | Frequency | Severity | Avg Resolution Time |
|-------|-----------|----------|-------------------|
| "Authentication failed" | High | Medium | 15 min |
| "Connection timeout" | High | Medium | 10 min |
| "WebSocket connection failed" | Medium | High | 30 min |
| "Template not found" | Low | High | 45 min |
| "PyInstaller failed" | Low | Medium | 60 min |

---

## 🆘 Escalation Path

### Level 1: Self-Service (0-30 min)
1. Search this index
2. Follow troubleshooting guide
3. Check documentation

### Level 2: Team Support (30-60 min)
1. Ask in #support Slack
2. Share error message and context
3. Try suggested solutions

### Level 3: Expert Escalation (60+ min)
1. Create detailed bug report
2. Tag Tech Lead
3. Schedule troubleshooting session

### Emergency (Production Down)
1. Follow `../05_RECOVERY/MASTER_RECOVERY.md`
2. Contact Tech Lead immediately
3. Engage entire team

---

## 📝 Contributing New Errors

### When you discover a new error:

1. **Document it immediately**
   ```markdown
   ### Error: "[exact message]"
   **Symptoms:** [what user sees]
   **Error Code:** [assign next available]
   **Added:** YYYY-MM-DD
   
   **Cause:** [root cause]
   **Solution:** [how to fix]
   ```

2. **Add to this index**
   - Add to appropriate category
   - Include search keywords
   - Link to detailed troubleshooting

3. **Update related docs**
   - Feature documentation
   - QA tests (if reproducible)
   - Troubleshooting guide

4. **Submit PR**
   - Tag: `docs: Add error [code] to index`
   - Include example scenario
   - Get peer review

---

## 🔗 Related Documentation

- **Connection Issues:** [CONNECTION_ISSUES.md](CONNECTION_ISSUES.md)
- **Authentication Issues:** [AUTH_ISSUES.md](AUTH_ISSUES.md)
- **Device-Specific:** [device_specific/](device_specific/)
- **Recovery:** [recovery/](recovery/)
- **QA Testing:** [../03_QA_TESTING/](qa_testing/)

---

**Document Owner:** Support Team  
**Last Error Added:** 2026-04-19  
**Total Errors Documented:** 25+  
**Update Frequency:** As new errors discovered

---

*Can't find your error? Add it! Follow the contribution guide above.*
