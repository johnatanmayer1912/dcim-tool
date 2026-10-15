# CHANGE_MANAGEMENT_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-08 |
| **last_updated** | 2026-05-31 |

**Related:** `PROMPT_EXECUTION_RULES.md` (G-15) · `QUALITY_GATE_POLICY.md` (G-07) · `DOCUMENTATION_POLICY.md` (G-06) · `RELEASE_MANAGEMENT_POLICY.md` (G-09)

## Purpose

Define the mandatory lifecycle for any modification.

---

## Lifecycle

Every significant change MUST progress through these phases. Do not skip phases.

| Phase | Name | Primary owner | Activities |
|-------|------|---------------|------------|
| 1 | **Problem** | Product Strategist / requester | State issue, user impact, success criteria |
| 2 | **Analysis** | System Architect + Lead Developer | Root cause, scope, dependencies, risks |
| 3 | **Design** | System Architect | Boundaries, contracts, rollback approach |
| 4 | **Implementation** | Lead Developer | Minimal scoped code/config changes |
| 5 | **Validation** | QA Engineer (+ domain gates) | Tests, smoke, `QUALITY_GATE_POLICY.md` |
| 6 | **Documentation** | Documentation Steward | `CHANGELOG`, `docs/`, usage guides |
| 7 | **Release Notes** | Release Manager + Documentation Steward | `VERSION`, release entry, dist notes |
| 8 | **Approval** | Release Manager / Team Meeting Council | Gate sign-off, ship or hold |

**RESYNC** runs before phase 1 when context may be stale (`U-RESYNC`).

Prompt-only changes: phases 1–2 may be brief; phases 6–8 include registry + `PROMPT_GOVERNANCE_POLICY.md` workflow.

---

## Rules

1. **No undocumented changes are permitted.**
2. **No implementation may begin** before the problem and analysis are clear (phases 1–2).
3. **No release may occur** without validation and documentation (phases 5–6 minimum).
4. Every change must state the **expected outcome** and **rollback path**.
5. Every change must identify **owners** and **dependencies** (registry, modules, roles).
6. Every change must **preserve or improve quality** unless explicitly justified and logged (Team Meeting if waiver).

### Engineering principles (this repository)

- Minimal scope diffs; match existing conventions.
- Backward compatibility for plugin IDs and saved inventories unless **major** version.
- No destructive git without explicit user request.
- Never commit secrets (`.env`, device passwords, live credentialed inventories).

---

## Change classes

| Class | Examples | Lifecycle depth | Approval |
|-------|----------|-----------------|----------|
| **Patch** | Bug fix, parser tweak | Full 1–8; abbreviated design if trivial | U-ENG + U-QA gates |
| **Minor** | New plugin, new tab, feature | Full 1–8 | U-ARCH review + U-QA + U-LIB |
| **Major** | Breaking API, credential model | Full 1–8 + Compatibility gate | User + U-COUNCIL note |

---

## Required artifacts

Each change MUST produce or update:

| Artifact | Phase | Typical location |
|----------|-------|------------------|
| **change summary** | 1–2 | Action log, task description |
| **risk assessment** | 2–3 | Action log, design note |
| **implementation notes** | 4 | PR-style summary, handoff to U-LIB |
| **test/validation notes** | 5 | QA log, commands run (`_prebuild`, VPC tests) |
| **documentation updates** | 6 | `docs/`, `CHANGELOG.md` |
| **release notes** | 7 | `CHANGELOG.md` top entry, `VERSION` |
| **approval record** | 8 | Quality-gate log, Team Meeting entry if needed |
| **rollback guidance** | 3, 7 | CHANGELOG, release manager notes |

---

## Prompt changes

Follow `PROMPT_GOVERNANCE_POLICY.md` (G-03): archive → enhance → registry → usage guide → documentation action log.

---

## Required change-management action log

Record in `action-logs/YYYY-MM-DD_<slug>.md` for non-trivial changes:

| Field | Content |
|-------|---------|
| **change phase completed** | Highest lifecycle phase finished (1–8) |
| **current state** | In progress / blocked / ready for release |
| **blockers** | Gates failed, dependencies, conflicts |
| **next step** | Owner and phase to execute next |

Include expected outcome and rollback path in the same log or linked design section.

Combine with G-07 quality-gate fields and G-06 documentation fields when those policies apply.

Template: `roles/_ACTION_LOG_SNIPPET.md`

---

## Escalation

- Architecture boundary disputes → `ESCALATION_MATRIX.md` (Architect row).
- Skipping lifecycle phase or gate → Team Meeting Council (U-COUNCIL).
- Security-sensitive change → U-SEC before phase 8 approval.

---

## Success criteria

- [ ] Phases 1–2 complete before code merge
- [ ] All required artifacts present for change class
- [ ] Validation and documentation complete before release
- [ ] Change-management action log fields filled
- [ ] Rollback path documented when risk ≥ medium

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set).
