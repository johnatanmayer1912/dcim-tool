# QA — Phase 5 Slice 8 (stdout authority)

## Scope

Every harness stdout JSON path must expose `result_authority` and `non_authoritative_signals`, matching `--json-out` when both exist.

## Modes covered

| Mode | Exit | Authority on stdout |
|---|---|---|
| `unauthorized_skip` | 2 | required |
| `live_ssh_prereq_skip` | 2 | required |
| `live_ssh_not_executed` | 2 | required |
| `replay` | 0/1 | required; matches artifact |
| `live_ssh` | 0/1 | required |

## Commands

```bash
python -m pytest tests/test_phase5_parser_topology_resilience_slice8.py -q
```

## Do not report as

- Missing stdout authority fields as “implicit pass”
- Replay stdout `ok: true` as live vendor validation
- Shell-task timeout as contract failure when exit + JSON say otherwise

## Validation (2026-08-21)

- Phase 5 Slice 1–8: 61 passed
- Phase 2 baseline: 126 passed
- Phase 3+4 telemetry: 164 passed
- Manifest: OK (28 suites, v3)
