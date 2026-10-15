# Roles folder

How the AI loads **council roles**, **domain usage**, and **workflows**.

## Council roles (invoke one file)

**Canonical:** `combined/ROLE_*_USAGE_PROMPT.md` — Part 1 = role mission/authority, Part 2 = ROLE USAGE (when/how).

| Registry | File |
|----------|------|
| R-GOV-LIB | [combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md](combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md) |
| R-ARCH | [combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md](combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md) |
| R-ENG | [combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md](combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md) |
| R-QA | [combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md](combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md) |
| R-SEC | [combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md](combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md) |
| R-OBS | [combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md](combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md) |
| R-LIB | [combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md](combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md) |
| R-REL | [combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md](combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md) |
| R-PROD | [combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md](combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md) |
| R-COUNCIL | [combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md](combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md) |

Do **not** look for separate `PROMPT_LIBRARIAN.md` / `*_USAGE.md` pairs in this folder — they were merged (registry **4.0.3**).

## Domain usage (separate guides)

| ID | File | When |
|----|------|------|
| U-RESYNC | [RESYNC_USAGE.md](RESYNC_USAGE.md) | Before significant work; platform source `PLATFORM_PROMPTS/RESYNC.md` |
| U-TOPO | [TOPOLOGY_USAGE.md](TOPOLOGY_USAGE.md) | VPC, topology, HTML maps, diagnostics |
| U-ORCH | [ORCHESTRATOR_USAGE.md](ORCHESTRATOR_USAGE.md) | Plugins, batch workflows |
| U-UI | [UI_DYNAMO_USAGE.md](UI_DYNAMO_USAGE.md) | Flask/Jinja/web UI |

## Workflows

| ID | File | Trigger |
|----|------|---------|
| W-BUG-SWEEP | [CHECK_SYSTEM_FOR_BUGS.md](CHECK_SYSTEM_FOR_BUGS.md) | `check system for bugs` |
| W-DOC-SYNC | [FULL_DOCS_SYNC.md](FULL_DOCS_SYNC.md) | `/full-docs-sync` |
| W-BUG-FIX-ALL | [FIND_ALL_BUGS_AND_FIX.md](FIND_ALL_BUGS_AND_FIX.md) | `/find-all-bugs-and-fix` |
| W-UI-UX | [UI_UX_AUDIT.md](UI_UX_AUDIT.md) | `/ui-ux-audit` |
| W-NEXT-STEPS | [NEXT_STEPS_COUNCIL.md](NEXT_STEPS_COUNCIL.md) | `/next-steps` |

**Offline manual:** [COMMAND_MANUAL.html](../../17-roles-by-command/COMMAND_MANUAL.html)

## Meta

| File | Purpose |
|------|---------|
| [_USAGE_GUIDE_STANDARD.md](_USAGE_GUIDE_STANDARD.md) | G-14 template for usage sections |
| [_ACTION_LOG_SNIPPET.md](_ACTION_LOG_SNIPPET.md) | Action log fields |

## AI behavior

1. Read [INDEX_PROMPT.md](../INDEX_PROMPT.md) and policies before acting.
2. Infer **all** relevant roles from the task (G-13) — load each **combined** council file that applies.
3. Read Part 1 then Part 2 in each combined file; follow dependency chain in [PROMPT_ACTIVATION_POLICY.md](../PROMPT_ACTIVATION_POLICY.md).
4. Log meaningful work under [action-logs/](../action-logs/).
