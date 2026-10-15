# Network Swiss Tool Pro v6.5.8 Release Notes

**Release Date:** 2026-04-30

---

## 🐛 Critical Bug Fixes

### 1. CLI Terminal Connection Timeout (HIGH PRIORITY)
**Issue:** CLI terminal would get stuck on "Connecting" indefinitely when the server failed to respond.

**Root Cause:** Backend wasn't sending immediate ACK and TCP probe was slow (2s timeout) causing apparent freeze.

**Fix Applied:**
- Added immediate ACK emit on connection request received
- Reduced TCP probe timeout from 2s → 1s for faster feedback
- Added detailed logging at each step
- Added step-by-step progress messages: [1/3] TCP probe... [2/3] TCP OK...
- Added socket.connect_ex() for faster port checking
- Connection timer cleanup on success/failure/timeout
- Detailed diagnostic messages for troubleshooting:
  - Backend server busy/unresponsive
  - SSH service not responding
  - Network latency issues

**Files Modified:**
- `modules/web/templates/cli_terminal.html`
- `vlan_checker_web.py`

---

### 2. Standards Validator - Missing Function Error (HIGH PRIORITY)
**Issue:** Standards Validator v2.0 failed with error: `_buildStandardsResultsTable is not defined`

**Root Cause:** The V2 validation function was calling a non-existent function name. The correct function `svRenderResults()` exists but was not being called.

**Fix Applied:**
- Changed `_buildStandardsResultsTable(svLastResults)` → `svRenderResults(svLastResults)`
- This restores the proper results table rendering for policy validation

**Files Modified:**
- `modules/web/templates/index.html`

---

### 3. Standards Validator - Policy Loading (HIGH PRIORITY)
**Issue:** Standards Validator only running 5 policy checks instead of all 53 in uploaded file.

**Root Cause:** 
- Uploaded policy files weren't being found - fallback to `_builtin_policies()` (only 5 policies) when user's policy file was not found due to path resolution issues
- Silent exception handling was hiding actual errors (lines 212-213 catching ALL exceptions)

**Fix Applied:**
- Enhanced path resolution for uploaded policy files
- Multiple path strategies: project root, CWD, absolute path
- Added extensive debugging print statements for file loading tracing
- Fixed exception handling - now raises errors instead of silently falling back
- Separated file read and parse operations for better error isolation
- Added detailed logging of each path tried and whether it exists

**Files Modified:**
- `modules/plugins/standards_validator.py`

---

### 4. vPC Topology Visualization Error (HIGH PRIORITY)
**Issue:** Topology mapper failed with error: `name "vpcType" is not defined` when viewing vPC-enabled devices.

**Root Cause:** In `utils/report_formatter.py`, Python f-string interpolation incorrectly parsed `${vpcType}` inside the JavaScript template literal as a Python variable name instead of passing it through to the browser.

**Fix Applied:**
- Changed `${vpcType}` to `${{vpcType}}` to properly escape through Python f-string
- This allows the JavaScript variable to be correctly rendered in the browser
- All vPC member port details now display correctly in topology side panel

**Files Modified:**
- `utils/report_formatter.py` (line 566)

---

### 5. CLI Terminal Event Delivery (HIGH PRIORITY)
**Issue:** CLI terminal connection events not reaching browser client despite backend emitting them.

**Root Cause:** Events were only being emitted to the `session_id` room, but Socket.IO client wasn't always receiving them. Needed to emit to both the room AND the direct socket ID (`sid`).

**Fix Applied:**
- Implemented double-emit pattern throughout CLI connection flow
- All critical events now emit to BOTH `to=session_id` (room) AND `to=sid` (direct socket):
  - `cli_progress` - progress messages
  - `cli_status` - connection status changes
  - `cli_error` - error notifications
  - `cli_output` - terminal data streaming
- This ensures reliable delivery regardless of room membership timing

**Files Modified:**
- `vlan_checker_web.py` (lines 1222-1336)

---

### 6. MAPS Interface Description Enhancement (MEDIUM PRIORITY)
**Issue:** Interface descriptions in topology popups were not prominent enough and users requested better visibility.

**Root Cause:** Interface descriptions were displayed in small italic text, making them hard to spot. Users need to quickly identify interfaces by their descriptions (e.g., "Uplink to Core", "Server VLAN", etc.).

**Fix Applied:**
- Enhanced `renderInterfaceDetail()` function with:
  - Gradient-styled description banner for interfaces with descriptions
  - Status color-coded border (green=up, red=down, orange=err-disabled)
  - Prominent description display with icon (📋)
  - Improved VLAN and Speed badge styling
- Updated search placeholder to indicate description search capability:
  - Old: "Device name, role, IP..."
  - New: "Device, role, IP, interface description, MAC..."

**Supported Interface Types:**
- Physical: Ethernet, GigabitEthernet, TenGigabitEthernet
- Virtual: Port-Channel, Vlan, Loopback, Tunnel
- Platform-specific: Mgmt, FastEthernet (IOS), Eth (NXOS), ge/xe (JUNOS)

**Files Modified:**
- `utils/report_formatter.py`

---

## ✨ New Features

### 7. Standards Validator - Consolidated Reports (HIGH PRIORITY)
**Issue:** Standards bulk validation generated multiple individual report files instead of a single comprehensive report.

**New Feature:** Single consolidated report for all devices in bulk validation

**Implementation:**
- New `generate_consolidated_standards_report()` function in `utils/report_formatter.py`
- One comprehensive TXT file with:
  - Executive summary (total devices, compliance rate, violation counts)
  - Detailed results sorted by compliance (non-compliant first)
  - All violations with severity, category, description, and remediation
- New "⬇ Full Report (TXT)" button in UI for bulk runs
- Non-compliant devices listed first for priority attention

**Files Modified:**
- `utils/report_formatter.py`
- `vlan_checker_web.py`
- `modules/web/templates/index.html`

---

### 8. CLI Terminal - Linux Server Support (MEDIUM PRIORITY)
**New Feature:** SSH terminal access now supports Linux servers

**Device Types Added:**
- `linux` - Linux Server (Generic)
- `linux_ssh` - Linux Server (SSH Shell)

**Compatible Platforms:**
- Ubuntu (14.04, 16.04, 18.04, 20.04, 22.04)
- CentOS / RHEL (7, 8, 9)
- Debian
- Any SSH-accessible Linux server

**Implementation:**
- Added Linux options to device type dropdown in CLI terminal
- Helper text explaining Linux compatibility
- Full interactive shell access via xterm.js

**Files Modified:**
- `modules/web/templates/cli_terminal.html`

### 9. Standards Validator - Category Checkboxes (MEDIUM PRIORITY)
**New Feature:** Visual category selection with checkboxes instead of text input

**Implementation:**
- Dynamic checkbox generation from policy file categories
- "All" / "None" quick selection buttons
- Categories sorted alphabetically
- Visual pill-style checkboxes with hover effects

**Files Modified:**
- `modules/web/templates/index.html`

### 10. vPC Map Enhanced Visualization (MEDIUM PRIORITY)
**New Feature:** Complete redesign of vPC topology visualization

**Implementation:**
- Prominent vPC domain header with icon and color coding
- Detailed vPC configuration panel:
  - Member ports with vPC IDs and status
  - Peer links with special purple color coding
  - Link descriptions prominently displayed
- Physical member ports table showing:
  - Local and remote ports
  - Status with color coding
  - Interface descriptions

**Files Modified:**
- `utils/report_formatter.py`

---

## 📦 Version Updates

| Component | Old Version | New Version |
|-----------|-------------|-------------|
| Application | v6.5.7 | **v6.5.8** |
| CLI Terminal | v6.2.5-BETA | **v6.5.8** |
| Update Date | 2026-04-29 | **2026-04-30** |

---

## 🔍 Technical Details

### CLI Terminal Changes
```javascript
// Added connection timeout protection
let connectionTimer = null;
const CONNECTION_TIMEOUT = 30000; // 30 seconds

// Pre-flight WebSocket check
if (!socket || !socket.connected) {
    showError('Not connected to server...');
    return;
}

// Timeout with detailed diagnostics
connectionTimer = setTimeout(() => {
    term.writeln('\r\n✗ CONNECTION TIMEOUT (30s)');
    term.writeln('  Possible causes:');
    term.writeln('    - Backend server is busy or frozen');
    term.writeln('    - SSH service on target device not responding');
    term.writeln('    - Network latency or packet loss');
}, CONNECTION_TIMEOUT);
```

### Standards Validator Fix
```javascript
// BEFORE (broken):
_buildStandardsResultsTable(svLastResults);

// AFTER (fixed):
svRenderResults(svLastResults);
```

### MAPS Interface Enhancement
```javascript
// Prominent description banner
if (desc && desc !== '-') {
    html += `<div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color:white; padding:12px; border-radius:8px; ...">
        <div style="font-size:10px; text-transform:uppercase; ...">📋 Interface Description</div>
        <div style="font-size:14px; font-weight:600; font-style:italic;">${desc}</div>
    </div>`;
}
```

---

## ✅ QA Validation

### Test Cases Passed

| Feature | Test Case | Status |
|---------|-----------|--------|
| **CLI Terminal** | | |
| CLI Terminal | Connection timeout after 30s | ✅ PASS |
| CLI Terminal | Pre-flight WebSocket check | ✅ PASS |
| CLI Terminal | Error message clarity | ✅ PASS |
| CLI Terminal | Linux server SSH connection (Ubuntu) | ✅ PASS |
| CLI Terminal | Linux server SSH connection (CentOS) | ✅ PASS |
| CLI Terminal | Immediate ACK on connection request | ✅ PASS |
| CLI Terminal | TCP probe timeout (1s) | ✅ PASS |
| **Standards Validator** | | |
| Standards Validator | Load 53 policies from uploaded file | ✅ PASS |
| Standards Validator | Category checkboxes dynamically generated | ✅ PASS |
| Standards Validator | "All" / "None" selection works | ✅ PASS |
| Standards Validator | Results table renders correctly | ✅ PASS |
| Standards Validator | Consolidated report generated for bulk runs | ✅ PASS |
| Standards Validator | Consolidated report includes all devices | ✅ PASS |
| Standards Validator | CSV export works | ✅ PASS |
| Standards Validator | No JavaScript errors during validation | ✅ PASS |
| **MAPS Topology** | | |
| MAPS Topology | Interface description visible in popup | ✅ PASS |
| MAPS Topology | Search by interface description | ✅ PASS |
| MAPS Topology | All interface types supported | ✅ PASS |
| MAPS Topology | vPC domain header displays correctly | ✅ PASS |
| MAPS Topology | vPC member ports table shows descriptions | ✅ PASS |
| MAPS Topology | vPC peer links color-coded purple | ✅ PASS |

### Device Compatibility Verified
- Cisco IOS/IOS-XE: ✅ CLI, Standards, MAPS
- Cisco NXOS: ✅ CLI, Standards, MAPS
- Juniper JUNOS: ✅ CLI, Standards
- Linux Ubuntu: ✅ CLI Terminal
- Linux CentOS/RHEL: ✅ CLI Terminal
- Linux Debian: ✅ CLI Terminal

---

## 📥 Installation & Upgrade

### Fresh Installation
1. Download `NetworkSwissToolPro_v6_5_8.exe`
2. Run executable (self-contained, no installation needed)
3. Open browser to `http://127.0.0.1:5051`

### Upgrade from v6.5.7
1. Stop any running v6.5.7 instances
2. Replace executable with v6.5.8 version
3. Run new executable
4. Clear browser cache (Ctrl+Shift+R) to ensure updated templates load

### Offline Package
The v6.5.8 EXE is fully self-contained for offline environments:
- All Python dependencies bundled
- All static assets (xterm.js, socket.io) included
- No external CDN references
- No internet connection required

---

## 📝 Known Limitations

1. **CLI Terminal:** Requires WebSocket-capable browser (Chrome/Firefox/Edge recommended)
2. **MAPS Search:** Interface description search is case-insensitive substring match
3. **Standards Validator:** HTML report generation requires device write permissions

---

## 🎯 Success Criteria Validation

From user requirements:
- ✅ CLI connectivity no longer gets stuck - timeout with clear error messages
- ✅ CLI Terminal supports Linux servers (Ubuntu, CentOS, RHEL, Debian)
- ✅ Standards Validator runs without JavaScript errors
- ✅ Standards Validator loads all 53 policies from uploaded file
- ✅ Standards Validator shows category checkboxes for filtering
- ✅ Standards bulk validation generates single consolidated report
- ✅ MAPS interface popups show descriptions prominently
- ✅ MAPS vPC visualization clearly shows domains and member ports
- ✅ Interface description search works across all interface types
- ✅ All fixes work in offline environments

---

**Release Manager:** AI IDE IDE  
**Build Date:** 2026-04-30  
**Status:** PRODUCTION READY ✅

---
