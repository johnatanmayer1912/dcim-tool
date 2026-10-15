"""Lab-only localhost telemetry ingest prototype (Phase 4).

In-process adapter: normalize → catalog → ObservationStore → snapshot.
Requires explicit ``lab_mode=True``. Never opens sockets, threads, or
persistent storage. Test-only authentication stubs — not production auth.

Integrates ``LabAuditSink`` for redacted in-memory security evidence.

NON-GOALS: live collectors, gRPC, mTLS, persistence, UI, topology writes,
public binds, packaging, durable audit.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Optional, Tuple

from utils.telemetry.lab_audit import (
    ET_AUTHN,
    ET_AUTHZ,
    ET_CONFIG,
    ET_DENY,
    ET_INGEST,
    ET_SNAPSHOT,
    LabAuditSink,
    OUT_DENIED,
    OUT_DUPLICATE,
    OUT_FAILURE,
    OUT_QUARANTINED,
    OUT_REJECTED,
    OUT_SUCCESS,
    RC_AUTHN_OK,
    RC_AUTHZ_DENIED,
    RC_AUTHZ_OK,
    RC_AUDIT_READ_DENIED,
    RC_BIND_REFUSED,
    RC_DEVICE_SCOPE,
    RC_DUPLICATE_FIRST_WINS,
    RC_EXPIRED,
    RC_INGEST_ACCEPTED,
    RC_INSERT_REJECTED,
    RC_KIND_MISMATCH,
    RC_LAB_MODE_REQUIRED,
    RC_MALFORMED_INPUT,
    RC_MISSING_PRINCIPAL,
    RC_PERSISTENCE_REFUSED,
    RC_QUARANTINED,
    RC_RAW_EXPORT_DENIED,
    RC_RAW_OUTPUT_REFUSED,
    RC_RAW_PROTOCOL,
    RC_REVOKED,
    RC_SECRET_LIKE,
    RC_SNAPSHOT_AUTHN,
    RC_SNAPSHOT_AUTHZ,
    RC_SNAPSHOT_OK,
    RC_TOKEN_MISMATCH,
    RC_TOPOLOGY_CFG_REFUSED,
    RC_TOPOLOGY_DENIED,
    RC_UNKNOWN_PERMISSION,
    RC_UNKNOWN_PRINCIPAL,
    safe_actor_id,
)
from utils.telemetry.normalize import normalize_observation
from utils.telemetry.snapshot import export_series_snapshot, snapshot_to_json
from utils.telemetry.store import INSERT_DUPLICATE, INSERT_INSERTED, ObservationStore

LOOPBACK_HOSTS = frozenset({'127.0.0.1', '::1', 'localhost'})

PERM_INGEST = 'telemetry_ingest'
PERM_READ = 'telemetry_read'
PERM_EXPORT = 'telemetry_export'
PERM_AUDIT_READ = 'telemetry_audit_read'

KIND_COLLECTOR = 'collector'
KIND_OPERATOR = 'operator'

STATUS_ACTIVE = 'active'
STATUS_EXPIRED = 'expired'
STATUS_REVOKED = 'revoked'

_GENERIC_AUTHN_FAIL = 'authentication failed'
_GENERIC_AUTHZ_FAIL = 'authorization denied'
_GENERIC_REJECT = 'request rejected'


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def assert_loopback_bind_host(bind_host: Any) -> str:
    """Refuse wildcard / public / non-loopback bind configuration."""
    host = _s(bind_host).lower()
    if not host:
        raise ValueError('bind_host required; lab ingest allows loopback only')
    if host in ('0.0.0.0', '::', '*', '[::]'):
        raise ValueError('wildcard bind refused; lab ingest is loopback-only')
    if host not in LOOPBACK_HOSTS:
        raise ValueError('non-loopback bind refused; lab ingest is loopback-only')
    return host


@dataclass(frozen=True)
class LabStubPrincipal:
    """Test-only principal. Not a production credential or mTLS identity."""

    principal_id: str
    kind: str
    permissions: FrozenSet[str] = field(default_factory=frozenset)
    device_scope: FrozenSet[str] = field(default_factory=frozenset)
    status: str = STATUS_ACTIVE
    stub_token_id: str = ''


@dataclass(frozen=True)
class LabAuthContext:
    """Registry of test-only stub principals (collector vs operator)."""

    principals: Tuple[LabStubPrincipal, ...] = ()

    def get(self, principal_id: Any) -> Optional[LabStubPrincipal]:
        pid = _s(principal_id)
        if not pid:
            return None
        for p in self.principals:
            if p.principal_id == pid:
                return p
        return None


@dataclass(frozen=True)
class LabIngestResult:
    ok: bool
    status: str
    reason: str
    observation_id: Optional[str] = None
    catalog_status: Optional[str] = None
    device_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ok': self.ok,
            'status': self.status,
            'reason': self.reason,
            'observation_id': self.observation_id,
            'catalog_status': self.catalog_status,
            'device_id': self.device_id,
        }


def default_lab_auth_context() -> LabAuthContext:
    """Deterministic fixtures for tests — not production identities."""
    return LabAuthContext(
        principals=(
            LabStubPrincipal(
                principal_id='lab-collector-a',
                kind=KIND_COLLECTOR,
                permissions=frozenset({PERM_INGEST}),
                device_scope=frozenset({'edge-xe-01', 'leaf-nx-01', 'qfx-01'}),
                status=STATUS_ACTIVE,
                stub_token_id='stub-collector-token-a',
            ),
            LabStubPrincipal(
                principal_id='lab-operator-a',
                kind=KIND_OPERATOR,
                permissions=frozenset({PERM_READ, PERM_EXPORT}),
                device_scope=frozenset(),
                status=STATUS_ACTIVE,
                stub_token_id='stub-operator-token-a',
            ),
            LabStubPrincipal(
                principal_id='lab-auditor-a',
                kind=KIND_OPERATOR,
                permissions=frozenset({PERM_AUDIT_READ}),
                device_scope=frozenset(),
                status=STATUS_ACTIVE,
                stub_token_id='stub-auditor-token-a',
            ),
            LabStubPrincipal(
                principal_id='lab-collector-expired',
                kind=KIND_COLLECTOR,
                permissions=frozenset({PERM_INGEST}),
                device_scope=frozenset({'edge-xe-01'}),
                status=STATUS_EXPIRED,
                stub_token_id='stub-expired',
            ),
            LabStubPrincipal(
                principal_id='lab-collector-revoked',
                kind=KIND_COLLECTOR,
                permissions=frozenset({PERM_INGEST}),
                device_scope=frozenset({'edge-xe-01'}),
                status=STATUS_REVOKED,
                stub_token_id='stub-revoked',
            ),
        )
    )


class LabTelemetryIngestor:
    """In-process lab ingest boundary. Does not listen on a network port."""

    def __init__(
        self,
        *,
        lab_mode: bool = False,
        bind_host: str = '127.0.0.1',
        auth_context: Optional[LabAuthContext] = None,
        audit_sink: Optional[LabAuditSink] = None,
        max_observations: int = 100,
        max_audit_events: int = 200,
        enable_persistence: bool = False,
        enable_topology_integration: bool = False,
        enable_raw_payload_output: bool = False,
        disable_lab_mode: bool = False,
    ) -> None:
        # Optional pre-built sink records config failures before instance exists.
        provisional = audit_sink

        def _cfg(reason_code: str) -> None:
            if provisional is not None:
                provisional.record(
                    event_type=ET_CONFIG,
                    outcome=OUT_REJECTED,
                    operation='construct',
                    reason_code=reason_code,
                    actor_kind='system',
                    actor_id_safe='system',
                )

        if disable_lab_mode or lab_mode is not True:
            _cfg(RC_LAB_MODE_REQUIRED)
            raise ValueError('explicit lab_mode=True is required; production mode refused')
        if enable_persistence:
            _cfg(RC_PERSISTENCE_REFUSED)
            raise ValueError('persistence refused in lab ingest prototype')
        if enable_topology_integration:
            _cfg(RC_TOPOLOGY_CFG_REFUSED)
            raise ValueError('topology integration refused in lab ingest prototype')
        if enable_raw_payload_output:
            _cfg(RC_RAW_OUTPUT_REFUSED)
            raise ValueError('raw payload output refused in lab ingest prototype')

        try:
            host = assert_loopback_bind_host(bind_host)
        except ValueError:
            _cfg(RC_BIND_REFUSED)
            raise

        if provisional is not None:
            if not getattr(provisional, 'lab_only', False):
                raise ValueError('audit_sink must be lab-only')
            self._audit = provisional
        else:
            self._audit = LabAuditSink(lab_mode=True, max_events=max_audit_events)

        self._lab_mode = True
        self._bind_host = host
        self._auth = auth_context if auth_context is not None else default_lab_auth_context()
        self._store = ObservationStore(
            max_observations=max_observations,
            default_query_limit=max_observations,
        )
        self._network_started = False
        self._ready = False

    @property
    def lab_mode(self) -> bool:
        return self._lab_mode

    @property
    def bind_host(self) -> str:
        return self._bind_host

    @property
    def network_started(self) -> bool:
        return self._network_started

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def audit_sink(self) -> LabAuditSink:
        return self._audit

    def store_stats(self) -> Dict[str, Any]:
        return dict(self._store.stats())

    def start(self) -> None:
        assert_loopback_bind_host(self._bind_host)
        self._ready = True
        self._network_started = False

    def stop(self) -> None:
        self._ready = False
        self._network_started = False

    def start_network_listener(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError('network listener refused; lab ingest is in-process only')

    def _emit(self, **fields: Any) -> bool:
        return bool(self._audit.record(**fields))

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
            return None, _GENERIC_AUTHN_FAIL, RC_MISSING_PRINCIPAL
        principal = self._auth.get(pid)
        if principal is None:
            return None, _GENERIC_AUTHN_FAIL, RC_UNKNOWN_PRINCIPAL
        if principal.stub_token_id != token:
            return None, _GENERIC_AUTHN_FAIL, RC_TOKEN_MISMATCH
        if principal.status == STATUS_EXPIRED:
            return None, _GENERIC_AUTHN_FAIL, RC_EXPIRED
        if principal.status == STATUS_REVOKED:
            return None, _GENERIC_AUTHN_FAIL, RC_REVOKED
        if principal.status != STATUS_ACTIVE:
            return None, _GENERIC_AUTHN_FAIL, RC_REVOKED
        if expected_kind and principal.kind != expected_kind:
            return None, _GENERIC_AUTHN_FAIL, RC_KIND_MISMATCH
        return principal, None, RC_AUTHN_OK

    def _authorize(self, principal: LabStubPrincipal, permission: str) -> Tuple[Optional[str], str]:
        if not permission or permission not in {
            PERM_INGEST, PERM_READ, PERM_EXPORT, PERM_AUDIT_READ,
        }:
            return _GENERIC_AUTHZ_FAIL, RC_UNKNOWN_PERMISSION
        if permission not in principal.permissions:
            return _GENERIC_AUTHZ_FAIL, RC_AUTHZ_DENIED
        return None, RC_AUTHZ_OK

    def ingest(
        self,
        payload: Any,
        *,
        principal_id: Any = None,
        stub_token_id: Any = None,
        received_at: Optional[str] = None,
    ) -> LabIngestResult:
        principal, err, authn_rc = self._authenticate(
            principal_id=principal_id,
            stub_token_id=stub_token_id,
            expected_kind=KIND_COLLECTOR,
        )
        actor_safe = safe_actor_id(principal_id)
        if err:
            self._emit(
                event_type=ET_AUTHN,
                outcome=OUT_FAILURE,
                operation='ingest',
                reason_code=authn_rc,
                actor_kind=KIND_COLLECTOR,
                actor_id_safe=actor_safe,
            )
            return LabIngestResult(ok=False, status='authn_failed', reason=err)

        assert principal is not None
        if not self._emit(
            event_type=ET_AUTHN,
            outcome=OUT_SUCCESS,
            operation='ingest',
            reason_code=RC_AUTHN_OK,
            actor_kind=principal.kind,
            actor_id_safe=actor_safe,
            device_scope_safe=principal.device_scope,
        ):
            return LabIngestResult(
                ok=False, status='audit_failed', reason=_GENERIC_REJECT,
            )

        az_err, az_rc = self._authorize(principal, PERM_INGEST)
        if az_err:
            self._emit(
                event_type=ET_AUTHZ,
                outcome=OUT_DENIED,
                operation='ingest',
                reason_code=az_rc,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
                device_scope_safe=principal.device_scope,
            )
            return LabIngestResult(ok=False, status='authz_denied', reason=az_err)

        if not self._emit(
            event_type=ET_AUTHZ,
            outcome=OUT_SUCCESS,
            operation='ingest',
            reason_code=RC_AUTHZ_OK,
            actor_kind=principal.kind,
            actor_id_safe=actor_safe,
            device_scope_safe=principal.device_scope,
        ):
            return LabIngestResult(
                ok=False, status='audit_failed', reason=_GENERIC_REJECT,
            )

        if not isinstance(payload, dict):
            self._emit(
                event_type=ET_INGEST,
                outcome=OUT_REJECTED,
                operation='ingest',
                reason_code=RC_MALFORMED_INPUT,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
            )
            return LabIngestResult(ok=False, status='rejected', reason=_GENERIC_REJECT)

        if any(k in payload for k in ('raw_cli', 'ssh_output', 'snmp_pdu', 'protobuf', 'grpc_payload')):
            self._emit(
                event_type=ET_INGEST,
                outcome=OUT_REJECTED,
                operation='ingest',
                reason_code=RC_RAW_PROTOCOL,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
            )
            return LabIngestResult(ok=False, status='rejected', reason=_GENERIC_REJECT)

        obs = normalize_observation(payload, received_at=received_at)

        if obs.get('quarantined'):
            notes = ' '.join(str(n) for n in (obs.get('notes') or []))
            warnings = ' '.join(str(w) for w in (obs.get('warnings') or []))
            secretish = (
                'secret' in notes.lower()
                or 'secret' in warnings.lower()
                or any('secret' in str(k).lower() for k in (payload or {}).keys())
            )
            rc = RC_SECRET_LIKE if secretish else RC_QUARANTINED
            self._emit(
                event_type=ET_INGEST,
                outcome=OUT_QUARANTINED,
                operation='ingest',
                reason_code=rc,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
                observation_id=_s(obs.get('observation_id')) or None,
                catalog_status=_s(obs.get('catalog_status')) or None,
                device_scope_safe=_s(obs.get('device_id')) or 'unknown',
            )
            return LabIngestResult(
                ok=False,
                status='quarantined',
                reason=_GENERIC_REJECT,
                observation_id=_s(obs.get('observation_id')) or None,
                catalog_status=_s(obs.get('catalog_status')) or None,
                device_id=_s(obs.get('device_id')) or None,
            )

        device_id = _s(obs.get('device_id'))
        if not device_id or device_id == 'unknown':
            self._emit(
                event_type=ET_INGEST,
                outcome=OUT_REJECTED,
                operation='ingest',
                reason_code=RC_MALFORMED_INPUT,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
            )
            return LabIngestResult(ok=False, status='rejected', reason=_GENERIC_REJECT)

        if device_id not in principal.device_scope:
            self._emit(
                event_type=ET_AUTHZ,
                outcome=OUT_DENIED,
                operation='ingest',
                reason_code=RC_DEVICE_SCOPE,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
                device_scope_safe=principal.device_scope,
            )
            return LabIngestResult(ok=False, status='authz_denied', reason=_GENERIC_AUTHZ_FAIL)

        oid = _s(obs.get('observation_id'))
        if oid and self._store.get(oid) is not None:
            if not self._emit(
                event_type=ET_INGEST,
                outcome=OUT_DUPLICATE,
                operation='ingest',
                reason_code=RC_DUPLICATE_FIRST_WINS,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
                device_scope_safe=device_id,
                observation_id=oid,
                catalog_status=_s(obs.get('catalog_status')) or None,
            ):
                return LabIngestResult(
                    ok=False, status='audit_failed', reason=_GENERIC_REJECT,
                    observation_id=oid, device_id=device_id,
                )
            return LabIngestResult(
                ok=True,
                status='duplicate',
                reason='first-wins',
                observation_id=oid,
                catalog_status=_s(obs.get('catalog_status')) or None,
                device_id=device_id,
            )

        # Fail-closed: audit accept before insert so a sink failure cannot
        # silently claim an unrecorable acceptance.
        if not self._emit(
            event_type=ET_INGEST,
            outcome=OUT_SUCCESS,
            operation='ingest',
            reason_code=RC_INGEST_ACCEPTED,
            actor_kind=principal.kind,
            actor_id_safe=actor_safe,
            device_scope_safe=device_id,
            observation_id=oid or None,
            catalog_status=_s(obs.get('catalog_status')) or None,
        ):
            return LabIngestResult(
                ok=False, status='audit_failed', reason=_GENERIC_REJECT,
            )

        insert = self._store.insert(obs)
        st = insert.get('status')
        if st == INSERT_INSERTED:
            return LabIngestResult(
                ok=True,
                status='inserted',
                reason='accepted',
                observation_id=insert.get('observation_id'),
                catalog_status=_s(obs.get('catalog_status')) or None,
                device_id=device_id,
            )
        if st == INSERT_DUPLICATE:
            # Race-rare after get(); still report first-wins.
            self._emit(
                event_type=ET_INGEST,
                outcome=OUT_DUPLICATE,
                operation='ingest',
                reason_code=RC_DUPLICATE_FIRST_WINS,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
                device_scope_safe=device_id,
                observation_id=insert.get('observation_id'),
                catalog_status=_s(obs.get('catalog_status')) or None,
            )
            return LabIngestResult(
                ok=True,
                status='duplicate',
                reason='first-wins',
                observation_id=insert.get('observation_id'),
                catalog_status=_s(obs.get('catalog_status')) or None,
                device_id=device_id,
            )

        self._emit(
            event_type=ET_INGEST,
            outcome=OUT_REJECTED,
            operation='ingest',
            reason_code=RC_INSERT_REJECTED,
            actor_kind=principal.kind,
            actor_id_safe=actor_safe,
            observation_id=insert.get('observation_id'),
        )
        return LabIngestResult(
            ok=False,
            status='rejected',
            reason=_GENERIC_REJECT,
            observation_id=insert.get('observation_id'),
        )

    def snapshot(
        self,
        *,
        principal_id: Any = None,
        stub_token_id: Any = None,
        generated_at: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        principal, err, authn_rc = self._authenticate(
            principal_id=principal_id,
            stub_token_id=stub_token_id,
            expected_kind=KIND_OPERATOR,
        )
        actor_safe = safe_actor_id(principal_id)
        if err:
            self._emit(
                event_type=ET_AUTHN,
                outcome=OUT_FAILURE,
                operation='snapshot',
                reason_code=authn_rc if authn_rc != RC_AUTHN_OK else RC_SNAPSHOT_AUTHN,
                actor_kind=KIND_OPERATOR,
                actor_id_safe=actor_safe,
            )
            return {
                'ok': False,
                'status': 'authn_failed',
                'reason': err,
                'snapshot': None,
            }

        assert principal is not None
        az, az_rc = self._authorize(principal, PERM_READ)
        if az:
            self._emit(
                event_type=ET_AUTHZ,
                outcome=OUT_DENIED,
                operation='snapshot',
                reason_code=RC_SNAPSHOT_AUTHZ,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
            )
            return {
                'ok': False,
                'status': 'authz_denied',
                'reason': az,
                'snapshot': None,
            }
        az_ex, _ = self._authorize(principal, PERM_EXPORT)
        if az_ex:
            self._emit(
                event_type=ET_AUTHZ,
                outcome=OUT_DENIED,
                operation='snapshot',
                reason_code=RC_SNAPSHOT_AUTHZ,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
            )
            return {
                'ok': False,
                'status': 'authz_denied',
                'reason': az_ex,
                'snapshot': None,
            }

        if not self._emit(
            event_type=ET_SNAPSHOT,
            outcome=OUT_SUCCESS,
            operation='snapshot',
            reason_code=RC_SNAPSHOT_OK,
            actor_kind=principal.kind,
            actor_id_safe=actor_safe,
        ):
            return {
                'ok': False,
                'status': 'audit_failed',
                'reason': _GENERIC_REJECT,
                'snapshot': None,
            }

        snap = export_series_snapshot(
            self._store,
            generated_at=generated_at,
            device_id=device_id,
            limit=limit,
        )
        safe = copy.deepcopy(snap)
        self._scrub_snapshot(safe)
        return {
            'ok': True,
            'status': 'ok',
            'reason': 'snapshot',
            'snapshot': safe,
            'json': snapshot_to_json(safe),
        }

    def read_audit_events(
        self,
        *,
        principal_id: Any = None,
        stub_token_id: Any = None,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        reason_code: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Read-only audit retrieval; requires telemetry_audit_read (not snapshot perms)."""
        principal, err, authn_rc = self._authenticate(
            principal_id=principal_id,
            stub_token_id=stub_token_id,
            expected_kind=KIND_OPERATOR,
        )
        actor_safe = safe_actor_id(principal_id)
        if err:
            self._emit(
                event_type=ET_AUTHN,
                outcome=OUT_FAILURE,
                operation='audit_read',
                reason_code=authn_rc,
                actor_kind=KIND_OPERATOR,
                actor_id_safe=actor_safe,
            )
            return {'ok': False, 'status': 'authn_failed', 'reason': err, 'events': []}

        assert principal is not None
        az, az_rc = self._authorize(principal, PERM_AUDIT_READ)
        if az:
            self._emit(
                event_type=ET_AUTHZ,
                outcome=OUT_DENIED,
                operation='audit_read',
                reason_code=RC_AUDIT_READ_DENIED,
                actor_kind=principal.kind,
                actor_id_safe=actor_safe,
            )
            return {'ok': False, 'status': 'authz_denied', 'reason': az, 'events': []}

        events = self._audit.query(
            event_type=event_type,
            outcome=outcome,
            reason_code=reason_code,
            limit=limit,
        )
        return {'ok': True, 'status': 'ok', 'reason': 'audit_read', 'events': events}

    def topology_access(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self._emit(
            event_type=ET_DENY,
            outcome=OUT_DENIED,
            operation='topology',
            reason_code=RC_TOPOLOGY_DENIED,
            actor_kind='unknown',
            actor_id_safe=safe_actor_id(kwargs.get('principal_id')),
        )
        return {
            'ok': False,
            'status': 'authz_denied',
            'reason': _GENERIC_AUTHZ_FAIL,
        }

    def export_raw_payloads(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self._emit(
            event_type=ET_DENY,
            outcome=OUT_DENIED,
            operation='raw_export',
            reason_code=RC_RAW_EXPORT_DENIED,
            actor_kind='unknown',
            actor_id_safe=safe_actor_id(kwargs.get('principal_id')),
        )
        return {
            'ok': False,
            'status': 'authz_denied',
            'reason': _GENERIC_AUTHZ_FAIL,
        }

    @staticmethod
    def _scrub_snapshot(snap: Dict[str, Any]) -> None:
        forbidden = {
            'raw_payload', 'payload', 'password', 'token', 'secret',
            'private_key', 'credential', 'ssh_output', 'grpc_payload',
        }
        series = snap.get('series') or []
        if isinstance(series, list):
            for row in series:
                if not isinstance(row, dict):
                    continue
                for k in list(row.keys()):
                    if k.lower() in forbidden or 'password' in k.lower() or 'token' in k.lower():
                        row.pop(k, None)


def build_lab_ingestor(**kwargs: Any) -> LabTelemetryIngestor:
    """Factory requiring explicit lab_mode (default False → fail)."""
    return LabTelemetryIngestor(**kwargs)
