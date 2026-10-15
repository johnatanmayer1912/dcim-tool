# BUG-0004 — Hardcoded VERSION in validation script

**Severity:** Low | **Owner:** QA Engineer

`tests/validate_vpc_member_interfaces.py` line ~133: `ver == "6.9.25"` fails on every version bump. Fix: read `VERSION` file and compare, or assert semver pattern / `>=` minimum.
