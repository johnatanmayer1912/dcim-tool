# Network Swiss Tool Pro v6.5.4 Release Notes

**Release Date:** 2026-04-28  
**Version:** v6.5.4  
**Type:** Bugfix + Feature Release  
**Base:** v6.5.3

---

## Summary

v6.5.4 fixes the CLI terminal "stuck on connecting" issue, resolves four M-severity bugs (missing `log_func` and `finally` disconnect in core modules), removes the dangerous `restore_backup()` method, and adds the new Standards Validator plugin with a 20+ policy YAML library.

---

## New Features

### Standards Validator Plugin
**File:** `modules/plugins/standards_validator.py`  
**Policy Library:** `policies/standards.yaml`

Compares live device configuration against a user-editable YAML policy library. Reports violations with exact remediation commands per device. Read-only — never pushes changes.

**Capabilities:**
- 5 check types: contains, not_contains, regex_match, regex_extract, line_format
- 20+ built-in policies: Security, NTP, SNMP, Logging, Banner, Naming, AAA
- Severity filtering (critical/high/medium/low)
- Category filtering (comma-separated)
- Per-device remediation scripts (ready to paste in config mode)
- Human-readable reports (same style as VLAN missing report)
- No code changes needed to add new standards — edit the YAML file

**Sample output:**
```
[CRITICAL]  telnet_disabled
Description: Telnet must be disabled on all VTY lines
Current:     transport input telnet ssh
Expected:    Must NOT contain: transport input telnet
Fix:
  line vty 0 4
   transport input ssh
```

---

## Fixes

### [P0] CLI Terminal Stuck on "Connecting"
**File:** `modules/cli_manager.py` — complete rewrite with full inline documentation.

**Root causes fixed:**
1. `_do_connect()` never forwarded progress to `log_callback` — frontend saw nothing during the 10–45s SSH handshake. Fixed: every SSH step now emits progress.
2. `self.hostname` was never updated from the initial IP. Fixed: initial prompt read after shell open to extract real hostname.
3. Buffered prompt bytes not forwarded to frontend. Fixed: prompt forwarded immediately so device prompt appears without delay.

**Inline documentation added:**
- Architecture diagram showing the full connection flow
- Critical rules that must not be broken (join_room, no nested ThreadPoolExecutor, single emit target)
- HOW TO VALIDATE CLI IS WORKING checklist
- COMMON FAILURE MODES with root causes

### [P1] M-Bug: Missing `log_func` + `finally` disconnect
**Files:** `modules/network_audit.py`, `modules/config_backup.py`, `modules/save_config.py`, `modules/vlan_compare.py`

All four modules were missing:
- `log_func=None` parameter (no UI feedback during operation)
- `finally: conn.disconnect()` (SSH session leaks on exception)

Fixed in all four modules.

### [P1] Removed `restore_backup()`
**Files:** `utils/config_backup_system.py`, `modules/vlan_mgmt_production.py`, `vlan_checker_web.py`

The experimental `restore_backup()` method used a blind line-by-line paste approach that corrupts NX-OS configurations. Removed entirely along with `rollback_vlan_change()` and the `/api/plugins/rollback` route.

### [P2] Added `utils/app_logger.py`
Production-grade structured logging with rotating JSON files, audit trail, GUI callback support, and `export_logs()` for AI/support analysis.

---

## MAPS Side Panel Fixes (also in v6.5.4)

### [P0] Interfaces/Speed/VLAN/MACs Not Showing
**Files:** `modules/topology_mapper.py`, `modules/adapters.py`, `utils/report_formatter.py`

Four root causes fixed:
1. `int_meta` entries from desc parser missing `speed`/`vlan`/`duplex`/`macs` keys — JS got `undefined`. Fixed: all fields initialised in every code path.
2. MAC normalization mismatch — `_parse_mac_table` used `norm_int()` but valid_interfaces check was case-sensitive exact match. Fixed: case-insensitive fallback.
3. Edge panel `f_int_data` lookup used raw CDP port name (`GigabitEthernet0/1`) but `int_meta` keys are normalized (`Gi0/1`). Fixed: `norm_int()` applied before lookup.
4. `adapters.py` MAC merge block didn't guarantee all fields exist. Fixed: `setdefault()` for all display fields.

### [P1] Neighbor-Only Nodes Show Nothing
Nodes discovered via CDP/LLDP but not directly scanned showed blank side panel. Fixed: "Interface Data Unavailable" message with explanation.

---

## Files Modified

| File | Change |
|------|--------|
| `modules/cli_manager.py` | Complete rewrite with inline docs + hostname resolution |
| `modules/network_audit.py` | Added log_func + finally disconnect |
| `modules/config_backup.py` | Added log_func + finally disconnect |
| `modules/save_config.py` | Added log_func + finally disconnect |
| `modules/vlan_compare.py` | Added log_func + finally disconnect |
| `utils/config_backup_system.py` | Removed restore_backup() |
| `modules/vlan_mgmt_production.py` | Removed rollback_vlan_change() |
| `vlan_checker_web.py` | Removed /api/plugins/rollback route |
| `modules/topology_mapper.py` | Fixed int_meta field init + MAC normalization |
| `modules/adapters.py` | Fixed edge lookup + setdefault fields |
| `utils/report_formatter.py` | Fixed side panel rendering + neighbor-only message |
| `utils/app_logger.py` | New: production logging system |
| `modules/plugins/standards_validator.py` | New: Standards Validator plugin |
| `policies/standards.yaml` | New: 20+ policy library |
| `PLUGINS_INCLUDED.txt` | Updated: 10 plugins |

---

## Build

- **EXE:** `dist/NetworkSwissToolPro_v6_5_4.exe` — 711.9 MB  
- **Package:** `dist_package_v6_5_4/`  
- **Plugins:** 10 bundled, 0 errors
