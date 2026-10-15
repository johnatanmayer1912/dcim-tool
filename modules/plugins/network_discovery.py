"""
modules/plugins/network_discovery.py
-----------------------------------
Network Discovery and Topology Mapping Plugin for Network Swiss Tool Pro v6.9.21.

This plugin implements dynamic network crawling starting from a seed device
by recursively fetching and parsing CDP/LLDP neighbors across multiple platforms.

AI_CONTEXT: BFS CDP/LLDP crawler. Seed → SSH → neighbor parse → graph canonicalize → HTML.
AI_FLOW: execute() → crawl_network_multi_seed → parsers → discovery_graph → discovery_map_formatter
AI_DEPENDS_ON: netmiko via network_base, utils.discovery_graph, utils.output_paths
AI_IMPACTS: Discovery Command Center maps, discovered_inventory JSON, Swiss Tools L2
AI_CRAWL_NOTE: Hop depth 1–3. cancel_check returns partial graph. Never invent neighbors.
AI_MAP_NOTE: Overlay/EVPN is not collected here. One-sided edges stay Medium/spoof-risk.
AI_SECURITY_NOTE: Credentials come from the web job; do not log passwords. Plugin is in-process.
AI_OFFLINE_NOTE: demo_mode builds a synthetic lab with no SSH.
AI_TEST_NOTE: tests/test_network_discovery.py + fixtures/discovery/
AI_BREADCRUMB: next — utils/discovery_graph.py, utils/topology_trust.py
AI_TODO_NEXT: SNMP/NETCONF collectors are absent; do not fake them.

=============================================================================
HARDCODED REQUIREMENTS - ALL PLUGINS MUST COMPLY
=============================================================================
1. VERSION REQUIREMENTS (MANDATORY):
   - Version: "1.0.0"
2. DOCUMENTATION REQUIREMENTS (MANDATORY):
   - Located in: docs/plugins/network_discovery/
3. CONTRACT COMPLIANCE:
   - Contains METADATA dict
   - Implements run() function
   - Implements validate_plugin() function
=============================================================================
"""

METADATA = {
    "plugin_id": "network_discovery",
    "display_name": "Network Discovery & Crawl",
    "version": "1.8.0",
    "author": "Network Swiss Tool",
    "category": "Discovery",
    "description": "Recursively crawl CDP/LLDP neighbors starting from a seed device to discover inventory and generate topology. Enhanced with comprehensive edge case handling, offline validation, and duplicate device detection. Fixed JUNOS LLDP discovery by trying brief command first for compatibility with older Junos versions.",
    "min_platform_version": "6.9.21",
    
    "changelog": [
        {
            "version": "1.8.0",
            "date": "2026-06-07",
            "changes": "Critical JUNOS LLDP fix: Changed command order for Juniper devices to try 'show lldp neighbors' (brief) first, then 'show lldp neighbors detail' if needed. This fixes discovery failures on older Junos versions that don't support the detail command. Research from Juniper documentation confirmed that some versions only support the brief format.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.7.0",
            "date": "2026-06-07",
            "changes": "Deep dive enhancements: Added comprehensive parser regression testing for edge cases, enhanced offline environment validation with health check integration, improved duplicate device detection for VPC peer correlation, added user error prevention documentation, enhanced fallback mechanisms for weird scenarios including malformed output, non-standard formats, and legacy device versions",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.6.0",
            "date": "2026-06-07",
            "changes": "JUNOS LLDP and Interface fixes: Fixed 0 links found issue with table format parser for xe- interfaces, added comprehensive 4-tier fallback (standard→brief→table→alternative), fixed interface status unknown issue with Physical link Up/Down detection, improved xe- interface support across all parsers",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.5.0",
            "date": "2026-06-04",
            "changes": "JUNOS LLDP discovery fix: Fixed 0 devices scanned issue with multi-pattern parsing, added fallback mechanisms for older Junos 13.X versions, added brief format fallback, added alternative parsing for non-standard output, improved error handling and logging for troubleshooting",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.4.0",
            "date": "2026-05-31",
            "changes": "NX-OS LLDP: Local Port id, not-advertised hostnames, MAC chassis fallback, MAC-as-Port-id uses Port Description; neighbor dedupe; port normalization.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.3.0",
            "date": "2026-05-24",
            "changes": "BUG-0007 platform classifier (no ex-in-nexus); canonical device merge; graph validation; os_source on nodes.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.2.0",
            "date": "2026-05-31",
            "changes": "NX-OS hostname via resolve_device_hostname; offline discovery map with link inventory tab; neighbor name sanitization.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.1.1",
            "date": "2026-05-31",
            "changes": "Discovery tab UI fix; NetworkDiscoveryPlugin API bridge; multi-seed BFS; IOS/NXOS/Junos detection; demo mode; topology report route.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        },
        {
            "version": "1.0.0",
            "date": "2026-05-26",
            "changes": "Initial release of recursive CDP/LLDP crawler with duplicate detection and dynamic Vis.js mapping.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        }
    ],
    
    "documentation": {
        "readme": "docs/plugins/network_discovery/README.md",
        "release_notes": "docs/plugins/network_discovery/RELEASE_NOTES.md",
        "prompt": "docs/plugins/network_discovery/PROMPT.md",
        "changelog": "docs/plugins/network_discovery/CHANGELOG.md",
        "test_results": "docs/plugins/network_discovery/TEST_RESULTS.md",
        "compatibility": "docs/plugins/network_discovery/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/network_discovery/versions/",
        "current_version_folder": "docs/plugins/network_discovery/versions/v1.0.0/"
    },
    
    "version_archive": {
        "v1.0.0": {
            "file": "docs/plugins/network_discovery/versions/v1.0.0/network_discovery_v1.0.0.py",
            "manifest": "docs/plugins/network_discovery/versions/v1.0.0/manifest.json",
            "date": "2026-05-26",
            "status": "current"
        }
    },
    
    "required_params": {
        "depth": {
            "type": "integer",
            "label": "Crawl Depth (1-3 hops)",
            "default": 2,
            "min": 1,
            "max": 3,
            "required": True,
            "description": "How many hops away from seed device to crawl."
        },
        "protocol": {
            "type": "dropdown",
            "label": "Discovery Protocol",
            "options": ["CDP", "LLDP", "Both"],
            "default": "Both",
            "required": True,
            "description": "Protocol used to fetch neighbor adjacencies."
        },
        "dry_run": {
            "type": "checkbox",
            "label": "Dry Run Mode (Seed Only)",
            "default": False,
            "description": "Scan seed device only without recursive hops."
        }
    },
    
    "supports_parallel": False,
    "supports_dry_run": True,
    "modifies_device": False,
    "requires_enable": True
}

from modules.network_base import (
    safe_connection,
    build_json,
    safe_node_name,
    resolve_device_hostname,
    normalize_neighbor_hostname,
)
from utils.report_formatter import save_plugin_report, append_to_master_report
from datetime import datetime
import re
import os
import json
import socket
import sys


class DiscoveryCancelled(Exception):
    """Operator cancelled between CLI commands. In-flight Netmiko is not killed."""


def _cli_cancelled(cancel_check=None):
    if cancel_check:
        try:
            if cancel_check():
                return True
        except Exception:
            pass
    try:
        from utils.task_control_plane import should_abort
        if should_abort():
            return True
    except Exception:
        pass
    return False


def _send_cli(conn, command, timeout=60, cancel_check=None):
    """Send one CLI command after a cooperative cancel check."""
    if _cli_cancelled(cancel_check):
        raise DiscoveryCancelled('cancelled by operator before CLI')
    try:
        return conn.send_command(command, read_timeout=timeout)
    except DiscoveryCancelled:
        raise
    except Exception:
        if _cli_cancelled(cancel_check):
            raise DiscoveryCancelled('cancelled during CLI (SSH session closed)')
        raise


def _get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _parse_seed_entry(raw):
    """Parse seed line: IP, type or IP type or IP only."""
    raw = (raw or '').strip()
    if not raw:
        return None, None
    if ',' in raw:
        host, dtype = [p.strip() for p in raw.split(',', 1)]
        return host, dtype or ''
    parts = raw.split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    # IP-only seed: leave type empty so crawl can try multi-driver fallback
    return raw, ''


def _detect_device_type(ver_output, fallback_dtype):
    from utils.discovery_graph import classify_os_family
    return classify_os_family(ver_output=ver_output, dtype_hint=fallback_dtype)


def _extract_serial(ver_output, dtype):
    if not ver_output:
        return ''
    for pattern in (
        r'Processor board ID\s+(\S+)',
        r'System serial number\s*:\s*(\S+)',
        r'Chassis Serial Number\s*:\s*(\S+)',
        r'Serial Number\s*:\s*(\S+)',
    ):
        m = re.search(pattern, ver_output, re.I)
        if m:
            return m.group(1).rstrip(',')
    # Junos SN is not reliably in show version — leave empty for chassis hardware path
    return ''


def _ssh_type_for_neighbor(neigh, existing_dtype=''):
    """Best Netmiko device_type for a neighbor — never invent Juniper as IOS."""
    dtype = (existing_dtype or '').strip()
    if dtype and dtype not in ('unknown',):
        return dtype
    plat = neigh.get('platform', '') if isinstance(neigh, dict) else ''
    classified = _platform_from_neighbor_string(plat)
    if classified and classified not in ('', 'unknown'):
        return classified
    plat_l = str(plat or '').lower()
    proto = str((neigh or {}).get('protocol') or '').upper()
    if any(t in plat_l for t in ('juniper', 'junos', 'qfx', 'srx', 'mx', 'ex4', 'ex-')):
        return 'juniper_junos'
    if any(t in plat_l for t in ('nx-os', 'nxos', 'nexus', 'n9k', 'n5k', 'n7k', 'n3k')):
        return 'cisco_nxos'
    if proto == 'CDP':
        return 'cisco_ios'
    return ''


_DRIVER_FALLBACK_ORDER = (
    'cisco_ios', 'cisco_xe', 'cisco_nxos', 'juniper_junos',
)


def _driver_try_order(preferred):
    pref = (preferred or '').strip()
    if pref and pref not in ('unknown',):
        rest = [d for d in _DRIVER_FALLBACK_ORDER if d != pref]
        return [pref] + rest
    return list(_DRIVER_FALLBACK_ORDER)


def _open_discovery_ssh(host, preferred_dtype, username, password, secret, log_func, fallback_credentials):
    """Try Netmiko drivers until one connects. Returns (context_manager, conn, dtype)."""
    last_err = None
    for dtype in _driver_try_order(preferred_dtype):
        device = {'host': host, 'device_type': dtype, 'port': 22}
        cm = safe_connection(
            device, username, password, secret, log_func,
            fallback_credentials=fallback_credentials,
        )
        try:
            conn = cm.__enter__()
            if log_func and dtype != (preferred_dtype or '').strip():
                log_func(f"[{host}] Connected using driver {dtype}")
            return cm, conn, dtype
        except Exception as e:
            last_err = e
            try:
                cm.__exit__(type(e), e, e.__traceback__)
            except Exception:
                pass
            if log_func:
                log_func(f"[{host}] SSH driver {dtype} failed: {e}")
            continue
    if last_err:
        raise last_err
    raise RuntimeError(f'No SSH driver succeeded for {host}')


def _platform_from_neighbor_string(platform):
    from utils.discovery_graph import classify_os_family
    return classify_os_family(platform_str=platform)


# ── LLDP/CDP neighbor normalization (NX-OS / IOS edge cases) ─────────────────
from utils.cisco_iface import (
    is_mac_like as _is_mac_like,
    normalize_cisco_iface as _normalize_interface_name,
    strip_mac_prefix as _strip_mac_prefix,
)

_LLDP_EMPTY_NAME = re.compile(
    r'^(?:not\s+advertised|not-advertised|null|none|n/?a|\.|-|unknown)$',
    re.I,
)


def _lldp_value_invalid(value: str) -> bool:
    if not value:
        return True
    return bool(_LLDP_EMPTY_NAME.match(str(value).strip()))


def _lldp_peer_hostname(system_name: str, chassis_id: str) -> str:
    """Resolve neighbor id when System Name is missing or not advertised (NX-OS)."""
    sn = (system_name or '').strip()
    if sn and not _lldp_value_invalid(sn):
        token = sn.split()[0].split('(')[0].strip()
        if token.lower() not in ('not', 'null', 'none'):
            return token
    cid = _strip_mac_prefix((chassis_id or '').strip())
    if cid and not _lldp_value_invalid(cid):
        if _is_mac_like(cid):
            return cid.lower().replace(':', '.')
        return cid.split('(')[0].strip()
    return ''


def _lldp_resolve_remote_port(port_id: str, port_description: str) -> str:
    """
    NX-OS often reports Port id as MAC when ifName TLV is absent; prefer Port Description.
    """
    desc = _normalize_interface_name(port_description)
    if desc:
        return desc
    pid = _normalize_interface_name(port_id)
    if pid and not _is_mac_like(pid):
        return pid
  # MAC or opaque port-id — unusable as interface name
    if port_id and not _is_mac_like(port_id):
        return str(port_id).strip()
    return ''


def _make_incomplete_observation(
    *,
    hostname: str = '',
    chassis_id: str = '',
    ip=None,
    platform: str = '',
    protocol: str = '',
    parse_source: str = '',
    gaps: list | None = None,
    parse_warning: str = '',
    raw_fragment: str = '',
    local_port: str = '',
    remote_port: str = '',
) -> dict:
    """Explicit incomplete discovery observation — never invents ports or edges."""
    gap_list = list(gaps or [])
    if not (local_port or '').strip() and 'local_port' not in gap_list:
        gap_list.append('local_port')
    warning = parse_warning or (
        'incomplete observation: ' + ', '.join(gap_list) if gap_list
        else 'incomplete observation'
    )
    return {
        'hostname': (hostname or '').strip(),
        'chassis_id': (chassis_id or '').strip(),
        'ip': ip,
        'local_port': (local_port or '').strip(),
        'remote_port': (remote_port or '').strip(),
        'platform': platform or '',
        'protocol': protocol or '',
        'parse_source': parse_source or '',
        'incomplete': True,
        'partial': True,
        'edge_eligible': False,
        'observation_kind': 'incomplete',
        'evidence_gaps': gap_list,
        'parse_warning': warning,
        'raw_fragment': (raw_fragment or '')[:500],
    }


def _finalize_neighbor(neigh: dict) -> dict | None:
    """Normalize ports/hostnames; drop records that cannot form an honest edge.

    Truth rules:
    - No peer identity → drop
    - Incomplete observations (flagged) are preserved with empty ports and edge_eligible=False
    - No local_port on a normal neighbor → drop (cannot attribute the adjacency)
    - Missing remote_port → keep as partial (empty string), never invent 'n/a'/'unknown'
    """
    host = _lldp_peer_hostname(
        neigh.get('hostname', ''),
        neigh.get('chassis_id', ''),
    )
    local_port = _normalize_interface_name(neigh.get('local_port', ''))
    remote_port = _lldp_resolve_remote_port(
        neigh.get('remote_port', ''),
        neigh.get('port_description', ''),
    )
    if _lldp_value_invalid(remote_port):
        remote_port = ''

    if neigh.get('incomplete') or neigh.get('observation_kind') == 'incomplete':
        # Incomplete evidence may lack hostname or local_port; never invent either.
        if not host and not local_port:
            return None
        gaps = list(neigh.get('evidence_gaps') or [])
        if not local_port and 'local_port' not in gaps:
            gaps.append('local_port')
        if not remote_port and 'remote_port' not in gaps:
            gaps.append('remote_port')
        if not host and 'hostname' not in gaps:
            gaps.append('hostname')
        out = dict(neigh)
        out['hostname'] = host or ''
        out['local_port'] = local_port or ''
        out['remote_port'] = remote_port or ''
        out['incomplete'] = True
        out['partial'] = True
        out['edge_eligible'] = False
        out['observation_kind'] = 'incomplete'
        out['evidence_gaps'] = gaps
        out['parse_warning'] = (
            neigh.get('parse_warning')
            or ('incomplete observation: ' + ', '.join(gaps))
        )
        if out.get('ip') and _lldp_value_invalid(str(out.get('ip'))):
            out['ip'] = None
        return out

    if not host:
        return None
    if not local_port:
        return None
    neigh = dict(neigh)
    neigh['hostname'] = host
    neigh['local_port'] = local_port
    neigh['remote_port'] = remote_port or ''
    neigh['edge_eligible'] = True
    gaps = []
    if not remote_port:
        gaps.append('remote_port')
        neigh['partial'] = True
    if gaps:
        neigh['evidence_gaps'] = gaps
        neigh['parse_warning'] = 'partial neighbor: ' + ', '.join(gaps)
    if neigh.get('ip') and _lldp_value_invalid(str(neigh.get('ip'))):
        neigh['ip'] = None
    return neigh


def _dedupe_neighbors(neighbors: list) -> list:
    """Prefer detail-parse rows over brief duplicates (same local port + peer)."""
    best: dict = {}
    score_detail = 4
    score_has_ip = 2
    score_ports = 1

    def _port_ok(value):
        s = (value or '').strip().lower()
        return bool(s) and s not in ('unknown', 'n/a', 'null', 'none', '-')

    def rank(n):
        s = 0
        if n.get('parse_source') == 'detail':
            s += score_detail
        if n.get('ip'):
            s += score_has_ip
        if _port_ok(n.get('local_port')):
            s += score_ports
        if _port_ok(n.get('remote_port')):
            s += score_ports
        return s

    for n in neighbors:
        key = (
            (n.get('local_port') or '').lower(),
            (n.get('hostname') or '').lower(),
            (n.get('protocol') or '').upper(),
        )
        if key not in best or rank(n) > rank(best[key]):
            best[key] = n
    return list(best.values())


def _operator_incomplete_observation(obs: dict) -> dict:
    """Sanitized incomplete row for API/UI — never invents ports; omits raw CLI body."""
    from utils.evidence_inspector import build_incomplete_observation_model

    o = obs if isinstance(obs, dict) else {}
    model = build_incomplete_observation_model(o)
    local_raw = str(o.get('local_port') or '').strip()
    remote_raw = str(o.get('remote_port') or '').strip()
    if local_raw.lower() in ('unknown', 'n/a', 'n\\a'):
        local_raw = ''
    if remote_raw.lower() in ('unknown', 'n/a', 'n\\a'):
        remote_raw = ''
    host = str(o.get('hostname') or '').strip()
    if host.lower() in ('unknown', 'n/a', 'n\\a'):
        host = ''
    return {
        'incomplete': True,
        'edge_eligible': False,
        'hostname': host,
        'protocol': str(o.get('protocol') or ''),
        'parse_source': str(o.get('parse_source') or ''),
        'local_port': local_raw,
        'remote_port': remote_raw,
        'local_port_display': model['ports']['local_port'],
        'remote_port_display': model['ports']['remote_port'],
        'evidence_gaps': list(o.get('evidence_gaps') or []),
        'parse_warning': str(o.get('parse_warning') or ''),
        'cable_claim': (model.get('classification') or {}).get('cable_claim') or (
            'incomplete observation — not a cable and not a map edge'
        ),
        'raw_fragment_present': bool(str(o.get('raw_fragment') or '').strip()),
    }


def _nodes_to_api_devices(nodes):
    devices = []
    for n in nodes:
        status = n.get('status', '')
        reachable = n.get('is_scanned', False) and not str(status).startswith('Failed')
        st = n.get('scan_state', '')
        if not st:
            if n.get('discovered_via') == 'Seed':
                st = 'seed'
            elif n.get('is_scanned'):
                st = 'scanned'
            elif str(status).startswith('Failed'):
                st = 'failed'
            else:
                st = 'neighbor_only'
        incompletes = [
            _operator_incomplete_observation(obs)
            for obs in (n.get('incomplete_observations') or [])
            if isinstance(obs, dict)
        ]
        devices.append({
            'id': n.get('id'),
            'hostname': n.get('id'),
            'host': n.get('ip'),
            'ip': n.get('ip'),
            'device_type': n.get('device_type', n.get('platform', '')),
            'platform': n.get('platform', ''),
            'serial': n.get('serial', ''),
            'serial_number': n.get('serial', ''),
            'depth': n.get('depth', 0),
            'reachable': reachable,
            'discovered_via': n.get('discovered_via', ''),
            'scan_state': st,
            'neighbor_evidence': n.get('neighbor_evidence', ''),
            'neighbor_evidence_note': n.get('neighbor_evidence_note', ''),
            'identity_conflict': bool(n.get('identity_conflict')),
            'chassis_conflict': bool(n.get('chassis_conflict')),
            'chassis_id': n.get('chassis_id') or '',
            'incomplete_observation_count': len(incompletes),
            'incomplete_observations': incompletes,
        })
    return devices


def _edges_to_api_links(edges):
    def _port_display(p):
        """Honest port labels for API — empty stays empty (never invent n/a/unknown)."""
        if p is None:
            return ''
        s = str(p).strip()
        if not s or s.lower() in ('unknown', 'null', 'none', 'n/a', 'n\\a', '-'):
            return ''
        return s

    return [{
        'from': e.get('from'),
        'to': e.get('to'),
        'local_port': _port_display(e.get('f_port')),
        'remote_port': _port_display(e.get('t_port')),
        'protocol': e.get('protocol', ''),
        'confidence': e.get('confidence', ''),
        'one_sided': bool(e.get('one_sided') or e.get('spoof_risk')),
        'spoof_risk': bool(e.get('spoof_risk') or e.get('one_sided')),
        'contradictions': list(e.get('contradictions') or []),
        'bundle_kind': e.get('bundle_kind') or '',
        'sources': list(e.get('sources') or []),
        'not_physical': bool(e.get('not_physical')),
        'layer': e.get('layer') or '',
        'edge_kind': e.get('edge_kind') or '',
        'lacp_collected': bool(e.get('lacp_collected')),
        'lacp_oper': e.get('lacp_oper') or '',
    } for e in edges]


def _fetch_neighbors(conn, hostname, dtype, protocol, log_func, cancel_check=None):
    """Collect CDP/LLDP neighbors with detail-first, brief CDP fallback for legacy IOS."""
    neighbors = []
    raw_outputs = []
    dtype_low = (dtype or '').lower()
    is_juniper = 'juniper' in dtype_low

    if protocol in ('CDP', 'BOTH') and not is_juniper:
        if log_func:
            log_func(f"[{hostname}] Fetching CDP neighbors…")
        try:
            cdp_out = _send_cli(conn, 'show cdp neighbors detail', 90, cancel_check)
            raw_outputs.append(cdp_out)
            neighbors.extend(_parse_cisco_cdp_detail(cdp_out, hostname, log_func))
            if not neighbors:
                brief = _send_cli(conn, 'show cdp neighbors', 60, cancel_check)
                raw_outputs.append(brief)
                neighbors.extend(_parse_cisco_cdp_brief(brief, hostname, log_func))
        except DiscoveryCancelled:
            raise
        except Exception as ex:
            if log_func:
                log_func(f"[{hostname}] CDP warning: {ex}")

    if protocol in ('LLDP', 'BOTH'):
        if log_func:
            log_func(f"[{hostname}] Fetching LLDP neighbors…")
        try:
            # For Juniper, try brief first (more compatible) then detail if needed
            # Some Junos versions don't support "show lldp neighbors detail"
            if is_juniper:
                try:
                    lldp_brief = _send_cli(conn, 'show lldp neighbors', 60, cancel_check)
                    raw_outputs.append(lldp_brief)
                    neighbors.extend(_parse_juniper_lldp_brief(lldp_brief, hostname, log_func))
                    if log_func:
                        log_func(f"[{hostname}] Junos LLDP brief found {len(neighbors)} neighbors")
                except DiscoveryCancelled:
                    raise
                except Exception as ex:
                    if log_func:
                        log_func(f"[{hostname}] Junos LLDP brief warning: {ex}")
                
                # If no neighbors from brief, try detail
                if not neighbors:
                    try:
                        lldp_detail = _send_cli(conn, 'show lldp neighbors detail', 90, cancel_check)
                        raw_outputs.append(lldp_detail)
                        neighbors.extend(_parse_juniper_lldp_detail(lldp_detail, hostname, log_func))
                        if log_func:
                            log_func(f"[{hostname}] Junos LLDP detail found {len(neighbors)} neighbors")
                    except DiscoveryCancelled:
                        raise
                    except Exception as ex:
                        if log_func:
                            log_func(f"[{hostname}] Junos LLDP detail warning: {ex}")
            else:
                # For Cisco, try detail first then brief
                lldp_out = _send_cli(conn, 'show lldp neighbors detail', 90, cancel_check)
                raw_outputs.append(lldp_out)
                neighbors.extend(_parse_cisco_lldp_detail(lldp_out, hostname, log_func))
                if not neighbors:
                    lldp_brief = _send_cli(conn, 'show lldp neighbors', 60, cancel_check)
                    raw_outputs.append(lldp_brief)
                    neighbors.extend(_parse_cisco_lldp_brief(lldp_brief, hostname, log_func))
        except DiscoveryCancelled:
            raise
        except Exception as ex:
            if log_func:
                log_func(f"[{hostname}] LLDP warning: {ex}")

    finalized = []
    for raw in neighbors:
        n = _finalize_neighbor(raw)
        if n:
            finalized.append(n)
    evidence = classify_neighbor_evidence(finalized, raw_outputs)
    return _dedupe_neighbors(finalized), evidence


def crawl_network_multi_seed(seeds, credentials, max_depth, protocol, config, log_func=None, *,
                            dry_run=False, inventory_basename=None, progress_callback=None,
                            cancel_check=None):
    """
    BFS crawl from one or more seeds.
    seeds: list of (host, device_type) tuples.
    """
    protocol = (protocol or 'Both').upper()
    if protocol == 'BOTH':
        protocol = 'BOTH'
    max_depth = int(max_depth or 2)
    dry_run = bool(dry_run)

    username = credentials.get('username')
    password = credentials.get('password')
    secret = credentials.get('secret')

    queue = []
    for host, dtype in seeds:
        if host:
            queue.append((host, dtype or '', 0))

    visited = set()
    discovered_nodes = {}
    discovered_edges = []
    from datetime import datetime, timezone
    crawl_observed_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    for host, dtype in seeds:
        if not host:
            continue
        key = host.lower()
        discovered_nodes[key] = {
            'id': host,
            'label': host,
            'ip': host,
            'platform': 'unknown',
            'device_type': dtype or '',
            'discovered_via': 'Seed',
            'depth': 0,
            'is_scanned': False,
            'serial': '',
            'scan_state': 'seed',
        }

    def _progress(**kwargs):
        if progress_callback:
            try:
                progress_callback(**kwargs)
            except Exception:
                pass

    cancelled = False
    overlay_links = []
    overlay_collected_any = False
    overlay_note = 'EVPN/VXLAN overlay is not collected'
    lacp_index = {}
    pc_summary = {}
    while queue:
        if cancel_check:
            try:
                if cancel_check():
                    cancelled = True
                    if log_func:
                        log_func('[Discovery] Cancelled by operator — returning partial graph')
                    break
            except Exception:
                pass
        curr_ip, curr_dtype, curr_depth = queue.pop(0)
        if curr_depth > max_depth:
            continue
        visited_key = curr_ip.lower()
        if visited_key in visited:
            continue

        if log_func:
            log_func(f"[{curr_ip}] Crawling hop {curr_depth} (max {max_depth})…")
        _progress(
            current_host=curr_ip,
            hop=curr_depth,
            devices_found=len({n.get('id') for n in discovered_nodes.values() if n.get('id')}),
            links_found=len(discovered_edges),
            queue_remaining=len(queue),
        )

        if dry_run:
            visited.add(visited_key)
            continue

        try:
            if cancel_check:
                try:
                    if cancel_check():
                        cancelled = True
                        if log_func:
                            log_func('[Discovery] Cancelled before SSH — returning partial graph')
                        break
                except Exception:
                    pass
            _ssh_cm = None
            try:
                _ssh_cm, conn, curr_dtype = _open_discovery_ssh(
                    curr_ip, curr_dtype, username, password, secret, log_func,
                    credentials.get('fallback_credentials'),
                )
                ver_output = _send_cli(conn, 'show version', 60, cancel_check)
                hostname = resolve_device_hostname(
                    conn, ver_output, curr_ip, curr_dtype, log_func=log_func,
                )
                hostname_lower = hostname.lower()
                curr_dtype = _detect_device_type(ver_output, curr_dtype)
                serial = _extract_serial(ver_output, curr_dtype)

                node_data = discovered_nodes.get(visited_key) or {}
                node_data.update({
                    'id': hostname,
                    'label': hostname,
                    'ip': curr_ip,
                    'depth': curr_depth,
                    'is_scanned': True,
                    'device_type': curr_dtype,
                    'serial': serial,
                    'os_source': 'scanned',
                    'scan_state': 'scanned',
                })

                if 'juniper' in curr_dtype.lower():
                    try:
                        chassis_out = _send_cli(conn, 'show chassis hardware', 60, cancel_check)
                        m = re.search(r'chassis\s+(\S+)', chassis_out, re.I)
                        node_data['platform'] = m.group(1) if m else 'Juniper'
                        if not serial:
                            for pat in (
                                r'[Ss]erial\s*[Nn]umber\s*:?\s*(\S+)',
                                r'\bSN:\s*(\S+)',
                            ):
                                sm = re.search(pat, chassis_out)
                                if sm:
                                    serial = sm.group(1).rstrip(',')
                                    node_data['serial'] = serial
                                    break
                    except DiscoveryCancelled:
                        raise
                    except Exception:
                        node_data['platform'] = 'Juniper'
                else:
                    m = re.search(
                        r'Model\s+Number\s*:\s*(\S+)|cisco\s+(\S+)\s+\([^)]+\)\s+processor',
                        ver_output, re.I,
                    )
                    node_data['platform'] = (
                        (m.group(1) or m.group(2)) if m else 'Cisco'
                    )

                neighbors, neighbor_evidence = _fetch_neighbors(
                    conn, hostname, curr_dtype, protocol, log_func, cancel_check,
                )
                def _hop_send(cmd, timeout=60):
                    return _send_cli(conn, cmd, timeout, cancel_check)
                from modules.overlay_collector import collect_overlay
                from utils.lacp_oper import collect_lacp
                ov = collect_overlay(conn, hostname, curr_dtype, _hop_send)
                if ov.get('collected'):
                    overlay_collected_any = True
                    overlay_note = ov.get('overlay_note') or overlay_note
                    overlay_links.extend(ov.get('links') or [])
                idx, summary = collect_lacp(conn, curr_dtype, _hop_send)
                lacp_index.update(idx)
                pc_summary.update(summary)
                node_data['neighbor_evidence'] = neighbor_evidence
                node_data['neighbor_evidence_note'] = NEIGHBOR_EVIDENCE_NOTES.get(
                    neighbor_evidence, '',
                )
                # Preserve incomplete parse evidence without promoting to nodes/edges
                node_data['incomplete_observations'] = [
                    n for n in neighbors
                    if n.get('incomplete') or n.get('edge_eligible') is False
                ]
                discovered_nodes[visited_key] = node_data
                discovered_nodes[hostname_lower] = node_data

                for neigh in neighbors:
                    if neigh.get('incomplete') or neigh.get('edge_eligible') is False:
                        continue
                    n_host = normalize_neighbor_hostname(
                        neigh['hostname'], neigh.get('ip'),
                    )
                    n_ip = neigh.get('ip')
                    n_key = n_host.lower()
                    n_ip_key = n_ip.lower() if n_ip else ''

                    existing_node = discovered_nodes.get(n_key) or (
                        discovered_nodes.get(n_ip_key) if n_ip_key else None
                    )
                    if not existing_node:
                        n_dtype = _platform_from_neighbor_string(neigh.get('platform', ''))
                        os_src = 'cdp' if neigh.get('protocol') == 'CDP' else 'lldp'
                        if n_dtype in ('', 'unknown'):
                            os_src = os_src + ',unclassified_platform'
                        new_node = {
                            'id': n_host,
                            'label': n_host,
                            'ip': n_ip or 'unknown',
                            'platform': neigh.get('platform', 'unknown'),
                            'device_type': n_dtype,
                            'discovered_via': neigh.get('protocol', ''),
                            'depth': curr_depth + 1,
                            'is_scanned': False,
                            'serial': '',
                            'os_source': os_src,
                            'scan_state': 'neighbor_only',
                        }
                        discovered_nodes[n_key] = new_node
                        if n_ip_key:
                            discovered_nodes[n_ip_key] = new_node
                    else:
                        new_node = existing_node

                    fp = (neigh.get('local_port') or '').strip()
                    tp = (neigh.get('remote_port') or '').strip()
                    # No local port → refuse to invent an edge
                    if not fp:
                        continue
                    edge_exists = any(
                        (
                            (e['from'].lower() == hostname_lower and e['to'].lower() == n_key)
                            or (e['from'].lower() == n_key and e['to'].lower() == hostname_lower)
                        )
                        and e.get('f_port') == fp and e.get('t_port') == tp
                        for e in discovered_edges
                    )
                    if not edge_exists:
                        from utils.discovery_graph import make_observation_evidence
                        from utils.juniper_iface import is_junos_irb_or_l3_svi

                        rem_label = tp if tp else '(remote port unobserved)'
                        observed_at = (
                            neigh.get('collected_at')
                            or crawl_observed_at
                        )
                        vendor = 'juniper' if 'juniper' in str(neigh.get('platform') or '').lower() else (
                            'cisco' if 'cisco' in str(neigh.get('platform') or '').lower()
                            or str(neigh.get('protocol') or '').upper() == 'CDP'
                            else ''
                        )
                        not_phys = bool(
                            neigh.get('not_physical')
                            or is_junos_irb_or_l3_svi(fp)
                            or is_junos_irb_or_l3_svi(tp)
                        )
                        evidence_item = make_observation_evidence(
                            protocol=str(neigh.get('protocol') or ''),
                            vendor=vendor,
                            command=str(neigh.get('command') or ''),
                            evidence_type='neighbor',
                            collected_at=observed_at,
                            local_port=fp,
                            remote_port=tp,
                            raw_fragment=str(
                                neigh.get('raw_fragment') or neigh.get('raw_evidence') or ''
                            ),
                            port_role=str(neigh.get('port_role') or ''),
                            not_physical=not_phys,
                            parse_source=str(neigh.get('parse_source') or ''),
                            platform=str(neigh.get('platform') or ''),
                        )
                        edge = {
                            'from': hostname,
                            'to': n_host,
                            'f_port': fp,
                            't_port': tp,
                            'label': f"{neigh['protocol']}\n{fp} ↔ {rem_label}",
                            'type': 'standard',
                            'protocol': neigh['protocol'],
                            'discovery': str(neigh.get('protocol') or '').lower(),
                            'collected_at': observed_at,
                            'evidence': [evidence_item],
                            'vendor': vendor,
                        }
                        if neigh.get('port_role'):
                            edge['port_role'] = neigh['port_role']
                        if not_phys:
                            edge['not_physical'] = True
                            edge['layer'] = 'l3-logical'
                            edge['edge_kind'] = 'irb-adjacency'
                            edge['label'] = (
                                f"{neigh['protocol']} (IRB/L3 — not a cable)\n{fp} ↔ {rem_label}"
                            )
                        if neigh.get('partial') or not tp:
                            edge['partial'] = True
                            edge['evidence_gaps'] = list(
                                neigh.get('evidence_gaps') or ['remote_port']
                            )
                        if neigh.get('raw_fragment') or neigh.get('raw_evidence'):
                            edge['raw_evidence'] = (
                                neigh.get('raw_fragment') or neigh.get('raw_evidence')
                            )
                        discovered_edges.append(edge)

                    if curr_depth < max_depth and n_ip and not dry_run:
                        if n_ip_key not in visited and n_key not in visited:
                            ssh_type = _ssh_type_for_neighbor(
                                neigh, new_node.get('device_type') or n_dtype,
                            )
                            if not ssh_type:
                                ssh_type = ''  # multi-driver try on connect
                            queue.append((n_ip, ssh_type, curr_depth + 1))

                visited.add(visited_key)
                if log_func:
                    log_func(f"[{curr_ip}] Scan completed.")
            finally:
                if _ssh_cm is not None:
                    try:
                        _ssh_cm.__exit__(None, None, None)
                    except Exception:
                        pass

        except DiscoveryCancelled:
            cancelled = True
            if log_func:
                log_func('[Discovery] Cancelled mid-CLI — returning partial graph')
            break
        except Exception as e:
            from utils.discovery_profiles import classify_discovery_failure
            fail_kind = classify_discovery_failure(e)
            if log_func:
                log_func(f"[WARNING] Discovery {fail_kind} on {curr_ip}: {e}")
            if visited_key in discovered_nodes:
                discovered_nodes[visited_key]['status'] = f"{fail_kind}: {str(e)[:80]}"
                discovered_nodes[visited_key]['is_scanned'] = False
                discovered_nodes[visited_key]['scan_state'] = fail_kind
            # Do not add to visited — transient failures may succeed on re-queue

    raw_nodes = []
    seen_ids = set()
    for node in discovered_nodes.values():
        nid = node.get('id')
        if nid and nid not in seen_ids:
            raw_nodes.append(node)
            seen_ids.add(nid)

    from utils.discovery_graph import canonicalize_discovery_graph
    from utils.lacp_oper import apply_lacp_to_edges
    final_nodes, discovered_edges, validation = canonicalize_discovery_graph(
        raw_nodes, discovered_edges,
    )
    discovered_edges = apply_lacp_to_edges(discovered_edges, lacp_index, pc_summary)
    discovered_edges.extend(overlay_links)
    if cancelled:
        validation = dict(validation)
        validation['partial'] = True
        warnings = list(validation.get('warnings') or [])
        warnings.append('crawl cancelled by operator')
        validation['warnings'] = warnings

    if log_func:
        log_func(
            f"[Discovery] Finished: {len(final_nodes)} nodes, "
            f"{len(discovered_edges)} links."
        )
        if validation.get('warnings'):
            log_func(
                f"[Discovery] Graph validation: {validation.get('warnings')}"
            )

    from utils.output_paths import CAT_DISCOVERY, path_in_run, prepare_run_output, slugify, write_run_manifest
    paths = prepare_run_output(CAT_DISCOVERY, slugify(f'depth{max_depth}_{protocol}'))
    reports_dir = paths['run_dir']
    if inventory_basename:
        inv_name = inventory_basename
        inv_path = os.path.join(reports_dir, inv_name)
    else:
        inv_name = 'discovered_inventory.json'
        inv_path = path_in_run(paths, inv_name)
    try:
        with open(inv_path, 'w', encoding='utf-8') as f:
            from utils.discovery_schema import annotate_export
            json.dump(annotate_export({
                'nodes': final_nodes,
                'edges': discovered_edges,
                'devices': _nodes_to_api_devices(final_nodes),
                'links': _edges_to_api_links(discovered_edges),
                'timestamp': datetime.now().isoformat(),
                'max_depth': max_depth,
                'protocol': protocol,
                'cancelled': cancelled,
                'partial': bool(validation.get('partial') or cancelled),
                'collection_status': (
                    'cancelled' if cancelled else (
                        'partial' if validation.get('partial') else 'complete'
                    )
                ),
                'overlay_collected': overlay_collected_any,
                'overlay_note': overlay_note,
                'overlay_links': overlay_links,
            }), f, indent=2)
        if log_func:
            log_func(f"[Discovery] Inventory JSON: {inv_path}")
    except Exception as je:
        if log_func:
            log_func(f"[WARNING] Could not save inventory JSON: {je}")
        inv_path = ''

    html_file = ''
    try:
        html_file = path_in_run(paths, 'discovery_map.html')
        _generate_discovery_html(
            html_file, final_nodes, discovered_edges,
            extra_meta={
                'partial': bool(validation.get('partial') or cancelled),
                'cancelled': cancelled,
                'collection_status': (
                    'cancelled' if cancelled else (
                        'partial' if validation.get('partial') else 'complete'
                    )
                ),
                'failed_hosts': validation.get('failed_hosts') or [],
                'overlay_collected': overlay_collected_any,
                'overlay_note': overlay_note,
                'collected_at': crawl_observed_at,
            },
        )
        if log_func:
            log_func(f"[Discovery] Topology map: {html_file}")
    except Exception as he:
        if log_func:
            log_func(f"[WARNING] Topology HTML failed: {he}")

    seed_label = seeds[0][0] if seeds else 'unknown'
    txt_file = path_in_run(paths, 'report.txt')
    try:
        result_preview = {
            'discovered_nodes': final_nodes,
            'discovered_edges': discovered_edges,
            'timestamp': datetime.now().isoformat(),
        }
        with open(txt_file, 'w', encoding='utf-8') as tf:
            tf.write(_format_discovery_report(result_preview, seed_label))
    except OSError as te:
        if log_func:
            log_func(f"[WARNING] Discovery TXT report failed: {te}")
        txt_file = ''

    write_run_manifest(paths, {
        'inventory_path': inv_path,
        'html_path': html_file,
        'txt_path': txt_file,
        'nodes': len(final_nodes),
        'edges': len(discovered_edges),
    })

    if log_func:
        log_func(f"[Discovery] Output folder: {reports_dir}")

    devices_api = _nodes_to_api_devices(final_nodes)
    incomplete_total = sum(
        int(d.get('incomplete_observation_count') or 0) for d in devices_api
    )
    if incomplete_total and log_func:
        log_func(
            f"[Discovery] Incomplete observations retained (not links): {incomplete_total}"
        )

    result_data = {
        'discovered_nodes': final_nodes,
        'discovered_edges': discovered_edges,
        'devices': devices_api,
        'links': _edges_to_api_links(discovered_edges),
        'incomplete_observation_count': incomplete_total,
        'inventory_json_path': inv_path,
        'json_path': inv_path,
        'topology_path': html_file,
        'html_report': html_file,
        'timestamp': datetime.now().isoformat(),
        'report_path': txt_file,
        'output_folder': reports_dir,
        'validation': validation,
        'validation_warnings': validation.get('warnings', []),
        'partial': bool(validation.get('partial') or cancelled),
        'cancelled': cancelled,
        'failed_hosts': validation.get('failed_hosts') or [],
        'collection_status': 'cancelled' if cancelled else (
            'partial' if validation.get('partial') else 'complete'
        ),
        'overlay_collected': overlay_collected_any,
        'overlay_note': overlay_note,
        'overlay_links': overlay_links,
    }
    return result_data


def _build_demo_discovery_data(seed_hosts, max_depth, log_func=None):
    """Synthetic lab topology for offline UI validation (no SSH)."""
    if log_func:
        log_func('[Discovery] DEMO MODE — generating sample topology (no SSH).')
    seeds = seed_hosts or ['10.0.0.1']
    primary = seeds[0]
    nodes = [
        {'id': 'CORE-NXOS-01', 'label': 'CORE-NXOS-01', 'ip': primary, 'platform': 'N9K-C93180YC',
         'device_type': 'cisco_nxos', 'depth': 0, 'is_scanned': True, 'serial': 'DEMO-NX001',
         'discovered_via': 'Seed', 'scan_state': 'seed'},
        {'id': 'DIST-IOS-02', 'label': 'DIST-IOS-02', 'ip': '10.0.0.2', 'platform': 'C9300-48P',
         'device_type': 'cisco_ios', 'depth': 1, 'is_scanned': True, 'serial': 'DEMO-IOS002',
         'discovered_via': 'CDP', 'scan_state': 'scanned'},
        {'id': 'ACCESS-IOS-03', 'label': 'ACCESS-IOS-03', 'ip': '10.0.0.3', 'platform': 'C2960X',
         'device_type': 'cisco_ios', 'depth': 2, 'is_scanned': True, 'serial': 'DEMO-IOS003',
         'discovered_via': 'CDP', 'scan_state': 'scanned'},
        {'id': 'EDGE-JUNOS-04', 'label': 'EDGE-JUNOS-04', 'ip': '10.0.0.4', 'platform': 'EX4300-48T',
         'device_type': 'juniper_junos', 'depth': 1, 'is_scanned': True, 'serial': 'DEMO-JN004',
         'discovered_via': 'LLDP', 'scan_state': 'scanned'},
        {'id': 'SPINE-NXOS-05', 'label': 'SPINE-NXOS-05', 'ip': '10.0.0.5', 'platform': 'Nexus7000',
         'device_type': 'cisco_nxos', 'depth': 1, 'is_scanned': False, 'serial': 'DEMO-NX005',
         'discovered_via': 'LLDP', 'scan_state': 'neighbor_only'},
    ]
    edges = [
        {'from': 'CORE-NXOS-01', 'to': 'DIST-IOS-02', 'f_port': 'Eth1/1', 't_port': 'Gi1/0/1',
         'protocol': 'CDP', 'label': 'CDP'},
        {'from': 'CORE-NXOS-01', 'to': 'EDGE-JUNOS-04', 'f_port': 'Eth1/2', 't_port': 'ge-0/0/0',
         'protocol': 'LLDP', 'label': 'LLDP'},
        {'from': 'DIST-IOS-02', 'to': 'ACCESS-IOS-03', 'f_port': 'Gi1/0/48', 't_port': 'Gi0/1',
         'protocol': 'CDP', 'label': 'CDP'},
        {'from': 'CORE-NXOS-01', 'to': 'SPINE-NXOS-05', 'f_port': 'Eth1/3', 't_port': 'Eth2/1',
         'protocol': 'LLDP', 'label': 'LLDP'},
        {'from': 'CORE-NXOS-01', 'to': '10.0.0.5', 'f_port': 'nve1', 't_port': 'nve1',
         'protocol': 'EVPN', 'label': 'EVPN', 'layer': 'overlay', 'edge_kind': 'nve-peer',
         'not_physical': True, 'overlay_kind': 'vxlan-nve', 'demo': True,
         'sources': ['demo show nve peers']},
    ]
    if int(max_depth or 2) < 2:
        nodes = [n for n in nodes if n['depth'] <= 1]
        edges = [e for e in edges if e['to'] != 'ACCESS-IOS-03']

    from utils.output_paths import CAT_DISCOVERY, path_in_run, prepare_run_output, write_run_manifest
    paths = prepare_run_output(CAT_DISCOVERY, 'demo')
    reports_dir = paths['run_dir']
    html_file = path_in_run(paths, 'discovery_demo_map.html')
    _generate_discovery_html(
        html_file, nodes, edges,
        extra_meta={
            'overlay_collected': True,
            'overlay_note': 'Demo EVPN/NVE peers from fixture CLI (not live). Overlay edges are not cables.',
            'collection_status': 'complete',
        },
    )
    inv_path = path_in_run(paths, 'discovered_inventory_demo.json')
    with open(inv_path, 'w', encoding='utf-8') as f:
        from utils.discovery_schema import annotate_export
        json.dump(annotate_export({
            'nodes': nodes,
            'edges': edges,
            'devices': _nodes_to_api_devices(nodes),
            'links': _edges_to_api_links(edges),
            'demo': True,
            'demo_mode': True,
            'cancelled': False,
            'partial': False,
            'collection_status': 'complete',
            'overlay_collected': True,
            'overlay_note': 'Demo EVPN/NVE peers from fixture CLI (not live). Overlay edges are not cables.',
            'overlay_links': [e for e in edges if e.get('layer') == 'overlay'],
            'timestamp': datetime.now().isoformat(),
        }), f, indent=2)
    write_run_manifest(paths, {'inventory_path': inv_path, 'html_path': html_file, 'demo_mode': True})
    txt_file = path_in_run(paths, 'report.txt')
    try:
        demo_preview = {
            'discovered_nodes': nodes,
            'discovered_edges': edges,
            'timestamp': datetime.now().isoformat(),
        }
        with open(txt_file, 'w', encoding='utf-8') as tf:
            tf.write(_format_discovery_report(demo_preview, primary))
        write_run_manifest(paths, {
            'inventory_path': inv_path,
            'html_path': html_file,
            'txt_path': txt_file,
            'demo_mode': True,
        })
    except OSError:
        txt_file = html_file
    if log_func:
        log_func(f'[Discovery] Demo output folder: {reports_dir}')

    return {
        'discovered_nodes': nodes,
        'discovered_edges': edges,
        'devices': _nodes_to_api_devices(nodes),
        'links': _edges_to_api_links(edges),
        'inventory_json_path': inv_path,
        'json_path': inv_path,
        'topology_path': html_file,
        'html_report': html_file,
        'timestamp': datetime.now().isoformat(),
        'demo_mode': True,
        'report_path': txt_file,
        'output_folder': reports_dir,
        'cancelled': False,
        'partial': False,
        'collection_status': 'complete',
        'overlay_collected': True,
        'overlay_note': 'Demo EVPN/NVE peers from fixture CLI (not live). Overlay edges are not cables.',
        'overlay_links': [e for e in edges if e.get('layer') == 'overlay'],
    }


# BFS Discovery Crawler (plugin contract — single seed)
def run(device, credentials, params, config, log_func):
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'cisco_ios')
    depth = params.get('depth', params.get('max_depth', 2))
    protocol = params.get('protocol', 'Both')

    if params.get('demo_mode'):
        result_data = _build_demo_discovery_data([host], depth, log_func)
        return build_json(host, 'success', result_data)

    result_data = crawl_network_multi_seed(
        [(host, device_type)], credentials, depth, protocol, config, log_func,
    )
    report_path = result_data.get('report_path', '')
    if report_path:
        summary = (
            f"Discovered {len(result_data.get('devices', []))} devices & "
            f"{len(result_data.get('links', []))} links from seed {host}."
        )
        append_to_master_report(METADATA['plugin_id'], host, 'success', summary, report_path)
    return build_json(host, 'success', result_data)


# ── Cisco CDP Parser ─────────────────────────────────────────────────────────
_CISCO_NEIGHBOR_DISABLED_RE = re.compile(
    r'(?:'
    r'feature\s+(?:lldp|cdp)\s+is\s+(?:not\s+enabled|disabled)'
    r'|(?:lldp|cdp)\s+is\s+(?:not\s+enabled|disabled)'
    r'|%\s*invalid\s+command'
    r'|syntax\s+error[^\n]*(?:lldp|cdp)'
    r')',
    re.I,
)


def cisco_neighbor_collection_disabled(output):
    """True when CLI shows LLDP/CDP is off or the show command is invalid."""
    text = output or ''
    return bool(_CISCO_NEIGHBOR_DISABLED_RE.search(text))


NEIGHBOR_EVIDENCE_NOTES = {
    'collected': 'Neighbors parsed from CDP/LLDP on this scan.',
    'none_collected': (
        'Zero neighbors parsed. This is lack of CDP/LLDP evidence, '
        'not proof the device is isolated or that the network is empty.'
    ),
    'protocol_disabled': (
        'Neighbor protocol appears disabled or the show command is invalid. '
        'Not a fabric census and not an empty network.'
    ),
}


def classify_neighbor_evidence(neighbors, raw_outputs=None):
    """Empty neighbor list is lack of evidence, not isolation."""
    if neighbors:
        return 'collected'
    texts = raw_outputs or []
    if any(cisco_neighbor_collection_disabled(t) for t in texts if t):
        return 'protocol_disabled'
    return 'none_collected'


def _empty_if_neighbor_protocol_disabled(output, protocol, log_func):
    if not cisco_neighbor_collection_disabled(output):
        return False
    if log_func:
        log_func(
            f'[Parser] {protocol} not enabled or invalid command — '
            'no neighbors (not a parse failure)'
        )
    return True


_CDP_BRIEF_IFACE_START = re.compile(
    r'^(?:Eth(?:ernet)?|Gi(?:g(?:abitEthernet)?)?|Te(?:n(?:GigabitEthernet|GigE)?)?|'
    r'Fo(?:rtyGigabitEthernet)?|Hu(?:ndredGigE)?|Fa(?:s(?:tEthernet)?)?|'
    r'Po(?:rt-channel)?|mgmt|Vl(?:an)?|Twe(?:ntyFiveGigE)?)\b',
    re.I,
)


_CDP_PORT_TOKEN = re.compile(
    r'((?:Ethernet|Eth|GigabitEthernet|Gig|Gi|FastEthernet|Fas|Fa|'
    r'TenGigabitEthernet|TenGigE|Ten|Te|TwentyFiveGigE|Twe|'
    r'FortyGigabitEthernet|For|Fo|HundredGigE|Hun|Hu|'
    r'Port-channel|Por|Po)\s*\S+)$',
    re.I,
)


def _cdp_brief_split_platform_port(token: str) -> tuple[str, str]:
    """Split 'C9300-48P Gig 1/0/48' when Platform and Port ID have a single space."""
    s = (token or '').strip()
    if not s:
        return '', ''
    m = _CDP_PORT_TOKEN.search(s)
    if not m:
        return s, ''
    port = m.group(1).strip()
    plat = s[: m.start()].strip()
    return plat, port


def _cdp_brief_iface_start(token: str) -> bool:
    return bool(_CDP_BRIEF_IFACE_START.match((token or '').strip()))


def _parse_cisco_cdp_brief(output, local_hostname, log_func):
    """Parse 'show cdp neighbors' table (legacy IOS when detail is empty).

    Device-ID wrapping: when the hostname exceeds the Device ID column, IOS
    prints the name on its own line and the remaining columns on the next line
    (leading spaces). Hostname-only lines never become neighbors by themselves.
    """
    if _empty_if_neighbor_protocol_disabled(output, 'CDP', log_func):
        return []
    neighbors = []
    pending_host = ''

    def _emit(neigh_host, local_port, remote_port, platform, neigh_ip):
        if any(x in (platform or '').lower() for x in (
            'phone', 'ata', 'camera', 'ap ', 'air-ap', 'air-', 'access point',
        )):
            return
        if not neigh_host or not local_port:
            return
        neighbors.append({
            'hostname': neigh_host,
            'ip': neigh_ip,
            'local_port': local_port,
            'remote_port': remote_port,
            'platform': platform or 'Cisco',
            'protocol': 'CDP',
            'parse_source': 'brief',
        })

    for raw in output.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith('device') or '---' in line:
            continue
        low = line.lower()
        if low.startswith('capability') or re.match(r'^\([A-Z]\)\s', line):
            continue
        parts = re.split(r'\s{2,}|\t', line)
        try:
            # Continuation of a wrapped Device ID
            if pending_host and parts and _cdp_brief_iface_start(parts[0]):
                local_port = parts[0].strip()
                plat, port = _cdp_brief_split_platform_port(parts[-1])
                if not port and len(parts) > 1:
                    port = parts[-1].strip()
                    plat = parts[-2].strip() if len(parts) > 2 else plat
                platform = plat or (parts[-2].strip() if len(parts) > 2 else 'Cisco')
                _emit(pending_host, local_port, port, platform, None)
                pending_host = ''
                continue
            if len(parts) < 5:
                if (
                    len(parts) == 1
                    and not _cdp_brief_iface_start(parts[0])
                    and not parts[0].startswith('(')
                ):
                    pending_host = parts[0].split('(')[0].strip()
                else:
                    pending_host = ''
                continue
            neigh_host = parts[0].split('(')[0].strip()
            local_port = parts[1].strip() if len(parts) > 1 else ''
            plat, port = _cdp_brief_split_platform_port(parts[-1])
            if port:
                platform = plat or (parts[-2].strip() if len(parts) > 3 else 'Cisco')
                remote_port = port
            else:
                remote_port = parts[-1].strip()
                platform = parts[-2].strip() if len(parts) > 3 else 'Cisco'
            m_ip = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', parts[0])
            neigh_ip = m_ip.group(1) if m_ip else None
            pending_host = ''
            _emit(neigh_host, local_port, remote_port, platform, neigh_ip)
        except Exception as e:
            pending_host = ''
            if log_func:
                log_func(f'[Parser WARNING] CDP brief line: {e}')
    return neighbors


_CISCO_BRIEF_IFACE = re.compile(
    r'^(?:Eth(?:ernet)?|Gi(?:gabitEthernet)?|Te(?:nGigabitEthernet)?|'
    r'Fo(?:rtyGigabitEthernet)?|Hu(?:ndredGigE)?|Fa(?:stEthernet)?|'
    r'Po(?:rt-channel)?|mgmt|Vl(?:an)?)\S*',
    re.I,
)


def _cisco_brief_noise_line(line: str) -> bool:
    """Skip comment/corruption lines that are not LLDP table rows."""
    s = (line or '').lstrip()
    if not s:
        return True
    if s[:1] in '#!*@':
        return True
    return False


def _looks_like_cisco_iface_token(token: str) -> bool:
    t = (token or '').strip()
    return bool(t and _CISCO_BRIEF_IFACE.match(t))


def _parse_cisco_lldp_brief(output, local_hostname, log_func):
    """Parse 'show lldp neighbors' brief table (IOS/IOS-XE/NX-OS)."""
    if _empty_if_neighbor_protocol_disabled(output, 'LLDP', log_func):
        return []
    neighbors = []
    _skip_headers = {
        'local intf', 'local interface', 'neighbor', 'vlan', 'device id',
        'system name', 'port id', 'capability', 'platform',
    }
    for line in output.splitlines():
        line = line.strip()
        if not line or '---' in line or _cisco_brief_noise_line(line):
            continue
        low = line.lower()
        if low.startswith('capability') or (line.startswith('(') and 'router' in low):
            continue
        if re.match(r'^\([A-Z]\)\s', line):
            continue
        if 'device id' in low and 'local' in low:
            continue
        if any(h in low for h in ('local intf', 'system name')) and 'port id' in low:
            continue
        parts = re.split(r'\s{2,}|\t+', line)
        if len(parts) < 2:
            parts = line.split()
        if len(parts) < 2:
            continue
        try:
            p0 = parts[0].split('(')[0].strip()
            p1 = parts[1].split('(')[0].strip() if len(parts) > 1 else ''
            if p0.lower() in _skip_headers or p1.lower() in _skip_headers:
                continue
            # NX-OS: Local Intf first (Eth1/1  SPINE-01  Eth1/2  120)
            if re.match(r'^(Eth|Gi|Te|Fo|Hu|mgmt|Po|Ethernet|Gigabit|TenGig)', p0, re.I):
                local_port = p0
                neigh_host = p1
                remote_port = parts[2].strip() if len(parts) > 2 and not parts[2].isdigit() else ''
            elif len(parts) >= 5 and parts[2].isdigit():
                # IOS / IOS-XE: Device ID  Local Intf  Hold-time  Capability  Port ID
                neigh_host = p0
                local_port = p1
                remote_port = parts[-1].strip()
            else:
                neigh_host = p0
                if _lldp_value_invalid(neigh_host) and len(parts) > 3:
                    neigh_host = parts[3].split('(')[0].strip()
                local_port = parts[1].strip() if len(parts) > 1 else ''
                remote_port = parts[2].strip() if len(parts) > 2 else ''
            if _is_mac_like(remote_port) and len(parts) > 3:
                alt = parts[3].strip()
                if not _is_mac_like(alt):
                    remote_port = alt
            if (remote_port or '').isdigit():
                # Hold-time/TTL leaked into Port ID when the column is missing
                remote_port = ''
            if not _looks_like_cisco_iface_token(local_port):
                continue
            if not neigh_host or neigh_host[:1] in '#!*@':
                continue
            neighbors.append({
                'hostname': neigh_host,
                'ip': None,
                'local_port': local_port,
                'remote_port': remote_port,
                'platform': 'Cisco Switch',
                'protocol': 'LLDP',
                'parse_source': 'brief',
            })
        except Exception:
            pass
    return neighbors


def _parse_cisco_cdp_detail(output, local_hostname, log_func):
    if _empty_if_neighbor_protocol_disabled(output, 'CDP', log_func):
        return []
    neighbors = []
    blocks = output.split("-------------------------")
    for block in blocks:
        if not block.strip() or "Device ID" not in block:
            continue
            
        try:
            # Device ID / Hostname
            m_id = re.search(r'Device ID\s*:\s*(\S+)', block, re.I)
            if not m_id:
                continue
            neigh_host = m_id.group(1).split('(')[0] if '(' in m_id.group(1) else m_id.group(1) # remove domains/FQDNS
            
            # Management IP Address
            m_ip = re.search(r'IP\s+address\s*:\s*(\S+)|IPv4\s+Address\s*:\s*(\S+)', block, re.I)
            neigh_ip = (m_ip.group(1) or m_ip.group(2)) if m_ip else None
            
            # Local & Remote Interface — CDP only (never invent unknown/n/a)
            m_lint = re.search(r'Interface\s*:\s*([^,\s]+)', block, re.I)
            m_rint = re.search(r'Port\s+ID\s*\(outgoing\s+port\)\s*:\s*(\S+)', block, re.I)
            local_port = (m_lint.group(1) if m_lint else '').rstrip(',')
            remote_port = m_rint.group(1) if m_rint else ''

            # Platform model
            m_plat = re.search(r'Platform\s*:\s*([^,\n]+)', block, re.I)
            platform = m_plat.group(1).strip() if m_plat else "Cisco"
            
            # Skip IP Phones/PCs (observability filter)
            plat_low = platform.lower()
            if any(x in plat_low for x in (
                'ip phone', 'ata', 'desktop', 'camera', 'air-ap', 'wireless ap',
                'access point', 'meraki mr',
            )):
                continue

            if not local_port:
                # Truncated / incomplete CDP detail: keep explicit observation, not silence
                gaps = ['local_port']
                if not remote_port:
                    gaps.append('remote_port')
                neighbors.append(_make_incomplete_observation(
                    hostname=neigh_host,
                    ip=neigh_ip,
                    platform=platform,
                    protocol='CDP',
                    parse_source='detail',
                    gaps=gaps,
                    parse_warning=(
                        'incomplete CDP detail: missing Interface'
                        + ('' if remote_port else ' and Port ID')
                    ),
                    raw_fragment=block.strip()[:500],
                    local_port='',
                    remote_port='',
                ))
                continue
                
            neighbors.append({
                "hostname": neigh_host,
                "ip": neigh_ip,
                "local_port": local_port,
                "remote_port": remote_port,
                "platform": platform,
                "protocol": "CDP",
                "parse_source": "detail",
                "raw_fragment": block.strip()[:500],
            })
        except Exception as e:
            if log_func:
                log_func(f"[Parser WARNING] Failed to parse CDP block: {e}")
                
    return neighbors

# ── Cisco LLDP Parser ────────────────────────────────────────────────────────
def _split_cisco_lldp_detail_blocks(output: str) -> list:
    """Keep Local Interface/Intf with Chassis id when IOS prints local first.

    IOS 12.x: Local Interface, then Chassis id (often after a dash ruler).
    NX-OS: Chassis id, then Local Intf / Local Port id.
    Splitting only on Chassis id orphans the local port — incomplete, not a cable.
    """
    if re.search(r'-{8,}', output or ''):
        chunks = re.split(r'-{8,}', output)
    else:
        chunks = re.split(
            r'(?=Local\s+(?:Interface|Intf|Port id)\s*:)|(?=Chassis id\s*:)',
            output or '',
            flags=re.I,
        )
    merged = []
    buf = ''

    def _has_local(text: str) -> bool:
        return bool(re.search(r'Local\s+(?:Interface|Intf|Port id)\s*:', text, re.I))

    def _has_chassis(text: str) -> bool:
        return bool(re.search(r'Chassis id\s*:', text, re.I))

    for chunk in chunks:
        if not (chunk or '').strip():
            continue
        if not buf:
            buf = chunk
            continue
        buf_l, buf_c = _has_local(buf), _has_chassis(buf)
        cur_l, cur_c = _has_local(chunk), _has_chassis(chunk)
        if (buf_l and not buf_c and cur_c) or (buf_c and not buf_l and cur_l):
            buf = buf + '\n' + chunk
            merged.append(buf)
            buf = ''
            continue
        merged.append(buf)
        buf = chunk
    if buf.strip():
        merged.append(buf)
    return merged


def _parse_cisco_lldp_detail(output, local_hostname, log_func):
    """
    Parse 'show lldp neighbors detail' for IOS/NX-OS.
    Handles: Local Intf vs Local Port id; System Name not advertised; Port id = MAC.
    """
    if _empty_if_neighbor_protocol_disabled(output, 'LLDP', log_func):
        return []
    neighbors = []
    blocks = _split_cisco_lldp_detail_blocks(output)
    for block in blocks:
        if not block.strip():
            continue
        try:
            m_ch = re.search(r'Chassis id\s*:\s*(?:mac\s+)?(\S+)', block, re.I)
            chassis_id = _strip_mac_prefix(m_ch.group(1).strip() if m_ch else '')

            m_host = re.search(r'System\s+Name\s*:\s*(.+?)(?:\r?\n|$)', block, re.I)
            system_name = m_host.group(1).strip() if m_host else ''

            neigh_host = _lldp_peer_hostname(system_name, chassis_id)
            if not neigh_host:
                continue

            m_ip = re.search(
                r'Management\s+Address\s*:\s*(\d+\.\d+\.\d+\.\d+)',
                block,
                re.I,
            )
            if not m_ip:
                m_ip = re.search(
                    r'(?:IPv4\s+)?Address\s*:\s*(\d+\.\d+\.\d+\.\d+)',
                    block,
                    re.I,
                )
            neigh_ip = m_ip.group(1) if m_ip else None

            m_lint = re.search(
                r'Local\s+(?:Interface|Intf|Port id)\s*:\s*(\S+)',
                block,
                re.I,
            )
            m_rint = re.search(
                r'(?:^|\n)[ \t]*Port\s+id\s*:\s*(?:mac\s+)?(\S+)',
                block,
                re.I,
            )
            m_pdesc = re.search(r'Port\s+Description\s*:\s*(\S+)', block, re.I)

            local_port = m_lint.group(1) if m_lint else ''
            port_id = m_rint.group(1) if m_rint else ''
            port_description = m_pdesc.group(1) if m_pdesc else ''

            m_desc = re.search(r'System\s+Description\s*:\s*([^\n]+)', block, re.I)
            desc = m_desc.group(1).lower() if m_desc else ''
            if 'nexus' in desc or 'n5k' in desc or 'n7k' in desc or 'nx-os' in desc:
                platform = 'Cisco Nexus'
            elif 'juniper' in desc:
                platform = 'Juniper'
            else:
                platform = 'Cisco Switch'

            remote_port = _lldp_resolve_remote_port(port_id, port_description) or port_id

            if not local_port:
                # Keep resolved remote evidence when present; never invent a local port
                resolved_remote = _lldp_resolve_remote_port(port_id, port_description)
                gaps = ['local_port']
                if not resolved_remote:
                    gaps.append('remote_port')
                neighbors.append(_make_incomplete_observation(
                    hostname=neigh_host,
                    chassis_id=chassis_id,
                    ip=neigh_ip,
                    platform=platform,
                    protocol='LLDP',
                    parse_source='detail',
                    gaps=gaps,
                    parse_warning='incomplete LLDP detail: missing Local Intf/Port id',
                    raw_fragment=block.strip()[:500],
                    local_port='',
                    remote_port=resolved_remote or '',
                ))
                continue

            neighbors.append({
                'hostname': neigh_host,
                'chassis_id': chassis_id,
                'ip': neigh_ip,
                'local_port': local_port,
                'remote_port': remote_port,
                'port_description': port_description,
                'platform': platform,
                'protocol': 'LLDP',
                'parse_source': 'detail',
            })
        except Exception as e:
            if log_func:
                log_func(f'[Parser WARNING] Failed to parse LLDP block: {e}')

    return neighbors

# ── Juniper LLDP Parser ──────────────────────────────────────────────────────
def _parse_juniper_lldp_detail(output, local_hostname, log_func):
    """
    Parse Junos LLDP detail output with multiple format support and fallback mechanisms.
    
    Supports:
    - Standard Junos LLDP format
    - Older Junos 13.X format
    - Brief format fallback
    - Multiple parsing patterns for robustness
    """
    neighbors = []
    
    if not output or len(output.strip()) < 10:
        if log_func:
            log_func(f"[{local_hostname}] WARNING: Empty or invalid LLDP output")
        return neighbors
    
    # Try standard parsing first
    blocks = output.split("Local Interface")
    for block in blocks:
        if not block.strip():
            continue
            
        # Try to find system name with multiple patterns
        m_host = None
        hostname_patterns = [
            r'System\s+name\s*:\s*(\S+)',
            r'System\s+Name\s*:\s*(\S+)',
            r'Chassis\s+ID\s*:\s*(\S+)',
            r'Chassis\s+id\s*:\s*(\S+)',
        ]
        
        for pattern in hostname_patterns:
            m_host = re.search(pattern, block, re.I)
            if m_host:
                break
        
        if not m_host:
            # Try to find any hostname-like string (no capture group)
            m_host = re.search(r'[a-zA-Z][a-zA-Z0-9\-\.]{2,}', block)
            if not m_host:
                continue

        raw_host = m_host.group(1) if m_host.lastindex else m_host.group(0)
        neigh_host = raw_host.split('(')[0] if '(' in raw_host else raw_host
        
        # Management IP - multiple patterns
        m_ip = None
        ip_patterns = [
            r'Management\s+address\s*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'Management\s+Address\s*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'Management\s+IP\s*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'IP\s*address\s*:\s*(\d+\.\d+\.\d+\.\d+)',
        ]
        
        for pattern in ip_patterns:
            m_ip = re.search(pattern, block, re.I)
            if m_ip:
                break
        
        neigh_ip = m_ip.group(1) if m_ip else None
        
        # Local Port - multiple patterns
        m_lint = None
        local_port_patterns = [
            r'Local\s+Interface\s*:\s*(\S+)',
            r'Local\s+interface\s*:\s*(\S+)',
            r'Interface\s*:\s*(\S+)',
            r'Local\s+Port\s*:\s*(\S+)',
        ]
        
        for pattern in local_port_patterns:
            m_lint = re.search(pattern, block, re.I)
            if m_lint:
                break
        
        local_port = m_lint.group(1) if m_lint else ""
        if local_port in (':',) or _lldp_value_invalid(local_port):
            header_m = re.match(
                r'^\s*:\s*((?:ge|xe|et|fe|ae|irb|vlan|me)-[\w./]+|ae\d+(?:\.[\w]+)?|irb\.\w+|vlan\.\w+)',
                block,
                re.I,
            )
            if header_m:
                local_port = header_m.group(1)
            else:
                local_port = ""
        
        # Remote Port - multiple patterns
        m_rint = None
        remote_port_patterns = [
            r'Port\s+ID\s*:\s*(\S+)',
            r'Port\s+Description\s*:\s*(\S+)',
            r'Port\s+id\s*:\s*(\S+)',
            r'Remote\s+Port\s*:\s*(\S+)',
        ]
        
        for pattern in remote_port_patterns:
            m_rint = re.search(pattern, block, re.I)
            if m_rint:
                break
        
        port_id = m_rint.group(1) if m_rint else ''
        m_pdesc = re.search(r'Port\s+Description\s*:\s*(\S+)', block, re.I)
        port_description = m_pdesc.group(1) if m_pdesc else ''
        remote_port = _lldp_resolve_remote_port(port_id, port_description) or port_id or ""
        
        # Platform detection
        platform = "Juniper"
        m_platform = re.search(r'Platform\s*:\s*(\S+)', block, re.I)
        if m_platform:
            platform = m_platform.group(1)

        from utils.juniper_iface import classify_junos_port_role, is_junos_irb_or_l3_svi
        role = classify_junos_port_role(local_port)
        row = {
            "hostname": neigh_host,
            "ip": neigh_ip,
            "local_port": local_port,
            "remote_port": remote_port,
            "platform": platform,
            "protocol": "LLDP",
            "parse_source": "detail",
            "port_role": role,
            "command": "show lldp neighbors detail",
            "raw_fragment": ("Local Interface" + block)[:500],
        }
        if is_junos_irb_or_l3_svi(local_port) or is_junos_irb_or_l3_svi(remote_port):
            row['not_physical'] = True
            row['partial'] = True
            row['evidence_gaps'] = ['physical_link']
            row['parse_warning'] = (
                'Junos IRB/L3 SVI in LLDP detail — routed evidence, not a cable'
            )
        if not local_port:
            continue
        neighbors.append(row)
    
    # Fallback: If no neighbors found with standard parsing, try brief format
    if not neighbors:
        if log_func:
            log_func(f"[{local_hostname}] Standard LLDP parsing failed, trying brief format fallback")
        neighbors = _parse_juniper_lldp_brief(output, local_hostname, log_func)
    
    # Fallback: If still no neighbors, try table format parsing
    if not neighbors:
        if log_func:
            log_func(f"[{local_hostname}] Brief parsing failed, trying table format fallback")
        neighbors = _parse_juniper_lldp_table(output, local_hostname, log_func)
    
    # Fallback: If still no neighbors, try alternative parsing
    if not neighbors:
        if log_func:
            log_func(f"[{local_hostname}] Table parsing failed, trying alternative parsing")
        neighbors = _parse_juniper_lldp_alternative(output, local_hostname, log_func)
    
    return neighbors


def _parse_juniper_lldp_brief(output, local_hostname, log_func):
    """Parse Junos `show lldp neighbors` (brief). Older Junos has no detail command."""
    from utils.juniper_iface import classify_junos_port_role, is_junos_irb_or_l3_svi

    neighbors = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.lower().startswith('local') or '---' in line.lower():
            continue
        if line.lower().startswith('lldp'):
            continue
        parts = re.split(r'\s{2,}|\t+', line)
        if len(parts) < 3:
            continue
        try:
            local_port = parts[0].strip()
            # Accept physical, AE, me, and IRB/vlan.* for evidence — classify later
            if not re.match(
                r'^(ge|xe|et|fe|ae|me|irb|vlan)[-.]', local_port, re.I
            ) and not local_port.lower().startswith('ae'):
                continue
            if len(parts) >= 5 and _is_mac_like(parts[1].strip()):
                # Older Junos: no Parent Interface column — col1 is Chassis Id
                chassis_id = parts[1].strip()
                p2, p3 = parts[2].strip(), parts[3].strip()
                if p2.isdigit() and (
                    re.match(r'^(ge|xe|et|fe|ae|me|irb|vlan)[-.]', p3, re.I)
                    or p3.lower().startswith('ae')
                ):
                    remote_port = p3
                else:
                    remote_port = p2
                system_name = parts[4].strip()
            elif len(parts) >= 5:
                chassis_id = parts[2].strip()
                remote_port = parts[3].strip()
                system_name = parts[4].strip()
            elif len(parts) == 4 and parts[1].strip() in ('-',):
                chassis_id = parts[2].strip()
                maybe = parts[3].strip()
                # Incomplete row: Port info empty, System Name shifted left
                if re.match(
                    r'^(ge|xe|et|fe|ae|me|irb|vlan)[-.]', maybe, re.I
                ) or maybe.lower().startswith('ae'):
                    remote_port = maybe
                    system_name = ''
                else:
                    remote_port = ''
                    system_name = maybe
            elif len(parts) == 4:
                chassis_id = parts[1].strip()
                remote_port = parts[2].strip()
                system_name = parts[3].strip()
            else:
                chassis_id = parts[1].strip()
                remote_port = parts[2].strip() if len(parts) > 2 else ''
                system_name = ''
            if chassis_id in ('-',):
                continue
            m_ip = re.search(r'(\d+\.\d+\.\d+\.\d+)', chassis_id)
            neigh_ip = m_ip.group(1) if m_ip else None
            neigh_host = system_name if system_name and system_name not in ('-',) else chassis_id.split('(')[0].strip()
            if not neigh_host or neigh_host in ('-', local_port):
                continue
            role = classify_junos_port_role(local_port)
            row = {
                'hostname': neigh_host,
                'ip': neigh_ip,
                'local_port': local_port,
                'remote_port': remote_port or '',
                'platform': 'Juniper',
                'protocol': 'LLDP',
                'parse_source': 'brief',
                'port_role': role,
            }
            if is_junos_irb_or_l3_svi(local_port) or is_junos_irb_or_l3_svi(remote_port):
                row['not_physical'] = True
                row['partial'] = True
                row['evidence_gaps'] = ['physical_link']
                row['parse_warning'] = (
                    'Junos IRB/L3 SVI local or remote port — routed evidence, not a cable'
                )
                row['raw_fragment'] = line[:500]
            neighbors.append(row)
        except Exception as e:
            if log_func:
                log_func(f"[Parser WARNING] Junos LLDP brief line: {e}")
    return neighbors


def _parse_juniper_lldp_alternative(output, local_hostname, log_func):
    """Alternative parsing for non-standard Junos LLDP output.

    Never seeds hostname/remote_port as 'unknown'. Incomplete blocks stay incomplete.
    """
    neighbors = []
    lines = output.splitlines()
    current_neighbor = None

    def _flush(current):
        if not current:
            return
        host = (current.get('hostname') or '').strip()
        local_port = (current.get('local_port') or '').strip()
        remote_port = (current.get('remote_port') or '').strip()
        if _lldp_value_invalid(host):
            host = ''
        if _lldp_value_invalid(remote_port):
            remote_port = ''
        if not local_port:
            return
        if not host:
            neighbors.append(_make_incomplete_observation(
                hostname='',
                ip=current.get('ip'),
                platform='Juniper',
                protocol='LLDP',
                parse_source='alternative',
                gaps=['hostname'] + ([] if remote_port else ['remote_port']),
                parse_warning='incomplete Junos alternative LLDP: missing System Name',
                raw_fragment=str(current.get('raw_fragment') or '')[:500],
                local_port=local_port,
                remote_port='',
            ))
            return
        row = {
            'hostname': host,
            'ip': current.get('ip'),
            'local_port': local_port,
            'remote_port': remote_port,
            'platform': 'Juniper',
            'protocol': 'LLDP',
            'parse_source': 'alternative',
        }
        if not remote_port:
            row['partial'] = True
            row['evidence_gaps'] = ['remote_port']
            row['parse_warning'] = 'partial neighbor: remote_port'
        neighbors.append(row)

    for line in lines:
        line = line.strip()
        if not line or _cisco_brief_noise_line(line):
            continue

        # Detect new neighbor block - expanded to include xe-, et-, ge-, and other Junos interface types
        if re.match(r'^[a-z]{2,}-\d+/\d+/\d+', line, re.I):
            _flush(current_neighbor)
            current_neighbor = {
                'hostname': '',
                'ip': None,
                'local_port': line,
                'remote_port': '',
                'platform': 'Juniper',
                'protocol': 'LLDP',
                'raw_fragment': line,
            }
            continue

        if current_neighbor:
            current_neighbor['raw_fragment'] = (
                (current_neighbor.get('raw_fragment') or '') + '\n' + line
            )[:500]
            if not current_neighbor['hostname']:
                m_host = re.search(
                    r'(?:System\s+Name|System\s+name)\s*:\s*(\S+)',
                    line,
                    re.I,
                )
                if m_host and not _lldp_value_invalid(m_host.group(1)):
                    current_neighbor['hostname'] = m_host.group(1).split('(')[0].strip()

            if not current_neighbor['ip']:
                m_ip = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if m_ip:
                    current_neighbor['ip'] = m_ip.group(1)

            if not current_neighbor['remote_port']:
                m_port = re.search(r'Port\s*(?:ID|Id|info)?\s*[:\s]+(\S+)', line, re.I)
                if m_port and not _lldp_value_invalid(m_port.group(1)):
                    maybe = m_port.group(1).strip()
                    if re.match(
                        r'^(ge|xe|et|fe|ae|me|irb|vlan)[-.]', maybe, re.I
                    ) or maybe.lower().startswith('ae'):
                        current_neighbor['remote_port'] = maybe

    _flush(current_neighbor)
    return neighbors


def _parse_juniper_lldp_table(output, local_hostname, log_func):
    """Parse Junos LLDP table format (show lldp neighbors without detail)."""
    neighbors = []
    lines = output.splitlines()

    # Look for table header and parse table rows
    for line in lines:
        line = line.strip()

        # Skip header lines
        if not line or line.lower().startswith('local') or line.lower().startswith('lldp') or '---' in line.lower():
            continue
        if _cisco_brief_noise_line(line):
            continue

        # Try to parse as table format: Local Interface, Parent Interface, Chassis Id, Port info, System Name
        parts = re.split(r'\s{2,}|\t+', line)
        if len(parts) >= 3:
            try:
                # Extract local interface (first column)
                local_port = parts[0].strip()

                # Extract chassis ID (third column typically)
                chassis_id = parts[2].strip() if len(parts) > 2 else ''

                # Extract system name (fifth column typically)
                system_name = parts[4].strip() if len(parts) > 4 else ''

                # Extract port info (fourth column typically) — never default to 'unknown'
                port_info = parts[3].strip() if len(parts) > 3 else ''
                if _lldp_value_invalid(port_info):
                    port_info = ''

                # Extract IP from chassis_id if present
                m_ip = re.search(r'(\d+\.\d+\.\d+\.\d+)', chassis_id)
                neigh_ip = m_ip.group(1) if m_ip else None

                # Use system name as hostname, fallback to chassis_id
                neigh_host = system_name if system_name else (
                    chassis_id.split('(')[0].strip() if chassis_id else ''
                )
                if _lldp_value_invalid(neigh_host):
                    neigh_host = ''

                if not local_port:
                    continue
                if not neigh_host or neigh_host == local_port:
                    neighbors.append(_make_incomplete_observation(
                        hostname='',
                        chassis_id=chassis_id,
                        ip=neigh_ip,
                        platform='Juniper',
                        protocol='LLDP',
                        parse_source='table',
                        gaps=['hostname'],
                        parse_warning='incomplete Junos LLDP table: missing System Name',
                        raw_fragment=line[:500],
                        local_port=local_port,
                        remote_port='',
                    ))
                    continue
                row = {
                    'hostname': neigh_host,
                    'ip': neigh_ip,
                    'local_port': local_port,
                    'remote_port': port_info,
                    'platform': 'Juniper',
                    'protocol': 'LLDP',
                    'parse_source': 'table',
                }
                if not port_info:
                    row['partial'] = True
                    row['evidence_gaps'] = ['remote_port']
                    row['parse_warning'] = 'partial neighbor: remote_port'
                neighbors.append(row)
            except Exception as e:
                if log_func:
                    log_func(f"[Parser WARNING] Junos LLDP table line: {e}")

    return neighbors

# ── Report Formatter ──────────────────────────────────────────────────────────
def _format_discovery_report(data, host):
    nodes = data.get('discovered_nodes', [])
    edges = data.get('discovered_edges', [])
    ts = data.get('timestamp', datetime.now().isoformat())
    
    lines = []
    lines.append("=" * 70)
    lines.append("NETWORK DISCOVERY & NEIGHBOR SCAN REPORT")
    lines.append("=" * 70)
    lines.append(f"Seed Host:        {host}")
    lines.append(f"Scan Finished:    {ts}")
    lines.append(f"Discovered Nodes: {len(nodes)}")
    lines.append(f"Discovered Links: {len(edges)}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("DISCOVERED DEVICE CATALOG")
    lines.append("-" * 70)
    lines.append(f"{'Hostname':<22} | {'Management IP':<15} | {'Model/Platform':<15} | {'Hop':<4} | {'State':<10}")
    lines.append("-" * 70)
    for n in sorted(nodes, key=lambda x: x["depth"]):
        scanned = "Scanned" if n.get("is_scanned") else "Discovered"
        lines.append(f"{n['id']:<22} | {n['ip']:<15} | {n.get('platform','unknown'):<15} | {n['depth']:<4} | {scanned:<10}")
        
    lines.append("")
    lines.append("-" * 70)
    lines.append("DISCOVERED NEIGHBOR CONNECTIONS (PHYSICAL LINKS)")
    lines.append("-" * 70)
    for e in edges:
        lines.append(f"  [Link] {e['from']} [{e['f_port']}] ↔ {e['to']} [{e['t_port']}]  ({e['protocol']})")
        
    lines.append("=" * 70)
    return "\n".join(lines)

# ── Vis.js Discovery Map Template Generator ──────────────────────────────────
def _generate_discovery_html(filepath, nodes, edges, extra_meta=None):
    from utils.discovery_map_formatter import generate_discovery_html
    generate_discovery_html(filepath, nodes, edges, extra_meta=extra_meta)

# ── Class Interface (Discovery API / vlan_checker_web) ───────────────────────
class NetworkDiscoveryPlugin:
    """REST API bridge for multi-seed discovery jobs."""

    def execute(self, device, credentials, params, config, log_func=None):
        seed_hosts = params.get('seed_hosts') or [device.get('host')]
        if isinstance(seed_hosts, str):
            seed_hosts = [s.strip() for s in re.split(r'[,\n]+', seed_hosts) if s.strip()]

        max_depth = int(params.get('max_depth', params.get('depth', 2)))
        protocol = params.get('protocol', 'Both')
        protos = params.get('protocols')
        if isinstance(protos, list):
            up = [p.upper() for p in protos]
            if 'CDP' in up and 'LLDP' in up:
                protocol = 'Both'
            elif 'CDP' in up:
                protocol = 'CDP'
            elif 'LLDP' in up:
                protocol = 'LLDP'

        if params.get('demo_mode'):
            data = _build_demo_discovery_data(seed_hosts, max_depth, log_func)
            host = seed_hosts[0] if seed_hosts else 'demo'
            return build_json(host, 'success', data)

        seeds = []
        for raw in seed_hosts:
            parsed = _parse_seed_entry(raw)
            if parsed[0]:
                seeds.append(parsed)

        if not seeds:
            return build_json('unknown', 'error', {}, error='No valid seed hosts')

        inv_base = None
        job_id = params.get('job_id')
        if job_id:
            inv_base = f'discovered_inventory_{job_id}.json'
            try:
                from utils.task_control_plane import bind_session_key
                bind_session_key(job_id)
            except Exception:
                pass
        def _progress_cb(**kwargs):
            jid = params.get('job_id')
            if not jid:
                return
            try:
                import vlan_checker_web as vcw
                with vcw._job_store_lock:
                    job = vcw._discovery_jobs.get(jid)
                    if job:
                        prog = job.get('progress') or {}
                        prog.update(kwargs)
                        if kwargs.get('last_log_line'):
                            lines = prog.get('last_log_lines') or []
                            lines.append(kwargs['last_log_line'])
                            prog['last_log_lines'] = lines[-20:]
                        job['progress'] = prog
            except Exception:
                pass

        def _cancel_check():
            jid = params.get('job_id')
            try:
                from utils.task_control_plane import should_abort
                if should_abort():
                    return True
            except Exception:
                pass
            if not jid:
                return False
            try:
                import vlan_checker_web as vcw
                with vcw._job_store_lock:
                    job = vcw._discovery_jobs.get(jid) or {}
                    return bool(job.get('cancel'))
            except Exception:
                return False

        result_data = crawl_network_multi_seed(
            seeds, credentials, max_depth, protocol, config, log_func,
            dry_run=bool(params.get('dry_run')),
            inventory_basename=inv_base,
            progress_callback=_progress_cb,
            cancel_check=_cancel_check,
        )
        host = seeds[0][0]
        report_path = result_data.get('report_path', '')
        if report_path:
            summary = (
                f"Discovered {len(result_data.get('devices', []))} devices & "
                f"{len(result_data.get('links', []))} links."
            )
            append_to_master_report(METADATA['plugin_id'], host, 'success', summary, report_path)
        return build_json(host, 'success', result_data)


# ── Validation Helper ────────────────────────────────────────────────────────
def validate_plugin():
    errors = []
    required_meta_keys = ['plugin_id', 'display_name', 'version', 'category', 'required_params']
    for key in required_meta_keys:
        if key not in METADATA:
            errors.append(f"Missing METADATA key: {key}")
    if 'run' not in globals() or not callable(globals()['run']):
        errors.append("Missing required 'run' function")
    return len(errors) == 0, errors

if __name__ == "__main__":
    is_valid, errors = validate_plugin()
    if is_valid:
        print(f"✅ Plugin '{METADATA['plugin_id']}' is valid!")
    else:
        for err in errors:
            print(f"❌ {err}")
        exit(1)
