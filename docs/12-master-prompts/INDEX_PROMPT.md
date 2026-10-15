# INDEX_PROMPT

| Field | Value |
|-------|-------|
| **Version** | 4.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-00 |
| **last_updated** | 2026-06-10 (command center 1.0) |

---

## Purpose

**MANDATORY** entry point for the master prompt system. **READ THIS FIRST** before any work.

---

## Required reading order

The AI **MUST** read in this order (canonical paths only):

| Step | File |
|------|------|
| 1 | `GLOBAL_MASTER_PROMPT_RULES.md` (G-18) |
| 2 | `PROMPT_COMMAND_CENTER.md` (G-CC) — **commands, all-in-one, mandatory doc sync** |
| 3 | This file (`INDEX_PROMPT.md`) |
| 4 | `PROMPT_REGISTRY.md` (G-01) |
| 5 | `PROMPT_USAGE_MANUAL.md` (G-02) |
| 6 | `PROMPT_ACTIVATION_POLICY.md` (G-13) |
| 7 | `ROLE_USAGE_STANDARD.md` (G-14) |
| 8 | `PROMPT_EXECUTION_RULES.md` (G-15) |
| 9 | Policies G-03–G-11 (as applicable) | See [Policies (G-03–G-11)](#policies-g-03g-11) |
| 10 | Council roles (as applicable) | `roles/combined/ROLE_*_USAGE_PROMPT.md` — see [Council roles](#council-roles) |
| 11 | Relevant **project documentation** | `docs/`, `LIBRARIAN_MANDATE.md`, `14-roadmap/` if rebuilding |
| 12 | Latest **codebase changes** | Hot paths, diff, `VERSION` |
| 13 | Latest **release notes** | `CHANGELOG.md`, bug fixes |

**Then execute:** identify roles → dependency order → action logs → registry → documentation (G-15 Phase B).

**Extended:** `FINAL_OPERATING_INSTRUCTION.md` (G-17) · full `PLATFORM_PROMPTS/` for major RESYNC · `roles/CHECK_SYSTEM_FOR_BUGS.md` when user requests system bug check.

### Policies (G-03–G-11)

| File | ID |
|------|-----|
| `PROMPT_GOVERNANCE_POLICY.md` | G-03 |
| `ROLE_MATRIX.md` | G-04 |
| `ESCALATION_MATRIX.md` | G-05 |
| `DOCUMENTATION_POLICY.md` | G-06 |
| `QUALITY_GATE_POLICY.md` | G-07 |
| `CHANGE_MANAGEMENT_POLICY.md` | G-08 |
| `RELEASE_MANAGEMENT_POLICY.md` | G-09 |
| `COMPETITIVE_ADVANTAGE_POLICY.md` | G-10 |
| `TEAM_MEETING.md` | G-11 |

Also when relevant: `PROMPT_MIGRATION_SYNC.md` (G-16), `FINAL_OPERATING_INSTRUCTION.md` (G-17).

### Council roles

Invoke **one combined file** per role (`roles/combined/`). Part 1 = role; Part 2 = usage.

| Combined file | Registry |
|---------------|----------|
| `ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` | R-GOV-LIB |
| `ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` | R-ARCH |
| `ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` | R-ENG |
| `ROLE_QA_ENGINEER_USAGE_PROMPT.md` | R-QA |
| `ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` | R-SEC |
| `ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` | R-OBS |
| `ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` | R-LIB |
| `ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` | R-REL |
| `ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` | R-PROD |
| `ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` | R-COUNCIL |

Platform sources: `docs/02-codebase/PLATFORM_PROMPTS/` (never delete).

### Workflows

| File | ID | Trigger |
|------|-----|---------|
| `roles/CHECK_SYSTEM_FOR_BUGS.md` | W-BUG-SWEEP | `check system for bugs` |
| `roles/FULL_DOCS_SYNC.md` | W-DOC-SYNC | `/full-docs-sync` |
| `roles/FIND_ALL_BUGS_AND_FIX.md` | W-BUG-FIX-ALL | `/find-all-bugs-and-fix` |
| `roles/UI_UX_AUDIT.md` | W-UI-UX | `/ui-ux-audit` |
| `roles/NEXT_STEPS_COUNCIL.md` | W-NEXT-STEPS | `/next-steps` |

**Command manual:** `docs/17-roles-by-command/COMMAND_MANUAL.html`

---

## Mandatory rules

1. Read this file before any other prompt or action.
2. Read `PROMPT_REGISTRY.md` before any change.
3. Read original prompts in `docs/02-codebase/PLATFORM_PROMPTS/`.
4. **NEVER** delete original prompts.
5. Copy originals into `docs/12-master-prompts/` before enhancement.
6. **SYNC** forward, don't replace history.
7. Every council role has **role + usage** in one combined file (G-14); domain roles keep separate `*_USAGE.md`.
8. Create an **action log** for every meaningful role invocation.
9. Apply correct **policy prompts** before work.
10. Use dependency chain: **architect → developer → QA → security → observability → documentation → release** (RESYNC / Product Strategist precede architect when scope changes).
11. Escalate unresolved conflicts to `TEAM_MEETING.md` (G-11).
12. **RESYNC** before every significant action.
13. AI **MUST** automatically identify and activate **all** relevant roles from task scope, not just user-named roles.
14. **IF** role relevance uncertain, err on the side of **inclusion and escalation**.

**Authoritative superset:** `GLOBAL_MASTER_PROMPT_RULES.md` (G-18) — 20 absolute rules.

---

## Role auto-activation rule (critical)

The AI **MUST** infer all relevant roles from task domain and system context.  
The AI **MUST NOT** rely only on roles explicitly named by the user.  
If a role's mission is relevant, it **MUST** be loaded, read, and applied.  
If role relevance is uncertain, the AI **MUST** err on the side of inclusion and escalation.

Full matrix: `PROMPT_ACTIVATION_POLICY.md` (G-13).

---

## Simple commands the user can type

**Authoritative tables:** **`PROMPT_COMMAND_CENTER.md` (G-CC)** · **`FINAL_OPERATING_INSTRUCTION.md` (G-17)**

| User types | AI does |
|------------|---------|
| **check system for bugs** | `roles/CHECK_SYSTEM_FOR_BUGS.md` → `docs/13-bug-reports/` (all roles) |
| **fix bug [ID]** | fix-prompt + **mandatory doc/rebuild sync** |
| **code review** / **code review doc sync** | R-ARCH → R-ENG → R-QA → R-LIB (+ R-RECON) |
| **rebuild from docs** | `14-roadmap/DISASTER_RECOVERY_COMMAND.md` (one batch at a time) |
| **prepare release** / **/release-vX.Y.Z** | R-REL chain + rebuild index version bump |
| **Any implementation task** | Auto: R-ENG + R-QA + **R-LIB + R-RECON doc sync** (no separate command needed) |

---

## Project mission

Build the most capable, maintainable, extensible, reliable, and professionally engineered **network management platform in the world**.

Mission, vision, and engineering principles (full text): `GLOBAL_MASTER_PROMPT_RULES.md` (G-18).

---

## Required outputs before work

- Relevant prompts identified
- Relevant policies identified
- Relevant docs identified
- Risks identified
- Approval chain identified
- Next action defined

---

## Behavioral standard

The prompt system must support enterprise-grade maintainability, safety, observability, compatibility, and strategic product growth while preserving **legacy prompt intent**.

---

## Local paths

| Asset | Path |
|-------|------|
| Command center | `docs/12-master-prompts/PROMPT_COMMAND_CENTER.md` |
| Rebuild (disaster) | `docs/14-roadmap/` |
| Master hub | `docs/12-master-prompts/` |
| Bug sweep output | `docs/13-bug-reports/` (prompt: `roles/CHECK_SYSTEM_FOR_BUGS.md`) |
| Bug scaffolds | `docs/13-bug-reports/_SCAFFOLD/` |
| Council roles (canonical) | `docs/12-master-prompts/roles/combined/` |
| Original prompts | `docs/02-codebase/PLATFORM_PROMPTS/` |
| Action logs | `docs/12-master-prompts/action-logs/` |
| Version / changelog | `/VERSION`, `/CHANGELOG.md` |
