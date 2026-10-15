# Documentation Master Index

| Field | Value |
|-------|-------|
| **Version** | 1.2.0 |
| **Status** | active |
| **Owner** | Documentation Steward (R-LIB) |
| **Last Updated** | 2026-07-21 |
| **Application Version** | 7.0.85 |
| **Command center** | [13-master-prompts/PROMPT_COMMAND_CENTER.md](13-master-prompts/PROMPT_COMMAND_CENTER.md) |
| **Truth audit** | [DOCUMENTATION_TRUTH_AUDIT_2026-06-18.md](DOCUMENTATION_TRUTH_AUDIT_2026-06-18.md) |
| **Canonical map** | [DOCS_CANONICAL_MAP.md](DOCS_CANONICAL_MAP.md) |

---

## Purpose

This is the master navigation index for all documentation in Network Swiss Tool Pro. It provides a complete, organized view of all documentation assets, their purposes, and their relationships. This document serves as the single source of truth for documentation structure and navigation.

---

## Documentation Structure Overview

```
docs/
├── 00-overview/              # High-level project overview and introduction
├── 01-architecture/          # System and module architecture documentation
├── 02-codebase/              # Code inventory, API docs, and technical details
│   └── MODULE_DETAILED_DOCS/  # Detailed module documentation (NEW)
├── 03-infrastructure/        # Infrastructure and deployment documentation
├── 04-automation/            # Automation, CI/CD, and workflows
├── 05-plugins/               # Plugin system and individual plugins
├── 06-ui-ux/                 # UI/UX documentation (web templates, Jinja2)
├── 07-operations/            # Operational guides, runbooks, troubleshooting
├── 08-security/              # Security documentation (auth, authz, threat model)
├── 09-qa/                    # QA standards, testing, production readiness
├── 10-rebuild/               # Build process, installation, recovery
├── 11-reference/             # Reference materials, standards, archives
├── 12-master-prompts/        # Prompt governance framework (G-00 through G-18)
├── 13-bug-reports/           # Bug tracking and fix workflow
├── 14-roadmap/               # Roadmap and reconstruction prompts
├── 15-visual-guide/          # Visual guide for program reconstruction
├── 16-roles-by-command/      # Roles by command reference
├── 17-ongoing-tasks/         # Ongoing task prompts (T-001 through T-005)
├── 18-interface-management/ # Interface management feature documentation
├── 19-recovery/              # Recovery procedures and disaster recovery
├── 20-release-management/    # Release notes, changelog, compatibility
├── 21-proposed-features/     # Proposed features and competitive analysis (NEW)
└── rebuilt-1-1/              # 1:1 rebuild context documentation
```

---

## Folder-by-Folder Documentation

### 00-overview/ - Project Overview

**Purpose:** High-level introduction to the project, mission, and getting started information.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| LIBRARIAN_MANDATE.md | Documentation steward mandate and responsibilities | Active | 2026-05-31 |
| project-overview.md | High-level project overview and introduction | Active | 2026-05-31 |
| roadmap.md | Project roadmap and future direction | Active | 2026-05-31 |
| walkthrough.md | Getting started walkthrough | Active | 2026-05-31 |
| LIBRARIAN_AUDIT_v7.0.9.md | Historical audit documentation | Archive | 2026-05-31 |

**Cross-References:**
- References: 13-master-prompts/INDEX_PROMPT.md (project mission)
- Referenced by: README.md (root)

---

### 01-architecture/ - System Architecture

**Purpose:** System and module architecture documentation, design patterns, and data flow.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| MODULE_ARCHITECTURE.md | Core module architecture and dependencies | Active | 2026-06-02 |
| system-architecture.md | Overall system architecture | Active | 2026-05-31 |
| system-architecture-deep-dive.md | Deep dive into system architecture | Active | 2026-05-31 |
| backend-architecture.md | Backend architecture details | Active | 2026-05-31 |
| visualization-pipeline.md | Data visualization pipeline | Active | 2026-05-31 |

**Cross-References:**
- References: 02-codebase/CODE_INVENTORY.md (module inventory)
- Referenced by: 02-codebase/MODULE_ARCHITECTURE.md

---

### 02-codebase/ - Codebase Documentation

**Purpose:** Code inventory, API documentation, utilities, and technical implementation details.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| CODE_INVENTORY.md | Complete inventory of all code components | Active | 2026-06-02 |
| API_DOCUMENTATION.md | REST and WebSocket API documentation | Active | 2026-06-02 |
| UTILITIES_DOCUMENTATION.md | Utility modules documentation | Active | 2026-06-02 |
| DOCUMENTATION_GAP_ANALYSIS.md | Documentation gap analysis | Active | 2026-06-02 |
| CONSOLIDATION_LOG.md | Documentation consolidation tracking | Active | 2026-06-02 |
| RECREATION_TEST_REPORT.md | 1:1 recreation capability validation | Active | 2026-06-02 |
| foundation.md | Foundation documentation | Active | 2026-05-31 |
| repository-structure.md | Repository structure documentation | Active | 2026-05-31 |
| PLATFORM_PROMPTS/ | Original platform prompts (immutable) | Archive | 2026-05-31 |

**MODULE_DETAILED_DOCS/** - Detailed module documentation for 1:1 rebuild:
| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| main.py.md | Entry point documentation | Active | 2026-07-21 |
| vlan_checker_web.py.md | Web server documentation | Active | 2026-07-21 |
| plugin_registry.py.md | Plugin system architecture | Active | 2026-07-21 |
| adapters.py.md | Adapters module documentation | Active | 2026-07-21 |
| network_base.py.md | Network base module documentation | Active | 2026-07-21 |

**Cross-References:**
- References: 01-architecture/MODULE_ARCHITECTURE.md (module details)
- Referenced by: All technical documentation

---

### 03-infrastructure/ - Infrastructure

**Purpose:** Infrastructure and parsing workflow documentation.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| parsing-workflows.md | Parsing workflow documentation | Active | 2026-05-31 |

**Cross-References:**
- References: 02-codebase/UTILITIES_DOCUMENTATION.md (parsing utilities)

---

### 04-automation/ - Automation

**Purpose:** Automation and plugin development documentation.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| plugin-development-guide.md | Plugin development guide | Active | 2026-05-31 |
| plugin-development-template.md | Plugin development template | Active | 2026-05-31 |
| plugin-system.md | Plugin system documentation | Active | 2026-05-31 |
| vpc-domain-plugin.md | VPC domain plugin documentation | Active | 2026-05-31 |
| installed-plugins/README.md | Redirect to canonical plugin docs | Redirect | 2026-06-02 |

**Cross-References:**
- References: plugins/ (canonical plugin documentation)
- Referenced by: 05-plugins/ui-philosophy.md

---

### 05-plugins/ - Plugins

**Purpose:** Plugin UI philosophy and design principles.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| ui-philosophy.md | Plugin UI philosophy | Active | 2026-05-31 |

**Cross-References:**
- References: 04-automation/plugin-development-guide.md
- Referenced by: 06-ui-ux/WEB_TEMPLATES_DOCUMENTATION.md

---

### 06-ui-ux/ - UI/UX Documentation

**Purpose:** UI/UX documentation including web templates and Jinja2 templates.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| **standard-map-shell.md** | **Standard L2 Map NOC shell (canonical)** | Active | 2026-06-18 |
| README.md | UI/UX hub + mockup index | Active | 2026-06-18 |
| ui-philosophy.md | Design principles | Active | 2026-05-31 |
| WEB_TEMPLATES_DOCUMENTATION.md | Web templates (index.html, cli_terminal.html) | Active | 2026-06-02 |
| JINJA2_TEMPLATES_DOCUMENTATION.md | Jinja2 templates documentation | Active | 2026-06-02 |
| mockups/ | Standard Map design demos (pre-ship) | Reference | 2026-06-18 |

**Cross-References:**
- References: 02-codebase/CODE_INVENTORY.md (template inventory)
- Referenced by: 05-plugins/ui-philosophy.md

---

### 08-security/ - Security

**Purpose:** Security documentation including authentication, authorization, and threat model.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| authentication.md | Authentication documentation | Active | 2026-05-31 |
| authorization.md | Authorization documentation | Active | 2026-05-31 |
| threat-model.md | Threat model documentation | Active | 2026-05-31 |

**Cross-References:**
- References: 12-master-prompts/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md
- Referenced by: 07-operations/production-guidelines.md

---

### 07-operations/ - Operations

**Purpose:** Operational guides, runbooks, troubleshooting, and diagnostics.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| ROOT_LEVEL_SCRIPTS_DOCUMENTATION.md | Root-level scripts documentation | Active | 2026-06-02 |
| operational-workflows.md | Operational workflows | Active | 2026-05-31 |
| runbooks.md | Operational runbooks | Active | 2026-05-31 |
| troubleshooting.md | Troubleshooting guide | Active | 2026-05-31 |
| diagnostics.md | Diagnostics guide | Active | 2026-05-31 |
| production-guidelines.md | Production guidelines | Active | 2026-05-31 |
| production-operations.md | Production operations | Active | 2026-05-31 |
| service-recovery.md | Service recovery procedures | Active | 2026-05-31 |
| backup-recovery.md | Backup and recovery | Active | 2026-05-31 |
| TS_ERROR_INDEX.md | Error index | Active | 2026-05-31 |
| exe-smoke-checklist.md | EXE smoke checklist | Active | 2026-05-31 |
| health-check-wizard.md | Health check wizard | Active | 2026-05-31 |
| health-wizard.md | Health wizard | Active | 2026-05-31 |
| mac-trace-howto.md | Mac trace how-to | Active | 2026-05-31 |
| network-search-reports-guide.md | Network search reports guide | Active | 2026-05-31 |
| network-search-workflow.md | Network search workflow | Active | 2026-05-31 |
| search-it-reports-guide.md | Search IT reports guide | Active | 2026-05-31 |
| search-it-workflow.md | Search IT workflow | Active | 2026-05-31 |
| discovery-command-center-guide.md | Discovery command center guide | Active | 2026-05-31 |
| discovery-trust-validation.md | Discovery trust validation | Active | 2026-05-31 |
| topology-diagnostics-guide.md | Topology diagnostics guide | Active | 2026-05-31 |
| vpc-command-center-guide.md | VPC command center guide | Active | 2026-05-31 |
| audit-test-gaps.md | Audit test gaps | Active | 2026-05-31 |

**Cross-References:**
- References: 08-security/authentication.md, 08-security/authorization.md
- Referenced by: 10-rebuild/from-zero-installation.md

---

### 09-qa/ - Quality Assurance

**Purpose:** QA standards, testing procedures, and production readiness.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| QA_STANDARDS_VALIDATOR.md | QA standards validator | Active | 2026-05-31 |
| QA_TESTING_CHECKLIST.txt | QA testing checklist | Active | 2026-05-31 |
| QA_TEST_CLI_TERMINAL.md | CLI terminal QA testing | Active | 2026-05-31 |
| QA_VPC_MAP.md | VPC map QA testing | Active | 2026-05-31 |
| ST_MASTER_QA_SUITE.md | Master QA suite | Active | 2026-05-31 |
| production-readiness.md | Production readiness checklist | Active | 2026-05-31 |

**Cross-References:**
- References: 12-master-prompts/ROLE_QA_ENGINEER_USAGE_PROMPT.md
- Referenced by: 20-release-management/README.md

---

### 10-rebuild/ - Build and Rebuild

**Purpose:** Build process, installation procedures, and recovery documentation.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| BUILD_PROCESS.md | PyInstaller build process | Active | 2026-06-02 |
| build-process.md | Build process (legacy) | Archive | 2026-05-31 |
| from-zero-installation.md | From-zero installation | Active | 2026-05-31 |
| exact-rebuild-procedure.md | Exact rebuild procedure | Active | 2026-05-31 |
| cold-start-recovery.md | Cold start recovery | Active | 2026-05-31 |
| offline-recovery.md | Offline recovery | Active | 2026-05-31 |

**Cross-References:**
- References: 02-codebase/RECREATION_TEST_REPORT.md
- Referenced by: 07-operations/service-recovery.md

---

### 20-release-management/ - Release Management

**Purpose:** Release notes, changelog, compatibility, and release management.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| README.md | Release management overview | Active | 2026-05-31 |
| CHANGELOG.md | Complete changelog | Active | 2026-05-31 |
| PLUGIN_COMPATIBILITY.md | Plugin compatibility matrix | Active | 2026-05-31 |
| ROADMAP.md | Release roadmap | Active | 2026-05-31 |
| ROADMAP_FEATURES.md | Feature roadmap | Active | 2026-05-31 |
| RELEASE_NOTES_*.md | Individual release notes (v4.5.2 through v7.0.10) | Active | 2026-05-31 |

**Cross-References:**
- References: 12-master-prompts/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md
- Referenced by: README.md (root)

---

### 21-proposed-features/ - Proposed Features (NEW)

**Purpose:** Competitive analysis, proposed enhancements, and implementation guides for future features.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| README.md | Proposed features overview | Active | 2026-07-21 |
| competitive-analysis/FEATURE_REVIEW_PROPOSED.md | Competitive feature review | Active | 2026-07-21 |
| competitive-analysis/PROTOTYPE_CURRENT_VS_PROPOSED.html | Current vs proposed prototype | Active | 2026-07-21 |
| competitive-analysis/EXPERT_DEMO_MEGAPLAN.html | Expert demo with all scenarios | Active | 2026-07-21 |
| implementation-guide/MODULARIZATION_STRATEGY.md | Plugin-based implementation strategy | Active | 2026-07-21 |
| implementation-guide/INTEGRATION_CHECKLIST.md | Integration steps checklist | Active | 2026-07-21 |
| implementation-guide/TESTING_PLAN.md | Comprehensive testing plan | Active | 2026-07-21 |
| roadmap/PHASE1_VISUALIZATION.md | Phase 1 implementation roadmap | Active | 2026-07-21 |

**Cross-References:**
- References: 05-plugins/ (plugin system for implementation)
- References: 06-ui-ux/ (UI/UX documentation)
- Referenced by: 14-roadmap/ (future implementation)

---

### 11-reference/ - Reference Materials

**Purpose:** Archive and audit reference materials.

| Directory | Purpose | Status |
|-----------|---------|--------|
| archive/ | Archived documentation | Archive |
| audits/ | Audit documentation | Active |

**Cross-References:**
- References: 12-master-prompts/action-logs/ (audit logs)

---

### 12-master-prompts/ - Prompt Governance Framework

**Purpose:** Prompt governance framework including policies, roles, and usage guides.

**Canonical Entry Point:** INDEX_PROMPT.md (G-00)

**Key Documents:**
- INDEX_PROMPT.md (G-00) - Mandatory entry point
- PROMPT_REGISTRY.md (G-01) - Source of truth for prompts
- GLOBAL_MASTER_PROMPT_RULES.md (G-18) - Absolute rules
- PROMPT_GOVERNANCE_POLICY.md (G-03) - Governance policy
- DOCUMENTATION_POLICY.md (G-06) - Documentation policy
- QUALITY_GATE_POLICY.md (G-07) - Quality gate policy
- CHANGE_MANAGEMENT_POLICY.md (G-08) - Change management policy
- RELEASE_MANAGEMENT_POLICY.md (G-09) - Release management policy
- COMPETITIVE_ADVANTAGE_POLICY.md (G-10) - Competitive advantage policy
- TEAM_MEETING.md (G-11) - Team meeting escalation
- PROMPT_ACTIVATION_POLICY.md (G-13) - Prompt activation policy
- ROLE_USAGE_STANDARD.md (G-14) - Role usage standard
- PROMPT_EXECUTION_RULES.md (G-15) - Prompt execution rules
- PROMPT_MIGRATION_SYNC.md (G-16) - Prompt migration and sync
- FINAL_OPERATING_INSTRUCTION.md (G-17) - Final operating instruction
- ROLE_MATRIX.md (G-04) - Role matrix
- ESCALATION_MATRIX.md (G-05) - Escalation matrix

**Council Roles (Combined):**
- ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md (R-GOV-LIB) - Prompt Librarian v3.1.0
- ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md (R-ARCH) - System Architect
- ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md (R-ENG) - Lead Developer
- ROLE_QA_ENGINEER_USAGE_PROMPT.md (R-QA) - QA Engineer
- ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md (R-SEC) - Security Reviewer
- ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md (R-OBS) - Observability Engineer
- ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md (R-LIB) - Documentation Steward
- ROLE_RELEASE_MANAGER_USAGE_PROMPT.md (R-REL) - Release Manager
- ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md (R-PROD) - Product Strategist
- ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md (R-COUNCIL) - Team Meeting Council

**Subdirectories:**
- action-logs/ - Action logs for role invocations
- archive/ - Archived prompt versions
- bugs/ - Bug-related prompts
- roles/ - Role prompts (combined in roles/combined/)

**Cross-References:**
- References: All documentation (governance framework)
- Referenced by: All documentation (governance compliance)

---

### 13-bug-reports/ - Bug Reports

**Purpose:** Bug tracking, prioritization, and fix workflow.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| README.md | Bug reports overview | Active | 2026-05-31 |
| 00-executive-summary.md | Executive summary | Active | 2026-05-31 |
| 01-prioritized-bug-list.md | Prioritized bug list | Active | 2026-05-31 |
| 02-bug-details/ | Individual bug details | Active | 2026-05-31 |
| 03-team-contributions/ | Team contributions | Active | 2026-05-31 |
| 04-fix-workflow/ | Fix workflow | Active | 2026-05-31 |
| _SCAFFOLD/ | Bug report scaffolds | Active | 2026-05-31 |
| W-BUG-SWEEP-*.md | Bug sweep reports | Active | 2026-05-31 |

**Cross-References:**
- References: 12-master-prompts/roles/CHECK_SYSTEM_FOR_BUGS.md
- Referenced by: 12-master-prompts/ROLE_QA_ENGINEER_USAGE_PROMPT.md

---

### 14-roadmap/ - Rebuild Roadmap (disaster recovery)

**Purpose:** 1:1 reconstruction when **only docs survive**. P01–P42 prompts, DDOS-safe batch execution.

| Document | Purpose |
|----------|---------|
| [README.md](14-roadmap/README.md) | Entry point |
| [DISASTER_RECOVERY_COMMAND.md](14-roadmap/DISASTER_RECOVERY_COMMAND.md) | Copy-paste batches (max 4 prompts/message) |
| [SYNC_PROTOCOL.md](14-roadmap/SYNC_PROTOCOL.md) | **Update on every code change** |
| [00-RECONSTRUCTION_INDEX.md](14-roadmap/00-RECONSTRUCTION_INDEX.md) | Phase dependency graph |

**Cross-References:**
- Integrated: `PROMPT_COMMAND_CENTER.md`, G-18 rules 21–23, `PROC-CCDU`
- Role: R-RECON

---

### 15-visual-guide/ - Visual Guide

**Purpose:** Visual guide for program reconstruction and workflow visualization.

**Cross-References:**
- References: 14-roadmap/ (rebuild prompts)
- Referenced by: 00-overview/walkthrough.md

---

### 16-roles-by-command/ - Roles by Command

**Purpose:** Slash-command and natural-language cheat sheet → roles activated.

| Document | Purpose |
|----------|---------|
| [COMMAND_MANUAL.html](16-roles-by-command/COMMAND_MANUAL.html) | **Offline HTML command book** (copy-paste, search) |
| [ROLES_BY_COMMAND_REFERENCE.md](16-roles-by-command/ROLES_BY_COMMAND_REFERENCE.md) | Command table (v3.0) |

**Authoritative detail:** `12-master-prompts/PROMPT_COMMAND_CENTER.md` (G-CC)

**Workflows:** FULL_DOCS_SYNC, FIND_ALL_BUGS_AND_FIX, UI_UX_AUDIT, NEXT_STEPS_COUNCIL

**Cross-References:**
- References: PROMPT_COMMAND_CENTER, ROLE_MATRIX, INDEX_PROMPT

---

### 17-ongoing-tasks/ - Ongoing Tasks

**Purpose:** Ongoing task prompts for systematic program maintenance and improvement.

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| T001-SYSTEM-AUDIT.md | System audit for code, documentation, and process review | Active | 2026-06-03 |
| T002-CODE-REVIEW.md | Holistic code review with team perspective | Active | 2026-06-03 |
| T003-DOCUMENTATION-AUDIT.md | Documentation audit for completeness and accuracy | Active | 2026-06-03 |
| T004-UI-UX-OVERVIEW.md | UI/UX assessment and improvement planning | Active | 2026-06-03 |
| T005-IMPROVEMENT-NEXT-STEPS.md | Improvement and next steps planning with internet research | Active | 2026-06-04 |

**Cross-References:**
- References: 12-master-prompts/ROLE_ONGOING_TASK_EXECUTOR_USAGE_PROMPT.md (R-TASK)
- Referenced by: 12-master-prompts/INDEX_PROMPT.md (task governance)

---

### 18-interface-management/ - Interface Management

**Purpose:** Interface management feature documentation.

**Cross-References:**
- References: 05-plugins/interface_manager/ (canonical plugin docs)
- Referenced by: 04-automation/plugin-development-guide.md

---

### 05-plugins/ - Plugin Documentation

**Purpose:** Plugin system and individual plugin documentation.

**Structure:**
```
05-plugins/
├── base_template/
├── config_templates/
├── critical_logs_plugin/
├── device_time_plugin/
├── environment_status_plugin/
├── interface_errors_plugin/
├── network_discovery/
├── serial_number_plugin/
├── standards_validator/
├── stp_topology_visualizer/
├── unused_trunk_pruner/
├── vlan_audit_plugin/
└── vpc_domain/
```

**Each Plugin Contains:**
- README.md - Plugin overview
- PROMPT.md - Original creation prompt
- CHANGELOG.md - Version history
- COMPATIBILITY.md - Platform compatibility
- TEST_RESULTS.md - Test results
- RELEASE_NOTES.md - Release notes

**Cross-References:**
- References: 04-automation/plugin-development-guide.md
- Referenced by: 04-automation/installed-plugins/README.md (redirect)

---

## Root-Level Documentation

| Document | Purpose | Status | Last Updated |
|----------|---------|--------|--------------|
| README.md | Project README and getting started | Active | 2026-05-31 |
| LIBRARIAN_AUDIT_v6.9.5.md | Historical audit documentation | Archive | 2026-05-31 |
| LIBRARIAN_RESYNC_REPORT_v6.9.5.md | Historical resync report | Archive | 2026-05-31 |

**Cross-References:**
- References: 00-overview/project-overview.md
- Referenced by: All documentation (entry point)

---

## Cross-Reference Validation

### Policy References

All policy references in documentation must point to:
- docs/12-master-prompts/PROMPT_GOVERNANCE_POLICY.md (G-03)
- docs/12-master-prompts/DOCUMENTATION_POLICY.md (G-06)
- docs/12-master-prompts/QUALITY_GATE_POLICY.md (G-07)
- docs/12-master-prompts/CHANGE_MANAGEMENT_POLICY.md (G-08)
- docs/12-master-prompts/RELEASE_MANAGEMENT_POLICY.md (G-09)
- docs/12-master-prompts/COMPETITIVE_ADVANTAGE_POLICY.md (G-10)

### Role References

All role references in documentation must point to:
- docs/12-master-prompts/roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md (R-GOV-LIB)
- docs/12-master-prompts/roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md (R-ARCH)
- docs/12-master-prompts/roles/combined/ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md (R-ENG)
- docs/12-master-prompts/roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md (R-QA)
- docs/12-master-prompts/roles/combined/ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md (R-SEC)
- docs/12-master-prompts/roles/combined/ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md (R-OBS)
- docs/12-master-prompts/roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md (R-LIB)
- docs/12-master-prompts/roles/combined/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md (R-REL)
- docs/12-master-prompts/roles/combined/ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md (R-PROD)
- docs/12-master-prompts/roles/combined/ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md (R-COUNCIL)

### Documentation Cross-References

All cross-references must use relative paths from the docs/ directory:
- Example: `../01-architecture/MODULE_ARCHITECTURE.md` (from docs/02-codebase/)
- Example: `01-architecture/MODULE_ARCHITECTURE.md` (from docs/ root)

---

## Documentation Maintenance

### Version Control

All documentation must include:
- Version number in header
- Last updated date
- Status (active, archive, deprecated, retired)
- Owner (responsible role or person)

### Update Workflow

1. Identify documentation requiring update
2. Update version number (major.minor.patch)
3. Update last_updated date
4. Update PROMPT_REGISTRY.md if applicable
5. Create action log entry
6. Validate cross-references
7. Update this master index

### Validation Checklist

- [ ] All documents have version info
- [ ] All documents have last_updated date
- [ ] All documents have status
- [ ] All cross-references are valid
- [ ] No duplicate documentation
- [ ] All documents serve clear purpose
- [ ] Folder structure is logical
- [ ] README files exist for major folders
- [ ] Policy references are correct
- [ ] Role references are correct

---

## Navigation Guide

### For New Users

Start here:
1. README.md (root) - Project introduction
2. 00-overview/project-overview.md - Project overview
3. 00-overview/walkthrough.md - Getting started walkthrough

### For Developers

Start here:
1. 01-architecture/MODULE_ARCHITECTURE.md - Module architecture
2. 02-codebase/CODE_INVENTORY.md - Code inventory
3. 02-codebase/API_DOCUMENTATION.md - API documentation
4. 04-automation/plugin-development-guide.md - Plugin development

### For Operators

Start here:
1. 08-operations/operational-workflows.md - Operational workflows
2. 08-operations/runbooks.md - Runbooks
3. 08-operations/troubleshooting.md - Troubleshooting
4. 10-rebuild/BUILD_PROCESS.md - Build process

### For QA Engineers

Start here:
1. 09-qa/QA_STANDARDS_VALIDATOR.md - QA standards
2. 09-qa/QA_TESTING_CHECKLIST.txt - Testing checklist
3. 13-master-prompts/ROLE_QA_ENGINEER_USAGE_PROMPT.md - QA role

### For Release Managers

Start here:
1. 11-release-management/README.md - Release management
2. 11-release-management/CHANGELOG.md - Changelog
3. 13-master-prompts/ROLE_RELEASE_MANAGER_USAGE_PROMPT.md - Release role

### For Documentation Stewards

Start here:
1. 13-master-prompts/INDEX_PROMPT.md - Prompt governance
2. 13-master-prompts/PROMPT_REGISTRY.md - Prompt registry
3. 13-master-prompts/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md - Documentation role
4. This document (DOCUMENTATION_MASTER_INDEX.md) - Documentation index

---

## References

- INDEX_PROMPT.md: docs/13-master-prompts/INDEX_PROMPT.md
- PROMPT_REGISTRY.md: docs/13-master-prompts/PROMPT_REGISTRY.md
- CODE_INVENTORY.md: docs/02-codebase/CODE_INVENTORY.md
- DOCUMENTATION_GAP_ANALYSIS.md: docs/02-codebase/DOCUMENTATION_GAP_ANALYSIS.md
- CONSOLIDATION_LOG.md: docs/02-codebase/CONSOLIDATION_LOG.md
- RECREATION_TEST_REPORT.md: docs/02-codebase/RECREATION_TEST_REPORT.md
