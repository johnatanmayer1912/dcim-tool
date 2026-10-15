# Network Swiss Tool Pro — Project Overview

| Field | Value |
|-------|-------|
| **Purpose** | High-level platform summary and navigation for all stakeholders |
| **Version Awareness** | **v7.0.51** (sync with `/VERSION`) |
| **Last Updated** | 2026-06-18 |
| **Owner** | Product / R-PROD + R-LIB |

---

## Platform objective

Enterprise network observability and automation for NOC environments: multi-vendor topology (Cisco IOS/XE/NX-OS/**IOS-XR**, Juniper Junos), vPC/LACP visualization, modular plugins, offline/air-gapped operation.

---

## Start here (canonical)

| Need | Document |
|------|----------|
| **Docs hub** | [docs/README.md](../README.md) |
| **AI commands** | [PROMPT_COMMAND_CENTER.md](../12-master-prompts/PROMPT_COMMAND_CENTER.md) |
| **Architecture** | [MODULE_ARCHITECTURE.md](../01-architecture/MODULE_ARCHITECTURE.md) |
| **Standard L2 Map** | [standard-map-shell.md](../06-ui-ux/standard-map-shell.md) |
| **Code truth** | [CODE_INVENTORY.md](../02-codebase/CODE_INVENTORY.md) |
| **API** | [API_DOCUMENTATION.md](../02-codebase/API_DOCUMENTATION.md) |
| **Rebuild from docs only** | [14-roadmap/README.md](../14-roadmap/README.md) |
| **Build EXE** | [10-rebuild/BUILD_PROCESS.md](../10-rebuild/BUILD_PROCESS.md) |
| **QA** | [09-qa/README.md](../09-qa/README.md) |
| **Changelog** | [/CHANGELOG.md](../../CHANGELOG.md) |

---

## Documentation hierarchy (current)

```
docs/
├── README.md                 # Hub entry
├── DOCUMENTATION_MASTER_INDEX.md
├── DOCS_CANONICAL_MAP.md     # Canonical vs legacy paths
├── 00-overview/              # This folder
├── 01-architecture/
├── 02-codebase/              # CODE_INVENTORY, API, utilities
├── 03-automation/ · 04-plugins/ · 05-plugins/
├── 07-operations/            # Primary runbooks (canonical)
├── 09-qa/                    # QA suites (canonical)
├── 10-rebuild/               # Build/install procedures
├── 20-release-management/    # Per-version release notes
├── 12-master-prompts/        # Governance + PROMPT_COMMAND_CENTER
├── 13-bug-reports/
├── 14-roadmap/              # Disaster recovery P01–P42
└── 17-roles-by-command/
```

Legacy redirects: (none - all folders now canonical)

---

## Navigation by role

### First-time user
1. [walkthrough.md](walkthrough.md)
2. `dist/NetworkSwissToolPro_v7.0.51_OFFLINE.exe` + `inventory.txt`
3. Browser: `http://127.0.0.1:5051`

### Developer
1. [MODULE_ARCHITECTURE.md](../01-architecture/MODULE_ARCHITECTURE.md)
2. [CODE_INVENTORY.md](../02-codebase/CODE_INVENTORY.md)
3. [plugin-development-template.md](../04-automation/plugin-development-template.md)
4. `python create_plugin.py`

### QA engineer
1. [09-qa/ST_MASTER_QA_SUITE.md](../09-qa/ST_MASTER_QA_SUITE.md)
2. `python -m pytest tests/` + `python _prebuild.py`
3. [exe-smoke-checklist.md](../07-operations/exe-smoke-checklist.md)

### Disaster recovery
1. [14-roadmap/DISASTER_RECOVERY_COMMAND.md](../14-roadmap/DISASTER_RECOVERY_COMMAND.md) — one batch at a time
2. Ground truth: CODE_INVENTORY + MODULE_ARCHITECTURE

### Release manager
1. `/VERSION`, `/CHANGELOG.md`
2. [20-release-management/](../20-release-management/)
3. [PROMPT_COMMAND_CENTER.md](../12-master-prompts/PROMPT_COMMAND_CENTER.md) § `/release-vX.Y.Z`

### Support
1. [07-operations/TS_ERROR_INDEX.md](../07-operations/TS_ERROR_INDEX.md)
2. [07-operations/troubleshooting.md](../07-operations/troubleshooting.md)

---

## Key value propositions

1. **Observability** — Topology, MAC trace, discovery command center, vPC maps
2. **Automation** — Plugin registry, standards validator, interface manager
3. **Resilience** — Offline EXE, docs-only 1:1 rebuild roadmap

---

## Related

- [LIBRARIAN_MANDATE.md](LIBRARIAN_MANDATE.md)
- [roadmap.md](roadmap.md)
- [DOCUMENTATION_TRUTH_AUDIT_2026-06-10.md](../DOCUMENTATION_TRUTH_AUDIT_2026-06-10.md)
