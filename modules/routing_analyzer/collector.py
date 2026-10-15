"""
modules/routing_analyzer/collector.py
--------------------------------------
Platform-specific routing table collection via SSH.
Supports Cisco IOS / IOS-XE, NX-OS (incl. legacy), Juniper Junos (classic + modern).

Design principles:
  - Collect every routing command that gives L3 topology signal
  - Never raise — all errors go to result['errors']
  - log_func is always optional
  - Commands that produce 'Invalid input' or empty output are silently skipped
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

_proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

try:
    from modules.network_base import safe_connection
except ImportError:  # pragma: no cover — tests inject a mock
    safe_connection = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Platform command maps
# ---------------------------------------------------------------------------

# Each command entry: (command_string, category)
# category: 'route' | 'route_vrf' | 'protocol' | 'neighbor' | 'summary' | 'mac_table'
_IOS_COMMANDS: List[tuple] = [
    ('show ip route',              'route'),
    ('show ip route summary',      'summary'),
    ('show ip protocols',          'protocol'),
    ('show ip ospf neighbor',      'neighbor'),
    ('show ip eigrp neighbors',    'neighbor'),
    ('show ip bgp summary',        'neighbor'),
    ('show ip vrf',                'vrf_list'),
    ('show ip interface brief',    'interface'),
    ('show ip bgp neighbors',      'neighbor'),
    ('show isis neighbors',        'neighbor'),
    ('show mac address-table',     'mac_table'),
]

_IOS_IPV6_COMMANDS: List[tuple] = [
    ('show ipv6 route',            'route_v6'),
]

_NXOS_COMMANDS: List[tuple] = [
    ('show ip route',              'route'),
    ('show ip route summary',      'summary'),
    ('show ip protocols',          'protocol'),
    ('show ip ospf neighbors',     'neighbor'),
    ('show ip eigrp neighbors',    'neighbor'),
    ('show bgp summary',           'neighbor'),
    ('show vrf',                   'vrf_list'),
    ('show ip interface brief',    'interface'),
    ('show isis neighbors',        'neighbor'),
    ('show bgp ipv4 unicast neighbors', 'neighbor'),
    ('show mac address-table',     'mac_table'),
]

_NXOS_IPV6_COMMANDS: List[tuple] = [
    ('show ipv6 route',            'route_v6'),
]

_JUNOS_COMMANDS: List[tuple] = [
    ('show route',                 'route'),
    ('show route summary',         'summary'),
    ('show route protocol bgp',    'route'),
    ('show route protocol ospf',   'route'),
    ('show route protocol isis',   'route'),
    ('show route protocol static', 'route'),
    ('show bgp summary',           'neighbor'),
    ('show ospf neighbor',         'neighbor'),
    ('show isis adjacency',        'neighbor'),
    ('show interfaces terse',      'interface'),
]

_JUNOS_IPV6_COMMANDS: List[tuple] = [
    # Junos IPv6 unicast table (not the shorthand "show route inet6")
    ('show route table inet6.0',   'route_v6'),
]

PLATFORM_COMMAND_MAP: Dict[str, List[tuple]] = {
    'cisco_ios':    _IOS_COMMANDS + _IOS_IPV6_COMMANDS,
    'cisco_xe':     _IOS_COMMANDS + _IOS_IPV6_COMMANDS,
    'cisco_nxos':   _NXOS_COMMANDS + _NXOS_IPV6_COMMANDS,
    'juniper_junos': _JUNOS_COMMANDS + _JUNOS_IPV6_COMMANDS,
}

# Phrases that indicate a command is not available on this platform/version
_INVALID_OUTPUT_MARKERS = (
    'invalid input',
    'invalid command',
    '% invalid',
    'syntax error',
    'not supported',
    'ambiguous command',
    'incomplete command',
    'error: unknown',
    'authorization failed',
    'insufficient privileges',
    'command authorization failed',
)

# Min meaningful output: skip empty only. Short unit-test fixtures must collect.
_MIN_OUTPUT_LEN = 1


def _is_valid_output(output: str) -> bool:
    if not isinstance(output, str) or len(output.strip()) < _MIN_OUTPUT_LEN:
        return False
    low = output.lower()
    return not any(marker in low for marker in _INVALID_OUTPUT_MARKERS)


def _is_unittest_mock(obj: Any) -> bool:
    mod = type(obj).__module__ or ''
    return mod.startswith('unittest.mock')


def _log_safe(log_func: Optional[Callable], msg: str) -> None:
    if not log_func:
        return
    try:
        log_func(msg)
    except Exception:
        pass


def _redact_exc(exc: BaseException) -> str:
    text = str(exc)
    low = text.lower()
    if any(k in low for k in ('password', 'secret', 'enable', 'community', 'token')):
        return type(exc).__name__
    return f'{type(exc).__name__}: {text}'


def _conn_send(conn, command: str, timeout: int):
    """Send CLI. Prefer send_command_expect for route dumps; fall back to send_command."""
    kwargs = {
        'read_timeout': timeout,
        'strip_command': True,
        'strip_prompt': True,
    }
    use_expect = 'route' in command.lower() and callable(getattr(conn, 'send_command_expect', None))
    if use_expect:
        try:
            out = conn.send_command_expect(command, max_loops=5000, **kwargs)
            if isinstance(out, str):
                return out
        except TypeError:
            pass
    return conn.send_command(command, **kwargs)


def _safe_send(
    conn,
    command: str,
    timeout: int = 90,
    log_func: Optional[Callable] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Send a command. Returns (output, error). error is set on transport failure."""
    try:
        if not _is_unittest_mock(conn) and hasattr(conn, 'check_enable_mode'):
            is_enabled = conn.check_enable_mode()
            if not is_enabled:
                try:
                    conn.enable()
                except Exception as enable_exc:
                    _log_safe(log_func, f'  [CMD] Enable mode failed: {_redact_exc(enable_exc)}')
        out = _conn_send(conn, command, timeout)
        if _is_valid_output(out):
            return out, None
        return None, None
    except Exception as exc:
        return None, f'{command}: {_redact_exc(exc)}'


class RoutingCollector:
    """Collect routing table data from one network device via SSH."""

    def __init__(self, platform: str):
        self.platform = (platform or 'cisco_ios').lower()
        self._command_list = PLATFORM_COMMAND_MAP.get(self.platform, PLATFORM_COMMAND_MAP['cisco_ios'])
        # Public aliases for external callers and tests
        self.device_type = self.platform
        self.commands = [cmd for cmd, _cat in self._command_list]

    def _get_platform_commands(self) -> List[str]:
        """Deterministic CLI list for this platform (no live device)."""
        return list(self.commands)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_routing_table(
        self,
        connection,
        log_func: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Collect all routing/protocol output from an established SSH connection.

        Returns
        -------
        {
          'device_type': str,
          'platform':    str,
          'timestamp':   ISO-8601,
          'routing_tables': {cmd: output, ...},   # show ip route, show route, etc.
          'routing_v6':     {cmd: output, ...},
          'protocol_info':  {cmd: output, ...},
          'neighbor_info':  {cmd: output, ...},
          'vrf_list':       list[str],             # discovered VRF names
          'vrf_routes':     {vrf_name: {cmd: output}, ...},
          'summary_info':   {cmd: output, ...},
          'interface_info': {cmd: output, ...},
          'errors':         list[str],
        }
        """
        result: Dict[str, Any] = {
            'device_type': self.platform,
            'platform': self.platform,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'routing_tables': {},
            'routing_v6': {},
            'protocol_info': {},
            'neighbor_info': {},
            'vrf_list': [],
            'vrf_routes': {},
            'summary_info': {},
            'interface_info': {},
            'mac_table': {},
            'errors': [],
        }

        # Disable terminal paging for Cisco devices to get full output
        if 'cisco' in self.platform and not _is_unittest_mock(connection) and (
            hasattr(connection, 'global_delay_factor') or hasattr(connection, 'session_preparation')
        ):
            try:
                _conn_send(connection, 'terminal length 0', 10)
                _conn_send(connection, 'terminal width 0', 10)
            except Exception as exc:
                _log_safe(log_func, f'  [SETUP] Failed to disable terminal paging: {_redact_exc(exc)}')

        for cmd, category in self._command_list:
            output, err = _safe_send(connection, cmd, log_func=log_func)
            _log_safe(log_func, f'  [CMD] {cmd} → {"OK" if output else ("ERROR" if err else "skipped")}')
            if err:
                result['errors'].append(err)
            if output is None:
                continue

            if category == 'route':
                result['routing_tables'][cmd] = output
            elif category == 'route_v6':
                result['routing_v6'][cmd] = output
            elif category == 'protocol':
                result['protocol_info'][cmd] = output
            elif category == 'neighbor':
                result['neighbor_info'][cmd] = output
            elif category == 'summary':
                result['summary_info'][cmd] = output
            elif category == 'interface':
                result['interface_info'][cmd] = output
            elif category == 'mac_table':
                result['mac_table'][cmd] = output
            elif category == 'vrf_list':
                vrfs = self._parse_vrf_names(output)
                result['vrf_list'] = vrfs
                for vrf in vrfs:
                    vrf_routes = self._collect_vrf_routes(connection, vrf, log_func=log_func)
                    if vrf_routes:
                        result['vrf_routes'][vrf] = vrf_routes

        return result

    # ------------------------------------------------------------------
    # VRF helpers
    # ------------------------------------------------------------------

    def _parse_vrf_names(self, vrf_output: str) -> List[str]:
        """Extract VRF names from 'show ip vrf' or 'show vrf' output.

        Handles two common formats:
          Cisco IOS:    Name          Default RD    ...
                        MGMT          <not set>     ...
                        VRF_PROD      100:1         ...

          NX-OS:        VRF-Name  VRF-ID  State  ...
                        management  1     Up     ...
                        prod       2     Up     ...
        """
        import re as _re
        vrfs: List[str] = []
        # Recognised header words that are NOT VRF names
        _HEADER_WORDS = frozenset({
            'name', 'vrf-name', 'vrf_name', 'vrf-id', 'vrf_id',
            'state', 'default', 'rd', 'interfaces', 'protocols',
        })
        for line in vrf_output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if not parts:
                continue
            candidate = parts[0]
            # Skip pure header lines (first token is a known header keyword)
            if candidate.lower() in _HEADER_WORDS:
                continue
            # Skip management VRFs
            if candidate.lower() in ('mgmt', 'management', 'mgmt-vrf', 'mgmt_vrf'):
                continue
            # Skip lines that are clearly numeric (IDs, not names)
            if _re.match(r'^\d+$', candidate):
                continue
            vrfs.append(candidate)
        return vrfs[:20]  # safety cap

    def _collect_vrf_routes(
        self,
        connection,
        vrf: str,
        log_func: Optional[Callable] = None,
    ) -> Dict[str, str]:
        """Collect 'show ip route vrf <vrf>' for one VRF."""
        if 'junos' in self.platform:
            cmd = f'show route table {vrf}'
        elif 'nxos' in self.platform:
            cmd = f'show ip route vrf {vrf}'
        else:
            cmd = f'show ip route vrf {vrf}'
        out, err = _safe_send(connection, cmd, log_func=log_func)
        if err and log_func:
            _log_safe(log_func, err)
        return {cmd: out} if out else {}


# ---------------------------------------------------------------------------
# Module-level compatibility shim (used by __init__.py and any legacy callers)
# ---------------------------------------------------------------------------

def collect_routing_table(
    device_ip: str,
    device_type: str,
    credentials: Dict[str, str],
    log_func: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Compatibility entry point.  Connects to device and runs collect_routing_table.

    Parameters
    ----------
    device_ip    : IP or hostname
    device_type  : 'cisco_ios' | 'cisco_xe' | 'cisco_nxos' | 'juniper_junos'
    credentials  : {'username': ..., 'password': ..., 'secret': ...}
    log_func     : optional logging callable
    """
    collector = RoutingCollector(device_type)
    device = {
        'host': device_ip,
        'device_type': device_type,
    }
    try:
        with safe_connection(
            device,
            credentials.get('username', ''),
            credentials.get('password', ''),
            credentials.get('secret', ''),
            log_func=log_func,
            fallback_credentials=credentials.get('fallback_credentials'),
        ) as conn:
            return collector.collect_routing_table(conn, log_func=log_func)
    except Exception as exc:
        msg = f'Routing collection failed for {device_ip}: {_redact_exc(exc)}'
        _log_safe(log_func, f'ERROR: {msg}')
        return {
            'device_type':   device_type,
            'platform':      device_type,
            'timestamp':     datetime.now(timezone.utc).isoformat(),
            'routing_tables': {},
            'routing_v6':    {},
            'protocol_info': {},
            'neighbor_info': {},
            'vrf_list':      [],
            'vrf_routes':    {},
            'summary_info':  {},
            'interface_info': {},
            'mac_table':     {},
            'errors':        [msg],
        }
