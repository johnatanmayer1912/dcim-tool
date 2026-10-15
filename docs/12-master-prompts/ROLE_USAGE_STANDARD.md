# ROLE_USAGE_STANDARD

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-14 |
| **last_updated** | 2026-05-31 |

## Purpose

Define the standard structure for every role prompt and usage guide in the master prompt system.

**Implementation template:** `roles/_USAGE_GUIDE_STANDARD.md`  
**Registry:** `PROMPT_REGISTRY.md` · **Activation:** `PROMPT_ACTIVATION_POLICY.md`

---

## Every Role Prompt Must Include

Applies to prompts in `docs/02-codebase/PLATFORM_PROMPTS/` and any enhanced master copies under `docs/13-master-prompts/roles/` when created.

| # | Section | Content |
|---|---------|---------|
| 1 | **Mission** | Why the role exists; scope within Network Swiss Tool Pro |
| 2 | **Resync procedure** | What to read/verify before acting (scoped steps) |
| 3 | **When to use** | Triggers that require this role |
| 4 | **When not to use** | Exclusions; overlap with other roles |
| 5 | **Responsibilities** | Concrete duties during a task |
| 6 | **Authority** | What this role may decide vs recommend vs escalate |
| 7 | **Deliverables** | Artifacts, code, docs, gates |
| 8 | **Collaboration matrix** | Which roles before/after; handoffs |
| 9 | **Review requirements** | QA, security, doc, release gates that apply |
| 10 | **Escalation rules** | When to use Team Meeting Council / human |
| 11 | **Action log template** | Fields each invocation must record |
| 12 | **Success criteria** | Checklist before role is “done” |

**Platform prompts** (`ENGINEER.md`, `RESYNC.md`, etc.) are the behavioral source; usage guides in `roles/` MUST mirror sections 2–12 in elaborated form for the IDE.

---

## Every Role Usage Guide Must Include

Applies to every `docs/13-master-prompts/roles/*_USAGE.md` file.

| # | Required section | Maps from extended template |
|---|------------------|----------------------------|
| 1 | **When to invoke** | When to use + activation triggers |
| 2 | **Best practices** | Discipline and conventions |
| 3 | **Common scenarios** | Example scenarios (this repository) |
| 4 | **Expected result** | Expected outputs / deliverables |
| 5 | **Related roles** | Collaboration matrix (summary) |
| 6 | **Related policies** | G-* policy IDs and paths |
| 7 | **Common mistakes** | Anti-patterns |

### Recommended elaboration (professional quality)

Usage guides SHOULD also include (see `_USAGE_GUIDE_STANDARD.md`):

- Role purpose (mission summary)
- When not to use
- Required inputs
- Resync procedure (role-scoped)
- Escalation triggers
- Standard structured output (findings, recommendations, decisions, risks, action log)

---

## Professional Elaboration Rule

The AI MUST elaborate professionally on each role prompt to:

- clarify responsibilities
- expand scope where needed
- strengthen governance
- improve collaboration rules
- add missing policies
- ensure enterprise-grade quality

Elaboration MUST NOT contradict the original `PLATFORM_PROMPTS/` intent; forward-sync per `PROMPT_GOVERNANCE_POLICY.md`.

---

## Updated Information Rule

The program/AI will take only the **updated** information from the prompts and must elaborate professionally on each prompt and role.

- Prefer delta from `CHANGELOG.md`, registry change log, and git diff over stale conversation summary.
- Preserve legacy intent when elaborating.

---

## New Role Addition Rule

New roles MAY be added as needed, but:

- usage instructions MUST change accordingly (`roles/*_USAGE.md`)
- best practices MUST change accordingly
- `PROMPT_REGISTRY.md` MUST be updated (all 12 fields)
- `INDEX_PROMPT.md` MUST be updated if read order or rules change
- policies MUST be reviewed (`PROMPT_ACTIVATION_POLICY`, `ROLE_MATRIX`, gates)
- archive copy if sourced from `PLATFORM_PROMPTS/`

Workflow: `PROMPT_REGISTRY.md` § Required Registry Workflow.

---

## Standard Output Format

Every role invocation MUST produce structured output (in action log and/or task reply):

| Block | Content |
|-------|---------|
| **findings** | What was discovered in review |
| **recommendations** | Proposed actions not yet taken |
| **decisions** | Choices made (with rationale) |
| **risks** | Open risks, severity, mitigations |
| **action log** | Path under `action-logs/`; see template below |

---

## Action Log Template (per role)

Use in `docs/13-master-prompts/action-logs/YYYY-MM-DD_<slug>.md`:

```markdown
# Action Log — <Role name> (<prompt_id>)

**Date:** YYYY-MM-DD  
**Roles activated:** <list>  
**Why activated:** <1–2 sentences per PROMPT_ACTIVATION_POLICY>

## Findings
- 

## Recommendations
- 

## Decisions
- 

## Risks
- 

## Files reviewed
- 

## Files changed
- 

## Versions updated
- 

## Verified
- 

## Remains open
- 
```

Snippet copy: `roles/_ACTION_LOG_SNIPPET.md`

---

## Compliance

| Artifact | Standard |
|----------|----------|
| Council usage guides | 7 required sections + recommended elaboration |
| Platform `*_USAGE.md` / `P*.md` | Usage guide mirrors role prompt §1–12 where applicable |
| New role | Registry + usage + activation matrix row |
| AI task output | Standard output format when role was active |

---

## Index linkage

`INDEX_PROMPT.md` required reading order **§5** (after activation policy). Full sequence: `PROMPT_EXECUTION_RULES.md` (G-15) §6.
