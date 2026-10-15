"""Lab-only in-memory audit-event sink (Phase 4).

Redacted, structured security evidence for lab ingest tests.
Never writes to disk, opens sockets, or starts threads.

NOT production audit, durable retention, or compliance evidence.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any, Dict, List, Optional

REDACTED = '[REDACTED]'
REDACTION_VERSION = 'lab-audit-1'
UNKNOWN = 'unknown'

# Allowlisted event keys only.
EVENT_KEYS = (
    'event_id',
    'event_type',
    'outcome',
    'actor_kind',
    'actor_id_safe',
    'device_scope_safe',
    'operation',
    'observation_id',
    'catalog_status',
    'reason_code',
    'sequence',
    'lab_only',
    'redaction_version',
)

# Event types
ET_AUTHN = 'authn'
ET_AUTHZ = 'authz'
ET_INGEST = 'ingest'
ET_SNAPSHOT = 'snapshot'
ET_DENY = 'deny'
ET_CONFIG = 'config'
ET_SINK = 'sink'
ET_READ = 'read'
ET_EXPORT = 'export'

# Outcomes
OUT_SUCCESS = 'success'
OUT_FAILURE = 'failure'
OUT_DENIED = 'denied'
OUT_REJECTED = 'rejected'
OUT_QUARANTINED = 'quarantined'
OUT_DUPLICATE = 'duplicate'
OUT_OVERFLOW = 'overflow'

# Stable reason codes (never raw exception text)
RC_MISSING_PRINCIPAL = 'MISSING_PRINCIPAL'
RC_UNKNOWN_PRINCIPAL = 'UNKNOWN_PRINCIPAL'
RC_TOKEN_MISMATCH = 'TOKEN_MISMATCH'
RC_EXPIRED = 'PRINCIPAL_EXPIRED'
RC_REVOKED = 'PRINCIPAL_REVOKED'
RC_KIND_MISMATCH = 'KIND_MISMATCH'
RC_AUTHN_OK = 'AUTHN_OK'
RC_AUTHZ_OK = 'AUTHZ_OK'
RC_AUTHZ_DENIED = 'AUTHZ_DENIED'
RC_UNKNOWN_PERMISSION = 'UNKNOWN_PERMISSION'
RC_MALFORMED_INPUT = 'MALFORMED_INPUT'
RC_RAW_PROTOCOL = 'RAW_PROTOCOL_REJECTED'
RC_QUARANTINED = 'QUARANTINED'
RC_SECRET_LIKE = 'SECRET_LIKE_REJECTED'
RC_DEVICE_SCOPE = 'DEVICE_SCOPE_DENIED'
RC_INGEST_ACCEPTED = 'INGEST_ACCEPTED'
RC_DUPLICATE_FIRST_WINS = 'DUPLICATE_FIRST_WINS'
RC_INSERT_REJECTED = 'INSERT_REJECTED'
RC_SNAPSHOT_OK = 'SNAPSHOT_OK'
RC_SNAPSHOT_AUTHN = 'SNAPSHOT_AUTHN_FAILED'
RC_SNAPSHOT_AUTHZ = 'SNAPSHOT_AUTHZ_DENIED'
RC_TOPOLOGY_DENIED = 'TOPOLOGY_ACCESS_DENIED'
RC_RAW_EXPORT_DENIED = 'RAW_PAYLOAD_EXPORT_DENIED'
RC_LAB_MODE_REQUIRED = 'LAB_MODE_REQUIRED'
RC_BIND_REFUSED = 'BIND_REFUSED'
RC_PERSISTENCE_REFUSED = 'PERSISTENCE_REFUSED'
RC_TOPOLOGY_CFG_REFUSED = 'TOPOLOGY_CFG_REFUSED'
RC_RAW_OUTPUT_REFUSED = 'RAW_OUTPUT_CFG_REFUSED'
RC_AUDIT_WRITE_FAILED = 'AUDIT_WRITE_FAILED'
RC_OVERFLOW = 'AUDIT_OVERFLOW_EVICTED'
RC_AUDIT_READ_DENIED = 'AUDIT_READ_DENIED'
RC_INVALID_SCOPE = 'INVALID_SCOPE'
RC_INVALID_QUERY = 'INVALID_QUERY'
RC_LIMIT_EXCEEDED = 'LIMIT_EXCEEDED'
RC_REDACTION_FAILED = 'REDACTION_FAILED'
RC_READ_OK = 'READ_OK'
RC_EXPORT_OK = 'EXPORT_OK'
RC_HEALTH_OK = 'HEALTH_OK'
RC_SCHEMA_OK = 'SCHEMA_OK'
RC_TOPOLOGY_READ_DENIED = 'TOPOLOGY_READ_DENIED'
RC_INGEST_VIA_FACADE_DENIED = 'INGEST_VIA_FACADE_DENIED'
RC_RAW_PAYLOAD_DENIED = 'RAW_PAYLOAD_READ_DENIED'

_SECRET_NAME_FRAGMENTS = (
    'password', 'passwd', 'secret', 'token', 'credential', 'private_key',
    'api_key', 'authorization', 'cookie',
)


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def safe_actor_id(principal_id: Any) -> str:
    """Deterministic non-reversible marker for actor ids (never store raw tokens)."""
    pid = _s(principal_id)
    if not pid:
        return REDACTED
    digest = hashlib.sha256(f'lab-actor:{pid}'.encode('utf-8')).hexdigest()[:12]
    return f'actor:{digest}'


def safe_device_scope(scope: Any) -> str:
    """Sorted device ids joined, or redacted if empty/unknown."""
    if scope is None:
        return REDACTED
    if isinstance(scope, (set, frozenset, list, tuple)):
        parts = sorted({_s(x) for x in scope if _s(x)})
        return ','.join(parts) if parts else REDACTED
    text = _s(scope)
    return text if text else REDACTED


def looks_secret_like_path(path: Any) -> bool:
    low = _s(path).lower()
    if not low:
        return False
    return any(frag in low for frag in _SECRET_NAME_FRAGMENTS)


def redact_event_fields(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only allowlisted keys; coerce types; drop unsafe content."""
    out: Dict[str, Any] = {k: None for k in EVENT_KEYS}
    out['lab_only'] = True
    out['redaction_version'] = REDACTION_VERSION
    out['actor_id_safe'] = REDACTED
    out['device_scope_safe'] = REDACTED
    out['outcome'] = UNKNOWN
    out['event_type'] = UNKNOWN
    out['operation'] = UNKNOWN
    out['reason_code'] = UNKNOWN

    if not isinstance(raw, dict):
        out['reason_code'] = RC_MALFORMED_INPUT
        out['outcome'] = OUT_REJECTED
        return out

    for key in EVENT_KEYS:
        if key not in raw:
            continue
        val = raw[key]
        if key == 'lab_only':
            out[key] = True
            continue
        if key == 'redaction_version':
            out[key] = REDACTION_VERSION
            continue
        if key == 'actor_id_safe':
            text = _s(val)
            if not text or text == REDACTED:
                out[key] = REDACTED
            elif text.startswith('actor:'):
                out[key] = text
            else:
                out[key] = safe_actor_id(text)
            continue
        if key == 'device_scope_safe':
            out[key] = safe_device_scope(val)
            continue
        if key in (
            'event_id', 'event_type', 'outcome', 'actor_kind', 'operation',
            'observation_id', 'catalog_status', 'reason_code',
        ):
            text = _s(val)
            if key == 'observation_id':
                out[key] = text or None
            elif key in ('event_type', 'outcome', 'operation', 'reason_code'):
                out[key] = text or UNKNOWN
            else:
                out[key] = text or None
            continue
        if key == 'sequence':
            try:
                out[key] = int(val)
            except (TypeError, ValueError):
                out[key] = None
            continue

    out['lab_only'] = True
    out['redaction_version'] = REDACTION_VERSION
    return out


class LabAuditSink:
    """Bounded in-memory lab audit sink. Oldest-first eviction."""

    def __init__(
        self,
        *,
        lab_mode: bool = False,
        max_events: int = 200,
    ) -> None:
        if lab_mode is not True:
            raise ValueError('LabAuditSink requires explicit lab_mode=True')
        if int(max_events) < 1:
            raise ValueError('max_events must be >= 1')
        self._lab_mode = True
        self._max = int(max_events)
        self._events: List[Dict[str, Any]] = []
        self._seq = 0
        self._overflow_count = 0
        self._write_failures = 0

    @property
    def lab_only(self) -> bool:
        return self._lab_mode

    @property
    def overflow_count(self) -> int:
        return self._overflow_count

    @property
    def write_failures(self) -> int:
        return self._write_failures

    def stats(self) -> Dict[str, Any]:
        return {
            'lab_only': True,
            'stored': len(self._events),
            'max_events': self._max,
            'overflow_count': self._overflow_count,
            'write_failures': self._write_failures,
            'next_sequence': self._seq + 1,
        }

    def reset(self) -> None:
        self._events.clear()
        self._seq = 0
        self._overflow_count = 0
        self._write_failures = 0

    def record(self, **fields: Any) -> bool:
        """Redact and append. Returns True on success, False on failure.

        Never raises with secret-bearing content. On internal failure increments
        write_failures and returns False (fail-closed signal for callers).
        """
        try:
            self._seq += 1
            seq = self._seq
            payload = dict(fields)
            payload['sequence'] = seq
            payload.setdefault('event_id', f'lab-evt-{seq}')
            payload['lab_only'] = True
            event = redact_event_fields(payload)
            event['sequence'] = seq
            event['event_id'] = f'lab-evt-{seq}'
            event = {k: event.get(k) for k in EVENT_KEYS}

            while len(self._events) >= self._max:
                self._events.pop(0)
                self._overflow_count += 1
                if len(self._events) < self._max:
                    self._seq += 1
                    overflow = redact_event_fields({
                        'event_type': ET_SINK,
                        'outcome': OUT_OVERFLOW,
                        'operation': 'evict',
                        'reason_code': RC_OVERFLOW,
                        'actor_kind': 'system',
                        'actor_id_safe': REDACTED,
                        'sequence': self._seq,
                        'event_id': f'lab-evt-{self._seq}',
                    })
                    overflow['sequence'] = self._seq
                    overflow['event_id'] = f'lab-evt-{self._seq}'
                    overflow = {k: overflow.get(k) for k in EVENT_KEYS}
                    # Only append overflow marker if it fits; avoid infinite loop
                    if len(self._events) < self._max:
                        self._events.append(overflow)
                    break

            if len(self._events) >= self._max:
                self._events.pop(0)
                self._overflow_count += 1
            self._events.append(event)
            return True
        except Exception:
            self._write_failures += 1
            return False

    def query(
        self,
        *,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        reason_code: Optional[str] = None,
        operation: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Deterministic ascending sequence order; defensive copies."""
        rows = list(self._events)
        if event_type is not None:
            et = _s(event_type)
            rows = [r for r in rows if r.get('event_type') == et]
        if outcome is not None:
            oc = _s(outcome)
            rows = [r for r in rows if r.get('outcome') == oc]
        if reason_code is not None:
            rc = _s(reason_code)
            rows = [r for r in rows if r.get('reason_code') == rc]
        if operation is not None:
            op = _s(operation)
            rows = [r for r in rows if r.get('operation') == op]
        rows.sort(key=lambda r: int(r.get('sequence') or 0))
        if limit is not None:
            lim = max(0, int(limit))
            rows = rows[:lim]
        return [copy.deepcopy(r) for r in rows]


def classify_authn_failure(
    *,
    principal_id: Any,
    stub_token_id: Any,
    principal: Any,
    expected_kind: Optional[str],
) -> str:
    """Map authn failure to a stable reason code (no secret echo)."""
    pid = _s(principal_id)
    token = _s(stub_token_id)
    if not pid or not token:
        return RC_MISSING_PRINCIPAL
    if principal is None:
        return RC_UNKNOWN_PRINCIPAL
    status = _s(getattr(principal, 'status', None))
    if status == 'expired':
        return RC_EXPIRED
    if status == 'revoked':
        return RC_REVOKED
    if _s(getattr(principal, 'stub_token_id', None)) != token:
        return RC_TOKEN_MISMATCH
    if expected_kind and _s(getattr(principal, 'kind', None)) != _s(expected_kind):
        return RC_KIND_MISMATCH
    return RC_UNKNOWN_PRINCIPAL
