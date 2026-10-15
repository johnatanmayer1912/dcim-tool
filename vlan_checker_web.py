# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - vlan_checker_web.py
# ============================================================================
# PURPOSE: Main Flask web application entry point. Handles all HTTP API routes.
# ENTRY_POINT: This is the primary web server. Run via: python vlan_checker_web.py
# PORT: Default 5051 (configurable via NST_WEB_PORT env var)
#
# KEY_MODULES_CONNECTED:
#   - modules/plugin_registry.py: Plugin discovery and execution
#   - modules/credential_manager.py: Credential storage and retrieval
#   - modules/adapters.py: Task orchestration layer
#   - utils/collection_credentials.py: Credential bundling for plugins
#   - utils/vault_credentials.py: Vault credential resolution
#
# DATA_FLOW:
#   1. HTTP Request → Flask Route Handler
#   2. Route Handler → Credential Resolution (utils/vault_credentials.py)
#   3. Credential Resolution → Plugin Execution (modules/adapters.py)
#   4. Plugin Execution → Plugin Registry (modules/plugin_registry.py)
#   5. Plugin → Network Operations (modules/network_base.py)
#   6. Results → Response JSON
#
# CRITICAL_ROUTES:
#   - /api/execute: Generic plugin execution with credential fallback
#   - /api/discovery/run: Network discovery job execution
#   - /api/plugins/list: List available plugins
#   - /api/credentials/*: Credential management
#
# CREDENTIAL_FALLBACK_PATH:
#   /api/execute → resolve_execute_credentials() → bundle_for_plugin()
#   → run_generic_plugin() → plugin.run() with fallback_credentials dict
#
# PLUGIN_EXECUTION_PATH:
#   /api/execute → _plugin_execute_thread() → run_generic_plugin()
#   → PluginRegistry.execute() → plugin.run(device, credentials, params, config, log_func)
#
# ASSET_COLLECTION_SPECIFIC:
#   cisco_asset_warranty plugin uses modules/asset_collection_policy.py
#   which calls safe_connection() with fallback_credentials parameter
#
# ============================================================================
# CRITICAL: Install telnetlib compatibility for Python 3.13+
import sys
try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401

import os
import json
import re
import time
import threading
import webbrowser
import subprocess
import ipaddress
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Flask-SocketIO for CLI terminal interface (v5.0)
try:
    from flask_socketio import SocketIO, emit, disconnect, join_room
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("[WARNING] flask-socketio not available. CLI terminal feature disabled.")

def _get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):
        # 1. Check sys._MEIPASS first (bundled resources)
        if hasattr(sys, '_MEIPASS'):
            bundled_path = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(bundled_path):
                return bundled_path
        
        # 2. Check program directory (writable files like standards/ templates/)
        program_dir = os.path.dirname(sys.executable)
        program_path = os.path.join(program_dir, relative_path)
        if os.path.exists(program_path):
            return program_path
            
        # Fallback to bundled path
        return os.path.join(getattr(sys, '_MEIPASS', ''), relative_path)
    else:
        # Dev mode: Resolve relative to project root
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

def _read_version():
    """Read version from VERSION file (single source of truth)."""
    try:
        path = _get_resource_path("VERSION")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip().lstrip('v')
    except Exception:
        return "0.0.0-DEV"

if getattr(sys, 'frozen', False):
    # When bundled with PyInstaller, templates are in modules/web/templates
    template_folder = os.path.join(sys._MEIPASS, "modules", "web", "templates")
    app = Flask(__name__, template_folder=template_folder)
else:
    local_template_folder = os.path.join(os.path.dirname(__file__), "modules", "web", "templates")
    app = Flask(__name__, template_folder=local_template_folder)

# Process-local signing key (not persisted). Restart invalidates Flask cookies.
app.secret_key = os.urandom(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
# AI_CONTEXT: Flask operator console entry. Web-only; Tk is out of scope.
# AI_FLOW: index.html → /api/* → plugins/adapters → parsers → map shells / reports
# AI_DEPENDS_ON: utils.api_security, modules.credential_manager, PluginRegistry
# AI_IMPACTS: every operator action; discovery jobs; topology HTML
# AI_SECURITY_NOTE: Loopback + Origin is deployment isolation, not identity. No RBAC.
# AI_CRAWL_NOTE: /api/discovery/run|cancel|status — cancel is cooperative via job['cancel']
# AI_MAP_NOTE: Maps are files under reports/; served by discovery/L3/report routes
# AI_OFFLINE_NOTE: No CDN. vis.js bundled. Demo discovery needs no SSH.
# AI_BREADCRUMB: next — modules/plugins/network_discovery.py, utils/discovery_graph.py
# AI_TODO_NEXT: SSO is out of product scope; do not fake overlay collectors here.

try:
    from utils.session_cred_cache import register_session_cache_lifecycle
    register_session_cache_lifecycle()
except Exception:
    pass

# Initialize Flask-SocketIO for CLI terminal (v5.0)
if SOCKETIO_AVAILABLE:
    # v5.4.4: Hardened transport parameters for high-resiliency in restricted envs
    # CORS: product default is loopback via resolve_web_port(); CI may override via env.
    def _socketio_cors_origins():
        from utils.api_security import resolve_web_port
        p = resolve_web_port()
        origins = [
            f'http://127.0.0.1:{p}',
            f'http://localhost:{p}',
        ]
        # Preserve order, drop dupes
        return list(dict.fromkeys(origins))

    socketio = SocketIO(
        app,
        cors_allowed_origins=_socketio_cors_origins(),
        async_mode='threading',
        manage_session=False,  # v6.7.1: Fixes AttributeError with Flask 3.1
        logger=False,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=15,
        allow_upgrades=True
    )
    print("[INFO] Flask-SocketIO initialized for CLI terminal (v5.4.3)")
else:
    socketio = None

VERSION = _read_version()


def _read_update_date_label() -> str:
    """Operator-facing date line — keep in sync with VERSION + CHANGELOG title."""
    import re as _re
    from datetime import date as _date
    today = _date.today().isoformat()
    label = f"{today} — v{VERSION}"
    try:
        path = _get_resource_path('CHANGELOG.md')
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        # Prefer ### 7.x.y — Title under Unreleased
        m = _re.search(
            rf'^###\s+{_re.escape(VERSION)}\s+[—\-]\s+(.+)$',
            text,
            flags=_re.M,
        )
        if m:
            title = m.group(1).strip()
            if len(title) > 90:
                title = title[:87] + '…'
            return f"{today} — v{VERSION}: {title}"
    except Exception:
        pass
    return label


UPDATE_DATE = _read_update_date_label()


def _require_json_body():
    """Return (data_dict, error_response) for JSON POST bodies; error_response is (flask_response, status)."""
    if request.content_length and request.content_length > 0:
        if request.mimetype and 'json' not in request.mimetype:
            return None, (jsonify({"error": "Content-Type must be application/json"}), 415)
        data = request.get_json(silent=True)
        if data is None:
            return None, (jsonify({"error": "Invalid JSON body"}), 400)
        return data, None
    return request.get_json(silent=True) or {}, None


def _parse_bounded_int(value, default, field_name, *, min_val=None, max_val=None):
    try:
        n = int(value if value is not None and value != '' else default)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")
    if min_val is not None and n < min_val:
        raise ValueError(f"{field_name} must be >= {min_val}")
    if max_val is not None and n > max_val:
        raise ValueError(f"{field_name} must be <= {max_val}")
    return n


def _date_display_short(date_str: str) -> str:
    """Short date for sidebar UI (YYYY-MM-DD); full string kept for tooltip/docs."""
    s = (date_str or "").strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    for sep in ("—", "(", " "):
        if sep in s:
            return s.split(sep)[0].strip()
    return s


# v5.5.0: Startup logger for diagnosing EXE issues
def startup_log(msg):
    """Log startup messages with timestamp for debugging."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [STARTUP] {msg}")
    try:
        log_path = os.path.join(get_logs_dir(), "startup.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass  # Don't crash if log file can't be written

def log_dependencies():
    """Diagnostic splash: Log critical library versions for troubleshooting."""
    # v6.0.6: Simplified version detection for PyInstaller EXE compatibility
    # Just check if modules import successfully - don't check specific classes
    
    def check_module(module_name):
        """Check if module imports and get version if available."""
        try:
            mod = __import__(module_name)
            # Try to get version from various attributes
            for attr in ['__version__', 'VERSION', 'version', '__VERSION__']:
                ver = getattr(mod, attr, None)
                if ver:
                    return f"{ver}"
            return "OK"
        except Exception as e:
            return f"FAIL: {str(e)[:20]}"
    
    f_ver = check_module('flask')
    fs_ver = check_module('flask_socketio')
    s_ver = check_module('socketio')
    e_ver = check_module('engineio')
    sw_ver = check_module('simple_websocket')
    ws_p_ver = check_module('wsproto')
    bi_ver = check_module('bidict')
    
    diag_msg = (
        f"--- Dependency Splash (v6.0.6) ---\n"
        f"Flask: {f_ver}\n"
        f"Flask-SocketIO: {fs_ver}\n"
        f"Python-SocketIO: {s_ver}\n"
        f"Python-EngineIO: {e_ver}\n"
        f"Simple-WebSocket: {sw_ver}\n"
        f"wsproto: {ws_p_ver}\n"
        f"bidict: {bi_ver}\n"
        f"-----------------------------------"
    )
    add_log(diag_msg)


# Global state
# v6.2.6 / RB-ZT-03: bounded ring buffer; GET /api/logs snapshots, never drains.
from utils.operator_console_logs import (
    DEFAULT_LIMIT as _LOG_DEFAULT_LIMIT,
    MAX_LIMIT as _LOG_MAX_LIMIT,
    OperatorConsoleLogBuffer,
)
console_log_buffer = OperatorConsoleLogBuffer()

# v7.0.35: Session logs under dedicated data root (never install/CWD)
from utils.output_paths import get_data_root, get_logs_dir, new_session_log_path
os.makedirs(get_logs_dir(), exist_ok=True)
session_log_file = new_session_log_path()
startup_log(f"Output data root: {get_data_root()}")

# v7.0.18: Initialize credential manager for secure credential storage
try:
    from modules.credential_manager import CredentialManager
    from utils.output_paths import get_data_root
    _cred_dir = os.path.join(get_data_root(), 'credentials')
    os.makedirs(_cred_dir, exist_ok=True)
    credential_manager = CredentialManager(storage_dir=_cred_dir)
    startup_log("Credential manager initialized successfully")
except Exception as e:
    credential_manager = None
    startup_log(f"WARNING: Credential manager initialization failed: {e}")

@app.route('/health')
def health_check():
    """Simple HTTP health check to verify the server is reachable."""
    return "OK", 200

@app.route('/static/nst-enterprise.css')
def static_enterprise_css():
    """Offline enterprise design system (no CDN)."""
    from flask import send_file
    try:
        return send_file(
            _get_resource_path('modules/web/static/nst-enterprise.css'),
            mimetype='text/css',
        )
    except Exception:
        return "/* nst-enterprise.css missing */", 404, {'Content-Type': 'text/css'}


@app.route('/favicon.ico')
def favicon():
    """Serve favicon from root directory."""
    from flask import send_file
    try:
        return send_file(_get_resource_path('favicon_program.png'), mimetype='image/png')
    except:
        return "Not found", 404

@app.route('/static/favicon_program.png')
def static_favicon():
    """Serve favicon from static path for HTML reference."""
    from flask import send_file
    try:
        return send_file(_get_resource_path('favicon_program.png'), mimetype='image/png')
    except:
        return "Not found", 404

@app.route('/favicon_program.png')
def root_favicon_png():
    """Serve favicon from root path for HTML reference as requested."""
    from flask import send_file
    try:
        return send_file(_get_resource_path('favicon_program.png'), mimetype='image/png')
    except:
        return "Not found", 404

def _require_localhost_operator():
    """Loopback + same-origin gate for the operator console."""
    from utils.api_security import require_local_credential_access, require_trusted_origin
    denied, code = require_local_credential_access()
    if denied:
        return denied, code
    return require_trusted_origin()


def localhost_required(fn):
    """Decorator: mutation and credential-using APIs are loopback-only."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        denied, code = _require_localhost_operator()
        if denied:
            return denied, code
        return fn(*args, **kwargs)
    return wrapper


def _resolve_task_credentials(data, *, credential_id_required: bool = False):
    """Resolve credential_id server-side. Never serialize the returned secrets."""
    from utils.session_cred_cache import get_session_credentials, update_from_execute_payload
    from utils.vault_credentials import CredentialResolveError, flask_resolve_error, resolve_execute_credentials
    try:
        cached = get_session_credentials() or {}
        resolved = resolve_execute_credentials(
            data, credential_manager, cached,
            credential_id_required=credential_id_required,
        )
    except CredentialResolveError as cred_exc:
        return None, flask_resolve_error(cred_exc)
    if resolved.get('credential_id'):
        from utils.api_security import audit_credential_access
        audit_credential_access(add_log, 'RESOLVE', resolved['credential_id'])
        data['username'] = resolved['username']
        data['cred_label'] = resolved.get('label') or ''
        data['credential_id'] = resolved['credential_id']
        if resolved.get('secondary_credential_id'):
            data['secondary_credential_id'] = resolved['secondary_credential_id']
            data['secondary_label'] = (resolved.get('secondary_credential') or {}).get('label') or resolved['secondary_credential_id']
        if resolved.get('third_credential_id'):
            data['third_credential_id'] = resolved['third_credential_id']
            data['third_label'] = (resolved.get('third_credential') or {}).get('label') or resolved['third_credential_id']
        if resolved.get('snmp_credential_id'):
            data['snmp_credential_id'] = resolved['snmp_credential_id']
            data['snmp_label'] = resolved.get('snmp_label') or ''
        if resolved.get('fallback_credentials'):
            data['fallback_credentials'] = resolved['fallback_credentials']
        if resolved.get('secondary_credential'):
            data['secondary_credential'] = resolved['secondary_credential']
        if resolved.get('third_credential'):
            data['third_credential'] = resolved['third_credential']
        update_from_execute_payload({
            'credential_id': resolved['credential_id'],
            'username': resolved['username'],
            'cred_label': resolved.get('label') or '',
            'secondary_credential_id': resolved.get('secondary_credential_id') or '',
            'secondary_label': (resolved.get('secondary_credential') or {}).get('label') or resolved.get('secondary_credential_id') or '',
            'third_credential_id': resolved.get('third_credential_id') or '',
            'third_label': (resolved.get('third_credential') or {}).get('label') or resolved.get('third_credential_id') or '',
            'snmp_credential_id': resolved.get('snmp_credential_id') or '',
            'snmp_label': resolved.get('snmp_label') or '',
        })
    else:
        update_from_execute_payload(data)
    return resolved, None


def _overlay_request_secrets(data):
    """Copy vault secrets onto this request dict in memory for adapter routes."""
    resolved, err = _resolve_task_credentials(data, credential_id_required=True)
    if err:
        return err
    data['username'] = resolved['username']
    data['password'] = resolved['password']
    data['enable_pwd'] = resolved['enable_pwd']
    if resolved.get('fallback_credentials'):
        data['fallback_credentials'] = resolved['fallback_credentials']
    if resolved.get('secondary_credential'):
        data['secondary_credential'] = resolved['secondary_credential']
    if resolved.get('third_credential'):
        data['third_credential'] = resolved['third_credential']
    data['become_password'] = resolved.get('become_password') or ''
    return None


def _credentials_dict_from_request(data):
    """Build plugin/runner credentials including Secondary/Third fallback profiles."""
    creds = {
        'username': data.get('username'),
        'password': data.get('password'),
        'secret': data.get('enable_pwd'),
        'fallback_credentials': data.get('fallback_credentials') or [],
    }
    if data.get('secondary_credential'):
        creds['secondary_credential'] = data['secondary_credential']
    if data.get('third_credential'):
        creds['third_credential'] = data['third_credential']
    return creds


def _socketio_operator_denied():
    """Loopback + Origin for CLI Socket.IO events. Loopback is not identity."""
    from utils.api_security import request_origin_is_trusted, require_local_credential_access
    denied, _code = require_local_credential_access()
    if denied:
        return {'message': 'CLI is restricted to localhost.', 'code': 'nonlocal'}
    if not request_origin_is_trusted():
        return {'message': 'Cross-origin CLI is not allowed.', 'code': 'foreign_origin'}
    return None


@app.before_request
def _gate_console_to_localhost():
    """The whole operator UI is loopback-only; /health stays probeable."""
    path = request.path or ''
    if path in ('/health', '/favicon.ico', '/favicon_program.png'):
        return None
    if path.startswith('/static'):
        return None
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code
    return None


@app.route('/debug_status')
def debug_status():
    """Return JSON formatted dependency report for troubleshooting."""
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code

    def _pkg_ver(dist_name: str) -> str:
        try:
            from importlib.metadata import PackageNotFoundError, version as pkg_version
            return pkg_version(dist_name)
        except Exception:
            return "Not Found"

    return {
        "version": VERSION,
        "socketio_available": SOCKETIO_AVAILABLE,
        "libraries": {
            "flask": _pkg_ver("flask"),
            "flask_socketio": _pkg_ver("flask-socketio"),
            "socketio": _pkg_ver("python-socketio"),
            "engineio": _pkg_ver("python-engineio"),
            "wsproto": _pkg_ver("wsproto"),
            "bidict": _pkg_ver("bidict"),
        }
    }, 200

def add_log(msg):
    console_log_buffer.append(msg)
    print(msg) # Mirror to console
    # Write to session file persistently
    try:
        # Strip HTML tags for the text log
        clean_msg = re.sub(r'<[^>]*>', '', msg).replace('&lt;', '<').replace('&gt;', '>')
        with open(session_log_file, 'a', encoding='utf-8') as f:
            tstamp = datetime.now().strftime('%H:%M:%S')
            f.write(f"[{tstamp}] {clean_msg}\n")
    except: pass


def _log_exception_off_console():
    """Keep stack traces out of the operator log pane (/api/logs)."""
    import traceback
    tb = traceback.format_exc()
    try:
        from utils.structured_logger import get_logger
        get_logger().error(tb)
    except Exception:
        pass

# --- Target Scope Engine ---
def filter_inventory(inv_str, target_mode, filter_str, single_host, group_filter="All"):
    """Parse inventory text into device dicts for execute/scope.

    Host must be IPv4/IPv6 (same contract as inventory_store.preview).
    DNS hostnames and unknown device_types are skipped — never SSH'd.
    """
    from modules.inventory_store import (
        ALLOWED_DEVICE_TYPES,
        _normalize_inventory_host,
        _norm_type,
    )

    devices = []
    lines = inv_str.strip().split('\n')
    current_group = "Default"
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # [Group] header detection
        g_m = re.match(r'^\[([\w\-_ ]+)\]$', line)
        if g_m:
            current_group = g_m.group(1)
            continue

        # Split on comma only — spaces in device names/types are not valid
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 2:
            continue
        host_raw = parts[0]
        dtype_raw = parts[1]
        if not host_raw or not dtype_raw:
            continue
        host, host_err = _normalize_inventory_host(host_raw)
        if host_err or not host:
            continue
        dtype, _alias = _norm_type(dtype_raw)
        if dtype not in ALLOWED_DEVICE_TYPES:
            continue
        port = 22
        grp = current_group
        if len(parts) >= 3:
            if parts[2].isdigit():
                port = int(parts[2])
                if len(parts) >= 4:
                    grp = parts[3]
            else:
                grp = parts[2]
        devices.append({"host": host, "device_type": dtype, "port": port, "group": grp})

    if target_mode == 'single':
        # Guard: empty single_host must return nothing, not everything
        target = single_host.split('[')[0].strip() if '[' in single_host else single_host.strip()
        if not target:
            return []
        matched = [d for d in devices if d['host'] == target]
        if not matched:
            # Fallback: partial match for IPv6 presentation / short mismatches
            matched = [d for d in devices if target in d['host'] or d['host'] in target]
        return matched
    else:
        # Bulk mode: apply group filter first, then text filter
        if group_filter and group_filter.lower() != "all":
            devices = [d for d in devices if d.get('group', '').lower() == group_filter.lower()]
        if filter_str:
            f = filter_str.lower()
            return [d for d in devices if f in d['host'].lower() or f in d['device_type'].lower()]
        return devices

# ----- Core Threads (Delegates to modules/adapters.py) -----

def _connectivity_check_thread(devices, user, pwd, enb_pwd):
    try:
        add_log("\n--- Starting Connectivity Check ---")
        add_log(f"[System] Checking {len(devices)} device(s)...")
        import modules.adapters
        modules.adapters.run_connectivity(devices, user, pwd, enb_pwd, add_log)
        add_log("\n--- Connectivity Check Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Connectivity check failed: {str(e)}")
        _log_exception_off_console()


def _reachability_matrix_thread(devices, user, pwd, enb_pwd):
    """Fleet ping+SSH matrix report (Netdisco/LibreNMS-inspired daily ops)."""
    global _last_reachability_matrix
    try:
        add_log("\n--- Starting Fleet Reachability Matrix ---")
        from utils.output_paths import prepare_run_output, path_in_run, write_run_manifest, CAT_REACHABILITY
        from utils.reachability_matrix import (
            build_reachability_matrix,
            matrix_to_csv,
            matrix_to_html,
        )
        paths = prepare_run_output(CAT_REACHABILITY, 'fleet_matrix')
        summary = build_reachability_matrix(devices, user, pwd, enb_pwd, log_func=add_log)
        html_path = path_in_run(paths, 'reachability_matrix.html')
        csv_path = path_in_run(paths, 'reachability_matrix.csv')
        with open(html_path, 'w', encoding='utf-8') as fh:
            fh.write(matrix_to_html(summary))
        with open(csv_path, 'w', encoding='utf-8') as fh:
            fh.write(matrix_to_csv(summary))
        write_run_manifest(paths, {
            'action': 'reachability_matrix',
            'device_count': summary.get('device_count'),
            'counts': summary.get('counts'),
        })
        counts = summary.get('counts') or {}
        add_log(
            f"[Matrix] ok={counts.get('ok', 0)} ping_only={counts.get('ping_only', 0)} "
            f"unreachable={counts.get('unreachable', 0)} fail={counts.get('fail', 0)}"
        )
        add_log(f"[Matrix] HTML: {html_path}")
        add_log(f"[Matrix] CSV: {csv_path}")
        _last_reachability_matrix = {
            'status': 'complete',
            'summary': {
                'device_count': summary.get('device_count'),
                'counts': counts,
                'generated_at': summary.get('generated_at'),
            },
            'html_path': html_path,
            'csv_path': csv_path,
            'run_dir': paths.get('run_dir'),
        }
        add_log("\n--- Fleet Reachability Matrix Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Reachability matrix failed: {str(e)}")
        _last_reachability_matrix = {'status': 'error', 'error': str(e)}
        _log_exception_off_console()

def _vlan_check_thread(devices, user, pwd, enb_pwd=""):
    try:
        add_log("\n--- Starting VLAN Check ---")
        add_log(f"[System] Auditing VLANs on {len(devices)} device(s)...")
        import modules.vlan_audit
        from utils import report_formatter
        
        from utils.output_paths import CAT_VLAN_AUDIT, path_in_run, prepare_run_output, write_run_manifest
        paths = prepare_run_output(CAT_VLAN_AUDIT, 'web_vlan_check')
        out_file = path_in_run(paths, 'vlan_audit_report.txt')
        add_log(f"[System] Report folder: {paths['run_dir']}")
        add_log(f"[System] Report will be saved to: {out_file}")
        
        result_lines = [f"VLAN AUDIT REPORT\n" + "="*60 + "\n"]
        result_lines.append(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append(f"Devices Scanned: {len(devices)}\n")
        
        for dev in devices:
            host = dev['host']
            add_log(f"[{host}] Starting VLAN audit...")
            res = modules.vlan_audit.run(dev, user, pwd, enb_pwd, add_log)
            if res['status'] == 'success':
                true_host = res['data']['true_host']
                vlans = res['data'].get('vlans', [])
                result_lines.append(f"\n[{true_host}] VLANs Found: {len(vlans)}")
                for v in vlans[:20]:  # Limit to first 20 VLANs per device
                    result_lines.append(f"  VLAN {v.get('id', '?'):>4}: {v.get('name', 'N/A')}")
                if len(vlans) > 20:
                    result_lines.append(f"  ... and {len(vlans) - 20} more VLANs")
                add_log(f"[{true_host}] Found {len(vlans)} VLANs")
            else:
                result_lines.append(f"\n[{host}] ERROR: {res.get('error', 'Unknown error')}")
                add_log(f"[{host}] [ERROR] {res.get('error', 'Unknown error')}")
        
        result_lines.append(f"\n" + "="*60)
        result_lines.append(f"Report saved to: {out_file}")
        
        report_formatter.write_text_file(out_file, "\n".join(result_lines))
        write_run_manifest(paths, {'report_path': out_file})
        add_log(f"[System] VLAN audit report saved to: {out_file}")
        add_log("\n--- VLAN Check Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] VLAN check failed: {str(e)}")
        _log_exception_off_console()

def _find_missing_vlan_thread(devices, user, pwd, enb_pwd, vlan_id):
    """Find which devices are missing a specific VLAN."""
    try:
        add_log("\n--- Starting Find Missing VLAN ---")
        import modules.vlan_audit
        from utils import report_formatter
        
        if not vlan_id:
            add_log("[ERROR] VLAN ID is required."); return
        
        try:
            vlan_id_int = int(vlan_id)
        except ValueError:
            add_log("[ERROR] VLAN ID must be a number."); return
        
        from utils.output_paths import CAT_VLAN_MISSING, path_in_run, prepare_run_output, slugify, write_run_manifest
        paths = prepare_run_output(CAT_VLAN_MISSING, slugify(f'vlan{vlan_id}'))
        out_file = path_in_run(paths, 'missing_vlan_report.txt')
        add_log(f"[System] Searching for VLAN {vlan_id} across {len(devices)} device(s)...")
        add_log(f"[System] Report folder: {paths['run_dir']}")
        add_log(f"[System] Report will be saved to: {out_file}")
        add_log(f"\n--- Finding Missing VLAN {vlan_id} ---")
        
        result_lines = [f"MISSING VLAN {vlan_id} REPORT\n" + "="*60 + "\n"]
        result_lines.append(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append(f"Target VLAN: {vlan_id}")
        result_lines.append(f"Devices Scanned: {len(devices)}\n")
        
        missing_devices = []
        present_devices = []
        
        for dev in devices:
            host = dev['host']
            add_log(f"[{host}] Checking for VLAN {vlan_id}...")
            res = modules.vlan_audit.run(dev, user, pwd, enb_pwd, add_log)
            if res['status'] == 'success':
                true_host = res['data']['true_host']
                vlans = res['data'].get('vlans', [])
                vlan_ids = [int(v.get('id', 0)) for v in vlans if v.get('id')]
                
                if vlan_id_int in vlan_ids:
                    present_devices.append(true_host)
                    add_log(f"[{true_host}] VLAN {vlan_id} EXISTS")
                else:
                    missing_devices.append(true_host)
                    add_log(f"[{true_host}] VLAN {vlan_id} MISSING")
            else:
                add_log(f"[{host}] [ERROR] Could not retrieve VLAN data: {res.get('error', 'Unknown error')}")
        
        result_lines.append(f"\n✓ VLAN {vlan_id} PRESENT ON {len(present_devices)} DEVICES:")
        for d in present_devices:
            result_lines.append(f"  - {d}")
        
        result_lines.append(f"\n✗ VLAN {vlan_id} MISSING ON {len(missing_devices)} DEVICES:")
        for d in missing_devices:
            result_lines.append(f"  - {d}")
        
        if missing_devices:
            result_lines.append(f"\n" + "="*60)
            result_lines.append(f"RECOMMENDATION: VLAN {vlan_id} needs to be provisioned on the above {len(missing_devices)} devices.")
        else:
            result_lines.append(f"\n" + "="*60)
            result_lines.append(f"✓ All devices have VLAN {vlan_id} configured.")
        
        result_lines.append(f"\nReport saved to: {out_file}")
        result_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        report_formatter.write_text_file(out_file, "\n".join(result_lines))
        html_path = path_in_run(paths, 'missing_vlan_report.html')
        from utils.missing_vlan_formatter import write_missing_vlan_html
        write_missing_vlan_html(
            html_path, str(vlan_id), present_devices, missing_devices,
            meta={'run_dir': paths['run_dir']},
        )
        write_run_manifest(paths, {
            'report_path': out_file,
            'html_path': html_path,
            'vlan_id': vlan_id,
            'missing_count': len(missing_devices),
        })
        add_log(f"[System] Missing VLAN HTML report: {html_path}")
        add_log(f"[System] Missing VLAN report saved to: {out_file}")
        add_log("\n--- Find Missing VLAN Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Find Missing VLAN failed: {str(e)}")
        _log_exception_off_console()

def _mac_check_thread(devices, user, pwd, enb_pwd, target_mac):
    global _mac_trace_last
    try:
        add_log("\n--- Starting MAC Address Trace ---")
        if not target_mac:
            add_log("[ERROR] Target MAC is empty.")
            from utils.search_it_progress import progress_done
            progress_done('mac_trace', error='Target MAC is empty')
            return
        import modules.mac_trace
        from utils import report_formatter
        from utils.mac_trace_formatter import write_mac_trace_html
        from utils.search_report_output import prepare_search_run, write_run_manifest

        safe_mac = target_mac.replace(':', '-').replace('.', '-').replace(' ', '')
        paths = prepare_search_run('mac_trace', safe_mac)
        out_file = paths['txt_path']
        html_file = paths['html_path']
        add_log(f"[System] Tracing MAC {target_mac} across {len(devices)} device(s)...")
        add_log(f"[System] Report folder: {paths['run_dir']}")
        add_log(f"\n--- MAC Address Trace: {target_mac} ---")

        from utils.search_it_progress import progress_done, progress_start_if_needed, progress_tick
        n_dev = len(devices)
        progress_start_if_needed('mac_trace', n_dev, label=f'Tracing {target_mac}…')

        from utils.task_control_plane import should_abort
        result_lines = [f"MAC ADDRESS TRACE REPORT: {target_mac}\n" + "="*60 + "\n"]
        result_lines.append(f"Search Target: {target_mac}")
        result_lines.append(f"Devices Scanned: {len(devices)}\n")
        
        path_hops = []
        hop_idx = 0
        found_any = False
        endpoint = None
        ambiguous_devices = []
        for dev in devices:
            if should_abort():
                add_log("[Control Plane] Task cancelled — stopping MAC trace.")
                break
            host = dev['host']
            hop_idx += 1
            from utils.task_control_plane import update_task_progress
            update_task_progress(devices_done=hop_idx, devices_total=n_dev, message=f'{host} ({hop_idx}/{n_dev})')
            res = modules.mac_trace.run(dev, user, pwd, enb_pwd, target_mac, add_log)
            if res['status'] == 'success':
                true_host = res['data']['true_host']
                if res['data'].get('ambiguous'):
                    msg = res['data'].get('ambiguous_message', 'Partial MAC matches multiple addresses')
                    ambiguous_devices.append({'host': true_host, 'message': msg})
                    hop = {
                        'hop_index': hop_idx,
                        'device_ip': host,
                        'hostname': true_host,
                        'found': False,
                        'ambiguous': True,
                        'distinct_macs': res['data'].get('distinct_macs', []),
                        'vlan': None,
                        'port': None,
                        'status': 'ambiguous',
                        'message': msg,
                    }
                    path_hops.append(hop)
                    result_lines.append(f"\n[AMBIGUOUS] {true_host}")
                    result_lines.append(f"  {msg}")
                    add_log(f"[{true_host}] [AMBIGUOUS] {msg}")
                    continue
                found = res['data']['found']
                resolved_mac = res['data'].get('resolved_mac')
                distinct_macs = res['data'].get('distinct_macs') or []
                hop = {
                    'hop_index': hop_idx,
                    'device_ip': host,
                    'hostname': true_host,
                    'found': found,
                    'vlan': res['data'].get('vlan'),
                    'port': res['data'].get('port'),
                    'status': 'found' if found else 'not_found',
                    'distinct_macs': distinct_macs,
                    'resolved_mac': resolved_mac,
                }
                path_hops.append(hop)
                if found:
                    found_any = True
                    port = res['data']['port']
                    vlan = res['data'].get('vlan', 'N/A')
                    mac_label = resolved_mac or target_mac
                    endpoint = f"{mac_label} @ {true_host} — {port} (VLAN {vlan})"
                    result_lines.append(f"\n[FOUND] {true_host}")
                    if resolved_mac:
                        result_lines.append(f"  MAC: {resolved_mac}")
                    result_lines.append(f"  Port: {port}")
                    result_lines.append(f"  VLAN: {vlan}")
                    add_log(f"[{true_host}] MAC {mac_label} found on port {port} (VLAN: {vlan})")
                else:
                    result_lines.append(f"\n[NOT FOUND] {true_host} - MAC not present")
                    add_log(f"[{true_host}] MAC not found")
            else:
                path_hops.append({
                    'hop_index': hop_idx,
                    'device_ip': host,
                    'hostname': host,
                    'found': False,
                    'status': 'error',
                    'vlan': None,
                    'port': None,
                })
                result_lines.append(f"\n[ERROR] {host}: {res.get('error', 'Connection failed')}")
                add_log(f"[{host}] [ERROR] {res.get('error', 'Connection failed')}")
            progress_tick(
                'mac_trace', hop_idx, n_dev, host=host,
                found_count=1 if found_any else 0,
            )

        if ambiguous_devices:
            result_lines.append("\n" + "=" * 60)
            result_lines.append("NOTE: Partial MAC matched multiple distinct addresses on one or more devices.")
            result_lines.append("Refine your search to a full MAC (aa:bb:cc:dd:ee:ff) for a unique result.")
        if not found_any and not ambiguous_devices:
            result_lines.append("\n" + "="*60)
            result_lines.append("RESULT: MAC address not found in any of the scanned devices.")
            add_log(f"\n[RESULT] MAC {target_mac} not found in any device.")
        else:
            result_lines.append("\n" + "="*60)
            result_lines.append("RESULT: MAC address found successfully.")
        
        result_lines.append(f"\nText report: {out_file}")
        result_lines.append(f"HTML path report: {html_file}")
        result_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        report_formatter.write_text_file(out_file, "\n".join(result_lines))
        write_mac_trace_html(
            html_file, target_mac, path_hops,
            found_endpoint=endpoint or ('Ambiguous — refine MAC' if ambiguous_devices else 'Not found'),
            ambiguous_summary='; '.join(a['message'] for a in ambiguous_devices) if ambiguous_devices else None,
        )
        write_run_manifest(paths, {
            'target_mac': target_mac,
            'devices_scanned': len(devices),
            'found': found_any,
            'ambiguous': bool(ambiguous_devices),
            'endpoint': endpoint,
        })
        _mac_trace_last = {
            'target_mac': target_mac,
            'path_hops': path_hops,
            'html_path': os.path.abspath(html_file),
            'txt_path': os.path.abspath(out_file),
            'run_dir': paths['run_dir'],
            'found': found_any,
            'ambiguous': bool(ambiguous_devices),
            'ambiguous_devices': ambiguous_devices,
            'endpoint': endpoint,
            'ts': datetime.now().isoformat(),
        }
        try:
            from utils.mac_trace_formatter import _target_mac_display
            from utils.match_highlight import escape_html, highlight_mac_match
            from utils.mac_utils import format_mac_for_display
            _mac_trace_last['target_mac_html'] = highlight_mac_match(
                _target_mac_display(target_mac), target_mac,
            )
            found_mac = None
            for hop in _mac_trace_last['path_hops']:
                if hop.get('resolved_mac'):
                    found_mac = hop['resolved_mac']
                    break
            if found_mac:
                _mac_trace_last['found_mac'] = found_mac
                _mac_trace_last['found_mac_html'] = highlight_mac_match(found_mac, target_mac)
            for hop in _mac_trace_last['path_hops']:
                if hop.get('resolved_mac'):
                    hop['resolved_mac_html'] = highlight_mac_match(hop['resolved_mac'], target_mac)
                if hop.get('distinct_macs'):
                    hop['distinct_macs_html'] = [
                        highlight_mac_match(format_mac_for_display(m), target_mac)
                        for m in hop['distinct_macs'][:6]
                    ]
        except Exception as exc:
            add_log(f"[WARNING] MAC trace highlight enrichment failed: {exc}")
            from utils.match_highlight import escape_html
            _mac_trace_last['target_mac_html'] = escape_html(target_mac)
            for hop in _mac_trace_last.get('path_hops') or []:
                if hop.get('resolved_mac'):
                    hop['resolved_mac_html'] = escape_html(hop['resolved_mac'])
        add_log(f"[System] MAC trace saved: {out_file}")
        add_log(f"[System] HTML report: {html_file}")
        progress_done('mac_trace', message='MAC trace complete')
        add_log("\n--- MAC Trace Complete ---")
    except Exception as e:
        from utils.search_it_progress import progress_done
        progress_done('mac_trace', error=str(e))
        add_log(f"[CRITICAL ERROR] MAC trace failed: {str(e)}")
        _log_exception_off_console()

def _add_vlan_thread(devices, user, pwd, enb_pwd, vid, vname, dry_run=False, save_config=False):
    try:
        add_log("\n--- Starting VLAN Add Operation ---")
        import modules.adapters
        modules.adapters.run_vlan_management('add', devices, user, pwd, enb_pwd, vid, vname, add_log, dry_run=dry_run, save_config=save_config)
        add_log("\n--- VLAN Add Operation Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] VLAN add failed: {str(e)}")
        _log_exception_off_console()

def _rename_vlan_thread(devices, user, pwd, enb_pwd, vid, vname, dry_run=False, save_config=False):
    try:
        add_log("\n--- Starting VLAN Rename Operation ---")
        import modules.adapters
        modules.adapters.run_vlan_management('rename', devices, user, pwd, enb_pwd, vid, vname, add_log, dry_run=dry_run, save_config=save_config)
        add_log("\n--- VLAN Rename Operation Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] VLAN rename failed: {str(e)}")
        _log_exception_off_console()

def _delete_vlan_thread(devices, user, pwd, enb_pwd, vid, vname=None, dry_run=False, save_config=False):
    try:
        add_log("\n--- Starting VLAN Delete Operation ---")
        import modules.adapters
        modules.adapters.run_vlan_management('delete', devices, user, pwd, enb_pwd, vid, vname, add_log, dry_run=dry_run, save_config=save_config)
        add_log("\n--- VLAN Delete Operation Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] VLAN delete failed: {str(e)}")
        _log_exception_off_console()

def _description_search_thread(devices, user, pwd, enb_pwd, search_term):
    global _description_search_last
    try:
        add_log("\n--- Starting Description Search (search_it) ---")
        import modules.adapters
        from utils.description_search_formatter import write_description_search_html
        from utils.search_report_output import prepare_search_run, slugify, write_run_manifest

        needle = (search_term or '').strip()
        if not needle:
            add_log("[ERROR] Description search term is empty.")
            from utils.search_it_progress import progress_done
            progress_done('description_search', error='Search term is empty')
            return
        paths = prepare_search_run('description_search', slugify(needle))
        add_log(f"[System] Report folder: {paths['run_dir']}")

        from utils.search_it_progress import progress_done, progress_start_if_needed, progress_tick

        def _desc_progress_cb(idx, total, host, match_count):
            progress_tick(
                'description_search', idx, total, host=host,
                label=f'Searching {host} ({idx}/{total})',
                match_count=match_count,
            )

        progress_start_if_needed('description_search', len(devices), label=f'Searching for "{needle}"…')

        results, _report_file = modules.adapters.run_description_search(
            devices, user, pwd, enb_pwd, needle, add_log,
            report_txt_path=paths['txt_path'],
            progress_cb=_desc_progress_cb,
        )

        device_rows = []
        total_matches = 0
        for dev, res in zip(devices, results or []):
            host = dev.get('host', '')
            if res.get('status') == 'success':
                true_host = res['data'].get('true_host', host)
                matches = res['data'].get('matches', [])
                total_matches += len(matches)
                for m in matches:
                    device_rows.append({
                        'hostname': true_host,
                        'device_ip': host,
                        'interface': m.get('interface', ''),
                        'status': m.get('status', ''),
                        'description': m.get('description', ''),
                        'source': m.get('source', ''),
                    })
                if not matches:
                    device_rows.append({
                        'hostname': true_host,
                        'device_ip': host,
                        'interface': '',
                        'status': '',
                        'description': '(no matches on this device)',
                        'source': '',
                    })
            else:
                device_rows.append({
                    'hostname': host,
                    'device_ip': host,
                    'error': res.get('error', 'Connection failed'),
                })

        write_description_search_html(
            paths['html_path'],
            needle,
            device_rows,
            total_matches=total_matches,
            devices_scanned=len(devices),
        )
        write_run_manifest(paths, {
            'search_term': needle,
            'total_matches': total_matches,
            'devices_scanned': len(devices),
        })
        _description_search_last = {
            'search_term': needle,
            'total_matches': total_matches,
            'devices_scanned': len(devices),
            'html_path': paths['html_path'],
            'txt_path': paths['txt_path'],
            'run_dir': paths['run_dir'],
            'rows': device_rows,
            'ts': datetime.now().isoformat(),
        }
        try:
            from utils.match_highlight import escape_html, highlight_text_match
            enriched = []
            for row in device_rows:
                if row.get('error'):
                    enriched.append(dict(row))
                    continue
                er = dict(row)
                er['interface_html'] = highlight_text_match(row.get('interface', ''), needle)
                er['description_html'] = highlight_text_match(row.get('description', ''), needle)
                enriched.append(er)
            _description_search_last['rows'] = enriched
        except Exception as exc:
            add_log(f"[WARNING] Description search highlight enrichment failed: {exc}")
            from utils.match_highlight import escape_html
            _description_search_last['rows'] = [
                dict(r, interface_html=escape_html(r.get('interface', '')),
                     description_html=escape_html(r.get('description', '')))
                for r in device_rows
            ]
        progress_done('description_search', message='Description search complete')
        add_log(f"[System] Description search HTML: {paths['html_path']}")
        add_log("\n--- Description Search Complete ---")
    except Exception as e:
        from utils.search_it_progress import progress_done
        progress_done('description_search', error=str(e))
        add_log(f"[CRITICAL ERROR] Description search failed: {str(e)}")
        _log_exception_off_console()


def _interfaces_check_thread(devices, user, pwd, enb_pwd, filter_str):
    try:
        add_log("\n--- Starting Interfaces Check ---")
        import modules.adapters
        modules.adapters.run_interfaces(devices, user, pwd, enb_pwd, filter_str, add_log)
        add_log("\n--- Interfaces Check Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Interfaces check failed: {str(e)}")
        _log_exception_off_console()

def _node_analyze_thread(target_node, devices, user, pwd, enb_pwd):
    global _last_node_analyze
    import modules.node_analyze
    from utils import report_formatter
    from utils.output_paths import CAT_NODE_ANALYSIS, path_in_run, prepare_run_output, slugify, write_run_manifest
    _last_node_analyze = {
        "status": "running",
        "target_node": target_node,
        "devices_total": len(devices),
        "devices_done": 0,
        "hits": [],
    }
    add_log(f"\n--- Analyzing Connectivity for Node: {target_node} ---")
    paths = prepare_run_output(CAT_NODE_ANALYSIS, slugify(target_node))
    out_file = path_in_run(paths, 'node_analysis_report.txt')
    add_log(f"[Output] Node analysis folder: {paths['run_dir']}")
    result_lines = [f"NODE CONNECTIVITY ANALYSIS: {target_node}\n" + "="*50 + "\n"]
    found_any = False
    port_hits = []
    scanned = []
    done = 0
    for dev in devices:
        host = dev['host']
        res = modules.node_analyze.run(dev, user, pwd, enb_pwd, target_node, log_func=add_log)
        done += 1
        _last_node_analyze["devices_done"] = done
        if res['status'] == 'success':
            true_host = res['data']['true_host']
            scanned.append({"switch": true_host, "found": bool(res['data']['found'])})
            if res['data']['found']:
                found_any = True
                for p_info in res['data']['ports']:
                    mac_info = "Multiple MACs!" if p_info['macs'] > 1 else (f"MAC: {p_info['first_mac']}" if p_info['macs'] == 1 else "No MACs")
                    s = f"[{true_host}] Port: {p_info['port']} | Status: {p_info['status']} | Desc: {p_info['desc']} | {mac_info}"
                    result_lines.append(s)
                    add_log(s)
                    port_hits.append({
                        "switch": true_host,
                        "port": p_info['port'],
                        "status": p_info['status'],
                        "desc": p_info['desc'],
                        "macs": p_info['macs'],
                    })
            else:
                add_log(f"[{true_host}] Target not found.")
        else:
            add_log(f"[{host}] [ERROR] {res['error']}")
            scanned.append({"switch": host, "found": False, "error": res.get('error')})
    if not found_any:
        msg = f"[System] No direct connectivity found for Node '{target_node}'."
        result_lines.append(msg); add_log(msg)
    report_formatter.write_text_file(out_file, "\n".join(result_lines))
    write_run_manifest(paths, {'report_path': out_file, 'target_node': target_node, 'port_hits': port_hits})
    add_log(f"[System] Node report saved to: {out_file}")
    add_log("\n--- Node Connectivity Analysis Complete ---")
    _last_node_analyze = {
        "status": "complete",
        "target_node": target_node,
        "found_any": found_any,
        "port_hits": port_hits,
        "scanned": scanned,
        "report_path": out_file,
        "devices_total": len(devices),
        "devices_done": done,
    }

def _vlan_compare_thread(devices, user, pwd, enb_pwd):
    try:
        add_log("\n--- Starting VLAN Compare ---")
        import modules.adapters
        modules.adapters.run_vlan_compare(devices, user, pwd, enb_pwd, add_log)
        add_log("\n--- VLAN Compare Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] VLAN compare failed: {str(e)}")
        _log_exception_off_console()

def _config_backup_thread(devices, user, pwd, enb_pwd, filt):
    try:
        add_log("\n--- Starting Config Backup ---")
        import modules.adapters
        modules.adapters.run_config_backup(devices, user, pwd, enb_pwd, filt, add_log)
        add_log("\n--- Config Backup Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Config backup failed: {str(e)}")
        _log_exception_off_console()

def _network_audit_thread(devices, user, pwd, enb_pwd):
    try:
        add_log("\n--- Starting Network Audit ---")
        import modules.adapters
        modules.adapters.run_network_audit(devices, user, pwd, enb_pwd, add_log)
        add_log("\n--- Network Audit Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Network audit failed: {str(e)}")
        _log_exception_off_console()


def _failure_correlation_thread(devices, user, pwd, enb_pwd):
    global _last_failure_correlation
    try:
        add_log("\n--- Starting Failure Correlation Engine ---")
        import modules.adapters
        bundle, html_file = modules.adapters.run_failure_correlation_mapper(
            devices, user, pwd, enb_pwd, add_log,
        )
        hyp = (bundle or {}).get('rollups', {}).get('hypothesis_count', 0)
        _last_failure_correlation = {
            'status': 'complete',
            'html_path': html_file,
            'hypothesis_count': hyp,
            'completed_at': datetime.now().isoformat(),
        }
        add_log(f"[SUCCESS] Failure correlation ready — {hyp} hypotheses")
        add_log("\n--- Failure Correlation Complete ---")
    except Exception as e:
        _last_failure_correlation = {
            'status': 'error',
            'error': str(e),
            'completed_at': datetime.now().isoformat(),
        }
        add_log(f"[CRITICAL ERROR] Failure correlation failed: {str(e)}")
        _log_exception_off_console()


def _save_config_thread(devices, user, pwd, enb_pwd):
    try:
        add_log("\n--- Starting Save Config ---")
        import modules.adapters
        modules.adapters.run_save_config(devices, user, pwd, enb_pwd, add_log)
        add_log("\n--- Save Config Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Save config failed: {str(e)}")
        _log_exception_off_console()

def _node_interface_topology_thread(devices, user, pwd, enb_pwd):
    global _last_port_map
    try:
        _last_port_map = {
            "status": "running",
            "device_count": len(devices),
            "devices_total": len(devices),
            "devices_done": 0,
        }
        add_log("\n--- Starting Node Interface Topology ---")
        import modules.adapters
        results, html_file = modules.adapters.run_node_interface_topology(
            devices, user, pwd, enb_pwd, add_log,
        )
        ok = sum(1 for r in (results or []) if r.get("status") == "success")
        _last_port_map = {
            "status": "complete" if html_file else "error",
            "html_path": html_file,
            "html_basename": os.path.basename(html_file) if html_file else None,
            "device_count": len(devices),
            "devices_ok": ok,
            "devices_scanned": len(results or []),
            "multi_device": len(devices) > 1,
        }
        add_log("\n--- Node Interface Topology Complete ---")
    except Exception as e:
        _last_port_map = {"status": "error", "error": str(e)}
        add_log(f"[CRITICAL ERROR] Node interface topology failed: {str(e)}")
        _log_exception_off_console()


def _load_link_issues(diag_folder):
    """Load witness rows from last topology run. Empty if missing."""
    if not diag_folder:
        return []
    path = os.path.join(diag_folder, 'link_issues.json')
    if not os.path.isfile(path):
        f4 = os.path.join(diag_folder, '04_final_map_data.json')
        if os.path.isfile(f4):
            try:
                data = json.load(open(f4, encoding='utf-8'))
                return list(data.get('link_issues') or [])
            except Exception:
                return []
        return []
    try:
        data = json.load(open(path, encoding='utf-8'))
        return list(data.get('issues') or [])
    except Exception:
        return []


def _topology_mapper_thread(devices, user, pwd, enb_pwd, map_mode="all"):
    global _last_topology
    _last_topology = {
        "status": "running",
        "map_mode": map_mode,
        "started_at": datetime.now().isoformat(),
        "device_count": len(devices),
        "devices_total": len(devices),
        "devices_done": 0,
    }
    try:
        add_log(f"\n--- Starting Topology Mapper (mode: {map_mode}) ---")
        import modules.adapters
        results, html_file = modules.adapters.run_topology_mapper(
            devices, user, pwd, enb_pwd, add_log, map_mode,
        )
        if html_file and os.path.isfile(html_file):
            diag_folder = os.path.dirname(html_file)
            ok = sum(1 for r in (results or []) if r.get("status") == "success")
            node_count = edge_count = vpc_domains = 0
            vpc_adjacency_fallback = False
            meta = {}
            try:
                import json as _json
                mf = os.path.join(diag_folder, "07_post_render_manifest.json")
                if os.path.isfile(mf):
                    manifest = _json.load(open(mf, encoding="utf-8"))
                    meta = manifest.get("_meta") or {}
                    node_count = meta.get("node_count") or 0
                    edge_count = meta.get("edge_count") or 0
                    vpc_domains = meta.get("vpc_domain_nodes") or 0
                    vpc_adjacency_fallback = bool(meta.get("vpc_adjacency_fallback"))
                f4 = os.path.join(diag_folder, "04_final_map_data.json")
                if os.path.isfile(f4) and not node_count:
                    fd = _json.load(open(f4, encoding="utf-8"))
                    node_count = len(fd.get("nodes") or [])
                    edge_count = len(fd.get("edges") or [])
            except Exception:
                pass
            issues = _load_link_issues(diag_folder)
            _last_topology = {
                "status": "complete",
                "map_mode": map_mode,
                "html_path": html_file,
                "diag_folder": diag_folder,
                "html_basename": os.path.basename(html_file),
                "devices_scanned": len(results or []),
                "devices_ok": ok,
                "node_count": node_count,
                "edge_count": edge_count,
                "vpc_domains": vpc_domains,
                "vpc_adjacency_fallback": vpc_adjacency_fallback,
                "devices_requested": meta.get("devices_requested"),
                "devices_truncated": meta.get("devices_truncated", False),
                "devices_skipped_hosts": meta.get("devices_skipped_hosts") or [],
                "parallel_workers": meta.get("parallel_workers"),
                "failed_hosts": meta.get("failed_hosts") or [],
                "issues": issues,
                "issue_count": len(issues),
                "completed_at": datetime.now().isoformat(),
            }
            add_log(
                f"[SUCCESS] Map ready — open from Swiss Tools panel or: {os.path.basename(html_file)}"
            )
        else:
            _last_topology = {
                "status": "error",
                "map_mode": map_mode,
                "error": "No topology HTML produced (check device SSH / NX-OS vPC data)",
                "completed_at": datetime.now().isoformat(),
            }
            add_log("[ERROR] Topology map was not generated — see log above")
        add_log(f"\n--- Topology Mapper Complete ---")
    except Exception as e:
        _last_topology = {
            "status": "error",
            "map_mode": map_mode,
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        }
        add_log(f"[CRITICAL ERROR] Topology mapper failed: {str(e)}")
        _log_exception_off_console()


def _utilization_live_thread(devices, user, pwd, enb_pwd, credential_id, diag_folder, topology_job_id=None):
    """Bounded live SSH two-sample utilization. Does not recrawl topology."""
    global _last_utilization_live
    from utils.utilization_overlay.ssh_collector import (
        LiveUtilizationError,
        run_live_utilization,
    )
    _last_utilization_live = {
        'status': 'running',
        'mode': 'live',
        'evidence_class': 'live_ssh',
        'started_at': datetime.now().isoformat(),
        'device_count': len(devices),
        'message': (
            'Live SSH collection in progress — not SNMP. '
            'Two interface samples, then paint existing Standard L2 edges only. '
            'Does not certify topology.'
        ),
    }
    try:
        add_log('[UTIL-LIVE] starting bounded SSH two-sample collection (not SNMP)')
        out = run_live_utilization(
            inventory=devices,
            user=user,
            pwd=pwd,
            enb_pwd=enb_pwd,
            diag_folder=diag_folder,
            topology_job_id=topology_job_id,
            log=add_log,
            credential_id=credential_id,
        )
        public = {
            'status': out.get('status') or 'complete',
            'mode': 'live',
            'evidence_class': 'live_ssh',
            'degraded': bool(out.get('degraded')),
            'painted_count': out.get('painted_count', 0),
            'unmapped_count': out.get('unmapped_count', 0),
            'eligible_count': out.get('eligible_count', 0),
            'skipped_not_on_map_count': len(out.get('skipped_not_on_map') or []),
            'ssh_error_count': len(out.get('ssh_errors') or []),
            'html_basename': os.path.basename(out.get('html_path') or '') or None,
            'overlay_basename': os.path.basename(out.get('overlay_path') or '') or None,
            'message': out.get('message') or 'Live SSH — not SNMP.',
            'completed_at': datetime.now().isoformat(),
        }
        _last_utilization_live = public
        add_log(
            f"[UTIL-LIVE] {public['status']} painted={public['painted_count']} "
            f"unmapped={public['unmapped_count']} degraded={public['degraded']}"
        )
    except LiveUtilizationError as exc:
        _last_utilization_live = {
            'status': 'error',
            'mode': 'live',
            'evidence_class': 'live_ssh',
            'error': str(exc),
            'degraded': True,
            'message': str(exc),
            'completed_at': datetime.now().isoformat(),
        }
        add_log(f'[UTIL-LIVE] blocked: {exc}')
    except Exception as exc:
        _last_utilization_live = {
            'status': 'error',
            'mode': 'live',
            'error': 'Live SSH utilization failed',
            'degraded': True,
            'completed_at': datetime.now().isoformat(),
        }
        add_log(f'[UTIL-LIVE] failed: {type(exc).__name__}')
        _log_exception_off_console()


def _l3_map_thread(devices, user, pwd, enb_pwd, map_kind='l3'):
    """L3 routing or flow map generation thread."""
    global _last_l3_map
    _last_l3_map = {
        'status': 'running',
        'map_kind': map_kind,
        'started_at': datetime.now().isoformat(),
        'device_count': len(devices),
        'devices_total': len(devices),
        'devices_done': 0,
    }
    try:
        add_log(f"\n--- Starting L3 Cartography ({map_kind.upper()}) ---")
        import modules.adapters
        results, html_file, meta = modules.adapters.run_l3_topology_mapper(
            devices, user, pwd, enb_pwd, add_log, map_kind,
        )
        if html_file and os.path.isfile(html_file):
            _last_l3_map = {
                'status': 'complete',
                'map_kind': map_kind,
                'html_path': html_file,
                'html_basename': os.path.basename(html_file),
                'diag_folder': meta.get('diag_folder'),
                'devices_scanned': meta.get('devices_scanned', 0),
                'devices_ok': meta.get('devices_ok', 0),
                'node_count': meta.get('node_count', 0),
                'edge_count': meta.get('edge_count', 0),
                'route_count': meta.get('route_count', 0),
                'failed_hosts': meta.get('failed_hosts') or [],
                'devices_truncated': meta.get('devices_truncated', False),
                'devices_requested': meta.get('devices_requested'),
                'devices_skipped_hosts': meta.get('devices_skipped_hosts') or [],
                'parallel_workers': meta.get('parallel_workers'),
                'completed_at': datetime.now().isoformat(),
            }
            add_log(f"[SUCCESS] {map_kind.upper()} map ready — {os.path.basename(html_file)}")
        else:
            _last_l3_map = {
                'status': 'error',
                'map_kind': map_kind,
                'error': 'No L3 map HTML produced (check SSH / routing table access)',
                'completed_at': datetime.now().isoformat(),
            }
            add_log("[ERROR] L3 map was not generated — see log above")
        add_log(f"\n--- L3 Cartography Complete ({map_kind}) ---")
    except Exception as e:
        _last_l3_map = {
            'status': 'error',
            'map_kind': map_kind,
            'error': str(e),
            'completed_at': datetime.now().isoformat(),
        }
        add_log(f"[CRITICAL ERROR] L3 cartography failed: {str(e)}")
        _log_exception_off_console()


def _advanced_l2_map_thread(devices, user, pwd, enb_pwd):
    """Advanced L2 enriched map thread."""
    global _last_l3_map
    _last_l3_map = {
        'status': 'running',
        'map_kind': 'advanced_l2',
        'started_at': datetime.now().isoformat(),
        'device_count': len(devices),
        'devices_total': len(devices),
    }
    try:
        add_log("\n--- Starting Advanced L2 Map ---")
        import modules.adapters
        results, html_file, meta = modules.adapters.run_advanced_l2_map(
            devices, user, pwd, enb_pwd, add_log,
        )
        if html_file and os.path.isfile(html_file):
            _last_l3_map = {
                'status': 'complete',
                'map_kind': 'advanced_l2',
                'html_path': html_file,
                'html_basename': os.path.basename(html_file),
                'diag_folder': meta.get('diag_folder'),
                'devices_scanned': meta.get('devices_scanned', 0),
                'devices_ok': meta.get('devices_ok', 0),
                'node_count': meta.get('node_count', 0),
                'edge_count': meta.get('edge_count', 0),
                'failed_hosts': meta.get('failed_hosts') or [],
                'completed_at': datetime.now().isoformat(),
            }
            add_log(f"[SUCCESS] Advanced L2 map ready — {os.path.basename(html_file)}")
        else:
            _last_l3_map = {'status': 'error', 'map_kind': 'advanced_l2', 'error': 'No HTML produced'}
    except Exception as e:
        _last_l3_map = {'status': 'error', 'map_kind': 'advanced_l2', 'error': str(e)}
        add_log(f"[CRITICAL ERROR] Advanced L2 map failed: {str(e)}")

# ----- v6.0 Plugin System Threads -----

def _plugin_execute_thread(plugin_id, devices, user, pwd, enb_pwd, params, vault_extras=None):
    """Execute a v6.0 plugin on multiple devices."""
    try:
        add_log(f"\n--- Starting Plugin: {plugin_id} ---")
        import modules.adapters
        
        results = modules.adapters.run_generic_plugin(
            plugin_id, devices, user, pwd, enb_pwd, params, add_log, vault_extras=vault_extras
        )
        
        # Write report if plugin returns data
        success_count = sum(1 for r in results if r.get('status') == 'success')
        fail_count = len(results) - success_count
        
        if success_count > 0:
            from utils import report_formatter
            out_file = report_formatter.generate_consolidated_plugin_report(plugin_id, results)
            add_log(f"[System] Plugin report saved to: {out_file}")
            if plugin_id == 'cisco_asset_warranty':
                from utils.cisco_asset_reports import generate_cisco_asset_consolidated_reports
                paths = generate_cisco_asset_consolidated_reports(results, plugin_id)
                add_log(f"[System] Asset HTML report: {paths.get('html')}")
                add_log(f"[System] Asset CSV report: {paths.get('csv')}")
        
        add_log(f"\n--- Plugin {plugin_id} Complete ---")
    except Exception as e:
        add_log(f"[CRITICAL ERROR] Plugin execution failed: {str(e)}")
        _log_exception_off_console()

# ----- Routes -----
@app.route('/')
def index():
    return render_template(
        'index.html',
        version=VERSION,
        date=UPDATE_DATE,
        date_display=_date_display_short(UPDATE_DATE),
        date_title=UPDATE_DATE,
    )

def _inventory_error_response(exc):
    from modules.inventory_store import InventoryError, UnsavedInventoryError
    payload = {'error': str(exc)}
    if isinstance(exc, UnsavedInventoryError):
        payload['code'] = getattr(exc, 'code', 'unsaved_inventory')
        payload['require_acknowledge'] = True
        return jsonify(payload), 409
    code = 400 if isinstance(exc, InventoryError) else 500
    return jsonify(payload), code


def _resolve_request_inventory(data, action=''):
    """Return (scope_dict, error_response). error_response is (json, status) or None."""
    from modules import inventory_store as inv_store
    box = data.get('inventory')
    if box is None:
        box = ''
    try:
        resolved = inv_store.resolve_scope_text(
            box,
            data.get('inventory_source'),
            action=action or data.get('action') or '',
            acknowledge_unsaved=bool(data.get('acknowledge_unsaved')),
        )
    except inv_store.InventoryError as e:
        return None, _inventory_error_response(e)
    return resolved, None


def _inventory_meta(resolved):
    return {
        'inventory_source': resolved.get('source_used'),
        'inventory_state': resolved.get('state'),
        'inventory_warning': resolved.get('warning'),
        'device_count': resolved.get('accepted_count'),
        'box_differs': resolved.get('box_differs'),
    }


def _public_outputs_meta(path):
    from utils.job_index import public_outputs_meta
    return public_outputs_meta(path)


def _stp_public_result(result):
    """JSON-safe STP result: no absolute filesystem paths."""
    if not isinstance(result, dict):
        return {}
    out = {}
    skip = {'html_path', 'output_folder', 'txt_path'}
    for key, val in result.items():
        if key in skip:
            continue
        if isinstance(val, str) and os.path.isabs(val):
            continue
        out[key] = val
    meta = _public_outputs_meta(
        (result.get('output_folder') or result.get('html_path') or '')
    )
    out['run_dir'] = meta['run_dir']
    out['artifacts_available'] = meta['artifacts_available']
    out['run_dir_exists'] = meta['run_dir_exists']
    return out


@app.route('/api/inventory')
def api_inventory():
    from modules import inventory_store as inv_store
    try:
        text = inv_store.read_inventory_text()
    except inv_store.InventoryError as e:
        return jsonify({'error': str(e), 'inventory': '', 'baks': [], 'counts': {}})
    parsed = inv_store.preview(text)
    return jsonify({
        'inventory': text,
        'path': inv_store.resolve_inventory_path(),
        'counts': parsed['counts'],
        'baks': inv_store.list_baks(),
        'has_committed': True,
    })


@app.route('/api/inventory/source', methods=['POST'])
def api_inventory_source():
    from modules import inventory_store as inv_store
    data = request.get_json(silent=True) or {}
    text = data.get('text')
    if text is None:
        text = data.get('inventory', '')
    try:
        cmp = inv_store.describe_inventory_state(text)
    except inv_store.InventoryError as e:
        return _inventory_error_response(e)
    return jsonify(cmp)


@app.route('/api/inventory/preview', methods=['POST'])
def api_inventory_preview():
    from modules import inventory_store as inv_store
    data = request.get_json(silent=True) or {}
    text = data.get('text')
    if text is None:
        text = data.get('inventory', '')
    try:
        parsed = inv_store.preview(text)
    except inv_store.InventoryError as e:
        return _inventory_error_response(e)
    return jsonify(parsed)


@app.route('/api/inventory/commit', methods=['POST'])
def api_inventory_commit():
    from modules import inventory_store as inv_store
    data = request.get_json(silent=True) or {}
    text = data.get('text')
    if text is None:
        text = data.get('inventory', '')
    mode = data.get('mode', 'replace')
    confirm = bool(data.get('confirm'))
    try:
        result = inv_store.commit(text, mode, confirm=confirm)
    except inv_store.InventoryError as e:
        return _inventory_error_response(e)
    add_log(
        f"[Inventory] commit {result['mode']} written={result['written']} "
        f"omitted_reject={result['omitted_reject']} "
        f"omitted_duplicate={result['omitted_duplicate']} bak={result.get('bak') or '-'}"
    )
    return jsonify(result)


@app.route('/api/inventory/restore', methods=['POST'])
def api_inventory_restore():
    from modules import inventory_store as inv_store
    data = request.get_json(silent=True) or {}
    bak = data.get('bak') or data.get('name') or ''
    confirm = bool(data.get('confirm'))
    try:
        result = inv_store.restore(bak, confirm=confirm)
    except inv_store.InventoryError as e:
        return _inventory_error_response(e)
    add_log(f"[Inventory] restore bak={result.get('restored')} written={result.get('written')}")
    return jsonify(result)

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """Read-only snapshot of the operator pane buffer. GET never drains."""
    if request.args.get('drain') is not None:
        return jsonify({
            'error': 'GET /api/logs is read-only; drain is not supported.',
        }), 400
    for banned in ('file', 'path', 'clear', 'delete', 'purge', 'truncate'):
        if request.args.get(banned) is not None:
            return jsonify({
                'error': 'Log target parameters are not accepted.',
            }), 400
    try:
        since = int(request.args.get('since', '0'))
    except (TypeError, ValueError):
        return jsonify({'error': 'since must be a non-negative integer'}), 400
    if since < 0:
        return jsonify({'error': 'since must be a non-negative integer'}), 400
    try:
        limit = int(request.args.get('limit', str(_LOG_DEFAULT_LIMIT)))
    except (TypeError, ValueError):
        return jsonify({'error': 'limit must be an integer'}), 400
    if limit < 1:
        return jsonify({'error': 'limit must be at least 1'}), 400
    if limit > _LOG_MAX_LIMIT:
        limit = _LOG_MAX_LIMIT
    out, next_cursor = console_log_buffer.snapshot(since, limit)
    return jsonify({
        'logs': out,
        'next_cursor': next_cursor,
        'count': len(out),
    })

@app.route('/api/execute', methods=['POST'])
def api_execute():
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code
    if request.content_length and request.content_length > 0:
        if request.mimetype and 'json' not in request.mimetype:
            return jsonify({
                "status": "error",
                "error": "Content-Type must be application/json",
            }), 415
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"status": "error", "error": "Invalid JSON body"}), 400
    else:
        data = request.get_json(silent=True) or {}
    action = data.get('action')
    if not action:
        return jsonify({"status": "error", "error": "Missing required field: action"}), 400
    # UI progress category is mac_trace; execute API action is mac_check (v7.0.61 alias).
    if action == 'mac_trace':
        action = 'mac_check'
    resolved_creds, cred_err = _resolve_task_credentials(data, credential_id_required=True)
    if cred_err:
        return cred_err
    user = resolved_creds['username']
    pwd = resolved_creds['password']
    enb_pwd = resolved_creds['enable_pwd']
    data['become_password'] = resolved_creds.get('become_password') or ''
    inv, target_mode, filter_str, single = data.get('inventory',''), data.get('target_mode'), data.get('filter',''), data.get('single_host','')
    group_filter = data.get('group', 'All')
    resolved, inv_err = _resolve_request_inventory(data, action)
    if inv_err:
        return inv_err
    inv = resolved['text']
    add_log(
        f"[Inventory] execute source={resolved['source_used']} "
        f"state={resolved['state']} devices={resolved['accepted_count']} "
        f"warn={resolved.get('warning') or '-'}"
    )

    devices = filter_inventory(inv, target_mode, filter_str, single, group_filter)
    
    if not devices:
        return jsonify({"status": "error", "error": "Filtered scope resulted in 0 target devices. Check Inventory/Group settings."})

    # Stamp every device with Secondary/Third vault profiles for connect_device / safe_connection
    from modules.network_base import attach_fallback_to_devices
    devices = attach_fallback_to_devices(
        devices,
        fallback_credentials=resolved_creds.get('fallback_credentials'),
        secondary=resolved_creds.get('secondary_credential'),
        third=resolved_creds.get('third_credential'),
    )

    from utils.api_security import audit_execute_dispatch
    audit_execute_dispatch(
        add_log,
        str(action),
        credential_id=resolved_creds.get('credential_id') or '',
        device_count=len(devices),
    )

    util_live_diag = None
    util_live_job = None
    if action == 'utilization_live':
        cid = (data.get('credential_id') or '').strip()
        if not cid:
            return jsonify({
                "status": "error",
                "error": (
                    "credential_id required for live SSH utilization. "
                    "Unlock the vault and select a stored credential."
                ),
            }), 400
        last = _last_topology or {}
        if last.get('status') != 'complete' or (last.get('map_mode') or '') != 'all':
            return jsonify({
                "status": "error",
                "error": (
                    "Live SSH utilization requires a completed Inventory Standard L2 map. "
                    "Build Standard L2 first. Live SSH does not crawl discovery."
                ),
            }), 400
        util_live_diag = last.get('diag_folder') or ''
        if not util_live_diag or not os.path.isdir(util_live_diag):
            return jsonify({
                "status": "error",
                "error": "Standard L2 diagnostics folder missing. Rebuild the map.",
            }), 400
        util_live_job = last.get('task_id')

    # Pre-arm search_it progress so UI polling does not stop on idle before the worker thread starts.
    if action == 'description_search':
        from utils.search_it_progress import progress_start, progress_done
        term = (data.get('desc_search') or '').strip()
        if not term:
            progress_done('description_search', error='Search term is empty')
            return jsonify({"status": "error", "error": "Search term is empty"}), 400
        progress_start(
            'description_search',
            len(devices),
            label=f'Searching for "{term}"…',
        )
    elif action == 'mac_check':
        from utils.search_it_progress import progress_start, progress_done
        mac = (data.get('mac_address') or '').strip()
        if not mac:
            progress_done('mac_trace', error='Target MAC is empty')
            return jsonify({"status": "error", "error": "Target MAC is empty"}), 400
        progress_start(
            'mac_trace',
            len(devices),
            label=f'Tracing {mac}…',
        )
    
    # Thread mapping router
    m = {
        'connectivity': (_connectivity_check_thread, (devices, user, pwd, enb_pwd)),
        'reachability_matrix': (_reachability_matrix_thread, (devices, user, pwd, enb_pwd)),
        'vlan_check': (_vlan_check_thread, (devices, user, pwd, enb_pwd)),
        'find_missing_vlan': (_find_missing_vlan_thread, (devices, user, pwd, enb_pwd, data.get('vlan_id'))),
        'mac_check': (_mac_check_thread, (devices, user, pwd, enb_pwd, data.get('mac_address'))),
        'description_search': (_description_search_thread, (devices, user, pwd, enb_pwd, data.get('desc_search', ''))),
        'add_vlan': (_add_vlan_thread, (devices, user, pwd, enb_pwd, data.get('vlan_id'), data.get('vlan_name'), data.get('dry_run', False), data.get('save_config', True))),
        'rename_vlan': (_rename_vlan_thread, (devices, user, pwd, enb_pwd, data.get('vlan_id'), data.get('vlan_name'), data.get('dry_run', False), data.get('save_config', True))),
        'delete_vlan': (_delete_vlan_thread, (devices, user, pwd, enb_pwd, data.get('vlan_id'), data.get('vlan_name'), data.get('dry_run', False), data.get('save_config', True))),
        'interfaces': (_interfaces_check_thread, (devices, user, pwd, enb_pwd, data.get('int_filter'))),
        'vlan_compare': (_vlan_compare_thread, (devices, user, pwd, enb_pwd)),
        'node_analyze': (_node_analyze_thread, (data.get('node_id'), devices, user, pwd, enb_pwd)),
        'node_interface_topology': (_node_interface_topology_thread, (devices, user, pwd, enb_pwd)),
        'topology': (_topology_mapper_thread, (devices, user, pwd, enb_pwd, data.get('map_mode', 'all'))),
        'utilization_live': (
            _utilization_live_thread,
            (devices, user, pwd, enb_pwd, (data.get('credential_id') or '').strip(), util_live_diag, util_live_job),
        ),
        'l3_topology': (_l3_map_thread, (devices, user, pwd, enb_pwd, 'l3')),
        'flow_map': (_l3_map_thread, (devices, user, pwd, enb_pwd, 'flow')),
        'advanced_l2_map': (_advanced_l2_map_thread, (devices, user, pwd, enb_pwd)),
        'audit': (_network_audit_thread, (devices, user, pwd, enb_pwd)),
        'failure_correlation': (_failure_correlation_thread, (devices, user, pwd, enb_pwd)),
        'backup': (_config_backup_thread, (devices, user, pwd, enb_pwd, data.get('config_filter'))),
        'save_config': (_save_config_thread, (devices, user, pwd, enb_pwd))
    }
    
    if action in m:
        from utils.task_control_plane import register_task, complete_task, is_cancelled, bind_task

        fn, args = m[action]
        task_id = register_task(
            action,
            label=f'{action} ({len(devices)} device(s))',
            meta={
                'device_count': len(devices),
                'devices_total': len(devices),
                'devices_done': 0,
                'action': action,
                'inventory_source': resolved.get('source_used'),
                'inventory_state': resolved.get('state'),
                'credential_id': (data.get('credential_id') or '').strip() or None,
            },
        )

        def _task_wrapper():
            try:
                from utils.task_credentials import set_task_become_password
                set_task_become_password(data.get('become_password') or '')
                bind_task(task_id)
                if is_cancelled(task_id):
                    complete_task(task_id, 'cancelled')
                    add_log(f'[Control Plane] Task {task_id} cancelled before start')
                    return
                fn(*args)
                # Topology mapper sets _last_topology.status=error when no HTML —
                # do not mark the control-plane job complete in that case.
                if action == 'topology':
                    topo = _last_topology or {}
                    if topo.get('status') != 'complete':
                        complete_task(
                            task_id,
                            'error',
                            (topo.get('error') or 'No topology HTML produced')[:200],
                        )
                        return
                complete_task(task_id, 'complete')
            except Exception as exc:
                complete_task(task_id, 'error', str(exc))
                raise

        threading.Thread(target=_task_wrapper, daemon=True).start()
        started = {"status": "started", "task_id": task_id}
        started.update(_inventory_meta(resolved))
        started['device_count'] = len(devices)
        started['artifacts_expected'] = action not in ('connectivity',)
        cid = (data.get('credential_id') or '').strip()
        if cid:
            started['credential_id'] = cid
        return jsonify(started)
    else:
        # v6.0: Check plugin registry for dynamic plugins
        from modules.plugin_registry import get_registry
        registry = get_registry()
        
        if registry.exists(action):
            # Dynamic plugin execution
            from utils.task_control_plane import register_task, complete_task, is_cancelled, bind_task
            params = data.get('params', {})
            task_id = register_task(
                action,
                label=f'plugin:{action}',
                meta={
                    'device_count': len(devices),
                    'inventory_source': resolved.get('source_used'),
                    'inventory_state': resolved.get('state'),
                    'artifacts_expected': None,
                },
            )

            def _plugin_wrapper():
                try:
                    from utils.task_credentials import set_task_become_password
                    set_task_become_password(data.get('become_password') or '')
                    bind_task(task_id)
                    if is_cancelled(task_id):
                        complete_task(task_id, 'cancelled')
                        return
                    _plugin_execute_thread(
                        action, devices, user, pwd, enb_pwd, params, vault_extras=resolved_creds
                    )
                    complete_task(task_id, 'complete')
                except Exception as exc:
                    complete_task(task_id, 'error', str(exc))

            threading.Thread(target=_plugin_wrapper, daemon=True).start()
            started = {"status": "started", "task_id": task_id}
            started.update(_inventory_meta(resolved))
            started['device_count'] = len(devices)
            started['artifacts_expected'] = None
            return jsonify(started)
        else:
            return jsonify({"error": f"Invalid API Action {action}"})


@app.route('/api/vlan/validate', methods=['POST'])
@localhost_required
def api_vlan_validate():
    """Dry-run VLAN validation pipeline before confirm-and-execute."""
    data, err = _require_json_body()
    if err:
        return err
    action = data.get('action')
    if action not in ('add_vlan', 'rename_vlan', 'delete_vlan'):
        return jsonify({'error': 'action must be add_vlan, rename_vlan, or delete_vlan'}), 400
    cred_err = _overlay_request_secrets(data)
    if cred_err:
        return cred_err
    user, pwd, enb_pwd = data.get('username'), data.get('password'), data.get('enable_pwd')
    if not user or not pwd:
        return jsonify({'error': 'Credentials required'}), 400
    inv = data.get('inventory', '')
    resolved, inv_err = _resolve_request_inventory(data, action)
    if inv_err:
        return inv_err
    inv = resolved['text']
    add_log(
        f"[Inventory] vlan-validate source={resolved['source_used']} "
        f"state={resolved['state']} devices={resolved['accepted_count']}"
    )
    devices = filter_inventory(
        inv, data.get('target_mode'), data.get('filter', ''),
        data.get('single_host', ''), data.get('group', 'All'),
    )
    if not devices:
        return jsonify({'error': 'No devices in scope'}), 400
    vid = data.get('vlan_id')
    vname = data.get('vlan_name', '')
    if not vid:
        return jsonify({'error': 'vlan_id required'}), 400
    if action != 'delete_vlan' and not vname:
        return jsonify({'error': 'vlan_name required for add/rename'}), 400

    from utils.vlan_validate import validate_vlan_operation
    result = validate_vlan_operation(
        action, devices, user, pwd, enb_pwd, str(vid), vname or '', log_func=add_log,
    )
    return jsonify({'status': 'success', 'data': result, **_inventory_meta(resolved)})


@app.route('/api/control-plane/tasks', methods=['GET'])
def api_control_plane_tasks():
    from utils.task_control_plane import list_tasks
    include_finished = request.args.get('all', '1') != '0'
    return jsonify({'tasks': list_tasks(include_finished=include_finished)})


@app.route('/api/control-plane/tasks/<task_id>/cancel', methods=['POST'])
@localhost_required
def api_control_plane_cancel(task_id):
    from utils.task_control_plane import request_cancel, get_task
    ok = request_cancel(task_id)
    if not ok:
        return jsonify({'error': 'Task not found'}), 404
    add_log(f'[Control Plane] Cancel requested for task {task_id}')
    return jsonify({'ok': True, 'task': get_task(task_id)})


@app.route('/api/jobs', methods=['GET'])
@localhost_required
def api_jobs_list():
    """Evidence catalog: recent execute jobs. Metadata only; no artifact bodies."""
    from utils.job_index import clamp_limit, list_jobs
    limit = request.args.get('limit', '50')
    jobs = list_jobs(limit)
    return jsonify({
        'jobs': jobs,
        'count': len(jobs),
        'limit': clamp_limit(limit),
    })


@app.route('/api/jobs/<task_id>', methods=['GET'])
@localhost_required
def api_jobs_one(task_id):
    """Single job metadata. Does not open or return file contents."""
    from utils.job_index import get_job
    job = get_job(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'job': job})


@app.route('/api/jobs/<task_id>/pack', methods=['GET'])
@localhost_required
def api_jobs_pack(task_id):
    """ZIP evidence pack for a job's contained run_dir (manager-shareable)."""
    from flask import send_file
    from utils.evidence_pack import build_job_pack

    buf, name, meta = build_job_pack(task_id)
    if buf is None:
        err = meta or {'error': 'Pack unavailable'}
        return jsonify({'error': err.get('error')}), int(err.get('status') or 404)
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=name or 'nst_evidence.zip',
    )


@app.route('/api/jobs/<task_id>/open', methods=['GET'])
@localhost_required
def api_jobs_open(task_id):
    """Open the best report file for a job (HTML preferred) inside the contained run_dir."""
    from flask import send_file
    from utils.job_index import contained_run_dir, get_job
    from utils.output_paths import get_data_root

    job = get_job(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    rel = job.get('run_dir')
    if not rel or not job.get('artifacts_available'):
        return jsonify({'error': 'No artifacts on disk'}), 404
    abs_dir = os.path.join(get_data_root(), *str(rel).replace('\\', '/').split('/'))
    if not contained_run_dir(abs_dir) or not os.path.isdir(abs_dir):
        return jsonify({'error': 'Run directory unsafe or missing'}), 403
    prefer = []
    other = []
    for root, _dirs, files in os.walk(abs_dir):
        for name in files:
            fp = os.path.join(root, name)
            low = name.lower()
            if low.endswith(('.html', '.htm')):
                prefer.append(fp)
            elif low.endswith(('.txt', '.csv', '.json', '.md')):
                other.append(fp)
    pick = (prefer or other or [None])[0]
    if not pick or not os.path.isfile(pick):
        return jsonify({'error': 'No openable report in run folder'}), 404
    mime = 'text/html' if pick.lower().endswith(('.html', '.htm')) else 'text/plain'
    return send_file(pick, mimetype=mime)


@app.route('/api/jobs/<task_id>/reveal', methods=['POST'])
@localhost_required
def api_jobs_reveal(task_id):
    """Reveal run folder in OS file manager (localhost operator only)."""
    import subprocess
    from utils.job_index import contained_run_dir, get_job
    from utils.output_paths import get_data_root

    job = get_job(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    rel = job.get('run_dir')
    if not rel:
        return jsonify({'error': 'No run_dir'}), 404
    abs_dir = os.path.abspath(os.path.join(get_data_root(), *str(rel).replace('\\', '/').split('/')))
    if not contained_run_dir(abs_dir) or not os.path.isdir(abs_dir):
        return jsonify({'error': 'Run directory unsafe or missing'}), 403
    try:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', abs_dir])
        elif sys.platform.startswith('win'):
            subprocess.Popen(['explorer', abs_dir])
        else:
            subprocess.Popen(['xdg-open', abs_dir])
        return jsonify({'ok': True, 'run_dir': rel})
    except Exception as exc:
        return jsonify({'error': f'Reveal failed: {exc}', 'run_dir': rel}), 500


@app.route('/api/jobs/<task_id>/rerun', methods=['POST'])
@localhost_required
def api_jobs_rerun(task_id):
    """Safe re-run: returns prior action metadata so UI can re-execute with current vault session.

    Never stores or returns passwords. Operator must have session credentials selected.
    """
    from utils.job_index import get_job
    job = get_job(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    action = (job.get('action') or '').strip()
    if not action:
        return jsonify({'error': 'Job has no action to re-run'}), 400
    return jsonify({
        'ok': True,
        'action': action,
        'inventory_source': job.get('inventory_source'),
        'device_count': job.get('device_count'),
        'hint': 'Call /api/execute with current credential_id and inventory; secrets are never replayed from the index.',
    })


@app.route('/api/backups', methods=['GET'])
@localhost_required
def api_backups_list():
    """List config backups under data_root/backups (Oxidized-style catalog)."""
    from utils.backup_api import list_backup_records
    host = (request.args.get('host') or request.args.get('hostname') or '').strip() or None
    rows = list_backup_records(hostname=host)
    return jsonify({'backups': rows, 'count': len(rows)})


@app.route('/api/backups/diff', methods=['POST'])
@localhost_required
def api_backups_diff():
    """Unified diff between two contained backup files."""
    from utils.backup_api import compare_backup_paths
    data = request.get_json(silent=True) or {}
    path_a = data.get('path_a') or data.get('backup_a') or ''
    path_b = data.get('path_b') or data.get('backup_b') or ''
    diff, err = compare_backup_paths(path_a, path_b)
    if err:
        return jsonify({'error': err}), 400
    return jsonify({'success': True, 'diff': diff})


@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    """v6.2.6: werkzeug.server.shutdown was removed in Werkzeug 2.1.0.
    Use os._exit(0) in a delayed thread so the HTTP response returns first.
    This avoids port TIME_WAIT issues on Windows with SIGTERM.
    """
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code
    try:
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()
    except Exception:
        pass
    add_log("--- User requested SHUTDOWN. Terminating in 1s... ---")
    def _do_exit():
        import time
        time.sleep(1.0)
        os._exit(0)
    threading.Thread(target=_do_exit, daemon=True).start()
    return jsonify({"status": "shutting_down"})

@app.route('/api/version')
def api_version():
    return jsonify({
        "version": VERSION,
        "date": UPDATE_DATE,
        "data_root": get_data_root(),
        "outputs_root": os.path.join(get_data_root(), 'outputs'),
    })


def _parse_changelog_highlights(version_tag):
    """Parse bullet highlights from CHANGELOG for in-app release notes.

    Supports Keep-a-Changelog ``## [7.2.1]`` / ``## [v7.2.1]`` and this
    repo's working-tree style ``### 7.2.1 — …`` under Unreleased.
    """
    highlights = []
    try:
        path = _get_resource_path('CHANGELOG.md')
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        bare = str(version_tag or '').lstrip('vV').strip()
        markers = [
            f"## [{bare}]",
            f"## [v{bare}]",
            f"### {bare} —",
            f"### {bare} ",
            f"### {bare}\n",
        ]
        section = None
        for marker in markers:
            if marker in text:
                section = text.split(marker, 1)[1]
                break
        if section is None:
            return highlights
        cut = re.search(r'\n(?:## |### )', section)
        if cut:
            section = section[: cut.start()]
        for line in section.splitlines():
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                highlights.append(line.lstrip('-* ').strip())
    except Exception:
        pass
    return highlights[:12]


@app.route('/api/release-notes')
def api_release_notes():
    ver = VERSION if VERSION.startswith('v') else f'v{VERSION}'
    highlights = _parse_changelog_highlights(ver)
    if not highlights:
        rn_path = _get_resource_path(f'docs/11-release-management/RELEASE_NOTES_{VERSION}.md')
        try:
            with open(rn_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('- '):
                        highlights.append(line[2:].strip())
        except Exception:
            pass
    return jsonify({
        'version': VERSION,
        'date': UPDATE_DATE,
        'highlights': highlights,
    })

@app.route('/api/readme')
def api_readme():
    try:
        path = _get_resource_path("README.md")
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify({"content": f.read()})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/extract_docs', methods=['POST'])
@localhost_required
def api_extract_docs():
    import shutil
    docs = ["README.md", "QA_TESTING_CHECKLIST.txt", "walkthrough.txt", "inventory.txt"]
    docs_dir = "DOCS"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
    extracted = []
    errors = []
    for doc in docs:
        try:
            src = _get_resource_path(doc)
            if os.path.exists(src):
                dest = os.path.join(docs_dir, doc)
                shutil.copy2(src, dest)
                extracted.append(doc)
            else:
                errors.append(f"{doc} (Not in bundle)")
        except Exception as e:
            errors.append(f"{doc}: {str(e)}")
            
    if extracted:
        add_log(f"[System] Extracted documentation files to local folder: {docs_dir}/({', '.join(extracted)})")
    if errors:
        add_log(f"[System] [WARNING] Failed to extract: {', '.join(errors)}")
        
    return jsonify({
        "status": "done", 
        "folder": docs_dir,
        "extracted": extracted, 
        "errors": errors
    })

# ----- v6.0 Plugin Management API -----
@app.route('/api/plugins/list')
def api_plugins_list():
    """Return list of all registered plugins with metadata."""
    from modules.plugin_registry import get_registry
    from utils.api_security import plugin_install_model
    registry = get_registry()
    
    plugins = registry.get_all_metadata()
    errors = registry.get_errors()
    body = {
        "plugins": plugins,
        "errors": errors,
        "count": len(plugins),
    }
    body.update(plugin_install_model())
    return jsonify(body)

@app.route('/api/plugins/reload', methods=['POST'])
def api_plugins_reload():
    """Hot-reload the plugin registry."""
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code
    from modules.plugin_registry import get_registry
    # plugins_dir is never taken from the request (trusted local path only)
    registry = get_registry()
    registry.reload()
    errors = registry.get_errors()
    add_log(
        f"[Plugin System] Registry reload requested from={request.remote_addr or 'unknown'} "
        f"count={len(registry.get_all_metadata())} errors={len(errors)} "
        f"install_model=offline_local_directory execution_model=in_process"
    )
    body = {
        "status": "reloaded",
        "count": len(registry.get_all_metadata()),
        "errors": errors,
        "execution_model": "in_process",
        "sandbox": False,
        "trust_warning": (
            "Plugins execute in-process as the NST user. AST denylist is not a sandbox."
        ),
    }
    from utils.api_security import plugin_install_model
    body.update(plugin_install_model())
    return jsonify(body)

@app.route('/api/plugins/history/<plugin_id>')
def api_plugin_history(plugin_id):
    """Get backup history for a specific plugin."""
    from modules.plugin_registry import get_registry
    registry = get_registry()
    
    history = registry.get_plugin_history(plugin_id)
    return jsonify({
        "plugin_id": plugin_id,
        "history": history
    })


@app.route('/api/plugins/rollback', methods=['POST'])
@localhost_required
def api_plugin_rollback():
    """Rollback a plugin file to a prior backup (localhost operator only)."""
    data, err = _require_json_body()
    if err:
        return err
    plugin_id = (data.get('plugin_id') or '').strip()
    backup_filename = (data.get('backup_filename') or data.get('filename') or '').strip()
    if not plugin_id or not backup_filename:
        return jsonify({'error': 'plugin_id and backup_filename required'}), 400
    if '/' in backup_filename or '\\' in backup_filename or '..' in backup_filename:
        return jsonify({'error': 'Invalid backup filename'}), 400
    from modules.plugin_registry import get_registry
    ok, msg = get_registry().rollback(plugin_id, backup_filename)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'ok': True, 'message': msg})


@app.route('/api/capabilities/parsers')
@localhost_required
def api_capabilities_parsers():
    """Report ntc-templates / TextFSM / NAPALM-style layer availability."""
    from modules.ntc_parse import capability_report as ntc_cap
    from modules.napalm_style import capability_report as napalm_cap
    return jsonify({
        'ntc': ntc_cap(),
        'napalm_style': napalm_cap(),
        'snmp_graphs': True,
    })


@app.route('/api/snmp/interface-graphs', methods=['POST'])
@localhost_required
def api_snmp_interface_graphs():
    """Build offline SNMP IF-MIB counter sparkline HTML for one host."""
    data, err = _require_json_body()
    if err:
        return err
    host = (data.get('host') or data.get('ip') or '').strip()
    if not host:
        return jsonify({'error': 'host required'}), 400

    creds: dict = {}
    try:
        from utils.session_cred_cache import get_session_credentials
        from utils.vault_credentials import resolve_execute_credentials
        sess = get_session_credentials() or {}
        bundle = resolve_execute_credentials(data, credential_manager, session_creds=sess)
        for k in (
            'snmp_version', 'snmp_community', 'snmp_v3_user',
            'snmp_port', 'snmp_timeout',
        ):
            if bundle.get(k) is not None:
                creds[k] = bundle.get(k)
    except Exception:
        if data.get('snmp_community'):
            creds = {
                'snmp_version': data.get('snmp_version') or '2c',
                'snmp_community': data.get('snmp_community'),
            }

    from modules.snmp_interface_graphs import collect_interface_counters, counters_to_html
    from utils.output_paths import prepare_run_output, path_in_run, get_data_root

    payload = collect_interface_counters(
        host, creds,
        samples=int(data.get('samples') or 2),
        interval_sec=float(data.get('interval_sec') or 1.0),
    )
    html_doc = counters_to_html(payload)
    paths = prepare_run_output('reports')
    safe_host = ''.join(c if c.isalnum() or c in '._-' else '_' for c in host)[:64]
    out_path = path_in_run(paths, f'snmp_iface_{safe_host}.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    try:
        rel = os.path.relpath(out_path, get_data_root()).replace('\\', '/')
    except Exception:
        rel = out_path
    return jsonify({
        'ok': payload.get('status') == 'ok',
        'status': payload.get('status'),
        'host': host,
        'interface_count': len(payload.get('interfaces') or []),
        'html_path': rel,
        'open_url': '/api/snmp/interface-graphs/open?path=' + rel,
        'reason': payload.get('reason'),
        'note': payload.get('note'),
    })


@app.route('/api/snmp/interface-graphs/open')
@localhost_required
def api_snmp_interface_graphs_open():
    """Serve a contained SNMP graphs HTML report."""
    from flask import send_file as _send
    raw = (request.args.get('path') or '').strip()
    if not raw:
        return jsonify({'error': 'path required'}), 400
    try:
        from utils.output_paths import get_data_root, get_outputs_root
        root = os.path.abspath(get_data_root())
        cand = raw if os.path.isabs(raw) else os.path.join(root, raw)
        cand = os.path.abspath(os.path.normpath(cand))
        out_root = os.path.abspath(get_outputs_root())
        if os.path.commonpath([out_root, cand]) != out_root or not os.path.isfile(cand):
            return jsonify({'error': 'Invalid or missing report'}), 403
        return _send(cand, mimetype='text/html')
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/plugins/debug')
def api_plugins_debug():
    """Debug endpoint to troubleshoot plugin loading issues."""
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code
    from modules.plugin_registry import get_registry
    import sys
    registry = get_registry()
    
    # Get list of files in plugins directory
    plugins_dir = registry.plugins_dir
    files_in_dir = []
    try:
        if os.path.exists(plugins_dir):
            files_in_dir = os.listdir(plugins_dir)
    except Exception as e:
        files_in_dir = [f"ERROR: {e}"]
    
    return jsonify({
        "sys_frozen": getattr(sys, 'frozen', False),
        "sys_executable": sys.executable,
        "plugins_dir": plugins_dir,
        "plugins_dir_exists": os.path.exists(plugins_dir),
        "files_in_plugins_dir": files_in_dir,
        "loaded_plugins": list(registry._plugins.keys()),
        "plugin_count": len(registry._plugins),
        "error_count": len(registry._errors),
        "errors": registry._errors,
        "sys_path": sys.path[:5]  # First 5 entries
    })

@app.route('/api/plugins/upload', methods=['POST'])
def api_plugin_upload():
    """Runtime HTTP plugin install is disabled (RB-ZT-01). Never persists files."""
    denied, code = _require_localhost_operator()
    if denied:
        return denied, code
    from utils.api_security import (
        PLUGIN_UPLOAD_DISABLED_ERROR,
        plugin_install_model,
        plugin_upload_is_enabled,
    )
    raw_name = ''
    uploaded = request.files.get('file')
    if uploaded is not None:
        raw_name = uploaded.filename or ''
    safe_label = os.path.basename(str(raw_name).replace('\\', '/').replace('\x00', ''))[:80]
    low = safe_label.lower()
    if any(k in low for k in ('password', 'secret', 'token', 'enable')):
        safe_label = '[redacted-name]'
    add_log(
        f"[Plugin System] Runtime upload blocked (offline install only). name={safe_label or '-'}"
    )
    if plugin_upload_is_enabled():
        add_log('[Plugin System] Unexpected: plugin_upload_is_enabled True (must stay False)')
    body = {
        'error': PLUGIN_UPLOAD_DISABLED_ERROR,
    }
    body.update(plugin_install_model())
    return jsonify(body), 403

# ============================================================================
# STANDARDS VALIDATOR API (v6.5.5)
# ============================================================================

@app.route('/api/standards/run', methods=['POST'])
@localhost_required
def api_standards_run():
    """
    Run the Standards Validator against the selected device scope.

    Accepts the same inventory/scope parameters as /api/execute plus
    standards-specific params: policy_file, severity_filter, category_filter,
    generate_remediation_script.

    Returns results synchronously (not threaded) so the frontend gets
    structured JSON it can render directly — no polling needed.
    """
    data, err = _require_json_body()
    if err:
        return err
    cred_err = _overlay_request_secrets(data)
    if cred_err:
        return cred_err

    user    = data.get('username', '')
    pwd     = data.get('password', '')
    enb_pwd = data.get('enable_pwd', '')
    inv     = data.get('inventory', '')
    mode    = data.get('target_mode', 'bulk')
    filt    = data.get('filter', '')
    single  = data.get('single_host', '')
    group   = data.get('group', 'All')
    resolved, inv_err = _resolve_request_inventory(data, 'standards')
    if inv_err:
        return inv_err
    inv = resolved['text']
    add_log(
        f"[Inventory] standards source={resolved['source_used']} "
        f"state={resolved['state']} devices={resolved['accepted_count']}"
    )

    policy_file  = data.get('policy_file', 'policies/standards.yaml')
    sev_filter   = data.get('severity_filter', 'all')
    cat_filter   = data.get('category_filter', '')
    gen_script   = data.get('generate_remediation_script', True)

    if not inv.strip():
        return jsonify({"error": "No inventory provided"}), 400
    if not user or not pwd:
        return jsonify({"error": "Credentials required"}), 400

    devices = filter_inventory(inv, mode, filt, single, group)
    if not devices:
        return jsonify({"error": "Filtered scope resulted in 0 target devices. Check inventory/group settings."}), 400

    add_log(f"[Standards] Running validation on {len(devices)} device(s)...")

    params = {
        "policy_file"                : policy_file,
        "severity_filter"            : sev_filter,
        "category_filter"            : cat_filter,
        "generate_remediation_script": gen_script,
    }
    credentials = _credentials_dict_from_request({
        'username': user,
        'password': pwd,
        'enable_pwd': enb_pwd,
        'fallback_credentials': data.get('fallback_credentials') or [],
        'secondary_credential': data.get('secondary_credential'),
        'third_credential': data.get('third_credential'),
    })
    # Stamp devices for any nested connect_device paths
    from modules.network_base import attach_fallback_to_devices
    devices = attach_fallback_to_devices(
        devices,
        fallback_credentials=data.get('fallback_credentials'),
        secondary=data.get('secondary_credential'),
        third=data.get('third_credential'),
    )
    config = {"timeout": 30, "max_retries": 1, "log_level": "INFO", "parallel_workers": 10}

    from modules.plugin_registry import get_registry
    from utils.task_control_plane import bind_task, complete_task, register_task
    registry = get_registry()
    task_id = register_task(
        'standards',
        label=f'standards ({len(devices)} device(s))',
        meta={
            'inventory_source': resolved.get('source_used'),
            'device_count': len(devices),
            'artifacts_expected': True,
            'synchronous': True,
            'cancel_scope': 'none',
        },
    )
    bind_task(task_id)

    results = []
    for dev in devices:
        host = dev.get('host', 'unknown')
        add_log(f"[Standards] Checking {host}...")
        try:
            result = registry.execute(
                "standards_validator", dev, credentials, params, config,
                log_func=add_log
            )
            results.append(result)
        except Exception as e:
            results.append({
                "device": host,
                "status": "fail",
                "data"  : {},
                "error" : str(e)
            })

    compliant_count = sum(1 for r in results if r.get('data', {}).get('compliant', False))
    add_log(f"[Standards] Complete: {compliant_count}/{len(results)} compliant")

    # v6.5.8: Generate consolidated single report for bulk runs
    consolidated_path = None
    if len(results) > 0:
        try:
            from utils.report_formatter import generate_consolidated_standards_report
            consolidated_path = generate_consolidated_standards_report(
                policy_file, sev_filter, cat_filter, results
            )
            add_log(f"[Standards] Consolidated report written under outputs/")
        except Exception as e:
            add_log(f"[Standards] Warning: Could not generate consolidated report: {type(e).__name__}")

    art = _public_outputs_meta(consolidated_path)
    job_status = 'complete'
    try:
        complete_task(task_id, job_status)
    except Exception:
        pass

    payload = {
        "results": results,
        "total": len(results),
        "compliant": compliant_count,
        "consolidated_report": art.get('safe_path'),
        "task_id": task_id,
        "inventory_source": resolved.get('source_used'),
        "inventory_state": resolved.get('state'),
        "device_count": len(devices),
        "artifacts_expected": True,
        "artifacts_available": art['artifacts_available'],
        "run_dir": art['run_dir'],
        "run_dir_exists": art['run_dir_exists'],
        "synchronous": True,
        "cancel_scope": "none",
    }
    return jsonify(payload)


@app.route('/api/standards/policies', methods=['GET'])
def api_standards_policies():
    """
    Return the list of available policy files AND policy categories/IDs.
    Supports both YAML and JSON policy files.
    """
    policy_file = request.args.get('file', 'policies/standards.yaml')
    list_files = request.args.get('list_files', 'false').lower() == 'true'
    
    result = {
        "available_files": [],
        "total_policies": 0,
        "categories": [],
        "policies": []
    }
    
    # First, list available policy files if requested
    if list_files:
        try:
            from modules.plugins.standards_validator import list_available_policies
            result["available_files"] = list_available_policies()
        except Exception as e:
            app.logger.error(f"Error listing policy files: {e}")
    
    # Then load the specific policy file requested
    try:
        import yaml
        import json
        path = _get_resource_path(policy_file)
        if not os.path.exists(path):
            path = policy_file  # Try as-is
        
        with open(path, 'r', encoding='utf-8') as f:
            # Detect format by extension
            if path.endswith('.json'):
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        
        policies = data.get('policies', [])
        metadata = data.get('metadata', {})
        categories = sorted(set(p.get('category', 'General') for p in policies))
        
        result.update({
            "file_metadata": metadata,
            "total_policies": len(policies),
            "categories": categories,
            "policies": [
                {
                    "id": p.get('id'),
                    "category": p.get('category', 'General'),
                    "description": p.get('description', ''),
                    "severity": p.get('severity', 'medium'),
                    "platforms": p.get('platforms', []),
                }
                for p in policies
            ]
        })
        return jsonify(result)
    except Exception as e:
        result["error"] = str(e)
        return jsonify(result), 200


@app.route('/api/ping_scan', methods=['POST'])
@localhost_required
def api_ping_scan():
    """
    ICMP CIDR sweep. Not inventory, not Discovery, not STP.
    Body: { network: "192.168.1.0/24", target_source: "cidr_scan" }
    Omitted target_source is legacy_body (still CIDR of `network` only).
    """
    try:
        data, err = _require_json_body()
        if err:
            return err
        from utils.job_source import JobSourceError, resolve_cidr_scan
        try:
            resolved = resolve_cidr_scan(data)
        except JobSourceError as exc:
            from utils.search_it_progress import progress_done
            progress_done('ping_scan', error=str(exc))
            return jsonify({"status": "error", "error": str(exc), "target_source": "cidr_scan"}), 400

        network = resolved['network']
        from utils.search_it_progress import progress_start
        progress_start('ping_scan', 1, label=f'Starting CIDR ping scan for {network}…')

        from utils.task_control_plane import register_task
        task_id = register_task(
            'ping_scan',
            label=f'ping_scan CIDR {network} ({resolved["device_count"]} host(s))',
            meta={
                'inventory_source': resolved['target_source'],
                'device_count': resolved['device_count'],
                'target_source': resolved['target_source'],
            },
        )
        threading.Thread(target=_ping_scan_thread, args=(network, task_id), daemon=True).start()
        return jsonify({
            "status": "started",
            "task_id": task_id,
            "target_source": resolved['target_source'],
            "device_count": resolved['device_count'],
            "network": network,
            "warning": resolved.get('warning'),
            "artifacts_expected": True,
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


def _ping_scan_thread(network, task_id=None):
    """
    ICMP ping sweep of a CIDR. Not SSH and not inventory.
    """
    global _ping_scan_last
    from utils.task_control_plane import bind_task, complete_task, is_cancelled, should_abort
    try:
        if task_id:
            bind_task(task_id)
        add_log(f"[Ping Scan] Starting CIDR scan: {network}")

        try:
            network_obj = ipaddress.ip_network(network, strict=False)
        except ValueError as e:
            add_log(f"[Ping Scan] Invalid network format: {e}")
            from utils.search_it_progress import progress_done
            progress_done('ping_scan', error=f'Invalid network: {e}')
            if task_id:
                complete_task(task_id, 'error', str(e))
            return

        hosts = list(network_obj.hosts())
        total_hosts = len(hosts)

        add_log(f"[Ping Scan] Scanning {total_hosts} hosts in {network} (not inventory).")

        from utils.search_it_progress import progress_done, progress_start_if_needed, progress_tick
        progress_start_if_needed('ping_scan', total_hosts, label=f'Ping sweep {network}…')

        used_ips = []
        unused_ips = []

        import sys
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
            ping_cmd = lambda ip_str: ['ping', '-n', '1', '-w', '1000', ip_str]
        else:
            startupinfo = None
            creationflags = 0
            ping_cmd = lambda ip_str: ['ping', '-c', '1', '-W', '1', ip_str]

        from concurrent.futures import ThreadPoolExecutor, as_completed
        try:
            from utils.parallel_device_pool import get_max_workers
            ping_workers = min(get_max_workers(), 15)
        except Exception:
            ping_workers = 8

        def _ping_one(ip_str):
            try:
                result = subprocess.run(
                    ping_cmd(ip_str),
                    capture_output=True,
                    text=True,
                    timeout=2,
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
                return ip_str, result.returncode == 0
            except subprocess.TimeoutExpired:
                return ip_str, False
            except Exception:
                return ip_str, False

        cancelled = False
        done_count = 0
        with ThreadPoolExecutor(max_workers=ping_workers, thread_name_prefix='nst-ping') as pool:
            futures = {pool.submit(_ping_one, str(ip)): ip for ip in hosts}
            for fut in as_completed(futures):
                if should_abort():
                    cancelled = True
                    for pending in futures:
                        pending.cancel()
                    break
                done_count += 1
                ip_str, alive = fut.result()
                if alive:
                    used_ips.append(ip_str)
                else:
                    unused_ips.append(ip_str)
                if done_count % max(1, total_hosts // 10) == 0:
                    progress = int((done_count / total_hosts) * 100)
                    add_log(f"[Ping Scan] Progress: {progress}% ({done_count}/{total_hosts})")
                progress_tick(
                    'ping_scan', done_count, total_hosts, host=ip_str,
                    label=f'Pinging {ip_str} ({done_count}/{total_hosts})',
                    responsive_count=len(used_ips),
                )

        from utils.ping_scan_formatter import write_ping_scan_html
        from utils.search_report_output import prepare_search_run, slugify, write_run_manifest

        paths = prepare_search_run('ping_scan', slugify(network.replace('/', '_')))
        report_path = paths['txt_path']
        html_path = paths['html_path']
        add_log(f"[Ping Scan] Report folder: {paths['run_dir']}")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("NETWORK PING SCAN REPORT (CIDR ICMP — not inventory)\n")
            f.write("=" * 70 + "\n")
            f.write(f"Network:        {network}\n")
            f.write(f"Scan Date:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Hosts:    {total_hosts}\n")
            f.write(f"Used IPs:       {len(used_ips)}\n")
            f.write(f"Unused IPs:     {len(unused_ips)}\n")
            if cancelled:
                f.write("Status:         partial (cancelled)\n")
            f.write("\n")

            if used_ips:
                f.write("-" * 70 + "\n")
                f.write("USED IPs (Responsive to Ping):\n")
                f.write("-" * 70 + "\n")
                for ip in sorted(used_ips):
                    f.write(f"  {ip}\n")
                f.write("\n")

            if unused_ips:
                f.write("-" * 70 + "\n")
                f.write("UNUSED IPs (Unresponsive to Ping):\n")
                f.write("-" * 70 + "\n")
                for ip in sorted(unused_ips):
                    f.write(f"  {ip}\n")
                f.write("\n")

            f.write("=" * 70 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 70 + "\n")

        write_ping_scan_html(
            html_path, network, used_ips, unused_ips, total_hosts=total_hosts,
        )
        write_run_manifest(paths, {
            'network': network,
            'total_hosts': total_hosts,
            'used_count': len(used_ips),
            'unused_count': len(unused_ips),
            'target_source': 'cidr_scan',
            'cancelled': cancelled,
        })
        _ping_scan_last = {
            'network': network,
            'target_source': 'cidr_scan',
            'total_hosts': total_hosts,
            'used_count': len(used_ips),
            'unused_count': len(unused_ips),
            'used_ips': used_ips,
            'html_path': html_path,
            'txt_path': report_path,
            'run_dir': paths['run_dir'],
            'task_id': task_id,
            'artifacts_available': True,
            'partial': cancelled,
            'ts': datetime.now().isoformat(),
        }

        add_log(f"[Ping Scan] Scan complete. Used: {len(used_ips)}, Unused: {len(unused_ips)}")
        add_log(f"[Ping Scan] Text report: {report_path}")
        add_log(f"[Ping Scan] HTML report: {html_path}")
        if cancelled:
            progress_done('ping_scan', message='Ping scan cancelled (partial CIDR results)')
            if task_id:
                complete_task(task_id, 'cancelled')
        else:
            progress_done('ping_scan', message='Ping scan complete')
            if task_id:
                complete_task(task_id, 'complete')

    except Exception as e:
        from utils.search_it_progress import progress_done
        progress_done('ping_scan', error=str(e))
        add_log(f"[Ping Scan] Scan failed: {e}")
        if task_id:
            complete_task(task_id, 'error', str(e))
        _log_exception_off_console()


@app.route('/api/standards/upload', methods=['POST'])
@localhost_required
def api_standards_upload():
    """
    Upload a custom policy file (YAML or JSON).
    Saves to the standards/ directory in program directory.
    v6.9.21: Updated to save to program directory standards folder.
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    # Validate file extension
    allowed_extensions = {'.yaml', '.yml', '.json'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({
            "success": False, 
            "error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        }), 400
    
    try:
        # v6.9.21: Save to standards folder in program directory
        if getattr(sys, 'frozen', False):
            program_dir = os.path.dirname(sys.executable)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
        
        standards_dir = os.path.join(program_dir, 'standards')
        os.makedirs(standards_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        save_path = os.path.join(standards_dir, filename)
        
        # Don't overwrite built-in standards.yaml
        if filename == 'standards.yaml' and os.path.exists(save_path):
            filename = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            save_path = os.path.join(standards_dir, filename)
        
        file.save(save_path)
        
        # Validate the uploaded file
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                if ext == '.json':
                    import json
                    data = json.load(f)
                else:
                    import yaml
                    data = yaml.safe_load(f)
            
            policy_count = len(data.get('policies', []))
            
            # Return the relative path for the plugin
            return_path = f"standards/{filename}"
            
            return jsonify({
                "success": True,
                "filename": filename,
                "path": return_path,
                "policy_count": policy_count,
                "message": f"Uploaded {policy_count} policies successfully"
            })
        except Exception as e:
            # Invalid file - remove it
            os.remove(save_path)
            return jsonify({
                "success": False,
                "error": f"Invalid policy file format: {str(e)}"
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# NETWORK DISCOVERY API  (v6.9.21)
# ============================================================================

# Job stores (NEW-H4: guarded by _job_store_lock)
import uuid as _uuid
import threading as _threading
_job_store_lock = _threading.Lock()
_discovery_jobs: dict = {}
_DISCOVERY_JOBS_MAX = 50
_STP_JOBS_MAX = 50
_templates_renders: dict = {}
_last_topology: dict = {"status": "idle"}
_last_utilization_live: dict = {"status": "idle"}
_last_l3_map: dict = {"status": "idle"}
_last_port_map: dict = {"status": "idle"}
_last_failure_correlation: dict = {"status": "idle"}
_last_node_analyze: dict = {"status": "idle"}
_last_reachability_matrix: dict = {"status": "idle"}
_stp_jobs: dict = {}
_health_check_last: dict = {}
_mac_trace_last: dict = {}
_description_search_last: dict = {}
_ping_scan_last: dict = {}


def _prune_stp_jobs():
    with _job_store_lock:
        if len(_stp_jobs) <= _STP_JOBS_MAX:
            return
        ranked = sorted(
            _stp_jobs.items(),
            key=lambda item: item[1].get("started_at") or "",
            reverse=True,
        )
        for job_id, _ in ranked[_STP_JOBS_MAX:]:
            del _stp_jobs[job_id]


def _prune_discovery_jobs():
    """Keep in-memory discovery job store bounded (BUG-0005)."""
    with _job_store_lock:
        if len(_discovery_jobs) <= _DISCOVERY_JOBS_MAX:
            return
        ranked = sorted(
            _discovery_jobs.items(),
            key=lambda item: item[1].get("started_at") or "",
            reverse=True,
        )
        for job_id, _ in ranked[_DISCOVERY_JOBS_MAX:]:
            del _discovery_jobs[job_id]


def _discovery_job_snapshot(job_id):
    """Thread-safe shallow copy of a discovery job."""
    with _job_store_lock:
        job = _discovery_jobs.get(job_id)
        return dict(job) if job else None


@app.route('/api/discovery/run', methods=['POST'])
@localhost_required
def api_discovery_run():
    """
    Launch a background network discovery crawl.
    Body JSON: { seed_hosts: [...], username, password, enable_pwd,
                 max_depth (1-3), timeout (seconds) }
    Returns: { job_id, status: "started" }
    """
    data, err = _require_json_body()
    if err:
        return err
    demo_mode = bool(data.get('demo_mode', False))
    # Demo crawls use fixture graphs — no vault/SSH. Live crawls require credential_id.
    if not demo_mode:
        cred_err = _overlay_request_secrets(data)
        if cred_err:
            return cred_err
    seed_hosts = data.get('seed_hosts', [])
    username   = data.get('username', '')
    password   = data.get('password', '')
    enable_pwd = data.get('enable_pwd', '')
    from utils.job_source import JobSourceError, resolve_discovery_targets
    try:
        resolved = resolve_discovery_targets(data)
    except JobSourceError as exc:
        return jsonify({"error": str(exc)}), 400
    seed_hosts = resolved['seed_hosts']
    seed_typed = resolved['seed_typed']
    try:
        max_depth = _parse_bounded_int(data.get('max_depth', 2), 2, 'max_depth', min_val=1, max_val=3)
        timeout = _parse_bounded_int(data.get('timeout', 30), 30, 'timeout', min_val=5, max_val=300)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    from utils.discovery_profiles import resolve_scan_profile
    explicit_depth = 'max_depth' in data
    explicit_timeout = 'timeout' in data
    profile = resolve_scan_profile(
        data.get('scan_profile'),
        max_depth=max_depth if explicit_depth else None,
        timeout=timeout if explicit_timeout else None,
    )
    if not explicit_depth:
        max_depth = int(profile['max_depth'])
    if not explicit_timeout:
        timeout = int(profile['timeout'])
    try:
        max_depth = _parse_bounded_int(max_depth, 2, 'max_depth', min_val=1, max_val=3)
        timeout = _parse_bounded_int(timeout, 30, 'timeout', min_val=5, max_val=300)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    protocol   = data.get('protocol', 'Both')

    if not seed_hosts:
        return jsonify({"error": "At least one seed host is required"}), 400
    if not demo_mode and (not username or not password):
        return jsonify({"error": "Credentials required (or enable Demo mode)"}), 400

    _prune_discovery_jobs()
    from utils.task_control_plane import bind_task, complete_task, is_cancelled, register_task
    job_id = register_task(
        'discovery',
        label=f"discovery seeds={resolved['seed_count']} depth={max_depth}",
        meta={
            'inventory_source': resolved['target_source'],
            'device_count': resolved['device_count'],
            'max_depth': max_depth,
        },
    )
    with _job_store_lock:
        _discovery_jobs[job_id] = {
            "status": "running",
            "result": None,
            "error":  None,
            "started_at": datetime.now().isoformat(),
            "seed_hosts": seed_hosts,
            "max_depth": max_depth,
            "scan_profile": profile.get('profile'),
            "target_source": resolved['target_source'],
            "seed_count": resolved['seed_count'],
            "task_id": job_id,
            "cancel": False,
            "progress": {
                "current_host": "",
                "hop": 0,
                "devices_found": 0,
                "links_found": 0,
                "queue_remaining": 0,
                "last_log_lines": [],
            },
        }

    def _run():
        def _disc_log(line):
            add_log(line)
            with _job_store_lock:
                job = _discovery_jobs.get(job_id)
                if job:
                    prog = job.get('progress') or {}
                    lines = list(prog.get('last_log_lines') or [])
                    lines.append(str(line)[:240])
                    prog['last_log_lines'] = lines[-20:]
                    job['progress'] = prog

        try:
            bind_task(job_id)
            if is_cancelled(job_id):
                with _job_store_lock:
                    if job_id in _discovery_jobs:
                        _discovery_jobs[job_id]["status"] = "cancelled"
                complete_task(job_id, 'cancelled')
                add_log(f"[Discovery] Job {job_id} cancelled before start")
                return
            _disc_log(
                f"[Discovery] Job {job_id} started source={resolved['target_source']} "
                f"seed_count={resolved['seed_count']} depth={max_depth} timeout={timeout} "
                f"profile={profile.get('profile')}. {profile.get('truth_note')}"
            )
            from modules.plugins.network_discovery import NetworkDiscoveryPlugin
            plugin = NetworkDiscoveryPlugin()
            credentials = {
                "username": username,
                "password": password,
                "secret": enable_pwd,
                "fallback_credentials": data.get('fallback_credentials') or [],
            }
            if data.get('secondary_credential'):
                credentials['secondary_credential'] = data['secondary_credential']
            if data.get('third_credential'):
                credentials['third_credential'] = data['third_credential']
            params = {
                "seed_hosts": seed_typed,
                "max_depth":  max_depth,
                "timeout":    timeout,
                "protocol":   protocol,
                "demo_mode":  demo_mode,
                "job_id": job_id,
                "export_json": True,
                "generate_topology_html": True,
            }
            config = {"timeout": timeout, "max_retries": 1, "log_level": "INFO", "parallel_workers": 5}
            device = {"host": seed_hosts[0], "device_type": "cisco_ios", "port": 22}
            result = plugin.execute(device, credentials, params, config, log_func=_disc_log)
            plugin_err = (result or {}).get("error")
            data_block = (result or {}).get("data") or {}
            coll = data_block.get("collection_status") or ""
            with _job_store_lock:
                if (result or {}).get("status") == "error" or plugin_err:
                    err_msg = plugin_err or "Discovery plugin returned error"
                    _discovery_jobs[job_id]["status"] = "error"
                    _discovery_jobs[job_id]["error"] = str(err_msg)
                    _discovery_jobs[job_id]["result"] = result
                    add_log(f"[Discovery] Job {job_id} failed")
                    complete_task(job_id, 'error', str(err_msg)[:200])
                else:
                    _discovery_jobs[job_id]["result"] = result
                    if coll == "cancelled" or data_block.get("cancelled"):
                        _discovery_jobs[job_id]["status"] = "cancelled"
                        add_log(f"[Discovery] Job {job_id} finished — cancelled (not complete truth)")
                        complete_task(job_id, 'cancelled')
                    elif coll == "partial" or data_block.get("partial"):
                        _discovery_jobs[job_id]["status"] = "partial"
                        add_log(f"[Discovery] Job {job_id} finished — partial collection (not complete truth)")
                        complete_task(job_id, 'partial')
                    else:
                        _discovery_jobs[job_id]["status"] = "complete"
                        add_log(f"[Discovery] Job {job_id} complete (hop-bounded CDP/LLDP, not a census)")
                        complete_task(job_id, 'complete')
        except Exception as exc:
            with _job_store_lock:
                if job_id in _discovery_jobs:
                    _discovery_jobs[job_id]["status"] = "error"
                    _discovery_jobs[job_id]["error"]  = str(exc)
            add_log(f"[Discovery] Job {job_id} FAILED")
            complete_task(job_id, 'error', str(exc)[:200])
            _log_exception_off_console()

    threading.Thread(target=_run, daemon=True).start()
    started = {
        "job_id": job_id,
        "task_id": job_id,
        "status": "started",
        "target_source": resolved['target_source'],
        "seed_count": resolved['seed_count'],
        "max_depth": max_depth,
        "duplicates_omitted": resolved.get('duplicates_omitted') or 0,
        "inventory_warning": resolved.get('warning'),
    }
    return jsonify(started)


@app.route('/api/discovery/cancel/<job_id>', methods=['POST'])
@localhost_required
def api_discovery_cancel(job_id):
    """Stop an in-flight CDP/LLDP crawl; the crawler returns a partial graph."""
    with _job_store_lock:
        job = _discovery_jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if job.get("status") != "running":
            return jsonify({
                "job_id": job_id,
                "status": job.get("status"),
                "cancel": False,
                "message": "Job is not running",
            })
        job["cancel"] = True
        task_id = job.get("task_id") or job_id
    try:
        from utils.task_control_plane import request_cancel, request_session_cancel
        request_cancel(task_id)
        request_session_cancel(job_id)
    except Exception:
        pass
    return jsonify({"job_id": job_id, "status": "cancelling", "cancel": True, "ssh_disconnect": True})


@app.route('/api/discovery/profiles')
def api_discovery_profiles():
    """Named scan profiles (hop/timeout). Not a fabric census."""
    from utils.discovery_profiles import PROFILES
    return jsonify({"profiles": PROFILES, "default": "standard"})


@app.route('/api/discovery/program-status')
def api_discovery_program_status():
    """Phase 6 Wave 1 — Discovery Program Status (confirmed / incomplete / readiness).

    Read-only. Reuses Phase 5 readiness register; does not invent topology or
    clear the hard-stop release gate. Optional ``job_id`` attaches session crawl counts.
    """
    from utils.discovery_program_status import build_discovery_program_status

    job_id = (request.args.get('job_id') or '').strip()
    job = None
    if job_id:
        snap = _discovery_job_snapshot(job_id)
        if snap:
            job = dict(snap)
            job['job_id'] = job_id
    payload = build_discovery_program_status(job=job)
    return jsonify(payload)


def _job_collection_status(job):
    if not job:
        return None
    st = job.get("status")
    if st == "running":
        return "running"
    if st == "error":
        return "error"
    result = job.get("result") or {}
    data = result.get("data") if isinstance(result, dict) else {}
    if not isinstance(data, dict):
        data = {}
    return data.get("collection_status") or ("complete" if st == "complete" else st)


@app.route('/api/discovery/status/<job_id>')
def api_discovery_status(job_id):
    """Poll job status. Returns { status, result, error, collection_status }."""
    job = _discovery_job_snapshot(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    coll = _job_collection_status(job)
    return jsonify({
        "job_id":     job_id,
        "status":     job["status"],
        "result":     job["result"],
        "error":      job["error"],
        "started_at": job.get("started_at"),
        "seed_hosts": job.get("seed_hosts"),
        "max_depth":  job.get("max_depth"),
        "scan_profile": job.get("scan_profile"),
        "target_source": job.get("target_source"),
        "seed_count": job.get("seed_count"),
        "task_id": job.get("task_id") or job_id,
        "progress":   job.get("progress"),
        "collection_status": coll,
        "operator_truth": (
            "not complete truth — cancelled"
            if coll == "cancelled"
            else "not complete truth — partial"
            if coll == "partial"
            else "error"
            if coll == "error"
            else "running"
            if coll == "running"
            else "complete as collected (CDP/LLDP hop-bounded; not overlay)"
        ),
    })


@app.route('/api/discovery/export/<job_id>')
def api_discovery_export(job_id):
    """Return raw JSON inventory export for a completed job."""
    from flask import send_file as _send
    job = _discovery_job_snapshot(job_id)
    if not job or job.get("status") not in ("complete", "cancelled", "partial"):
        return jsonify({"error": "Job not complete or not found"}), 404

    result_data = job.get("result") or {}
    data_block  = result_data.get("data") or {}
    export_path = data_block.get("inventory_json_path") or data_block.get("json_path")

    if export_path and os.path.exists(export_path):
        return _send(export_path, as_attachment=True,
                     download_name=f"discovery_{job_id}.json",
                     mimetype="application/json")

    # Fallback: inline JSON — include links and honesty flags (not devices-only).
    from utils.discovery_schema import annotate_export
    payload = annotate_export({
        "job_id": job_id,
        "devices": data_block.get("devices", []),
        "links": data_block.get("links", []),
        "collection_status": data_block.get("collection_status"),
        "partial": bool(data_block.get("partial")),
        "cancelled": bool(data_block.get("cancelled")),
        "overlay_collected": bool(data_block.get("overlay_collected")),
        "overlay_links": data_block.get("overlay_links") or [],
        "overlay_note": data_block.get("overlay_note") or '',
    })
    return jsonify(payload)


@app.route('/api/discovery/report/<job_id>')
def api_discovery_report(job_id):
    """Serve Vis.js topology HTML for a completed discovery job."""
    from flask import send_file as _send
    job = _discovery_job_snapshot(job_id)
    if not job or job.get('status') not in ('complete', 'cancelled', 'partial'):
        return jsonify({'error': 'Job not complete or not found'}), 404
    result_data = (job.get('result') or {}).get('data') or job.get('result') or {}
    if isinstance(result_data, dict) and 'data' in result_data:
        result_data = result_data['data']
    html_path = (
        result_data.get('topology_path')
        or result_data.get('html_report')
        or result_data.get('report_path')
    )
    if html_path and os.path.exists(html_path):
        return _send(html_path, mimetype='text/html')
    return jsonify({'error': 'Topology report file not found'}), 404


@app.route('/api/discovery/advanced_map/l2')
def api_discovery_advanced_map_l2():
    """Serve last Advanced L2 map or return status."""
    return _serve_l3_map_response('advanced_l2')


@app.route('/api/discovery/advanced_map/l3')
def api_discovery_advanced_map_l3():
    """Serve last L3 routing map HTML."""
    return _serve_l3_map_response('l3')


@app.route('/api/discovery/advanced_map/flow')
def api_discovery_advanced_map_flow():
    """Serve last network flow map HTML."""
    return _serve_l3_map_response('flow')


def _serve_l3_map_response(expected_kind):
    from flask import send_file as _send
    if _last_l3_map.get('status') == 'complete' and _last_l3_map.get('map_kind') == expected_kind:
        html_path = _last_l3_map.get('html_path')
        if html_path and os.path.isfile(html_path):
            return _send(html_path, mimetype='text/html')
    if _last_l3_map.get('status') == 'running':
        return jsonify({
            'status': 'running',
            'map_kind': _last_l3_map.get('map_kind'),
            'message': 'Map generation in progress — use Swiss Tools L3 panel or poll /api/l3-map/status',
        }), 202
    return jsonify({
        'status': _last_l3_map.get('status', 'idle'),
        'error': 'No completed map — run from Swiss Tools (L3 Routing / Flow / Advanced L2 buttons)',
        'map_kind': expected_kind,
    }), 404


# ============================================================================
# HEALTH CHECK WIZARD (v7.0.0)
# ============================================================================

def _run_health_checks(quick=False, full=False, include_cli=False):
    from utils.health_check_runner import run_health_checks
    return run_health_checks(quick=quick, full=full, include_cli=include_cli)


@app.route('/api/health-check/run', methods=['GET', 'POST'])
@localhost_required
def api_health_check_run():
    global _health_check_last
    data = request.get_json(silent=True) or {}
    quick = data.get('quick', request.args.get('quick', '0') in ('1', 'true', 'yes'))
    full = data.get('full', request.args.get('full', '0') in ('1', 'true', 'yes'))
    include_cli = data.get('include_cli', request.args.get('include_cli', '0') in ('1', 'true', 'yes'))
    if not quick and not full and not include_cli:
        quick = True
    result = _run_health_checks(quick=quick, full=full, include_cli=include_cli)
    _health_check_last = result
    return jsonify(result)


# ============================================================================
# INTERFACE MANAGER (v7.0.10)
# ============================================================================

def _im_resolve_or_error(data):
    from utils.job_source import JobSourceError, resolve_im_target
    try:
        return resolve_im_target(data), None
    except JobSourceError as exc:
        return None, (jsonify({"error": str(exc)}), 400)


def _im_begin_task(action, resolved):
    from utils.task_control_plane import bind_task, complete_task, is_cancelled, register_task
    tid = register_task(
        f'interface_{action}',
        label=f'interface_{action} {resolved["host"]}',
        meta={
            'inventory_source': resolved['target_source'],
            'device_count': 1,
        },
    )
    bind_task(tid)
    if is_cancelled(tid):
        complete_task(tid, 'cancelled')
        return tid, True
    add_log(
        f"[Interface Manager] {action} source={resolved['target_source']} "
        f"host={resolved['host']} devices=1"
    )
    return tid, False


def _im_finish_task(tid, ok, err=None):
    from utils.task_control_plane import complete_task, is_cancelled
    if is_cancelled(tid):
        complete_task(tid, 'cancelled')
        return
    if ok:
        complete_task(tid, 'complete')
    else:
        complete_task(tid, 'error', (err or 'failed')[:200])


@app.route('/api/interface/discover', methods=['POST'])
@localhost_required
def api_interface_discover():
    """
    Discover interfaces on a device.
    Body JSON: { host, username, password, enable_pwd, device_type, interface_filter }
    Returns: { status, data: { interfaces, interface_count, ... } }
    """
    data, err = _require_json_body()
    if err:
        return err
    cred_err = _overlay_request_secrets(data)
    if cred_err:
        return cred_err
    resolved, src_err = _im_resolve_or_error(data)
    if src_err:
        return src_err
    host = resolved['host']
    username = data.get('username')
    password = data.get('password')
    enable_pwd = data.get('enable_pwd')
    device_type = resolved['device_type']
    interface_filter = data.get('interface_filter', '')

    if not username or not password:
        return jsonify({"error": "Credentials required"}), 400

    tid, cancelled = _im_begin_task('discover', resolved)
    if cancelled:
        return jsonify({"error": "Task cancelled", "task_id": tid, "target_source": resolved['target_source']}), 409

    def _log(line):
        add_log(line)

    try:
        from modules.plugins.interface_manager import METADATA, run
        device = {"host": host, "device_type": device_type}
        credentials = {
            "username": username,
            "password": password,
            "secret": enable_pwd,
            "fallback_credentials": data.get('fallback_credentials') or [],
        }
        if data.get('secondary_credential'):
            credentials['secondary_credential'] = data['secondary_credential']
        if data.get('third_credential'):
            credentials['third_credential'] = data['third_credential']
        params = {
            "operation": "discover",
            "interface_filter": interface_filter,
            "dry_run": False
        }
        config = {"timeout": 30, "max_retries": 3, "log_level": "INFO"}
        
        result = run(device, credentials, params, config, log_func=_log)
        
        if result.get("status") == "fail":
            msg = result.get("message", "Discovery failed")
            _im_finish_task(tid, False, msg)
            return jsonify({"error": msg, "task_id": tid, "target_source": resolved['target_source']}), 500

        _im_finish_task(tid, True)
        return jsonify({
            "status": "success",
            "plugin": METADATA['plugin_id'],
            "data": result.get("data", {}),
            "task_id": tid,
            "target_source": resolved['target_source'],
            "host": host,
            "device_count": 1,
        })
    except Exception as exc:
        add_log("[Interface Manager] Discovery failed")
        _im_finish_task(tid, False, str(exc))
        _log_exception_off_console()
        return jsonify({"error": str(exc), "task_id": tid, "target_source": resolved['target_source']}), 500


@app.route('/api/interface/validate', methods=['POST'])
@localhost_required
def api_interface_validate():
    """
    Validate proposed interface configuration.
    Body JSON: { host, username, password, enable_pwd, device_type, interface_filter, proposed_config }
    Returns: { status, data: { validation_results, overall_status, risk_level, ... } }
    """
    data, err = _require_json_body()
    if err:
        return err
    # Surface missing proposed_config before vault resolve (clearer operator error).
    proposed_config = data.get('proposed_config', '')
    if not proposed_config:
        return jsonify({"error": "Proposed configuration is required"}), 400
    cred_err = _overlay_request_secrets(data)
    if cred_err:
        return cred_err
    resolved, src_err = _im_resolve_or_error(data)
    if src_err:
        return src_err
    host = resolved['host']
    username = data.get('username')
    password = data.get('password')
    enable_pwd = data.get('enable_pwd')
    device_type = resolved['device_type']
    interface_filter = data.get('interface_filter', '')

    if not username or not password:
        return jsonify({"error": "Credentials required"}), 400

    tid, cancelled = _im_begin_task('validate', resolved)
    if cancelled:
        return jsonify({"error": "Task cancelled", "task_id": tid, "target_source": resolved['target_source']}), 409

    def _log(line):
        add_log(line)

    try:
        from modules.plugins.interface_manager import METADATA, run
        device = {"host": host, "device_type": device_type}
        credentials = _credentials_dict_from_request(data)
        params = {
            "operation": "validate",
            "interface_filter": interface_filter,
            "proposed_config": proposed_config,
            "dry_run": True
        }
        config = {"timeout": 30, "max_retries": 3, "log_level": "INFO"}
        
        result = run(device, credentials, params, config, log_func=_log)
        
        if result.get("status") == "fail":
            msg = result.get("message", "Validation failed")
            _im_finish_task(tid, False, msg)
            return jsonify({"error": msg, "task_id": tid, "target_source": resolved['target_source']}), 500

        _im_finish_task(tid, True)
        return jsonify({
            "status": "success",
            "plugin": METADATA['plugin_id'],
            "data": result.get("data", {}),
            "task_id": tid,
            "target_source": resolved['target_source'],
            "host": host,
            "device_count": 1,
        })
    except Exception as exc:
        add_log("[Interface Manager] Validation failed")
        _im_finish_task(tid, False, str(exc))
        _log_exception_off_console()
        return jsonify({"error": str(exc), "task_id": tid, "target_source": resolved['target_source']}), 500


@app.route('/api/interface/deploy', methods=['POST'])
@localhost_required
def api_interface_deploy():
    """
    Deploy interface configuration to a device.
    Body JSON: { host, username, password, enable_pwd, device_type, interface_filter, proposed_config, dry_run }
    Returns: { status, data: { deployment_results, rollback_available, ... } }
    """
    data, err = _require_json_body()
    if err:
        return err
    cred_err = _overlay_request_secrets(data)
    if cred_err:
        return cred_err
    resolved, src_err = _im_resolve_or_error(data)
    if src_err:
        return src_err
    host = resolved['host']
    username = data.get('username')
    password = data.get('password')
    enable_pwd = data.get('enable_pwd')
    device_type = resolved['device_type']
    interface_filter = data.get('interface_filter', '')
    proposed_config = data.get('proposed_config', '')
    dry_run = data.get('dry_run', True)

    if not username or not password:
        return jsonify({"error": "Credentials required"}), 400
    if not proposed_config:
        return jsonify({"error": "Proposed configuration is required"}), 400

    if not dry_run:
        from utils.golden_config_gate import evaluate_interface_change, raise_if_blocked
        gstep = evaluate_interface_change(proposed_config)
        try:
            raise_if_blocked(gstep)
        except RuntimeError as exc:
            add_log("[Interface Manager] Golden-config blocked deploy")
            return jsonify({"error": str(exc), "golden_config": gstep, "target_source": resolved['target_source']}), 403

    tid, cancelled = _im_begin_task('deploy', resolved)
    if cancelled:
        return jsonify({"error": "Task cancelled", "task_id": tid, "target_source": resolved['target_source']}), 409

    def _log(line):
        add_log(line)

    try:
        from modules.plugins.interface_manager import METADATA, run
        device = {"host": host, "device_type": device_type}
        credentials = _credentials_dict_from_request(data)
        params = {
            "operation": "deploy",
            "interface_filter": interface_filter,
            "proposed_config": proposed_config,
            "dry_run": dry_run
        }
        config = {"timeout": 30, "max_retries": 3, "log_level": "INFO"}
        
        result = run(device, credentials, params, config, log_func=_log)
        
        if result.get("status") == "fail":
            msg = result.get("message", "Deployment failed")
            _im_finish_task(tid, False, msg)
            return jsonify({"error": msg, "task_id": tid, "target_source": resolved['target_source']}), 500

        _im_finish_task(tid, True)
        return jsonify({
            "status": "success",
            "plugin": METADATA['plugin_id'],
            "data": result.get("data", {}),
            "task_id": tid,
            "target_source": resolved['target_source'],
            "host": host,
            "device_count": 1,
        })
    except Exception as exc:
        add_log("[Interface Manager] Deployment failed")
        _im_finish_task(tid, False, str(exc))
        _log_exception_off_console()
        return jsonify({"error": str(exc), "task_id": tid, "target_source": resolved['target_source']}), 500


@app.route('/api/interface/open-report')
def api_interface_open_report():
    """Serve IM HTML report from validated output path."""
    from flask import send_file as _send, request as _req
    from utils.job_index import is_safe_outputs_file
    rel = (_req.args.get('path') or '').strip()
    if not rel:
        return jsonify({'error': 'path query required'}), 400
    full = is_safe_outputs_file(rel, require_html=True)
    if not full:
        return jsonify({'error': 'Report file not found or outside outputs'}), 404
    return _send(full, mimetype='text/html')


@app.route('/api/interface/restore-guide', methods=['POST'])
@localhost_required
def api_interface_restore_guide():
    """Return manual restore steps for a pre-change backup (no automated restore)."""
    data, err = _require_json_body()
    if err:
        return err
    backup_path = data.get('backup_path', '')
    device_type = data.get('device_type', 'cisco_ios')
    if not backup_path:
        return jsonify({"error": "backup_path is required"}), 400
    from utils.restore_guide import get_manual_restore_guide
    guide = get_manual_restore_guide(
        backup_path, device_type, context='interface configuration',
    )
    add_log(f"[Interface Manager] Manual restore guide requested for {backup_path}")
    return jsonify({"status": "success", "restore_guide": guide})


# CREDENTIAL MANAGEMENT API (v7.0.18)
# ============================================================================

def _session_cred_api_guard():
    """Localhost-only session credential cache (no vault unlock required)."""
    return _require_localhost_operator()


@app.route('/api/session/credentials', methods=['GET', 'POST'])
def api_session_credentials():
    """In-memory sidebar credentials for browser reload (cleared on process shutdown only)."""
    denied, code = _session_cred_api_guard()
    if denied:
        return denied, code
    from utils.session_cred_cache import set_session_credentials
    if request.method == 'GET':
        from utils.session_cred_cache import public_session_view
        return jsonify(public_session_view())
    data = request.get_json(silent=True) or {}
    set_session_credentials(
        username=(data.get('username') or '').strip(),
        password=data.get('password') or '',
        enable_password=data.get('enable_password') or data.get('enable_pwd') or '',
        become_password=data.get('become_password') or '',
        label=(data.get('label') or '').strip(),
        credential_id=(data.get('credential_id') or '').strip(),
        secondary_credential_id=(data.get('secondary_credential_id') or '').strip(),
        secondary_label=(data.get('secondary_label') or '').strip(),
        third_credential_id=(data.get('third_credential_id') or '').strip(),
        third_label=(data.get('third_label') or '').strip(),
        snmp_credential_id=(data.get('snmp_credential_id') or '').strip(),
        snmp_label=(data.get('snmp_label') or '').strip(),
    )
    return jsonify({'ok': True})


def _credential_api_guard(require_unlock=True):
    """Localhost-only; optionally require unlocked vault."""
    from utils.api_security import require_credential_vault_unlocked, require_local_credential_access
    denied, code = require_local_credential_access()
    if denied:
        return denied, code
    if require_unlock and credential_manager:
        denied, code = require_credential_vault_unlocked(credential_manager)
        if denied:
            return denied, code
    if not credential_manager:
        from flask import jsonify
        return jsonify({"error": "Credential manager not available"}), 500
    return None, None


@app.route('/api/credentials/list', methods=['GET'])
def api_credentials_list():
    """List stored credentials as metadata only. Loopback is not identity."""
    from utils.api_security import audit_credential_access
    from utils.vault_credentials import mapping_has_secret_fields, public_credential_view
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'LIST')
        credentials = []
        for row in credential_manager.list_credentials():
            view = public_credential_view(row, row.get('username') or '')
            if view:
                credentials.append(view)
        payload = {
            "credentials": credentials,
            "count": len(credentials)
        }
        if mapping_has_secret_fields(payload):
            add_log('[Credential Manager] List refused: sanitizer detected secret field')
            return jsonify({"error": "Credential list unavailable"}), 500
        return jsonify(payload)
    except Exception:
        add_log("[Credential Manager] List failed")
        return jsonify({"error": "Credential list failed"}), 500


@app.route('/api/credentials/add', methods=['POST'])
def api_credentials_add():
    """Add a new credential set."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'ADD')
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        password = data.get('password')
        admin_password = data.get('admin_password')
        become_password = data.get('become_password')
        label = data.get('label')
        force = data.get('force', False)
        snmp_version = data.get('snmp_version')
        snmp_community = data.get('snmp_community')
        snmp_port = data.get('snmp_port')
        snmp_v3_user = data.get('snmp_v3_user')
        snmp_v3_auth_protocol = data.get('snmp_v3_auth_protocol')
        snmp_v3_auth_key = data.get('snmp_v3_auth_key')
        snmp_v3_priv_protocol = data.get('snmp_v3_priv_protocol')
        snmp_v3_priv_key = data.get('snmp_v3_priv_key')
        profile_type = data.get('profile_type')
        
        success, message = credential_manager.add_credential(
            username=username,
            password=password,
            admin_password=admin_password,
            become_password=become_password,
            label=label,
            force=force,
            snmp_version=snmp_version,
            snmp_community=snmp_community,
            snmp_port=snmp_port,
            snmp_v3_user=snmp_v3_user,
            snmp_v3_auth_protocol=snmp_v3_auth_protocol,
            snmp_v3_auth_key=snmp_v3_auth_key,
            snmp_v3_priv_protocol=snmp_v3_priv_protocol,
            snmp_v3_priv_key=snmp_v3_priv_key,
            profile_type=profile_type,
        )
        
        if success:
            add_log(f"[Credential Manager] Added credential for '{username}'")
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as exc:
        add_log(f"[Credential Manager] Add failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/get/<username>', methods=['GET'])
def api_credentials_get(username):
    """Metadata-only credential view for Use/Edit.

    Secrets stay in the vault and are resolved server-side on execute.
    Loopback is not identity; this route must never serialize password,
    private key, token, or the decrypted vault object.
    """
    from utils.api_security import audit_credential_access
    from utils.vault_credentials import mapping_has_secret_fields, public_credential_view
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'GET', username)
        credential = credential_manager.get_credential(username)
        if not credential:
            return jsonify({"error": "Credential not found"}), 404
        payload = public_credential_view(credential, username)
        if not payload or mapping_has_secret_fields(payload):
            add_log('[Credential Manager] Get refused: sanitizer detected secret field')
            return jsonify({"error": "Credential metadata unavailable"}), 500
        return jsonify({"credential": payload})
    except Exception:
        add_log("[Credential Manager] Get failed")
        return jsonify({"error": "Credential lookup failed"}), 500


@app.route('/api/credentials/update', methods=['POST'])
def api_credentials_update():
    """Update an existing credential."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'UPDATE', (request.get_json(silent=True) or {}).get('username', ''))
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        password = data.get('password')
        admin_password = data.get('admin_password')
        become_password = data.get('become_password')
        label = data.get('label')
        snmp_version = data.get('snmp_version')
        snmp_community = data.get('snmp_community')
        snmp_port = data.get('snmp_port')
        snmp_v3_user = data.get('snmp_v3_user')
        snmp_v3_auth_protocol = data.get('snmp_v3_auth_protocol')
        snmp_v3_auth_key = data.get('snmp_v3_auth_key')
        snmp_v3_priv_protocol = data.get('snmp_v3_priv_protocol')
        snmp_v3_priv_key = data.get('snmp_v3_priv_key')
        clear_snmp = bool(data.get('clear_snmp'))
        profile_type = data.get('profile_type')
        
        success, message = credential_manager.update_credential(
            username=username,
            password=password,
            admin_password=admin_password,
            become_password=become_password,
            label=label,
            snmp_version=snmp_version,
            snmp_community=snmp_community,
            snmp_port=snmp_port,
            snmp_v3_user=snmp_v3_user,
            snmp_v3_auth_protocol=snmp_v3_auth_protocol,
            snmp_v3_auth_key=snmp_v3_auth_key,
            snmp_v3_priv_protocol=snmp_v3_priv_protocol,
            snmp_v3_priv_key=snmp_v3_priv_key,
            clear_snmp=clear_snmp,
            profile_type=profile_type,
        )
        
        if success:
            add_log(f"[Credential Manager] Updated credential for '{username}'")
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as exc:
        add_log(f"[Credential Manager] Update failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/remove/<username>', methods=['DELETE'])
def api_credentials_remove(username):
    """Remove a credential."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'REMOVE', username)
        success, message = credential_manager.remove_credential(username)
        if success:
            add_log(f"[Credential Manager] Removed credential for '{username}'")
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as exc:
        add_log(f"[Credential Manager] Remove failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/export-file', methods=['POST'])
def api_credentials_export_file():
    """Export credentials to an encrypted file and return as download."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'EXPORT_FILE')
        data = request.get_json(silent=True) or {}
        password = data.get('password')
        
        if not password:
            return jsonify({"error": "Export password required"}), 400
        
        # Generate a temporary file path
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), f'credentials_export_{int(time.time())}.enc')
        
        success, message = credential_manager.export_credentials(temp_path, password)
        if success:
            from flask import send_file as _send
            try:
                return _send(temp_path, as_attachment=True, download_name=f'credentials_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.enc', mimetype='application/octet-stream')
            finally:
                # Clean up temp file after sending
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as exc:
        add_log(f"[Credential Manager] Export file failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/import-file', methods=['POST'])
def api_credentials_import_file():
    """Import credentials from an uploaded encrypted file."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'IMPORT_FILE')
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        password = request.form.get('password')
        merge = request.form.get('merge', 'true').lower() == 'true'
        
        if not password:
            return jsonify({"error": "Import password required"}), 400
        
        # Save uploaded file to temp location
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), f'credentials_import_{int(time.time())}.enc')
        file.save(temp_path)
        
        try:
            success, message = credential_manager.import_credentials(temp_path, password, merge)
            if success:
                add_log(f"[Credential Manager] Imported credentials from uploaded file")
                return jsonify({"success": True, "message": message})
            else:
                return jsonify({"success": False, "message": message}), 400
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
    except Exception as exc:
        add_log(f"[Credential Manager] Import file failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/master-password/status', methods=['GET'])
def api_credentials_master_password_status():
    """Vault readiness — daily use does not require a master password."""
    if not credential_manager:
        return jsonify({"error": "Credential manager not available"}), 500
    
    try:
        is_required = credential_manager.is_master_password_required()
        is_set = os.path.exists(credential_manager.master_password_file)
        ready = credential_manager.fernet is not None and not is_required
        return jsonify({
            "is_required": is_required,
            "is_set": is_set,
            "ready": ready,
            "unlocked": ready,
            "locked": is_required,
            "enabled": is_set or is_required,
            "has_master_password": is_set,
            "configured": is_set,
            "mode": "machine_key" if ready else ("legacy_locked" if is_required else "unavailable"),
            "message": (
                "Credentials ready — local machine key (no master password needed)"
                if ready else
                ("Legacy vault locked — unlock once to migrate to machine key"
                 if is_required else "Credential vault unavailable")
            ),
        })
    except Exception as exc:
        add_log(f"[Credential Manager] Master password status check failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/master-password/set', methods=['POST'])
def api_credentials_set_master_password():
    """Retired: master password is not required for credential use."""
    if not credential_manager:
        return jsonify({"error": "Credential manager not available"}), 500
    return jsonify({
        "success": False,
        "error": (
            "Master password is no longer required. Credentials stay available via the "
            "local machine key. Use Export with a password for portable encrypted backups."
        ),
    }), 400


@app.route('/api/credentials/master-password/unlock', methods=['POST'])
def api_credentials_unlock_master_password():
    """One-time unlock for legacy master-password vaults; migrates to machine key."""
    if not credential_manager:
        return jsonify({"error": "Credential manager not available"}), 500
    
    try:
        data = request.get_json(silent=True) or {}
        password = data.get('password')
        
        if not password:
            return jsonify({"error": "Password required"}), 400
        
        success = credential_manager.unlock_with_master_password(password)
        if success:
            add_log("[Credential Manager] Legacy vault unlocked and migrated to machine key")
            return jsonify({
                "success": True,
                "message": "Unlocked — vault migrated to local machine key (no further unlock needed)",
                "migrated": True,
            })
        else:
            return jsonify({"success": False, "message": "Incorrect password"}), 400
    except Exception as exc:
        add_log(f"[Credential Manager] Unlock failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/master-password/clear', methods=['POST'])
def api_credentials_clear_master_password():
    """Clear master-password gate when vault is already open."""
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    try:
        ok, msg = credential_manager.clear_master_password_gate(reencrypt=True)
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        add_log("[Credential Manager] Master password gate cleared")
        return jsonify({"success": True, "message": msg})
    except Exception as exc:
        add_log(f"[Credential Manager] Clear master password failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/credentials/export', methods=['POST'])
def api_credentials_export():
    """Export credentials to an encrypted file."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'EXPORT')
        data = request.get_json(silent=True) or {}
        from utils.output_paths import get_credentials_exports_dir
        default_name = f"credentials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
        raw_path = data.get('export_path') or default_name
        # Force exports under credentials exports dir only (no absolute client paths)
        base = os.path.basename(str(raw_path).replace('\\', '/')) or default_name
        if not base.endswith('.enc'):
            base = default_name
        export_dir = os.path.realpath(get_credentials_exports_dir())
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.realpath(os.path.join(export_dir, base))
        if os.path.commonpath([export_dir, export_path]) != export_dir:
            return jsonify({"error": "Invalid export path"}), 400
        password = data.get('password')
        
        if not password:
            return jsonify({"error": "Export password required"}), 400
        
        success, message = credential_manager.export_credentials(export_path, password)
        if success:
            rel_out = os.path.relpath(export_path, export_dir).replace('\\', '/')
            add_log(f"[Credential Manager] Exported credentials to exports/{rel_out}")
            return jsonify({"success": True, "message": message, "path": rel_out})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as exc:
        add_log(f"[Credential Manager] Export failed: {exc}")
        return jsonify({"error": "Credential export failed"}), 500


@app.route('/api/credentials/import', methods=['POST'])
def api_credentials_import():
    """Import credentials from an encrypted file."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'IMPORT')
        data = request.get_json(silent=True) or {}
        import_path = data.get('import_path')
        password = data.get('password')
        merge = data.get('merge', True)
        
        if not import_path or not password:
            return jsonify({"error": "Import path and password required"}), 400

        from utils.output_paths import get_credentials_exports_dir
        export_dir = os.path.realpath(get_credentials_exports_dir())
        raw = str(import_path).strip()
        # Only basename under exports dir (reject absolute / traversal)
        candidate = os.path.realpath(os.path.join(export_dir, os.path.basename(raw.replace('\\', '/'))))
        if os.path.commonpath([export_dir, candidate]) != export_dir:
            return jsonify({"error": "Import path must be under credentials exports directory"}), 400
        if not os.path.isfile(candidate):
            return jsonify({"error": "Import file not found in exports directory"}), 404
        
        success, message = credential_manager.import_credentials(candidate, password, merge)
        if success:
            add_log("[Credential Manager] Imported credentials from exports directory")
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as exc:
        add_log(f"[Credential Manager] Import failed: {exc}")
        return jsonify({"error": "Credential import failed"}), 500


@app.route('/api/credentials/clear', methods=['POST'])
def api_credentials_clear():
    """Clear all credentials."""
    from utils.api_security import audit_credential_access
    denied, code = _credential_api_guard(require_unlock=True)
    if denied:
        return denied, code
    
    try:
        audit_credential_access(add_log, 'CLEAR')
        success, message = credential_manager.clear_all_credentials()
        if success:
            add_log("[Credential Manager] Cleared all credentials")
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as exc:
        add_log(f"[Credential Manager] Clear failed: {exc}")
        return jsonify({"error": "Credential operation failed"}), 500


@app.route('/api/health-check/status')
def api_health_check_status():
    if _health_check_last:
        return jsonify(_health_check_last)
    return jsonify({'ok': None, 'checks': [], 'ran_at': None})


@app.route('/api/health-check/demo-map/<which>')
def api_health_check_demo_map(which):
    from flask import send_file as _send
    which = (which or '').lower()
    if which == 'discovery':
        try:
            from modules.plugins.network_discovery import NetworkDiscoveryPlugin
            plugin = NetworkDiscoveryPlugin()
            device = {'host': '127.0.0.1', 'device_type': 'cisco_nxos', 'port': 22}
            result = plugin.execute(
                device, {'username': 'd', 'password': 'd'},
                {'seed_hosts': ['10.0.0.1'], 'demo_mode': True, 'generate_topology_html': True},
                {}, log_func=None,
            )
            path = ((result or {}).get('data') or {}).get('topology_path')
            if path and os.path.isfile(path):
                return _send(path, mimetype='text/html')
        except Exception:
            pass
        return jsonify({'error': 'Discovery demo map not available'}), 404
    if which in ('vpc', 'v7'):
        from utils.output_paths import get_demo_vpc_topology_path
        path = get_demo_vpc_topology_path()
        if not os.path.isfile(path):
            try:
                import create_demo_map_v7
                create_demo_map_v7.create_v7_demo()
            except Exception:
                pass
        if os.path.isfile(path):
            return _send(path, mimetype='text/html')
        return jsonify({'error': 'vPC demo map not found'}), 404
    return jsonify({'error': 'Unknown demo type'}), 400


@app.route('/api/mac-trace/last')
def api_mac_trace_last():
    if not _mac_trace_last:
        return jsonify({'status': 'idle', 'empty': True, 'message': 'No MAC trace run yet'})
    return jsonify(_mac_trace_last)


@app.route('/api/mac-trace/report')
def api_mac_trace_report():
    from flask import send_file as _send
    path = (_mac_trace_last or {}).get('html_path')
    if path and os.path.isfile(path):
        return _send(path, mimetype='text/html')
    return jsonify({'error': 'No MAC path report available'}), 404


@app.route('/api/description-search/last')
def api_description_search_last():
    if not _description_search_last:
        return jsonify({'status': 'idle', 'empty': True, 'message': 'No description search run yet'})
    return jsonify(_description_search_last)


@app.route('/api/description-search/report')
def api_description_search_report():
    from flask import send_file as _send
    path = (_description_search_last or {}).get('html_path')
    if path and os.path.isfile(path):
        return _send(path, mimetype='text/html')
    return jsonify({'error': 'No description search report available'}), 404


@app.route('/api/ping-scan/last')
@localhost_required
def api_ping_scan_last():
    if not _ping_scan_last:
        return jsonify({'status': 'idle', 'empty': True, 'message': 'No ping scan run yet'})
    payload = dict(_ping_scan_last)
    payload.pop('html_path', None)
    payload.pop('txt_path', None)
    rel = None
    try:
        from utils.job_index import contained_run_dir
        rel = contained_run_dir(payload.get('run_dir'))
    except Exception:
        rel = None
    payload['run_dir'] = rel
    payload['artifacts_available'] = bool(rel)
    return jsonify(payload)


@app.route('/api/ping-scan/report')
@localhost_required
def api_ping_scan_report():
    from flask import send_file as _send
    path = (_ping_scan_last or {}).get('html_path')
    if path and os.path.isfile(path):
        return _send(path, mimetype='text/html')
    return jsonify({'error': 'No ping scan report available'}), 404


@app.route('/api/search-it/progress')
def api_search_it_progress():
    from utils.search_it_progress import get_all_progress
    return jsonify(get_all_progress())


# ============================================================================
# STP SWISS TOOLS API (v7.0.0)
# ============================================================================

@app.route('/api/stp/run', methods=['POST'])
@localhost_required
def api_stp_run():
    data, err = _require_json_body()
    if err:
        return err
    demo_mode = bool(data.get('demo_mode', False))
    if not demo_mode:
        cred_err = _overlay_request_secrets(data)
        if cred_err:
            return cred_err
    try:
        vlan_id = _parse_bounded_int(data.get('vlan_id', 0), 0, 'vlan_id', min_val=0, max_val=4094)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    username = data.get('username', '')
    password = data.get('password', '')
    enable_pwd = data.get('enable_pwd', '')

    from modules.inventory_store import InventoryError
    from utils.job_source import resolve_stp_targets
    try:
        resolved = resolve_stp_targets(data)
    except InventoryError as exc:
        return _inventory_error_response(exc)

    devices = resolved['devices']
    if not demo_mode and (not devices or not username or not password):
        return jsonify({'error': 'devices/inventory and credentials required (or demo_mode)'}), 400

    _prune_stp_jobs()
    from utils.task_control_plane import register_task
    job_id = register_task(
        'stp',
        label=f'stp source={resolved["target_source"]} devices={resolved["device_count"]}',
        meta={
            'inventory_source': resolved['target_source'],
            'device_count': resolved['device_count'],
            'target_source': resolved['target_source'],
        },
    )
    with _job_store_lock:
        _stp_jobs[job_id] = {
            'status': 'running', 'result': None, 'error': None,
            'started_at': datetime.now().isoformat(),
            'target_source': resolved['target_source'],
            'device_count': resolved['device_count'],
        }

    def _run():
        from utils.task_control_plane import bind_task, complete_task, is_cancelled
        bind_task(job_id)
        try:
            if is_cancelled(job_id):
                with _job_store_lock:
                    _stp_jobs[job_id]['status'] = 'cancelled'
                complete_task(job_id, 'cancelled')
                return
            from modules.stp_swiss_runner import run_stp_inventory_scan
            from utils.stp_map_formatter import generate_stp_html
            credentials = _credentials_dict_from_request(data)
            result = run_stp_inventory_scan(devices, credentials, vlan_id, add_log, demo_mode=demo_mode)
            if is_cancelled(job_id):
                with _job_store_lock:
                    _stp_jobs[job_id]['status'] = 'cancelled'
                    _stp_jobs[job_id]['result'] = result
                complete_task(job_id, 'cancelled')
                return
            with _job_store_lock:
                if result.get('status') != 'success' and not result.get('nodes'):
                    _stp_jobs[job_id]['status'] = 'error'
                    _stp_jobs[job_id]['error'] = 'No STP data collected'
                    _stp_jobs[job_id]['result'] = result
                    complete_task(job_id, 'error', 'No STP data collected')
                    return
            from utils.output_paths import CAT_STP_TOPOLOGY, path_in_run, prepare_run_output, slugify, write_run_manifest
            stp_paths = prepare_run_output(CAT_STP_TOPOLOGY, slugify(f'vlan{vlan_id}_{job_id}'))
            html_path = path_in_run(stp_paths, 'stp_topology.html')
            generate_stp_html(
                html_path,
                result.get('nodes', []),
                result.get('edges', []),
                result.get('link_rows'),
                vlan_id=vlan_id,
                demo_mode=demo_mode or result.get('demo'),
            )
            txt_path = path_in_run(stp_paths, 'report.txt')
            try:
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    tf.write(
                        f"STP Topology Scan — VLAN {vlan_id}\n"
                        f"Source: {resolved['target_source']}\n"
                        f"Targets: {resolved['device_count']}\n"
                        f"Nodes: {len(result.get('nodes', []))}\n"
                        f"Edges: {len(result.get('edges', []))}\n"
                        f"HTML: {html_path}\n"
                    )
            except OSError:
                txt_path = ''
            write_run_manifest(stp_paths, {
                'html_path': html_path,
                'txt_path': txt_path or None,
                'job_id': job_id,
                'vlan_id': vlan_id,
                'target_source': resolved['target_source'],
                'device_count': resolved['device_count'],
            })
            result['html_path'] = html_path
            result['output_folder'] = stp_paths['run_dir']
            result['target_source'] = resolved['target_source']
            result['device_count'] = resolved['device_count']
            result['artifacts_available'] = True
            with _job_store_lock:
                _stp_jobs[job_id]['status'] = 'complete'
                _stp_jobs[job_id]['result'] = result
            complete_task(job_id, 'complete')
            add_log(f'[STP] Job {job_id} complete source={resolved["target_source"]} — {html_path}')
            add_log(f'[STP] Output folder: {stp_paths["run_dir"]}')
        except Exception as exc:
            with _job_store_lock:
                _stp_jobs[job_id]['status'] = 'error'
                _stp_jobs[job_id]['error'] = str(exc)
            complete_task(job_id, 'error', str(exc))
            add_log(f'[STP] Job {job_id} failed: {exc}')
            _log_exception_off_console()

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({
        'job_id': job_id,
        'task_id': job_id,
        'status': 'started',
        'target_source': resolved['target_source'],
        'device_count': resolved['device_count'],
        'warning': resolved.get('warning'),
        'artifacts_expected': True,
    })


@app.route('/api/stp/status/<job_id>')
@localhost_required
def api_stp_status(job_id):
    with _job_store_lock:
        job = _stp_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    result = job.get('result') or {}
    public = _stp_public_result(result)
    art = {
        'run_dir': public.get('run_dir'),
        'artifacts_available': public.get('artifacts_available'),
        'run_dir_exists': public.get('run_dir_exists'),
    }
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'result': public,
        'error': job.get('error'),
        'target_source': job.get('target_source') or public.get('target_source'),
        'device_count': job.get('device_count') if job.get('device_count') is not None else public.get('device_count'),
        'artifacts_available': art['artifacts_available'],
        'run_dir': art['run_dir'],
        'run_dir_exists': art['run_dir_exists'],
    })


@app.route('/api/stp/report/<job_id>')
@localhost_required
def api_stp_report(job_id):
    from flask import send_file as _send
    with _job_store_lock:
        job = _stp_jobs.get(job_id)
    if not job or job.get('status') != 'complete':
        return jsonify({'error': 'Job not complete'}), 404
    path = (job.get('result') or {}).get('html_path')
    from utils.job_index import contained_run_dir
    if path and os.path.isfile(path) and contained_run_dir(path):
        return _send(path, mimetype='text/html')
    return jsonify({'error': 'Report not found'}), 404


@app.route('/api/topology/status')
def api_topology_status():
    """Poll last Standard / vPC map job from Swiss Tools.

    Includes real L2 edge count from 04_final_map_data.json so path-trace
    gating never treats html_path alone as evidence of reconstructable edges.
    """
    payload = dict(_last_topology or {})
    edges = _load_last_topology_edges()
    payload['edge_count'] = len(edges)
    payload['has_l2_edges'] = len(edges) > 0
    return jsonify(payload)


@app.route('/api/topology/edges-status')
@localhost_required
def api_topology_edges_status():
    """Explicit edge inventory for path-reconstruct gate (no invented links)."""
    edges = _load_last_topology_edges()
    return jsonify({
        'edge_count': len(edges),
        'has_l2_edges': len(edges) > 0,
        'status': (_last_topology or {}).get('status') or 'idle',
        'diag_folder': (_last_topology or {}).get('diag_folder') or '',
        'note': 'Edges loaded from last inventory L2 04_final_map_data.json only.',
    })


@app.route('/api/utilization-overlay/status')
@localhost_required
def api_utilization_overlay_status():
    """Poll last Standard L2 live SSH utilization job. No secrets, no CLI dumps."""
    payload = dict(_last_utilization_live or {"status": "idle"})
    payload.setdefault('mode', 'live')
    payload['note'] = (
        'Live SSH two-sample overlay on Inventory Standard L2 only. '
        'Not SNMP. Paint is not topology. Does not clear release_gate.'
    )
    return jsonify(payload)


@app.route('/api/topology/issues')
@localhost_required
def api_topology_issues():
    """Witness rows from last inventory L2 map. Not a cable certification."""
    issues = list(_last_topology.get('issues') or [])
    if not issues:
        issues = _load_link_issues(_last_topology.get('diag_folder'))
    return jsonify({
        'status': _last_topology.get('status') or 'idle',
        'note': 'Witnesses from last inventory L2 map (description/speed/duplex/DOM/LACP). Not a certified cable.',
        'issues': issues,
        'count': len(issues),
        'map_mode': _last_topology.get('map_mode'),
    })


@app.route('/api/path-trace', methods=['POST'])
@localhost_required
def api_path_trace():
    """Reconstruct a MAC path from last MAC hits + last L2 edges. Never invents hops."""
    data, err = _require_json_body()
    if err:
        return err
    target_mac = (data.get('mac') or data.get('target_mac') or '').strip()
    from modules.path_trace import reconstruct_path, collect_path_trace_from_mac_results

    hits = data.get('mac_hits') or data.get('hits')
    edges = data.get('edges')
    if edges is None:
        edges = _load_last_topology_edges()
    if hits is None:
        hits = []
        for hop in (_mac_trace_last.get('path_hops') or []):
            hits.append({
                'hostname': hop.get('hostname'),
                'port': hop.get('port'),
                'vlan': hop.get('vlan'),
                'found': bool(hop.get('found')),
                'command': 'show mac address-table',
                'evidence': f"{target_mac or _mac_trace_last.get('target_mac') or ''} on {hop.get('port')}"
                if hop.get('found') else 'not found',
            })
        if not target_mac:
            target_mac = (_mac_trace_last.get('target_mac') or '').strip()
    if data.get('mac_results'):
        path = collect_path_trace_from_mac_results(data.get('mac_results'), edges, target_mac)
    else:
        path = reconstruct_path(hits, edges, target_mac)
    path['source'] = 'reconstructed'
    return jsonify({'status': 'success', 'data': path})


def _load_last_topology_edges():
    diag = (_last_topology or {}).get('diag_folder') or ''
    f4 = os.path.join(diag, '04_final_map_data.json') if diag else ''
    if not f4 or not os.path.isfile(f4):
        return []
    try:
        payload = json.load(open(f4, encoding='utf-8'))
        out = []
        for e in payload.get('edges') or []:
            out.append(e.get('edge_data') or e)
        return out
    except Exception:
        return []


@app.route('/api/l3-map/status')
def api_l3_map_status():
    """Poll last L3 / Flow / Advanced L2 map job."""
    return jsonify(_last_l3_map)


@app.route('/api/l3-map/open')
def api_l3_map_open():
    """Serve the most recently generated L3/Flow/Advanced L2 HTML map."""
    from flask import send_file as _send
    from utils.job_index import is_safe_outputs_file
    if _last_l3_map.get('status') != 'complete':
        return jsonify({'error': 'No completed L3/Flow map'}), 404
    html_path = _last_l3_map.get('html_path')
    full = is_safe_outputs_file(html_path, require_html=True)
    if not full:
        return jsonify({'error': 'Map file missing or outside outputs'}), 404
    return _send(full, mimetype='text/html')


@app.route('/api/l3/trace-path', methods=['POST'])
def api_l3_trace_path():
    """Trace hop-by-hop packet forwarding path between Source IP and Destination IP.
    
    Zero-trust offline simulation using Longest Prefix Match (LPM) on collected routing tables.
    """
    data = request.get_json() or {}
    src_ip = (data.get('source_ip') or '').strip()
    dst_ip = (data.get('destination_ip') or '').strip()

    if not src_ip or not dst_ip:
        return jsonify({
            'status': 'error',
            'error': 'Both source_ip and destination_ip are required',
        }), 400

    all_routes = []
    devices_meta = {}
    subnet_analysis = {}
    gateway_analysis = {}

    html_path = _last_l3_map.get('html_path')
    if html_path and os.path.isfile(html_path):
        run_dir = os.path.dirname(html_path)
        routes_file = os.path.join(run_dir, 'l3_routes_normalized.json')
        gw_file = os.path.join(run_dir, 'l3_gateways.json')
        sn_file = os.path.join(run_dir, 'l3_subnets.json')

        if os.path.isfile(routes_file):
            try:
                with open(routes_file, 'r', encoding='utf-8') as f:
                    all_routes = json.load(f)
            except Exception:
                pass
        if os.path.isfile(gw_file):
            try:
                with open(gw_file, 'r', encoding='utf-8') as f:
                    gateway_analysis = json.load(f)
            except Exception:
                pass
        if os.path.isfile(sn_file):
            try:
                with open(sn_file, 'r', encoding='utf-8') as f:
                    subnet_analysis = json.load(f)
            except Exception:
                pass

    if data.get('all_routes'):
        all_routes = data.get('all_routes')
    if data.get('devices'):
        devices_meta = data.get('devices')

    from modules.routing_analyzer.path_tracer import L3PathTracer
    tracer = L3PathTracer(
        all_routes=all_routes,
        devices_meta=devices_meta,
        subnet_analysis=subnet_analysis,
        gateway_analysis=gateway_analysis,
    )

    result = tracer.trace_path(src_ip, dst_ip)
    if result.get('status') == 'error':
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/topology/open')
def api_topology_open():
    """Serve the most recently generated topology HTML (offline-safe if saved locally)."""
    from flask import send_file as _send
    from utils.job_index import is_safe_outputs_file
    if _last_topology.get('status') != 'complete':
        return jsonify({'error': 'No completed topology map'}), 404
    html_path = _last_topology.get('html_path')
    full = is_safe_outputs_file(html_path, require_html=True)
    if not full:
        return jsonify({'error': 'Map file missing or outside outputs'}), 404
    return _send(full, mimetype='text/html')


@app.route('/api/topology/open-diagnostics')
def api_topology_open_diagnostics():
    """Open diagnostics folder in OS file explorer (Windows)."""
    folder = _last_topology.get('diag_folder')
    if not folder or not os.path.isdir(folder):
        return jsonify({'error': 'Diagnostics folder not available'}), 404
    try:
        if sys.platform == 'win32':
            os.startfile(folder)  # noqa: S606
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder])
        return jsonify({'ok': True, 'folder': folder})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/topology/failed-hosts')
def api_topology_failed_hosts():
    """Return failed host list + diag paths for drill-down."""
    if _last_topology.get('status') != 'complete':
        return jsonify({'failed_hosts': [], 'error': 'No completed topology'}), 404
    diag = _last_topology.get('diag_folder') or ''
    fh_txt = os.path.join(diag, 'failed_hosts.txt') if diag else ''
    return jsonify({
        'failed_hosts': _last_topology.get('failed_hosts') or [],
        'failed_hosts_txt': fh_txt if fh_txt and os.path.isfile(fh_txt) else None,
        'diag_folder': diag or None,
    })


@app.route('/api/topology/export-bundle')
def api_topology_export_bundle():
    """ZIP export: HTML + JSON + manifest + failed_hosts (offline archive)."""
    import io
    import zipfile
    from flask import send_file
    if _last_topology.get('status') != 'complete':
        return jsonify({'error': 'No completed topology map'}), 404
    diag = _last_topology.get('diag_folder')
    html_path = _last_topology.get('html_path')
    if not diag or not os.path.isdir(diag):
        return jsonify({'error': 'Diagnostics folder missing'}), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name in (
            '00_README.txt', '04_final_map_data.json', '07_post_render_manifest.json',
            'failed_hosts.txt',
        ):
            fp = os.path.join(diag, name)
            if os.path.isfile(fp):
                zf.write(fp, arcname=name)
        if html_path and os.path.isfile(html_path):
            zf.write(html_path, arcname=os.path.basename(html_path))
    buf.seek(0)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        buf, mimetype='application/zip', as_attachment=True,
        download_name=f'topology_bundle_{ts}.zip',
    )


@app.route('/api/reachability/status')
@localhost_required
def api_reachability_status():
    payload = dict(_last_reachability_matrix or {'status': 'idle'})
    # Never leak absolute paths in idle/error summaries to remote; localhost OK
    return jsonify(payload)


@app.route('/api/reachability/open')
@localhost_required
def api_reachability_open():
    from flask import send_file as _send
    if (_last_reachability_matrix or {}).get('status') != 'complete':
        return jsonify({'error': 'No completed reachability matrix'}), 404
    html_path = (_last_reachability_matrix or {}).get('html_path')
    if not html_path or not os.path.isfile(html_path):
        return jsonify({'error': 'Matrix HTML missing'}), 404
    return _send(html_path, mimetype='text/html')


@app.route('/api/port-map/status')
def api_port_map_status():
    return jsonify(_last_port_map)


@app.route('/api/port-map/open')
def api_port_map_open():
    from flask import send_file as _send
    if _last_port_map.get('status') != 'complete':
        return jsonify({'error': 'No completed port map'}), 404
    html_path = _last_port_map.get('html_path')
    if not html_path or not os.path.isfile(html_path):
        return jsonify({'error': 'Map file missing'}), 404
    return _send(html_path, mimetype='text/html')


@app.route('/api/failure-correlation/status')
def api_failure_correlation_status():
    return jsonify(_last_failure_correlation)


@app.route('/api/failure-correlation/open')
def api_failure_correlation_open():
    from flask import send_file as _send
    if (_last_failure_correlation or {}).get('status') != 'complete':
        return jsonify({'error': 'No completed failure correlation report'}), 404
    html_path = (_last_failure_correlation or {}).get('html_path')
    if not html_path or not os.path.isfile(html_path):
        return jsonify({'error': 'Correlation HTML missing'}), 404
    return _send(html_path, mimetype='text/html')


@app.route('/api/node-analyze/status')
def api_node_analyze_status():
    return jsonify(_last_node_analyze)


# ============================================================================
# CONFIG TEMPLATES API  (v6.9.21)
# ============================================================================

@app.route('/api/templates/presets')
def api_templates_presets():
    """Preset catalog for template builder UI."""
    try:
        from modules.plugins.config_templates import get_template_presets
        return jsonify({"presets": get_template_presets()})
    except Exception as exc:
        return jsonify({"error": str(exc), "presets": []}), 200


@app.route('/api/templates/list')
def api_templates_list():
    """
    List all available config templates in the templates/ directory.
    Returns: { templates: [ { name, description, variables, path } ] }
    """
    try:
        from modules.plugins.config_templates import ConfigTemplatesPlugin
        plugin = ConfigTemplatesPlugin()

        if getattr(sys, 'frozen', False):
            program_dir = os.path.dirname(sys.executable)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(program_dir, 'templates')

        templates = plugin.list_templates(templates_dir)
        return jsonify({"templates": templates, "templates_dir": templates_dir})
    except Exception as exc:
        return jsonify({"error": str(exc), "templates": []}), 200


@app.route('/api/templates/save', methods=['POST'])
@localhost_required
def api_templates_save():
    """
    Save / overwrite a template file.
    Body JSON: { name, content, description }
    Returns: { success, path }
    """
    data, err = _require_json_body()
    if err:
        return err
    name    = data.get('name', '').strip()
    content = data.get('content', '')

    if not name:
        return jsonify({"success": False, "error": "Template name required"}), 400
    if not name.endswith('.j2') and not name.endswith('.txt'):
        name = name + '.j2'

    try:
        if getattr(sys, 'frozen', False):
            program_dir = os.path.dirname(sys.executable)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(program_dir, 'templates')
        os.makedirs(templates_dir, exist_ok=True)

        safe_name = secure_filename(name)
        save_path = os.path.join(templates_dir, safe_name)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(content)

        add_log(f"[Templates] Saved template: {safe_name}")
        return jsonify({"success": True, "path": save_path, "name": safe_name})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route('/api/templates/render', methods=['POST'])
@localhost_required
def api_templates_render():
    """
    Render a template with supplied variables.
    Body JSON: { template_name, variables: { key: value, ... } }
    Returns: { success, output, variables_used }
    """
    data, err = _require_json_body()
    if err:
        return err
    template_name = data.get('template_name', '')
    variables     = data.get('variables', {})

    if not template_name:
        return jsonify({"success": False, "error": "template_name required"}), 400

    try:
        from modules.plugins.config_templates import ConfigTemplatesPlugin
        plugin = ConfigTemplatesPlugin()

        if getattr(sys, 'frozen', False):
            program_dir = os.path.dirname(sys.executable)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(program_dir, 'templates')

        # Load template content
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            return jsonify({"success": False, "error": f"Template not found: {template_name}"}), 404

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Render via plugin engine
        output, vars_used = plugin.render_template(template_content, variables)
        add_log(f"[Templates] Rendered '{template_name}' with {len(variables)} variables")
        return jsonify({
            "success":        True,
            "output":         output,
            "variables_used": vars_used,
            "template_name":  template_name,
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route('/api/templates/get/<template_name>')
def api_templates_get(template_name):
    """Return raw content of a specific template file."""
    try:
        if getattr(sys, 'frozen', False):
            program_dir = os.path.dirname(sys.executable)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(program_dir, 'templates')

        safe = secure_filename(template_name)
        path = os.path.join(templates_dir, safe)
        if not os.path.exists(path):
            return jsonify({"error": "Template not found"}), 404

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse variables from template
        import re as _re
        vars_found = sorted(set(_re.findall(r'\{\{\s*(\w+)\s*\}\}', content)))
        return jsonify({"name": safe, "content": content, "variables": vars_found})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ============================================================================
# CLI TERMINAL INTERFACE (v5.0)
# ============================================================================

def get_device_type_from_inventory(host, inventory_file='inventory.txt'):
    """
    Parse inventory file to find device_type for given host.
    
    Supports inventory format:
    [Section]
    192.168.1.1, cisco_ios
    192.168.1.2, cisco_nxos
    """
    try:
        # Check for uploaded inventory first
        if os.path.exists('uploaded_inventory.txt'):
            inventory_file = 'uploaded_inventory.txt'
        elif not os.path.exists(inventory_file):
            return None
            
        with open(inventory_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip section headers, empty lines, comments
                if not line or line.startswith('[') or line.startswith('#'):
                    continue
                
                # Parse host,device_type format
                if ',' in line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        inventory_host = parts[0]
                        device_type = parts[1]
                        
                        # Match host (exact or IP match)
                        if inventory_host == host or inventory_host in host or host in inventory_host:
                            # Normalize device type
                            device_type = device_type.lower().replace('-', '_')
                            
                            # Validate known device types
                            valid_types = [
                                'cisco_ios', 'cisco_xe', 'cisco_nxos', 'cisco_xr',
                                'juniper_junos', 'hp_comware', 'huawei', 'arista_eos'
                            ]
                            
                            if device_type in valid_types:
                                app.logger.info(f"Found device type '{device_type}' for host '{host}' in inventory")
                                return device_type
                            else:
                                app.logger.warning(f"Unknown device type '{device_type}' for host '{host}'")
                                # Return as-is, let Netmiko handle it
                                return device_type
                                
    except Exception as e:
        app.logger.error(f"Error parsing inventory for host '{host}': {str(e)}")
    
    return None


@app.route('/api/get_device_type')
def api_get_device_type():
    """API endpoint to get device type from inventory for given host."""
    host = request.args.get('host', '')
    if not host:
        return jsonify({'error': 'No host specified'}), 400
    
    device_type = get_device_type_from_inventory(host)
    
    if device_type:
        return jsonify({
            'host': host,
            'device_type': device_type,
            'found': True
        })
    else:
        return jsonify({
            'host': host,
            'device_type': None,
            'found': False,
            'message': 'Device type not found in inventory, will use default'
        })


# ============================================================================
# Asset Warranty Consolidated Report API Endpoints
# ============================================================================

@app.route('/api/reports/asset-warranty/input-files')
def api_asset_warranty_input_files():
    """List all Asset Warranty report files in the input directory."""
    try:
        from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
        consolidator = AssetWarrantyConsolidator()
        files = consolidator.get_input_files()
        return jsonify({
            'success': True,
            'files': files,
            'input_dir': str(consolidator.input_dir)
        })
    except Exception as e:
        app.logger.error(f"Error listing input files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/asset-warranty/consolidate', methods=['POST'])
def api_asset_warranty_consolidate():
    """Consolidate all Asset Warranty reports into a master report."""
    try:
        from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
        
        data = request.get_json() or {}
        report_name = data.get('report_name')
        
        consolidator = AssetWarrantyConsolidator()
        result = consolidator.consolidate_reports(report_name)
        
        if result['success']:
            add_log(f"[Reports] Consolidated Asset Warranty report created: {result['output_file']}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        app.logger.error(f"Error consolidating reports: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/asset-warranty/output-files')
def api_asset_warranty_output_files():
    """List all generated consolidated Asset Warranty reports."""
    try:
        from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
        consolidator = AssetWarrantyConsolidator()
        
        files = []
        for file_path in consolidator.output_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return jsonify({
            'success': True,
            'files': sorted(files, key=lambda x: x['modified'], reverse=True),
            'output_dir': str(consolidator.output_dir)
        })
    except Exception as e:
        app.logger.error(f"Error listing output files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/reports/asset-warranty/<filename>')
def serve_asset_warranty_report(filename):
    """Serve a generated consolidated Asset Warranty report."""
    try:
        from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
        consolidator = AssetWarrantyConsolidator()
        file_path = consolidator.output_dir / filename
        
        if not file_path.exists():
            return jsonify({'error': 'Report not found'}), 404
        
        return send_file(str(file_path))
    except Exception as e:
        app.logger.error(f"Error serving report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/cli_terminal')
def cli_terminal():
    """Render CLI terminal page with device type from inventory."""
    host = request.args.get('host', '')
    device_type = request.args.get('device_type', '')
    
    # If device_type not provided in URL, try to get from inventory
    if not device_type and host:
        device_type = get_device_type_from_inventory(host)
        if not device_type:
            device_type = 'cisco_ios'  # Default fallback
    
    app.logger.info(f"CLI terminal opened for {host} with device type {device_type}")
    return render_template(
        'cli_terminal.html',
        host=host,
        device_type=device_type,
        version=VERSION,
    )


# WebSocket event handlers for CLI (only if SocketIO is available)
if SOCKETIO_AVAILABLE:
    from modules.cli_manager import (
        bind_cli_owner, cleanup_idle_sessions, cli_owner_matches,
        create_cli_session, get_cli_session, release_cli_owner,
        remove_cli_session, session_ids_owned_by_sid,
    )

    @socketio.on('connect')
    def handle_socketio_connect():
        from utils.vault_credentials import public_cli_status_payload
        denied = _socketio_operator_denied()
        if denied:
            emit('cli_error', public_cli_status_payload(denied))
            disconnect()
            return False
        return True

    @socketio.on('disconnect')
    def handle_socketio_disconnect():
        sid = getattr(request, 'sid', None)
        if not sid:
            return
        for sess in session_ids_owned_by_sid(sid):
            remove_cli_session(sess)
            add_log(f"[CLI] Session released on socket disconnect session={sess}")

    @socketio.on('cli_connect')
    def handle_cli_connect(data):
        """CLI SSH connect. Prefer credential_id; plaintext is a deprecated compat path."""
        from utils.session_cred_cache import get_session_credentials
        from utils.vault_credentials import (
            mapping_has_secret_fields,
            public_cli_status_payload,
            resolve_cli_connect_credentials,
        )

        denied = _socketio_operator_denied()
        sid = request.sid
        if denied:
            socketio.emit('cli_error', public_cli_status_payload(denied), to=sid)
            return
        if not isinstance(data, dict):
            socketio.emit(
                'cli_error',
                public_cli_status_payload({'message': 'Malformed connection payload', 'code': 'malformed_payload'}),
                to=sid,
            )
            return

        session_id = (data.get('session_id') or '').strip()
        device_host = (data.get('host') or '').strip()
        device_type = data.get('device_type', 'cisco_ios')
        try:
            device_port = int(data.get('port', 22) or 22)
        except (TypeError, ValueError):
            socketio.emit(
                'cli_error',
                public_cli_status_payload({'message': 'Invalid port', 'code': 'malformed_payload'}),
                to=sid,
            )
            return

        if session_id:
            join_room(session_id)

        def _log(msg):
            try:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(os.path.join(get_logs_dir(), "cli_socket_debug.log"), "a", encoding="utf-8") as f:
                    f.write(f"[{ts}] sid={sid} session={session_id} host={device_host} :: {msg}\n")
            except Exception:
                pass

        def _emit(event_name, payload, target='room'):
            if event_name == 'cli_output':
                safe = payload
            elif event_name in ('cli_status', 'cli_error', 'cli_progress'):
                safe = public_cli_status_payload(payload)
            else:
                safe = payload
            if event_name != 'cli_output' and mapping_has_secret_fields(safe):
                _log(f"emit blocked [{event_name}]: sanitizer detected secret field")
                safe = public_cli_status_payload({'message': 'CLI event unavailable', 'code': 'sanitizer'})
                event_name = 'cli_error'
            try:
                if target == 'sid':
                    socketio.emit(event_name, safe, to=sid)
                else:
                    socketio.emit(event_name, safe, to=session_id)
                _log(f"emit OK [{event_name}] to {target} keys={sorted(list(safe.keys()) if isinstance(safe, dict) else [])}")
            except Exception as exc:
                _log(f"emit FAIL [{event_name}]: {type(exc).__name__}")

        if not session_id or not device_host:
            _emit('cli_error', {'message': 'Missing connection parameters', 'code': 'missing_connection_parameters'}, target='sid')
            return

        resolved, cred_err = resolve_cli_connect_credentials(
            data, credential_manager, get_session_credentials() or {},
        )
        if cred_err:
            add_log(f"[CLI] credential reject code={cred_err.get('code')} session={session_id}")
            _emit('cli_error', {
                'message': cred_err.get('error') or 'Credential unavailable',
                'code': cred_err.get('code') or 'unavailable_credential',
            }, target='sid')
            return

        username = resolved['username']
        password = resolved['password']
        enable_password = resolved.get('enable_pwd') or ''
        cred_id = resolved.get('credential_id') or ''
        if cred_id:
            from utils.api_security import audit_credential_access
            audit_credential_access(add_log, 'RESOLVE', cred_id)

        existing = get_cli_session(session_id)
        if existing:
            if getattr(existing, 'connected', False):
                if not cli_owner_matches(session_id, sid):
                    _emit('cli_error', {'message': 'Session belongs to another client', 'code': 'session_isolated'}, target='sid')
                    return
                add_log(f"[CLI] Reconnecting to session {session_id}")
                _emit('cli_status', {
                    'status': 'connected',
                    'hostname': existing.hostname,
                    'message': f'Reconnected to {existing.hostname}',
                    'credential_id': existing.credential_id or None,
                })
                return
            remove_cli_session(session_id)

        bind_cli_owner(session_id, sid)
        device = {
            'device_type': device_type, 'host': device_host, 'port': device_port,
            'username': username, 'password': password, 'secret': enable_password,
        }

        _emit('cli_status', {
            'status': 'connecting',
            'message': 'Handshaking...',
            'credential_id': cred_id or None,
            'username': username,
        }, target='sid')

        def background_connect():
            try:
                _log("Background connect started")
                def log_callback(msg): _emit('cli_progress', {'message': msg})
                def data_callback(raw): _emit('cli_output', {'output': raw})

                _emit('cli_progress', {'message': f'[1/3] TCP probe {device_host}...'})
                import socket as _s
                try:
                    sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    sock.settimeout(3.0)
                    result = sock.connect_ex((device_host, device_port))
                    sock.close()
                    if result != 0:
                        release_cli_owner(session_id)
                        _emit('cli_error', {'message': f'TCP Port {device_port} unreachable (code {result})', 'code': 'adapter_failure'})
                        return
                except Exception:
                    release_cli_owner(session_id)
                    _emit('cli_error', {'message': 'TCP probe failed', 'code': 'adapter_failure'})
                    return

                _emit('cli_progress', {'message': '[2/3] SSH Auth...'})
                cli = create_cli_session(
                    session_id, device, username, password, enable_password,
                    log_callback, data_callback,
                )
                device['password'] = ''
                device['secret'] = ''
                if cli:
                    cli.credential_id = cred_id or ''
                    _emit('cli_status', {
                        'status': 'connected',
                        'hostname': cli.hostname,
                        'message': 'Ready',
                        'credential_id': cred_id or None,
                        'username': username,
                    })
                else:
                    release_cli_owner(session_id)
                    _emit('cli_error', {'message': 'SSH Auth Failed', 'code': 'adapter_failure'})
            except Exception:
                release_cli_owner(session_id)
                _emit('cli_error', {'message': 'Connect failed', 'code': 'adapter_failure'})

        socketio.start_background_task(background_connect)

    @socketio.on('cli_data')
    def handle_cli_data(data):
        if not isinstance(data, dict):
            return
        denied = _socketio_operator_denied()
        if denied:
            return
        session_id = data.get('session_id')
        input_data = data.get('data')
        if session_id and input_data is not None and cli_owner_matches(session_id, request.sid):
            cli = get_cli_session(session_id)
            if cli and cli.connected:
                cli.write(input_data)

    @socketio.on('cli_resize')
    def handle_cli_resize(data):
        if not isinstance(data, dict):
            return
        if _socketio_operator_denied():
            return
        session_id = data.get('session_id')
        if session_id and cli_owner_matches(session_id, request.sid):
            cli = get_cli_session(session_id)
            if cli:
                cli.resize_pty(data.get('cols'), data.get('rows'))

    @socketio.on('cli_disconnect')
    def handle_cli_disconnect(data):
        if not isinstance(data, dict):
            return
        if _socketio_operator_denied():
            return
        session_id = data.get('session_id')
        if session_id and cli_owner_matches(session_id, request.sid):
            remove_cli_session(session_id)
            from utils.vault_credentials import public_cli_status_payload
            socketio.emit(
                'cli_status',
                public_cli_status_payload({'status': 'disconnected', 'message': 'Closed'}),
                to=request.sid,
            )

# Background thread to cleanup idle sessions
def _cleanup_idle_sessions_task():
    """Background task to cleanup idle CLI sessions."""
    while True:
        try:
            if SOCKETIO_AVAILABLE:
                count = cleanup_idle_sessions(timeout_seconds=600)  # 10 minutes
                if count > 0:
                    add_log(f"[CLI] Cleaned up {count} idle sessions")
        except Exception as e:
            print(f"[CLI] Cleanup error: {e}")
        time.sleep(60)  # Check every minute

# Start cleanup thread
if SOCKETIO_AVAILABLE:
    cleanup_thread = threading.Thread(target=_cleanup_idle_sessions_task, daemon=True)
    cleanup_thread.start()
    print("[INFO] CLI idle session cleanup thread started")


def initialize_standards_folder():
    """v6.9.21: Create standards and templates folders in program directory with bundled files."""
    try:
        # Determine program directory
        if getattr(sys, 'frozen', False):
            program_dir = os.path.dirname(sys.executable)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. Initialize standards folder
        standards_dir = os.path.join(program_dir, 'standards')
        os.makedirs(standards_dir, exist_ok=True)
        
        # Copy bundled standards files if they don't exist
        bundled_standards = [
            ('policies/standards.yaml', 'standards.yaml'),
            ('policies/standards.json', 'standards.json')
        ]
        
        for bundled_path, local_name in bundled_standards:
            try:
                bundled_full = _get_resource_path(bundled_path)
                local_full = os.path.join(standards_dir, local_name)
                
                if os.path.exists(bundled_full) and not os.path.exists(local_full):
                    import shutil
                    shutil.copy2(bundled_full, local_full)
                    startup_log(f"Copied {local_name} to standards folder")
            except Exception as e:
                startup_log(f"Could not copy {local_name}: {e}")
        
        # Create category subdirectories
        categories = ['Security', 'NTP', 'SNMP', 'Logging', 'Naming', 'Interface', 'AAA', 'Routing', 'QoS', 'Redundancy', 'Management', 'Health', 'Crypto', 'Compliance']
        for category in categories:
            cat_dir = os.path.join(standards_dir, category)
            os.makedirs(cat_dir, exist_ok=True)
        
        startup_log(f"Standards folder initialized at {standards_dir}")
        
        # 2. Initialize and bootstrap templates folder
        templates_dir = os.path.join(program_dir, 'templates')
        try:
            from modules.plugins.config_templates import bootstrap_example_templates
            bootstrap_example_templates(templates_dir)
            startup_log(f"Config templates folder initialized at {templates_dir}")
        except Exception as te:
            startup_log(f"Could not bootstrap configuration templates: {te}")
            
    except Exception as e:
        startup_log(f"Could not initialize system folders: {e}")

def run_web():
    """v6.9.21: Hardened server startup with comprehensive logging."""
    from utils.api_security import resolve_web_bind_host, resolve_web_port
    bind_host = resolve_web_bind_host()
    web_port = resolve_web_port()
    browser_host = '127.0.0.1' if bind_host in ('0.0.0.0', '::', '*') else bind_host
    startup_log(f"=== Network Swiss Tool Pro v{VERSION} Starting ===")
    startup_log(f"Logs directory: {get_logs_dir()}")
    # v6.9.21: Initialize standards folder
    initialize_standards_folder()
    
    log_dependencies()
    add_log(f"--- System Booted. Persisting Session to {session_log_file} ---")
    
    # v5.5.0: Enhanced Port Probe with detailed logging
    import socket
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_available = False
    try:
        test_sock.bind((bind_host if bind_host not in ('0.0.0.0', '::') else '127.0.0.1', web_port))
        test_sock.close()
        port_available = True
        startup_log(f"Port {web_port} is available")
    except Exception as e:
        startup_log(f"CRITICAL: Port {web_port} is occupied or blocked: {e}")
        # We continue anyway but log the failure
    
    # v5.5.0: Log Socket.IO status
    if SOCKETIO_AVAILABLE:
        startup_log(f"Socket.IO is AVAILABLE (async_mode={socketio.async_mode})")
        startup_log(f"Socket.IO threading driver: engineio.async_drivers.threading")
    else:
        startup_log("WARNING: Socket.IO is NOT available - CLI Terminal will be disabled")
    
    # Open browser after a short delay to ensure server is ready
    startup_log("Scheduling browser open in 2 seconds...")
    threading.Timer(2.0, lambda: webbrowser.open(f"http://{browser_host}:{web_port}")).start()
    
    # v5.5.0: Start server with enhanced error handling
    if SOCKETIO_AVAILABLE:
        startup_log(f"Starting Socket.IO server on {bind_host}:5051...")
        try:
            # Log the actual configuration being used
            startup_log(f"Server config: host={bind_host}, port=web_port, threading mode")
            startup_log(f"Health check URL: http://{browser_host}:{web_port}/health")
            startup_log(f"Debug status URL: http://{browser_host}:{web_port}/debug_status")
            
            socketio.run(
                app, 
                host=bind_host, 
                port=web_port, 
                allow_unsafe_werkzeug=True,
                log_output=False  # v5.5.0: Disable to reduce console spam, use our own logging
            )
        except Exception as e:
            startup_log(f"FATAL: Socket.IO server failed to start: {e}")
            import traceback
            startup_log(f"Traceback: {traceback.format_exc()}")
            # Fallback to pure Flask
            startup_log("Falling back to pure Flask server (Socket.IO disabled)")
            app.run(host=bind_host, port=web_port)
    else:
        startup_log(f"Starting pure Flask server (no Socket.IO) on {bind_host}:5051")
        app.run(host=bind_host, port=web_port)

if __name__ == '__main__':
    run_web()
