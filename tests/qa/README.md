# tests/qa — Mandatory Persona QA Suite

Extensive, **always-evolving** automated QA scaffold for Network Swiss Tool Pro. Owned by the multi-persona council (network, architect, software, NOC, Steve Jobs simplicity lens, UI/UX).

## Manifest

`MANDATORY_MANIFEST.yaml` — suite list, phases, persona owners, council links.

Validate:

```bash
python scripts/validate_mandatory_qa_manifest.py
```

Run orchestrator (do not run full scaffolds unless implementing):

```bash
python scripts/mandatory_release_qa.py --phase every_code_change
python scripts/mandatory_release_qa.py --phase pre_release
```

Full scaffold execution:

```bash
set NST_MANDATORY_QA_FULL=1
python scripts/mandatory_release_qa.py --phase pre_release
```

## Modules (persona-owned)

| File | Owner | Focus |
|------|-------|-------|
| `test_01_network_engineer_vendor_ops.py` | network council | IOS/NX-OS/Junos CLI paths |
| `test_02_product_architect_platform.py` | architect | control plane, outputs, plugins |
| `test_03_backend_engineer_api.py` | software engineer | Flask API, validation, threading |
| `test_04_noc_operator_workflows.py` | NOC | operator journeys, dry-run, logs |
| `test_05_product_simplicity_lens.py` | Steve Jobs lens | clicks, clarity, delete steps |
| `test_06_ui_ux_clarity.py` | UI/UX | tables, highlights, HTML contracts |
| `test_07_security_credentials.py` | security | creds, audit, no secrets in reports |
| `test_08_outputs_audit_trail.py` | NOC | manifests, folders, report chrome |
| `test_09_search_it_regression.py` | NOC | MAC, description, ping, progress |
| `test_10_plugins_discovery.py` | architect | discovery, plugins, frozen sim |
| `test_11_vlan_interface_mutations.py` | network | VLAN + IM mutations |
| `test_12_topology_maps.py` | UI/UX | VPC, discovery maps, escape |
| `test_13_release_offline_exe.py` | software | prebuild, manifest, EXE discipline |
| `test_14_session_control_plane.py` | software | session cache, abort, tasks |
| `test_15_interface_manager.py` | network | IM discover/deploy/verify |
| `test_16_standards_stp_swiss.py` | network | STP, standards, Swiss tools |

## Scaffold convention

- `@mandatory` marker (see `_scaffold.py`)
- Default: **skipped** until `NST_MANDATORY_QA_FULL=1`
- Implement bodies incrementally per feature/bug (see `docs/09-qa/QA_EVOLUTION_POLICY.md`)

## Council questionnaire

Code-only team validation (not pytest): `.cursor/skills/nst-network-engineer-council/QUESTIONNAIRE.md`

Output: `.cursor/audits/TEAM_VALIDATION_REGISTER_*.md`
