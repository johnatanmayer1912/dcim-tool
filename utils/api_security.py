"""Flask API security helpers for credential and sensitive routes."""
from __future__ import annotations

import os

from flask import request

DEFAULT_WEB_BIND = '127.0.0.1'
DEFAULT_WEB_PORT = 5051
_LOOPBACK_BIND_HOSTS = frozenset({'127.0.0.1', '::1', 'localhost'})


def resolve_web_port(requested=None):
    """Single source of truth for HTTP bind/CORS/CSRF port (default 5051)."""
    if requested is not None:
        try:
            p = int(requested)
            if 1 <= p <= 65535:
                return p
        except (TypeError, ValueError):
            pass
    for key in ('NST_WEB_PORT', 'NST_CLI_BROWSER_QA_PORT', 'PORT'):
        raw = (os.environ.get(key) or '').strip()
        if raw.isdigit():
            p = int(raw)
            if 1 <= p <= 65535:
                return p
    return DEFAULT_WEB_PORT


def resolve_web_bind_host(requested=None, allow_nonlocal_env=None):
    """Default loopback. Refuse non-loopback binds unless NST_ALLOW_NONLOCAL_BIND=1."""
    if requested is None:
        raw = (os.environ.get('NST_BIND') or DEFAULT_WEB_BIND).strip() or DEFAULT_WEB_BIND
    else:
        raw = str(requested).strip() or DEFAULT_WEB_BIND
    if allow_nonlocal_env is None:
        allow_src = os.environ.get('NST_ALLOW_NONLOCAL_BIND', '')
    else:
        allow_src = allow_nonlocal_env
    allowed = str(allow_src).strip().lower() in ('1', 'true', 'yes')
    if raw.lower() not in _LOOPBACK_BIND_HOSTS and not allowed:
        raise ValueError(
            f'Refusing to bind {raw}. Default is {DEFAULT_WEB_BIND}. '
            'Set NST_ALLOW_NONLOCAL_BIND=1 only if you accept LAN exposure.'
        )
    return raw


def client_is_localhost() -> bool:
    """True when the request originates from loopback.

    Empty/missing remote_addr is not trusted (proxy or mis-set WSGI environ).
    """
    addr = (request.remote_addr or '').strip()
    return addr in ('127.0.0.1', '::1', 'localhost')


def _trusted_origin_parts():
    port = resolve_web_port()
    return frozenset({
        ('http', '127.0.0.1', port),
        ('http', 'localhost', port),
        ('https', '127.0.0.1', port),
        ('https', 'localhost', port),
        ('http', '::1', port),
        ('https', '::1', port),
    })


# Exact (scheme, host, port) tuples. Prefix matching is not used (RB-ZT-02).
# Recomputed via resolve_web_port() so CSRF matches the bound port.
_TRUSTED_ORIGIN_PARTS = _trusted_origin_parts()

# Dual-mode console: browser UI *and* local pytest/curl. Empty Origin/Referer on a
# loopback client is an explicit local-automation exception, not identity.
# Nonlocal clients are rejected by client_is_localhost() before this check.
EMPTY_ORIGIN_POLICY = 'loopback_local_automation'


def _origin_parts(value: str, *, allow_path: bool):
    """Parse Origin (no path) or Referer (path allowed) into (scheme, host, port).

    Returns None for empty, False for malformed / untrusted-shape values.
    """
    from urllib.parse import urlparse

    raw = (value or '').strip()
    if not raw:
        return None
    if any(c in raw for c in ' \t\r\n\'",<>'):
        return False
    if ',' in raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme not in ('http', 'https'):
        return False
    host = (parsed.hostname or '').lower()
    if not host:
        return False
    if parsed.username or parsed.password:
        return False
    if not allow_path:
        if parsed.path not in ('', '/') or parsed.query or parsed.fragment:
            return False
    try:
        port = parsed.port
    except ValueError:
        return False
    if port is None:
        port = 443 if parsed.scheme == 'https' else 80
    return (parsed.scheme, host, int(port))


def request_origin_is_trusted() -> bool:
    """True for the local UI origin, or empty Origin/Referer (local automation).

    Loopback is not identity. Foreign and prefix-lookalike origins are denied.
    """
    origin = (request.headers.get('Origin') or '').strip()
    referer = (request.headers.get('Referer') or '').strip()
    if origin:
        parts = _origin_parts(origin, allow_path=False)
        if parts is False or parts is None:
            return False
        return parts in _trusted_origin_parts()
    if referer:
        parts = _origin_parts(referer, allow_path=True)
        if parts is False or parts is None:
            return False
        return parts in _trusted_origin_parts()
    return True


def require_trusted_origin():
    """Block cross-site mutating requests to the local console (CSRF)."""
    from flask import jsonify
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return None, None
    if request_origin_is_trusted():
        return None, None
    return jsonify({
        'error': 'Cross-origin requests are not allowed. Use the local web UI.',
    }), 403


PLUGIN_INSTALL_MODEL = 'offline_local_directory'
PLUGIN_UPLOAD_DISABLED_ERROR = (
    'Runtime plugin upload is disabled. Install plugins only by placing '
    'trusted .py files in the operator-controlled plugins directory '
    '(modules/plugins, or the EXE sidecar plugins folder) then Reload or restart. '
    'AST checks are not a sandbox.'
)


def plugin_upload_is_enabled() -> bool:
    """Runtime HTTP plugin upload is permanently disabled (RB-ZT-01).

    Environment variables cannot re-enable upload. Trusted plugins load only
    from the on-disk plugins directory.
    """
    return False


def plugin_install_model() -> dict:
    return {
        'runtime_upload': False,
        'install_model': PLUGIN_INSTALL_MODEL,
        'execution_model': 'in_process',
        'sandbox': False,
        'trust_warning': (
            'Plugins from the local plugins directory execute in-process as the '
            'NST process user. AST denylist is not a sandbox. HTTP upload is disabled. '
            'Reload is a deliberate local operator action.'
        ),
    }


def require_local_credential_access():
    """
    Credential vault routes must be accessed from localhost only.
    Returns (None, None) if OK, else (response, status_code).
    """
    from flask import jsonify
    if not client_is_localhost():
        return jsonify({
            'error': 'Credential API is restricted to localhost. '
                     'Run the web UI on this machine only.',
        }), 403
    return None, None


def require_credential_vault_unlocked(credential_manager):
    """Vault must be unlocked (master password) before read/write secrets."""
    from flask import jsonify
    if credential_manager is None:
        return jsonify({'error': 'Credential manager not available'}), 500
    if credential_manager.is_master_password_required():
        return jsonify({
            'error': 'Credential vault is locked. Unlock with master password first.',
        }), 403
    return None, None


def audit_credential_access(log_func, action: str, username: str = '', detail: str = ''):
    if log_func:
        who = request.remote_addr or 'unknown'
        log_func(f"[Credential Audit] {action} user={username or '-'} from={who} {detail}".strip())


def audit_execute_dispatch(log_func, action: str, *, credential_id: str = '', device_count: int = 0, detail: str = ''):
    """Operator execute audit — no secrets."""
    if log_func:
        who = request.remote_addr or 'unknown'
        cid = (credential_id or '-').strip() or '-'
        log_func(
            f"[Execute Audit] action={action} credential_id={cid} "
            f"devices={device_count} from={who} {detail}".strip()
        )
