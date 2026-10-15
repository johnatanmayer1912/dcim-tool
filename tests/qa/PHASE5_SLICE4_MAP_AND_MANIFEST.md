# Phase 5 Slice 4 — Map shell + mandatory manifest

**Status:** closed (fixture-only, 2026-08-21)  
**Decision:** both open items — map HTML incomplete surface **and** Phase 5 mandatory suite registration.

## Map shell contract

- `__DISCOVERY__` includes `incomplete_observation_count` and sanitized per-device `incomplete_observations[]`.
- Subtitle notes incomplete count (“not map links”).
- Overview banner + Summary panel list incompletes with `(unobserved)` ports.
- Device table badge when count > 0.
- Legend: “Incomplete observations = diagnostics only (not map links).”
- Incompletes are **never** drawn as vis.js edges.

## Manifest

Suite id: `pytest_phase5_parser_topology_resilience`  
Files: Slice 1–4 resilience tests  
Phase: `pre_release`, `blocking: true`

## Live truncated CDP/LLDP

Still **not** exercised over live SSH. Fixture parity covered in Slice 4 (`TestLiveLikeTruncatedFixtureParity`).

## Tests

`tests/test_phase5_parser_topology_resilience_slice4.py`
