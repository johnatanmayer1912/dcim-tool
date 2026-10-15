# Network Swiss Tool Pro v6.5.3 Release Notes

**Release Date:** 2026-04-28  
**Version:** v6.5.3  
**Type:** Bugfix Release  
**Base:** v6.5.2

---

## Summary

v6.5.3 fixes five production bugs found after v6.5.2 shipped: a plugin registry syntax error that silently broke all plugin loading, missing report formatter functions that caused ImportError on every plugin, a VLAN scope bug that returned all devices when single mode had an empty host, and two data quality issues in report_formatter.

---

## Fixes

### [P0] Plugin Registry Syntax Error
**File:** `modules/plugin_registry.py`  
**Root cause:** `_validate_metadata()` had `::` (double colon) on line 216 — a Python syntax error that prevented the entire module from importing. All 9 plugins silently failed to load on every startup.  
**Fix:** Corrected `::` → `:`  
**Result:** All 9 plugins load with 0 errors.

### [P0] Missing Plugin Report Functions
**File:** `utils/report_formatter.py`  
**Root cause:** All 9 plugins import `save_plugin_report`, `append_to_master_report`, and 6 `format_*_report` functions that did not exist in the file. Every plugin load raised `ImportError`.  
**Fix:** Added all 9 missing functions with correct signatures.  
**Result:** 9 plugins, 0 errors.

### [P1] Single Device VLAN Operations → "0 target devices"
**File:** `vlan_checker_web.py`  
**Root cause:** `filter_inventory()` applied the group dropdown filter before the single-host match. If the group dropdown showed a non-matching group, the selected host was excluded.  
**Fix:** Group filter skipped entirely in single mode. Added empty-host guard (`if not target: return []`).  
**Result:** Single device operations work correctly regardless of group dropdown state.

### [P1] vPC Topology Map Disorganized
**Files:** `modules/adapters.py`, `utils/report_formatter.py`  
**Root cause:** vPC map used `barnesHut` physics producing a chaotic layout.  
**Fix:** Replaced with hierarchical `UD` layout. vPC summary replaced with structured table.

### [P1] Topology Side Panel Missing Speed/VLAN/MAC
**File:** `modules/topology_mapper.py`  
**Root cause:** `show interface status` parsed for link state only; Speed, VLAN, Duplex columns never extracted.  
**Fix:** Added `_parse_status_line_fields()`. Side panel now shows speed, VLAN, duplex, MACs.

---

## Files Modified

| File | Change |
|------|--------|
| `modules/plugin_registry.py` | Fixed `::` syntax error |
| `utils/report_formatter.py` | Added 9 missing plugin report functions; fixed vPC layout |
| `vlan_checker_web.py` | Fixed group filter + empty host guard |
| `modules/adapters.py` | vPC summary table |
| `modules/topology_mapper.py` | Speed/VLAN/duplex extraction |

---

## Build

- **EXE:** `dist/NetworkSwissToolPro_v6_5_3.exe` — 711.9 MB  
- **Package:** `dist_package_v6_5_3/`  
- **Plugins:** 9 bundled, 0 errors
