# Docs Folder — Canonical Map

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | R-LIB + R-GOV-LIB |
| **Last Updated** | 2026-06-18 |
| **Application Version** | 7.0.51 |

## Purpose

One page explaining **which folders matter**, what is canonical vs legacy overlap, and what **not** to duplicate. Use when cleaning or onboarding.

---

## Canonical folders (keep & maintain)

| Folder | Purpose | Canonical for |
|--------|---------|---------------|
| `00-overview/` | Mission, mandate, walkthrough | Project introduction |
| `01-architecture/` | System/module design | `MODULE_ARCHITECTURE.md` |
| `02-codebase/` | Code inventory, API, utilities | Technical truth |
| `03-infrastructure/` | Parsing / infra workflows | Device automation infra |
| `04-automation/` | Plugin development guides | plugin-development-template.md |
| `05-plugins/` | Per-plugin feature docs | interface_manager, network_discovery, … |
| `09-qa/` | QA & production readiness | Test gates |
| `07-operations/` | **Primary** runbooks & how-tos | MAC trace, EXE smoke, command centers |
| `08-security/` | Security documentation | Auth, authz, threat model |
| `10-rebuild/` | Build process, installation, recovery | Build how-to |
| `11-reference/` | Reference materials, archives | Reference only |
| `12-master-prompts/` | AI governance hub | **PROMPT_COMMAND_CENTER**, roles, policies |
| `13-bug-reports/` | Bug sweep & fix prompts | W-BUG-SWEEP-* |
| `14-roadmap/` | **Disaster recovery** | P01–P42 reconstruction |
| `15-visual-guide/` | Visual guide for reconstruction | Visual documentation |
| `16-roles-by-command/` | Slash-command reference | User command cheat sheet |
| `17-ongoing-tasks/` | T-001–T-005 task prompts | Recurring workflows |
| `18-interface-management/` | Interface management | Interface feature docs |
| `19-recovery/` | Recovery procedures | Disaster recovery |
| `20-release-management/` | Per-version release notes | Ship history |
| `21-utilization-overlay/` | L2 utilization paint contract (spec; not shipping) | Overlay is not topology |

### Root-level docs (canonical)
- `DOCUMENTATION_MASTER_INDEX.md` — Navigation index
- `DOCUMENTATION_MAINTENANCE_GUIDE.md` — Maintenance standards
- `DOCS_CANONICAL_MAP.md` — This file
- `README.md` — Docs hub entry

---

## Legacy / overlap (do not delete — redirect mentally)

| Path | Status | Use instead |
|------|--------|-------------|
| `06-ui-ux/` vs `05-ui-ux/` in old indexes | Naming drift | UI docs: check `DOCUMENTATION_MASTER_INDEX` |
| `09-release-notes/` in old README | Superseded | `20-release-management/` + root `CHANGELOG.md` |
| `10-rebuild/` vs `14-roadmap/` | Partial overlap | **Disaster recovery → `14-roadmap/`**; build how-to may stay in `10-rebuild/` or `BUILD_GUIDE.md` |
| `00-overview/LIBRARIAN_AUDIT_v7.0.9.md` | Archive | Historical only |
| `11-reference/` | Archive materials | Reference only |

**Rule:** Do not create a third copy of the same content. Update canonical path; add one-line redirect in legacy file if needed.

---

## What we do NOT need (avoid creating)

- Duplicate release notes outside `20-release-management/` and `CHANGELOG.md`
- Second prompt registry outside `12-master-prompts/PROMPT_REGISTRY.md`
- Per-feature docs scattered in root `docs/plugins/` **and** `05-plugins/` — prefer `05-plugins/<name>/`
- Ad-hoc command lists outside `PROMPT_COMMAND_CENTER.md` and `FINAL_OPERATING_INSTRUCTION.md`

---

## Files required for 1:1 rebuild

Minimum set if code is lost:

1. `14-roadmap/` (all P-prompts + DISASTER_RECOVERY_COMMAND)
2. `02-codebase/CODE_INVENTORY.md`
3. `01-architecture/MODULE_ARCHITECTURE.md`
4. `02-codebase/API_DOCUMENTATION.md`
5. `CHANGELOG.md` + `VERSION` (if preserved separately)

---

## Cross-references

- Command center: `12-master-prompts/PROMPT_COMMAND_CENTER.md`
- Sync on code change: `14-roadmap/SYNC_PROTOCOL.md`
- Maintenance: `DOCUMENTATION_MAINTENANCE_GUIDE.md`
