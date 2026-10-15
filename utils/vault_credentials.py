# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - utils/vault_credentials.py
# ============================================================================
# PURPOSE: Resolve vault credential_id for execute tasks with fallback support.
# PROVIDES: Functions to resolve primary, secondary, and tertiary credentials.
#
# KEY_FUNCTIONS:
#   - resolve_execute_credentials(credential_id, secondary_credential_id, third_credential_id):
#     Resolves primary, secondary, and tertiary credentials from vault
#   - public_credential_view(record):
#     Returns safe view of credential without secrets
#
# CREDENTIAL_FALLBACK:
#   resolve_execute_credentials() constructs fallback_creds list
#   Includes secondary and tertiary credentials if provided
#   Returns bundle with fallback_credentials, secondary_credential, third_credential
#
# VAULT_STRUCTURE:
#   - Vault is username-keyed (credential_id is username, not UUID)
#   - Stored in modules/credential_manager.py with Fernet encryption
#   - Loopback is not identity; explicit id maps to stored secrets
#
# SECRET_FIELDS:
#   - password, admin_password, become_password, enable_password, secret
#   - private_key, token, api_key, passphrase, credential_key
#   - snmp_community, snmp_v3_auth_key, snmp_v3_priv_key
#
# CONNECTIONS:
#   - Called by: vlan_checker_web.py (credential resolution for /api/execute)
#   - Uses: modules/credential_manager.py (credential retrieval)
#   - Used by: utils/collection_credentials.py (credential bundling)
#
# USAGE_PATTERN:
#   vault_extras = resolve_execute_credentials(primary_id, secondary_id, third_id)
#   credentials = bundle_for_plugin(primary_record, vault_extras)
#
# ============================================================================
"""Resolve vault credential_id for execute tasks.

The vault is username-keyed. ``credential_id`` is that username, not a UUID.
Loopback is not identity; this module only maps an explicit id to stored secrets.
API responses must use public_credential_view — never the decrypted vault record.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


_SECRET_FIELD_NAMES = frozenset({
    'password',
    'admin_password',
    'become_password',
    'enable_password',
    'enable_pwd',
    'secret',
    'private_key',
    'privatekey',
    'token',
    'api_key',
    'apikey',
    'passphrase',
    'credential_key',
    'master_password',
    'snmp_community',
    'snmp_v3_auth_key',
    'snmp_v3_priv_key',
})


class CredentialResolveError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def public_credential_view(record: Optional[Dict[str, Any]], username: str = '') -> Optional[Dict[str, Any]]:
    """Metadata-only credential record. Never copies unknown or secret fields."""
    if not record:
        return None
    uname = str(record.get('username') or record.get('credential_id') or username or '').strip()
    if 'has_admin' in record:
        has_admin = bool(record.get('has_admin'))
    else:
        has_admin = bool(record.get('admin_password'))
    if 'has_become' in record:
        has_become = bool(record.get('has_become'))
    else:
        has_become = bool(record.get('become_password'))
    has_snmp = record.get('has_snmp')
    if has_snmp is None:
        from modules.credential_manager import _credential_has_snmp
        has_snmp = _credential_has_snmp(record)
    snmp_version = str(record.get('snmp_version') or 'none')
    return {
        'credential_id': str(record.get('credential_id') or uname),
        'username': uname,
        'label': str(record.get('label') or uname),
        'has_admin': has_admin,
        'has_become': has_become,
        'has_snmp': bool(has_snmp),
        'snmp_version': snmp_version if has_snmp else 'none',
        'profile_type': str(record.get('profile_type') or 'ssh_and_snmp'),
        'has_ssh': bool(record.get('has_ssh')) if 'has_ssh' in record else (
            str(record.get('profile_type') or 'ssh_and_snmp') != 'snmp_only'
            and bool(record.get('password')) and record.get('password') != '-'
        ),
        'created_at': record.get('created_at'),
        'updated_at': record.get('updated_at'),
        'last_used_at': record.get('last_used_at'),
        'available': True,
    }


def mapping_has_secret_fields(obj: Any) -> bool:
    """True when a JSON-like object contains secret-bearing keys with values."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            kl = str(key).lower().replace('-', '_')
            if kl.startswith('has_'):
                if mapping_has_secret_fields(value):
                    return True
                continue
            if kl in _SECRET_FIELD_NAMES or kl.endswith('_password') or 'private_key' in kl:
                if value not in (None, '', False, True):
                    return True
            if mapping_has_secret_fields(value):
                return True
        return False
    if isinstance(obj, (list, tuple)):
        return any(mapping_has_secret_fields(item) for item in obj)
    return False


def parse_credential_id(raw: Any) -> Optional[str]:
    """Return a vault key, or None if the field is omitted.

    Present-but-invalid values fail closed.
    """
    if raw is None:
        return None
    if isinstance(raw, bool) or isinstance(raw, (int, float)):
        raise CredentialResolveError('Invalid credential_id')
    s = str(raw).strip()
    if s == '':
        return None
    if len(s) > 128:
        raise CredentialResolveError('Invalid credential_id')
    if any(c in s for c in '/\\:\x00') or '..' in s:
        raise CredentialResolveError('Invalid credential_id')
    return s


def _load_vault_record(credential_manager, cid: str) -> Dict[str, Any]:
    if credential_manager is None:
        raise CredentialResolveError('Credential manager not available', 500)
    if credential_manager.is_master_password_required():
        raise CredentialResolveError(
            'Credential vault is locked. Unlock with master password first.',
            403,
        )
    cred = credential_manager.get_credential(cid)
    if not cred:
        raise CredentialResolveError('Unknown or deleted credential_id', 404)
    try:
        credential_manager.record_use(cid)
    except Exception as exc:
        # Do not silently ignore vault I/O when an ID was requested
        import logging
        logging.getLogger(__name__).warning('record_use failed for %s: %s', cid, exc)
    return cred


def apply_snmp_credential_id(
    bundle: Dict[str, Any],
    data: Optional[Dict[str, Any]],
    credential_manager,
    session_creds: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """When snmp_credential_id is set, overlay SNMP secrets from that vault profile."""
    from utils.collection_credentials import overlay_snmp_fields

    data = data or {}
    session_creds = session_creds or {}
    snmp_cid = parse_credential_id(data.get('snmp_credential_id'))
    if not snmp_cid:
        snmp_cid = parse_credential_id(session_creds.get('snmp_credential_id'))
    if not snmp_cid:
        return bundle
    if snmp_cid == bundle.get('credential_id'):
        return bundle
    cred = _load_vault_record(credential_manager, snmp_cid)
    from utils.credential_profiles import profile_has_snmp_config
    if not profile_has_snmp_config(cred):
        raise CredentialResolveError(
            f"SNMP profile '{snmp_cid}' has no SNMP configuration",
            400,
        )
    out = overlay_snmp_fields(bundle, cred)
    out['snmp_credential_id'] = snmp_cid
    out['snmp_label'] = cred.get('label') or snmp_cid
    return out


def _resolve_optional_vault_cred(cid_raw: Any, credential_manager) -> Optional[Dict[str, Any]]:
    cid = parse_credential_id(cid_raw)
    if not cid:
        return None
    if not credential_manager:
        raise CredentialResolveError('Credential manager not available', 500)
    # Fail closed when an ID was requested (locked / unknown)
    cred = _load_vault_record(credential_manager, cid)
    return {
        'username': cred.get('username') or cid,
        'password': cred.get('password') or '',
        'enable_pwd': cred.get('admin_password') or '',
        'become_password': cred.get('become_password') or '',
        'credential_id': cid,
        'label': cred.get('label') or cid,
    }


def resolve_execute_credentials(
    data: Optional[Dict[str, Any]],
    credential_manager,
    session_creds: Optional[Dict[str, str]] = None,
    *,
    credential_id_required: bool = False,
) -> Dict[str, Any]:
    """Build username/password/enable/become for a task.

    If credential_id is set, the vault is authoritative (fail closed on
    missing, deleted, locked, or mismatched username). Otherwise the
    request body plus in-memory session cache is used (existing console path).

    When ``credential_id_required`` is True (``/api/execute``), client
    plaintext secrets are rejected and a vault ``credential_id`` is mandatory.
    """
    data = data or {}
    session_creds = session_creds or {}

    if credential_id_required and mapping_has_secret_fields(data):
        raise CredentialResolveError(
            'Plaintext secrets in the request body are not allowed. '
            'Select a vault credential.',
            400,
        )

    cid = parse_credential_id(data.get('credential_id'))
    if not cid:
        if credential_id_required:
            # Never silently reuse session cache for /api/execute. An empty
            # credential_id in the body is an operator/UI failure (the
            # "hidden credentials" class) — fail closed so the sidebar
            # Primary select must be sent explicitly.
            raise CredentialResolveError(
                'credential_id required. Select a Primary vault profile in the sidebar '
                '(Settings passwords are draft-only and are not used for SSH).',
                400,
            )
        else:
            payload_password = data.get('password')
            if payload_password in (None, ''):
                cid = parse_credential_id(session_creds.get('credential_id'))

    sec_cid = parse_credential_id(data.get('secondary_credential_id')) or parse_credential_id(session_creds.get('secondary_credential_id'))
    third_cid = parse_credential_id(data.get('third_credential_id')) or parse_credential_id(session_creds.get('third_credential_id'))

    secondary_cred = _resolve_optional_vault_cred(sec_cid, credential_manager)
    third_cred = _resolve_optional_vault_cred(third_cid, credential_manager)

    fallback_creds = []
    if secondary_cred:
        fallback_creds.append(secondary_cred)
    if third_cred:
        fallback_creds.append(third_cred)

    if cid:
        if credential_manager is None:
            raise CredentialResolveError('Credential manager not available', 500)
        if credential_manager.is_master_password_required():
            raise CredentialResolveError(
                'Credential vault is locked. Unlock with master password first.',
                403,
            )
        username_payload = (data.get('username') or '').strip()
        if username_payload and username_payload != cid:
            raise CredentialResolveError('credential_id does not match username')
        cred = credential_manager.get_credential(cid)
        if not cred:
            raise CredentialResolveError('Unknown or deleted credential_id', 404)
        from utils.credential_profiles import normalize_profile_type
        if credential_id_required and normalize_profile_type(cred.get('profile_type')) == 'snmp_only':
            raise CredentialResolveError(
                'credential_id must be an SSH-capable profile. '
                'Select an SSH profile for credential_id and an SNMP profile for snmp_credential_id.',
                400,
            )
        try:
            credential_manager.record_use(cid)
        except Exception:
            pass
        bundle = {
            'username': cred.get('username') or cid,
            'password': cred.get('password') or '',
            'enable_pwd': cred.get('admin_password') or '',
            'become_password': cred.get('become_password') or '',
            'credential_id': cid,
            'label': cred.get('label') or cid,
            'source': 'vault',
            'secondary_credential_id': sec_cid or None,
            'third_credential_id': third_cid or None,
            'secondary_credential': secondary_cred,
            'third_credential': third_cred,
            'fallback_credentials': fallback_creds,
            'snmp_version': cred.get('snmp_version') or 'none',
            'snmp_community': cred.get('snmp_community') or '',
            'snmp_port': cred.get('snmp_port') or 161,
            'snmp_v3_user': cred.get('snmp_v3_user') or '',
            'snmp_v3_auth_protocol': cred.get('snmp_v3_auth_protocol') or 'sha',
            'snmp_v3_auth_key': cred.get('snmp_v3_auth_key') or '',
            'snmp_v3_priv_protocol': cred.get('snmp_v3_priv_protocol') or 'aes',
            'snmp_v3_priv_key': cred.get('snmp_v3_priv_key') or '',
        }
        return apply_snmp_credential_id(bundle, data, credential_manager, session_creds)

    if credential_id_required:
        raise CredentialResolveError(
            'credential_id required. Store credentials in Settings and select a vault profile.',
            400,
        )

    user = (data.get('username') or '').strip() or session_creds.get('username') or ''
    password = data.get('password')
    if password in (None, ''):
        password = session_creds.get('password') or ''
    enable_pwd = data.get('enable_pwd') or data.get('enable_password')
    if enable_pwd in (None, ''):
        enable_pwd = session_creds.get('enable_password') or ''
    become = data.get('become_password')
    if become in (None, ''):
        become = session_creds.get('become_password') or ''
    base = {
        'username': user,
        'password': password or '',
        'enable_pwd': enable_pwd or '',
        'become_password': become or '',
        'credential_id': None,
        'label': (data.get('cred_label') or data.get('label') or session_creds.get('label') or '').strip(),
        'source': 'payload_or_session',
        'secondary_credential_id': sec_cid or None,
        'third_credential_id': third_cid or None,
        'secondary_credential': secondary_cred,
        'third_credential': third_cred,
        'fallback_credentials': fallback_creds,
        'snmp_version': 'none',
        'snmp_community': '',
        'snmp_port': 161,
        'snmp_v3_user': '',
        'snmp_v3_auth_protocol': 'sha',
        'snmp_v3_auth_key': '',
        'snmp_v3_priv_protocol': 'aes',
        'snmp_v3_priv_key': '',
    }
    return apply_snmp_credential_id(base, data, credential_manager, session_creds)


def flask_resolve_error(exc: CredentialResolveError) -> Tuple[Any, int]:
    from flask import jsonify
    return jsonify({'status': 'error', 'error': exc.message}), exc.status


def _cli_error_code(status: int) -> str:
    if status == 403:
        return 'vault_locked'
    if status == 404:
        return 'unknown_credential_id'
    if status == 500:
        return 'vault_unavailable'
    return 'invalid_credential_id'


def resolve_cli_connect_credentials(
    data: Optional[Dict[str, Any]],
    credential_manager,
    session_creds: Optional[Dict[str, str]] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Resolve CLI Socket.IO credentials (credential_id only).

    Vault credential_id is mandatory. Client password/enable fields are ignored
    and never used as a fallback. HTTP session RAM passwords are not used
    (Socket.IO session isolation); only a session credential_id may be reused.
    """
    if data is None or not isinstance(data, dict):
        return None, {
            'error': 'Malformed connection payload',
            'code': 'malformed_payload',
        }
    raw_cid = data.get('credential_id')
    cid_present = raw_cid is not None and str(raw_cid).strip() != ''
    try:
        if cid_present:
            vault_only = {
                'credential_id': raw_cid,
                'username': data.get('username') or '',
            }
            resolved = resolve_execute_credentials(vault_only, credential_manager, None)
            return resolved, None
        session_creds = session_creds or {}
        session_cid = parse_credential_id(session_creds.get('credential_id'))
        if session_cid:
            resolved = resolve_execute_credentials(
                {'credential_id': session_cid},
                credential_manager,
                None,
            )
            return resolved, None
        return None, {
            'error': (
                'credential_id required. Store a vault credential and select it '
                'in the CLI terminal. Plaintext Socket.IO passwords are not supported.'
            ),
            'code': 'credential_id_required',
        }
    except CredentialResolveError as exc:
        return None, {
            'error': exc.message,
            'code': _cli_error_code(exc.status),
            'status': exc.status,
        }


def public_cli_status_payload(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Whitelist Socket.IO cli_status / cli_error fields. Never copies secrets."""
    allowed = {
        'status', 'message', 'hostname', 'code', 'credential_id', 'username',
        'label',
    }
    out: Dict[str, Any] = {}
    for key, value in (extra or {}).items():
        if key in allowed:
            out[key] = value
    return out
