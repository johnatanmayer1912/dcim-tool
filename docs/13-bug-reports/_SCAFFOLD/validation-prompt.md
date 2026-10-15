# VALIDATION PROMPT — [BUG-ID] (copy-paste into AI IDE)

```
RESYNC per INDEX_PROMPT. Validate fix for [BUG-ID]: [one-line title].

## Original repro
[steps]

## Fix summary
[what changed — files]

## Validation set (minimal)
- [ ] Original repro passes
- [ ] _prebuild.py
- [ ] tests/validate_vpc_member_interfaces.py (if topology/VPC)
- [ ] Flask smoke / /health (if web)
- [ ] Plugin load (if plugins)

## Gates
- U-QA sign-off: pass/fail
- U-SEC: N/A or pass
- U-OBS: N/A or pass

Report evidence in bug action-log.md. Coordinate U-REL if release-bound.
```
