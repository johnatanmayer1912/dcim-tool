# CHECK_SYSTEM_FOR_BUGS

| Field | Value |
|-------|-------|
| **Version** | 4.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | W-BUG-SWEEP |
| **Trigger** | User: **check system for bugs** |
| **Output root** | `docs/14-bug-reports/` |
| **last_updated** | 2026-05-31 |

**Invoke:** Paste this entire file into the AI IDE, or say: `check system for bugs`

**Policies:** G-00, G-01, G-07, G-11, G-18 · **Council:** all R-* / U-* via combined prompts in `roles/combined/`

---

## Simple usage

User types: **check system for bugs**

The AI will automatically:

1. Read all master prompts (INDEX read order `00`–`15` + applicable roles `16`–`25`)
2. Activate **ALL** council roles automatically
3. Scan the entire system
4. Create structured bug report folder at `docs/14-bug-reports/`
5. Output all fix prompts ready to copy-paste

---

## Mission

Systematically scan the program for bugs, functionality issues, gaps, and improvements. Create a **dedicated structured bug report folder** at `docs/14-bug-reports/`. **Fully engage the entire team** where each role actively participates. Output **exact copy-paste-ready prompts** for fix, validation, documentation, and version update for each bug.

---

## Automatic role activation (mandatory)

This check **MUST** automatically activate **ALL** roles:

| Role | Combined invoke | Scan focus |
|------|-----------------|------------|
| Prompt Librarian | `ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` | Prompt system integrity |
| System Architect | `ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` | Architecture and structure |
| Lead Developer | `ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` | Code and implementation |
| QA Engineer | `ROLE_QA_ENGINEER_USAGE_PROMPT.md` | Functionality, regression |
| Security Reviewer | `ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` | Security vulnerabilities |
| Observability Engineer | `ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` | Logs, metrics, diagnostics |
| Documentation Steward | `ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` | Documentation completeness |
| Release Manager | `ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` | Release / rollback risk |
| Product Strategist | `ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` | Strategic gaps, advantage |
| Team Meeting Council | `ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` | Synthesize all findings |

---

## Resync procedure (mandatory before starting)

Every role **MUST** resync:

1. Read `INDEX_PROMPT.md`
2. Read `PROMPT_REGISTRY.md`
3. Read `03_PROMPT_USAGE_MANUAL.md`
4. Read `04_PROMPT_ACTIVATION_POLICY.md`
5. Read all relevant policies (G-03–G-11, G-16, G-17, G-18)
6. Read latest codebase (hot paths in registry Application Hot Paths)
7. Read latest release notes (`CHANGELOG.md`, `VERSION`)
8. Read latest bug fixes (CHANGELOG **Fixed**)
9. Read all relevant documentation (`docs/`, `LIBRARIAN_MANDATE.md`)
10. Read relevant role prompts and usage guides (`roles/combined/`)

---

## Step 1: Create bug report folder structure

Create (or refresh) under `docs/14-bug-reports/` for this run:

```text
docs/14-bug-reports/
├── README.md
├── 00-executive-summary.md
├── 01-prioritized-bug-list.md
├── 02-bug-details/
│   └── BUG-0001-[short-description]/
│       ├── bug-report.md
│       ├── fix-prompt.md
│       ├── validation-prompt.md
│       ├── documentation-prompt.md
│       ├── version-update-prompt.md
│       ├── action-log.md
│       └── role-contributions.md
├── 03-team-contributions/
│   ├── librarian-contributions.md
│   ├── architect-contributions.md
│   ├── developer-contributions.md
│   ├── qa-contributions.md
│   ├── security-contributions.md
│   ├── observability-contributions.md
│   ├── documentation-contributions.md
│   ├── release-contributions.md
│   ├── product-contributions.md
│   └── team-meeting-synthesis.md
├── 04-fix-workflow/
│   ├── fix-sequence.md
│   ├── quality-gates.md
│   └── role-activation-plan.md
├── 05-validation-reports/
├── 06-documentation-updates/
└── 07-version-history/
```

Use `_SCAFFOLD/` templates in `docs/14-bug-reports/_SCAFFOLD/` when creating each `BUG-*` folder.

**Create folder structure BEFORE scanning.**

---

## Step 2: Each role scans for bugs

### Prompt Librarian

Outdated prompts, missing prompts, prompt drift, missing usage guides, registry inconsistencies.

### System Architect

Architecture violations, module boundaries, dependency problems, coupling, structural weaknesses.

### Lead Developer

Code bugs, logic errors, implementation issues, dead code, deprecated APIs, maintainability.

### QA Engineer

Functional bugs, regression risks, compatibility, edge cases, test coverage gaps.

### Security Reviewer

Vulnerabilities, authZ/authN, secrets handling, external integration risks.

### Observability Engineer

Missing logs/metrics/traces, poor error messages, hard-to-diagnose failures, monitoring gaps.

### Documentation Steward

Missing/outdated/inconsistent docs, missing usage guidance, missing CHANGELOG entries.

### Release Manager

Release risks, rollback gaps, validation gaps, deployment issues, production readiness.

### Product Strategist

Strategic gaps, competitive disadvantages, UX issues, feature gaps, roadmap misalignment.

Each role writes findings to `03-team-contributions/<role>-contributions.md`.

---

## Step 3: Team Meeting Council synthesizes

After all roles report, **R-COUNCIL** MUST:

1. Consolidate all findings
2. Remove duplicates
3. Resolve conflicts
4. Prioritize by severity and impact
5. Assign owners
6. Create `01-prioritized-bug-list.md`
7. Generate exact fix prompts for each bug
8. Record synthesis in `03-team-contributions/team-meeting-synthesis.md`

Use **Required Issue Schema** from `TEAM_MEETING_COUNCIL.md` (R-COUNCIL).

---

## Step 4: Create bug artifacts (per bug)

For each bug, create `02-bug-details/BUG-NNNN-[short-description]/`:

| File | Content |
|------|---------|
| `bug-report.md` | Metadata, description, root cause, impact, repro, priority, all role findings |
| `fix-prompt.md` | **EXACT copy-paste** prompt for AI IDE to fix |
| `validation-prompt.md` | **EXACT copy-paste** prompt to validate fix |
| `documentation-prompt.md` | **EXACT copy-paste** prompt to update docs |
| `version-update-prompt.md` | **EXACT copy-paste** prompt for VERSION + registry |
| `action-log.md` | Actions taken for this bug |
| `role-contributions.md` | Per-role findings for this bug |

---

## Step 5: Create executive summary

Populate `00-executive-summary.md`:

```markdown
# EXECUTIVE SUMMARY

## System check results
- Date: [YYYY-MM-DD]
- Roles participated: All council roles
- Total bugs found: [number]

## Bug summary by severity
| Severity | Count |
|----------|-------|
| Critical | [n] |
| High | [n] |
| Medium | [n] |
| Low | [n] |

## Top priority bugs (P0 — fix immediately)
| BUG-ID | Description | Severity | Owner |
|--------|-------------|----------|-------|
| BUG-0001 | [desc] | Critical | [role] |

## Recommended fix sequence
1. BUG-0001 — [reason]
2. BUG-0002 — [reason]

## Team participation summary
- Prompt Librarian: [summary]
- System Architect: [summary]
- Lead Developer: [summary]
- QA Engineer: [summary]
- Security Reviewer: [summary]
- Observability Engineer: [summary]
- Documentation Steward: [summary]
- Release Manager: [summary]
- Product Strategist: [summary]
```

Populate `04-fix-workflow/` (fix-sequence, quality-gates per G-07, role-activation-plan per G-13).

---

## Project scan checklist (Network Swiss Tool Pro)

Run after folder creation:

| Check | Command / path |
|-------|----------------|
| Pre-build | `_prebuild.py` |
| VPC validation | `tests/validate_vpc_member_interfaces.py` |
| Web health | `/health`, main routes |
| Jinja safety | `modules/web/templates/index.html` |
| Plugins | `modules/plugins/` load |
| Diagnostics | `topology_diagnostics_*`, `01`–`07` JSON |
| Version parity | `VERSION` vs `docs/README.md` vs CHANGELOG top |

---

## Expected output

After running this prompt, the AI **MUST** confirm:

1. Folder structure created at `docs/14-bug-reports/`
2. **Executive summary** with total bugs found
3. **Prioritized bug list**
4. **Per bug:** bug-report, fix, validation, documentation, version-update prompts (copy-paste ready), action-log, role-contributions
5. **Team contributions** (all 9 role files + synthesis)
6. **Fix workflow** (sequence + quality gates)
7. Hub action log: `docs/13-master-prompts/action-logs/YYYY-MM-DD_bug-sweep.md`

---

## How to use the output

1. Read `00-executive-summary.md`
2. Review `01-prioritized-bug-list.md`
3. For each bug, open `02-bug-details/BUG-*/`
4. Copy `fix-prompt.md` → run in AI IDE
5. Copy `validation-prompt.md` → run after fix
6. Copy `documentation-prompt.md` → run if behavior changed
7. Copy `version-update-prompt.md` → run when releasing
8. Fill `action-log.md`
9. Next bug

---

## Mandatory rules

1. Create folder structure **before** scanning
2. **ALL** roles MUST participate actively
3. Each role MUST document findings in `03-team-contributions/`
4. Team Meeting Council MUST synthesize all findings
5. Each bug MUST have a complete folder with all artifacts
6. Each bug MUST have exact copy-paste-ready prompts
7. Bugs MUST be prioritized by severity and impact
8. All actions MUST be logged
9. All quality gates MUST be enforced (G-07)
10. Registry and VERSION updated after fixes (user-requested commit only)

---

## Success criteria

- [ ] Folder structure at `docs/14-bug-reports/`
- [ ] All roles participated
- [ ] All findings documented
- [ ] All bugs have complete artifacts
- [ ] All bugs have fix / validation / documentation / version prompts
- [ ] Executive summary and prioritized list created
- [ ] Quality gates documented in `04-fix-workflow/quality-gates.md`
- [ ] Actions logged (hub + per-bug)
- [ ] Team fully synced and engaged
