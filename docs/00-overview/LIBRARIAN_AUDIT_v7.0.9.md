# LIBRARIAN audit — v7.0.9 (2026-05-31)

| Field | Value |
|-------|-------|
| **Role** | PROMPT LIBRARIAN (R-GOV-LIB) |
| **Scope** | Documentation alignment + release v7.0.9 |
| **VERSION file** | 7.0.9 |
| **Artifact** | `NetworkSwissToolPro_v7.0.9_OFFLINE.exe` |

## Resync performed

1. Read `CHANGELOG.md`, `VERSION`, `vlan_checker_web.py` (`UPDATE_DATE`, template vars).
2. Renamed user-facing tab docs: **Network Search** (`network-search-*.md`); stubs left at `search-it-*.md`.
3. Updated `mac-trace-howto.md`, root `CHANGELOG.md`, `RELEASE_NOTES_7.0.9.md`.
4. UI mockups retained under `docs/ui-mockups/` (approval trail).

## Version alignment checklist

| Source | Version / label | Status |
|--------|-----------------|--------|
| `VERSION` | 7.0.9 | OK |
| `vlan_checker_web.py` | reads VERSION | OK |
| `index.html` sidebar `{{ version }}` | from template | OK |
| `CHANGELOG.md` [v7.0.9] | present | OK |
| `RELEASE_NOTES_7.0.9.md` | present | OK |
| Network Search tab label | UI | OK |
| API `/api/search-it/*` | unchanged (compat) | OK |

## Known doc path notes

- `docs/README.md` hierarchy lists canonical `07-operations/` paths; live ops docs are under **`docs/07-operations/`** — see network-search guides there.
- `PROMPT_REGISTRY.md` may still reference `search-it-workflow`; canonical file is `docs/07-operations/network-search-workflow.md`.

## Gaps / follow-up (non-blocking)

- Update `docs/README.md` Version Awareness footer to v7.0.9 when steward runs full index pass.
- Optional: add `date_display` to `/api/version` JSON for clients.

## Sign-off

Documentation consistent with v7.0.9 shipping UI and EXE naming. Redirect stubs prevent broken links from older bookmarks.
