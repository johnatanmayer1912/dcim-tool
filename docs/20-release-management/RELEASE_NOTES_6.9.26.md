# Network Swiss Tool Pro v6.9.26 Release Notes

**Release Date:** 2026-05-31  
**Version:** v6.9.26  
**Status:** PRODUCTION READY

---

## Summary

Resolves all open items from the 2026-05-31 bug sweep (BUG-0001 through BUG-0005).

### Fixes

- **Discovery API (BUG-0002):** Job status is `error` when the plugin returns `status: error`; UI shows failure instead of false success.
- **Discovery memory (BUG-0005):** Job store pruned to 50 most recent entries.
- **Tests (BUG-0003, BUG-0004):** Fixture files closed properly; VERSION validation uses semver from file.
- **Documentation (BUG-0001):** Hub docs aligned to v6.9.26 and `NetworkSwissToolPro_v6.9.26_OFFLINE.exe`.

---

## Artifact

`dist/NetworkSwissToolPro_v6.9.26_OFFLINE.exe`

## Validation

```bash
python _prebuild.py
python -m unittest discover -s tests -p "test_*.py" -v
python tests/validate_vpc_member_interfaces.py
```
