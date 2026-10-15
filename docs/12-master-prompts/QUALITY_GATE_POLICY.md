# QUALITY_GATE_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-07 |
| **last_updated** | 2026-05-31 |

**Related:** `ROLE_MATRIX.md` (reviews column) · `RELEASE_MANAGEMENT_POLICY.md` (G-09) · `PROMPT_EXECUTION_RULES.md` (G-15)

## Purpose

Define mandatory review gates for all significant changes.

---

## Required gates when relevant

No change may ship without every **applicable** gate below. Use the risk-profile table to select the set.

| Gate | Owner role | Registry ID | Typical outcome |
|------|------------|-------------|-----------------|
| **Developer Review** | Lead Developer | U-ENG | Approve diff scope, conventions, handoff |
| **Architect Review** | System Architect | U-ARCH | Approve boundaries, dependencies, contracts |
| **QA Review** | QA Engineer | U-QA | Approve tests, regression, release readiness |
| **Documentation Review** | Documentation Steward | U-LIB | Approve CHANGELOG, `docs/`, parity |
| **Release Review** | Release Manager | U-REL | Approve VERSION, build, rollback plan |
| **Backward Compatibility Review** | System Architect + QA | U-ARCH, U-QA | Approve breaking-change strategy |
| **Performance Review** | Lead Developer + TOPOLOGY | U-ENG, U-TOPO | Approve latency/render/batch impact |
| **Security Review** | Security Reviewer | U-SEC | Approve or block cred/trust changes |
| **Observability Review** | Observability Engineer | U-OBS | Approve logs, diagnostics, exports |
| **Network Engineering Review** | TOPOLOGY | U-TOPO | Approve parsers, VPC, map behavior |
| **Automation Review** | ORCHESTRATOR | U-ORCH | Approve plugins, batch workflows |

---

## Rules

1. **No change may bypass applicable gates.**
2. The **gate set must match the risk profile** of the change (see below).
3. **High-risk changes require more than one gate** (minimum: Architect + QA + Documentation; add Security for sensitive paths).
4. A gate may **approve**, **reject**, or **request changes**.
5. **Missing a required gate blocks release** (Release Manager must not ship).

---

## Risk profile → gate set

| Profile | Examples | Minimum gates |
|---------|----------|----------------|
| **Low** | Typo in comment, internal-only doc | Documentation Review (if user-visible text) |
| **Medium** | Bug fix, single-module feature | Developer, QA, Documentation |
| **High** | Cross-module, plugin, web UI, topology | Developer, Architect, QA, Documentation; + domain gates |
| **Critical** | Security, release, breaking API, outage fix | All applicable including Security, Release, Compatibility; Team Meeting if waiver needed |

### Domain triggers (add gates)

| Change touches | Add gate |
|----------------|----------|
| `modules/web/templates/index.html`, Flask routes | Developer, QA, Documentation; Jinja/template check |
| `adapters.py`, `topology_mapper.py`, `report_formatter.py` | Network Engineering, QA (VPC script), Performance |
| `modules/plugins/` | Automation, Architect, QA |
| SSH, passwords, inventory export | Security, Documentation |
| Diagnostics, logs, `topology_diagnostics_*` | Observability, QA |
| `VERSION`, EXE, `dist/` | Release, QA, Documentation |
| `docs/13-master-prompts/`, registry | Documentation, Prompt Librarian (G-03), QA if behavior tied to prompts |

---

## Project verification hooks

Concrete checks for this repository (in addition to council review):

| Gate | Command / artifact | Required when |
|------|-------------------|---------------|
| Prebuild | `python _prebuild.py` | Release, large refactor |
| VPC validation | `python tests/validate_vpc_member_interfaces.py` | Topology / `report_formatter` / `adapters` |
| Smoke (dev) | Flask: `/`, `/health`, critical APIs | Web or template changes |
| Template safety | No raw `{{` in JS inside Jinja without escape | Any `index.html` edit (see v6.9.22 CHANGELOG) |
| Plugin load | Plugin registry: 0 load errors | New/changed plugin |

---

## Failure handling

- Do **not** ship EXE if prebuild or VPC validation fails.
- **P0** web failures (500 on `/`) block release until root cause in `CHANGELOG.md`.
- Skipping a gate requires **Team Meeting Council** decision logged in `TEAM_MEETING.md` (`ESCALATION_MATRIX.md`).

---

## Regression focus (Network Swiss Tool Pro)

- VPC member interfaces visible in HTML (`bundled_links`, `vpc_member_interfaces`).
- Diagnostics folder at app cwd for topology runs.
- search_it description search output file naming.
- Offline HTML map loads without CDN dependency for embedded Vis.js path.

---

## Required quality-gate action log

For significant changes, record in `action-logs/YYYY-MM-DD_<slug>.md`:

| Field | Content |
|-------|---------|
| **gates identified** | List of applicable gates from risk profile |
| **approvals obtained** | Which gates passed (role, date, evidence) |
| **blockers found** | Failed checks, rejected gates |
| **unresolved risks** | Waivers, deferred fixes |
| **release recommendation** | Ship / hold / hotfix — U-REL input |

Combine with G-14 output (findings, decisions, risks) when QA or Release roles were active.

Template: `roles/_ACTION_LOG_SNIPPET.md` · QA role: `roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md`

---

## Success criteria

- [ ] Applicable gates identified before implementation completes
- [ ] Each gate approve / reject / request-changes recorded
- [ ] No release without Release Review when shipping
- [ ] High-risk changes have multiple gate sign-offs
- [ ] Quality-gate action log fields filled for significant work

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set).
