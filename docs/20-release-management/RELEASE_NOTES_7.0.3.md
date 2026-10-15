# Network Swiss Tool Pro v7.0.3 — Audit fix sprint & VPC Command Center

**Date:** 2026-05-24  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.3_OFFLINE.exe`

## Added

- **VPC Command Center** offline HTML: light theme, Overview split (engineering board + map), Link inventory tab, Collected data tab aligned with `topology_diagnostics_*/06_pre_render_presentation.json`.
- Operator guide: `docs/08-operations/vpc-command-center-guide.md`.

## Fixed (audit NEW-*)

- Frozen EXE loads bundled plugins when sidecar `plugins/` is empty (NEW-C1).
- Discovery: `visited` only after successful scan; `dry_run` skips SSH; Junos LLDP local port; edge dedup includes ports; per-job inventory JSON.
- CLI session lock held through full `connect()` (NEW-H3).
- Web job stores guarded with locks; STP job map pruned (NEW-H4).
- MAC trace platform-specific rows; adapters handle string `matches`; silent JSON on `/api/execute`.
- STP poll errors restore action buttons; health `ok` reflects full mode; IOS classifier tightened.

## Changed

- vPC Swiss Tools opens **VPC Command Center** (not hidden map-only view).
- `utils/vpc_map_shell.py` defers vis.js init until map pane is visible.

## Upgrade

Replace EXE; no database migration. Regenerate vPC HTML from Topology Mapper for new shell.
