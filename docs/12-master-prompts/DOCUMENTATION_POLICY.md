# DOCUMENTATION_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-06 |
| **last_updated** | 2026-06-10 |

**Institutional authority:** `docs/00-overview/LIBRARIAN_MANDATE.md` (D-LIB)  
**Execution:** `PROMPT_EXECUTION_RULES.md` step 15 · **Role:** Documentation Steward (R-LIB / U-LIB)

## Purpose

Ensure every meaningful change is documented and traceable.

## Prime rule

**Nothing exists unless documented.** Implementation without docs is incomplete work.

**Hardcoded sync:** Documentation updates are **part of every code change**, not a separate user command. See `PROMPT_COMMAND_CENTER.md` (G-CC), `CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md` (PROC-CCDU), and `roles/_MANDATORY_SYNC_FOOTER.md`.

---

## Rebuild roadmap (disaster recovery)

| Rule | Detail |
|------|--------|
| Folder | `docs/15-rebuild-roadmap/` |
| Sync matrix | `SYNC_PROTOCOL.md` — update on every code touch |
| Batch rebuild | `DISASTER_RECOVERY_COMMAND.md` — max 4 prompts per IDE message |
| Owner | R-RECON (prompts) + R-LIB (ongoing docs) |
| Trigger | Same as rules 1–5 below — **every** code/architecture/release change |

---

## Rules

1. Every **code change** triggers documentation review.
2. Every **architecture change** triggers documentation review.
3. Every **prompt change** triggers documentation review.
4. Every **release** triggers documentation review.
5. Every **bug fix** triggers documentation review (when behavior or ops impact changes).
6. Every **new role or policy** triggers documentation review.
7. Documentation must describe **what** changed, **why** it changed, and **how to use** it.
8. Documentation must include **compatibility and rollback notes** when relevant.
9. Documentation must **preserve legacy intent** and historical meaning (forward sync, no silent erasure).

---

## Ownership

| Owner | Council role | Registry ID | Responsibility |
|-------|--------------|-------------|----------------|
| Documentation Steward | Documentation Steward | U-LIB | Accuracy, consistency, CHANGELOG, `docs/` parity |
| Prompt Librarian | Prompt Librarian | U-GOV-LIB | Prompt/registry/usage guide alignment |
| Architect | System Architect | U-ARCH | Design documentation, architecture docs |
| Lead Developer | Lead Developer | U-ENG | Implementation notes, inline clarity, handoff list |
| QA | QA Engineer | U-QA | Validation notes, test evidence in logs or QA docs |
| Release Manager | Release Manager | U-REL | Release notes, `VERSION`, rollout/rollback |

Documentation Steward has **final accountability** for doc/code parity; others supply inputs.

---

## Required updates by change type

| Change | Minimum documentation |
|--------|------------------------|
| User-facing feature | `CHANGELOG.md`, feature/ops doc under `docs/` |
| Parser / topology | `docs/03-automation/`, `docs/01-architecture/`, QA note if behavioral |
| Plugin | `docs/04-plugins/<name>.md`, plugin registry metadata |
| Release | `VERSION`, `CHANGELOG.md`, `docs/README.md` version awareness, dist README if packaged |
| Bug fix (behavioral) | `CHANGELOG.md` **Fixed** with root cause, impact, location |
| Governance / prompts | `PROMPT_REGISTRY.md`, usage guide, `action-logs/`, hub `CHANGELOG` doc section |
| New role or policy | Registry entry, usage guide (or draft row), INDEX/execution cross-refs if needed |
| Security / creds | Ops doc + no secrets in repo; review with U-SEC |

---

## Documentation locations

| Area | Path |
|------|------|
| Hub | `docs/README.md` |
| Master prompts | `docs/13-master-prompts/` |
| Overview / mandate | `docs/00-overview/` |
| Architecture | `docs/01-architecture/` |
| Plugins | `docs/04-plugins/` |
| Operations | `docs/08-operations/` (canonical; `07-operations/` = legacy redirect) |
| QA | `docs/09-qa/` |
| Disaster recovery | `docs/15-rebuild-roadmap/` |
| Commands | `docs/13-master-prompts/PROMPT_COMMAND_CENTER.md` |
| Release truth | `/CHANGELOG.md`, `/VERSION` |

---

## Style and quality

- Complete sentences; version and date on release entries (Keep a Changelog format).
- Prefer updating canonical docs over duplicating content across `dist_package_*` trees (source repo is truth).
- Code citations use path + line when pointing to implementation.
- Align with `ROLE_USAGE_STANDARD.md` (G-14) when updating usage guides.

---

## Required documentation action log

For every **documentation review** triggered by this policy, record in `action-logs/YYYY-MM-DD_<slug>.md` (or section within a task log):

| Field | Content |
|-------|---------|
| **docs reviewed** | Paths read for accuracy |
| **docs updated** | Paths written or materially edited |
| **gaps found** | Missing or stale documentation |
| **risks noted** | Drift, wrong version, missing rollback |
| **remaining work** | Follow-up doc tasks |

Also include G-14 standard output when Documentation Steward was active: findings, recommendations, decisions, risks.

Template: `roles/_ACTION_LOG_SNIPPET.md` · Steward guide: `roles/DOCUMENTATION_STEWARD_USAGE.md`

---

## Gates and escalation

- **Documentation Review** gate (`QUALITY_GATE_POLICY.md`) — required for meaningful changes before release.
- Doc/code mismatch → `ESCALATION_MATRIX.md` row **Documentation gap** (U-LIB → U-ENG → Team Meeting).
- Prompt drift → U-GOV-LIB + U-LIB per escalation matrix.

---

## Success criteria

- [ ] What / why / how documented for the change
- [ ] CHANGELOG updated when user-visible or version shipped
- [ ] Compatibility/rollback noted when applicable
- [ ] Legacy intent preserved in prompt/governance edits
- [ ] Documentation action log fields completed

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set).
