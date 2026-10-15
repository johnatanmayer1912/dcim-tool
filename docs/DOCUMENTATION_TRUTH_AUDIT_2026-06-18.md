# Documentation truth audit — 2026-06-18

| Field | Value |
|-------|-------|
| **Application Version** | **7.0.51** |
| **Auditor** | R-LIB (FULL_DOCS_SYNC) |
| **Trigger** | Standard Map v7.0.51 ship + user docs sync request |

---

## Ground truth

```
/VERSION                    → 7.0.51
/CHANGELOG.md               → [v7.0.51] … [v7.0.49] Standard Map redesign
dist/                       → NetworkSwissToolPro_v7.0.51_OFFLINE.exe
NetworkSwissToolPro_v7.0.51.spec
utils/standard_map_shell.py → Standard Map shell (new v7.0.49+)
modules/adapters.py         → _finalize_standard_map_edges (v7.0.51)
tests/test_standard_map_v7049.py
```

---

## Hub sync status

| Document | Version line | Status |
|----------|--------------|--------|
| `docs/README.md` | 7.0.51 | synced |
| `DOCUMENTATION_MASTER_INDEX.md` | 7.0.51 | synced |
| `DOCS_CANONICAL_MAP.md` | 7.0.51 | synced |
| `00-overview/project-overview.md` | 7.0.51 | synced |
| `00-overview/walkthrough.md` | 7.0.51 | synced |
| `07-operations/README.md` | 7.0.51 | synced |
| `10-rebuild/README.md` | 7.0.51 spec | synced |
| `09-qa/README.md` | 7.0.51 | synced |

---

## Feature documentation

| Feature | Canonical doc | Code anchor |
|---------|---------------|-------------|
| Standard L2 Map shell | `06-ui-ux/standard-map-shell.md` | `standard_map_shell.py` |
| Visualization pipeline | `01-architecture/visualization-pipeline.md` | `report_formatter.py` |
| Utilities | `02-codebase/UTILITIES_DOCUMENTATION.md` | `utils/*` |
| Topology troubleshooting | `07-operations/TOPOLOGY_ISSUES.md` | — |
| Release | `20-release-management/RELEASE_NOTES_7.0.51.md` | `/CHANGELOG.md` |

---

## Intentional non-sync (archive)

- Per-version bug sweep reports under `13-bug-reports/` — point-in-time; not rewritten each release.
- `docs/20-release-management/CHANGELOG.md` — legacy partial copy; use root changelog for 7.0.47+.
- Platform prompt archives under `12-master-prompts/archive/`.

---

## Validation commands

```powershell
python -m pytest tests/test_standard_map_v7049.py -q
python _prebuild.py
python scripts/validate_docs_links.py
```

---

## Sign-off

Docs folder reflects v7.0.51 Standard Map UX, peer-link behavior, and current EXE/spec naming. See [LIBRARIAN_AUDIT_v7.0.51.md](00-overview/LIBRARIAN_AUDIT_v7.0.51.md).
