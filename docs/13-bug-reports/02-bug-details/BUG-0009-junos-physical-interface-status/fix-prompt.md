# Fix prompt — BUG-0009 (copy-paste into AI IDE)

```
Fix BUG-0009: Junos Physical interface same-line status parsing.

In modules/plugins/interface_manager.py → _parse_junos_interfaces():
When matching "Physical interface: ge-0/0/0, Enabled, Physical link is Up" on a single line:
- After extracting interface name, scan the FULL line (not just following lines) for:
  - "Physical link is Up" → status/admin/oper up
  - "Physical link is Down" → oper down
  - "Enabled" / "Disabled" → admin status

Run: python -m pytest tests/test_parser_regression.py::TestInterfaceParserRegression -v
All three junos interface tests must pass.

Minimal diff only. No unrelated changes.
```
