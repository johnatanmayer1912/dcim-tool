"""In-process fixture-only telemetry observation store / index (Phase 3 slice 3).

Answers: insert normalized observations deterministically, dedupe by observation_id,
query by device/metric/time, and bound memory with oldest-first eviction.

NON-GOALS
---------
- No SQLite/Redis/Kafka/files/persistence across restarts.
- No live collectors, gRPC, SSH, SNMP, UI, alerting, or auth.
- No topology edges, trust, or cable inference from stored metrics.
- Not a production durability claim — testable ingestion boundary only.

Ordering
--------
- Default query order: insertion order (oldest accepted first).
- Eviction: oldest accepted insertion first when ``max_observations`` is exceeded.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from utils.telemetry.contract import (
    UNKNOWN,
    assert_no_secrets_in_observation,
    is_secret_field_name,
)

INSERT_INSERTED = 'inserted'
INSERT_DUPLICATE = 'duplicate'
INSERT_REJECTED = 'rejected'


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _deep_copy(obs: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(obs)


def _ts_key(raw: Any) -> str:
    """Sortable timestamp key; missing → empty (sorts first, never invented)."""
    return _s(raw)


def _in_range(value: Any, start: Optional[str], end: Optional[str]) -> bool:
    if start is None and end is None:
        return True
    if value is None or value == '':
        # Missing timestamp does not match an explicit range filter
        return False
    key = _ts_key(value)
    if start is not None and key < _s(start):
        return False
    if end is not None and key > _s(end):
        return False
    return True


class ObservationStore:
    """Bounded in-memory store of accepted normalized telemetry observations."""

    def __init__(self, *, max_observations: int = 1000, default_query_limit: int = 100):
        if max_observations < 1:
            raise ValueError('max_observations must be >= 1')
        if default_query_limit < 1:
            raise ValueError('default_query_limit must be >= 1')
        self._max = int(max_observations)
        self._default_limit = int(default_query_limit)
        self._order: List[str] = []  # observation_ids in insertion order
        self._by_id: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            'inserted': 0,
            'duplicates': 0,
            'rejected': 0,
            'evicted': 0,
            'queried': 0,
        }

    # --- mutation ---------------------------------------------------------

    def clear(self) -> None:
        """Reset store contents and counters (tests / fixture harness)."""
        self._order.clear()
        self._by_id.clear()
        for k in self._stats:
            self._stats[k] = 0

    def insert(self, observation: Any) -> Dict[str, Any]:
        """Insert one normalized observation. First-wins on observation_id."""
        if not isinstance(observation, dict):
            self._stats['rejected'] += 1
            return {
                'status': INSERT_REJECTED,
                'reason': 'not an observation object',
                'observation_id': None,
            }

        # Reject secret-bearing payloads before copy/storage
        try:
            assert_no_secrets_in_observation(observation)
        except ValueError:
            self._stats['rejected'] += 1
            return {
                'status': INSERT_REJECTED,
                'reason': 'secret field not allowed',
                'observation_id': None,
            }
        for k in observation.keys():
            if is_secret_field_name(str(k)):
                self._stats['rejected'] += 1
                return {
                    'status': INSERT_REJECTED,
                    'reason': 'secret field not allowed',
                    'observation_id': None,
                }

        oid = _s(observation.get('observation_id'))
        if not oid or oid.lower() == UNKNOWN:
            self._stats['rejected'] += 1
            return {
                'status': INSERT_REJECTED,
                'reason': 'missing or unknown observation_id',
                'observation_id': oid or None,
            }

        if observation.get('quarantined'):
            self._stats['rejected'] += 1
            return {
                'status': INSERT_REJECTED,
                'reason': 'quarantined observation',
                'observation_id': oid,
            }

        if oid in self._by_id:
            self._stats['duplicates'] += 1
            return {
                'status': INSERT_DUPLICATE,
                'reason': 'observation_id already stored; first wins',
                'observation_id': oid,
            }

        record = _deep_copy(observation)
        # Ensure lists are independent
        record['warnings'] = list(record.get('warnings') or [])
        record['notes'] = list(record.get('notes') or [])
        record['catalog_matches'] = list(record.get('catalog_matches') or [])

        self._by_id[oid] = record
        self._order.append(oid)
        self._stats['inserted'] += 1

        evicted_ids: List[str] = []
        while len(self._order) > self._max:
            old = self._order.pop(0)
            self._by_id.pop(old, None)
            self._stats['evicted'] += 1
            evicted_ids.append(old)

        out: Dict[str, Any] = {
            'status': INSERT_INSERTED,
            'reason': 'accepted',
            'observation_id': oid,
        }
        if evicted_ids:
            out['evicted'] = list(evicted_ids)
        return out

    def ingest_normalized_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Insert ``accepted`` items from ``normalize_batch`` output only.

        Quarantined items from the batch are not stored. Returns aggregate counts.
        """
        accepted = list((batch or {}).get('accepted') or [])
        results = [self.insert(obs) for obs in accepted]
        return {
            'count_in': len(accepted),
            'inserted': sum(1 for r in results if r['status'] == INSERT_INSERTED),
            'duplicates': sum(1 for r in results if r['status'] == INSERT_DUPLICATE),
            'rejected': sum(1 for r in results if r['status'] == INSERT_REJECTED),
            'results': results,
        }

    # --- query ------------------------------------------------------------

    def query(
        self,
        *,
        device_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        entity_path: Optional[str] = None,
        catalog_status: Optional[str] = None,
        source_timestamp_start: Optional[str] = None,
        source_timestamp_end: Optional[str] = None,
        received_at_start: Optional[str] = None,
        received_at_end: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return defensive copies matching filters. Order: insertion (oldest first)."""
        lim = self._default_limit if limit is None else int(limit)
        if lim < 0:
            raise ValueError('limit must be >= 0')
        self._stats['queried'] += 1

        want_device = _s(device_id).lower() if device_id is not None else None
        want_metric = _s(metric_name) if metric_name is not None else None
        want_entity = _s(entity_path) if entity_path is not None else None
        want_cat = _s(catalog_status).lower() if catalog_status is not None else None

        out: List[Dict[str, Any]] = []
        for oid in self._order:
            obs = self._by_id.get(oid)
            if not obs:
                continue
            if want_device is not None and _s(obs.get('device_id')).lower() != want_device:
                continue
            if want_metric is not None and _s(obs.get('metric_name')) != want_metric:
                continue
            if want_entity is not None and _s(obs.get('entity_path')) != want_entity:
                continue
            if want_cat is not None and _s(obs.get('catalog_status')).lower() != want_cat:
                continue
            if not _in_range(
                obs.get('source_timestamp'),
                source_timestamp_start,
                source_timestamp_end,
            ):
                continue
            if not _in_range(
                obs.get('received_at'),
                received_at_start,
                received_at_end,
            ):
                continue
            out.append(_deep_copy(obs))
            if len(out) >= lim:
                break
        return out

    def get(self, observation_id: str) -> Optional[Dict[str, Any]]:
        oid = _s(observation_id)
        rec = self._by_id.get(oid)
        return _deep_copy(rec) if rec else None

    def count(self) -> int:
        return len(self._order)

    def stats(self) -> Dict[str, Any]:
        return {
            **dict(self._stats),
            'stored': len(self._order),
            'max_observations': self._max,
            'default_query_limit': self._default_limit,
        }

    def observation_ids(self) -> Tuple[str, ...]:
        return tuple(self._order)

    def pairwise_deltas(
        self,
        *,
        device_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        entity_path: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Consecutive deltas for a filtered series (copies only; no mutation)."""
        from utils.telemetry.delta import pairwise_deltas as _pairwise

        rows = self.query(
            device_id=device_id,
            metric_name=metric_name,
            entity_path=entity_path,
            limit=limit if limit is not None else self._default_limit,
        )
        return _pairwise(rows)

    def latest_delta(
        self,
        *,
        device_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        entity_path: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Latest pairwise delta for a filtered series."""
        from utils.telemetry.delta import latest_delta as _latest

        rows = self.query(
            device_id=device_id,
            metric_name=metric_name,
            entity_path=entity_path,
            limit=limit if limit is not None else self._default_limit,
        )
        return _latest(rows)
