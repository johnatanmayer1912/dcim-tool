# Quality Assurance Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | QA Engineer (R-QA) |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.61 |

## Purpose

Validation protocols, test suites, and production-readiness checklists.

## Documents

| File | Purpose |
|------|---------|
| [ST_MASTER_QA_SUITE.md](ST_MASTER_QA_SUITE.md) | Master QA suite |
| [production-readiness.md](production-readiness.md) | Ship checklist |
| [QA_VPC_MAP.md](QA_VPC_MAP.md) | vPC map validation |
| [QA_STANDARDS_VALIDATOR.md](QA_STANDARDS_VALIDATOR.md) | Standards validator QA |
| [QA_TEST_CLI_TERMINAL.md](QA_TEST_CLI_TERMINAL.md) | CLI terminal tests |
| [QA_TESTING_CHECKLIST.txt](QA_TESTING_CHECKLIST.txt) | Manual checklist |

## Gates

- `python -m pytest tests/` — unit/integration (target: 146+ pass)
- `python _prebuild.py` — prebuild gate
- [exe-smoke-checklist.md](../07-operations/exe-smoke-checklist.md) — post-EXE smoke

## Related

- [PROMPT_COMMAND_CENTER.md](../12-master-prompts/PROMPT_COMMAND_CENTER.md)
- [ROLE_QA_ENGINEER_USAGE_PROMPT.md](../12-master-prompts/roles/combined/ROLE_QA_ENGINEER_USAGE_PROMPT.md)
