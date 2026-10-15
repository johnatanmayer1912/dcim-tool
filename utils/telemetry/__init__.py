"""Phase 3 telemetry package — fixture-only observation contract.

See ``contract.py`` for non-goals and timestamp rules.
"""
from utils.telemetry.catalog import (
    apply_catalog_to_observation,
    lookup_metric,
)
from utils.telemetry.contract import (
    UNKNOWN,
    compute_observation_id,
    empty_observation,
    observation_field_names,
)
from utils.telemetry.delta import (
    compute_delta,
    latest_delta,
    pairwise_deltas,
    same_series,
    series_key,
)
from utils.telemetry.normalize import load_fixture_json, normalize_batch, normalize_observation
from utils.telemetry.snapshot import export_series_snapshot, snapshot_to_json
from utils.telemetry.store import ObservationStore

__all__ = [
    'UNKNOWN',
    'compute_observation_id',
    'empty_observation',
    'observation_field_names',
    'load_fixture_json',
    'normalize_batch',
    'normalize_observation',
    'lookup_metric',
    'apply_catalog_to_observation',
    'ObservationStore',
    'compute_delta',
    'latest_delta',
    'pairwise_deltas',
    'same_series',
    'series_key',
    'export_series_snapshot',
    'snapshot_to_json',
]
