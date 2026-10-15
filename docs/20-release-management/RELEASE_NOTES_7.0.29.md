# Release Notes — v7.0.29 (2026-06-10)

## Summary

Enterprise-grade bug-fix release closing all open high-priority items from W-BUG-SWEEP-2026-06-10-v7028. Full test suite green.

## Fixed

| ID | Fix |
|----|-----|
| BUG-0009 | Junos `Physical interface:` same-line status parsing |
| BUG-0010 | 146/146 pytest pass (was 136/146) |
| NEW-H5 | Junos LLDP local port — interface-aware header, no `:` false match |
| NEW-C1 | Frozen EXE: bundled plugins when read-only install path |
| NEW-M2 | Graph merge by serial number |

## QA

- `pytest tests/` — **146 passed**
- `_prebuild.py` — **ALL CHECKS PASSED**
- CLI smoke — 11/11

## Artifact

- `NetworkSwissToolPro_v7.0.29_OFFLINE.exe`
