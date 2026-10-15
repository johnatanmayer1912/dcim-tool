# QA — Phase 6 Wave 1 (Discovery Program Status)

## Scope

Operator-visible Discovery Program Status. Not exhaustive program QA.

## Commands

```bash
python -m pytest tests/test_phase6_wave1_discovery_program_status.py -q
curl -s http://127.0.0.1:5051/api/discovery/program-status | python -m json.tool
```

Expect: `readiness.release_gate=BLOCKED`, `hard_stop=true` (hard stop), `may_claim_enterprise_ready=false`.

## Do not report as

- Session crawl complete = enterprise ready
- Program Status panel present = live truncated CDP/LLDP validated
- `ok` from Phase 5 checker = release clearance
