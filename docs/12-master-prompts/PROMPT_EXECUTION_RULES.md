# PROMPT_EXECUTION_RULES

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-15 |
| **last_updated** | 2026-05-31 |

## Purpose

Define mandatory execution rules for the AI IDE when using the master prompt system.

**Orchestrates:** `GLOBAL_MASTER_PROMPT_RULES.md` (G-18) · `INDEX_PROMPT.md` · `FINAL_OPERATING_INSTRUCTION.md` (G-17) · `PROMPT_ACTIVATION_POLICY.md` · `ROLE_USAGE_STANDARD.md` · `PROMPT_USAGE_MANUAL.md`

---

## Mandatory Execution Sequence

The AI MUST follow this sequence for **every significant task** (unfamiliar, high-risk, release, governance, or multi-file change).

### Phase A — Read (in order)

| Step | Action |
|------|--------|
| 1 | Read `INDEX_PROMPT.md` |
| 2 | Read `PROMPT_REGISTRY.md` (locate `prompt_id`, `status`, `source_prompt`) |
| 3 | Read `GLOBAL_MASTER_PROMPT_RULES.md` (G-18 — 20 absolute rules) |
| 4 | Read `PROMPT_USAGE_MANUAL.md` |
| 5 | Read `PROMPT_ACTIVATION_POLICY.md` |
| 6 | Read `ROLE_USAGE_STANDARD.md` |
| 7 | Read `PROMPT_EXECUTION_RULES.md` (this file) |
| 8 | Read `FINAL_OPERATING_INSTRUCTION.md` (G-17) |
| 9 | Read **relevant policy prompts** (see § Policy set below) |
| 10 | Read **relevant role prompts** — R-*, combined `roles/combined/`, platform P-* |
| 11 | Read **relevant role prompts** (council: `roles/combined/ROLE_*_USAGE_PROMPT.md` Part 1+2; domain: `roles/*_USAGE.md`) |
| 12 | **RESYNC** — latest docs, code, release notes, bug fixes (see § Resync) |

### Phase B — Execute

| Step | Action |
|------|--------|
| 13 | Identify **all** relevant roles automatically (G-13, G-17, G-18 §15–17) |
| 14 | Execute roles in **dependency order** (see § Dependency enforcement) |
| 15 | **Log** all actions (`action-logs/`, G-14 output format) |
| 16 | **Update registry** when prompts/versions/status change (`PROMPT_REGISTRY.md` workflow) |
| 17 | **Update documentation** when behavior or guidance changes (`DOCUMENTATION_POLICY.md`) |
| 18 | **Update rebuild roadmap** when code changes (`15-rebuild-roadmap/SYNC_PROTOCOL.md`, R-RECON) |
| 19 | **Verify mandatory sync footer** applied — `roles/_MANDATORY_SYNC_FOOTER.md`; task incomplete if skipped |

### Policy set (step 9 — as applicable)

| Policy | ID | When |
|--------|-----|------|
| Governance | G-03 | Prompt or registry changes |
| Role matrix | G-04 | Role selection |
| Escalation | G-05 | Conflicts, L2+ |
| Documentation | G-06 | Any meaningful change |
| Quality gates | G-07 | Code, tests, release |
| Change management | G-08 | Implementation |
| Release | G-09 | VERSION, EXE, ship |
| Competitive advantage | G-10 | Scope, roadmap, differentiation |
| Team meeting | G-11 | Recorded escalation |

---

## No Skipping Rules

- **NO** skipping the index.
- **NO** skipping the registry.
- **NO** skipping resync (step 10).
- **NO** skipping relevant roles.
- **NO** skipping policy gates.
- **NO** skipping action logs (step 13).
- **NO** skipping documentation updates when behavior changed (step 17).
- **NO** skipping rebuild roadmap sync when code changed (step 18).
- **NO** marking implementation complete before steps 17–19 (mandatory sync).

Lightweight exception: trivial read-only Q&A with no code/doc/prompt impact may use steps 1–2 + task-specific doc only — **when in doubt, run full sequence**.

---

## Automatic Role Selection

The AI MUST automatically select all relevant roles based on **task domain**, not user instruction.

Matrix: `PROMPT_ACTIVATION_POLICY.md` · Hints: `ROLE_MATRIX.md`

---

## Dependency Enforcement

Roles MUST execute in dependency order:

0. **RESYNC** (context — step 10; also before chain)  
1. **Product Strategist** (scope — when feature/direction changes)  
2. **System Architect** (design)  
3. **Lead Developer** (implementation)  
4. **QA Engineer** (validation)  
5. **Security Reviewer** (if sensitive)  
6. **Observability Engineer** (if telemetry/diagnostics)  
7. **Documentation Steward** (meaningful changes)  
8. **Release Manager** (if shipping)  
9. **Prompt Librarian** (if prompts/registry changed)

Domain roles (**TOPOLOGY**, **ORCHESTRATOR**, **UI DYNAMO**) run with Developer/QA when signals match.

Shorthand: **architect → developer → QA → security → observability → documentation → release** (RESYNC and Product Strategist precede architect when applicable).

---

## Resync (step 10)

Minimum:

1. `VERSION` at repository root  
2. `CHANGELOG.md` (current + prior version; **Fixed** section)  
3. `PROMPT_REGISTRY.md` application sync line  
4. Task-specific `docs/` and hot-path modules (registry Tier 3)  
5. Git diff / recent changes if available  
6. Confirm no newer prompt supersedes context  

Full checklist: `PROMPT_USAGE_MANUAL.md` § Resync Rules · Role guide: `U-RESYNC`

---

## Logging Requirement

Every execution MUST produce (in action log and/or task summary):

| Field | Content |
|-------|---------|
| **what was read** | Files, policies, roles, version |
| **what was changed** | Paths, summary of diff |
| **what was verified** | Tests, smoke checks, gates |
| **what was recommended** | Not yet implemented |
| **what remains open** | Follow-ups |
| **risks identified** | Severity, mitigation |
| **decisions made** | Rationale |

Template: `roles/_ACTION_LOG_SNIPPET.md` · Standard: `ROLE_USAGE_STANDARD.md` § Standard Output Format

---

## Professional Elaboration

The AI MUST elaborate professionally on each role to maintain enterprise-grade quality.

- Clarify responsibilities; do not contradict `PLATFORM_PROMPTS/` intent.  
- Forward-sync per `PROMPT_GOVERNANCE_POLICY.md`.

---

## Updated Information Only

The AI will take only the **updated** information from the prompts and must elaborate professionally on each.

Prefer: `CHANGELOG`, registry change log, git diff, live `VERSION` over stale conversation summary.

---

## Success Criteria

- [ ] All rules in this document followed  
- [ ] All relevant roles activated  
- [ ] All applicable gates satisfied (`QUALITY_GATE_POLICY.md`)  
- [ ] All actions logged (step 13)  
- [ ] Registry updated if prompts changed (step 14)  
- [ ] Docs updated if behavior changed (step 15)  
- [ ] INDEX pre-work outputs met (prompts, policies, docs, risks, approval chain, next action)

---

## Index linkage

`INDEX_PROMPT.md` required reading order **§6**; full sequence is authoritative for Phase A + B.
