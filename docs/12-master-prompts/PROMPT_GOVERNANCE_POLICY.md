# PROMPT_GOVERNANCE_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-03 |
| **last_updated** | 2026-05-31 |

## Purpose

Define the governance model for the entire master prompt ecosystem.

**Scope:** `docs/13-master-prompts/`, `docs/02-codebase/PLATFORM_PROMPTS/`, registry, usage guides, action logs, and cross-links to institutional docs.

---

## Authority

The master prompt system governs how AI and human contributors interpret roles, policies, and execution order.

| Asset | Governs |
|-------|---------|
| `INDEX_PROMPT.md` (G-00) | Entry point, mission, mandatory rules, read order |
| `PROMPT_EXECUTION_RULES.md` (G-15) | Mandatory read → resync → execute → log → registry → docs (with G-17 at step 7) |
| `PROMPT_REGISTRY.md` (G-01) | Prompt identity, lineage, versions, dependencies |
| `PROMPT_ACTIVATION_POLICY.md` (G-13) | Automatic role activation |
| `ROLE_USAGE_STANDARD.md` (G-14) | Role prompt + usage guide structure, output format |
| Role prompts (`PLATFORM_PROMPTS/`) | Execution behavior and responsibility |
| Council combined (`roles/combined/ROLE_*_USAGE_PROMPT.md`) + domain usage (`roles/*_USAGE.md`) | Correct invocation, gates, escalation |
| `LIBRARIAN_MANDATE.md` | Documentation truth for the wider repository |

---

## Rules

1. **All prompts must be versioned and registry-backed** — every file has a `PROMPT_REGISTRY.md` entry with required fields (see registry § Required Fields).
2. **All prompts must have a purpose, scope, dependencies, and output format** — documented in registry and/or prompt body; roles use G-14 § Standard Output Format.
3. **All council roles use combined invoke files** — Part 1 + Part 2 in `roles/combined/` per `ROLE_USAGE_STANDARD.md` (G-14). Domain specialists keep `roles/*_USAGE.md` (draft rows allowed until file exists).
4. **All prompts must include action logging requirements** — `PROMPT_EXECUTION_RULES.md` step 13; `ROLE_USAGE_STANDARD.md` action log template.
5. **All prompts must support source-to-master traceability** — `source_prompt` field; archive under `archive/platform-prompts-original/`.
6. **All prompts must preserve historical intent** — forward sync only; no silent replacement of legacy meaning.
7. **All prompt changes require documentation review** — Documentation Steward (`DOCUMENTATION_POLICY.md`, `CHANGELOG.md`).
8. **All prompt changes require dependency and compatibility review** — System Architect + affected policies; registry `dependencies` / `used_with` updated.
9. **Prompt retirement requires deprecation notes and migration guidance** — registry `status`: `deprecated` → `retired`; `notes` must cite successor (`prompt_id` or path).

### Immutable operational rules

1. **Never delete** files in `docs/02-codebase/PLATFORM_PROMPTS/`.
2. **Archive before enhance** — verbatim copies in `archive/platform-prompts-original/`.
3. **Forward sync** — document deltas in registry change log and action logs.
4. **Registry first** — no new prompt without registry entry (workflow § Required Registry Workflow).
5. **No undocumented prompt changes** — steps 13–15 of `PROMPT_EXECUTION_RULES.md` apply.

---

## Governance Expectations

- The prompt ecosystem is treated as a **managed engineering asset**.
- Prompt changes are reviewed like **production system changes** (change class per `CHANGE_MANAGEMENT_POLICY.md`).
- The **index prompt** governs execution order (Phase A/B; defers sequence detail to G-15).
- The **registry** governs prompt identity and lineage.
- **Role prompts** govern execution behavior.
- **Usage prompts** govern correct usage.
- **Activation policy** (G-13) governs which roles run without explicit user naming.
- **Quality gates** (`QUALITY_GATE_POLICY.md`) apply when prompts affect runtime behavior or release artifacts.

---

## Prompt change workflow

Detailed steps: **`PROMPT_MIGRATION_SYNC.md` (G-16)** — migration workflow (1–10) and sync workflow.

| Step | Owner | Action |
|------|-------|--------|
| 1 | Prompt Librarian | Identify prompt; confirm `source_prompt` |
| 2 | Prompt Librarian | Archive if `PLATFORM_PROMPTS/` source changed (G-16) |
| 3 | System Architect | Dependency / compatibility review (major/minor) |
| 4 | Prompt Librarian | Update registry (version bump: major / minor / patch) |
| 5 | Documentation Steward | CHANGELOG, docs, usage guide |
| 6 | Team Meeting Council | If conflict or policy precedence dispute |
| 7 | Prompt Librarian | Action log; index linkage validation |

Version semantics (registry):

- **Major:** structure, responsibility, or behavior changes  
- **Minor:** expanded scope or important clarification  
- **Patch:** wording or formatting only  

---

## Retirement and deprecation

| Status | Meaning | Required in `notes` |
|--------|---------|---------------------|
| `deprecated` | Superseded but traceable | Successor `prompt_id` or path |
| `retired` | No longer used for activation | Migration guide link; historical archive path |

Deprecated prompts remain in `PLATFORM_PROMPTS/` and archive; never deleted.

Examples: `P-IDX-A`, `P-IDX-B` → superseded by G-00 / G-01.

---

## Conflict resolution

If two prompts disagree, precedence order:

1. `GLOBAL_MASTER_PROMPT_RULES.md` (G-18) for the 20 absolute rules, mission, vision, principles  
2. `INDEX_PROMPT.md` mandatory entry and read order  
3. `FINAL_OPERATING_INSTRUCTION.md` (G-17) for IDE operational duties and success criteria  
4. `PROMPT_EXECUTION_RULES.md` (G-15) for sequence and no-skip rules  
5. Active policy in `docs/13-master-prompts/` (including G-13 activation, G-14 usage standard)  
6. `docs/00-overview/LIBRARIAN_MANDATE.md` for repository documentation truth  
7. Original `PLATFORM_PROMPTS/` text  
8. Escalate to `TEAM_MEETING.md` (G-11)  

---

## Required governance action log

For every **prompt governance** change, append `action-logs/YYYY-MM-DD_<slug>.md` including:

| Field | Content |
|-------|---------|
| **Governance concern reviewed** | What policy/rule applied |
| **Prompt risk identified** | Drift, precedence, retirement, missing usage guide |
| **Policy affected** | G-* IDs (G-03, G-13, G-14, G-15, etc.) |
| **Decision made** | Approve, defer, escalate, version bump class |
| **Remaining risk** | Open items, draft usage guides, sync lag |

Also include G-14 standard blocks when roles were active: findings, recommendations, files changed, versions updated.

Template: `roles/_ACTION_LOG_SNIPPET.md` · Prompt-specific: `action-logs/2026-05-31_*_governance.md` examples in folder.

---

## Review cadence

- **Each release:** update registry application sync line; RESYNC Tier 3 hot paths if modules moved.  
- **Each new PLATFORM_PROMPT:** archive + registry + usage guide (or draft row).  
- **Each governance spec from owner:** bump policy `version`, registry `last_updated`, CHANGELOG documentation section.

---

## Success criteria

- [ ] All prompts registry-backed with purpose, dependencies, and status  
- [ ] Usage guides exist or draft rows tracked for every operational role  
- [ ] Traceability: source → archive → master → registry  
- [ ] Prompt changes documented and compatibility reviewed  
- [ ] Governance action log filed for non-trivial changes  

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set, first policy file).
