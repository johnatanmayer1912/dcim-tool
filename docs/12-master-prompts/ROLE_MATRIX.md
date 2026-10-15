# ROLE_MATRIX

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-04 |
| **last_updated** | 2026-05-31 |

**Related:** `PROMPT_ACTIVATION_POLICY.md` (G-13) · `PROMPT_EXECUTION_RULES.md` (G-15) · `PROMPT_USAGE_MANUAL.md` (G-02)

## Purpose

Define the ownership and coordination map for all roles in the master prompt system and Network Swiss Tool Pro engineering workflow.

---

## Matrix fields

Every role entry MUST document:

| Field | Description |
|-------|-------------|
| **role_name** | Council or domain role title |
| **mission** | Primary outcome the role owns |
| **owner_domain** | Bounded area of authority |
| **required_collaborators** | Roles that must be consulted or handed off to |
| **required_reviews** | Quality gates this role initiates or must pass |
| **escalation_target** | Where unresolved issues go |
| **output_artifacts** | Typical deliverables (docs, code, logs, builds) |

**Registry ID** (`prompt_id`) and **usage guide** path are listed for IDE lookup in `PROMPT_REGISTRY.md`.

---

## Rules

- Every role must have a clearly defined domain.
- Every role must know its collaborators.
- Every role must know which reviews it requires.
- Every role must know where it escalates unresolved issues.
- The matrix must be updated when roles change (registry + `CHANGELOG.md` + action log).

---

## Role matrix — council roles

| role_name | prompt_id | mission | owner_domain | required_collaborators | required_reviews | escalation_target | output_artifacts |
|-----------|-----------|---------|--------------|------------------------|------------------|-------------------|------------------|
| **RESYNC** | U-RESYNC | Reconstruct full project context before action | Synchronization | All roles (feeds chain) | — | Team Meeting Council | Context summary, risk list, next action |
| **Prompt Librarian** | R-GOV-LIB / U-GOV-LIB | Maintain prompt ecosystem integrity | Prompt governance | Documentation Steward, Release Manager | Prompt Governance (G-03) | Team Meeting Council | Registry entries, archive copies, governance action logs |
| **System Architect** | R-ARCH / U-ARCH | System coherence and scalability | Architecture | Lead Developer, QA, Security, Observability, Release | Architect Review | Team Meeting Council | Findings, dependency impacts, migration strategy, action log |
| **Lead Developer** | R-ENG / U-ENG | Implement approved changes safely | Code | Architect, QA, Security, Observability, Documentation, Release | Developer Review, QA Review | Architect or Team Meeting Council | Code changes, verification, compatibility, action log |
| **QA Engineer** | R-QA / U-QA | Verify correctness, no regression, compatibility | Quality | Lead Developer, Architect, Release, Security | QA Review | Release Manager or Team Meeting Council | Validation scope, results, release recommendation, action log |
| **Security Reviewer** | R-SEC / U-SEC | Protect from unsafe behavior and trust violations | Security | Architect, Developer, QA, Release | Security Review | Release Manager or Team Meeting Council | Surface reviewed, risks, mitigations, approve/block, action log |
| **Observability Engineer** | R-OBS / U-OBS | Observable, diagnosable, operationally transparent | Observability | Developer, QA, Release, Security (leakage) | Observability Review | Team Meeting Council | Observability review, gaps, instrumentation, alerting impact, action log |
| **Documentation Steward** | R-LIB / U-LIB | Accurate docs aligned with code, prompts, policy, architecture | Documentation | Prompt Librarian, Architect, Developer, QA, Release | Documentation Review | Team Meeting Council | Docs reviewed/updated, gaps, action log (what/why/remaining) |
| **Release Manager** | R-REL / U-REL | Readiness, rollout discipline, rollback, change safety | Release | QA, Security, Observability, Documentation, Architect, Developer | Release Review | Team Meeting Council | Scope, approvals, rollback, validation, deployment sequence, action log |
| **Product Strategist** | R-PROD / U-PROD | Mission and competitive advantage; best network mgmt tool goal | Product | Architect, Release, Prompt Librarian | Product Review | Team Meeting Council | Strategic assessment, impact, gaps, opportunities, priorities, action log |
| **Team Meeting Council** | R-COUNCIL / U-COUNCIL | Cross-functional review; gaps; exact next-step prompts | Governance | All council roles + domain as needed | N/A (convenes reviews) | Human owner (L3/L4) | Meeting outputs, issue schema, `TEAM_MEETING.md`, action log |

### Invoke files (council)

| role_name | combined prompt (Part 1 + Part 2) |
|-----------|--------------------------------------|
| RESYNC | `roles/RESYNC_USAGE.md` (domain; platform `RESYNC.md`) |
| Prompt Librarian | `roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md` |
| System Architect | `roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md` |
| Lead Developer | `roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md` |
| QA Engineer | `roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md` |
| Security Reviewer | `roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md` |
| Observability Engineer | `roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md` |
| Documentation Steward | `roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md` |
| Release Manager | `roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md` |
| Product Strategist | `roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md` |
| Team Meeting Council | `roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md` |

### Source prompts / policies

| role_name | primary source |
|-----------|----------------|
| RESYNC | `PLATFORM_PROMPTS/RESYNC.md` |
| Prompt Librarian | R-GOV-LIB, G-01, G-03, G-16 |
| System Architect | R-ARCH; advisory `P01-FOUNDATION.md`, `P01_CONTRACT.md`, `ENGINEER.md`, `P06_ALIGNMENT.md` |
| Lead Developer | R-ENG; platform `ENGINEER.md` (P-ENG) |
| QA Engineer | R-QA, G-07, `docs/09-qa/` |
| Security Reviewer | R-SEC, G-08; advisory P-BAK |
| Observability Engineer | R-OBS, G-07; `docs/08-operations/diagnostics.md`, topology diagnostics |
| Documentation Steward | R-LIB, G-06, D-LIB; advisory P-LIB |
| Release Manager | R-REL, G-09, G-08 (7–8), `VERSION`, `CHANGELOG.md` |
| Product Strategist | R-PROD, G-10, `INDEX_PROMPT.md` mission |
| Team Meeting Council | R-COUNCIL, G-11, G-05 |

---

## Role matrix — domain specialists

Activate **in addition** to council roles when task signals match (`PROMPT_ACTIVATION_POLICY.md`).

| role_name | prompt_id | mission | owner_domain | required_collaborators | required_reviews | escalation_target | output_artifacts |
|-----------|-----------|---------|--------------|------------------------|------------------|-------------------|------------------|
| **TOPOLOGY** | U-TOPO | Network topology, VPC, and map intelligence | Network visualization | Lead Developer, QA Engineer, Observability Engineer | Network Engineering Review, QA Review | System Architect or Team Meeting Council | Parsed topology JSON, HTML maps, `topology_diagnostics_*` |
| **ORCHESTRATOR** | U-ORCH | Multi-device and plugin workflows | Automation | Lead Developer, System Architect | Automation Review, QA Review | Team Meeting Council | Plugin outputs, batch run logs, registry metadata |
| **UI DYNAMO** | U-UI | Web UI and template safety | UI / Flask | Lead Developer, QA Engineer | Developer Review, QA Review (Jinja) | Team Meeting Council | `index.html` changes, route smoke results |
| **Plugin Registry** | U-REG | Plugin identity and registration | Plugin platform | ORCHESTRATOR, System Architect | Architect Review | Prompt Librarian or Team Meeting Council | Registry entries, `docs/04-plugins/` |

| role_name | usage guide | primary source |
|-----------|-------------|----------------|
| TOPOLOGY | `roles/TOPOLOGY_USAGE.md` | `P05-TOPOLOGY.md` |
| ORCHESTRATOR | `roles/ORCHESTRATOR_USAGE.md` | `P03_ORCHESTRATOR.md` |
| UI DYNAMO | `roles/UI_DYNAMO_USAGE.md` | `P04_UI_DYNAMO.md` |
| Plugin Registry | `REGISTRY_USAGE.md` *(draft)* | `P02_REGISTRY.md` |

---

## Summary table (quick reference)

| Role | Mission | Domain | Collaborators | Reviews | Escalation |
|------|---------|--------|---------------|---------|------------|
| Prompt Librarian | Maintain prompt ecosystem | Prompt governance | Documentation, Release | Prompt Governance (G-03) | Team Meeting |
| System Architect | System coherence and scalability | Architecture | Developer, QA, Security, Observability | Architect Review | Team Meeting |
| Lead Developer | Implementation | Code | Architect, QA, Security, Observability | Developer Review, QA | Architect or Team Meeting |
| QA Engineer | Validation and quality | Quality | Developer, Release | QA Review | Release Manager or Team Meeting |
| Security Reviewer | Security protection | Security | Architect, Developer, Release | Security Review | Release Manager or Team Meeting |
| Observability Engineer | Operational visibility | Observability | Developer, QA, Release | Observability Review | Team Meeting |
| Documentation Steward | Documentation accuracy | Documentation | Librarian, Architect, Developer | Documentation Review | Team Meeting |
| Release Manager | Release control | Release | QA, Security, Observability, Documentation | Release Review | Team Meeting |
| Product Strategist | Strategic alignment | Product | Architect, Release | Product Review | Team Meeting |
| Team Meeting Council | Cross-functional review | Governance | All roles | N/A | N/A |

*RESYNC precedes all rows. Domain specialists add reviews per subdomain table above.*

---

## Dependency chain (enforced)

Per `PROMPT_EXECUTION_RULES.md` / `PROMPT_ACTIVATION_POLICY.md`:

```
RESYNC
→ Product Strategist (when scope/direction changes)
→ System Architect
→ Lead Developer
→ QA Engineer
→ Security Reviewer (if applicable)
→ Observability Engineer (if applicable)
→ Documentation Steward
→ Release Manager (if shipping)
→ Prompt Librarian (if prompts/registry changed)
```

**Team Meeting Council** overlays any step when conflicts exist.

---

## Auto-activation hints (this repository)

| Signal | Activate |
|--------|----------|
| `vpc`, `member interface`, `keepalive` | U-TOPO, U-QA, D-QA-VPC |
| `search_it`, `description` | U-ENG, D-SEARCH |
| `plugin` | U-ORCH, U-REG, plugin doc |
| `500`, `Jinja`, `template` | U-ENG, U-UI, U-QA |
| `EXE`, `PyInstaller`, `dist` | U-REL, U-QA |
| governance, registry, INDEX | U-GOV-LIB, G-00–G-15 |
| secrets, SSH, password | U-SEC |
| `VERSION`, release | U-REL, U-LIB |

---

## Legacy names

| Legacy | Council equivalent |
|--------|-------------------|
| ENGINEER | R-ARCH (design) + R-ENG (implement) |
| LIBRARIAN | Documentation Steward |
| QA (informal) | QA Engineer |

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (with `ROLE_MATRIX.md` in policy set).
