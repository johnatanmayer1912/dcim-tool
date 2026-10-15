# Rebuild Roadmap Sync Protocol

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Status** | active |
| **Owner** | R-RECON + R-LIB |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.29 |

## Purpose

When code changes, **this matrix tells you exactly which docs and reconstruction prompts to update.** R-ENG triggers identification; R-LIB updates ongoing docs; R-RECON updates P-prompts.

**Integrated into every implementation task** via `PROMPT_COMMAND_CENTER.md` — not optional.

---

## Sync workflow (every code change)

```
Code merged → R-ENG lists affected rows below
           → R-LIB updates "Ongoing docs" column
           → R-RECON updates "Rebuild prompts" column
           → R-QA confirms tests still describe behavior
           → Log in action-logs/
```

---

## Code path → documentation map

| Code path / feature | Ongoing docs (update) | Rebuild prompts (update) |
|---------------------|----------------------|--------------------------|
| `vlan_checker_web.py`, Flask API | `02-codebase/API_DOCUMENTATION.md` | P12, P20 |
| `modules/web/templates/` | `06-ui-ux/`, ops guides | P13 |
| WebSocket / CLI terminal | `API_DOCUMENTATION.md` | P14, P15 |
| `modules/network_base.py` | `MODULE_ARCHITECTURE.md`, `CODE_INVENTORY.md` | P05 |
| `modules/adapters.py` | `CODE_INVENTORY.md`, `03-automation/` | P06 |
| `modules/mac_trace.py` | `08-operations/mac-trace-howto.md`, API doc | P08, P20 |
| `utils/mac_utils.py` | `UTILITIES_DOCUMENTATION.md`, `CODE_INVENTORY.md` | P16 |
| `utils/juniper_iface.py` | `UTILITIES_DOCUMENTATION.md`, `05-plugins/interface_manager/` | P16, P11 |
| `modules/node_interface_topology.py` | `MODULE_ARCHITECTURE.md`, interface docs | P08, P19 |
| `modules/plugin_registry.py` | `04-plugins/`, `08-operations/exe-smoke-checklist.md` | P09, P25 |
| `modules/plugins/*.py` | `docs/05-plugins/<name>/README.md` | P10, P11 |
| `interface_manager` plugin | `05-plugins/interface_manager/` | P11 |
| `network_discovery` plugin | `05-plugins/network_discovery/` | P11 |
| `utils/discovery_graph.py` | `UTILITIES_DOCUMENTATION.md` | P16, P19 |
| `utils/discovery_map_shell.py` | `08-operations/discovery-command-center-guide.md` | P16, P13 |
| `utils/vpc_map_shell.py` | `08-operations/vpc-command-center-guide.md` | P16 |
| `tests/` | `08-operations/audit-test-gaps.md`, `09-qa/` | P22, P23, P24 |
| `NetworkSwissToolPro_*.spec`, build | `BUILD_GUIDE.md`, `10-rebuild/` | P25, P26, P27 |
| `VERSION`, release | `CHANGELOG.md`, `11-release-management/`, `docs/README.md` | P42, `00-RECONSTRUCTION_INDEX.md` header |
| `docs/13-master-prompts/` | `PROMPT_REGISTRY.md`, `INDEX_PROMPT.md` | P31, P32, P33 |
| Entire app structure | `DOCUMENTATION_MASTER_INDEX.md` | All phase `00-PROMPT-INDEX.md` |

---

## New module checklist

When adding a **new file or plugin**:

1. Add row to this table
2. Add entry to `CODE_INVENTORY.md`
3. Extend P11 or P16 (or add subsection — avoid new P-id unless new phase)
4. Add plugin README under `docs/05-plugins/<name>/`
5. Update `DOCUMENTATION_MASTER_INDEX.md`
6. Log in `action-logs/`

---

## v7.0.28–7.0.29 changes (reference)

| Change | Docs updated | Prompts to verify |
|--------|--------------|-------------------|
| `mac_utils.py` | UTILITIES, CODE_INVENTORY, mac-trace-howto | **P16** — include MAC normalization section |
| `juniper_iface.py` | UTILITIES, interface_manager README | **P16**, **P11** — LACP/ae correlation |
| `plugin_registry` read-only EXE | exe-smoke-checklist | **P09**, **P25** |
| BUG-0009 Junos parser | interface_manager README | **P11** |
| LLDP parsers | network_discovery README | **P11** |

---

## Validation

After sync:

- [ ] `VERSION` in docs matches `/VERSION`
- [ ] CODE_INVENTORY lists all `utils/` and `modules/` files
- [ ] Reconstruction index `Application Version` matches
- [ ] At least one action log entry for the change

**Monthly:** R-RECON runs spot-check reconstruction of one random phase (see R-RECON role).
