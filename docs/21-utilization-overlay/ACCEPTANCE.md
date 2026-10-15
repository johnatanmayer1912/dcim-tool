# Utilization overlay — acceptance criteria (M1–M5)

Cite [FEATURE_CONTRACT.md](FEATURE_CONTRACT.md). Implemented in product code; live SSH is not live-lab proven.

## Correctness

- Overlay apply does not change the set of vis `{from,to,f_port,t_port}` pairs.
- Every `paints[].cable_key` exists in the bound L2 key set.
- `pct` is never computed from a single counter sample.

## Honesty

- Replay UI never says live / SNMP live poll.
- Live UI says `Live SSH — not SNMP`.
- Gray dashed remains for no-sample; missing color ≠ down (copy present).
- Program Status / `release_gate` unchanged by overlay jobs.

## Explainability

- Selected edge shows L2 identity + utilization provenance + freshness.
- Unmapped rows have a closed-set `reason`.

## Resilience

- Missing overlay document → no invented 0% paint.
- Live cancel → `degraded`, partial paints only for completed joins.
- Device id mismatch → refuse paint (fail closed).

## Mapping safety

- Ambiguous endpoint → unmapped, no paint.
- Po member counters do not paint Po edges.
- IRB/mgmt/SVI never paint L2 cables.

## Visual consistency

- Thresholds 70 / 90 and colors match contract (demo 07 aligned).
- Overlay off restores protocol coloring.

## Regression

- `utils.telemetry.__all__` freeze still holds.
- Discovery incomplete observations still non-edge-eligible.
- Discovery utilization host paints only existing L2 cable-key matches; EVPN/overlay vis edges keep protocol color.
- No new vis edges from utilization fixtures.

## Test categories

| Category | Examples |
|----------|----------|
| Unit | schema load, mode/evidence_class mismatch reject |
| Join | exact, Junos unique unit fallback, ambiguous, mgmt, bundle member |
| Replay fixture | golden overlay JSON + known L2 graph |
| Stale | `stale=true` keeps color, banner STALE |
| No-sample | all gray dash, edge count unchanged |
| UI | banner, legend, inspector, unmapped table, esc; CI-browser Playwright (`run_operator_browser_qa.py`, `run_offline_map_html_qa.py`) |
| Invariant | edge count before/after overlay |
