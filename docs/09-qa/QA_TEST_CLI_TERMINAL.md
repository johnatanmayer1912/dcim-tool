# QA Test Prompt: CLI Terminal Feature

> **Comprehensive testing for v5.0 CLI Terminal functionality**

**Test Suite:** CLI Terminal  
**Feature Version:** 5.0.0  
**Test Count:** 25 individual tests  
**Estimated Time:** 45 minutes  
**Prerequisites:** Lab devices (minimum 2), modern browser, WebSocket support

---

## 📋 Test Suite Overview

### Feature Components Tested
1. WebSocket communication (Flask-SocketIO)
2. SSH session management (cli_manager.py)
3. Terminal UI (xterm.js integration)
4. Session lifecycle (connect, command, disconnect)
5. Multi-session handling
6. Security & privacy features

### Critical Success Factors
- ✅ CLI button visible in UI
- ✅ WebSocket connection established
- ✅ SSH session created successfully
- ✅ Commands execute and return output
- ✅ Terminal output NOT logged (privacy)
- ✅ Session cleanup on disconnect
- ✅ Multiple sessions work concurrently

---

## 🧪 Individual Test Prompts

---

### CLI-001: UI Button Visibility and Accessibility
**Priority:** Critical  
**Type:** UI/UX  
**Automation:** Manual only (UI validation)

#### Objective
Verify "Connect via CLI" button is visible and accessible in Single Device mode.

#### Prerequisites
- [ ] Application running (web interface)
- [ ] Inventory loaded with at least one device

#### Procedure
1. Open browser to `http://localhost:5000`
2. In "Target Scope" dropdown, select "Single Device"
3. Verify "Select Device" dropdown appears
4. Select any device from dropdown
5. Observe below the dropdown

#### Expected Results
- [ ] Green button with text "🔌 Connect via CLI" visible
- [ ] Button positioned below device dropdown
- [ ] Button style matches UI (green background, white text)
- [ ] Helper text "Opens terminal in new tab" appears below button
- [ ] Button clickable (cursor changes to pointer)

#### Pass Criteria
All expected results present and functional.

#### Fail Criteria
- Button not visible
- Button not clickable
- Wrong styling
- Missing helper text

---

### CLI-002: Terminal Page Load
**Priority:** Critical  
**Type:** UI/UX  
**Automation:** Can automate with Selenium/Playwright

#### Objective
Verify CLI terminal page loads correctly when button clicked.

#### Prerequisites
- [ ] Application running
- [ ] CLI-001 passed

#### Procedure
1. Navigate to main interface
2. Select "Single Device" mode
3. Select a device
4. Click "🔌 Connect via CLI" button
5. Wait for new tab to open
6. Observe new tab content

#### Expected Results
- [ ] New browser tab opens automatically
- [ ] Tab title shows "CLI Terminal - Network Swiss Tool Pro"
- [ ] Page header shows "🖥️ CLI Terminal"
- [ ] Connection dialog appears (modal overlay)
- [ ] Terminal container visible in background
- [ ] xterm.js CSS loaded (no styling errors)

#### Pass Criteria
Terminal page fully rendered with no errors.

#### Fail Criteria
- Tab doesn't open
- Page shows 404 error
- Missing CSS/styles
- JavaScript errors in console

---

### CLI-003: Connection Dialog Validation
**Priority:** High  
**Type:** UI/UX  
**Automation:** Manual (form validation)

#### Objective
Verify connection dialog captures all required credentials.

#### Prerequisites
- [ ] Terminal page loaded (CLI-002)

#### Procedure
1. Observe connection dialog
2. Check all form fields present
3. Test field validation
4. Check device type dropdown

#### Expected Results
- [ ] "Device Host" field pre-filled with selected device IP
- [ ] "Device Type" dropdown with options:
  - Cisco IOS
  - Cisco IOS-XE
  - Cisco NXOS
  - Juniper JUNOS
  - HP Comware
  - Huawei
  - Arista EOS
- [ ] "Username" field empty (mandatory)
- [ ] "Password" field empty (mandatory, masked)
- [ ] "Enable Password" field empty (optional, masked)
- [ ] "Connect" button enabled
- [ ] "Cancel" button enabled

#### Pass Criteria
All fields present and functional.

#### Fail Criteria
- Missing fields
- Wrong device type options
- Fields not editable
- Buttons non-functional

---

### CLI-004: WebSocket Connection Establishment
**Priority:** Critical  
**Type:** Functional  
**Automation:** Can automate with WebSocket client

#### Objective
Verify WebSocket connection established between browser and backend.

#### Prerequisites
- [ ] Terminal page open
- [ ] Connection dialog ready

#### Procedure
1. Open browser developer tools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Enter valid credentials in dialog
5. Click "Connect"
6. Observe WebSocket traffic

#### Expected Results
- [ ] WebSocket connection request sent to `ws://localhost:5000/socket.io/`
- [ ] Connection status shows "Connecting..." briefly
- [ ] WebSocket handshake completes (status 101)
- [ ] `cli_connect` event emitted with session data
- [ ] Server responds with `cli_status` event
- [ ] No WebSocket errors in console

#### Pass Criteria
WebSocket connected and events flowing.

#### Fail Criteria
- WebSocket connection refused
- Connection times out
- Socket.IO errors
- No events transmitted

---

### CLI-005: SSH Connection Success
**Priority:** Critical  
**Type:** Functional  
**Automation:** Requires actual device

#### Objective
Verify SSH connection to device succeeds.

#### Prerequisites
- [ ] Valid test device available
- [ ] Device credentials known
- [ ] Network connectivity confirmed

#### Procedure
1. Enter device host/IP in dialog
2. Select correct device type
3. Enter valid username
4. Enter valid password
5. Click "Connect"
6. Wait for connection (max 30 seconds)

#### Expected Results
- [ ] Status indicator changes to green "Connected"
- [ ] Header updates to show device hostname/IP
- [ ] Tab title updates to "CLI: {hostname}"
- [ ] Terminal shows connection message
- [ ] Device prompt appears in terminal

#### Pass Criteria
Connected and device prompt visible.

#### Fail Criteria
- Connection timeout
- Authentication failure
- Protocol error
- No prompt displayed

---

### CLI-006: SSH Connection Failure Handling
**Priority:** High  
**Type:** Functional/Error Handling  
**Automation:** Can simulate with wrong credentials

#### Objective
Verify graceful handling of connection failures.

#### Prerequisites
- [ ] Terminal page open
- [ ] Connection dialog ready

#### Procedure
1. Enter device host
2. Enter WRONG username
3. Enter WRONG password
4. Click "Connect"
5. Observe error handling

#### Expected Results
- [ ] Error message displayed: "Connection failed: Authentication failed"
- [ ] Status shows red "Disconnected"
- [ ] Connection dialog remains open
- [ ] Fields retain entered values
- [ ] "Reconnect" button appears
- [ ] No crash or freeze

#### Pass Criteria
Clear error message, no crash, retry option available.

#### Fail Criteria
- No error message
- Application crashes
- Dialog closes unexpectedly
- Infinite loading spinner

---

### CLI-007: Command Execution - Basic
**Priority:** Critical  
**Type:** Functional  
**Automation:** Requires connected session

#### Objective
Verify commands execute and return output.

#### Prerequisites
- [ ] SSH session connected (CLI-005)

#### Procedure
1. Type command: `show version` (or platform equivalent)
2. Press Enter
3. Wait for response (max 10 seconds)
4. Observe terminal output

#### Expected Results
- [ ] Command echoes in terminal
- [ ] Output appears below command
- [ ] Output matches device response
- [ ] Prompt returns after execution
- [ ] No mangled text or encoding issues

#### Pass Criteria
Command executes and output displays correctly.

#### Fail Criteria
- Command not sent
- No output received
- Garbled output
- Terminal freezes

---

### CLI-008: Command Execution - Multiple Commands
**Priority:** High  
**Type:** Functional  
**Automation:** Requires connected session

#### Objective
Verify multiple consecutive commands work.

#### Prerequisites
- [ ] SSH session connected

#### Procedure
1. Execute: `show version`
2. Execute: `show running-config`
3. Execute: `show interfaces brief`
4. Execute: `show vlans`

#### Expected Results
- [ ] All four commands execute successfully
- [ ] Each command has separate output
- [ ] No command interference
- [ ] Prompt returns after each
- [ ] Terminal scrolls correctly

#### Pass Criteria
All commands execute in sequence without errors.

#### Fail Criteria
- Commands hang
- Output interleaved incorrectly
- Terminal corruption
- Session disconnect

---

### CLI-009: Terminal Output Privacy (Security)
**Priority:** Critical  
**Type:** Security  
**Automation:** Can check log files

#### Objective
Verify terminal output is NOT logged (privacy feature).

#### Prerequisites
- [ ] SSH session connected
- [ ] Log directory accessible

#### Procedure
1. Connect to device (CLI-005)
2. Execute sensitive command: `show running-config`
3. Execute: `show users`
4. Execute: `show ip route`
5. Disconnect session
6. Check application logs

#### Expected Results
- [ ] Log shows "CLI session connected to {host}"
- [ ] Log shows "CLI session disconnected from {host}"
- [ ] NO command text in logs
- [ ] NO command output in logs
- [ ] NO device configuration in logs

#### Pass Criteria
Only connect/disconnect logged, no terminal content.

#### Fail Criteria
- Commands logged
- Output logged
- Sensitive data in logs

**Security Note:** This is v5.0 privacy feature.

---

### CLI-010: Session Timeout (Idle Disconnect)
**Priority:** High  
**Type:** Functional  
**Automation:** Requires 10-minute wait

#### Objective
Verify idle session times out after 10 minutes.

#### Prerequisites
- [ ] SSH session connected
- [ ] 10 minutes available for test

#### Procedure
1. Connect to device
2. Execute one command
3. Leave terminal idle (no input)
4. Wait 10 minutes
5. Observe status

#### Expected Results
- [ ] After 10 minutes, status shows "Disconnected"
- [ ] Log entry: "CLI session timeout for {session_id}"
- [ ] Terminal shows disconnect message
- [ ] Reconnect button available

#### Pass Criteria
Session disconnects automatically after 10 min idle.

#### Fail Criteria
- Session stays connected > 10 min
- No timeout message
- No log entry

---

### CLI-011: Manual Disconnect
**Priority:** High  
**Type:** Functional  
**Automation:** Manual

#### Objective
Verify manual disconnect button works.

#### Prerequisites
- [ ] SSH session connected

#### Procedure
1. Verify "Disconnect" button enabled
2. Click "Disconnect" button
3. Observe terminal and status

#### Expected Results
- [ ] Status changes to red "Disconnected"
- [ ] Terminal shows "✗ Disconnected" message
- [ ] SSH session terminated
- [ ] Log entry: "CLI session disconnected"
- [ ] "Connect" button re-enabled

#### Pass Criteria
Clean disconnect with proper cleanup.

#### Fail Criteria
- Session remains connected
- No disconnect message
- Button non-functional

---

### CLI-012: Tab Close Auto-Disconnect
**Priority:** Critical  
**Type:** Functional  
**Automation:** Manual

#### Objective
Verify closing browser tab disconnects SSH session.

#### Prerequisites
- [ ] SSH session connected
- [ ] Log monitoring active

#### Procedure
1. Connect to device
2. Verify connection active
3. Close browser tab/window
4. Check application logs

#### Expected Results
- [ ] Tab closes without error
- [ ] Log entry within 5 seconds: "CLI session disconnected"
- [ ] SSH connection terminated on server
- [ ] No orphaned sessions

#### Pass Criteria
Tab close triggers immediate cleanup.

#### Fail Criteria
- No disconnect log entry
- Session remains active after tab close
- Resource leak

---

### CLI-013: Multiple Concurrent Sessions
**Priority:** High  
**Type:** Integration  
**Automation:** Manual (requires multiple devices)

#### Objective
Verify multiple CLI sessions work simultaneously.

#### Prerequisites
- [ ] 2+ devices available
- [ ] 2+ browser tabs/windows

#### Procedure
1. Open CLI terminal to Device A (Tab 1)
2. Open CLI terminal to Device B (Tab 2)
3. Connect both sessions
4. Execute different commands on each
5. Observe both terminals

#### Expected Results
- [ ] Both sessions connect independently
- [ ] Tab titles show different hostnames
- [ ] Commands on Device A don't affect Device B
- [ ] Both terminals responsive
- [ ] Both sessions logged separately

#### Pass Criteria
Multiple sessions isolated and functional.

#### Fail Criteria
- Sessions interfere
- Commands cross between sessions
- Performance degradation
- One session disconnects other

---

### CLI-014: Reconnect Functionality
**Priority:** Medium  
**Type:** Functional  
**Automation:** Manual

#### Objective
Verify reconnect button after disconnect.

#### Prerequisites
- [ ] Previously disconnected session

#### Procedure
1. Disconnect session (CLI-011) or wait for timeout (CLI-010)
2. Observe "Reconnect" button appears
3. Click "Reconnect"
4. Enter credentials
5. Connect

#### Expected Results
- [ ] Reconnect button visible after disconnect
- [ ] Clicking opens connection dialog
- [ ] New session created successfully
- [ ] Previous session data not retained (security)

#### Pass Criteria
Clean reconnect with fresh session.

#### Fail Criteria
- Reconnect fails
- Old session data leaks
- Credentials cached unexpectedly

---

### CLI-015: Terminal Clear Function
**Priority:** Low  
**Type:** UI/UX  
**Automation:** Manual

#### Objective
Verify clear terminal button works.

#### Prerequisites
- [ ] Session with command history

#### Procedure
1. Execute several commands
2. Terminal has scrollback content
3. Click "Clear" button
4. Observe terminal

#### Expected Results
- [ ] Terminal screen clears
- [ ] Scrollback history removed
- [ ] Prompt remains at top
- [ ] Can continue typing commands

#### Pass Criteria
Terminal clears but session remains active.

#### Fail Criteria
- Screen doesn't clear
- Session disconnects
- Prompt lost

---

### CLI-016: Terminal Resizing
**Priority:** Medium  
**Type:** UI/UX  
**Automation:** Manual

#### Objective
Verify terminal adapts to window resizing.

#### Prerequisites
- [ ] Session connected
- [ ] Browser window resizable

#### Procedure
1. Connect to device
2. Resize browser window:
   - Make smaller
   - Make larger
   - Maximize
   - Restore
3. Observe terminal layout

#### Expected Results
- [ ] Terminal resizes with window
- [ ] Text reflows correctly
- [ ] No text truncation
- [ ] Scrollbar adjusts
- [ ] xterm.js fit-addon working

#### Pass Criteria
Terminal responsive to all resize operations.

#### Fail Criteria
- Terminal fixed size
- Text cut off
- Layout breaks

---

### CLI-017: Cross-Browser Compatibility
**Priority:** Medium  
**Type:** UI/UX  
**Automation:** Manual (multiple browsers)

#### Objective
Verify CLI works across different browsers.

#### Prerequisites
- [ ] Chrome installed
- [ ] Firefox installed
- [ ] Edge installed

#### Procedure
Repeat CLI-001 through CLI-007 in:
1. Chrome (latest)
2. Firefox (latest)
3. Edge (latest)

#### Expected Results
- [ ] All browsers: Page loads
- [ ] All browsers: WebSocket connects
- [ ] All browsers: Commands execute
- [ ] All browsers: Terminal renders correctly

#### Pass Criteria
Feature works in all supported browsers.

#### Fail Criteria
- Browser-specific failures
- WebSocket issues in specific browser
- Rendering differences

---

### CLI-018: Performance Under Load
**Priority:** Medium  
**Type:** Performance  
**Automation:** Manual (load simulation)

#### Objective
Verify terminal responsive during heavy output.

#### Prerequisites
- [ ] Session connected
- [ ] Device with large output capability

#### Procedure
1. Connect to device
2. Execute command with large output: `show tech-support` or `show running-config` on large config
3. Observe terminal performance
4. Measure response time

#### Expected Results
- [ ] Output streams smoothly
- [ ] No browser freeze
- [ ] Can scroll during output
- [ ] Memory usage stable
- [ ] Output completes within reasonable time

#### Pass Criteria
Terminal handles large output without degradation.

#### Fail Criteria
- Browser freezes
- Out of memory error
- Output truncated
- Unresponsive UI

---

### CLI-019: Keyboard Input Handling
**Priority:** High  
**Type:** UI/UX  
**Automation:** Manual

#### Objective
Verify all keyboard input works correctly.

#### Prerequisites
- [ ] Session connected

#### Procedure
1. Type alphabetic characters
2. Type numeric characters
3. Type special characters: !@#$%
4. Press Backspace (deletes characters)
5. Press Enter (sends command)
6. Press Ctrl+C (interrupt - if supported)
7. Press Tab (if command completion)
8. Use arrow keys (if history navigation)

#### Expected Results
- [ ] All characters appear correctly
- [ ] Backspace removes last character
- [ ] Enter sends command
- [ ] Cursor position correct
- [ ] No phantom characters

#### Pass Criteria
Keyboard input matches expected behavior.

#### Fail Criteria
- Characters don't appear
- Wrong characters appear
- Backspace non-functional
- Cursor position wrong

---

### CLI-020: Device Type Compatibility
**Priority:** High  
**Type:** Compatibility  
**Automation:** Requires multiple device types

#### Objective
Verify CLI works with different device platforms.

#### Prerequisites
- [ ] At least 2 different device types available

#### Procedure
Test CLI-005 through CLI-008 on:
1. Cisco IOS device
2. Juniper JUNOS device
3. HP Comware device

#### Expected Results
- [ ] All device types connect successfully
- [ ] All device types execute commands
- [ ] Prompt recognition works per platform
- [ ] No platform-specific errors

#### Pass Criteria
CLI works across all supported platforms.

#### Fail Criteria
- Platform-specific connection failures
- Prompt not recognized
- Command execution fails

---

### CLI-021: Session Isolation Security
**Priority:** Critical  
**Type:** Security  
**Automation:** Manual

#### Objective
Verify sessions are properly isolated.

#### Prerequisites
- [ ] Two sessions open to same device (CLI-013)

#### Procedure
1. Open Session A to Device X
2. Open Session B to Device X (same device)
3. In Session A, execute: `show users` or `who`
4. In Session B, execute different command
5. Verify no cross-contamination

#### Expected Results
- [ ] Session A commands don't appear in Session B
- [ ] Session B commands don't appear in Session A
- [ ] Output completely separate
- [ ] Closing one session doesn't affect other

#### Pass Criteria
Complete session isolation maintained.

#### Fail Criteria
- Commands leak between sessions
- Output mixed
- One disconnect affects other

---

### CLI-022: Invalid Command Handling
**Priority:** Medium  
**Type:** Error Handling  
**Automation:** Manual

#### Objective
Verify graceful handling of invalid commands.

#### Prerequisites
- [ ] Session connected

#### Procedure
1. Type invalid command: `xyz123invalid`
2. Press Enter
3. Observe device response

#### Expected Results
- [ ] Command sent to device
- [ ] Device returns error message
- [ ] Error displays in terminal
- [ ] Prompt returns
- [ ] Session remains connected

#### Pass Criteria
Invalid commands handled gracefully.

#### Fail Criteria
- Session disconnects
- Terminal hangs
- No error feedback
- Application crash

---

### CLI-023: Long-Running Command
**Priority:** Medium  
**Type:** Functional  
**Automation:** Manual

#### Objective
Verify long-running commands don't timeout.

#### Prerequisites
- [ ] Session connected
- [ ] Device with traceroute/ping capability

#### Procedure
1. Execute long command: `traceroute 8.8.8.8` or `ping -c 100 <ip>`
2. Wait for completion (may take minutes)
3. Observe terminal during execution

#### Expected Results
- [ ] Command starts immediately
- [ ] Output streams in real-time
- [ ] No premature timeout
- [ ] Command completes or interrupted
- [ ] Session stable throughout

#### Pass Criteria
Long commands execute without timeout issues.

#### Fail Criteria
- Premature timeout
- Session disconnect during command
- Output buffering issues

---

### CLI-024: Network Disconnection Recovery
**Priority:** High  
**Type:** Error Handling  
**Automation:** Manual (simulated)

#### Objective
Verify graceful handling of network interruption.

#### Prerequisites
- [ ] Session connected
- [ ] Ability to interrupt network (VPN disconnect, firewall block)

#### Procedure
1. Connect to remote device
2. Verify session active
3. Interrupt network connection (disconnect VPN, block port)
4. Wait 30 seconds
5. Observe status
6. Restore network
7. Try reconnect

#### Expected Results
- [ ] Session detects disconnection
- [ ] Status changes to "Disconnected"
- [ ] Error message shown
- [ ] No application crash
- [ ] Reconnect possible after network restore

#### Pass Criteria
Network interruption handled gracefully.

#### Fail Criteria
- Application crashes
- Frozen UI
- No disconnect detection
- Cannot reconnect

---

### CLI-025: Complete Workflow Integration
**Priority:** Critical  
**Type:** Integration  
**Automation:** Manual

#### Objective
Verify CLI integrates with full application workflow.

#### Prerequisites
- [ ] All previous tests passed
- [ ] Full inventory available

#### Procedure
1. Load inventory with 5+ devices
2. Run VLAN Audit on all devices
3. While audit running, open CLI to one device
4. Execute commands to verify device state
5. Close CLI tab
6. Export audit results
7. Generate topology map
8. Open CLI to different device
9. Make configuration change
10. Run VLAN Audit again

#### Expected Results
- [ ] CLI works during other operations
- [ ] No interference between features
- [ ] Data consistent across features
- [ ] All features complete successfully
- [ ] System stable throughout

#### Pass Criteria
CLI integrates seamlessly with all features.

#### Fail Criteria
- Performance degradation
- Feature interference
- Data inconsistency
- System instability

---

## 📊 Test Results Summary

### Test Execution Log

| Test ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| CLI-001 | Button Visibility | Critical | ⬜ | |
| CLI-002 | Terminal Page Load | Critical | ⬜ | |
| CLI-003 | Connection Dialog | High | ⬜ | |
| CLI-004 | WebSocket Connection | Critical | ⬜ | |
| CLI-005 | SSH Connection Success | Critical | ⬜ | |
| CLI-006 | Connection Failure | High | ⬜ | |
| CLI-007 | Command Execution Basic | Critical | ⬜ | |
| CLI-008 | Multiple Commands | High | ⬜ | |
| CLI-009 | Output Privacy | Critical | ⬜ | |
| CLI-010 | Session Timeout | High | ⬜ | |
| CLI-011 | Manual Disconnect | High | ⬜ | |
| CLI-012 | Tab Close Disconnect | Critical | ⬜ | |
| CLI-013 | Multiple Sessions | High | ⬜ | |
| CLI-014 | Reconnect | Medium | ⬜ | |
| CLI-015 | Terminal Clear | Low | ⬜ | |
| CLI-016 | Terminal Resize | Medium | ⬜ | |
| CLI-017 | Cross-Browser | Medium | ⬜ | |
| CLI-018 | Performance | Medium | ⬜ | |
| CLI-019 | Keyboard Input | High | ⬜ | |
| CLI-020 | Device Compatibility | High | ⬜ | |
| CLI-021 | Session Isolation | Critical | ⬜ | |
| CLI-022 | Invalid Command | Medium | ⬜ | |
| CLI-023 | Long Command | Medium | ⬜ | |
| CLI-024 | Network Recovery | High | ⬜ | |
| CLI-025 | Full Workflow | Critical | ⬜ | |

### Summary Statistics
- **Total Tests:** 25
- **Critical:** 9 tests
- **High:** 10 tests
- **Medium:** 5 tests
- **Low:** 1 test
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___
- **Pass Rate:** ___%

### Critical Test Requirements
**All Critical tests (CLI-001, 002, 004, 005, 007, 009, 012, 021, 025) MUST pass for release.**

---

## 🎓 Tester Guidelines

### Before Testing
1. Read feature documentation in `../../02_FEATURES/CLI_TERMINAL/`
2. Understand WebSocket and SSH concepts
3. Have test devices ready
4. Clear browser cache

### During Testing
1. Document exact browser version
2. Record device models tested
3. Note any deviations from procedure
4. Screenshot failures
5. Check browser console for errors

### After Testing
1. Complete results table
2. Document any new issues
3. Verify all critical tests passed
4. Sign off on results

---

## 🆘 Troubleshooting Test Failures

### WebSocket Won't Connect
- Check firewall settings
- Verify port 5000 available
- Check browser WebSocket support
- Review `modules/cli_manager.py` logs

### SSH Connection Fails
- Verify device reachable
- Check credentials
- Confirm device type correct
- Review Netmiko compatibility

### Terminal Not Rendering
- Check xterm.js CDN accessible
- Verify JavaScript enabled
- Check browser console for errors
- Test in different browser

---

## 📝 Version History

- **v5.0.0** (2026-04-19): Initial comprehensive test suite for CLI Terminal feature
- Tests designed for xterm.js + Flask-SocketIO implementation
- Security tests added for privacy feature (CLI-009)

---

**Test Suite Owner:** QA Lead  
**Feature Owner:** Backend Team  
**Last Execution:** _________  
**Next Scheduled:** _________

---

*This test suite ensures the CLI Terminal feature works safely, securely, and reliably.*
