# PROMPT_USAGE_MANUAL

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **last_updated** | 2026-05-31 |
| **Registry ID** | G-02 |

## Purpose

This manual explains when, how, and why to use each prompt in the master prompt system.

This is **MANDATORY** reading for the AI IDE. The AI MUST read this before using any role prompt if the task is unfamiliar or high risk.

**Full runbook:** `PROMPT_EXECUTION_RULES.md` (G-15) — steps 1–15 (read → resync → activate roles → log → registry → docs).

---

## Global Usage Rules

1. Use `INDEX_PROMPT.md` first.
2. Use `PROMPT_REGISTRY.md` to locate the right prompt (`prompt_id`, `status`, `source_prompt`).
3. Use this usage manual (and the relevant `roles/*_USAGE.md`) before using the role prompt if the task is unfamiliar or high risk.
4. Use the role prompt (`docs/02-codebase/PLATFORM_PROMPTS/`) for execution behavior.
5. Use the policy prompts (`G-06`–`G-10`) whenever the task touches their domain.
6. Use `TEAM_MEETING.md` when multiple roles need coordination or the issue is ambiguous.
7. **RESYNC** before every significant action: latest docs, prompts, code/release notes, bug fixes, and policies.

---

## Mandatory Role Activation Rule

**Policy:** `PROMPT_ACTIVATION_POLICY.md` (G-13) — authoritative for automatic activation, dependency order, and activation logging.

THE AI MUST automatically identify every relevant role for a task based on:

- the prompt
- codebase context
- documentation
- release notes
- current system state

**EVEN when the user does not explicitly mention that role.**

If a role is relevant to the request, the AI MUST read and apply that role's prompt and usage guide before taking action.

If multiple roles are relevant, the AI MUST coordinate them in dependency order and escalate conflicts to the Team Meeting Council when needed.

**Dependency order (default):**

```
RESYNC → Product Strategist (scope) → System Architect (design) → Lead Developer (code)
→ QA Engineer → Security Reviewer → Observability Engineer → Documentation Steward
→ Release Manager → Prompt Librarian (if prompts/registry changed)
```

Team Meeting Council may reorder when conflicts exist.

---

## Council Roles ↔ Project Prompts

| Council role | Registry | Invoke (`roles/combined/`) |
|--------------|----------|----------------------------|
| **Prompt Librarian** | R-GOV-LIB | `ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` · G-01, G-03, G-16 |
| **System Architect** | R-ARCH | `ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` · advisory P-FND, P-CON, ENGINEER, P06_ALIGNMENT |
| **Lead Developer** | R-ENG | `ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` · platform `ENGINEER.md` (P-ENG) |
| **QA Engineer** | R-QA | `ROLE_QA_ENGINEER_USAGE_PROMPT.md` · G-07, `docs/09-qa/` |
| **Security Reviewer** | R-SEC | `ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` · G-08, P-BAK |
| **Observability Engineer** | R-OBS | `ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` · G-07, diagnostics |
| **Documentation Steward** | R-LIB | `ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` · G-06, D-LIB |
| **Release Manager** | R-REL | `ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` · G-09, G-08 |
| **Product Strategist** | R-PROD | `ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` · G-10 |
| **Team Meeting Council** | R-COUNCIL | `ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` · G-11, G-05 |
| **RESYNC** (pre-chain) | `U-RESYNC` | `RESYNC.md` |
| **Topology / Network** | `U-TOPO` | `P05-TOPOLOGY.md` |
| **Orchestrator** | `U-ORCH` | `P03_ORCHESTRATOR.md` |

Domain specialists (TOPOLOGY, ORCHESTRATOR, UI DYNAMO, etc.) activate **in addition** when signals match `ROLE_MATRIX.md`.

---

## Every Usage Guide Must Include

**Authoritative standard:** `ROLE_USAGE_STANDARD.md` (G-14)

Each `roles/*_USAGE.md` MUST include the **7 required sections**:

1. When to invoke  
2. Best practices  
3. Common scenarios  
4. Expected result  
5. Related roles  
6. Related policies  
7. Common mistakes  

Plus **recommended elaboration** (role purpose, when not to use, required inputs, resync, escalation) and **standard output** (findings, recommendations, decisions, risks, action log).

**Role prompts** (`PLATFORM_PROMPTS/`) should align to G-14 §12 sections when enhanced; originals remain immutable source.

Templates: `roles/_USAGE_GUIDE_STANDARD.md` · `roles/_ACTION_LOG_SNIPPET.md`

---

## How the AI IDE Chooses Roles

1. Analyze the task domain.
2. Identify which roles' missions are relevant (table above + `ROLE_MATRIX.md`).
3. Check `PROMPT_REGISTRY.md` for all **active** prompts; note **draft** usage guides if creating them.
4. Read the usage manual section (this file) and each relevant `roles/*_USAGE.md`.
5. Activate all relevant roles automatically.
6. Execute in dependency order.
7. Log actions in `action-logs/`.
8. Update registry and docs when prompts, versions, or behavior change.

---

## Role Activation Rules

A role is **automatically activated** when:

| Role | Activate when |
|------|----------------|
| **Prompt Librarian** | Prompts are created, copied, renamed, synced, deprecated, retired, or registry updates are needed. |
| **System Architect** | Architecture, module boundaries, dependencies, or core design may change. |
| **Lead Developer** | Code needs to be written, changed, fixed, or refactored. |
| **QA Engineer** | Features, fixes, refactors, or prompt-driven behavior change; or release readiness must be validated. |
| **Security Reviewer** | Authentication, authorization, permissions, secrets, external systems, sensitive data, or trust boundaries are involved. |
| **Observability Engineer** | Logs, metrics, traces, alerts, dashboards, or operational diagnosis may change. |
| **Documentation Steward** | Behavior, prompts, architecture, or user guidance changes. |
| **Release Manager** | Change is nearing release, risk is non-trivial, or rollback plan is needed. |
| **Product Strategist** | Change affects user value, roadmap, market position, or product direction. |
| **Team Meeting Council** | Multiple roles are involved, conflicts exist, or complex/strategic issues must be resolved. |

**Also activate (domain):** RESYNC (always before significant work); TOPOLOGY (VPC/maps); ORCHESTRATOR (plugins/batch); UI DYNAMO (Flask/Jinja/templates).

---

## Resync Rules

Before every significant action, the AI MUST:

1. Read `INDEX_PROMPT.md`.
2. Read `PROMPT_REGISTRY.md`.
3. Read relevant policies (`G-03`–`G-10` as applicable).
4. Read relevant project docs (`docs/`, feature docs, `LIBRARIAN_MANDATE.md`).
5. Read latest code changes (git diff / touched modules).
6. Read latest release notes (`CHANGELOG.md`, `VERSION`).
7. Read latest bug fixes (top CHANGELOG **Fixed** entries).
8. Confirm no newer prompt or doc supersedes current context.

**Project RESYNC shortcut:** `VERSION` + `CHANGELOG.md` (first 2 versions) + `PROMPT_REGISTRY.md` application sync line + task-specific modules from registry Tier 3 hot paths.

---

## Escalation Rules

- Escalate unresolved conflicts to **Team Meeting Council** (`TEAM_MEETING.md`).
- Escalate architecture drift to **System Architect** or Team Meeting.
- Escalate quality risks to **Release Manager** or Team Meeting.
- Escalate security risks to **Release Manager** or Team Meeting.
- Escalate observability gaps to Team Meeting.
- Escalate documentation gaps to Team Meeting.
- **When in doubt, escalate.**

Matrix: `ESCALATION_MATRIX.md` · Council: `roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md`

---

## Documentation Rules

- Every code change must trigger **Documentation Steward** review.
- Every prompt change must trigger Documentation Steward + **Prompt Librarian** review.
- Every architecture change must trigger Documentation Steward review.
- Every release must trigger Documentation Steward review.
- Every bug fix must trigger Documentation Steward review if behavior or ops impact changes.
- Documentation must describe **what** changed, **why**, and **how to use** it.
- Include compatibility and rollback notes when relevant.
- Preserve legacy intent and historical meaning (`PROMPT_GOVERNANCE_POLICY.md` sync rule).

Policy: `DOCUMENTATION_POLICY.md` · Mandate: `docs/00-overview/LIBRARIAN_MANDATE.md`

---

## Quality Gate Rules

Required gates when relevant (no bypass):

| Gate | Owner role | Project hook |
|------|------------|--------------|
| Developer Review | Lead Developer | Peer/self review of diff scope |
| Architect Review | System Architect | Module boundaries, dependencies |
| QA Review | QA Engineer | `_prebuild.py`, `tests/validate_vpc_member_interfaces.py` |
| Documentation Review | Documentation Steward | CHANGELOG, `docs/` |
| Release Review | Release Manager | `VERSION`, EXE, dist package |
| Backward Compatibility Review | System Architect + QA | Plugin IDs, inventory formats |
| Performance Review | Lead Developer + TOPOLOGY | HTML map, physics, batch jobs |
| Security Review | Security Reviewer | SSH, creds, secrets |
| Observability Review | Observability Engineer | Diagnostics folder, logs |
| Network Engineering Review | TOPOLOGY | Parsers, VPC, CDP/LLDP |
| Automation Review | ORCHESTRATOR | Plugins, multi-device workflows |

Policy detail: `QUALITY_GATE_POLICY.md`

---

## Example Workflows

### Workflow 1: New Feature

1. Read index and registry.
2. Activate **Product Strategist** for scope (`G-10`).
3. Activate **System Architect** for design (`P-ENG`, `P-CON`, `P-FND`).
4. Activate **Lead Developer** for implementation (`ENGINEER.md`).
5. Activate **QA Engineer** for validation (`G-07`, tests).
6. Activate **Security Reviewer** for sensitive changes.
7. Activate **Observability Engineer** for monitoring/diagnostics if operational surface changes.
8. Activate **Documentation Steward** for docs.
9. Activate **Release Manager** for rollout (`G-09`).
10. Log all actions (`action-logs/`).

### Workflow 2: Bug Fix

1. Read index and registry.
2. **RESYNC** — note latest **Fixed** entries (e.g. v6.9.22 Jinja `index.html`).
3. Activate **QA Engineer** for reproduction.
4. Activate **Lead Developer** for fix.
5. Activate **QA Engineer** for regression testing.
6. Activate **Documentation Steward** if behavior changed.
7. Activate **Release Manager** for hotfix if shipping.
8. Log all actions.

### Workflow 3: Prompt System Change

1. Read index and registry.
2. Activate **Prompt Librarian** for migration (archive → enhance → registry).
3. Activate **Documentation Steward** for usage guide updates.
4. Activate **System Architect** if structure/responsibility changes (major version).
5. Activate **Team Meeting Council** for governance review if conflicts.
6. Log all actions; update `PROMPT_REGISTRY.md` change log.

### Workflow 4: Topology / VPC (this project)

1. RESYNC + registry.
2. **System Architect** + **Lead Developer** + **TOPOLOGY** (`U-TOPO`).
3. **QA Engineer** — `QA_VPC_MAP.md`, validation script.
4. **Observability Engineer** — `topology_diagnostics_*` exports.
5. **Documentation Steward** — parsing/visualization docs.
6. Log actions.

---

## Task → Quick Activation (legacy map)

| User intent | Council + domain roles |
|-------------|------------------------|
| RESYNC / align | RESYNC, Documentation Steward, Prompt Librarian |
| Feature / fix | RESYNC, Product Strategist, Architect, Developer, QA, Documentation Steward |
| Topology / VPC | + TOPOLOGY, Network Engineering gate |
| Plugin | + ORCHESTRATOR, Architect |
| UI / Flask / Jinja | + UI DYNAMO (`U-UI`), QA |
| Release / EXE | Release Manager, QA, Documentation Steward |
| Governance only | Prompt Librarian, Team Meeting Council |

---

## Common Mistakes

- Using a role without reading the index first.
- Skipping resync.
- Not activating all relevant roles.
- Bypassing required policy gates.
- Not logging actions.
- Not preserving legacy prompt intent.
- Not escalating conflicts.
- Not updating the registry.
- Treating **ENGINEER** as only coder — missing **Architect** design pass on structural changes.
- Editing `PLATFORM_PROMPTS/` without archive + registry workflow.

---

## Action Log Requirements

Every meaningful invocation MUST log under `docs/13-master-prompts/action-logs/` with:

- files reviewed
- files changed
- versions updated
- links preserved
- what was verified
- what remains open
- risks remaining
- decisions made

Filename: `YYYY-MM-DD_<short-slug>.md` · Format: `action-logs/README.md`

---

## Success Criteria

Before execution starts, confirm:

- [ ] Relevant prompts identified (`PROMPT_REGISTRY.md`)
- [ ] Relevant policies identified
- [ ] Relevant docs identified
- [ ] Risks identified
- [ ] Approval chain identified (escalation level)
- [ ] Next action defined

After execution:

- [ ] All actions logged
- [ ] Registry updated (if prompts/versions changed)
- [ ] Documentation updated (if behavior changed)

---

## Related Documents

| Document | ID |
|----------|-----|
| `INDEX_PROMPT.md` | G-00 |
| `PROMPT_REGISTRY.md` | G-01 |
| `ROLE_MATRIX.md` | G-04 |
| `ESCALATION_MATRIX.md` | G-05 |
| `TEAM_MEETING.md` | G-11 |
| `PROMPT_ACTIVATION_POLICY.md` | G-13 |
| `ROLE_USAGE_STANDARD.md` | G-14 |
| `PROMPT_EXECUTION_RULES.md` | G-15 |
| `PROMPT_GOVERNANCE_POLICY.md` | G-03 |
| `PROMPT_MIGRATION_SYNC.md` | G-16 |
