# NEXT_STEPS_COUNCIL

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Registry ID** | W-NEXT-STEPS |
| **Trigger** | `what are the next steps` · `/next-steps` · `improvement roadmap` |
| **Owner** | R-COUNCIL + R-PROD |
| **last_updated** | 2026-06-10 |

**Invoke:** Say **`what are the next steps to improve the program`** or paste this file.

---

## Mission

**360° council review** to recommend what to build next for **network engineers**: effectiveness, time saved, professionalism, simplicity. Output is a **decision-ready roadmap** with **implementation prompts** per item — not vague ideas.

**Audience:** Practicing network engineers (NOC, enterprise campus/datacenter). **Deployment:** Offline Windows PC EXE.

---

## Roles (all mandatory — holistic)

| Role | Question they answer |
|------|----------------------|
| R-PROD | What saves engineers the most time? What's missing vs competitors? |
| R-ARCH | What fits the architecture? What's the coupling cost? |
| R-ENG | What's feasible next sprint? Technical debt blockers? |
| R-QA | What needs tests first? Regression risk? |
| R-SEC | Security/compliance gaps? |
| R-OBS | Diagnostics gaps in the field? |
| R-LIB | What docs/training gaps block adoption? |
| R-REL | Release/EXE impact? |
| R-RECON | Does rebuild roadmap need new P-prompts? |
| R-GOV-LIB | Prompt/governance gaps? |
| R-COUNCIL | Prioritize, resolve conflicts, final recommendations |

---

## Inputs (resync before council)

1. `/VERSION`, `CHANGELOG.md`, `docs/14-bug-reports/01-prioritized-bug-list.md` (open medium/low)
2. `docs/08-operations/audit-test-gaps.md`
3. Recent user pain: MAC trace, discovery, interface map, plugins
4. `COMPETITIVE_ADVANTAGE_POLICY.md` (G-10)

---

## Output format (required)

Create **`docs/14-bug-reports/03-team-contributions/NEXT-STEPS-COUNCIL-YYYY-MM-DD.md`** and summary in **`docs/00-overview/roadmap.md`** (append section, do not erase history).

### Per recommendation row

| Field | Required |
|-------|------------|
| **ID** | NEXT-001, … |
| **Title** | Short name |
| **Decision** | Do now / Next sprint / Backlog / Defer |
| **Why** | Engineer value — time saved, risk reduced |
| **What it adds** | Capability in plain language |
| **Complexity** | S / M / L / XL (with hours estimate) |
| **Roles** | Who implements (R-ENG, …) |
| **Dependencies** | Bugs, arch work, lab gear |
| **Risks** | If we don't do it |
| **Success metric** | How we know it worked |
| **Implementation prompt** | Copy-paste block below |

### Implementation prompt template (per item)

Each NEXT-* item MUST include:

```markdown
### Implement NEXT-NNN: [Title]

ACTIVATE: [roles in order]

SCOPE:
- Files: ...
- Tests: ...
- Docs: ... (SYNC_PROTOCOL rows)

STEPS:
1. ...
2. ...

VALIDATE:
- pytest / prebuild / manual lab

DOCUMENT:
- CHANGELOG, plugin README, 15-rebuild-roadmap touch

COMMAND AFTER MERGE: /full-docs-sync
```

---

## Council decision rules

1. **Engineer time first** — prefer features that remove CLI repetition or clarify topology
2. **Offline trust** — no cloud dependencies
3. **Simplicity** — fewer tabs/clicks beats more options
4. **Fix before feature** — Critical/High bugs outrank NEW features unless council waives (record in TEAM_MEETING)
5. **Complexity honesty** — XL items must be split into phases

---

## Suggested categories (scan all)

| Category | Examples |
|----------|----------|
| Parser/platform | Legacy IOS, Junos versions, NX-OS |
| Discovery/topology | Parallel links (NEW-M1), orphan nodes |
| Search | MAC trace lab automation, description search |
| Interface manager | Bulk ops, range config |
| Plugins | New vendor, STP depth |
| UI/UX | Tab polish, progress UX (link W-UI-UX findings) |
| EXE/dist | Bare EXE smoke, read-only deploy |
| Quality | Live SSH test harness, coverage gaps |
| Docs/rebuild | CODE_INVENTORY body audit |

---

## Deliverables

- [ ] `NEXT-STEPS-COUNCIL-YYYY-MM-DD.md` with full table
- [ ] Each NEXT-* has implementation prompt
- [ ] `team-meeting-synthesis.md` addendum or cross-link
- [ ] Top 3 **"do now"** items highlighted
- [ ] Action log entry

---

## Follow-up commands

| User types | Action |
|------------|--------|
| `implement NEXT-001` | Run that item's implementation prompt |
| `/full-fix-and-ship NEXT-001` | Implement + test + doc + optional release |
| `ui ux check` | If item is UX-related |
