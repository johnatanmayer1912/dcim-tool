# FULL_DOCS_SYNC

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Registry ID** | W-DOC-SYNC |
| **Trigger** | `full docs sync` · `/full-docs-sync` · `sync all documentation` |
| **Owner** | R-LIB + R-GOV-LIB + R-RECON |
| **last_updated** | 2026-06-10 |

**Invoke:** Say **`full docs sync`** or paste this file.

---

## Mission

Achieve **complete documentation parity** with code, prompts, and `VERSION` in one coordinated pass. Update ongoing docs, governance hub, rebuild roadmap, cross-references, and validation evidence.

---

## Roles (all mandatory)

| Order | Role | Focus |
|-------|------|-------|
| 1 | RESYNC | INDEX, REGISTRY, VERSION, CHANGELOG |
| 2 | R-GOV-LIB | PROMPT_REGISTRY, combined roles, G-CC |
| 3 | R-LIB | All `docs/` truth docs, plugin READMEs, ops guides |
| 4 | R-RECON | `15-rebuild-roadmap/SYNC_PROTOCOL.md` + affected P-prompts |
| 5 | R-ARCH | MODULE_ARCHITECTURE, design doc accuracy |
| 6 | R-QA | Test/prebuild evidence in action log |
| 7 | R-REL | Release notes alignment if VERSION changed |

---

## Execution sequence

### Phase 1 — Inventory (R-GOV-LIB + R-LIB)

1. Read `/VERSION`, `/CHANGELOG.md`, `docs/README.md`
2. Run `python scripts/validate_docs_links.py` — record broken count
3. Diff hot paths: `modules/`, `utils/`, `vlan_checker_web.py`, `modules/web/templates/index.html`
4. List drift vs `CODE_INVENTORY.md`, `API_DOCUMENTATION.md`, `UTILITIES_DOCUMENTATION.md`

### Phase 2 — Sync ongoing docs (R-LIB)

Update every affected file per `CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md` (PROC-CCDU):

| Area | Paths |
|------|-------|
| Hub | `docs/README.md`, `DOCUMENTATION_MASTER_INDEX.md`, `DOCS_CANONICAL_MAP.md` |
| Code truth | `02-codebase/CODE_INVENTORY.md`, `API_DOCUMENTATION.md`, `UTILITIES_DOCUMENTATION.md` |
| Architecture | `01-architecture/MODULE_ARCHITECTURE.md` |
| Plugins | `05-plugins/*/README.md` |
| Operations | `08-operations/*.md` (version lines, EXE smoke) |
| QA | `09-qa/README.md` |
| Release | `11-release-management/RELEASE_NOTES_*.md` if needed |
| Bug registry | `14-bug-reports/00-executive-summary.md`, `01-prioritized-bug-list.md` |

### Phase 3 — Rebuild roadmap (R-RECON)

1. Apply `15-rebuild-roadmap/SYNC_PROTOCOL.md` matrix for all changed modules
2. Bump `00-RECONSTRUCTION_INDEX.md` Application Version
3. Update phase `00-PROMPT-INDEX.md` if prompts touched

### Phase 4 — Governance (R-GOV-LIB)

1. `PROMPT_REGISTRY.md` application sync line = `VERSION`
2. `INDEX_PROMPT.md` / `PROMPT_COMMAND_CENTER.md` cross-refs valid
3. Action log: `action-logs/YYYY-MM-DD_full-docs-sync.md`

### Phase 5 — Validate (R-QA)

1. `python -m pytest tests/ -q` (record pass count)
2. `python _prebuild.py` (record PASS/FAIL)
3. Re-run `validate_docs_links.py` — compare to Phase 1

---

## Deliverables

| Artifact | Location |
|----------|----------|
| Sync report | Action log + optional `DOCUMENTATION_TRUTH_AUDIT_*.md` section |
| Updated docs | All paths in Phase 2–3 |
| Link delta | Before/after broken link count |
| Gaps list | What still needs lab/SSH validation |

---

## Success criteria

- [ ] `docs/README.md` version = `/VERSION`
- [ ] CODE_INVENTORY header + new modules listed
- [ ] SYNC_PROTOCOL rows current
- [ ] PROMPT_REGISTRY application sync current
- [ ] Link validator improved or legacy-only debt documented
- [ ] Action log complete
