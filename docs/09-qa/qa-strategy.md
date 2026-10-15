# QA Strategy

> **See also:** [ST_MASTER_QA_SUITE.md](ST_MASTER_QA_SUITE.md) · [production-readiness.md](production-readiness.md)

## Gates

1. `python -m pytest tests/ -q`
2. `python _prebuild.py`
3. `python scripts/enterprise_qa_gate.py`
4. `python scripts/validate_docs_links.py`
