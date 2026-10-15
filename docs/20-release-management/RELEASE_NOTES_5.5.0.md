# Network Swiss Tool Pro v5.5.0 Release Notes

**Release Date:** 2026-04-19  
**Build Target:** Offline / Air-gapped Environments  
**Priority:** CRITICAL FIX for XHR Poll / Transport Errors

---

## Summary

Version 5.5.0 is a **critical bugfix release** that resolves XHR poll errors and transport errors that prevented the CLI Terminal from connecting to the server. This release includes comprehensive diagnostics, health checks, and enhanced error handling.

---

## Critical Fixes

### XHR Poll Error Fix

**Problem:** The CLI Terminal was showing "XHR poll error" and "transport error" messages, preventing any SSH connections to network devices.

**Root Causes Addressed:**
1. Server startup timing issues - client tried to connect before server was fully ready
2. Missing threading driver components in PyInstaller bundle
3. Insufficient error handling and diagnostics
4. Port 5051 availability not properly verified

**Solutions Implemented:**

1. **Server-Side Startup Logging (vlan_checker_web.py)**
   - Added `startup_log()` function that logs to both console and `logs/startup.log`
   - Logs every step of initialization: Socket.IO setup, port check, server start
   - Logs the health check URL and debug status URL

2. **Client-Side Health Check (cli_terminal.html)**
   - Added `checkServerHealth()` async function that pings `/health` endpoint
   - Health check runs BEFORE attempting Socket.IO connection
   - Visual feedback in debug log and terminal if server not ready

3. **Enhanced Socket.IO Configuration**
   - Timeout increased from 20s to 30s for EXE cold start scenarios
   - Reconnection attempts increased from 10 to 15
   - Exponential backoff: 1s initial, 5s max delay
   - WebSocket tried first, falls back to polling

4. **Improved Error Messages**
   - XHR poll errors now show helpful troubleshooting steps:
     - Server not started yet (EXE still loading)
     - Port 5051 blocked by firewall
     - Antivirus blocking localhost connection
     - Page loaded before server was ready

5. **PyInstaller Spec Hardening**
   - Added `collect_all('engineio.async_drivers.threading')` - CRITICAL
   - Excluded eventlet/gevent to FORCE threading mode
   - All jaraco submodules explicitly collected

---

## Files Modified

| File | Change |
|------|--------|
| `vlan_checker_web.py` | Added startup_log(), enhanced run_web() with error handling, bumped version to 5.5.0 |
| `modules/web/templates/cli_terminal.html` | Added async health check, enhanced initSocket(), improved error messages, bumped version |
| `main.py` | Bumped version to 5.5.0 |
| `VERSION` | Updated to 5.5.0 |
| `CHANGELOG.md` | Added v5.5.0 release notes |
| `NetworkSwissToolPro_v5_5_0_Offline.spec` | New spec with threading driver and all dependencies |

---

## How to Verify the Fix

1. **Launch the EXE** - Look for startup messages in console
2. **Check logs/startup.log** - Verify server started successfully
3. **Open CLI Terminal** - Should show "Server: OK (WEBSOCKET)" or "Server: OK (POLLING)"
4. **Check Debug Panel** - Click [Debug] to see connection log
5. **Connect to Device** - SSH connection should succeed without XHR errors

---

## Offline Build Features

The v5.5.0 offline build includes **ALL** dependencies bundled into a single EXE file:

### Socket.IO Stack (CRITICAL for CLI Terminal)
- Flask-SocketIO 5.x with threading driver
- Python-SocketIO 5.x
- Python-EngineIO 4.x with threading async driver
- Simple-Websocket 0.10+
- All jaraco dependencies (text, functools, context)
- All pkg_resources vendor packages

### Network Device Connectivity
- Netmiko 4.1.2
- Paramiko (full SSH implementation)
- Cryptography (all ciphers and algorithms)
- BCrypt, PyNaCl

### Excluded (Not Needed)
- eventlet, gevent, greenlet (intentionally excluded to force threading mode)
- GUI libraries (tkinter, PyQt, wxPython)
- Scientific computing (numpy, pandas, scipy)

---

## Build Specifications

- **Spec File:** `NetworkSwissToolPro_v5_5_0_Offline.spec`
- **Output:** `NetworkSwissToolPro_v5_5_0_Offline.exe`
- **Distribution:** `NetworkSwissToolPro_v5_5_0_Offline.zip`

---

## Troubleshooting

If you still see XHR poll errors:

1. **Check logs/startup.log** - Look for error messages
2. **Verify port 5051** - Make sure no other app is using it
3. **Check firewall** - Allow localhost:5051 connections
4. **Antivirus** - Add EXE to exclusions if needed
5. **Wait longer** - EXE cold start can take 5-10 seconds

---

**Built with PyInstaller for offline deployment.**  
**Made by AI IDE**
