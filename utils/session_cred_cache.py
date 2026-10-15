"""In-memory session credential cache — process lifetime only (cleared on shutdown)."""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional

_lock = threading.Lock()
_cache: Dict[str, str] = {}


def get_session_credentials() -> Optional[Dict[str, str]]:
    with _lock:
        if not _cache:
            return None
        return dict(_cache)


def public_session_view() -> Dict[str, Any]:
    """Sidebar restore payload — never includes secret values."""
    creds = get_session_credentials() or {}
    return {
        'username': creds.get('username', ''),
        'label': creds.get('label', ''),
        'credential_id': creds.get('credential_id', ''),
        'secondary_credential_id': creds.get('secondary_credential_id', ''),
        'secondary_label': creds.get('secondary_label', ''),
        'third_credential_id': creds.get('third_credential_id', ''),
        'third_label': creds.get('third_label', ''),
        'snmp_credential_id': creds.get('snmp_credential_id', ''),
        'snmp_label': creds.get('snmp_label', ''),
        'has_password': bool(creds.get('password')),
        'has_enable_password': bool(creds.get('enable_password')),
        'has_become_password': bool(creds.get('become_password')),
        'has_snmp_profile': bool(creds.get('snmp_credential_id')),
    }


def set_session_credentials(
    *,
    username: str = '',
    password: str = '',
    enable_password: str = '',
    become_password: str = '',
    label: str = '',
    credential_id: str = '',
    secondary_credential_id: str = '',
    secondary_label: str = '',
    third_credential_id: str = '',
    third_label: str = '',
    snmp_credential_id: str = '',
    snmp_label: str = '',
) -> None:
    with _lock:
        cid = (credential_id or '').strip()
        sec_cid = (secondary_credential_id or '').strip()
        third_cid = (third_credential_id or '').strip()
        snmp_cid = (snmp_credential_id or '').strip()
        if not any((username, password, enable_password, become_password, label, cid, sec_cid, third_cid, snmp_cid)):
            _cache.clear()
            return
        _cache['username'] = username or ''
        _cache['label'] = label or ''
        _cache['credential_id'] = cid
        _cache['secondary_credential_id'] = sec_cid
        _cache['secondary_label'] = secondary_label or ''
        _cache['third_credential_id'] = third_cid
        _cache['third_label'] = third_label or ''
        _cache['snmp_credential_id'] = snmp_cid
        _cache['snmp_label'] = snmp_label or ''
        if cid:
            _cache['password'] = ''
            _cache['enable_password'] = ''
            _cache['become_password'] = ''
            return
        _cache['password'] = password or ''
        _cache['enable_password'] = enable_password or ''
        _cache['become_password'] = become_password or ''


def clear_session_credentials() -> None:
    with _lock:
        _cache.clear()


def register_session_cache_lifecycle() -> None:
    """Clear in-memory credentials on normal process exit."""
    import atexit
    atexit.register(clear_session_credentials)


def update_from_execute_payload(data: Dict[str, Any]) -> None:
    """Persist sidebar credentials used for a task dispatch."""
    if not data:
        return
    existing = get_session_credentials() or {}
    cid = (data.get('credential_id') or '').strip()
    sec_cid = (data.get('secondary_credential_id') or '').strip()
    third_cid = (data.get('third_credential_id') or '').strip()
    snmp_cid = (data.get('snmp_credential_id') or '').strip()
    username = (data.get('username') or '').strip() or existing.get('username', '')
    label = (data.get('cred_label') or data.get('label') or '').strip() or existing.get('label', '')
    sec_label = (data.get('secondary_label') or '').strip() or existing.get('secondary_label', '')
    third_label = (data.get('third_label') or '').strip() or existing.get('third_label', '')
    snmp_label = (data.get('snmp_label') or '').strip() or existing.get('snmp_label', '')
    if cid:
        set_session_credentials(
            username=username,
            password='',
            enable_password='',
            become_password='',
            label=label,
            credential_id=cid,
            secondary_credential_id=sec_cid or existing.get('secondary_credential_id', ''),
            secondary_label=sec_label,
            third_credential_id=third_cid or existing.get('third_credential_id', ''),
            third_label=third_label,
            snmp_credential_id=snmp_cid or existing.get('snmp_credential_id', ''),
            snmp_label=snmp_label,
        )
        return
    password = data.get('password')
    if password in (None, ''):
        password = existing.get('password', '')
    enable_password = data.get('enable_pwd') or data.get('enable_password')
    if enable_password in (None, ''):
        enable_password = existing.get('enable_password', '')
    become_password = data.get('become_password')
    if become_password in (None, ''):
        become_password = existing.get('become_password', '')
    set_session_credentials(
        username=username,
        password=password or '',
        enable_password=enable_password or '',
        become_password=become_password or '',
        label=label,
        credential_id='',
        secondary_credential_id=sec_cid,
        secondary_label=sec_label,
        third_credential_id=third_cid,
        third_label=third_label,
        snmp_credential_id=snmp_cid,
        snmp_label=snmp_label,
    )

