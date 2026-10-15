# Network Swiss Tool Pro v5.0.0 Release Notes

**Release Date:** April 17, 2026  
**Version:** 5.0.0  
**Codename:** "Terminal Velocity"

---

## 🚀 Major New Feature: CLI Terminal Interface

### Overview
v5.0.0 introduces a revolutionary **embedded CLI terminal** that allows users to open persistent SSH sessions directly from the web interface. This feature provides real-time, interactive command-line access to network devices without leaving the application.

### Key Features

- 🔌 **"Connect via CLI" Button** - Available in Single Device mode
- 🖥️ **Web-Based Terminal** - Full xterm.js terminal emulator in browser
- 🔗 **WebSocket Communication** - Real-time bidirectional data flow
- 📱 **Multiple Sessions** - Open concurrent terminals to different devices
- 🔒 **Privacy-First** - Terminal commands and output are NOT logged
- ⏱️ **Auto-Disconnect** - Idle timeout after 10 minutes (configurable)
- 🔄 **Session Recovery** - Reconnect option if tab is accidentally closed

### How to Use

1. Select "Single Device" mode from the Target Scope dropdown
2. Choose a device from the dropdown menu
3. Click the green "🔌 Connect via CLI" button
4. Enter credentials in the connection dialog
5. Interact with the device through the terminal
6. Close the tab to disconnect (automatically logged)

---

## 📦 Technical Implementation

### New Components

1. **Flask-SocketIO** - WebSocket support for real-time communication
2. **xterm.js** - Industry-standard terminal emulator (loaded via CDN)
3. **CLI Manager Module** (`modules/cli_manager.py`) - SSH session management
4. **CLI Terminal Template** (`cli_terminal.html`) - Terminal UI

### Architecture

```
Browser (xterm.js)  <--WebSocket-->  Flask-SocketIO  <--SSH-->  Network Device
     |                                     |
     v                                     v
 Terminal UI                        CLI Manager
 (commands/output)            (session lifecycle)
```

---

## 🔧 Improvements & Fixes

### JUNOS Compatibility (v4.5.8 → v5.0.0)
- ✅ ELS/Non-ELS VLAN syntax detection
- ✅ SRX firewall MAC trace support
- ✅ Full compatibility: EX, QFX, SRX, MX series
- ✅ Backward compatibility: JUNOS 12.x through 22.x+

### Bug Fixes
- Fixed syntax error in `vlan_mgmt.py` (unclosed parenthesis)
- Fixed `generate_topology_html()` missing `extra_header` parameter
- Fixed topology mapper "dict object has no attribute 'upper'" error

### Code Quality
- Added comprehensive JUNOS validation documentation
- Updated all documentation to reflect v5.0.0 features
- Validated all function signatures and arguments
- No syntax errors in any module

### Branding
- Added permanent "Made by AI IDE" branding to web interface
- Visible in header on all application pages
- Included in CLI terminal interface

---

## 📋 Upgrade Instructions

### From v4.5.8 or earlier

1. **Download** the new v5.0.0 executable
2. **Replace** your old executable
3. **Install new dependency** (if running from source):
   ```bash
   pip install flask-socketio>=5.3.0
   ```
4. **Run** the new version

### Data Compatibility
- ✅ All inventory files compatible
- ✅ All saved configurations compatible
- ✅ Logs from previous versions readable

---

## 🎯 System Requirements

### Minimum Requirements
- **OS:** Windows 10/11 (64-bit)
- **RAM:** 4 GB
- **Storage:** 100 MB free space
- **Network:** Local network access to devices
- **Browser:** Chrome 90+, Firefox 88+, Edge 90+

### For CLI Terminal Feature
- **Browser:** Modern browser with WebSocket support
- **JavaScript:** Enabled
- **CDN Access:** For xterm.js library (or use local copy)

---

## 🔐 Security Notes

### Privacy-First Design
- Terminal **commands are NOT logged** in application logs
- Terminal **output is NOT logged** in application logs
- Only **connection events** (connect/disconnect) are logged
- SSH sessions are isolated per device
- Auto-disconnect on tab close

### Recommendations
- Use strong passwords for device access
- Enable enable/secret passwords where available
- Use SSH keys where supported
- Close terminal tabs when finished
- Monitor connection logs for unauthorized access

---

## 📚 Documentation

### Updated Documentation
- `docs/JUNOS-VALIDATION-SUMMARY.md` - Complete JUNOS compatibility guide
- `docs/02-APP-LOGIC.md` - Updated with CLI workflow
- `docs/06-TROUBLESHOOTING.md` - CLI troubleshooting added
- `docs/COMPLETION-SUMMARY.md` - v5.0.0 implementation summary
- `docs/HOW-TO-REBUILD.md` - Rebuild instructions updated

### New Documentation
- CLI terminal user guide (inline in application)
- WebSocket error handling procedures
- Session management best practices

---

## 🐛 Known Limitations

### CLI Terminal
- Requires modern browser with WebSocket support
- xterm.js loaded from CDN (requires internet or local copy)
- 10-minute idle timeout (configurable in future releases)
- One terminal per device tab (no multiplexing)

### JUNOS Support
- SRX VLAN provisioning limited (firewall architecture)
- MX routers use bridge domains (not traditional VLANs)
- Virtual chassis not explicitly handled

---

## 🎉 What's Next

### Planned for v5.1.0
- CLI session recording (optional, opt-in)
- Command history persistence
- Multi-tab terminal within single window
- SFTP file transfer integration

### Planned for v5.2.0
- Config diff viewer
- Scheduled config backups
- Enhanced topology visualization
- REST API for external integrations

---

## 📞 Support

### Getting Help
1. Check `docs/06-TROUBLESHOOTING.md` for common issues
2. Review `docs/JUNOS-VALIDATION-SUMMARY.md` for JUNOS-specific help
3. Use the "Extract Documentation" button in the application
4. Check connection logs for error details

### Reporting Issues
Include the following information:
- Application version (shown in header)
- Operating system
- Browser type and version
- Device type being accessed
- Error message or screenshot
- Steps to reproduce

---

## 🙏 Acknowledgments

- **xterm.js** - For the excellent terminal emulator
- **Flask-SocketIO** - For seamless WebSocket integration
- **Netmiko** - For reliable SSH connections
- **Contributors** - For feedback and feature suggestions

---

## 📄 License & Usage

Network Swiss Tool Pro v5.0.0  
© 2026 - All rights reserved.

**End of Release Notes**
