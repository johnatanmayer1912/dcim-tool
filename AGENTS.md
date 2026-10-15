# Network Swiss Tool Pro — AI IDE Command Center

This repository is an auto-orchestrated AI IDE for a **web-only** network management / visibility product (Flask + Netmiko, offline EXE).

Optional knowledge junctions (`.devin/`, `skillss/`, `.cursor/skills-devin/`) may be absent. **Native `.cursor/skills/` is the source of truth.**

## Start here (agent)

1. `.cursor/skills/nst-orchestrator/SKILL.md` — classify and route
2. `.cursor/ROLE_ACTIVATION_MATRIX.md` — roles
3. `.cursor/docs/OPERATING_MODEL.md` — rules vs skills vs commands
4. `.cursor/KNOWLEDGE_BASE_INDEX.md` — skill index
5. `python scripts/build_skill_catalog.py` — regenerate `.cursor/SKILL_CATALOG.json`
6. Maps/discovery honesty: `.cursor/docs/BASELINE_ASSERTIONS.md`, `.cursor/docs/ACCEPTANCE_CRITERIA.md`, `.cursor/docs/AI_NAVIGATION.md`, `.cursor/docs/READINESS_TRACEABILITY.md`, `.cursor/docs/pilot/`, `.cursor/docs/EVIDENCE_README.md`

## Native skills

| Skill | Role |
|---|---|
| `nst-orchestrator` | Command center — every session |
| `repo-onboarding` | Inventory and architecture map |
| `zero-trust-audit-360` | Zero Trust 360 + GAP_REGISTER |
| `nst-zero-trust-network-council` | Council wrapper for ZT |
| `nst-network-engineer-council` | Team questionnaire → TEAM_VALIDATION_REGISTER |
| `nst-oss-competitive-excellence` | OSS peers → NOC wow slice (evidence/backup/reachability) |
| `nst-gap-remediation-workflow` | Register → P0/P1/P2 → patches |
| `topology-map-excellence` | L2/L3/overlay maps |
| `parser-and-vendor-compatibility` | Junos / IOS-XE / NX-OS parsers |
| `network-domain-test-lab` | Domain fixtures and tests |
| `line-by-line-code-audit` | File-by-file review |
| `product-ux-audit` | Operator UX |
| `implementation-planner` | REMEDIATION_PLAN |
| `safe-refactor-and-fix` | Incremental patches |
| `exhaustive-test-and-validate` | pytest + QA gates |
| `release-readiness-review` | Verdict |
| `docs-and-governance-maintainer` | Logs, catalog, AGENTS |
| `nst-python-backend` | Flask, adapters, plugins |
| `nst-security-ops` | Vault, mutations, audit |
| `nst-product-architect` | Product policy |
| `nst-network-operations` | NOC workflows |
| `nst-release-engineer` | QA + PyInstaller |
| `nst-multi-advisor` | Tradeoff boards |
| `auth-rbac-auditor` | Authn/authz reality |
| `accessibility-reviewer` | Keyboard / labels |

## Commands

`.cursor/commands/` — `/repo-onboard`, `/zero-trust-360`, `/code-audit`, `/map-audit`, `/vendor-compat`, `/ux-audit`, `/plan-remediation`, `/fix-safely`, `/test-exhaustive`, `/release-review`, `/god-mode-network-audit`.

God-mode prompt: `.cursor/docs/GOD_MODE_MASTER_PROMPT.md`.

## Audit chain

```
nst-network-engineer-council  →  .cursor/audits/TEAM_VALIDATION_REGISTER_*.md
zero-trust-audit-360          →  .cursor/audits/GAP_REGISTER_*.md
nst-gap-remediation-workflow  →  .cursor/audits/REMEDIATION_PLAN_*.md  →  fixes + tests
```

Questionnaires:
- `.cursor/skills/nst-network-engineer-council/QUESTIONNAIRE.md`
- `.cursor/skills/zero-trust-audit-360/QUESTIONNAIRE.md`

## Mandatory QA

| Artifact | Purpose |
|---|---|
| `tests/qa/MANDATORY_MANIFEST.yaml` | Persona suites |
| `scripts/mandatory_release_qa.py` | `every_code_change` / `pre_release` |
| `docs/09-qa/MANDATORY_RELEASE_QA.md` | Human/agent workflow |
| `docs/09-qa/QA_EVOLUTION_POLICY.md` | Feature/bug → test + manifest |

## Product anchors

| Concern | Location |
|---|---|
| Operator UI | `modules/web/templates/index.html` |
| API | `vlan_checker_web.py` |
| VLAN | `modules/vlan_mgmt_production.py`, `/api/vlan/validate` |
| Interface Manager | `modules/plugins/interface_manager.py` |
| L2 discovery | `modules/plugins/network_discovery.py` |
| L3 | `modules/routing_analyzer/`, `modules/l3_topology_runner.py` |
| Topology trust | `utils/topology_trust.py` |
| Outputs | `utils/output_paths.py` |
| Control plane | `utils/task_control_plane.py` |
| Job index | `utils/job_index.py`, GET `/api/jobs` |
| API guards | `utils/api_security.py` |
| Map/crawl honesty | `.cursor/docs/BASELINE_ASSERTIONS.md`, `.cursor/docs/AI_NAVIGATION.md`, `.cursor/docs/READINESS_TRACEABILITY.md`, `.cursor/docs/pilot/`, `.cursor/docs/EVIDENCE_README.md` |

## Supported UI: web only

Tk (`vlan_checker_gui.py`) is **out of scope**. G-014 closed by design. Do not extend Tk.

## Rules (alwaysApply)

`00-nst-mandatory-governance`, `01-repo-context`, `03-safe-change`, `05-security-and-zero-trust`, `08-workflow-discipline`, `10-command-usage`.

File-scoped: coding, testing, topology, UX, docs.

## Do not

- Depend on missing `.devin/` packs
- Skip validation pipelines for device mutations
- Invent topology links or security controls
- Commit `.credential_key` or vault secrets
- Write exploit PoCs
