# Network Swiss Tool Pro v7.0.2 — Health wizard & MAC trace clarity

**Date:** 2026-05-24  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.2_OFFLINE.exe`

## Fixed

- **Startup “hang”:** Health wizard no longer auto-runs slow checks (discovery demo + CLI smoke) on open. **Continue to program** is the primary action.
- **Plugin false negative:** Registry check uses `get_all_metadata()`, threshold ≥10, lists plugin IDs; tolerates minor load warnings.

## Changed

- Health API: `POST /api/health-check/run` accepts `{ quick, full, include_cli }`; default is quick-only.
- Diagnostics MAC section documents inventory-wide trace vs CDP hop-by-hop.
- Ops docs: `docs/08-operations/health-wizard.md`, `mac-trace-howto.md`.

## Unchanged

- Discovery trust fixes from v7.0.1 remain in place.
