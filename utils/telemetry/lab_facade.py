"""Lab-only Gate D facade — in-process permission-checked reads (Phase 4).

Provides read/export helpers over ObservationStore, snapshot, delta, catalog,
quarantine summaries (from audit), and LabAuditSink.

Requires ``lab_mode=True``. Never opens sockets, listeners, threads, or disk.
Not exported from ``utils.telemetry`` (Phase 3 API freeze).

NON-GOALS: HTTP/mTLS/gRPC, persistence, UI, live collectors, topology.
"""
from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Optional, Tuple

from utils.telemetry.catalog import lookup_metric
from utils.telemetry.delta import latest_delta, pairwise_deltas
from utils.telemetry.lab_audit import (
    ET_AUTHN,
    ET_AUTHZ,
    ET_DENY,
    ET_EXPORT,
    ET_READ,
    EVENT_KEYS,
    LabAuditSink,
    OUT_DENIED,
    OUT_FAILURE,
    OUT_QUARANTINED,
    OUT_REJECTED,
    OUT_SUCCESS,
    RC_AUTHN_OK,
    RC_AUTHZ_DENIED,
    RC_AUTHZ_OK,
    RC_EXPIRED,
    RC_EXPORT_OK,
    RC_HEALTH_OK,
    RC_INGEST_VIA_FACADE_DENIED,
    RC_INVALID_QUERY,
    RC_INVALID_SCOPE,
    RC_KIND_MISMATCH,
    RC_LAB_MODE_REQUIRED,
    RC_LIMIT_EXCEEDED,
    RC_MISSING_PRINCIPAL,
    RC_RAW_PAYLOAD_DENIED,
    RC_READ_OK,
    RC_REDACTION_FAILED,
    RC_REVOKED,
    RC_SCHEMA_OK,
    RC_TOKEN_MISMATCH,
    RC_TOPOLOGY_DENIED,
    RC_TOPOLOGY_READ_DENIED,
    RC_UNKNOWN_PERMISSION,
    RC_UNKNOWN_PRINCIPAL,
    looks_secret_like_path,
    safe_actor_id,
)
from utils.telemetry.lab_ingest import (
    KIND_COLLECTOR,
    KIND_OPERATOR,
    PERM_AUDIT_READ,
    PERM_EXPORT,
    PERM_INGEST,
    PERM_READ,
    STATUS_ACTIVE,
    STATUS_EXPIRED,
    STATUS_REVOKED,
    LabAuthContext,
    LabStubPrincipal,
    LabTelemetryIngestor,
    default_lab_auth_context,
)
from utils.telemetry.snapshot import SNAPSHOT_SCHEMA_VERSION, export_series_snapshot, snapshot_to_json
from utils.telemetry.store import ObservationStore

FACADE_SCHEMA_VERSION = 'p4-gate-d-lab-1'
DEFAULT_MAX_RECORDS = 100
DEFAULT_MAX_RESPONSE_BYTES = 256_000

OBS_ALLOWLIST = (
    'observation_id',
    'device_id',
    'platform',
    'vendor',
    'metric_name',
    'metric_path',
    'entity_path',
    'value',
    'value_type',
    'unit',
    'metric_kind',
    'catalog_status',
    'source_timestamp',
    'received_at',
    'quality',
    'quarantined',
    'warnings',
    'notes',
    'sequence',
    'monotonic',
)

DELTA_ALLOWLIST = (
    'previous_observation_id',
    'current_observation_id',
    'series_key',
    'metric_name',
    'entity_path',
    'comparison_basis',
    'previous_value',
    'current_value',
    'absolute_delta',
    'direction',
    'reset_detected',
    'delta_status',
    'warnings',
    'notes',
)

CATALOG_ALLOWLIST = (
    'status',
    'metric_name',
    'metric_kind',
    'unit',
    'value_type',
    'monotonic',
    'warnings',
    'notes',
    'matches',
)

_GENERIC_AUTHN = 'authentication failed'
_GENERIC_AUTHZ = 'authorization denied'
_GENERIC_REJECT = 'request rejected'


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _err(status: str, reason: str = _GENERIC_REJECT, **extra: Any) -> Dict[str, Any]:
    out = {'ok': False, 'status': status, 'reason': reason, 'data': None}
    out.update(extra)
    return out


def _ok(data: Any, *, status: str = 'ok', reason: str = 'ok') -> Dict[str, Any]:
    return {'ok': True, 'status': status, 'reason': reason, 'data': data}


class LabGateDFacade:
    """In-process Gate D read/export surface. Lab-only; no network."""

    def __init__(
        self,
        *,
        lab_mode: bool = False,
        auth_context: Optional[LabAuthContext] = None,
        store: Optional[ObservationStore] = None,
        audit_sink: Optional[LabAuditSink] = None,
        ingestor: Optional[LabTelemetryIngestor] = None,
        max_records: int = DEFAULT_MAX_RECORDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        if lab_mode is not True:
            raise ValueError('LabGateDFacade requires explicit lab_mode=True')
        if int(max_records) < 1:
            raise ValueError('max_records must be >= 1')
        if int(max_response_bytes) < 1024:
            raise ValueError('max_response_bytes must be >= 1024')

        if ingestor is not None:
            self._store = ingestor._store  # shared in-process lab store
            self._audit = ingestor.audit_sink
            self._auth = ingestor._auth
        else:
            self._store = store if store is not None else ObservationStore(
                max_observations=max(max_records, 100),
                default_query_limit=max_records,
            )
            if audit_sink is not None:
                if not getattr(audit_sink, 'lab_only', False):
                    raise ValueError('audit_sink must be lab-only')
                self._audit = audit_sink
            else:
                self._audit = LabAuditSink(lab_mode=True)
            self._auth = auth_context if auth_context is not None else default_lab_auth_context()

        self._lab_mode = True
        self._max_records = int(max_records)
        self._max_bytes = int(max_response_bytes)
        self._network_started = False

    @property
    def lab_mode(self) -> bool:
        return self._lab_mode

    @property
    def network_started(self) -> bool:
        return self._network_started

    def start_network_listener(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError('network listener refused; lab Gate D facade is in-process only')

    # --- authn / authz -------------------------------------------------------

    def _authenticate(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        expected_kind: Optional[str] = None,
    ) -> Tuple[Optional[LabStubPrincipal], Optional[str], str]:
        pid = _s(principal_id)
        token = _s(stub_token_id)
        if not pid or not token:
            return None, _GENERIC_AUTHN, RC_MISSING_PRINCIPAL
        principal = self._auth.get(pid)
        if principal is None:
            return None, _GENERIC_AUTHN, RC_UNKNOWN_PRINCIPAL
        if principal.stub_token_id != token:
            return None, _GENERIC_AUTHN, RC_TOKEN_MISMATCH
        if principal.status == STATUS_EXPIRED:
            return None, _GENERIC_AUTHN, RC_EXPIRED
        if principal.status == STATUS_REVOKED or principal.status != STATUS_ACTIVE:
            return None, _GENERIC_AUTHN, RC_REVOKED
        if expected_kind and principal.kind != expected_kind:
            return None, _GENERIC_AUTHN, RC_KIND_MISMATCH
        return principal, None, RC_AUTHN_OK

    def _authorize(self, principal: LabStubPrincipal, permission: str) -> Tuple[Optional[str], str]:
        allowed = {PERM_INGEST, PERM_READ, PERM_EXPORT, PERM_AUDIT_READ}
        if not permission or permission not in allowed:
            return _GENERIC_AUTHZ, RC_UNKNOWN_PERMISSION
        if permission not in principal.permissions:
            return _GENERIC_AUTHZ, RC_AUTHZ_DENIED
        return None, RC_AUTHZ_OK

    def _emit(self, **fields: Any) -> bool:
        return bool(self._audit.record(**fields))

    def _gate(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        permission: str,
        operation: str,
        expected_kind: Optional[str] = None,
    ) -> Tuple[Optional[LabStubPrincipal], Optional[Dict[str, Any]]]:
        principal, err, authn_rc = self._authenticate(
            principal_id=principal_id,
            stub_token_id=stub_token_id,
            expected_kind=expected_kind,
        )
        actor = safe_actor_id(principal_id)
        if err:
            self._emit(
                event_type=ET_AUTHN,
                outcome=OUT_FAILURE,
                operation=operation,
                reason_code=authn_rc,
                actor_kind=_s(expected_kind) or 'unknown',
                actor_id_safe=actor,
            )
            return None, _err('authn_failed', err)
        assert principal is not None
        az, az_rc = self._authorize(principal, permission)
        if az:
            self._emit(
                event_type=ET_AUTHZ,
                outcome=OUT_DENIED,
                operation=operation,
                reason_code=az_rc,
                actor_kind=principal.kind,
                actor_id_safe=actor,
            )
            return None, _err('authz_denied', az)
        return principal, None

    def _bounded(self, payload: Any) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        try:
            text = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            return None, _err('redaction_failed', _GENERIC_REJECT)
        if len(text.encode('utf-8')) > self._max_bytes:
            return None, _err('limit_exceeded', _GENERIC_REJECT)
        return payload, None

    # --- field scrubbers -----------------------------------------------------

    @staticmethod
    def _scrub_obs(obs: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key in OBS_ALLOWLIST:
            if key not in obs:
                continue
            val = obs[key]
            if key in ('metric_path', 'entity_path') and looks_secret_like_path(val):
                out[key] = '[REDACTED]'
            elif key in ('warnings', 'notes'):
                out[key] = list(val or [])
            else:
                out[key] = copy.deepcopy(val)
        return out

    @staticmethod
    def _scrub_delta(delta: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key in DELTA_ALLOWLIST:
            if key in delta:
                out[key] = copy.deepcopy(delta.get(key))
        return out

    @staticmethod
    def _scrub_catalog(result: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key in CATALOG_ALLOWLIST:
            if key in result:
                out[key] = copy.deepcopy(result[key])
        # Never echo secret-like raw path from caller through notes
        notes = [n for n in (out.get('notes') or []) if not looks_secret_like_path(n)]
        out['notes'] = notes
        return out

    def _scrub_snapshot(self, snap: Dict[str, Any]) -> Dict[str, Any]:
        safe = copy.deepcopy(snap)
        for row in safe.get('series') or []:
            if not isinstance(row, dict):
                continue
            for k in list(row.keys()):
                low = k.lower()
                if low in ('raw_payload', 'payload', 'password', 'token', 'secret') or 'password' in low or 'token' in low:
                    row.pop(k, None)
                if k in ('metric_path', 'entity_path') and looks_secret_like_path(row.get(k)):
                    row[k] = '[REDACTED]'
        return safe

    # --- surfaces ------------------------------------------------------------

    def health(self, *, principal_id: Any = None, stub_token_id: Any = None) -> Dict[str, Any]:
        """Unauthenticated-safe probe (no store data), or authenticated lab health."""
        data = {
            'status': 'lab_ready',
            'lab_mode': True,
            'schema_version': FACADE_SCHEMA_VERSION,
            'phase3_snapshot_schema': SNAPSHOT_SCHEMA_VERSION,
            'network_started': False,
        }
        if principal_id is None and stub_token_id is None:
            return _ok(data, reason='health')
        principal, err = self._gate(
            principal_id=principal_id,
            stub_token_id=stub_token_id,
            permission=PERM_READ,  # any authenticated read-capable; collectors fail authz
            operation='health',
        )
        # Collectors / auditors may call health with authn-only: retry authn without perm
        if err and err.get('status') == 'authz_denied':
            p2, aerr, arc = self._authenticate(
                principal_id=principal_id, stub_token_id=stub_token_id,
            )
            if aerr:
                return _err('authn_failed', aerr)
            assert p2 is not None
            if not self._emit(
                event_type=ET_READ, outcome=OUT_SUCCESS, operation='health',
                reason_code=RC_HEALTH_OK, actor_kind=p2.kind,
                actor_id_safe=safe_actor_id(principal_id),
            ):
                return _err('audit_failed', _GENERIC_REJECT)
            return _ok(data, reason='health')
        if err:
            return err
        assert principal is not None
        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='health',
            reason_code=RC_HEALTH_OK, actor_kind=principal.kind,
            actor_id_safe=safe_actor_id(principal_id),
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(data, reason='health')

    def read_schema(self, *, principal_id: Any, stub_token_id: Any) -> Dict[str, Any]:
        p, aerr, arc = self._authenticate(
            principal_id=principal_id, stub_token_id=stub_token_id,
        )
        actor = safe_actor_id(principal_id)
        if aerr:
            self._emit(
                event_type=ET_AUTHN, outcome=OUT_FAILURE, operation='schema',
                reason_code=arc, actor_kind='unknown', actor_id_safe=actor,
            )
            return _err('authn_failed', aerr)
        assert p is not None
        data = {
            'schema_version': FACADE_SCHEMA_VERSION,
            'phase3_snapshot_schema': SNAPSHOT_SCHEMA_VERSION,
            'lab_only': True,
            'frozen_phase3_api': True,
        }
        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='schema',
            reason_code=RC_SCHEMA_OK, actor_kind=p.kind, actor_id_safe=actor,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(data, reason='schema')

    def read_observations(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        device_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        source_timestamp_start: Optional[str] = None,
        source_timestamp_end: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_READ, operation='observation_read',
        )
        if err:
            return err
        assert principal is not None
        actor = safe_actor_id(principal_id)

        if device_id is not None and not _s(device_id):
            self._emit(
                event_type=ET_READ, outcome=OUT_REJECTED, operation='observation_read',
                reason_code=RC_INVALID_SCOPE, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('invalid_scope', _GENERIC_REJECT)
        if metric_name is not None and not _s(metric_name):
            self._emit(
                event_type=ET_READ, outcome=OUT_REJECTED, operation='observation_read',
                reason_code=RC_INVALID_QUERY, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('invalid_query', _GENERIC_REJECT)

        lim = self._max_records if limit is None else int(limit)
        if lim < 0 or lim > self._max_records:
            self._emit(
                event_type=ET_READ, outcome=OUT_REJECTED, operation='observation_read',
                reason_code=RC_LIMIT_EXCEEDED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('limit_exceeded', _GENERIC_REJECT)

        try:
            rows = self._store.query(
                device_id=device_id,
                metric_name=metric_name,
                source_timestamp_start=source_timestamp_start,
                source_timestamp_end=source_timestamp_end,
                limit=lim,
            )
            safe_rows = [self._scrub_obs(r) for r in rows]
            # Deterministic order by observation_id then device
            safe_rows.sort(key=lambda r: (
                _s(r.get('device_id')),
                _s(r.get('metric_name')),
                _s(r.get('observation_id')),
            ))
        except Exception:
            self._emit(
                event_type=ET_READ, outcome=OUT_FAILURE, operation='observation_read',
                reason_code=RC_REDACTION_FAILED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('redaction_failed', _GENERIC_REJECT)

        payload = {'count': len(safe_rows), 'observations': safe_rows}
        bounded, berr = self._bounded(payload)
        if berr:
            self._emit(
                event_type=ET_READ, outcome=OUT_REJECTED, operation='observation_read',
                reason_code=RC_LIMIT_EXCEEDED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return berr

        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='observation_read',
            reason_code=RC_READ_OK, actor_kind=principal.kind, actor_id_safe=actor,
            device_scope_safe=device_id or principal.device_scope,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(copy.deepcopy(bounded), reason='observation_read')

    def read_snapshot(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        generated_at: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_READ, operation='snapshot_read',
        )
        if err:
            return err
        assert principal is not None
        return self._snapshot_body(
            principal=principal, principal_id=principal_id,
            generated_at=generated_at, device_id=device_id, limit=limit,
            export=False,
        )

    def export_snapshot(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        generated_at: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_READ, operation='snapshot_export',
        )
        if err:
            return err
        assert principal is not None
        az, az_rc = self._authorize(principal, PERM_EXPORT)
        actor = safe_actor_id(principal_id)
        if az:
            self._emit(
                event_type=ET_AUTHZ, outcome=OUT_DENIED, operation='snapshot_export',
                reason_code=az_rc, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('authz_denied', az)
        return self._snapshot_body(
            principal=principal, principal_id=principal_id,
            generated_at=generated_at, device_id=device_id, limit=limit,
            export=True,
        )

    def _snapshot_body(
        self,
        *,
        principal: LabStubPrincipal,
        principal_id: Any,
        generated_at: Optional[str],
        device_id: Optional[str],
        limit: Optional[int],
        export: bool,
    ) -> Dict[str, Any]:
        actor = safe_actor_id(principal_id)
        lim = limit
        if lim is not None and (int(lim) < 0 or int(lim) > self._max_records):
            self._emit(
                event_type=ET_EXPORT if export else ET_READ,
                outcome=OUT_REJECTED, operation='snapshot_export' if export else 'snapshot_read',
                reason_code=RC_LIMIT_EXCEEDED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('limit_exceeded', _GENERIC_REJECT)
        try:
            snap = export_series_snapshot(
                self._store,
                generated_at=generated_at,
                device_id=device_id,
                limit=lim,
            )
            safe = self._scrub_snapshot(snap)
        except Exception:
            self._emit(
                event_type=ET_READ, outcome=OUT_FAILURE,
                operation='snapshot_export' if export else 'snapshot_read',
                reason_code=RC_REDACTION_FAILED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('redaction_failed', _GENERIC_REJECT)

        data: Dict[str, Any] = {'snapshot': safe}
        if export:
            data['json'] = snapshot_to_json(safe)

        bounded, berr = self._bounded(data)
        if berr:
            self._emit(
                event_type=ET_EXPORT if export else ET_READ,
                outcome=OUT_REJECTED,
                operation='snapshot_export' if export else 'snapshot_read',
                reason_code=RC_LIMIT_EXCEEDED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return berr

        op = 'snapshot_export' if export else 'snapshot_read'
        et = ET_EXPORT if export else ET_READ
        rc = RC_EXPORT_OK if export else RC_READ_OK
        if not self._emit(
            event_type=et, outcome=OUT_SUCCESS, operation=op,
            reason_code=rc, actor_kind=principal.kind, actor_id_safe=actor,
            device_scope_safe=device_id or '',
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(copy.deepcopy(bounded), reason=op)

    def read_delta(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        device_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        pairwise: bool = False,
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_READ, operation='delta_read',
        )
        if err:
            return err
        assert principal is not None
        actor = safe_actor_id(principal_id)
        rows = self._store.query(
            device_id=device_id, metric_name=metric_name, limit=self._max_records,
        )
        try:
            if pairwise:
                deltas = pairwise_deltas(rows)
                safe = [self._scrub_delta(d) for d in deltas]
            else:
                d = latest_delta(rows)
                safe = self._scrub_delta(d) if d else None
        except Exception:
            self._emit(
                event_type=ET_READ, outcome=OUT_FAILURE, operation='delta_read',
                reason_code=RC_REDACTION_FAILED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('redaction_failed', _GENERIC_REJECT)

        payload = {'delta': safe}
        bounded, berr = self._bounded(payload)
        if berr:
            self._emit(
                event_type=ET_READ, outcome=OUT_REJECTED, operation='delta_read',
                reason_code=RC_LIMIT_EXCEEDED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return berr
        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='delta_read',
            reason_code=RC_READ_OK, actor_kind=principal.kind, actor_id_safe=actor,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(copy.deepcopy(bounded), reason='delta_read')

    def read_catalog(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        path: Any,
        platform: str = '',
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_READ, operation='catalog_read',
        )
        if err:
            return err
        assert principal is not None
        actor = safe_actor_id(principal_id)
        if not _s(path):
            self._emit(
                event_type=ET_READ, outcome=OUT_REJECTED, operation='catalog_read',
                reason_code=RC_INVALID_QUERY, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('invalid_query', _GENERIC_REJECT)
        if looks_secret_like_path(path):
            # Do not echo path; catalog also rejects
            result = lookup_metric('redacted/secret/path', platform=platform)
        else:
            result = lookup_metric(path, platform=platform)
        try:
            safe = self._scrub_catalog(result)
        except Exception:
            self._emit(
                event_type=ET_READ, outcome=OUT_FAILURE, operation='catalog_read',
                reason_code=RC_REDACTION_FAILED, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('redaction_failed', _GENERIC_REJECT)
        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='catalog_read',
            reason_code=RC_READ_OK, actor_kind=principal.kind, actor_id_safe=actor,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(safe, reason='catalog_read')

    def read_quarantine_summary(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Summaries from audit quarantine events (store never retains quarantined)."""
        # Allow telemetry_read OR telemetry_audit_read
        p, aerr, arc = self._authenticate(
            principal_id=principal_id, stub_token_id=stub_token_id,
        )
        actor = safe_actor_id(principal_id)
        if aerr:
            self._emit(
                event_type=ET_AUTHN, outcome=OUT_FAILURE, operation='quarantine_read',
                reason_code=arc, actor_kind='unknown', actor_id_safe=actor,
            )
            return _err('authn_failed', aerr)
        assert p is not None
        az_r, _ = self._authorize(p, PERM_READ)
        az_a, _ = self._authorize(p, PERM_AUDIT_READ)
        if az_r and az_a:
            self._emit(
                event_type=ET_AUTHZ, outcome=OUT_DENIED, operation='quarantine_read',
                reason_code=RC_AUTHZ_DENIED, actor_kind=p.kind, actor_id_safe=actor,
            )
            return _err('authz_denied', _GENERIC_AUTHZ)

        lim = self._max_records if limit is None else int(limit)
        if lim < 0 or lim > self._max_records:
            return _err('limit_exceeded', _GENERIC_REJECT)

        events = self._audit.query(outcome=OUT_QUARANTINED, limit=lim)
        summaries = []
        for ev in events:
            summaries.append({
                'event_id': ev.get('event_id'),
                'reason_code': ev.get('reason_code'),
                'observation_id': ev.get('observation_id'),
                'catalog_status': ev.get('catalog_status'),
                'device_scope_safe': ev.get('device_scope_safe'),
                'sequence': ev.get('sequence'),
            })
        summaries.sort(key=lambda r: int(r.get('sequence') or 0))
        payload = {'count': len(summaries), 'quarantine': summaries}
        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='quarantine_read',
            reason_code=RC_READ_OK, actor_kind=p.kind, actor_id_safe=actor,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok(copy.deepcopy(payload), reason='quarantine_read')

    def read_audit_events(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        reason_code: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_AUDIT_READ, operation='audit_read',
            expected_kind=KIND_OPERATOR,
        )
        if err:
            # collectors fail kind mismatch or authz — keep generic
            return err
        assert principal is not None
        lim = self._max_records if limit is None else int(limit)
        if lim < 0 or lim > self._max_records:
            return _err('limit_exceeded', _GENERIC_REJECT)
        events = self._audit.query(
            event_type=event_type, outcome=outcome, reason_code=reason_code, limit=lim,
        )
        # Ensure allowlist only
        safe = [{k: e.get(k) for k in EVENT_KEYS} for e in events]
        actor = safe_actor_id(principal_id)
        if not self._emit(
            event_type=ET_READ, outcome=OUT_SUCCESS, operation='audit_read',
            reason_code=RC_READ_OK, actor_kind=principal.kind, actor_id_safe=actor,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok({'count': len(safe), 'events': copy.deepcopy(safe)}, reason='audit_read')

    def export_audit_events(
        self,
        *,
        principal_id: Any,
        stub_token_id: Any,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        principal, err = self._gate(
            principal_id=principal_id, stub_token_id=stub_token_id,
            permission=PERM_AUDIT_READ, operation='audit_export',
            expected_kind=KIND_OPERATOR,
        )
        if err:
            return err
        assert principal is not None
        actor = safe_actor_id(principal_id)
        az, az_rc = self._authorize(principal, PERM_EXPORT)
        if az:
            self._emit(
                event_type=ET_AUTHZ, outcome=OUT_DENIED, operation='audit_export',
                reason_code=az_rc, actor_kind=principal.kind, actor_id_safe=actor,
            )
            return _err('authz_denied', az)
        base = self.read_audit_events(
            principal_id=principal_id, stub_token_id=stub_token_id, limit=limit,
        )
        if not base.get('ok'):
            return base
        data = base['data']
        try:
            text = json.dumps(data, sort_keys=True)
        except Exception:
            return _err('redaction_failed', _GENERIC_REJECT)
        if len(text.encode('utf-8')) > self._max_bytes:
            return _err('limit_exceeded', _GENERIC_REJECT)
        if not self._emit(
            event_type=ET_EXPORT, outcome=OUT_SUCCESS, operation='audit_export',
            reason_code=RC_EXPORT_OK, actor_kind=principal.kind, actor_id_safe=actor,
        ):
            return _err('audit_failed', _GENERIC_REJECT)
        return _ok({'events': data['events'], 'count': data['count'], 'json': text}, reason='audit_export')

    def deny_raw_payload(self, *, principal_id: Any = None, stub_token_id: Any = None) -> Dict[str, Any]:
        self._emit(
            event_type=ET_DENY, outcome=OUT_DENIED, operation='raw_payload_read',
            reason_code=RC_RAW_PAYLOAD_DENIED, actor_kind='unknown',
            actor_id_safe=safe_actor_id(principal_id),
        )
        return _err('authz_denied', _GENERIC_AUTHZ)

    def deny_topology_read(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self._emit(
            event_type=ET_DENY, outcome=OUT_DENIED, operation='topology_read',
            reason_code=RC_TOPOLOGY_READ_DENIED, actor_kind='unknown',
            actor_id_safe=safe_actor_id(kwargs.get('principal_id')),
        )
        return _err('authz_denied', _GENERIC_AUTHZ)

    def deny_topology_write(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self._emit(
            event_type=ET_DENY, outcome=OUT_DENIED, operation='topology_write',
            reason_code=RC_TOPOLOGY_DENIED, actor_kind='unknown',
            actor_id_safe=safe_actor_id(kwargs.get('principal_id')),
        )
        return _err('authz_denied', _GENERIC_AUTHZ)

    def ingest(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Ingest is LabTelemetryIngestor-only — always denied on facade."""
        self._emit(
            event_type=ET_DENY, outcome=OUT_DENIED, operation='ingest',
            reason_code=RC_INGEST_VIA_FACADE_DENIED, actor_kind='unknown',
            actor_id_safe=safe_actor_id(kwargs.get('principal_id')),
        )
        return _err('authz_denied', _GENERIC_AUTHZ)


def build_lab_facade(**kwargs: Any) -> LabGateDFacade:
    return LabGateDFacade(**kwargs)
