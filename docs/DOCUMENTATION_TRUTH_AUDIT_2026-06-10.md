# Documentation Truth Audit — 2026-06-10

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Application Version** | **7.0.29** |
| **Roles** | R-LIB, R-GOV-LIB, R-ARCH, R-RECON, R-QA |
| **Verdict** | **PASS with tracked debt** |

---

## Executive summary

The `docs/` folder is now a **coherent knowledge system** with a single command hub, disaster-recovery roadmap, canonical path map, and automated link validation. **Critical truth documents** align with `VERSION` 7.0.29. Remaining issues are **legacy archive files** (v5/v6 layouts) explicitly marked — not silent drift.

---

## Truth chain (source of runtime reality)

```
/VERSION (7.0.29)
    ↓
CHANGELOG.md
    ↓
docs/README.md · CODE_INVENTORY.md · API_DOCUMENTATION.md (header)
    ↓
14-roadmap/SYNC_PROTOCOL.md (code → doc mapping)
    ↓
P01–P42 reconstruction prompts
```

**AI entry:** `12-master-prompts/PROMPT_COMMAND_CENTER.md` → `INDEX_PROMPT.md` → roles

---

## Audit gates

| Gate | Result | Evidence |
|------|--------|----------|
| VERSION parity (hub docs) | **PASS** | `docs/README.md`, `project-overview.md`, plugin READMEs, reconstruction index |
| Governance sync | **PASS** | G-18 rules 21–24, PROC-CCDU, mandatory sync footer |
| Command center registered | **PASS** | G-CC in `PROMPT_REGISTRY.md` Quick Index |
| QA path canonical | **PASS** | `09-qa/` + `08-qa/README.md` redirect stub |
| Ops path canonical | **PASS** | `07-operations/` + `08-operations/README.md` redirect |
| Rebuild DR package | **PASS** | README + DISASTER_RECOVERY_COMMAND + SYNC_PROTOCOL |
| pytest / prebuild (code truth) | **PASS** | 146/146 pytest; `_prebuild.py` PASS |
| Internal link scan | **IMPROVED** | 83 → **~58** broken (see below); validator added |

---

## Fixes applied (this audit)

| Category | Action |
|----------|--------|
| **Paths** | `08-qa` → `09-qa` across governance, ops, registry |
| **Paths** | `08-operations` links → `07-operations` in walkthrough, architecture |
| **Paths** | `03-automation`/`04-plugins` → `03-infrastructure`/`04-automation`/`05-plugins` in hub README |
| **Redirects** | Created `08-qa/README.md`, `07-operations/README.md`, `09-qa/README.md` |
| **Stale versions** | API header, interface_manager, network_discovery, network-search-workflow |
| **Hub rewrite** | `project-overview.md`, `walkthrough.md` — v7.0.29 canonical links |
| **Archive banners** | `system-architecture-deep-dive.md`, `production-guidelines.md` |
| **Rebuild pointer** | `10-rebuild/README.md`, `exact-rebuild-procedure.md` → `14-roadmap` |
| **Registry** | App sync 7.0.29; G-CC; D-SEARCH/D-QA-VPC paths |
| **Tooling** | `scripts/validate_docs_links.py` |

---

## Remaining link debt (acceptable / tracked)

Run: `python scripts/validate_docs_links.py`

| Bucket | Count (approx.) | Mitigation |
|--------|-----------------|------------|
| Legacy v5 `prompts/P0x` in `10-rebuild/exact-rebuild-procedure.md` | ~11 | Superseded by `14-roadmap/`; banner added |
| `TS_ERROR_INDEX.md` child topic files (never created) | ~12 | Index body still usable; split docs optional |
| `production-guidelines.md` v5 paths | ~10 | Archive banner; use `07-operations/README.md` |
| `file://` external paths in deep-dive | ~10 | Archive banner |
| Plugin guide relative CHANGELOG links | ~4 | Point to repo root in future pass |
| Missing `qa-strategy.md`, `plugin-architecture.md` | few | Create or redirect in T-003 |

**Policy:** Legacy files keep archive banners; do not delete history.

---

## Canonical folder truth (filesystem)

| Folder | Role |
|--------|------|
| `00-overview/` | Strategy, walkthrough, mandate |
| `01-architecture/` | MODULE_ARCHITECTURE, system design |
| `02-codebase/` | CODE_INVENTORY, API, utilities |
| `03-infrastructure/` | Parsing workflows |
| `04-automation/` | Plugin dev guides |
| `05-plugins/` | Per-plugin docs |
| `08-operations/` | **Canonical ops** |
| `09-qa/` | **Canonical QA** |
| `10-rebuild/` | Build/install (day-to-day) |
| `20-release-management/` | Release notes |
| `12-master-prompts/` | Governance + G-CC |
| `13-bug-reports/` | Bug sweep |
| `14-roadmap/` | **Disaster recovery** |
| `17-roles-by-command/` | Command cheat sheet |

See [`DOCS_CANONICAL_MAP.md`](DOCS_CANONICAL_MAP.md)

---

## Cross-reference matrix (documents know each other)

| From | Must reference |
|------|----------------|
| `docs/README.md` | G-CC, 15-rebuild, MASTER_INDEX, CANONICAL_MAP |
| `PROMPT_COMMAND_CENTER` | SYNC_PROTOCOL, PROC-CCDU, roles, 15-rebuild |
| `INDEX_PROMPT` | G-CC (step 2), 15-rebuild |
| `SYNC_PROTOCOL` | CODE_INVENTORY, UTILITIES, plugin READMEs, P-prompts |
| `project-overview` | All role entry paths |
| Plugin READMEs | `05-plugins/`, CHANGELOG, ops guides |

---

## Ongoing maintenance (hardcoded)

1. **Every code change** → `SYNC_PROTOCOL.md` row + ongoing docs (G-18 rule 21)
2. **Every release** → VERSION, CHANGELOG, release notes, `docs/README.md`, reconstruction index
3. **Weekly** → `python scripts/validate_docs_links.py` (target: &lt;30 legacy-only breaks)
4. **Monthly** → R-RECON spot-check one rebuild batch

---

## Sign-off

| Role | Verdict |
|------|---------|
| R-LIB | Truth hub synced to 7.0.29 |
| R-GOV-LIB | G-CC integrated; registry updated |
| R-ARCH | MODULE_ARCHITECTURE ↔ CODE_INVENTORY aligned |
| R-RECON | 14-roadmap operational |
| R-QA | Gates documented in 09-qa/README |

**Next audit:** After next `VERSION` bump or major feature.
