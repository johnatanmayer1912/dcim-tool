# PROMPT COMMAND CENTER

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Status** | active |
| **Owner** | Prompt Librarian (R-GOV-LIB) + Documentation Steward (R-LIB) |
| **Registry ID** | G-CC |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.29 |

**Purpose:** Single entry point for **what to type**, **which roles activate**, **execution order**, and **mandatory documentation sync**. Use this before any multi-step or release task.

**Read first:** `INDEX_PROMPT.md` (G-00) · **Absolute rules:** `GLOBAL_MASTER_PROMPT_RULES.md` (G-18)

---

## How to use this file

1. Pick a **command** from the tables below (natural language or slash form).
2. The AI **MUST** load every role in the **Activates** column — not only what you named.
3. The AI **MUST** run roles in **dependency order** (see § Execution order).
4. The AI **MUST** complete **§ Mandatory documentation sync** before marking work done — **no separate “doc sync” command required**.
5. For disaster recovery (code lost), use **§ Rebuild from docs only**.

---

## Mandatory documentation sync (hardcoded — every code change)

**This is NOT optional.** It runs automatically with **every** implementation, fix, or release — not only when the user says “update documentation.”

| Step | Owner | Action |
|------|-------|--------|
| 1 | R-ENG | After code change: identify affected paths using `15-rebuild-roadmap/SYNC_PROTOCOL.md` |
| 2 | R-LIB | Update ongoing docs: `CHANGELOG.md`, `docs/02-codebase/*`, feature/ops guides, `docs/README.md` version line |
| 3 | R-RECON | Update affected `15-rebuild-roadmap/**/P*.md` prompts + `SYNC_PROTOCOL.md` row if new module |
| 4 | R-GOV-LIB | If prompts/policies changed: `PROMPT_REGISTRY.md`, action log |
| 5 | R-QA | Confirm tests/prebuild; note gaps in action log |
| 6 | All | Log in `action-logs/YYYY-MM-DD_<slug>.md` |

**Procedure detail:** `CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md` (PROC-CCDU)  
**Snippet for role prompts:** `roles/_MANDATORY_SYNC_FOOTER.md`

---

## Execution order (dependency chain)

```
RESYNC → R-PROD (scope) → R-ARCH → R-ENG → R-QA → R-SEC (if security) → R-OBS (if ops/logs)
       → R-LIB + R-RECON (doc + rebuild, parallel) → R-GOV-LIB (if prompts) → R-REL (if release) → R-COUNCIL (if conflict)
```

**Bug sweep:** All council roles — see `roles/CHECK_SYSTEM_FOR_BUGS.md`.

---

## All-in-one commands (copy-paste)

### Daily development

| You type | Activates | Delivers |
|----------|-----------|----------|
| **implement [feature/fix]** | RESYNC, R-ARCH, R-ENG, R-QA, R-LIB, R-RECON | Code + tests + CHANGELOG + docs + rebuild prompt touch |
| **fix bug [BUG-ID]** | R-ENG, R-QA, R-LIB, R-RECON | `14-bug-reports/02-bug-details/[ID]/fix-prompt.md` + validation + doc sync |
| **validate fix [BUG-ID]** | R-QA, R-LIB | `validation-prompt.md` + regression evidence |

### Quality & architecture

| You type | Activates | Delivers |
|----------|-----------|----------|
| **check system for bugs** / **/check-system-bugs** | **All council roles** | `docs/14-bug-reports/W-BUG-SWEEP-*.md` + prioritized list + fix prompts |
| **code review** / **/code-review** | R-ARCH → R-ENG → R-QA → R-LIB | Review report + architecture validation + test analysis + doc sync |
| **review architecture** | R-ARCH, R-LIB | Architecture compliance report |
| **security review** | R-SEC, R-ENG, R-LIB | Security findings + doc notes |

### Documentation & governance

| You type | Activates | Delivers |
|----------|-----------|----------|
| **`/full-docs-sync`** · **full docs sync** | R-GOV-LIB, R-LIB, R-RECON, R-ARCH, R-QA, R-REL | **Complete** doc + rebuild + registry + link validation — `FULL_DOCS_SYNC.md` |
| **sync documentation** / **update documentation** | R-LIB, R-GOV-LIB, R-RECON | Quick parity pass (use full-docs-sync for complete) |
| **doc audit** / **/doc-audit** | R-GOV-LIB, R-LIB, R-RECON | Gap analysis + `DOCUMENTATION_MASTER_INDEX` validation |
| **govern prompts** | R-GOV-LIB, R-LIB | Registry + combined roles + INDEX linkage |

### Holistic council (360°)

| You type | Activates | Delivers |
|----------|-----------|----------|
| **`/find-all-bugs-and-fix`** | **All council** | Sweep + severity + fix prompts + `FIX-ALL-CONSOLIDATED-PROMPT.md` — `FIND_ALL_BUGS_AND_FIX.md` |
| **`execute fix all from latest bug sweep`** | R-ENG → R-QA → R-LIB | Runs consolidated fix prompt in priority order |
| **`/ui-ux-audit`** · **ui ux check** | R-PROD, R-ENG, R-QA, R-ARCH, R-COUNCIL | PC/offline UX report + fix prompts — `UI_UX_AUDIT.md` |
| **`/next-steps`** · **what are the next steps** | **All council** | NEXT-* roadmap + implementation prompts — `NEXT_STEPS_COUNCIL.md` |

**HTML manual (offline):** `docs/17-roles-by-command/COMMAND_MANUAL.html`

### Release & build

| You type | Activates | Delivers |
|----------|-----------|----------|
| **prepare release** | R-REL, R-QA, R-LIB, R-RECON, R-ENG | VERSION, CHANGELOG, release notes, EXE, smoke checklist |
| **build exe** | R-ENG, R-QA, R-REL | `_prebuild.py` PASS → PyInstaller → `dist/*_OFFLINE.exe` |

### Disaster recovery (docs folder only)

| You type | Activates | Delivers |
|----------|-----------|----------|
| **rebuild from docs** / **reconstruct program** | R-RECON, R-ARCH, R-ENG, R-QA, R-LIB | Phased P01–P42 per `15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md` |

---

## Mega-commands (full pipeline — one message)

Use when you want the entire team chain without naming roles.

### `/full-fix-and-ship [BUG-ID or feature description]`

```
ACTIVATE: RESYNC, R-ARCH, R-ENG, R-QA, R-SEC (if creds/auth), R-LIB, R-RECON, R-REL (if VERSION change)

SEQUENCE:
1. R-ARCH — Confirm design / module boundaries
2. R-ENG — Implement + unit tests
3. R-QA — pytest + _prebuild.py
4. R-LIB — CHANGELOG, ops/feature docs, API/CODE_INVENTORY as needed
5. R-RECON — Update 15-rebuild-roadmap prompts per SYNC_PROTOCOL.md
6. R-REL — VERSION, release notes, EXE if requested

MANDATORY: CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md checklist complete before done.
```

### `/code-review-doc-sync`

```
ACTIVATE: R-ARCH → R-ENG → R-QA → R-LIB (same as code review + documentation sync command)

DELIVERABLES: Code review report, architecture validation, test coverage, updated docs, cross-ref validation.
```

### `/release-v[X.Y.Z]`

```
ACTIVATE: R-REL, R-QA, R-LIB, R-RECON, R-ENG

SEQUENCE:
1. All tests green + prebuild PASS
2. VERSION + CHANGELOG + RELEASE_NOTES
3. docs/README.md version line + DOCUMENTATION_MASTER_INDEX
4. Rebuild roadmap Application Version bump
5. Build EXE + exe-smoke-checklist.md
6. Action log
```

---

## Role quick reference

| ID | Combined prompt | Primary mission |
|----|-----------------|-----------------|
| R-GOV-LIB | `roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` | Prompts, registry, audits |
| R-LIB | `roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` | Doc/code parity |
| R-ARCH | `roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` | Architecture |
| R-ENG | `roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` | Implementation |
| R-QA | `roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md` | Tests, gates |
| R-SEC | `roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` | Security |
| R-OBS | `roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` | Logs, diagnostics |
| R-REL | `roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` | Ship, VERSION |
| R-PROD | `roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` | Scope, UX |
| R-RECON | `roles/combined/ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md` | 1:1 rebuild roadmap |
| R-COUNCIL | `roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` | Conflicts |

**Workflow (not a council role):** `roles/CHECK_SYSTEM_FOR_BUGS.md`

---

## Rebuild from docs only

When **all code is lost** but `docs/` remains:

1. Open `docs/15-rebuild-roadmap/README.md`
2. Run batches from `docs/15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md` (**max 4 prompts per batch**, 30s pause between batches)
3. Validate after each phase using prompts P28–P30 and `_prebuild.py`
4. Do **not** send all 42 prompts in one IDE message (DDOS prevention)

**Master index:** `15-rebuild-roadmap/00-RECONSTRUCTION_INDEX.md`  
**Code→prompt map:** `15-rebuild-roadmap/SYNC_PROTOCOL.md`

---

## File map (governance hub)

| Need | Path |
|------|------|
| Entry & read order | `INDEX_PROMPT.md` |
| This command center | `PROMPT_COMMAND_CENTER.md` |
| User simple commands | `FINAL_OPERATING_INSTRUCTION.md` |
| 20+ absolute rules | `GLOBAL_MASTER_PROMPT_RULES.md` |
| Execution sequence | `PROMPT_EXECUTION_RULES.md` |
| Doc policy | `DOCUMENTATION_POLICY.md` |
| Code change → docs | `CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md` |
| Docs folder guide | `../DOCS_CANONICAL_MAP.md` |
| Master doc index | `../DOCUMENTATION_MASTER_INDEX.md` |

---

## Success criteria (every task)

- [ ] Relevant roles activated (not only user-named roles)
- [ ] Dependency order followed
- [ ] Tests/prebuild considered (R-QA)
- [ ] **Documentation sync completed** (R-LIB + R-RECON) — hardcoded
- [ ] Rebuild roadmap touched if code changed (R-RECON)
- [ ] Action log if meaningful scope
- [ ] Registry updated if prompts changed (R-GOV-LIB)
