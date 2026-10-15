# QA — End-program exhaustive readiness review

## Scope

Evidence-gate readiness review only. No product UI or status-model changes.

## Commands

```bash
python3 -m pytest tests/test_phase5_*.py tests/test_phase6_wave*.py -q
python3 -m pytest tests/test_phase2_topology_truth_slice{1..7}.py tests/test_phase2_topology_truth_regression.py -q
python3 -m pytest tests/test_phase2_topology_truth_regression.py tests/test_discovery_map_html_contract.py tests/test_topo_map_shell.py tests/test_map_acceptance.py tests/test_discovery_acceptance.py tests/test_standard_map_v7049.py tests/qa/test_12_topology_maps.py -q
python3 -m pytest tests/test_phase3_*.py tests/test_phase4_*.py -q
python3 scripts/validate_mandatory_qa_manifest.py
python3 scripts/phase5_discovery_readiness_check.py
python3 scripts/phase5_discovery_release_consumer.py
python3 scripts/phase5_discovery_readiness_check.py --require-release-pass   # expect exit 1
python3 scripts/phase5_discovery_release_consumer.py --require-release-pass # expect exit 1
```

## Gate

`release_gate=BLOCKED`, `hard_stop=true`, `live_evidence_artifact=null` → **no readiness PASS**.

## Do not report as

- Fixture green = live vendor validated
- `ok: true` = enterprise ready
- Phase 6 UI complete = release clearance
