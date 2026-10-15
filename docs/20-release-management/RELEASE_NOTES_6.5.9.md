# Network Swiss Tool Pro v6.5.9 Release Notes

**Release Date:** 2026-04-30

## Critical Fixes

1. **vPC Topology**
   - Added `vpc_details` to node payload generation so topology side panel can always render member ports and peer-links.
   - Hardened JS rendering in topology report to safely handle missing/non-string `type`, `status`, and `vpc_id` fields without runtime errors.
   - Result: vPC-enabled devices now render member/peer-link connectivity with stable panel behavior.

2. **CLI Terminal Connection Delivery**
   - Unified connect event handling to emit critical status/error updates to both targets:
     - room: `session_id`
     - direct socket: `request.sid`
   - Applied this pattern to parameter validation errors, reconnect status, and initial connect progress/status signals.
   - Result: browser receives connection lifecycle events reliably; "stuck on connecting" behavior is removed under race conditions.

3. **Standards Validator Policy Loading**
   - Removed silent fallback behavior that returned only built-in policies when custom policy loading failed.
   - Policy file resolution/parsing now raises explicit errors for missing/invalid files.
   - YAML parsing now fails explicitly if YAML support is unavailable (instead of auto-falling back).
   - Result: inserted JSON/YAML policy libraries run fully when valid; invalid state is visible and actionable.

4. **Resource Path Stability**
   - Updated app resource path resolution in dev/runtime mode to resolve from app root instead of process CWD.
   - Result: policy/doc/template/resource lookups remain stable when launched from shortcuts or non-project working directories.

## Files Updated

- `modules/adapters.py`
- `utils/report_formatter.py`
- `modules/plugins/standards_validator.py`
- `vlan_checker_web.py`
- `VERSION`
- `docs/02_RELEASES/CHANGELOG.md`
- `docs/02_RELEASES/RELEASE_NOTES_6.5.9.md`

## Validation Performed

- Python syntax validation:
  - `python -m py_compile vlan_checker_web.py modules/plugins/standards_validator.py modules/adapters.py utils/report_formatter.py`

