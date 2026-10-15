# LIBRARIAN audit — v7.0.51 (2026-06-18)

| Field | Value |
|-------|-------|
| **Scope** | Full docs sync after Standard Map UI/UX ship |
| **VERSION file** | 7.0.51 |
| **Artifact** | `NetworkSwissToolPro_v7.0.51_OFFLINE.exe` |

---

## Actions taken

1. Hub/index version stamps updated to **7.0.51** (`docs/README.md`, `DOCUMENTATION_MASTER_INDEX.md`, `DOCS_CANONICAL_MAP.md`, overview, ops, rebuild, QA).
2. Added [standard-map-shell.md](../06-ui-ux/standard-map-shell.md) — canonical Standard Map UX reference.
3. Updated [visualization-pipeline.md](../01-architecture/visualization-pipeline.md), [UTILITIES_DOCUMENTATION.md](../02-codebase/UTILITIES_DOCUMENTATION.md), [TOPOLOGY_ISSUES.md](../07-operations/TOPOLOGY_ISSUES.md).
4. Added [RELEASE_NOTES_7.0.51.md](../20-release-management/RELEASE_NOTES_7.0.51.md); synced [release-history.md](../20-release-management/release-history.md).
5. Updated [exe-smoke-checklist.md](../07-operations/exe-smoke-checklist.md) and [10-rebuild/README.md](../10-rebuild/README.md) spec pointer.
6. Truth audit: [DOCUMENTATION_TRUTH_AUDIT_2026-06-18.md](../DOCUMENTATION_TRUTH_AUDIT_2026-06-18.md).

---

## Verification

| Check | Result |
|-------|--------|
| `/VERSION` | 7.0.51 |
| Root `/CHANGELOG.md` [v7.0.51] | present |
| `tests/test_standard_map_v7049.py` | 11 passed |
| `_prebuild.py` | ALL CHECKS PASSED |
| PyInstaller v7.0.51 spec | built |

---

## Known legacy drift (explicit archive)

- `docs/20-release-management/CHANGELOG.md` — partial mirror; **root `/CHANGELOG.md` is canonical** for v7.0.47+.
- `docs/00-overview/LIBRARIAN_AUDIT_v7.0.9.md` — historical only.
- `docs/11-reference/archive/*` — v5/v6 snapshots; do not update for routine releases.

---

## Status

Documentation consistent with v7.0.51 Standard Map shell, peer-link finalize, and offline EXE naming.
