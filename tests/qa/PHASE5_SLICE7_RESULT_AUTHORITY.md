# QA — Phase 5 Slice 7 (result authority)

## Scope

Document and lock: **harness exit + JSON** are authoritative; **IDE/agent shell timeout / background status** are not.

## Authority checklist

When reviewing a “failed” Phase 5 live-lab / replay job:

1. Did pytest for the slice file exit 0?
2. Did `scripts/phase5_live_lab_truncated_discovery.py` exit 0 (replay) or 2 (not executed)?
3. Does JSON show `live_vendor_validated: false` for replay / not-executed?
4. Only if (1)–(3) fail is there a real regression.

If (1)–(3) succeed and only the outer shell task timed out → **do not** report contract failure.

## Commands

```bash
python -m pytest tests/test_phase5_parser_topology_resilience_slice7.py -q
NST_PHASE5_LIVE_LAB=1 NST_PHASE5_LIVE_LAB_REPLAY=tests/fixtures/discovery/phase5_live_lab_capture_replay.json \
  python scripts/phase5_live_lab_truncated_discovery.py
# Judge: process exit + printed JSON (result_authority), not agent task chrome.
```

## Do not report as

- Shell-task timeout = replay/contract failure
- Replay success = live vendor truncated CDP/LLDP validation

## Validation (2026-08-21)

- Phase 5 Slice 1–7: 56 passed
- Phase 2 baseline: 126 passed
- Phase 3+4 telemetry: 164 passed
- Manifest: OK (28 suites, v3)
