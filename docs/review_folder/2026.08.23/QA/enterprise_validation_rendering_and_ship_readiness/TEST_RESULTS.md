# Test results (pytest + mandatory QA)

**VERSION:** 7.2.2 · **Date:** 2026-08-23

## Pytest

| Battery | Command / scope | Result | Log |
|---|---|---|---|
| Core | Trust, inventory, UI, security, maps-related set | **309 passed**, 1 Flask deprecation warning | `pytest/core_battery.txt` |
| Post-IM calm | trust + inventory + UI + flask e2e | **47 passed** | `pytest/ui_after_im_calm.txt` |
| Parser/vendor | parser_regression + vendor_matrix + QA vendor ops | **57 passed** | `pytest/parser_vendor.txt` |
| Parser+topology (earlier) | + phase5 slices + routing_analyzer | **127 passed** | prior run in session |

## Mandatory QA

| Phase | Result | Log |
|---|---|---|
| `every_code_change` | **PASS** | `qa/every_code_change.txt` |

## Fixture / content tests (non-pytest)

| Check | Result | Artifact |
|---|---|---|
| expected_vs_actual maps | **MATCH** | `generated_outputs/exports/expected_vs_actual.json` |
| JSON/inventory edge cases | **PASS** | `generated_outputs/edge_cases/edge_case_results.json` |

## Known warnings

- Flask `__version__` DeprecationWarning in `vlan_checker_web.py` (non-blocking).

## Verdict

**Automated offline QA: PASS** for the executed batteries. Does not clear `release_gate`.
