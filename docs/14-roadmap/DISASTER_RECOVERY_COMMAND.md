# Disaster Recovery Command — Rebuild from docs only

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Status** | active |
| **Owner** | R-RECON |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.29 |

## Rules (DDOS prevention)

1. **One batch per IDE message** — wait for completion before the next.
2. **Max 4 prompts per batch** — never send P01–P42 in one message.
3. **30 seconds** minimum between batches (rate limit / context recovery).
4. **Validate** after phases 1, 2, 6, 7, 8, 13 (`python -m pytest`, `_prebuild.py`).
5. Read `CODE_INVENTORY.md` + `MODULE_ARCHITECTURE.md` as ground truth when a prompt is ambiguous.

---

## Pre-flight (human or AI)

```text
ACTIVATE R-RECON, R-ARCH.
Read: docs/15-rebuild-roadmap/00-RECONSTRUCTION_INDEX.md
Read: docs/02-codebase/CODE_INVENTORY.md (inventory)
Read: docs/01-architecture/MODULE_ARCHITECTURE.md (dependencies)
Confirm: empty or fresh project directory for rebuild output.
```

---

## Batch 1 — Foundation (P01–P04)

```text
ACTIVATE R-RECON, R-ENG.
Execute reconstruction prompts in order (read each file fully, implement exactly):
1. docs/15-rebuild-roadmap/01-foundation/P01-ENVIRONMENT-SETUP.md
2. docs/15-rebuild-roadmap/01-foundation/P02-DEPENDENCY-INSTALLATION.md
3. docs/15-rebuild-roadmap/01-foundation/P03-PROJECT-STRUCTURE.md
4. docs/15-rebuild-roadmap/01-foundation/P04-INITIAL-CONFIGURATION.md
VALIDATE: python --version; project tree matches P03; requirements installable.
STOP. Do not proceed to Batch 2 until validated.
```

---

## Batch 2 — Core modules (P05–P08)

```text
ACTIVATE R-RECON, R-ENG, R-ARCH.
Execute in order:
5. docs/15-rebuild-roadmap/02-core-modules/P05-NETWORK-BASE.md
6. docs/15-rebuild-roadmap/02-core-modules/P06-ADAPTERS.md
7. docs/15-rebuild-roadmap/02-core-modules/P07-CONNECTIVITY.md
8. docs/15-rebuild-roadmap/02-core-modules/P08-INTERFACES.md
Ground truth: CODE_INVENTORY.md entries for network_base, adapters, mac_trace, node_interface_topology.
VALIDATE: import modules.network_base; no syntax errors.
STOP.
```

---

## Batch 3 — Plugin system (P09–P11)

```text
ACTIVATE R-RECON, R-ENG.
Execute in order:
9. docs/15-rebuild-roadmap/03-plugins/P09-PLUGIN-REGISTRY.md
10. docs/15-rebuild-roadmap/03-plugins/P10-PLUGIN-TEMPLATES.md
11. docs/15-rebuild-roadmap/03-plugins/P11-PLUGIN-IMPLEMENTATIONS.md
Include v7.0.29 behaviors: plugin_registry read-only EXE → bundled _MEIPASS;
interface_manager Junos status; network_discovery LLDP parsers; mac_utils/juniper_iface per SYNC_PROTOCOL.md.
VALIDATE: PluginRegistry loads; list plugins under modules/plugins/.
STOP.
```

---

## Batch 4 — Web interface (P12–P15)

```text
ACTIVATE R-RECON, R-ENG.
Execute in order:
12. docs/15-rebuild-roadmap/04-web-interface/P12-FLASK-APPLICATION.md
13. docs/15-rebuild-roadmap/04-web-interface/P13-WEB-TEMPLATES.md
14. docs/15-rebuild-roadmap/04-web-interface/P14-WEBSOCKET-HANDLING.md
15. docs/15-rebuild-roadmap/04-web-interface/P15-CLI-TERMINAL.md
VALIDATE: python vlan_checker_web.py starts; http://127.0.0.1:5051 responds.
STOP.
```

---

## Batch 5 — Utilities (P16–P18)

```text
ACTIVATE R-RECON, R-ENG.
Execute in order:
16. docs/15-rebuild-roadmap/05-utilities/P16-PARSING-UTILITIES.md
17. docs/15-rebuild-roadmap/05-utilities/P17-VALIDATION-UTILITIES.md
18. docs/15-rebuild-roadmap/05-utilities/P18-LOGGING-UTILITIES.md
MUST CREATE: utils/mac_utils.py, utils/juniper_iface.py per UTILITIES_DOCUMENTATION.md (v7.0.28+).
VALIDATE: from utils.mac_utils import normalize_mac_hex; from utils.juniper_iface import split_junos_unit
STOP.
```

---

## Batch 6 — Integration (P19–P21)

```text
ACTIVATE R-RECON, R-ENG, R-ARCH.
Execute in order:
19. docs/15-rebuild-roadmap/06-integration/P19-MODULE-INTEGRATION.md
20. docs/15-rebuild-roadmap/06-integration/P20-API-INTEGRATION.md
21. docs/15-rebuild-roadmap/06-integration/P21-DATABASE-INTEGRATION.md
VALIDATE: MAC trace API path works; discovery job API responds.
STOP.
```

---

## Batch 7 — Testing (P22–P24)

```text
ACTIVATE R-RECON, R-QA, R-ENG.
Execute in order:
22. docs/15-rebuild-roadmap/07-testing/P22-UNIT-TESTS.md
23. docs/15-rebuild-roadmap/07-testing/P23-INTEGRATION-TESTS.md
24. docs/15-rebuild-roadmap/07-testing/P24-TEST-EXECUTION.md
VALIDATE: python -m pytest tests/ -q → target 146 passed (or current CODE_INVENTORY count).
STOP.
```

---

## Batch 8 — Deployment (P25–P27)

```text
ACTIVATE R-RECON, R-REL, R-ENG.
Execute in order:
25. docs/15-rebuild-roadmap/08-deployment/P25-BUILD-PROCESS.md
26. docs/15-rebuild-roadmap/08-deployment/P26-PACKAGING.md
27. docs/15-rebuild-roadmap/08-deployment/P27-DEPLOYMENT.md
VALIDATE: python _prebuild.py → ALL CHECKS PASSED; EXE builds if PyInstaller available.
STOP.
```

---

## Batch 9 — Validation (P28–P30)

```text
ACTIVATE R-RECON, R-QA.
Execute in order:
28. docs/15-rebuild-roadmap/09-validation/P28-FUNCTIONAL-VALIDATION.md
29. docs/15-rebuild-roadmap/09-validation/P29-PERFORMANCE-VALIDATION.md
30. docs/15-rebuild-roadmap/09-validation/P30-SECURITY-VALIDATION.md
STOP.
```

---

## Batch 10 — Documentation structure (P31–P33)

```text
ACTIVATE R-RECON, R-LIB, R-GOV-LIB.
Execute in order:
31. docs/15-rebuild-roadmap/10-documentation/P31-DOCUMENTATION-STRUCTURE.md
32. docs/15-rebuild-roadmap/10-documentation/P32-DOCUMENTATION-CONTENT.md
33. docs/15-rebuild-roadmap/10-documentation/P33-DOCUMENTATION-VALIDATION.md
Note: If docs/ already exists (this scenario), validate and patch rather than overwrite history.
STOP.
```

---

## Batch 11 — Optimization (P34–P36) [optional post-MVP]

```text
ACTIVATE R-RECON, R-ENG.
Execute: P34, P35, P36 from docs/15-rebuild-roadmap/11-optimization/
STOP.
```

---

## Batch 12 — Troubleshooting (P37–P39) [optional]

```text
ACTIVATE R-RECON, R-OBS.
Execute: P37, P38, P39 from docs/15-rebuild-roadmap/12-troubleshooting/
STOP.
```

---

## Batch 13 — Finalization (P40–P42)

```text
ACTIVATE R-RECON, R-QA, R-LIB, R-REL.
Execute in order:
40. docs/15-rebuild-roadmap/13-finalization/P40-FINAL-VALIDATION.md
41. docs/15-rebuild-roadmap/13-finalization/P41-COMPLETION-REPORT.md
42. docs/15-rebuild-roadmap/13-finalization/P42-DOCUMENTATION-UPDATE.md
DELIVER: Reconstruction report; VERSION matches docs; CHANGELOG reflects rebuild.
DONE.
```

---

## Single mega-paste (orchestrator only — still one batch at a time)

User message template:

```text
rebuild from docs — Batch [N] only per docs/15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md
Do not execute other batches. Validate before stopping.
```

**Command center:** `docs/13-master-prompts/PROMPT_COMMAND_CENTER.md` § Rebuild from docs only
