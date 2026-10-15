# Network Swiss Tool Pro v5.5.0 Release Notes

**Release Date:** 2026-04-19  
**Build Target:** Offline / Air-gapped Environments  
**Priority:** CRITICAL FIX for CLI Terminal

---

## Summary

Version 5.5.0 is a **critical bugfix release** that resolves the CLI Terminal connectivity issue where the terminal would be stuck in "Connecting..." state. This release also provides a fully self-contained offline EXE with ALL dependencies bundled for air-gapped environments.

---

## Critical Fixes

### CLI Terminal Connectivity Fix

**Problem:** The CLI Terminal feature was non-functional due to a missing `initSocket()` call, causing the WebSocket connection to never be established. The UI would show "Server: OFFLINE" and remain stuck in "Connecting..." state indefinitely.

**Root Cause:** In `modules/web/templates/cli_terminal.html`, the `initSocket()` function was defined but never called in the DOMContentLoaded event handler.

**Fix:** Added `initSocket()` call to initialize the WebSocket connection immediately on page load.

**Code Change:**
```javascript
// Before (Broken):
document.addEventListener('DOMContentLoaded', () => {
    initTerminal();
    // Socket never initialized - stuck in OFFLINE state
});

// After (Fixed):
document.addEventListener('DOMContentLoaded', () => {
    initTerminal();
    initSocket();  // v5.5.0: Initialize WebSocket connection
});
```

### ImportError Fix

**Problem:** ImportError for missing `list_cli_sessions()` function in `cli_manager.py`.

**Fix:** Added the missing `list_cli_sessions()` function to `modules/cli_manager.py`.

---

## Files Modified

| File | Change |
|------|--------|
| `modules/web/templates/cli_terminal.html` | Added `initSocket()` call in DOMContentLoaded |
| `modules/cli_manager.py` | Added `list_cli_sessions()` function |
| `vlan_checker_web.py` | Version bump to 5.5.0 |
| `VERSION` | Updated to 5.5.0 |
| `CHANGELOG.md` | Added v5.5.0 release notes |
| `modules/web/templates/cli_terminal.html` | Updated version strings in title/terminal output |

---

## Offline Build Features

The v5.5.0 offline build includes **ALL** dependencies bundled into a single EXE file:

### Web Framework Stack
- Flask 3.x
- Flask-SocketIO 5.x
- Python-SocketIO 5.x
- Python-EngineIO 4.x
- Simple-Websocket 0.10+
- Jinja2, Werkzeug, Click

### Network Device Connectivity
- Netmiko 4.1.2
- Paramiko (full SSH implementation)
- Cryptography (all ciphers and algorithms)
- BCrypt, PyNaCl
- TextFSM, NTC Templates

### Security & Crypto
- Full cryptography library with all backends
- All Paramiko key types (RSA, ECDSA, Ed25519)
- All KEX algorithms
- CFFI and PyCParser

### Other Embedded Libraries
- PyYAML
- PySerial
- Tenacity (retry logic)
- Invoke (Netmiko dependency)
- pyasn1 and pyasn1-modules
- RSA

### Excluded (Not Needed)
- GUI libraries (tkinter, PyQt, wxPython)
- Scientific computing (numpy, pandas, scipy)
- ML/AI libraries (tensorflow, torch)
- Development tools (jupyter, sphinx, etc.)

---

## Build Specifications

- **Spec File:** `NetworkSwissToolPro_v5_4_9_Offline.spec`
- **Build Script:** `build_v5.5.0_offline.bat`
- **Output:** `NetworkSwissToolPro_v5_4_9_Offline.exe`
- **Distribution:** `NetworkSwissToolPro_v5_4_9_Offline.zip`

### Build Requirements
- Python 3.10 or higher
- Windows 10/11 or Windows Server 2016+
- 4GB RAM minimum (8GB recommended for build)
- ~500MB disk space for build process

### Target Runtime Requirements
- Windows 7 or higher (Windows 10+ recommended)
- NO Python installation required
- NO internet connection required
- 2GB RAM minimum

---

## Verification Steps

After building or extracting the distribution:

1. **Verify EXE size:** Should be ~80-120MB (indicates all dependencies bundled)
2. **Test CLI Terminal:**
   - Launch the application
   - Click "Connect via CLI" on any device
   - Verify "Server: OK" appears in the status
   - Enter SSH credentials and connect to a device
   - Verify interactive terminal works
3. **Test Offline Capability:**
   - Disconnect from internet
   - Launch application
   - Verify all features work without network errors

---

## Known Limitations

1. **Browser Cache:** Users upgrading from v5.5.0 may need to clear browser cache (Ctrl+Shift+R) to load the fixed JavaScript.
2. **Port 5051:** The application requires port 5051 to be available on localhost.
3. **Windows Only:** This build is for Windows environments only.

---

## Rollback Instructions

If issues occur with v5.5.0, the previous v5.5.0 ZIP file can be extracted and used. The v5.5.0 distribution is preserved in the backup folder.

---

## Support

For issues or questions regarding this release:
1. Check the `docs/` folder in the distribution package
2. Review `CHANGELOG.md` for recent changes
3. Check `logs/` folder for runtime logs

---

**Built with PyInstaller for offline deployment.**  
**Made by AI IDE**
