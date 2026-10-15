# PROMPT_ACTIVATION_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-13 |
| **last_updated** | 2026-05-31 |

## Purpose

Define mandatory rules for when and how the AI IDE must activate roles automatically, even without explicit user instruction.

**Related:** `PROMPT_USAGE_MANUAL.md` (workflows) · `ROLE_MATRIX.md` (IDs) · `PROMPT_REGISTRY.md` (paths)

---

## Mandatory Activation Rule

THE AI MUST automatically identify every relevant role for a task based on:

- the user prompt
- codebase context
- documentation
- release notes
- current system state
- task domain

**EVEN when the user does not explicitly mention that role.**

---

## Activation Conditions

A role MUST be activated when its mission is relevant to the task.

### Automatic Activation Matrix

| Council role | Registry ID | Invoke (Part 1 + Part 2) | Activated when |
|--------------|-------------|--------------------------|----------------|
| **RESYNC** | U-RESYNC | `roles/RESYNC_USAGE.md` | Before every significant action; new session; stale context |
| **Prompt Librarian** | R-GOV-LIB | `roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` | Prompts created, copied, renamed, synced, deprecated, retired, registry updated |
| **System Architect** | R-ARCH | `roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` | Architecture, boundaries, dependencies, core design may change |
| **Lead Developer** | R-ENG | `roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` | Code written, changed, fixed, refactored |
| **QA Engineer** | R-QA | `roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md` | Features, fixes, refactors, behavior change, release validation |
| **Security Reviewer** | R-SEC | `roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` | Auth, permissions, secrets, external systems, sensitive data, trust boundaries |
| **Observability Engineer** | R-OBS | `roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` | Logs, metrics, traces, alerts, dashboards, operational diagnosis |
| **Documentation Steward** | R-LIB | `roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` | Behavior, prompts, architecture, user guidance changes |
| **Release Manager** | R-REL | `roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` | Nearing release, non-trivial risk, rollback, deployment coordination |
| **Product Strategist** | R-PROD | `roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` | User value, roadmap, market position, prioritization, product direction |
| **Team Meeting Council** | R-COUNCIL | `roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` | Multiple roles, conflicts, cross-functional/strategic issues |

### Domain specialists (add when signals match)

| Role | Registry ID | Activated when |
|------|-------------|----------------|
| **TOPOLOGY** | U-TOPO | VPC, topology map, CDP/LLDP, HTML visualization, diagnostics exports |
| **ORCHESTRATOR** | U-ORCH | Plugins, batch/multi-device workflows |
| **UI DYNAMO** | U-UI | Flask, Jinja, `index.html`, web UI tabs |

See `ROLE_MATRIX.md` § Auto-Activation Hints for project-specific keywords.

---

## No Explicit User Instruction Required

The AI MUST NOT wait for the user to name a role.

If the task domain touches a role's mission, the AI MUST:

1. Load the council **combined** file (`docs/13-master-prompts/roles/combined/ROLE_*_USAGE_PROMPT.md`) or platform/policy prompt as applicable.
2. Read **Part 1** (role) then **Part 2** (usage) in that file; for domain specialists use `roles/*_USAGE.md`.
3. **RESYNC** to latest context (`VERSION`, `CHANGELOG.md`, registry, task docs).
4. Apply the role's responsibilities.
5. Document the role's contribution (action log).

---

## Dependency Chain

Roles must execute in dependency order:

0. **RESYNC** (context reconstruction — always before significant work)
1. **Product Strategist** (scope / value — when feature or direction changes)
2. **System Architect** (design approval)
3. **Lead Developer** (implementation)
4. **QA Engineer** (validation)
5. **Security Reviewer** (if sensitive)
6. **Observability Engineer** (if telemetry/diagnostics affected)
7. **Documentation Steward** (always for meaningful changes)
8. **Release Manager** (rollout approval when shipping)
9. **Prompt Librarian** (when prompts/registry changed)

Domain roles (TOPOLOGY, ORCHESTRATOR, UI DYNAMO) run **with** Developer/QA when their signals are active.

---

## Escalation to Team Meeting

Escalate to **Team Meeting Council** (`TEAM_MEETING.md`, `U-COUNCIL`) when:

- Multiple roles are involved.
- Conflicting findings exist.
- The system needs cross-functional review.
- Strategic or complex issue must be resolved.
- Uncertainty is high.
- No single role owns the decision.

Escalation matrix: `ESCALATION_MATRIX.md`

---

## Documentation Requirement

Every role activation must be logged in `docs/13-master-prompts/action-logs/` with:

- which role was activated
- why it was activated
- what it reviewed
- what it changed
- what it recommended
- what remains open

Format: `action-logs/README.md` · Manual: `PROMPT_USAGE_MANUAL.md` § Action Log Requirements

---

## Policy Enforcement

- No role may operate in isolation when another role is impacted.
- No role may bypass documentation, QA, security, observability, architecture, or release review when relevant.
- No change may bypass quality gates (`QUALITY_GATE_POLICY.md`).
- No undocumented changes are permitted (`DOCUMENTATION_POLICY.md`).

---

## Success Criteria

- [ ] All relevant roles activated automatically
- [ ] Roles executed in dependency order (RESYNC first)
- [ ] All actions logged
- [ ] All escalations documented in `TEAM_MEETING.md` when required
- [ ] All applicable gates satisfied (`QUALITY_GATE_POLICY.md`)

---

## Index linkage

Listed in `INDEX_PROMPT.md` required reading order **§4**. Full sequence: `PROMPT_EXECUTION_RULES.md` (G-15).
