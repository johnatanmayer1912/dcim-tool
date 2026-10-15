# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/network_base.py
# ============================================================================
# PURPOSE: Core network connection utilities and helper functions.
# PROVIDES: SSH connection management with credential fallback support.
#
# KEY_FUNCTIONS:
#   - safe_connection(device, user, pwd, enb_pwd, log_func, fallback_credentials):
#     Context manager for SSH connections with credential fallback
#   - connect_device(...): same fallback order; returns live connection (caller disconnects)
#   - safe_connection_from_credentials(device, credentials, log_func):
#     Plugin-friendly wrapper reading fallback_credentials from credentials dict
#   - attach_fallback_to_devices(devices, ...): stamp devices for legacy Tools paths
#   - connect_permissive(target_dict, user, pwd, enb_pwd, log_func):
#     Two-pass SSH connection (modern algorithms, then legacy fallback)
#   - build_json(device_host, status, data, error):
#     Standard JSON response format for all operations
#   - safe_node_name(hostname): Sanitize hostname for safe use
#
# CREDENTIAL_FALLBACK_MECHANISM:
#   safe_connection() / connect_device() accept fallback_credentials (list of dicts)
#   Tries primary credential first, then secondary, then tertiary
#   Logs each attempt with attempt number (1/3, 2/3, 3/3)
#   Raises exception if all credentials fail
#   Deduplicates identical credentials to avoid redundant attempts
#
# SSH_ALGORITHM_FALLBACK:
#   connect_permissive() uses two-pass strategy:
#   Pass 1: Modern algorithms (works on IOS-XE 17.3+, NX-OS 9.3+)
#   Pass 2: Legacy fallback (disables rsa-sha2-512/256 for older devices)
#   Only falls back on algorithm negotiation failures, not auth failures
#
# CONNECTIONS:
#   - Used by: All plugins, Discovery/IM/STP/Standards APIs, legacy Tools modules
#   - Used by: modules/adapters.py for network operations
#   - Used by: modules/plugins/*.py for SSH connections
#
# USAGE_PATTERN:
#   with safe_connection(device, username, password, secret, log_func,
#                       fallback_credentials=credentials.get('fallback_credentials')) as conn:
#       output = conn.send_command('show version')
#
# ============================================================================
# CRITICAL: Install telnetlib compatibility for Python 3.13+
import sys
try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401

import re
from contextlib import contextmanager
from netmiko import ConnectHandler

def build_json(device_host, status, data=None, error=None):
    return {
        "device": device_host,
        "status": status,
        "data": data if data is not None else {},
        "error": str(error) if error else None
    }

def connect_permissive(target_dict, user, pwd, enb_pwd, log_func=None):
    """Two-pass SSH connection strategy (v6.2.6).

    Pass 1: Modern algorithms (default Paramiko behaviour).
            Works on IOS-XE 17.3+, NX-OS 9.3+, Juniper 21.x+.
    Pass 2: Legacy fallback – disables rsa-sha2-512/256 for older
            devices that only support ssh-rsa (SHA-1).
    """
    host = target_dict["host"]
    dtype = target_dict["device_type"]

    base_params = {
        "host": host,
        "device_type": dtype,
        "username": user,
        "password": pwd,
        "global_delay_factor": 1.5,
        "timeout": 20,
        "auth_timeout": 20,
        "banner_timeout": 20,
    }
    # GUI sets port
    if 'port' in target_dict:
        base_params['port'] = target_dict['port']
    if enb_pwd:
        base_params["secret"] = enb_pwd
    else:
        try:
            from utils.task_credentials import get_task_become_password
            become = get_task_become_password()
        except ImportError:
            become = ''
        if become and 'juniper' in dtype.lower():
            base_params["secret"] = become

    def _enable_if_needed(conn, device_type, secret_password=None, log_func=None):
        """Attempt enable mode for Cisco-family devices."""
        if any(t in device_type.lower() for t in ("cisco", "nxos", "ios")):
            if not conn.check_enable_mode():
                try:
                    # netmiko uses the secret from connection parameters automatically
                    conn.enable()
                    if log_func:
                        log_func(f"[{conn.host}] Entered enable mode successfully")
                except Exception as exc:
                    if log_func:
                        log_func(f"[{conn.host}] Enable mode failed: {exc}")
                    # Don't raise - some devices may not need enable mode for show commands

    # ── Pass 1: Modern algorithms (no overrides) ──
    try:
        conn = ConnectHandler(**base_params)
        _enable_if_needed(conn, dtype, enb_pwd, log_func)
        return conn
    except Exception as e1:
        e1_str = str(e1).lower()
        # ONLY fall back on SSH algorithm negotiation failures.
        # Auth failures (wrong password) or network errors (timeout, refused)
        # must NOT be retried — retrying auth risks device account lockout.
        is_algo_failure = any(kw in e1_str for kw in [
            "no acceptable kex", "no matching", "algorithm negotiation",
            "key exchange", "unable to agree", "incompatible",
            "kex negotiation", "no supported", "disabled_algorithms",
        ])
        if not is_algo_failure:
            raise  # Auth failure / unreachable — propagate immediately
        if log_func:
            log_func(f"[{host}] SSH algorithm mismatch, trying legacy mode...")

    # ── Pass 2: Legacy fallback – disable SHA-2 pubkeys ──
    legacy_params = dict(base_params)
    legacy_params["disabled_algorithms"] = dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"])

    conn = ConnectHandler(**legacy_params)
    _enable_if_needed(conn, dtype, enb_pwd, log_func)
    return conn

def safe_node_name(hostname):
    if not hostname: return "unknown"
    hostname = hostname.strip().lower()
    hostname = re.sub(r'[:>#\]\)]+$', '', hostname).strip()
    if _hostname_looks_like_banner(hostname):
        return None
    blacklist = ['password', 'login', 'username', 'user', 'cisconexus', 'juniper', 'ios', 'nexus', 'switch', 'router']
    if hostname in blacklist or len(hostname) < 2: return None
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname): return hostname
    return hostname.split('.')[0]

_BANNER_HOSTNAME_MARKERS = (
    'software', 'http://', 'https://', 'tac support', 'copyright',
    'cisco nexus operating', 'nx-os', 'ios software', 'image file',
)


def _hostname_looks_like_banner(value):
    """Reject show-version banner blobs mistaken for hostnames."""
    if not value:
        return True
    low = value.strip().lower()
    if len(low) > 63:
        return True
    if any(m in low for m in _BANNER_HOSTNAME_MARKERS):
        return True
    if low.count(' ') >= 4:
        return True
    return False


_AUTH_PROMPT_MARKERS = (
    'password', 'username', 'login:', 'user access', 'enter password',
    'user name', 'enable password', 'passphrase', 'authentication failed',
    'access denied', 'connection closed', 'timeout expired', 'press return',
    'last login', 'warning:', 'notice:', 'error:', 'invalid',
)


def _prompt_looks_invalid(value):
    """Reject SSH/login noise mistaken for a hostname (MAC trace / bulk scans)."""
    if not value or _hostname_looks_like_banner(value):
        return True
    low = value.strip().lower()
    low = re.sub(r':+$', '', low).strip()
    if any(m in low for m in _AUTH_PROMPT_MARKERS):
        return True
    if low in ('yes', 'no', 'confirm', 'continue', 'enable', 'secret', 'login'):
        return True
    if safe_node_name(low) is None:
        return True
    return False


def _fallback_hostname_label(fallback_ip):
    """Management IP or inventory label when prompt/version parse fails."""
    fallback = (fallback_ip or '').strip() or 'unknown'
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', fallback):
        return fallback.lower()
    cleaned = safe_node_name(fallback)
    return cleaned or fallback.lower()


def _hostname_from_prompt_text(prompt):
    """Normalize find_prompt() text to a hostname candidate or None."""
    if not prompt:
        return None
    prompt = re.sub(r'\(config[^)]*\)#?$', '', prompt, flags=re.I).strip()
    prompt = prompt.replace('#', '').replace('>', '').strip()
    prompt = re.sub(r':+$', '', prompt).strip()
    if '@' in prompt:
        prompt = prompt.split('@')[-1].strip()
    if _prompt_looks_invalid(prompt):
        return None
    return safe_node_name(prompt)


def _hostname_from_ver_output(ver_output, device_type):
    """Parse hostname/switchname from show version (line-based, not whole blob)."""
    if not ver_output:
        return None
    dtype = (device_type or '').lower()
    patterns = [
        r'^\s*switchname\s*:\s*(\S+)',
        r'^\s*Device\s+name\s*:\s*(\S+)',
        r'^\s*hostname\s*:\s*(\S+)',
        r'^\s*hostname\s+(\S+)',
    ]
    for line in ver_output.splitlines():
        for pat in patterns:
            m = re.search(pat, line, re.I)
            if m:
                candidate = m.group(1).strip().strip('"')
                if not _hostname_looks_like_banner(candidate):
                    return safe_node_name(candidate) or candidate.lower()
    if 'nxos' in dtype or 'nexus' in dtype:
        m = re.search(r'^\s*([A-Za-z0-9][A-Za-z0-9_-]{1,62})\s+uptime\s+is', ver_output, re.M | re.I)
        if m and not _hostname_looks_like_banner(m.group(1)):
            return safe_node_name(m.group(1)) or m.group(1).lower()
    return None


def resolve_device_hostname(conn, ver_output, fallback_ip, device_type=None, log_func=None):
    """
    Resolve a stable device hostname for graph labels (Discovery, audit helpers).
    Order: SSH prompt -> show version fields -> show hostname -> fallback IP.
    """
    fallback = (fallback_ip or '').strip() or 'unknown'
    candidates = []

    if conn is not None:
        try:
            from_prompt = _hostname_from_prompt_text(conn.find_prompt() or '')
            if from_prompt:
                candidates.append(from_prompt)
        except Exception:
            pass

    parsed = _hostname_from_ver_output(ver_output, device_type)
    if parsed:
        candidates.append(parsed)

    if conn is not None:
        try:
            host_out = conn.send_command('show hostname', read_timeout=15)
            for line in (host_out or '').splitlines():
                line = line.strip()
                if not line:
                    continue
                m = re.search(r'hostname\s+is\s+["\']?(\S+)', line, re.I)
                if m:
                    candidates.append(m.group(1))
                    continue
                m = re.search(r'^hostname\s+(\S+)', line, re.I)
                if m:
                    candidates.append(m.group(1))
                    continue
                if line.lower().startswith('hostname'):
                    continue
                if not _prompt_looks_invalid(line):
                    cleaned = safe_node_name(line)
                    if cleaned:
                        candidates.append(cleaned)
                    break
        except Exception:
            pass

    for raw in candidates:
        if not raw or _hostname_looks_like_banner(raw) or _prompt_looks_invalid(raw):
            continue
        cleaned = safe_node_name(raw)
        if cleaned:
            return cleaned
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', raw.strip().lower()):
            return raw.strip().lower()

    if log_func:
        log_func(f"[{fallback}] Using management IP as hostname label (prompt/version parse failed)")
    return _fallback_hostname_label(fallback)


def resolve_hostname_from_prompt(conn, fallback_ip, device_type=None):
    """Hostname from SSH prompt; falls back to management IP (never auth prompt text)."""
    try:
        if conn is not None:
            from_prompt = _hostname_from_prompt_text(conn.find_prompt() or '')
            if from_prompt:
                return from_prompt
    except Exception:
        pass
    return _fallback_hostname_label(fallback_ip)


def resolve_hostname_from_connection(conn, fallback_ip, device_type=None, log_func=None, fetch_version=True):
    """Resolve hostname using prompt and optionally show version."""
    ver_output = ''
    if fetch_version and conn is not None:
        try:
            ver_output = conn.send_command('show version', read_timeout=60)
        except Exception:
            pass
    return resolve_device_hostname(conn, ver_output, fallback_ip, device_type, log_func)


def normalize_neighbor_hostname(hostname, fallback=None):
    """Sanitize neighbor CDP/LLDP names; reject banner-like strings."""
    if not hostname:
        return fallback or 'unknown'
    host = hostname.split('(')[0].strip()
    if _hostname_looks_like_banner(host):
        return fallback or 'unknown'
    cleaned = safe_node_name(host)
    return cleaned or host.lower().split('.')[0]


def parse_vlan_output(output, device_type):
    results = []
    lines = output.splitlines()
    dt = (device_type or "").lower()
    is_cisco_family = (
        'juniper' not in dt
        and any(tag in dt for tag in ('cisco', 'ios', 'nxos', 'iosxr', 'ios_xr', 'cisco_xr', 'ios-xr'))
    )
    if is_cisco_family:
        cisco_pattern = re.compile(r'^(\d+)\s+([\w-]+)\s+([\w-]+)')
        for line in lines:
            match = cisco_pattern.search(line.strip())
            if match:
                results.append((match.group(1), match.group(2), match.group(3)))
    elif 'juniper' in device_type.lower():
        els_pattern = re.compile(r'^\S+\s+([\w-]+)\s+(\d+)(\s+|$)') 
        legacy_pattern = re.compile(r'^([\w-]+)\s+(\d+)(\s+|$)') 
        _skip_headers = frozenset({
            'vlan name', 'name', 'routing instance', 'vlan-id', 'vlan id',
        })
        for line in lines:
            line = line.strip()
            if not line or line.lower() in _skip_headers or line.lower().startswith('routing instance'):
                continue
            els_match = els_pattern.search(line)
            if els_match:
               results.append((els_match.group(2), els_match.group(1), "N/A"))
               continue
            legacy_match = legacy_pattern.search(line)
            if legacy_match:
                results.append((legacy_match.group(2), legacy_match.group(1), "N/A"))
    return results
def get_devices_from_file(path):
    """Centralized inventory loader supporting Group headers and comma/space separation."""
    import os
    devices = []
    current_group = "Default"
    if not os.path.exists(path):
        return []
    try:
        with open(path, mode='r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Detect Group Header [GroupName]
                group_match = re.match(r'^\[([\w\-_ ]+)\]$', line)
                if group_match:
                    current_group = group_match.group(1)
                    continue

                # Support comma or space separation
                parts = re.split(r'[,\s]+', line)
                if len(parts) >= 2:
                    host_val = parts[0]
                    dtype_val = parts[1]
                    port_val = 22
                    grp_val = current_group
                    
                    if len(parts) > 2:
                        if parts[2].isdigit():
                            port_val = int(parts[2])
                        else:
                            grp_val = parts[2]
                    
                    devices.append({
                        'host': host_val,
                        'device_type': dtype_val,
                        'port': port_val,
                        'group': grp_val
                    })
        return devices
    except Exception:
        return []


def _build_credential_attempts(device, user, pwd, enb_pwd, fallback_credentials=None):
    """Build ordered Primary → Secondary → Third credential attempt list."""
    creds_to_try = [{'username': user, 'password': pwd, 'enable_pwd': enb_pwd, 'label': 'Primary'}]
    fb_list = list(fallback_credentials or device.get('fallback_credentials') or [])
    if not fb_list:
        if device.get('secondary_credential'):
            fb_list.append(device['secondary_credential'])
        if device.get('third_credential'):
            fb_list.append(device['third_credential'])
    for fb in fb_list:
        if isinstance(fb, dict) and (fb.get('username') or fb.get('password')):
            u = fb.get('username') or user
            p = fb.get('password') or ''
            e = (
                fb.get('enable_pwd')
                or fb.get('admin_password')
                or fb.get('secret')
                or fb.get('become_password')
                or enb_pwd
            )
            lbl = fb.get('label') or fb.get('credential_id') or 'Credential'
            if (u, p, e) != (user, pwd, enb_pwd):
                creds_to_try.append({'username': u, 'password': p, 'enable_pwd': e, 'label': lbl})
    return creds_to_try


def connect_device(device, user, pwd, enb_pwd, log_func=None, fallback_credentials=None):
    """Connect with Primary → Secondary → Tertiary fallback. Caller must disconnect.

    Drop-in upgrade for connect_permissive() that honors device['fallback_credentials']
    and an explicit fallback_credentials list.
    """
    host = device.get('host', 'unknown')
    creds_to_try = _build_credential_attempts(device, user, pwd, enb_pwd, fallback_credentials)
    last_exc = None
    for idx, cred in enumerate(creds_to_try):
        curr_user = cred['username']
        curr_pwd = cred['password']
        curr_enb = cred['enable_pwd']
        lbl = cred['label']
        if idx > 0:
            lbl = f"Secondary ({lbl})" if idx == 1 else f"Third ({lbl})"
        try:
            try:
                from utils.task_control_plane import should_abort
                if should_abort():
                    raise RuntimeError('cancelled by operator')
            except RuntimeError:
                raise
            except Exception:
                pass
            if log_func:
                if len(creds_to_try) > 1:
                    log_func(
                        f"[{host}] Connecting to device using {lbl} [{curr_user}] "
                        f"(attempt {idx + 1}/{len(creds_to_try)})..."
                    )
                else:
                    log_func(f"[{host}] Connecting to device...")
            conn = connect_permissive(device, curr_user, curr_pwd, curr_enb, log_func=log_func)
            try:
                from utils.task_control_plane import register_live_connection, should_abort
                register_live_connection(conn)
                if should_abort():
                    raise RuntimeError('cancelled by operator')
            except RuntimeError:
                raise
            except Exception:
                pass
            if log_func:
                log_func(f"[{host}] Successfully connected using {lbl} [{curr_user}]")
            return conn
        except RuntimeError as rerr:
            if 'cancelled' in str(rerr).lower():
                raise
            last_exc = rerr
            if log_func:
                log_func(f"[{host}] {lbl} connection failed [{curr_user}]: {str(rerr)}")
            if idx == len(creds_to_try) - 1:
                raise
        except Exception as e:
            last_exc = e
            if log_func:
                log_func(f"[{host}] {lbl} connection failed [{curr_user}]: {str(e)}")
            if idx == len(creds_to_try) - 1:
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError(f'[{host}] No credentials available for connection')


@contextmanager
def safe_connection(device, user, pwd, enb_pwd, log_func=None, fallback_credentials=None):
    """Context manager that ensures proper connect/disconnect with logging and credential fallback.
    
    Args:
        device: Device dict with host, device_type, port
        user: Username (Primary)
        pwd: Password (Primary)
        enb_pwd: Enable password (optional)
        log_func: Logging function that accepts a string (optional)
        fallback_credentials: Optional list of fallback credential dicts (Secondary, Third)
    
    Yields:
        Netmiko connection object
    """
    conn = connect_device(device, user, pwd, enb_pwd, log_func=log_func, fallback_credentials=fallback_credentials)
    try:
        yield conn
    finally:
        if conn:
            try:
                from utils.task_control_plane import unregister_live_connection
                unregister_live_connection(conn)
            except Exception:
                pass
            try:
                host = device.get('host', 'unknown')
                if log_func:
                    log_func(f"[{host}] Logging out from device...")
                conn.disconnect()
                if log_func:
                    log_func(f"[{host}] Successfully logged out")
            except Exception as e:
                if log_func:
                    host = device.get('host', 'unknown')
                    log_func(f"[{host}] Error during disconnect: {str(e)}")


@contextmanager
def safe_connection_from_credentials(device, credentials, log_func=None):
    """Context manager: connect using a credentials dict that may include fallback_credentials."""
    credentials = credentials or {}
    with safe_connection(
        device,
        credentials.get('username') or '',
        credentials.get('password') or '',
        credentials.get('secret') or credentials.get('enable_pwd'),
        log_func=log_func,
        fallback_credentials=credentials.get('fallback_credentials'),
    ) as conn:
        yield conn


def attach_fallback_to_devices(devices, fallback_credentials=None, secondary=None, third=None):
    """Stamp devices with fallback credential metadata for connect_device/safe_connection."""
    fb = list(fallback_credentials or [])
    if not fb:
        if secondary:
            fb.append(secondary)
        if third:
            fb.append(third)
    if not fb:
        return devices
    stamped = []
    for d in devices or []:
        item = dict(d) if isinstance(d, dict) else {'host': str(d)}
        item['fallback_credentials'] = fb
        stamped.append(item)
    return stamped


def credentials_with_fallback(username, password, secret=None, fallback_credentials=None, **extra):
    """Build a credentials dict suitable for plugins / runners."""
    creds = {
        'username': username or '',
        'password': password or '',
        'secret': secret,
    }
    if fallback_credentials:
        creds['fallback_credentials'] = list(fallback_credentials)
    creds.update(extra)
    return creds

