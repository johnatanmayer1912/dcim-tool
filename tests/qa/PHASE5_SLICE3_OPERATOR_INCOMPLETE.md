# Phase 5 Slice 3 — Operator-facing incomplete observations

**Status:** closed (fixture-only, 2026-08-21)  
**Depends on:** Slice 2 incomplete-observation contract

## Operator contract

1. Incomplete observations remain `incomplete=True` / `edge_eligible=False` and never become map links.
2. Crawl stores them on scanned nodes; `merge_nodes` preserves/merges them across identity merge.
3. API devices expose:
   - `incomplete_observation_count`
   - `incomplete_observations[]` (sanitized: empty ports, `(unobserved)` display fields, no raw CLI body)
4. Crawl result includes top-level `incomplete_observation_count`.
5. Discovery tab UI:
   - Evidence cell notes incomplete count (“not link(s)”)
   - Yellow panel lists incomplete rows with `(unobserved)` ports
   - Status line appends incomplete count when present
6. `_edges_to_api_links` no longer invents `n/a` for empty/placeholder ports (returns `''`).

## Tests

`tests/test_phase5_parser_topology_resilience_slice3.py`

## Out of scope / next slice

- Live vendor truncated output
- Mandatory-manifest suite registration (optional once UI settles)
- Map HTML shell wiring of incompletes (Command Center panel is Discovery tab only)
