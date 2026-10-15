# QA — Phase 5 Slice 11 (hard-stop consumer)

## Operator one-liner

Release gate: **BLOCKED (HARD STOP — not advisory)**. Contract proven. Enterprise ready: **NO**. Live truncated CDP/LLDP: **NOT VALIDATED**.

## Commands

```bash
python scripts/phase5_discovery_readiness_check.py
# ok=true, release_gate=BLOCKED, hard_stop=true, may_claim_*=false

python scripts/phase5_discovery_release_consumer.py
# interpretation: HARD STOP — not advisory; exit 0 (contract held)

python scripts/phase5_discovery_readiness_check.py --require-release-pass
# exit 1 while blocked (enterprise claim mode)

python -m pytest tests/test_phase5_parser_topology_resilience_slice11.py -q
```

## Do not report as

- `ok: true` = cleared for enterprise release of truncated discovery
- `release_gate: BLOCKED` = advisory / informational
- Consumer exit 0 = live vendor validated

## Validation (2026-08-21)

- Checker: hard_stop=true; may_claim_*=false; --require-release-pass exit 1
- Consumer: HARD STOP — not advisory; exit 0
- Phase 5 Slice 1–11: 80 passed
- Phase 2: 126; Phase 3+4: 164
- Manifest: OK (30 suites, v3)
