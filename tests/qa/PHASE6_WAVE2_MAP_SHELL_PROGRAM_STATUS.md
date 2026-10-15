# QA — Phase 6 Wave 2 (map shell Program Status)

## Scope

Discovery Command Center / offline map embeds Wave 1 Program Status. Not exhaustive QA.

## Commands

```bash
python -m pytest tests/test_phase6_wave2_map_shell_program_status.py -q
```

Expect HTML embeds: `program_status`, `release_gate: BLOCKED`, `hard_stop: true`, `HARD STOP — not advisory`.

## Do not report as

- Map banner present = enterprise ready
- Crawl complete on map = live truncated CDP/LLDP validated
- Program Status = topology layer
