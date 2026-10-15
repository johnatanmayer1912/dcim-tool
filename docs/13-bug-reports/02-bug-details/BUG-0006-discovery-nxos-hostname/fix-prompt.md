# BUG-0006 — Discovery NX-OS hostname shows software banner

## Symptom
Network Discovery labels NX-OS switches with text like `cisco nexus operating system (nx-os) software tac support http://...` instead of the real hostname.

## Root cause
`network_discovery.py` passed the entire `show version` output to `safe_node_name()`, which lowercases the full banner blob.

## Fix
Use `resolve_device_hostname()` in `modules/network_base.py` (prompt → parsed fields → show hostname → IP fallback).

## Verify
```bash
python -m unittest tests.test_network_discovery.TestHostnameResolver -v
python tests/validate_vpc_member_interfaces.py
```
