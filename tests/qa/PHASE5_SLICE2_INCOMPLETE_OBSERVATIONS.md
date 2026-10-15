# Phase 5 Slice 2 — Incomplete observations & placeholder quarantine

**Status:** closed (fixture-only, 2026-08-21)  
**Depends on:** Slice 1 baseline (`PHASE5_PARSER_TOPOLOGY_RESILIENCE_BASELINE.md`)

## Contract

1. Truncated CDP/LLDP detail with peer identity but missing local interface emits an **incomplete observation** (`incomplete=True`, `edge_eligible=False`, empty local port) — not silent `[]` and not a map edge.
2. Junos LLDP alternative/table paths never seed or emit `hostname`/`remote_port` as `"unknown"`.
3. Graph construction and crawl skip incomplete observations for nodes/edges; incompletes may be retained on the scanned node as `incomplete_observations`.
4. Inspector model `build_incomplete_observation_model` displays empty ports as `(unobserved)`, not invented interface names.

## Tests

- `tests/test_phase5_parser_topology_resilience_slice2.py`
- Slice 1 truncated CDP assertion updated to incomplete contract

## Out of scope

Live vendor truth, Arista, telemetry transport, packaging.
