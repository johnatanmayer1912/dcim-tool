# Network Swiss Tool Pro v6.9.25 Release Notes

**Release Date:** 2026-05-31  
**Version:** v6.9.25  
**Status:** PRODUCTION READY

---

## Executive Summary

Patch release fixing **live Network Discovery** on single (and multi) seed devices. Includes v6.9.24 Swiss Tools topology UX and v6.9.23 Discovery tab work.

### Key fix

- **Discovery live crawl**: Resolved `ValueError: not enough values to unpack (expected 3, got 2)` when starting a real SSH crawl from the Discovery tab (demo mode was unaffected).

---

## Build artifact

| File | Location |
|------|----------|
| Offline Web EXE | `dist/NetworkSwissToolPro_v6.9.25_OFFLINE.exe` |
| Spec | `NetworkSwissToolPro_v6.9.25.spec` |

---

## Validation

```bash
python -m unittest tests.test_network_discovery -v
python tests/validate_vpc_member_interfaces.py
```

---

## Upgrade notes

Replace prior `NetworkSwissToolPro_v6.9.*_OFFLINE.exe` with v6.9.25. No inventory or config format changes.
