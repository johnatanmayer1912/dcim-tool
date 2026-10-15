# QA — Phase 5 Slice 6 (live-lab honesty)

## Scope

Gated harness diagnostics + multi-family replay. **Not** a live truncated CDP/LLDP vendor pass.

## Expected outcomes

| Mode | Exit | `live_vendor_validated` |
|---|---|---|
| Gate off | 2 | false |
| Replay authorized | 0 (if contract holds) | **false** |
| Live env but all hosts TCP/22 down | 2 | **false** (`live_ssh_not_executed`) |
| Live SSH success | 0 | true (only then) |

## Commands

```bash
python -m pytest tests/test_phase5_parser_topology_resilience_slice6.py -q
NST_PHASE5_LIVE_LAB=1 NST_PHASE5_LIVE_LAB_REPLAY=tests/fixtures/discovery/phase5_live_lab_capture_replay.json \
  python scripts/phase5_live_lab_truncated_discovery.py
```

## Do not report as

- “Live lab validated truncated CDP/LLDP”
- “Inventory discovery succeeded” when hosts were down

## Residual risk

Live SSH path remains unexercised until an authorized lab with reachable devices is available.

## Validation (2026-08-21)

- Phase 5 Slice 1–6: 51 passed
- Phase 2 baseline: 126 passed
- Phase 3+4 telemetry: 164 passed
- Manifest: OK (28 suites, v3)
- Replay: `live_vendor_validated=false`
- Unreachable live path: exit 2, `live_ssh_not_executed`
