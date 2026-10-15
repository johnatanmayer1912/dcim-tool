# ESCALATION_MATRIX

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-05 |
| **last_updated** | 2026-05-31 |

**Related:** `ROLE_MATRIX.md` (G-04) · `TEAM_MEETING.md` (G-11) · `PROMPT_ACTIVATION_POLICY.md` (G-13)

## Purpose

Define how issues escalate across roles and when to involve additional reviewers.

---

## Matrix fields

Every escalation row MUST document:

| Field | Description |
|-------|-------------|
| **issue_type** | Category of problem or decision |
| **primary_role** | First owner to investigate and propose fix |
| **secondary_role** | Required collaborator or gate owner |
| **blocker_condition** | Whether work must stop until resolved (`Yes` / `No`) |
| **escalation_target** | Where unresolved issues go |
| **resolution_requirement** | Definition of done |

**Registry IDs** for roles: see `ROLE_MATRIX.md` (e.g. U-GOV-LIB, U-ARCH, U-COUNCIL).

---

## Escalation matrix

| issue_type | primary_role | secondary_role | blocker_condition | escalation_target | resolution_requirement |
|------------|--------------|----------------|-------------------|-------------------|------------------------|
| Prompt drift | Prompt Librarian (U-GOV-LIB) | Documentation Steward (U-LIB) | Yes | Team Meeting Council (U-COUNCIL) | Fix and sync registry, archive, docs |
| Architecture boundary change | System Architect (U-ARCH) | Lead Developer (U-ENG) | Yes | Team Meeting Council | Architect approval documented |
| Security-sensitive behavior | Security Reviewer (U-SEC) | Release Manager (U-REL) | Yes | Team Meeting Council | Mitigation implemented or release blocked |
| Observability gap | Observability Engineer (U-OBS) | Lead Developer (U-ENG) | No | Team Meeting Council | Instrumentation / diagnostics in place |
| Compatibility risk | QA Engineer (U-QA) | Release Manager (U-REL) | Yes | Team Meeting Council | Fix regression or documented waiver |
| Strategic opportunity | Product Strategist (U-PROD) | System Architect (U-ARCH) | No | Team Meeting Council | Roadmap / scope update in docs |
| Unresolved quality risk | QA Engineer (U-QA) | Release Manager (U-REL) | Yes | Team Meeting Council | Fix or explicit accept with log |
| Documentation gap | Documentation Steward (U-LIB) | Lead Developer (U-ENG) | No | Team Meeting Council | Docs updated (`CHANGELOG`, `docs/`) |
| Multiple role conflict | N/A | N/A | Yes | Team Meeting Council | Recorded decision in `TEAM_MEETING.md` |
| Uncertain ownership | N/A | N/A | No | Team Meeting Council | Owner role assigned in meeting log |

### Summary table (quick reference)

| Issue Type | Primary | Secondary | Blocker | Escalation | Resolution |
|------------|---------|-----------|---------|------------|------------|
| Prompt drift | Prompt Librarian | Documentation Steward | Yes | Team Meeting | Fix and sync |
| Architecture boundary change | System Architect | Lead Developer | Yes | Team Meeting | Architect approval |
| Security-sensitive behavior | Security Reviewer | Release Manager | Yes | Team Meeting | Mitigation or block |
| Observability gap | Observability Engineer | Lead Developer | No | Team Meeting | Instrumentation |
| Compatibility risk | QA Engineer | Release Manager | Yes | Team Meeting | Fix or approve |
| Strategic opportunity | Product Strategist | System Architect | No | Team Meeting | Roadmap update |
| Unresolved quality risk | QA Engineer | Release Manager | Yes | Team Meeting | Fix or accept |
| Documentation gap | Documentation Steward | Lead Developer | No | Team Meeting | Update docs |
| Multiple role conflict | N/A | N/A | Yes | Team Meeting | Decision |
| Uncertain ownership | N/A | N/A | No | Team Meeting | Assign owner |

---

## Severity levels (cross-cutting)

Use with issue-type matrix when impact spans categories:

| Level | Condition | Action |
|-------|-----------|--------|
| **L0** | Routine task, clear scope | RESYNC + relevant roles; no Team Meeting |
| **L1** | Doc/code mismatch | Documentation Steward + fix before continue |
| **L2** | Conflicting prompts/policies | Team Meeting entry; `PROMPT_GOVERNANCE_POLICY.md` precedence |
| **L3** | Data loss, security incident, production outage | Stop work; U-SEC; user notification; no release |
| **L4** | Breaking API/plugin contract fork | U-ARCH + CHANGE_MANAGEMENT + explicit user approval |

---

## Additional Team Meeting triggers

Escalate to **Team Meeting Council** (`TEAM_MEETING.md`) when:

- Two policies give incompatible instructions.
- Release requires skipping a quality gate (`QUALITY_GATE_POLICY.md`).
- Plugin registry vs runtime behavior disagree.
- `VERSION` ≠ UI/EXE branding without documented intent.
- Any row above with `blocker_condition: Yes` and no resolution within the task.

---

## Escalate to human owner

Required for (in addition to Team Meeting record):

- Credential handling or production device access model changes.
- Destructive git or force push to protected branches (user must request).
- Legal/licensing changes for bundled assets.
- L3/L4 severity with production or security impact.

---

## Default bias

When role relevance is uncertain: activate **RESYNC**, **Lead Developer**, **Documentation Steward**, and domain role (e.g. U-TOPO).  
When ownership is uncertain: use **Uncertain ownership** row → Team Meeting → assign owner.

---

## Resolution logging

All escalations with `blocker_condition: Yes` or Team Meeting involvement MUST log:

- issue_type, primary/secondary roles, escalation_target  
- resolution_requirement met (yes/no)  
- `TEAM_MEETING.md` link or action log path  

Template: `roles/_ACTION_LOG_SNIPPET.md` · Governance fields: `PROMPT_GOVERNANCE_POLICY.md` § Required governance action log

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set, with `ROLE_MATRIX.md`).
