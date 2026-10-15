# Phase 3 — Fixture-only telemetry acceptance (API freeze)

**Status:** Phase 3 closed (fixture-only).  
**Scope:** In-memory / fixture telemetry under `utils/telemetry/`.  
**Not:** live collectors, gRPC, SSH, SNMP, UI, auth, persistence, alerting, or topology mutation.

## Supported fixture families

- Cisco IOS-XE (`tests/fixtures/telemetry/iosxe_interface_counters.json`)
- Cisco NX-OS (`tests/fixtures/telemetry/nxos_interface_counters.json`)
- Juniper Junos (`tests/fixtures/telemetry/junos_interface_optics.json`)

## Frozen public package exports (`utils.telemetry`)

| Symbol | Role |
|--------|------|
| `UNKNOWN` | Sentinel for unknown / omitted fields |
| `compute_observation_id` | Deterministic identity |
| `empty_observation` | Legacy-compatible empty shape |
| `observation_field_names` | Contract field list |
| `load_fixture_json` | Fixture loader |
| `normalize_observation` / `normalize_batch` | Contract normalize |
| `lookup_metric` / `apply_catalog_to_observation` | Catalog |
| `ObservationStore` | In-process store |
| `same_series` / `series_key` | Series identity |
| `compute_delta` / `pairwise_deltas` / `latest_delta` | Deltas |
| `export_series_snapshot` / `snapshot_to_json` | Snapshot export |

Module-level details (statuses, insert result codes, store methods) live on their modules; private `_` helpers are not public API.

## Contract

- Accepted vs quarantined/rejected; secrets never accepted.
- Preserve `source_timestamp`; never invent it; keep `received_at` distinct.
- Duplicate `observation_id` expectations: store first-wins.

## Catalog

- Exact-path lookup; statuses: `known` / `unknown` / `invalid` / `ambiguous`.
- Ambiguous never silently picks one entry.
- Vendor/platform precedence deterministic; metadata conflicts warn.

## Store (`ObservationStore`)

- `insert`, `query`, `stats`, `clear`, `ingest_normalized_batch`, `get`, `count`
- `latest_delta` / `pairwise_deltas` over query copies only
- First-wins dedupe; oldest-first eviction; defensive copies

## Delta

- Ordering: `source_timestamp` → `received_at` → insertion
- Signed gauges; positive counters; reset only when monotonic explicit
- No rollover / wrap math; incompatible → non-numeric status

## Snapshot

- One row per retained series; ordered by `series_key`
- `generated_at` caller-supplied or `unknown` (no wall clock)
- Explicit unavailable delta when &lt;2 compatible points
- No raw payloads, secrets, topology edges, or trust claims

## Security / topology boundaries

- Secret-like paths/payloads quarantined or rejected; errors must not echo secrets.
- Telemetry must not create edges, trust tiers, cable/link claims, or mutate topology modules.

## Explicit non-goals

Live vendor compatibility · gRPC/protobuf · durable history · real-time analytics · alerting · production performance · complete sensor coverage · security certification · Arista · UI dashboards.

## Validation commands

```bash
python3 -m pytest \
  tests/test_phase3_telemetry_api_freeze.py \
  tests/test_phase3_telemetry_regression_slice6.py \
  tests/test_phase3_telemetry_snapshot_slice5.py \
  tests/test_phase3_telemetry_delta_slice4.py \
  tests/test_phase3_telemetry_store_slice3.py \
  tests/test_phase3_telemetry_catalog_slice2.py \
  tests/test_phase3_telemetry_contract_slice1.py \
  -q --tb=short

python3 -m pytest tests/test_phase2_topology_truth_regression.py -q --tb=short

python3 scripts/validate_mandatory_qa_manifest.py
# Optional pre_release suite (includes Phase 3 fixture pack when run):
# python3 scripts/mandatory_release_qa.py --phase pre_release
```

## Regression anchors

- `tests/test_phase3_telemetry_regression_slice6.py` — end-to-end chain
- `tests/test_phase3_telemetry_api_freeze.py` — export surface freeze
- Manifest suite: `pytest_phase3_telemetry_fixture` (pre_release)
