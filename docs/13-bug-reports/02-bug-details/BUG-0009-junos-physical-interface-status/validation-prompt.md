# Validation prompt — BUG-0009

```
Validate BUG-0009 fix:
1. python -m pytest tests/test_parser_regression.py::TestInterfaceParserRegression -v
2. python -m pytest tests/plugins/test_interface_manager.py -v
3. Confirm Interface Manager discover on Junos fixture shows status "up" for xe-0/0/0
Report pass/fail counts.
```
