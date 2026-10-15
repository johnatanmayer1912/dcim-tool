# QA — Phase 5 Slice 9 (discovery readiness register)

## Gap

Enterprise readiness truth for truncated CDP/LLDP discovery must be machine-checkable and stay **false** for live vendor / operational ready until evidence exists.

## Commands

```bash
python scripts/phase5_discovery_readiness_check.py
python -m pytest tests/test_phase5_parser_topology_resilience_slice9.py -q
```

Expected checker: `ok: true`, `enterprise_operational_ready: false`, `live_vendor_truncated_cdp_lldp_validated: false`.

## Do not report as

- Phase 5 “complete” = enterprise operational ready
- Replay / Slice 1–8 green = live truncated CDP/LLDP vendor validated

## Validation (2026-08-21)

- Readiness checker: ok=true; enterprise/live flags false
- Phase 5 Slice 1–9: 67 passed
- Phase 2 baseline: 126 passed
- Phase 3+4 telemetry: 164 passed
- Manifest: OK (28 suites, v3)
