# FIND_ALL_BUGS_AND_FIX

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Registry ID** | W-BUG-FIX-ALL |
| **Trigger** | `find all bugs and fix` · `/find-all-bugs-and-fix` |
| **Owner** | R-COUNCIL (orchestrates all roles) |
| **last_updated** | 2026-06-10 |

**Invoke:** Say **`find all bugs and fix`** or paste this file.

**Extends:** `CHECK_SYSTEM_FOR_BUGS.md` (W-BUG-SWEEP) with **fix phase** and **consolidated fix command**.

---

## Mission

Holistic **find → report → prioritize → fix** pipeline. Every council role scans; council synthesizes; output includes **per-bug fix prompts** AND **one mega-command to fix everything** in priority order.

---

## Phase A — FIND (all roles)

**Run full W-BUG-SWEEP** (`CHECK_SYSTEM_FOR_BUGS.md`):

1. Activate **ALL** roles: R-GOV-LIB, R-ARCH, R-ENG, R-QA, R-SEC, R-OBS, R-LIB, R-REL, R-PROD, R-COUNCIL
2. Create `docs/14-bug-reports/W-BUG-SWEEP-YYYY-MM-DD-v*.md`
3. Per role: `03-team-contributions/<role>-contributions.md`
4. R-COUNCIL: `01-prioritized-bug-list.md`, `team-meeting-synthesis.md`
5. Per bug folder: `02-bug-details/BUG-NNNN-*/` with scaffolds

### Required scan surfaces

| Role | Scan |
|------|------|
| R-ENG | `modules/`, `utils/`, parsers, race conditions |
| R-QA | `pytest`, `_prebuild.py`, HTML contracts, edge cases |
| R-ARCH | Module boundaries, coupling, plugin registry |
| R-SEC | Credentials, injection, API exposure |
| R-OBS | Logs, error messages, 500 paths |
| R-LIB | Doc/code drift vs VERSION |
| R-REL | EXE bootstrap, VERSION, dist layout |
| R-PROD | UX friction, missing engineer workflows |
| R-GOV-LIB | Prompt/registry drift |

---

## Phase B — REPORT (structured output)

**Executive summary** (`00-executive-summary.md`) MUST include:

| Column | Content |
|--------|---------|
| Bug ID | BUG-NNNN or NEW-* |
| Severity | Critical / High / Medium / Low |
| Title | One line |
| Root cause | Where in code |
| Fix summary | What to change |
| Owner role | R-ENG, etc. |
| Fix prompt | Path to `fix-prompt.md` |

**Prioritized table** in `01-prioritized-bug-list.md` — fix order: Critical → High → Medium → Low.

Each `fix-prompt.md` MUST be **copy-paste ready** for the IDE.

---

## Phase C — FIX (user choice)

### Option 1 — Fix one bug

```
fix bug BUG-NNNN
```

Runs `02-bug-details/BUG-NNNN/fix-prompt.md` + validate + doc sync.

### Option 2 — Fix all (mega-command)

After sweep completes, generate **`04-fix-workflow/FIX-ALL-CONSOLIDATED-PROMPT.md`** containing:

```markdown
# FIX ALL — Consolidated prompt (from sweep W-BUG-SWEEP-...)

ACTIVATE: R-ARCH → R-ENG → R-QA → R-LIB → R-RECON → R-REL (if VERSION bump)

Fix in this exact order:
1. [BUG-ID] — [title] — see 02-bug-details/BUG-.../fix-prompt.md
2. ...

After each fix:
- pytest + _prebuild.py
- Do not proceed if regression

After all fixes:
- /full-docs-sync
- /release-vX.Y.Z (if user requests ship)
```

User then types:

```
execute fix all from latest bug sweep
```

or copies `FIX-ALL-CONSOLIDATED-PROMPT.md` into chat.

### Option 3 — Auto-proceed (explicit)

If user said **"find all bugs and fix"** with **auto proceed**:

1. Complete Phase A + B
2. Execute Phase C Option 2 fixes in priority order without waiting
3. Stop only on blocking regression or R-COUNCIL escalation

---

## Deliverables checklist

- [ ] `W-BUG-SWEEP-*.md` full report
- [ ] `01-prioritized-bug-list.md` with severity
- [ ] Every bug: `fix-prompt.md`, `validation-prompt.md`, `documentation-prompt.md`
- [ ] `04-fix-workflow/FIX-ALL-CONSOLIDATED-PROMPT.md`
- [ ] `04-fix-workflow/fix-sequence.md` (ordered IDs)
- [ ] `team-meeting-synthesis.md` with council sign-off
- [ ] Action log in `13-master-prompts/action-logs/`

---

## Success criteria

- [ ] All roles contributed
- [ ] Every finding has severity + owner
- [ ] Fix prompts exist for all Critical/High (and Medium if time)
- [ ] Consolidated fix-all prompt generated
- [ ] If auto-fix: pytest green + doc sync before done
