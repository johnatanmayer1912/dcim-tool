# FIX ALL — Consolidated prompt (from sweep W-BUG-SWEEP-2026-06-10-v7033)

**Status:** Executed 2026-06-10 → shipped **v7.0.33**

ACTIVATE: R-ARCH → R-ENG → R-QA → R-LIB → R-RECON → R-REL

Fix order (completed):

1. **NEW-S1** — Master password vault wipe when locked — `credential_manager.set_master_password` guard + test
2. **NEW-S2** — Plugin upload path traversal — `secure_filename` in `api_plugin_upload`
3. **NEW-S3** — Discovery job TOCTOU — `_discovery_job_snapshot()`
4. **NEW-S4** — JSON body guards — `_require_json_body()` shared helper
5. **NEW-S5** — Bounded int parsing — discovery `max_depth`/`timeout`, STP `vlan_id`
6. **NEW-S6** — Credential XSS — DOM-safe table render
7. **NEW-S7** — Clear credential label wipes sidebar fields
8. **NEW-S9** — `UPDATE_DATE` sync

Validation: **165/165 pytest PASS** · enterprise QA gate PASS

Post-fix: rebuild `NetworkSwissToolPro_v7.0.33_OFFLINE.exe` when shipping artifact.
