# Network Swiss Tool Pro — Documentation Hub

| Field | Value |
|-------|-------|
| **Purpose** | Central entry for all operational, technical, governance, and disaster-recovery knowledge |
| **Version Awareness** | **v7.0.51** (sync with `/VERSION`) |
| **Last Updated** | 2026-06-18 |
| **Owner** | R-LIB + R-GOV-LIB |

---

## Start here

| I want to… | Go to |
|------------|-------|
| Run AI commands (fix, release, review) | [**COMMAND_MANUAL.html**](16-roles-by-command/COMMAND_MANUAL.html) (offline) · [PROMPT_COMMAND_CENTER](12-master-prompts/PROMPT_COMMAND_CENTER.md) |
| Mandatory read order for AI | [`12-master-prompts/INDEX_PROMPT.md`](12-master-prompts/INDEX_PROMPT.md) |
| Navigate all docs | [`DOCUMENTATION_MASTER_INDEX.md`](DOCUMENTATION_MASTER_INDEX.md) |
| Understand folder layout | [`DOCS_CANONICAL_MAP.md`](DOCS_CANONICAL_MAP.md) |
| **Rebuild app from docs only** | [`14-roadmap/README.md`](14-roadmap/README.md) |
| Bug sweep output | [`13-bug-reports/`](13-bug-reports/) |

---

## Documentation hierarchy

### Governance & commands
- **[12-master-prompts/](12-master-prompts/)** — Policies G-00–G-18, council roles, action logs
  - **[PROMPT_COMMAND_CENTER.md](12-master-prompts/PROMPT_COMMAND_CENTER.md)** — All-in-one commands
  - **[INDEX_PROMPT.md](12-master-prompts/INDEX_PROMPT.md)** — Mandatory read order
- **[16-roles-by-command/](16-roles-by-command/)** — Slash-command reference

### Disaster recovery (“docs folder only”)
- **[14-roadmap/](14-roadmap/)** — 42-step 1:1 reconstruction (P01–P42)
  - [DISASTER_RECOVERY_COMMAND.md](14-roadmap/DISASTER_RECOVERY_COMMAND.md) — Batch copy-paste (DDOS-safe)
  - [SYNC_PROTOCOL.md](14-roadmap/SYNC_PROTOCOL.md) — Code → doc/prompt map (**update on every code change**)

### Architecture & code truth
- **[01-architecture/](01-architecture/)** — `MODULE_ARCHITECTURE.md`, system design
- **[02-codebase/](02-codebase/)** — `CODE_INVENTORY.md`, `API_DOCUMENTATION.md`, `UTILITIES_DOCUMENTATION.md`
- **[03-infrastructure/](03-infrastructure/)** — Infrastructure & parsing workflows
- **[04-automation/](04-automation/)** — Plugin development guides & parsing
- **[05-plugins/](05-plugins/)** — Per-plugin READMEs (interface_manager, network_discovery, …)

### Operations & QA
- **[08-operations/](08-operations/)** — Runbooks (MAC trace, discovery command center, EXE smoke)
- **[07-operations/](07-operations/)** — Legacy troubleshooting index (see canonical map)
- **[09-qa/](09-qa/)** — QA suites, production readiness

### Release & bugs
- **[20-release-management/](20-release-management/)** — Release notes per version
- **[13-bug-reports/](13-bug-reports/)** — Sweep reports, prioritized list, fix prompts
- **Root:** `/CHANGELOG.md`, `/VERSION`

### Maintenance
- **[DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md)** — Standards & workflows
- **[12-master-prompts/CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md](12-master-prompts/CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md)** — PROC-CCDU

---

## Validation

- **Truth audit:** [DOCUMENTATION_TRUTH_AUDIT_2026-06-18.md](DOCUMENTATION_TRUTH_AUDIT_2026-06-18.md)
- **Link checker:** `python scripts/validate_docs_links.py` (from repo root)

---

## Hardcoded documentation sync

**Every code change** must update ongoing docs **and** `14-roadmap/` per `SYNC_PROTOCOL.md` — integrated into `PROMPT_COMMAND_CENTER.md` and G-18 rules 21–24. This does **not** require a separate “doc sync” command.

---

## Overview
- [Project Overview](00-overview/project-overview.md)
- [LIBRARIAN Mandate](00-overview/LIBRARIAN_MANDATE.md)
- [Walkthrough](00-overview/walkthrough.md)

---

*Maintained by R-LIB · Prompt governance by R-GOV-LIB · Rebuild roadmap by R-RECON*
