# PROMPT_REGISTRY

| Field | Value |
|-------|-------|
| **Version** | 4.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-01 |
| **Council invoke** | `roles/combined/ROLE_*_USAGE_PROMPT.md` (canonical since 4.0.3) |
| **last_updated** | 2026-06-10 |
| **Application sync** | 7.0.29 (`VERSION`) |
| **Data release** | 4.0.3 (entries below; see [Registry Change Log](#registry-change-log)) |

---

## Purpose

Source of truth for `docs/13-master-prompts/`. Tracks **versions**, **ownership**, **status**, and **source linkage**.

Read **`INDEX_PROMPT.md`** first · Absolute rules: **`GLOBAL_MASTER_PROMPT_RULES.md`** (G-18).

---

## Required fields

Every registered entry **must** include:

- `prompt_id`
- `file_name`
- `version`
- `owner`
- `status`
- `type`
- `source_prompt`
- `purpose`
- `dependencies`
- `used_with`
- `last_updated`
- `notes`

---

## Status values

- `draft`
- `review`
- `approved`
- `active`
- `deprecated`
- `retired`

---

## Rules

- Every prompt file must be registered
- Council roles: one **combined** entry per role (`roles/combined/ROLE_*_USAGE_PROMPT.md`); separate split R/U files are retired (4.0.3)
- Domain usage guides (`RESYNC_USAGE.md`, etc.) remain separate and must be registered
- Every version change must be recorded
- Every enhanced prompt must reference original source
- Every deprecated prompt must remain traceable
- No prompt introduced without registry entry
- No prompt changed without updating registry

---

## Versioning

- **Major:** structure, responsibility, or behavior changes
- **Minor:** expanded scope or important clarification
- **Patch:** wording or formatting only

---

## Sync policy

- Keep source prompts intact (`docs/02-codebase/PLATFORM_PROMPTS/`)
- Maintain master copies in `docs/13-master-prompts/`
- When source changes, reflect in master copy while preserving older versions
- Record both current and previous versions ([Registry Change Log](#registry-change-log))
- Do not lose legacy intent

Detail: `PROMPT_MIGRATION_SYNC.md` (G-16) · archive: `archive/platform-prompts-original/`

## Required Registry Workflow

1. Identify prompt or role.
2. Confirm source prompt.
3. Confirm version and owner.
4. Confirm related usage guide.
5. Confirm dependencies and policy coverage.
6. Update entry.
7. Validate index linkage (`INDEX_PROMPT.md` read order).
8. Log the change in `action-logs/`.

---

## Quick Index

| prompt_id | file_name | status | type |
|-----------|-----------|--------|------|
| G-CC | PROMPT_COMMAND_CENTER.md | active | command-hub |
| G-00 | INDEX_PROMPT.md | active | entry |
| G-01 | PROMPT_REGISTRY.md | active | registry |
| G-02 | PROMPT_USAGE_MANUAL.md | active | guide |
| G-03 | PROMPT_GOVERNANCE_POLICY.md | active | policy |
| G-04 | ROLE_MATRIX.md | active | matrix |
| G-05 | ESCALATION_MATRIX.md | active | matrix |
| G-06 | DOCUMENTATION_POLICY.md | active | policy |
| G-07 | QUALITY_GATE_POLICY.md | active | policy |
| G-08 | CHANGE_MANAGEMENT_POLICY.md | active | policy |
| G-09 | RELEASE_MANAGEMENT_POLICY.md | active | policy |
| G-10 | COMPETITIVE_ADVANTAGE_POLICY.md | active | policy |
| G-11 | TEAM_MEETING.md | active | escalation |
| G-12 | README.md | active | hub |
| G-13 | PROMPT_ACTIVATION_POLICY.md | active | policy |
| G-14 | ROLE_USAGE_STANDARD.md | active | standard |
| G-15 | PROMPT_EXECUTION_RULES.md | active | execution |
| G-16 | PROMPT_MIGRATION_SYNC.md | active | migration |
| G-17 | FINAL_OPERATING_INSTRUCTION.md | active | contract |
| G-18 | GLOBAL_MASTER_PROMPT_RULES.md | active | rules |
| W-BUG-SWEEP | roles/CHECK_SYSTEM_FOR_BUGS.md | active | workflow |
| W-DOC-SYNC | roles/FULL_DOCS_SYNC.md | active | workflow |
| W-BUG-FIX-ALL | roles/FIND_ALL_BUGS_AND_FIX.md | active | workflow |
| W-UI-UX | roles/UI_UX_AUDIT.md | active | workflow |
| W-NEXT-STEPS | roles/NEXT_STEPS_COUNCIL.md | active | workflow |
| EXT-00 | INDEX_PROMPT.md (root) | active | pointer |
| U-RESYNC | roles/RESYNC_USAGE.md | active | usage |
| U-TOPO | roles/TOPOLOGY_USAGE.md | active | usage |
| U-ORCH | roles/ORCHESTRATOR_USAGE.md | active | usage |
| U-UI | roles/UI_DYNAMO_USAGE.md | active | usage |
| R-GOV-LIB | roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md | active | role+usage |
| R-ARCH | roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md | active | role+usage |
| R-ENG | roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md | active | role+usage |
| R-QA | roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md | active | role+usage |
| R-SEC | roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md | active | role+usage |
| R-OBS | roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md | active | role+usage |
| R-LIB | roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md | active | role+usage |
| R-REL | roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md | active | role+usage |
| R-PROD | roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md | active | role+usage |
| R-COUNCIL | roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md | active | role+usage |
| U-STD | roles/_USAGE_GUIDE_STANDARD.md | active | meta |
| U-LOG-TPL | roles/_ACTION_LOG_SNIPPET.md | active | meta |
| U-CON | CONTRACT_USAGE.md | draft | usage |
| U-REG | REGISTRY_USAGE.md | draft | usage |
| U-LC | LIFECYCLE_USAGE.md | draft | usage |
| U-ALIGN | ALIGNMENT_USAGE.md | draft | usage |
| U-BAK | BACKUP_RECOVERY_USAGE.md | draft | usage |
| U-AI | AI_BEHAVIOR_USAGE.md | draft | usage |
| U-FND | FOUNDATION_USAGE.md | draft | usage |
| AL-README | action-logs/README.md | active | meta |
| AL-20260524 | 2026-05-24_governance-v3-scaffold.md | active | action-log |

Platform sources (Tier P): see [Platform Source Prompts](#platform-source-prompts).  
Archive copies (Tier A): see [Archive Copies](#archive-copies).

---

## Tier 0 — Governance & Hub (`docs/13-master-prompts/`)

### G-00 — INDEX_PROMPT

| Field | Value |
|-------|-------|
| **prompt_id** | G-00 |
| **file_name** | `INDEX_PROMPT.md` |
| **version** | 4.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | entry |
| **source_prompt** | `docs/13-master-prompts/INDEX_PROMPT.md` (authoritative); absolute rules in G-18 |
| **purpose** | Mandatory AI entry; read order; defers 20 rules + mission to G-18 |
| **dependencies** | G-18 |
| **used_with** | G-01, G-15, G-17, G-18; Phase A/B |
| **last_updated** | 2026-05-31 |
| **notes** | Root shortcut: `/INDEX_PROMPT.md` → this file |

### G-01 — PROMPT_REGISTRY

| Field | Value |
|-------|-------|
| **prompt_id** | G-01 |
| **file_name** | `PROMPT_REGISTRY.md` |
| **version** | 4.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | registry |
| **source_prompt** | `docs/13-master-prompts/PROMPT_REGISTRY.md` (authoritative) |
| **purpose** | Source of truth: versions, ownership, status, source linkage for master hub |
| **dependencies** | G-00, G-18 |
| **used_with** | G-02, G-03, U-GOV-LIB, all `action-logs/` |
| **last_updated** | 2026-05-31 |
| **notes** | Read-order alias `02_PROMPT_REGISTRY.md`; data release 3.1.33 in change log |

### G-02 — PROMPT_USAGE_MANUAL

| Field | Value |
|-------|-------|
| **prompt_id** | G-02 |
| **file_name** | `PROMPT_USAGE_MANUAL.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | guide |
| **source_prompt** | `docs/13-master-prompts/PROMPT_USAGE_MANUAL.md` (governance v3.0 spec) |
| **purpose** | Mandatory AI manual: global rules, council activation, workflows, gates, resync, success criteria |
| **dependencies** | G-00, G-01, G-04, G-05 |
| **used_with** | All `U-*` usage guides; `_USAGE_GUIDE_STANDARD.md` |
| **last_updated** | 2026-05-31 |
| **notes** | Council roles mapped in § Council Roles ↔ Project Prompts |

### G-03 — PROMPT_GOVERNANCE_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-03 |
| **file_name** | `PROMPT_GOVERNANCE_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/PROMPT_GOVERNANCE_POLICY.md` (governance v3.0 spec) |
| **purpose** | Ecosystem governance model: versioning, registry, usage guides, traceability, change/retirement review, governance action log |
| **dependencies** | G-00, G-01, G-14, G-15 |
| **used_with** | U-GOV-LIB, G-11, G-06, G-08, `PLATFORM_PROMPTS/` |
| **last_updated** | 2026-05-31 |
| **notes** | Precedence: INDEX → G-15 → policies → LIBRARIAN_MANDATE → PLATFORM_PROMPTS |

### G-04 — ROLE_MATRIX

| Field | Value |
|-------|-------|
| **prompt_id** | G-04 |
| **file_name** | `ROLE_MATRIX.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | matrix |
| **source_prompt** | `docs/13-master-prompts/ROLE_MATRIX.md` (governance v3.0 spec) |
| **purpose** | Ownership/coordination map: mission, domain, collaborators, reviews, escalation, output artifacts |
| **dependencies** | G-00, G-13, G-15 |
| **used_with** | All `U-*` guides, `P-*` roles, `PROMPT_ACTIVATION_POLICY.md` |
| **last_updated** | 2026-05-31 |
| **notes** | Matrix fields §; council + domain specialist tables; update on role change |

### G-05 — ESCALATION_MATRIX

| Field | Value |
|-------|-------|
| **prompt_id** | G-05 |
| **file_name** | `ESCALATION_MATRIX.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | matrix |
| **source_prompt** | `docs/13-master-prompts/ESCALATION_MATRIX.md` (governance v3.0 spec) |
| **purpose** | Issue-type escalation map: primary/secondary roles, blockers, Team Meeting, resolution requirements |
| **dependencies** | G-00, G-04, G-11 |
| **used_with** | U-COUNCIL, `TEAM_MEETING.md`, G-13 |
| **last_updated** | 2026-05-31 |
| **notes** | Retains L0–L4 severity; 10 issue-type rows + human escalation |

### G-06 — DOCUMENTATION_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-06 |
| **file_name** | `DOCUMENTATION_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/DOCUMENTATION_POLICY.md` (governance v3.0 spec) |
| **purpose** | Traceable documentation for all change types; ownership matrix; documentation action log fields |
| **dependencies** | G-00, G-15, D-LIB |
| **used_with** | U-LIB, U-GOV-LIB, U-ARCH, U-ENG, U-QA, U-REL, G-09 |
| **last_updated** | 2026-05-31 |
| **notes** | Prime rule + LIBRARIAN_MANDATE; step 15 G-15 |

### G-07 — QUALITY_GATE_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-07 |
| **file_name** | `QUALITY_GATE_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/QUALITY_GATE_POLICY.md` (governance v3.0 spec) |
| **purpose** | Mandatory review gates by risk profile; no bypass; quality-gate action log; project test hooks |
| **dependencies** | G-00, G-04, G-09 |
| **used_with** | U-QA, U-REL, U-ENG, U-ARCH, U-TOPO, U-SEC, U-OBS, U-ORCH, U-LIB |
| **last_updated** | 2026-05-31 |
| **notes** | 11 council gates + `_prebuild`, VPC validation, Jinja smoke |

### G-08 — CHANGE_MANAGEMENT_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-08 |
| **file_name** | `CHANGE_MANAGEMENT_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/CHANGE_MANAGEMENT_POLICY.md` (governance v3.0 spec) |
| **purpose** | 8-phase change lifecycle, required artifacts, change-management action log, change classes |
| **dependencies** | G-03, G-06, G-07, G-09, G-15 |
| **used_with** | U-ENG, U-ARCH, U-QA, U-LIB, U-REL, U-COUNCIL |
| **last_updated** | 2026-05-31 |
| **notes** | Maps phases to council roles; secrets and git safety retained |

### G-09 — RELEASE_MANAGEMENT_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-09 |
| **file_name** | `RELEASE_MANAGEMENT_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/RELEASE_MANAGEMENT_POLICY.md` (governance v3.0 spec) |
| **purpose** | Rollout control, required checks, rollback readiness, release action log, post-release visibility |
| **dependencies** | G-06, G-07, G-08, G-15 |
| **used_with** | U-REL, U-QA, U-SEC, U-OBS, U-LIB, U-ARCH, `VERSION`, `CHANGELOG.md` |
| **last_updated** | 2026-05-31 |
| **notes** | Update G-01 application sync on behavior change; EXE + dist_package workflow |

### G-10 — COMPETITIVE_ADVANTAGE_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-10 |
| **file_name** | `COMPETITIVE_ADVANTAGE_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/COMPETITIVE_ADVANTAGE_POLICY.md` (governance v3.0 spec) |
| **purpose** | Market positioning, review domains, strategic outputs, invest/avoid pillars for Network Swiss Tool Pro |
| **dependencies** | G-00, G-08 |
| **used_with** | U-PROD, U-ARCH, G-09, `docs/00-overview/` |
| **last_updated** | 2026-05-31 |
| **notes** | Six required outputs + strategic action log; Product Review gate |

### G-11 — TEAM_MEETING

| Field | Value |
|-------|-------|
| **prompt_id** | G-11 |
| **file_name** | `TEAM_MEETING.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | escalation |
| **source_prompt** | `docs/13-master-prompts/TEAM_MEETING.md` |
| **purpose** | Record and resolve prompt/policy conflicts (L2+) |
| **dependencies** | G-05 |
| **used_with** | R-COUNCIL, U-COUNCIL, G-03 conflict precedence |
| **last_updated** | 2026-05-31 |
| **notes** | Issue schema: `roles/TEAM_MEETING_COUNCIL.md` |

### G-12 — README (hub)

| Field | Value |
|-------|-------|
| **prompt_id** | G-12 |
| **file_name** | `README.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | hub |
| **source_prompt** | `docs/13-master-prompts/README.md` |
| **purpose** | Folder orientation and quick-start links |
| **dependencies** | G-00 |
| **used_with** | `docs/README.md` §13-Master-Prompts |
| **last_updated** | 2026-05-24 |
| **notes** | — |

### G-13 — PROMPT_ACTIVATION_POLICY

| Field | Value |
|-------|-------|
| **prompt_id** | G-13 |
| **file_name** | `PROMPT_ACTIVATION_POLICY.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | policy |
| **source_prompt** | `docs/13-master-prompts/PROMPT_ACTIVATION_POLICY.md` (governance v3.0 spec) |
| **purpose** | Mandatory automatic role activation, dependency chain, logging, enforcement |
| **dependencies** | G-00, G-02, G-04, G-05 |
| **used_with** | All `U-*` usage guides; `INDEX_PROMPT.md` §4; `G-15` step 4 |
| **last_updated** | 2026-05-31 |
| **notes** | Supersedes informal activation text only in usage manual |

### G-14 — ROLE_USAGE_STANDARD

| Field | Value |
|-------|-------|
| **prompt_id** | G-14 |
| **file_name** | `ROLE_USAGE_STANDARD.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | standard |
| **source_prompt** | `docs/13-master-prompts/ROLE_USAGE_STANDARD.md` (governance v3.0 spec) |
| **purpose** | Structure for role prompts (12 sections) and usage guides (7 sections); output format; new-role rules |
| **dependencies** | G-00, G-02, G-03 |
| **used_with** | `U-STD`, `U-LOG-TPL`, all `roles/*_USAGE.md`; `INDEX_PROMPT.md` §5; `G-15` step 5 |
| **last_updated** | 2026-05-31 |
| **notes** | `_USAGE_GUIDE_STANDARD.md` is implementation template |

### G-15 — PROMPT_EXECUTION_RULES

| Field | Value |
|-------|-------|
| **prompt_id** | G-15 |
| **file_name** | `PROMPT_EXECUTION_RULES.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | execution |
| **source_prompt** | `docs/13-master-prompts/PROMPT_EXECUTION_RULES.md` (governance v3.0 spec) |
| **purpose** | Mandatory read/execute sequence (Phase A 12 + Phase B 5); G-18 at step 3; G-17 at step 8 |
| **dependencies** | G-00, G-01, G-02, G-13, G-14 |
| **used_with** | `INDEX_PROMPT.md`, G-17; Phase B §12–16 |
| **last_updated** | 2026-05-31 |
| **notes** | Authoritative orchestration for Phase A read + Phase B execute |

### G-16 — PROMPT_MIGRATION_SYNC

| Field | Value |
|-------|-------|
| **prompt_id** | G-16 |
| **file_name** | `PROMPT_MIGRATION_SYNC.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | migration |
| **source_prompt** | `docs/13-master-prompts/PROMPT_MIGRATION_SYNC.md` (governance v3.0 spec) |
| **purpose** | Migrate/sync prompts without history loss; 10-step migration; sync versioning; six output requirements |
| **dependencies** | G-03, G-01, G-14 |
| **used_with** | U-GOV-LIB, `archive/platform-prompts-original/`, `PLATFORM_PROMPTS/` |
| **last_updated** | 2026-05-31 |
| **notes** | Implements G-03 archive-first rules; read with governance before prompt changes |

### G-17 — FINAL OPERATING INSTRUCTION

| Field | Value |
|-------|-------|
| **prompt_id** | G-17 |
| **file_name** | `FINAL_OPERATING_INSTRUCTION.md` |
| **version** | 4.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | contract |
| **source_prompt** | `docs/13-master-prompts/FINAL_OPERATING_INSTRUCTION.md` (authoritative) |
| **purpose** | Operational IDE contract; simple user commands; auto-activation; continuous development UX |
| **dependencies** | G-00, G-01, G-18, G-13, G-15, G-16, W-BUG-SWEEP |
| **used_with** | All council R-* / U-*; G-03–G-11; INDEX step 8; `docs/14-bug-reports/` |
| **last_updated** | 2026-05-31 |
| **notes** | Simple commands table; absolutes in G-18 |

### G-18 — GLOBAL MASTER PROMPT RULES

| Field | Value |
|-------|-------|
| **prompt_id** | G-18 |
| **file_name** | `GLOBAL_MASTER_PROMPT_RULES.md` |
| **version** | 4.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | rules |
| **source_prompt** | `docs/13-master-prompts/GLOBAL_MASTER_PROMPT_RULES.md` (authoritative) |
| **purpose** | 20 absolute rules; mission; vision; engineering principles; hub v4.0 binding |
| **dependencies** | G-00, G-01 |
| **used_with** | G-15, G-17, all R-* / U-*; INDEX step 3 |
| **last_updated** | 2026-05-31 |
| **notes** | Precedence #1 in G-03 |

### W-BUG-SWEEP — CHECK SYSTEM FOR BUGS

| Field | Value |
|-------|-------|
| **prompt_id** | W-BUG-SWEEP |
| **file_name** | `roles/CHECK_SYSTEM_FOR_BUGS.md` |
| **version** | 4.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | workflow |
| **source_prompt** | `docs/13-master-prompts/roles/CHECK_SYSTEM_FOR_BUGS.md` |
| **purpose** | "check system for bugs"; all roles; docs/14-bug-reports/ artifacts |
| **dependencies** | G-00, G-01, G-07, G-11, G-18, all R-* |
| **used_with** | `docs/14-bug-reports/_SCAFFOLD/`, R-COUNCIL |
| **last_updated** | 2026-05-31 |
| **notes** | Run entire file in IDE; copy-paste fix/validation prompts per bug |

### EXT-00 — Root INDEX pointer

| Field | Value |
|-------|-------|
| **prompt_id** | EXT-00 |
| **file_name** | `INDEX_PROMPT.md` (repository root) |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | pointer |
| **source_prompt** | G-00 (`docs/13-master-prompts/INDEX_PROMPT.md`) |
| **purpose** | Discoverability shortcut to master hub |
| **dependencies** | G-00 |
| **used_with** | IDE / repo root open |
| **last_updated** | 2026-05-24 |
| **notes** | Not a duplicate of G-00 content |

---

## Tier R — Council roles (`docs/13-master-prompts/roles/combined/`)

Each council role is **one file**: Part 1 = master role (R-*), Part 2 = ROLE USAGE (legacy U-* IDs refer to Part 2 of the same file). Split `roles/<ROLE>.md` + `roles/*_USAGE.md` pairs were **retired** in data release **4.0.3**.

### R-GOV-LIB — PROMPT LIBRARIAN (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-GOV-LIB (usage: legacy U-GOV-LIB → Part 2) |
| **file_name** | `roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` |
| **version** | 3.1.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file (authoritative) |
| **purpose** | Prompt ecosystem, registry, migration, documentation audit; G-14 invoke in Part 2 |
| **dependencies** | G-00, G-01, G-03, G-16 |
| **used_with** | R-LIB, R-ARCH, R-ENG, R-QA, R-REL, R-COUNCIL |
| **last_updated** | 2026-06-02 |
| **notes** | G-11 Prompt Governance Officer = self + G-03; v3.1.0 added documentation audit responsibilities |

### R-ARCH — SYSTEM ARCHITECT (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-ARCH (usage: legacy U-ARCH → Part 2) |
| **file_name** | `roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Architecture, boundaries, migration; Architect Review gate |
| **dependencies** | G-00, G-01, G-08, G-07 |
| **used_with** | R-ENG, R-QA, R-SEC, R-OBS, R-REL, R-PROD, U-TOPO |
| **last_updated** | 2026-05-31 |
| **notes** | Advisory: P-FND, P-CON, P-ENG, P-ALIGN |

### R-ENG — LEAD DEVELOPER (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-ENG (usage: legacy U-ENG → Part 2) |
| **file_name** | `roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file; platform: `PLATFORM_PROMPTS/ENGINEER.md` (P-ENG) |
| **purpose** | Implement approved changes; minimal scope; verification |
| **dependencies** | G-00, G-01, G-07, G-08, R-ARCH |
| **used_with** | R-QA, R-SEC, R-OBS, R-LIB, R-REL, U-TOPO, U-ORCH, U-UI |
| **last_updated** | 2026-05-31 |
| **notes** | P-ENG remains platform source; archive before PLATFORM edits |

### R-QA — QA ENGINEER (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-QA (usage: legacy U-QA → Part 2) |
| **file_name** | `roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Verification, regression, release readiness; QA Review gate |
| **dependencies** | G-00, G-01, G-07 |
| **used_with** | R-ENG, R-ARCH, R-REL, R-SEC, U-TOPO |
| **last_updated** | 2026-05-31 |
| **notes** | G-07 quality-gate + project test hooks |

### R-SEC — SECURITY REVIEWER (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-SEC (usage: legacy U-SEC → Part 2) |
| **file_name** | `roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Trust boundaries, secrets, unsafe prompts; Security Review gate |
| **dependencies** | G-00, G-01, G-07, G-08 |
| **used_with** | R-ARCH, R-ENG, R-QA, R-REL, R-OBS, R-COUNCIL |
| **last_updated** | 2026-05-31 |
| **notes** | Invoke: trust/access/exposure/misuse; full path + prompt surface |

### R-OBS — OBSERVABILITY ENGINEER (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-OBS (usage: legacy U-OBS → Part 2) |
| **file_name** | `roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Telemetry, diagnostics; Observability Review gate |
| **dependencies** | G-00, G-01, G-07, G-09 |
| **used_with** | R-ENG, R-QA, R-REL, R-SEC, U-TOPO, R-COUNCIL |
| **last_updated** | 2026-05-31 |
| **notes** | Seen/measured/diagnosed; logs/metrics/traces together |

### R-LIB — DOCUMENTATION STEWARD (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-LIB (usage: legacy U-LIB → Part 2) |
| **file_name** | `roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Doc/code/prompt parity; Documentation Review gate |
| **dependencies** | G-00, G-01, G-06, D-LIB |
| **used_with** | R-GOV-LIB, R-ARCH, R-ENG, R-QA, R-REL, R-COUNCIL |
| **last_updated** | 2026-05-31 |
| **notes** | Truth for maintainers; why + compatibility |

### R-REL — RELEASE / CHANGE MANAGER (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-REL (usage: legacy U-REL → Part 2) |
| **file_name** | `roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Readiness, rollout, rollback; Release Review gate |
| **dependencies** | G-00, G-01, G-07, G-08, G-09 |
| **used_with** | R-QA, R-SEC, R-OBS, R-LIB, R-ARCH, R-ENG, R-COUNCIL |
| **last_updated** | 2026-05-31 |
| **notes** | Implementation→release; dependency chain; rollback first |

### R-PROD — PRODUCT / PLATFORM STRATEGIST (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-PROD (usage: legacy U-PROD → Part 2) |
| **file_name** | `roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Mission, advantage, prioritization; Product Review gate |
| **dependencies** | G-00, G-01, G-10 |
| **used_with** | R-ARCH, R-REL, R-GOV-LIB, R-COUNCIL, R-ENG |
| **last_updated** | 2026-05-31 |
| **notes** | Direction, differentiation, roadmap; explicit tradeoffs |

### R-COUNCIL — TEAM MEETING COUNCIL (role + usage)

| Field | Value |
|-------|-------|
| **prompt_id** | R-COUNCIL (usage: legacy U-COUNCIL → Part 2) |
| **file_name** | `roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | role+usage |
| **source_prompt** | Canonical combined file |
| **purpose** | Cross-functional review; exact next-step AI prompts |
| **dependencies** | G-00, G-01, G-05, G-11 |
| **used_with** | All R-* combined files, `TEAM_MEETING.md` |
| **last_updated** | 2026-05-31 |
| **notes** | Multi-domain + prompt-system review; L2 per G-05 |

---

## Tier U — Usage Guides (`docs/13-master-prompts/roles/`)

### U-RESYNC

| Field | Value |
|-------|-------|
| **prompt_id** | U-RESYNC |
| **file_name** | `RESYNC_USAGE.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/RESYNC.md` |
| **purpose** | When/how to RESYNC; preconditions and failure modes |
| **dependencies** | P-RESYNC, G-00 |
| **used_with** | U-ENG, G-09 |
| **last_updated** | 2026-05-24 |
| **notes** | Archive: A-RESYNC |

### U-TOPO

| Field | Value |
|-------|-------|
| **prompt_id** | U-TOPO |
| **file_name** | `TOPOLOGY_USAGE.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P05-TOPOLOGY.md` |
| **purpose** | Topology/VPC/HTML map and diagnostics workflow |
| **dependencies** | P-TOPO, G-07, D-QA-VPC |
| **used_with** | `modules/adapters.py`, `utils/report_formatter.py` |
| **last_updated** | 2026-05-24 |
| **notes** | Archive: A-TOPO |

### U-ORCH

| Field | Value |
|-------|-------|
| **prompt_id** | U-ORCH |
| **file_name** | `ORCHESTRATOR_USAGE.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P03_ORCHESTRATOR.md` |
| **purpose** | Multi-device and plugin chain execution |
| **dependencies** | P-ORCH, P-REG |
| **used_with** | `docs/04-plugins/*` |
| **last_updated** | 2026-05-24 |
| **notes** | Archive: A-ORCH |

### U-CON — CONTRACT (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-CON |
| **file_name** | `CONTRACT_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P01_CONTRACT.md` |
| **purpose** | API/plugin contract enforcement usage *(pending file)* |
| **dependencies** | P-CON |
| **used_with** | P-REG, plugin development |
| **last_updated** | 2026-05-31 |
| **notes** | Registry entry required before file creation per G-03 |

### U-REG — REGISTRY (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-REG |
| **file_name** | `REGISTRY_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P02_REGISTRY.md` |
| **purpose** | Plugin registry operations *(pending file)* |
| **dependencies** | P-REG |
| **used_with** | U-ORCH, `modules/plugins/` |
| **last_updated** | 2026-05-31 |
| **notes** | — |

### U-UI — UI DYNAMO (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-UI |
| **file_name** | `UI_DYNAMO_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P04_UI_DYNAMO.md` |
| **purpose** | Flask/Jinja/UI template safety *(pending file)* |
| **dependencies** | P-UI, G-07 |
| **used_with** | `modules/web/templates/index.html` |
| **last_updated** | 2026-05-31 |
| **notes** | Critical after v6.9.22 Jinja fix in `tmplBuildVarForm` |

### U-LC — LIFECYCLE (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-LC |
| **file_name** | `LIFECYCLE_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P05_LIFECYCLE.md` |
| **purpose** | Feature/plugin lifecycle *(pending file)* |
| **dependencies** | P-LC |
| **used_with** | G-08, G-09 |
| **last_updated** | 2026-05-31 |
| **notes** | — |

### U-ALIGN — ALIGNMENT (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-ALIGN |
| **file_name** | `ALIGNMENT_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P06_ALIGNMENT.md` |
| **purpose** | Cross-module alignment audits *(pending file)* |
| **dependencies** | P-ALIGN, U-RESYNC |
| **used_with** | G-04 |
| **last_updated** | 2026-05-31 |
| **notes** | — |

### U-BAK — BACKUP-RECOVERY (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-BAK |
| **file_name** | `BACKUP_RECOVERY_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/BACKUP-RECOVERY.md` |
| **purpose** | DR and backup procedures *(pending file)* |
| **dependencies** | P-BAK, D-LIB |
| **used_with** | G-05 L3 escalations |
| **last_updated** | 2026-05-31 |
| **notes** | — |

### U-AI — AI BEHAVIOR (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-AI |
| **file_name** | `AI_BEHAVIOR_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/AI-BEHAVIOR-GUIDE.md` |
| **purpose** | AI agent behavioral standards *(pending file)* |
| **dependencies** | P-AI, G-00 |
| **used_with** | All roles |
| **last_updated** | 2026-05-31 |
| **notes** | — |

### U-FND — FOUNDATION (draft usage)

| Field | Value |
|-------|-------|
| **prompt_id** | U-FND |
| **file_name** | `FOUNDATION_USAGE.md` *(planned)* |
| **version** | — |
| **owner** | Prompt Governance Framework |
| **status** | draft |
| **type** | usage |
| **source_prompt** | `docs/02-codebase/PLATFORM_PROMPTS/P01-FOUNDATION.md` |
| **purpose** | Platform foundation concepts *(pending file)* |
| **dependencies** | P-FND |
| **used_with** | P-CON, P-REG |
| **last_updated** | 2026-05-31 |
| **notes** | — |

---

## Platform Source Prompts

**Canonical path (never delete):** `docs/02-codebase/PLATFORM_PROMPTS/`  
**Read in INDEX order:** all files in this folder (INDEX_PROMPT §18).

| prompt_id | file_name | version | owner | status | type | source_prompt | purpose (summary) | dependencies | used_with | last_updated | notes |
|-----------|-----------|---------|-------|--------|------|---------------|-------------------|--------------|-----------|--------------|-------|
| P-RESYNC | RESYNC.md | 1.0.0 | Platform Team | active | role | Self | Pre-task full project sync | — | U-RESYNC, G-00 | — | A-RESYNC |
| P-ENG | ENGINEER.md | 1.0.0 | Platform Team | active | role | Self | Platform implementation norms (depth) | P-RESYNC | R-ENG, U-ENG | — | A-ENG; council master: R-ENG |
| P-LIB | P07-DOCUMENTATION-LIBRARIAN.md | 1.0.0 | Platform Team | active | role | Self | Documentation authority | D-LIB | U-LIB | — | A-LIB |
| P-ORCH | P03_ORCHESTRATOR.md | 1.0.0 | Platform Team | active | role | Self | Workflow orchestration | P-ENG | U-ORCH | — | A-ORCH |
| P-CON | P01_CONTRACT.md | 1.0.0 | Platform Team | active | role | Self | Contracts / interfaces | P-FND | U-CON | — | A-CON |
| P-REG | P02_REGISTRY.md | 1.0.0 | Platform Team | active | role | Self | Plugin registry | P-CON | U-REG, U-ORCH | — | A-REG |
| P-UI | P04_UI_DYNAMO.md | 1.0.0 | Platform Team | active | role | Self | UI/UX and templates | P-ENG | U-UI | — | A-UI |
| P-LC | P05_LIFECYCLE.md | 1.0.0 | Platform Team | active | role | Self | Lifecycle management | P-ENG | U-LC | — | A-LC |
| P-ALIGN | P06_ALIGNMENT.md | 1.0.0 | Platform Team | active | role | Self | System alignment | P-RESYNC | U-ALIGN | — | A-ALIGN |
| P-TOPO | P05-TOPOLOGY.md | 1.0.0 | Platform Team | active | role | Self | Topology / visualization | P-ENG | U-TOPO | — | A-TOPO |
| P-BAK | BACKUP-RECOVERY.md | 1.0.0 | Platform Team | active | role | Self | Backup / DR | D-LIB | U-BAK | — | A-BAK |
| P-AI | AI-BEHAVIOR-GUIDE.md | 1.0.0 | Platform Team | active | guide | Self | AI behavior norms | G-00 | U-AI | — | A-AI |
| P-FND | P01-FOUNDATION.md | 1.0.0 | Platform Team | active | foundation | Self | Platform foundation | — | U-FND, P-CON | — | A-FND |
| P-IDX-A | 00_INDEX.md | 1.0.0 | Platform Team | deprecated | index | Self | Legacy prompt index | P-IDX-B | G-00 | — | Superseded by G-00; keep traceable |
| P-IDX-B | 00-PROMPT-INDEX.md | 1.0.0 | Platform Team | deprecated | index | Self | Legacy prompt index | — | G-00, G-01 | — | Link to v3 hub recommended |

*Platform `last_updated` unknown at source — set when source file is next edited and bump patch version.*

---

## Archive Copies

**Path:** `docs/13-master-prompts/archive/platform-prompts-original/`  
**Rule:** Verbatim snapshot; update only when source changes (new archive generation or forward-sync step).

| prompt_id | file_name | version | owner | status | type | source_prompt | purpose | dependencies | used_with | last_updated | notes |
|-----------|-----------|---------|-------|--------|------|---------------|---------|--------------|-----------|--------------|-------|
| A-RESYNC | RESYNC.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-RESYNC | Frozen copy for diff/history | P-RESYNC | G-03 | 2026-05-24 | 15 files archived together |
| A-ENG | ENGINEER.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-ENG | Frozen copy | P-ENG | G-03 | 2026-05-24 | — |
| A-LIB | P07-DOCUMENTATION-LIBRARIAN.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-LIB | Frozen copy | P-LIB | G-03 | 2026-05-24 | — |
| A-ORCH | P03_ORCHESTRATOR.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-ORCH | Frozen copy | P-ORCH | G-03 | 2026-05-24 | — |
| A-CON | P01_CONTRACT.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-CON | Frozen copy | P-CON | G-03 | 2026-05-24 | — |
| A-REG | P02_REGISTRY.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-REG | Frozen copy | P-REG | G-03 | 2026-05-24 | — |
| A-UI | P04_UI_DYNAMO.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-UI | Frozen copy | P-UI | G-03 | 2026-05-24 | — |
| A-LC | P05_LIFECYCLE.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-LC | Frozen copy | P-LC | G-03 | 2026-05-24 | — |
| A-ALIGN | P06_ALIGNMENT.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-ALIGN | Frozen copy | P-ALIGN | G-03 | 2026-05-24 | — |
| A-TOPO | P05-TOPOLOGY.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-TOPO | Frozen copy | P-TOPO | G-03 | 2026-05-24 | — |
| A-BAK | BACKUP-RECOVERY.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-BAK | Frozen copy | P-BAK | G-03 | 2026-05-24 | — |
| A-AI | AI-BEHAVIOR-GUIDE.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-AI | Frozen copy | P-AI | G-03 | 2026-05-24 | — |
| A-FND | P01-FOUNDATION.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-FND | Frozen copy | P-FND | G-03 | 2026-05-24 | — |
| A-IDX-A | 00_INDEX.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-IDX-A | Frozen copy | P-IDX-A | G-03 | 2026-05-24 | deprecated source |
| A-IDX-B | 00-PROMPT-INDEX.md | 1.0.0 | Prompt Governance Framework | active | archive-copy | P-IDX-B | Frozen copy | P-IDX-B | G-03 | 2026-05-24 | deprecated source |

---

## Linked Project Documentation

Registered for INDEX read order §14–17; not stored under `13-master-prompts/`.

| prompt_id | file_name | version | status | type | source_prompt | purpose | used_with | last_updated |
|-----------|-----------|---------|--------|------|---------------|---------|-----------|--------------|
| D-LIB | LIBRARIAN_MANDATE.md | 1.0.0 | active | institutional | `docs/00-overview/LIBRARIAN_MANDATE.md` | Institutional memory / DR | U-LIB, G-06 | — |
| D-OVR | docs/README.md | — | active | hub | Self | Documentation hierarchy | G-12 | 2026-05-31 |
| D-QA-VPC | QA_VPC_MAP.md | 1.0.0 | active | qa | `docs/09-qa/QA_VPC_MAP.md` | VPC map validation | U-TOPO, G-07 | — |
| D-SEARCH | search-it-workflow.md | 1.1.0 | active | operations | `docs/08-operations/search-it-workflow.md` | Network Search tab workflow | U-ENG | Also: network-search-workflow.md |
| D-VPC-PLG | vpc-domain-plugin.md | 1.0.0 | active | plugin | `docs/04-plugins/vpc-domain-plugin.md` | vPC Domain plugin | U-ORCH | — |
| D-REL | CHANGELOG.md | — | active | release-notes | `/CHANGELOG.md` | Release truth | G-09, U-RESYNC | 2026-05-31 |

---

## Action Logs (`docs/13-master-prompts/action-logs/`)

### AL-README

| Field | Value |
|-------|-------|
| **prompt_id** | AL-README |
| **file_name** | `README.md` |
| **version** | 3.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | meta |
| **source_prompt** | G-03, G-02 |
| **purpose** | Action log format and location |
| **dependencies** | G-02 |
| **used_with** | All meaningful role invocations |
| **last_updated** | 2026-05-24 |
| **notes** | — |

### AL-20260524

| Field | Value |
|-------|-------|
| **prompt_id** | AL-20260524 |
| **file_name** | `2026-05-24_governance-v3-scaffold.md` |
| **version** | 1.0.0 |
| **owner** | Prompt Governance Framework |
| **status** | active |
| **type** | action-log |
| **source_prompt** | G-03 workflow |
| **purpose** | Record initial v3.0 hub creation |
| **dependencies** | G-00–G-12 |
| **used_with** | — |
| **last_updated** | 2026-05-24 |
| **notes** | — |

---

## Application Hot Paths (reference)

Not prompt files; indexed for RESYNC and ENGINEER (Tier 3 from prior registry).

| Domain | Modules |
|--------|---------|
| Web entry | `vlan_checker_web.py` |
| Adapters / topology | `modules/adapters.py`, `modules/topology_mapper.py` |
| HTML maps | `utils/report_formatter.py` |
| Plugins | `modules/plugins/*.py` |
| Description search | `modules/description_search.py` |
| UI templates | `modules/web/templates/index.html` |
| Pre-build gates | `_prebuild.py`, `tests/validate_vpc_member_interfaces.py` |

---

## Registry Change Log

| Date | Registry version | Change type | Summary |
|------|------------------|-------------|---------|
| 2026-05-24 | 3.0.0 | major | Initial hub: governance files, 5 usage guides, platform archive |
| 2026-05-31 | 3.1.0 | major | Full required-fields schema; all G/U/P/A entries; draft usage slots for 8 roles |
| 2026-05-31 | 3.1.1 | minor | PROMPT_USAGE_MANUAL v3.0 council model; 9 council usage guides + UI_DYNAMO; ROLE_MATRIX 3.1 |
| 2026-05-31 | 3.1.2 | minor | G-13 PROMPT_ACTIVATION_POLICY; INDEX read order §4 |
| 2026-05-31 | 3.1.3 | minor | G-14 ROLE_USAGE_STANDARD; U-LOG-TPL; template alignment |
| 2026-05-31 | 3.1.4 | minor | G-15 PROMPT_EXECUTION_RULES; INDEX Phase A/B aligned to 15-step sequence |
| 2026-05-31 | 3.1.5 | minor | G-03 PROMPT_GOVERNANCE_POLICY v3.0 full spec; governance action log fields |
| 2026-05-31 | 3.1.6 | minor | G-04 ROLE_MATRIX v3.0: matrix fields, full council/domain tables, output artifacts |
| 2026-05-31 | 3.1.7 | minor | G-05 ESCALATION_MATRIX v3.0: issue-type matrix, matrix fields, resolution logging |
| 2026-05-31 | 3.1.8 | minor | G-06 DOCUMENTATION_POLICY v3.0: rules, ownership, documentation action log |
| 2026-05-31 | 3.1.9 | minor | G-07 QUALITY_GATE_POLICY v3.0: 11 gates, risk profile, quality-gate action log |
| 2026-05-31 | 3.1.10 | minor | G-08 CHANGE_MANAGEMENT_POLICY v3.0: 8-phase lifecycle, artifacts, change action log |
| 2026-05-31 | 3.1.11 | minor | G-09 RELEASE_MANAGEMENT_POLICY v3.0: required checks, release action log, rollback rules |
| 2026-05-31 | 3.1.12 | minor | G-10 COMPETITIVE_ADVANTAGE_POLICY v3.0: review domains, required outputs, strategic log |
| 2026-05-31 | 3.1.13 | minor | G-16 PROMPT_MIGRATION_SYNC v3.0: migration/sync workflows, output requirements |
| 2026-05-31 | 3.1.14 | minor | R-GOV-LIB PROMPT_LIBRARIAN role prompt v3.0; U-GOV-LIB usage realigned |
| 2026-05-31 | 3.1.15 | minor | R-ARCH SYSTEM_ARCHITECT role prompt v3.0; U-ARCH ROLE USAGE aligned |
| 2026-05-31 | 3.1.16 | minor | R-ENG LEAD_DEVELOPER role prompt v3.0; U-ENG ROLE USAGE; P-ENG linked |
| 2026-05-31 | 3.1.17 | minor | R-QA QA_ENGINEER role prompt v3.0; U-QA ROLE USAGE; G-07 alignment |
| 2026-05-31 | 3.1.18 | minor | R-SEC SECURITY_REVIEWER role prompt v3.0; U-SEC ROLE USAGE |
| 2026-05-31 | 3.1.19 | patch | U-SEC: trust/access/exposure/misuse invoke; full-path + prompt surface practices |
| 2026-05-31 | 3.1.20 | minor | R-OBS OBSERVABILITY_ENGINEER role prompt v3.0; U-OBS ROLE USAGE (G-14) |
| 2026-05-31 | 3.1.21 | patch | U-OBS: seen/measured/diagnosed invoke; logs/metrics/traces + actionable telemetry |
| 2026-05-31 | 3.1.22 | minor | R-LIB DOCUMENTATION_STEWARD role v3.0; U-LIB canonical DOCUMENTATION_STEWARD_USAGE |
| 2026-05-31 | 3.1.23 | patch | U-LIB: system-change truth invoke; future maintainers, why, compatibility |
| 2026-05-31 | 3.1.24 | minor | R-REL RELEASE_MANAGER role v3.0; U-REL ROLE USAGE; G-09 alignment |
| 2026-05-31 | 3.1.25 | patch | U-REL: implementation→release invoke; no uncertainty; dependency chain; rollback first |
| 2026-05-31 | 3.1.26 | minor | R-PROD PRODUCT_STRATEGIST role v3.0; U-PROD ROLE USAGE; G-10 alignment |
| 2026-05-31 | 3.1.27 | patch | U-PROD: direction/differentiation/roadmap invoke; mission, durable advantage, tradeoffs |
| 2026-05-31 | 3.1.28 | minor | R-COUNCIL TEAM_MEETING_COUNCIL v3.0; U-COUNCIL ROLE USAGE; G-11 template link |
| 2026-05-31 | 3.1.29 | patch | U-COUNCIL: multi-domain/prompt-system invoke; focused assessments; exact next prompts |
| 2026-06-10 | 4.0.4 | minor | G-CC PROMPT_COMMAND_CENTER; app sync 7.0.29; D-SEARCH → 08-operations; path corrections 09-qa |
| 2026-06-10 | 4.0.5 | minor | W-DOC-SYNC, W-BUG-FIX-ALL, W-UI-UX, W-NEXT-STEPS workflows; COMMAND_MANUAL.html |
| 2026-05-31 | 3.1.30 | minor | G-17 FINAL_OPERATING_INSTRUCTION v3.0; INDEX read order; G-03 precedence |
| 2026-05-31 | 3.1.31 | minor | Combined ROLE_*_USAGE_PROMPT.md per council role (roles/combined/) |
| 2026-05-31 | 3.1.32 | major | G-18 GLOBAL_MASTER_PROMPT_RULES v4.0; INDEX v4.0; 20 absolute rules |
| 2026-05-31 | 3.1.33 | major | INDEX v4.0 user spec; numbered stubs 00-25; 26 bug sweep; bugs/_TEMPLATE |
| 2026-05-31 | 4.0.0 | major | PROMPT_REGISTRY v4.0 preamble (purpose, fields, rules, sync); G-01 entry 4.0.0 |
| 2026-05-31 | 4.0.1 | minor | W-BUG-SWEEP v4.0 roles/CHECK_SYSTEM_FOR_BUGS.md; docs/14-bug-reports/ scaffold |
| 2026-05-31 | 4.0.2 | minor | G-17 FINAL_OPERATING_INSTRUCTION v4.0; simple commands; success criteria + continuous dev |
| 2026-05-31 | 4.0.3 | major | Hub dedup: council canonical in `roles/combined/` only; retired split R/U, C-* rows, numbered stubs, `bugs/_TEMPLATE`; INDEX/registry/activation aligned |

---

## Index Linkage Validation

| INDEX_PROMPT § | Linked registry IDs |
|----------------|---------------------|
| §2 | G-01 |
| §3 | G-02 |
| §4 | G-13 |
| §5 | G-14 |
| §6 | G-15 |
| §7 | G-03 … G-11 (policies) |
| §8 | P-* (role prompts) |
| §9 | U-* (usage guides) |
| §10 | RESYNC / D-*, VERSION, CHANGELOG |
| §11–15 | G-15 Phase B (activate, execute, log, registry, docs) |
| §16 | P-* (all PLATFORM_PROMPTS) |

**Validated:** 2026-05-31 — INDEX aligned to G-15 execution sequence.
