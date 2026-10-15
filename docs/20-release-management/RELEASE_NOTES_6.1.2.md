# Network Swiss Tool Pro v6.1.2-BETA Release Notes

**Release Date:** 2026-04-21  
**Build Target:** Offline / Air-gapped Environments  
**Priority:** CRITICAL FIX — CLI Terminal "Stuck at Connecting"

---

## Summary

Version 6.1.2-BETA is a **critical bugfix release** that resolves the CLI terminal being permanently stuck at "Connecting..." when attempting to SSH into network devices. Two root causes were identified and fixed.

---

## Root Cause Analysis

### Bug 1 (CRITICAL): `disabled_algorithms` Broke All Modern Devices

**File:** `modules/cli_manager.py`

**The broken code:**
```python
# v5.4.0 — THIS WAS WRONG:
transport_kwargs = {
    ...
    "disabled_algorithms": {"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},
}
```

**Why it broke:**
- `rsa-sha2-256` and `rsa-sha2-512` are the **preferred and often ONLY** host key algorithms on:
  - Cisco IOS-XE 17.3+ (SHA1/ssh-rsa disabled by default since 2021)
  - Cisco NXOS 9.3+ (same policy)
  - Any device hardened with `ip ssh server algorithm hostkey rsa-sha2-256`
- Disabling them forced Paramiko to fall back to `ssh-rsa` (SHA1)
- Modern devices **reject** SHA1 connections
- Result: SSH key exchange hangs → 45-second timeout → "Connecting..." forever

**The original intent** was to support legacy devices (IOS 12.x) that don't understand rsa-sha2. But it was applied globally, breaking all modern devices.

### Bug 2 (HIGH): Missing `import time`

**File:** `vlan_checker_web.py`

```python
# The cleanup thread used time.sleep(60) but 'time' was never imported
def _cleanup_idle_sessions_task():
    while True:
        ...
        time.sleep(60)  # NameError: name 'time' is not defined
```

This caused the idle session cleanup thread to crash immediately on every startup, visible in the console as:
```
NameError: name 'time' is not defined. Did you forget to import 'time'?
```

---

## Fixes Implemented

### Fix 1: Two-Pass SSH Connection Strategy

```python
# v6.1.2 — CORRECT: Two-pass with modern first, legacy fallback
def _do_connect(self):
    # Pass 1: Modern auto-negotiation (no disabled_algorithms)
    # Works with: IOS-XE 17.3+, NXOS 9.3+, Juniper, all modern devices
    try:
        self.client.connect(**base_kwargs)  # No disabled_algorithms
        
    except AuthenticationException:
        raise  # Wrong password — don't retry
        
    except Exception as e:
        if is_algorithm_error(e):
            # Pass 2: Legacy fallback (disable rsa-sha2 to force ssh-rsa)
            # Works with: IOS 12.x, old NXOS, legacy devices
            legacy_kwargs["disabled_algorithms"] = {
                "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]
            }
            self.client.connect(**legacy_kwargs)
        else:
            raise
```

### Fix 2: Added `import time`

```python
# vlan_checker_web.py — added at module level
import time
```

### Fix 3: Explicit Port Support

```python
# CLIConnection now reads port from device dict
self.port = int(device.get("port", 22))

# And passes it to paramiko
base_kwargs = {
    "hostname": self.host,
    "port": self.port,  # NEW
    ...
}
```

### Fix 4: Port Field in UI

The connection dialog now has an SSH Port field (default: 22) for devices using non-standard ports.

### Fix 5: Wider PTY

Terminal PTY size increased from 80×24 to 220×50 for better display of wide command output (e.g., `show interface status`).

---

## Files Modified

| File | Change |
|------|--------|
| `modules/cli_manager.py` | Two-pass SSH, port support, better error messages, wider PTY |
| `vlan_checker_web.py` | Added `import time`, version → 6.1.2-BETA, port in device dict |
| `modules/web/templates/cli_terminal.html` | Port field, v6.1.2 banner, pass info in terminal |
| `VERSION` | Updated to 6.1.2-BETA |
| `docs/02_RELEASES/CHANGELOG.md` | Added v6.1.2 entry |

---

## Device Compatibility Matrix

| Device | IOS Version | Algorithm | v6.1.1 | v6.1.2 |
|--------|-------------|-----------|--------|--------|
| Cisco IOS-XE | 17.3+ | rsa-sha2-256 | ❌ Broken | ✅ Pass 1 |
| Cisco NXOS | 9.3+ | rsa-sha2-256 | ❌ Broken | ✅ Pass 1 |
| Cisco IOS | 12.x–15.x | ssh-rsa | ✅ Worked | ✅ Pass 2 |
| Cisco NXOS | 7.x–9.2 | ssh-rsa | ✅ Worked | ✅ Pass 2 |
| Juniper JunOS | Any | rsa-sha2-256 | ❌ Broken | ✅ Pass 1 |
| HP Comware | Any | rsa-sha2-256 | ❌ Broken | ✅ Pass 1 |

---

## How to Verify the Fix

1. **Launch the EXE** — verify no `NameError: name 'time'` in console
2. **Open CLI Terminal** — click "Connect via CLI" in Single Device mode
3. **Connect to a modern device** (IOS-XE 17.3+) — should connect in <10s
4. **Connect to a legacy device** (IOS 12.x) — should connect via Pass 2 fallback
5. **Check terminal** — should show "Pass 1: Trying modern SSH algorithms..."

---

**Built with PyInstaller for offline deployment.**  
**Made by AI IDE**
