# QA Evolution Policy

Mandatory QA **evolves with the product**. Stale tests are a release risk.

## Triggers (agents MUST act)

| Event | Required updates |
|-------|------------------|
| **New operator-facing feature** | ≥1 row in council `QUESTIONNAIRE.md`; ≥1 test in `tests/qa/`; manifest suite entry; implement or scaffold with `@mandatory` |
| **Bug fix** | Regression test in `tests/` (implemented) or `tests/qa/` scaffold referencing bug/symptom |
| **New Python module** | `_prebuild.py` syntax path; PyInstaller `hiddenimports` if bundled; manifest if operator-visible |
| **UI / report change** | `tests/qa/test_06_ui_ux_clarity.py` scenario; questionnaire row in section H or O |
| **API route change** | `tests/qa/test_03_backend_engineer_api.py`; questionnaire L-section |
| **Credential / security change** | `tests/qa/test_07_security_credentials.py`; questionnaire F-section |
| **Release ship** | Bump `minimum_app_version` in `MANDATORY_MANIFEST.yaml`; `last_reviewed` date |

## Scaffold → implemented

1. New scenarios start as `@mandatory` tests using `tests/qa/_scaffold.py` (skipped unless `NST_MANDATORY_QA_FULL=1`)
2. Replace `pytest.skip` body with real assertions as behavior stabilizes
3. When implemented, consider moving to `tests/test_*.py` and keep qa module as integration umbrella
4. Set `blocking: true` in manifest only when test is reliable offline

## Questionnaire sync

Council questionnaire sections **A–R** map to `tests/qa/test_01` … `test_16`. When you add a question, add the **QA map** column target.

## Review cadence

- **Every code change:** manifest validate (automatic via `_prebuild` / orchestrator)
- **Every release:** council Team Validation Register + pre_release suite
- **Quarterly (or major refactor):** skim all 16 qa modules for obsolete scenarios; delete or update

## Ownership

| Persona | Owns modules |
|---------|----------------|
| network_engineer_council | test_01, test_07, test_11, test_15, test_16 |
| product_architect | test_02, test_10 |
| software_engineer | test_03, test_13, test_14 |
| noc_operator | test_04, test_08, test_09 |
| product_simplicity | test_05 |
| ui_ux_professional | test_06, test_12 |

## Anti-patterns

- Shipping without updating manifest after new feature
- Questionnaire answer without code citation
- Deleting tests without removing manifest entry
- Running full scaffold suite in CI before bodies exist (use `NST_MANDATORY_QA_FULL` locally)

## See also

- `tests/qa/MANDATORY_MANIFEST.yaml`
- `docs/09-qa/MANDATORY_RELEASE_QA.md`
- `.cursor/skills/nst-network-engineer-council/SKILL.md`
