# FINAL OPERATING INSTRUCTION

| Field | Value |
|-------|-------|
| **Version** | 4.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-17 |
| **last_updated** | 2026-06-10 |

**Absolute rules:** `GLOBAL_MASTER_PROMPT_RULES.md` (G-18) — **24 rules**  
**Command center:** `PROMPT_COMMAND_CENTER.md` (G-CC) — **start here for all-in-one commands**  
**Entry & read order:** `INDEX_PROMPT.md` (G-00) · **Registry:** `PROMPT_REGISTRY.md` (G-01)  
**Execution:** `PROMPT_EXECUTION_RULES.md` (G-15) · **Activation:** `PROMPT_ACTIVATION_POLICY.md` (G-13)

This file is the **operational IDE contract** — how to run day-to-day. For full command tables and mega-commands, use **G-CC**. When detail is needed, follow linked policies and role prompts.

---

## Simple usage for user

The user can type these simple commands:

| User types | AI does |
|------------|---------|
| **check system for bugs** | `CHECK_SYSTEM_FOR_BUGS.md` → all roles → `14-bug-reports/` |
| **fix bug [ID]** | fix-prompt + R-ENG + R-QA + **auto doc/rebuild sync** (R-LIB, R-RECON) |
| **code review doc sync** | R-ARCH → R-ENG → R-QA → R-LIB (see G-CC) |
| **rebuild from docs** | `15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md` — **one batch only** |
| **/full-fix-and-ship** | Full chain per `PROMPT_COMMAND_CENTER.md` |
| **prepare release** | R-REL + R-QA + R-LIB + R-RECON + EXE |
| **Any code change** | R-ENG + R-QA + **R-LIB + R-RECON** (mandatory — no separate doc command) |
| **`/full-docs-sync`** | Full documentation + rebuild parity |
| **`/find-all-bugs-and-fix`** | All roles → bugs + fix-all prompt |
| **`/ui-ux-audit`** | PC/offline UI/UX holistic check |
| **`/next-steps`** | Council 360° improvement roadmap |

**Full tables:** `PROMPT_COMMAND_CENTER.md` · **HTML:** `docs/17-roles-by-command/COMMAND_MANUAL.html`

Bug sweep prompt: `roles/CHECK_SYSTEM_FOR_BUGS.md` only (no duplicate under `combined/`).

---

## The AI must

- Keep all original prompts (`docs/02-codebase/PLATFORM_PROMPTS/` — never delete)
- Sync them into `docs/13-master-prompts/`
- Enhance them according to each role's mission
- Create usage/explanation prompts for each role (G-14; `roles/combined/ROLE_*_USAGE_PROMPT.md`)
- Preserve history and version lineage (G-16, archive-first)
- Maintain registry accuracy (`PROMPT_REGISTRY.md`)
- Enforce the policy chain (G-03–G-11, G-13–G-18)
- Apply quality gates and change management (G-07, G-08)
- Evaluate competitive advantage periodically (G-10, R-PROD)
- **Automatically activate all relevant roles even without explicit user instruction**
- Never let legacy intent be lost
- Elaborate professionally on each prompt
- Take only updated information from prompts (forward sync)
- Add new roles as needed with updated usage instructions and registry entries

---

## Mission

Build the most capable, maintainable, extensible, reliable, and professionally engineered **network management platform in the world**.

---

## Success criteria

- All prompts created and registered
- All roles elaborated professionally
- All usage guides created
- All policies enforced
- All actions logged (`action-logs/`)
- All documentation updated when behavior changes
- All legacy intent preserved
- All relevant roles activated automatically
- All gates satisfied (or Team Meeting waiver per G-11)
- **System simple to use for continuous development** (simple commands table above)

---

## Automatic role activation

The IDE **must not** wait for the user to name every role.

| Signal | Activate (minimum) |
|--------|-------------------|
| Any code/behavior change | RESYNC, R-ENG, R-QA, **R-LIB, R-RECON** (ongoing docs + rebuild roadmap) |
| Feature / scope | R-PROD, R-ARCH, then chain |
| Secrets / auth / exports | R-SEC |
| Logs / diagnostics / 500s | R-OBS |
| Near release / EXE | R-REL + applicable gates |
| Prompt/registry change | R-GOV-LIB, R-LIB |
| Multi-domain conflict | R-COUNCIL |
| Full bug sweep | **All** council roles (see CHECK_SYSTEM_FOR_BUGS) |

Full matrix: `PROMPT_ACTIVATION_POLICY.md` · Order: `PROMPT_EXECUTION_RULES.md`

---

## Policy chain (enforce)

| ID | Policy |
|----|--------|
| G-03 | Prompt governance |
| G-04 | Role matrix |
| G-05 | Escalation |
| G-06 | Documentation |
| G-07 | Quality gates |
| G-08 | Change management |
| G-09 | Release management |
| G-10 | Competitive advantage |
| G-11 | Team meeting |
| G-13 | Role activation |
| G-14 | Role / usage standards |
| G-15 | Execution rules |
| G-16 | Migration / sync |
| G-18 | Global master rules (20 absolutes) |

---

## Council roles (single-file invoke)

| R-* | Combined prompt |
|-----|-----------------|
| R-GOV-LIB | `roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` |
| R-ARCH | `roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` |
| R-ENG | `roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` |
| R-QA | `roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md` |
| R-SEC | `roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` |
| R-OBS | `roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` |
| R-LIB | `roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` |
| R-REL | `roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` |
| R-PROD | `roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` |
| R-COUNCIL | `roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` |

Workflow: `roles/CHECK_SYSTEM_FOR_BUGS.md` (not a council role; full-team sweep).

---

## Required outputs (every meaningful task)

- Relevant prompts, policies, and docs identified (RESYNC)
- Applicable roles activated and executed in dependency order
- Action log in `action-logs/` when a role or gate applies
- Registry updated if prompts changed
- Documentation updated if behavior changed (`CHANGELOG.md`, `docs/`)
- Gates satisfied or explicit Team Meeting waiver (G-11)

---

## Sync and elaboration

- Read **source** (`PLATFORM_PROMPTS/`) and **archive** (`archive/platform-prompts-original/`)
- Merge **only updated intent** into master copies
- **Elaborate** professionally; do not shrink scope
- Record versions in registry change log

---

## Escalation

Unresolved conflict or missing gate → `15_TEAM_MEETING.md` / `TEAM_MEETING.md` via **U-COUNCIL**.

L3/L4 → stop work; `09_ESCALATION_MATRIX.md`; human path as required.
