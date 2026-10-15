# RELEASE_MANAGEMENT_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-09 |
| **last_updated** | 2026-05-31 |

**Related:** `CHANGE_MANAGEMENT_POLICY.md` (G-08) phase 7–8 · `QUALITY_GATE_POLICY.md` (G-07) · `DOCUMENTATION_POLICY.md` (G-06) · **Role:** Release / Change Manager (R-REL / U-REL)

## Purpose

Control rollout, approval, rollback readiness, and post-release visibility.

---

## Rules

1. Every **high-risk change** needs a **rollback plan**.
2. Every **release** needs **validation evidence** (tests, smoke, gate sign-offs).
3. Every **release** needs **documentation updates** (`CHANGELOG`, `docs/`, version awareness).
4. Every **release** needs **monitoring readiness** (observability: diagnostics, health routes, ops guidance).
5. Every **release** needs **ownership and support coverage** (named roles in action log).
6. Every **release** must be **reversible where feasible** (prior EXE, VERSION revert path, CHANGELOG note).

### Version and build truth (this repository)

- Single version source: `VERSION` at repository root.
- UI / package naming must align with `CHANGELOG.md` and release notes.
- Commit and push only when the user explicitly requests.
- No force push to protected branches without explicit approval.

---

## Required checks before release

All applicable items must pass; missing check **blocks** ship (`QUALITY_GATE_POLICY.md`).

| Check | Owner | Registry ID | When required |
|-------|-------|-------------|---------------|
| **QA signoff** | QA Engineer | U-QA | Every release |
| **Security signoff** | Security Reviewer | U-SEC | Auth, secrets, SSH, exports, trust boundaries |
| **Observability readiness** | Observability Engineer | U-OBS | Runtime, diagnostics, logging changes |
| **Documentation readiness** | Documentation Steward | U-LIB | Every release |
| **Architecture approval** | System Architect | U-ARCH | Structure, modules, contracts, plugins |
| **Compatibility review** | Architect + QA | U-ARCH, U-QA | Plugin IDs, inventory formats, breaking changes |
| **Performance review** | Developer + TOPOLOGY | U-ENG, U-TOPO | HTML maps, batch jobs, large topology |

**Release Review** gate (U-REL) consolidates checklist approval.

---

## Release workflow (project)

Aligns with `CHANGE_MANAGEMENT_POLICY.md` phases 7–8:

| Step | Action |
|------|--------|
| 1 | **RESYNC** — `CHANGELOG`, registry application sync, hot paths |
| 2 | Confirm all **required checks** and G-07 project hooks (`_prebuild.py`, VPC tests if applicable) |
| 3 | Bump **`VERSION`**; top **`CHANGELOG.md`** entry (what / why / impact / rollback) |
| 4 | Update **`PROMPT_REGISTRY.md`** “Application sync” if behavior changed |
| 5 | Build — `NetworkSwissToolPro_v*_FINAL.spec` → `dist/NetworkSwissToolPro_*_OFFLINE.exe` |
| 6 | Optional **`dist_package_v*/`** — README, plugins copy, demo HTML |
| 7 | **Documentation Steward** — `docs/README.md` version line, ops/plugin docs |
| 8 | **Release action log** (below) + ship recommendation |

---

## Artifacts

| Artifact | Path / description |
|----------|-------------------|
| Offline EXE | `dist/NetworkSwissToolPro_*_OFFLINE.exe` |
| Offline bundle | `dist_package_v*/` (README, plugins, demo) |
| Release notes | `CHANGELOG.md` [vX.Y.Z] section |
| Version file | `/VERSION` |
| Validation evidence | Test commands, smoke results in action log |

---

## Required release action log

Record in `action-logs/YYYY-MM-DD_release-vX.Y.Z.md` (or task log) before ship:

| Field | Content |
|-------|---------|
| **release scope** | VERSION, features/fixes included, files/areas touched |
| **approvals** | QA, Security (if applicable), Documentation, Architect, etc. |
| **rollback plan** | Revert VERSION, prior EXE, config/data impact, hotfix path |
| **validation completed** | Commands run, pass/fail, smoke routes |
| **deployment sequence** | Build order, dist package, user-facing steps |
| **post-release watch items** | Metrics, diagnostics, known risks, support notes |

Include G-07 **release recommendation** (ship / hold / hotfix).

Template: `roles/_ACTION_LOG_SNIPPET.md` · Role guide: `roles/RELEASE_MANAGER_USAGE.md`

---

## Risk and escalation

- **Unresolved quality risk** → `ESCALATION_MATRIX.md` (QA + Release Manager → Team Meeting).
- **Security-sensitive release** → U-SEC signoff mandatory; block if missing.
- Skipping required check → Team Meeting waiver logged in `TEAM_MEETING.md`.

---

## Success criteria

- [ ] All required checks signed off for release scope
- [ ] Validation evidence attached
- [ ] Documentation and VERSION aligned
- [ ] Rollback plan documented for high-risk changes
- [ ] Release action log complete
- [ ] Observability/monitoring readiness confirmed for operational changes

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set).
