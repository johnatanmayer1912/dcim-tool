# BUG-0003 — Unclosed discovery test fixtures

**Severity:** Low | **Owner:** QA / Lead Developer

`tests/test_network_discovery.py` opens fixture files without `with` — Python 3.13 emits ResourceWarning. Fix: use `with open(...) as f: text = f.read()`.
