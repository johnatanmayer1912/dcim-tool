"""
modules/routing_analyzer/parser.py
------------------------------------
Parse routing table outputs for Cisco IOS/IOS-XE, NX-OS, and Juniper Junos.

Strategy (in order):
  1. TextFSM template (ntc-templates style) — most accurate
  2. Regex with NX-OS / Junos / legacy IOS branches — robust fallback
  3. Return empty list — never raise

Supported output variants:
  Cisco IOS / IOS-XE:
    - Standard 'show ip route' (all codes: C S O B D R E L M)
    - Multi-line via entries (continuation lines with 4-space indent)
    - Classful + CIDR
    - VRF-aware (same format, different header)
  Cisco NX-OS:
    - 'show ip route' (NX-OS uses '/' prefix style, no 'is directly connected')
    - Tag / route-preference annotation '... [110/1]'
  Juniper Junos:
    - Classic text 'show route' (inet.0 table)
    - Multi-line next-hop blocks (> to X via Y)
    - Protocol names: Direct, Local, Static, OSPF, BGP, ISIS
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys


# ---------------------------------------------------------------------------
# TextFSM wrapper (graceful if ntc-templates / textfsm not installed)
# ---------------------------------------------------------------------------

def _try_textfsm(template_path: Path, output: str) -> List[Dict[str, Any]]:
    """Run TextFSM template; return [] on any error."""
    if not template_path.exists():
        return []
    try:
        from textfsm import TextFSM
        with open(template_path, encoding='utf-8') as f:
            tmpl = TextFSM(f)
        rows = tmpl.ParseText(output)
        headers = tmpl.header
        return [{headers[i].lower(): (row[i] if i < len(row) else '') for i in range(len(headers))}
                for row in rows]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Protocol code → canonical name
# ---------------------------------------------------------------------------

PROTO_CODE_MAP: Dict[str, str] = {
    'C': 'Connected',
    'L': 'Local',
    'S': 'Static',
    'R': 'RIP',
    'M': 'Mobile',
    'B': 'BGP',
    'D': 'EIGRP',
    'EX': 'EIGRP-External',
    'O': 'OSPF',
    'OI': 'OSPF-InterArea',
    'IA': 'OSPF-InterArea',
    'ON1': 'OSPF-NSSA-Ext1',
    'ON2': 'OSPF-NSSA-Ext2',
    'N1': 'OSPF-NSSA-Ext1',
    'N2': 'OSPF-NSSA-Ext2',
    'OE1': 'OSPF-Ext1',
    'OE2': 'OSPF-Ext2',
    'E1': 'OSPF-Ext1',
    'E2': 'OSPF-Ext2',
    'i': 'ISIS',
    'su': 'ISIS-Summary',
    'L1': 'ISIS-L1',
    'L2': 'ISIS-L2',
    'ia': 'ISIS-InterArea',
    'K1': 'ODR',
    'K': 'ODR',
    'G': 'DHCP',
    '+': 'Replicated',
    '%': 'Next-Table',
    'P': 'Periodic-downloaded',
    # NX-OS text protocol names (full words from *via proto column)
    'direct': 'Connected',
    'local': 'Local',
    'static': 'Static',
    'ospf': 'OSPF',
    'bgp': 'BGP',
    'eigrp': 'EIGRP',
    'isis': 'ISIS',
    'rip': 'RIP',
    'connected': 'Connected',
}


def _canon_proto(code: str) -> str:
    """Map a protocol code to a canonical readable name.

    Handles:
      - Single-char Cisco codes: C, L, S, O, B, D ...
      - Space-separated multi-token codes: O IA, O N1, O N2, D EX, i L1, i L2
      - NX-OS process-suffixed names: ospf-101, bgp-65000, eigrp-100, isis-1
      - Junos protocol strings: Direct, Static, OSPF, BGP ...
      - Mixed-case inputs
    """
    code = code.strip().rstrip('*').strip() if code else ''
    if not code:
        return 'Unknown'

    # Handle space-separated two-token IOS codes (O IA, O N1, D EX, i L1, etc.)
    # Must be checked before single-char lookup to avoid 'O' matching instead of 'O IA'
    _MULTI_TOKEN_MAP = {
        'O IA': 'OSPF-InterArea',
        'O IA': 'OSPF-InterArea',
        'O E1': 'OSPF-Ext1',
        'O E2': 'OSPF-Ext2',
        'O N1': 'OSPF-NSSA-Ext1',
        'O N2': 'OSPF-NSSA-Ext2',
        'D EX': 'EIGRP-External',
        'i L1': 'ISIS-L1',
        'i L2': 'ISIS-L2',
        'i su': 'ISIS-Summary',
        'i ia': 'ISIS-InterArea',
    }
    # Normalised space check (collapse multiple spaces)
    code_norm = re.sub(r'\s+', ' ', code)
    if code_norm in _MULTI_TOKEN_MAP:
        return _MULTI_TOKEN_MAP[code_norm]
    if code_norm.upper() in {k.upper(): v for k, v in _MULTI_TOKEN_MAP.items()}:
        return {k.upper(): v for k, v in _MULTI_TOKEN_MAP.items()}[code_norm.upper()]

    # Exact match first (case-sensitive for single-char codes)
    if code in PROTO_CODE_MAP:
        return PROTO_CODE_MAP[code]
    # Case-insensitive exact match (Junos 'Direct', 'Local', etc.)
    low = code.lower()
    if low in PROTO_CODE_MAP:
        return PROTO_CODE_MAP[low]
    # NX-OS process-suffixed: ospf-101 -> ospf, bgp-65000 -> bgp, eigrp-100 -> eigrp
    _NXOS_PREFIX_RE = re.compile(r'^([a-z]+)-\d+$')
    m = _NXOS_PREFIX_RE.match(low)
    if m:
        base = m.group(1)
        if base in PROTO_CODE_MAP:
            return PROTO_CODE_MAP[base]
    # Prefix match for multi-char codes like 'OI', 'OE1', 'EX'
    for k, v in PROTO_CODE_MAP.items():
        if low == k.lower():
            return v
    # IS-IS with hyphen — Junos emits 'IS-IS' as the protocol string
    if low == 'is-is':
        return 'ISIS'
    return code


# ---------------------------------------------------------------------------
# Cisco IOS / IOS-XE / NX-OS regex parser
# ---------------------------------------------------------------------------

# Match:  C    10.0.0.0/8 is directly connected, GigabitEthernet0/0
# Also:     C    10.0.0.0/8 is directly connected, GigabitEthernet0/0.100
_RX_IOS_CONNECTED = re.compile(
    r'^(?P<code>[A-Za-z*+%]+(?:\s+[A-Za-z0-9]+)?)\s+'
    r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
    r'\s+is\s+directly\s+connected,\s*(?P<iface>\S+)',
    re.MULTILINE,
)

# Match:  C    10.0.0.0/8 [0/0] is directly connected, GigabitEthernet0/0
# Some IOS versions include [0/0] for connected routes
_RX_IOS_CONNECTED_AD = re.compile(
    r'^(?P<code>[A-Za-z*+%]+(?:\s+[A-Za-z0-9]+)?)\s+'
    r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
    r'\s+\[(?P<ad>\d+)/(?P<metric>\d+)\]\s+is\s+directly\s+connected,\s*(?P<iface>\S+)',
    re.MULTILINE,
)

# Match:  O    10.1.0.0/24 [110/2] via 192.168.1.1, 00:05:11, Gi0/0
# Also:   S    0.0.0.0/0 [1/0] via 10.0.0.1
# Also:   O    10.1.0.0/24 [110/2] via 192.168.1.1, Gi0/0 (no uptime)
# Also:   O    10.1.0.0/24 [110/2] via 192.168.1.1, Gi0/0, 00:05:11 (interface first)
# Uptime format: 00:05:11, 1d02h, 3w5d, etc.
_RX_IOS_VIA = re.compile(
    r'^(?P<code>[A-Za-z*+%]+(?:\s+[A-Za-z0-9]+)?)\s+'
    r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
    r'(?:\s+\[(?P<ad>\d+)/(?P<metric>\d+)\])?\s+'
    r'via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?:,\s*(?P<field1>[^,]+))?(?:,\s*(?P<field2>[^,]+))?',
    re.MULTILINE,
)

# Multi-line continuation for IOS:
#   O    10.1.0.0/24 [110/2] via 192.168.1.1, ...
#                            via 192.168.1.2, ...   <-- continuation (indent, no net)
_RX_IOS_CONTINUATION = re.compile(
    r'^\s{5,}'
    r'via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?:,\s*(?P<field1>[^,]+))?(?:,\s*(?P<field2>[^,]+))?',
    re.MULTILINE,
)

# Classic classful: C  10.1.1.0  255.255.255.0  [...]  interface
_RX_IOS_LEGACY_CLASSFUL = re.compile(
    r'^(?P<code>[A-Z*]+)\s+'
    r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+'
    r'(?P<mask>255\.\d+\.\d+\.\d+)\s+'
    r'\[(?P<ad>\d+)/(?P<metric>\d+)\]\s+'
    r'via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
    re.MULTILINE,
)

# NX-OS local route:  L  10.0.0.1/32, ubest/mbest: 1/0, attached
_RX_NXOS_LOCAL = re.compile(
    r'^(?P<code>[A-Za-z*]+)\s+'
    r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}),\s*'
    r'ubest/mbest:',
    re.MULTILINE,
)

# NX-OS via:    *via 10.1.1.1, Eth1/1, [110/40], ...
_RX_NXOS_VIA = re.compile(
    r'^\s+\*?via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}),'
    r'\s+(?P<iface>\S+),\s+'
    r'\[(?P<ad>\d+)/(?P<metric>\d+)\],\s*'
    r'(?P<uptime>\S+),\s*(?P<proto>\S+)',
    re.MULTILINE,
)


def _parse_cisco_regex(output: str, platform: str = 'cisco_ios') -> List[Dict[str, Any]]:
    """Regex-based Cisco IOS/XE/NX-OS route parser with multi-line support.

    NX-OS can emit two different output styles:
      Modern (ubest/mbest):  10.1.0.0/24, ubest/mbest: 1/0
                                 *via 10.0.0.1, Eth1/1, [110/20], 00:01:00, ospf-101
      Legacy / IOS-like:     C    192.168.1.0/24 is directly connected, Vlan10
                             S    0.0.0.0/0 [1/0] via 10.0.0.1, Ethernet1/1
    Both styles are handled.  Protocol process IDs (ospf-101, bgp-65000, eigrp-100)
    are normalised to their canonical names.

    Also handles minimal IOS switch format (L2 switches with only a default-gateway):
      Default gateway is 10.10.10.1 Host Gateway ... ICMP redirect cache is empty

    NOTE: the minimal-switch early-return guard only fires when the output contains
    BOTH 'Default gateway is' AND 'ICMP redirect cache'. It does NOT fire for NX-OS
    output that merely contains the phrase 'Default gateway is' without the ICMP
    line — NX-OS output does not contain 'ICMP redirect cache' in the route table.
    """
    routes: List[Dict[str, Any]] = []
    if not output:
        return routes

    plat = (platform or '').lower()
    is_nxos = (
        'nxos' in plat
        or 'nx-os' in plat
        or 'nexus' in plat
        or plat in ('cisco_nxos', 'nxos')
    )

    # Handle minimal IOS switch format ONLY for non-NX-OS platforms.
    # This check must be after is_nxos so NX-OS output is never short-circuited.
    if not is_nxos and 'Default gateway is' in output and 'ICMP redirect cache' in output:
        gw_match = re.search(r'Default gateway is (\S+)', output)
        if gw_match:
            routes.append({
                'protocol': 'Static',
                'network': '0.0.0.0/0',
                'next_hop': gw_match.group(1),
                'metric': '0',
                'admin_distance': '1',
                'interface': '',
                'uptime': '',
            })
        return routes

    if is_nxos:
        # ── Modern NX-OS (ubest/mbest) ─────────────────────────────────────
        # Header: 10.1.0.0/24, ubest/mbest: 1/0, attached
        nxos_hdr_re = re.compile(
            r'^(?:(?P<code>[A-Za-z*]+)\s+)?'
            r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})'
            r'(?:,\s*ubest/mbest:\s*\d+/\d+)?(?:,\s*\S+)?\s*$',
        )
        # Via line: *via 10.0.0.1, Eth1/1, [110/20], 00:01:00, ospf-101, intra
        nxos_via_re = re.compile(
            r'^\s+\*?via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?:,\s*(?P<iface>[^,\[]+?))?'            # interface (up to , or [)
            r'(?:,\s*\[(?P<ad>\d+)/(?P<metric>\d+)\])?'
            r'(?:,\s*(?P<uptime>[\d:hwdmsHWDMS]+))?'
            r'(?:,\s*(?P<proto>[A-Za-z][A-Za-z0-9_-]*))?'  # ospf-101, bgp-65000 ...
            r'(?:,.*)?$',
        )
        lines = output.splitlines()
        current_net = None
        current_code = None
        modern_routes: List[Dict[str, Any]] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("'") or stripped.startswith('+'):
                continue

            # Skip table-header lines
            if stripped.lower().startswith('ip route table') or \
               stripped.lower().startswith('vrf') or \
               re.match(r'^[-=]{4,}', stripped):
                continue

            hdr_m = nxos_hdr_re.match(line)
            if hdr_m and hdr_m.group('net') and not line.startswith(' '):
                current_net = hdr_m.group('net')
                current_code = hdr_m.group('code') or ''
                # Handle IOS-style connected on same line
                if 'is directly connected' in line.lower():
                    iface_m = re.search(r'directly connected,\s*(\S+)', line, re.I)
                    modern_routes.append({
                        'protocol': 'Connected',
                        'network': current_net,
                        'next_hop': '0.0.0.0',
                        'metric': '0',
                        'admin_distance': '0',
                        'interface': iface_m.group(1) if iface_m else '',
                        'uptime': '',
                    })
                continue

            via_m = nxos_via_re.match(line)
            if via_m and current_net:
                proto_raw = (via_m.group('proto') or current_code or '').lower()
                canon = _canon_proto(proto_raw) if proto_raw else 'Unknown'
                iface = (via_m.group('iface') or '').strip().rstrip(',')
                modern_routes.append({
                    'protocol': canon,
                    'network': current_net,
                    'next_hop': via_m.group('nhop'),
                    'metric': via_m.group('metric') or '0',
                    'admin_distance': via_m.group('ad') or '0',
                    'interface': iface,
                    'uptime': via_m.group('uptime') or '',
                })

        if modern_routes:
            return modern_routes

        # ── Legacy NX-OS (IOS-style output) — fall through to IOS passes ──

    # ── IOS / IOS-XE (and NX-OS legacy fallback) ──────────────────────────
    # Multi-pass parser with continuation-line linking for ECMP routes

    # Pass 1: directly connected (with and without AD)
    for m in _RX_IOS_CONNECTED_AD.finditer(output):
        routes.append({
            'protocol': _canon_proto(m.group('code')),
            'network': m.group('net'),
            'next_hop': '0.0.0.0',
            'metric': m.group('metric'),
            'admin_distance': m.group('ad'),
            'interface': m.group('iface'),
        })
    
    for m in _RX_IOS_CONNECTED.finditer(output):
        routes.append({
            'protocol': _canon_proto(m.group('code')),
            'network': m.group('net'),
            'next_hop': '0.0.0.0',
            'metric': '0',
            'admin_distance': '0',
            'interface': m.group('iface'),
        })

    # Pass 2: via routes — with continuation-line tracking (ECMP)
    # We do a line-by-line pass to correctly handle:
    #   O  10.1.0.0/24 [110/2] via 10.0.0.1, 00:10:00, Gi0/0
    #                          via 10.0.0.2, 00:10:00, Gi0/1   <- continuation
    lines = output.splitlines()
    current_net_via: Optional[str] = None
    current_code_via: Optional[str] = None
    current_ad_via: str = '0'
    current_metric_via: str = '0'

    # Regex for first via line (has network prefix)
    # The code group handles multi-token codes: O IA, O N1, O N2, D EX, i L1, i L2, i su
    _RX_IOS_VIA_HDR = re.compile(
        r'^(?P<code>[A-Za-z*+%]+(?:\s+(?:IA|N1|N2|EX|L1|L2|su|E1|E2))?)\s+'
        r'(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
        r'(?:\s+\[(?P<ad>\d+)/(?P<metric>\d+)\])?\s+'
        r'via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?:,\s*(?P<field1>[^,]+))?(?:,\s*(?P<field2>[^,]+))?',
    )
    # Regex for continuation via line (indented, no network prefix)
    _RX_IOS_VIA_CONT = re.compile(
        r'^\s{5,}via\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?:,\s*(?P<field1>[^,]+))?(?:,\s*(?P<field2>[^,]+))?',
    )
    
    def _parse_ios_fields(field1, field2):
        """Parse IOS route fields to determine uptime and interface.
        Interface names start with letters (Gi, Te, Fa, Eth, Vlan, etc.)
        Uptime formats: 00:05:11, 1d02h, 3w5d, etc.
        """
        uptime = ''
        interface = ''
        
        if field1:
            # Strip trailing comma if present
            field1 = field1.rstrip(',')
        if field2:
            field2 = field2.rstrip(',')
        
        if field1:
            # Check if field1 looks like an interface (starts with letter)
            if field1 and field1[0].isalpha():
                interface = field1
                uptime = field2 or ''
            else:
                uptime = field1
                interface = field2 or ''
        elif field2:
            # Only field2 present
            if field2[0].isalpha():
                interface = field2
            else:
                uptime = field2
        
        return uptime, interface

    via_routes: List[Dict[str, Any]] = []
    for line in lines:
        hdr_m = _RX_IOS_VIA_HDR.match(line)
        if hdr_m:
            current_net_via = hdr_m.group('net')
            current_code_via = hdr_m.group('code')
            current_ad_via = hdr_m.group('ad') or '0'
            current_metric_via = hdr_m.group('metric') or '0'
            uptime, interface = _parse_ios_fields(hdr_m.group('field1'), hdr_m.group('field2'))
            via_routes.append({
                'protocol': _canon_proto(current_code_via),
                'network': current_net_via,
                'next_hop': hdr_m.group('nhop'),
                'metric': current_metric_via,
                'admin_distance': current_ad_via,
                'interface': interface,
                'uptime': uptime,
            })
            continue
        cont_m = _RX_IOS_VIA_CONT.match(line)
        if cont_m and current_net_via:
            uptime, interface = _parse_ios_fields(cont_m.group('field1'), cont_m.group('field2'))
            via_routes.append({
                'protocol': _canon_proto(current_code_via or ''),
                'network': current_net_via,
                'next_hop': cont_m.group('nhop'),
                'metric': current_metric_via,
                'admin_distance': current_ad_via,
                'interface': interface,
                'uptime': uptime,
            })
            continue
        # Only reset continuation tracking when we see a clearly new route header
        # (non-blank, non-indented, non-comment line that is NOT a via continuation).
        # This prevents ECMP continuation paths from being silently dropped after
        # comment lines ('!'), empty lines, or informational lines mid-table.
        if line and not line.startswith(' ') and not line.startswith('\t'):
            stripped = line.strip()
            if stripped and not stripped.startswith('!') and not stripped.startswith('#'):
                # Only reset if this looks like a real new route entry or table header
                if re.match(r'^[A-Za-z*+%]', stripped):
                    current_net_via = None

    routes.extend(via_routes)

    # Pass 3: legacy classful (only if no routes found)
    if not routes:
        for m in _RX_IOS_LEGACY_CLASSFUL.finditer(output):
            try:
                prefix = sum(bin(int(x)).count('1') for x in m.group('mask').split('.'))
                net = f"{m.group('net')}/{prefix}"
            except Exception:
                net = m.group('net')
            routes.append({
                'protocol': _canon_proto(m.group('code')),
                'network': net,
                'next_hop': m.group('nhop'),
                'metric': m.group('metric'),
                'admin_distance': m.group('ad'),
                'interface': '',
            })

    return routes


# ---------------------------------------------------------------------------
# Juniper Junos regex parser
# ---------------------------------------------------------------------------

# Table header:  inet.0: 14 destinations, 14 routes ...
_RX_JUNOS_TABLE = re.compile(r'^(?P<table>\S+):\s+\d+ destinations', re.MULTILINE)

# Route prefix line:  10.0.0.0/8  (1 entry, 1 announced)
# Also matches:       10.0.0.0/8        *[Static/5] ...  (no entry count)
_RX_JUNOS_PREFIX = re.compile(
    r'^(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})'
    r'(?:\s+\(\d+ entr|\s+\*\[|\s*$)',
    re.MULTILINE,
)

# Protocol + AD line:  *[OSPF/10] 1d 2h 3m 4s
_RX_JUNOS_PROTO = re.compile(
    r'^\s+(?P<active>\*)?\[(?P<proto>[A-Za-z0-9_-]+)/(?P<ad>\d+)\]',
    re.MULTILINE,
)

# Next hop line:   > to 10.1.1.1 via ge-0/0/0.0
_RX_JUNOS_NHOP = re.compile(
    r'^\s+>\s+to\s+(?P<nhop>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?:\s+via\s+(?P<iface>\S+))?',
    re.MULTILINE,
)

# Directly connected:  > directly connected, ge-0/0/0.0
_RX_JUNOS_DIRECT = re.compile(
    r'^\s+>\s+via\s+(?P<iface>\S+)',
    re.MULTILINE,
)


def _parse_juniper_regex(output: str) -> List[Dict[str, Any]]:
    """Regex Junos route parser — handles classic and terse 'show route' text output.

    Handles two formats:
      Classic:  prefix (N entry, N announced)
                    *[Proto/AD] age
                    > to nhop via iface
      Terse:    prefix        *[Proto/AD] age
                    > to nhop via iface

    Key fix: a terse-format line sets current_net AND current_proto simultaneously.
    The subsequent `> to IP via iface` line must emit exactly ONE route entry.
    We guard against emitting a second zero-nhop entry by tracking whether the
    current prefix+proto was already emitted via a real next-hop line.
    """
    routes: List[Dict[str, Any]] = []
    if not output:
        return routes

    # Combined prefix+proto on same line (terse format):
    # 10.1.1.0/24        *[Direct/0] 1w6d
    _RX_TERSE_HDR = re.compile(
        r'^(?P<net>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})'
        r'\s+\*?\[(?P<proto>[A-Za-z0-9_-]+)/(?P<ad>\d+)\]',
        re.MULTILINE,
    )

    lines = output.splitlines()
    current_net = None
    current_proto = None
    current_ad = '0'
    # Track whether we've emitted at least one route for (net, proto) — prevents
    # the "direct via" fallback from firing when a real next-hop was already emitted.
    _emitted_for_current: bool = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Try terse format first (prefix + proto on same line)
        terse_m = _RX_TERSE_HDR.match(line)
        if terse_m:
            current_net = terse_m.group('net')
            current_proto = terse_m.group('proto')
            current_ad = terse_m.group('ad')
            _emitted_for_current = False
            i += 1
            continue

        # Classic format: new prefix line (no proto on same line)
        pref_m = _RX_JUNOS_PREFIX.match(line)
        if pref_m:
            # Only update current_net if this is a fresh prefix line (no [Proto/AD] on same line)
            if not _RX_TERSE_HDR.match(line):
                current_net = pref_m.group('net')
                current_proto = None
                current_ad = '0'
                _emitted_for_current = False
            i += 1
            continue

        # Protocol line (classic format):   *[OSPF/10] 1d 2h
        proto_m = _RX_JUNOS_PROTO.match(line)
        if proto_m and current_net:
            current_proto = proto_m.group('proto')
            current_ad = proto_m.group('ad')
            _emitted_for_current = False
            i += 1
            continue

        # Next-hop line:   > to 10.1.1.1 via ge-0/0/0.0
        nhop_m = _RX_JUNOS_NHOP.match(line)
        if nhop_m and current_net:
            routes.append({
                'protocol': _canon_proto(current_proto or 'Unknown'),
                'network': current_net,
                'next_hop': nhop_m.group('nhop'),
                'metric': current_ad,
                'admin_distance': current_ad,
                'interface': nhop_m.group('iface') or '',
            })
            _emitted_for_current = True
            i += 1
            continue

        # Directly connected via (no `to IP`):   > via ge-0/0/0.0
        # Only emit if we haven't already emitted a real next-hop for this entry.
        direct_m = _RX_JUNOS_DIRECT.match(line)
        if direct_m and current_net and not _emitted_for_current:
            proto = 'Connected' if current_proto in ('Direct', 'Local', None) else _canon_proto(current_proto)
            routes.append({
                'protocol': proto,
                'network': current_net,
                'next_hop': '0.0.0.0',
                'metric': '0',
                'admin_distance': current_ad,
                'interface': direct_m.group('iface'),
            })
            _emitted_for_current = True
            i += 1
            continue

        i += 1

    return routes


# ---------------------------------------------------------------------------
# Public RoutingParser class
# ---------------------------------------------------------------------------

class RoutingParser:
    """Unified routing parser: TextFSM first, regex fallback.

    Public attribute ``template_dir`` is canonical. ``_tdir`` is an alias to
    the same Path (do not set one without the other).
    """

    def __init__(self, template_dir: Optional[str | Path] = None):
        if template_dir is None or str(template_dir).strip() == '':
            self.template_dir = self._find_template_dir()
        else:
            self.template_dir = Path(template_dir)

    def _find_template_dir(self) -> Path:
        if getattr(sys, 'frozen', False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent.parent
        return base / 'modules' / 'templates'

    @property
    def _tdir(self) -> Path:
        return self.template_dir

    @_tdir.setter
    def _tdir(self, value: str | Path) -> None:
        self.template_dir = Path(value)

    # ------------------------------------------------------------------
    # Primary entry points
    # ------------------------------------------------------------------

    def parse_routing_output(
        self,
        platform: str,
        command: str,
        output: str,
    ) -> List[Dict[str, Any]]:
        """
        Parse a single command output for given platform.
        Tries TextFSM first, then regex fallback.
        Never raises.
        """
        if not output or not output.strip():
            return []

        platform = (platform or 'cisco_ios').lower()
        command = (command or '').lower()

        # Choose parser branch
        try:
            if 'juniper' in platform or 'junos' in platform:
                return self._parse_junos(command, output)
            elif 'nxos' in platform or 'nx-os' in platform:
                return self._parse_nxos(command, output)
            else:
                return self._parse_ios(command, output)
        except Exception:
            pass

        return self.parse_routing_output_regex(platform, output)

    def parse_routing_output_regex(
        self,
        platform: str,
        output: str,
    ) -> List[Dict[str, Any]]:
        """Pure regex fallback — always safe."""
        if not output:
            return []
        platform = (platform or 'cisco_ios').lower()
        if 'juniper' in platform or 'junos' in platform:
            return _parse_juniper_regex(output)
        return _parse_cisco_regex(output, platform)

    # ------------------------------------------------------------------
    # Platform-specific helpers
    # ------------------------------------------------------------------

    def _parse_ios(self, command: str, output: str) -> List[Dict[str, Any]]:
        """Cisco IOS / IOS-XE parser (ntc-templates → local TextFSM → regex).

        Prefer whichever path yields more routes so multi-token codes (O IA, D EX)
        are not lost when a template is incomplete.
        """
        if 'ip route' in command or 'route' in command:
            candidates: List[List[Dict[str, Any]]] = []
            try:
                from modules.ntc_parse import parse_cli
                ntc_rows, _ = parse_cli('cisco_ios', 'show ip route', output)
                if ntc_rows:
                    candidates.append(self._map_textfsm_ios(ntc_rows))
            except Exception:
                pass
            tmpl = self.template_dir / 'cisco' / 'show_ip_route.textfsm'
            textfsm_parsed = _try_textfsm(tmpl, output)
            if textfsm_parsed:
                candidates.append(self._map_textfsm_ios(textfsm_parsed))
            candidates.append(_parse_cisco_regex(output, 'cisco_ios'))
            return max(candidates, key=len) if candidates else []
        return _parse_cisco_regex(output, 'cisco_ios')

    def _parse_nxos(self, command: str, output: str) -> List[Dict[str, Any]]:
        """Cisco NX-OS parser — TextFSM then regex, prefer whichever has more routes."""
        tmpl = self.template_dir / 'cisco' / 'show_ip_route.textfsm'
        textfsm_parsed = _try_textfsm(tmpl, output)
        if textfsm_parsed:
            textfsm_result = self._map_textfsm_ios(textfsm_parsed)
            regex_result = _parse_cisco_regex(output, 'cisco_nxos')
            return textfsm_result if len(textfsm_result) >= len(regex_result) else regex_result
        return _parse_cisco_regex(output, 'cisco_nxos')

    def _parse_junos(self, command: str, output: str) -> List[Dict[str, Any]]:
        """Juniper Junos parser (TextFSM → regex).

        Like IOS, if TextFSM returns fewer routes than regex, prefer regex.
        This guards against TextFSM templates that don't cover all Junos output variants.
        """
        tmpl = self.template_dir / 'juniper' / 'show_route.textfsm'
        textfsm_parsed = _try_textfsm(tmpl, output)
        if textfsm_parsed:
            textfsm_result = self._map_textfsm_junos(textfsm_parsed)
            regex_result = _parse_juniper_regex(output)
            return textfsm_result if len(textfsm_result) >= len(regex_result) else regex_result
        return _parse_juniper_regex(output)

    # ------------------------------------------------------------------
    # TextFSM result mappers (normalize column names → standard fields)
    # ------------------------------------------------------------------

    @staticmethod
    def _map_textfsm_ios(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for r in rows:
            net = r.get('network') or r.get('vrf_network') or ''
            nhop = r.get('next_hop') or r.get('nexthop') or ''
            proto = r.get('protocol') or r.get('route_protocol') or ''
            out.append({
                'protocol': _canon_proto(proto),
                'network': net,
                'next_hop': nhop,
                'metric': r.get('metric') or '0',
                'admin_distance': r.get('distance') or r.get('admin_distance') or '0',
                'interface': r.get('interface') or r.get('nexthop_if') or '',
                'uptime': r.get('uptime') or '',
            })
        return [x for x in out if x['network']]

    @staticmethod
    def _map_textfsm_junos(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for r in rows:
            net = r.get('network') or r.get('route_destination') or ''
            nhop = r.get('next_hop') or r.get('to') or ''
            proto = r.get('protocol') or r.get('route_protocol') or ''
            out.append({
                'protocol': _canon_proto(proto),
                'network': net,
                'next_hop': nhop,
                'metric': r.get('metric') or '0',
                'admin_distance': r.get('preference') or r.get('admin_distance') or '0',
                'interface': r.get('interface') or r.get('via') or '',
            })
        # Drop rows with empty next_hop — TextFSM emits one blank-nhop row per
        # prefix (the "header" row) plus one real-nhop row per path. Keeping only
        # rows that have a real nhop or a real interface avoids duplicates while
        # retaining Connected/Local routes (nhop='' but interface is set).
        filtered = []
        for x in out:
            if not x['network']:
                continue
            # Keep if nhop is present OR interface is present (connected routes)
            if x['next_hop'] or x['interface']:
                filtered.append(x)
        return filtered

    def parse_mac_address_table(
        self,
        platform: str,
        command: str,
        output: str,
    ) -> List[Dict[str, Any]]:
        """Parse MAC address table output for IOS/NX-OS devices.
        
        Returns list of MAC entries with: mac_address, vlan, interface, type
        """
        if not output or not output.strip():
            return []
        
        mac_entries = []
        
        # IOS format: 100    0000.0c12.3456    DYNAMIC     Gi1/0/1
        # NX-OS format: 10       00:00:00:00:00:01 dynamic   10       Ethernet1/1
        # More flexible patterns to handle various output formats
        # Pattern: VLAN (digits) + MAC (hex with : or .) + TYPE (word) + INTERFACE (word/symbols)
        _RX_MAC_GENERIC = re.compile(
            r'(?P<vlan>\d+)\s+'
            r'(?P<mac>[0-9a-fA-F:.]{14,17})\s+'
            r'(?P<type>\w+)\s+'
            r'(?:\d+\s+)?'  # Optional Age column (NX-OS)
            r'(?P<iface>[\w/\.:-]+)',
            re.MULTILINE
        )
        
        # Try to find MAC entries in the output
        for m in _RX_MAC_GENERIC.finditer(output):
            mac = m.group('mac')
            vlan = m.group('vlan')
            iface = m.group('iface')
            mac_type = m.group('type')
            
            # Validate MAC address format
            if ':' in mac or '.' in mac:
                mac_entries.append({
                    'mac_address': mac,
                    'type': mac_type,
                    'vlan': vlan,
                    'interface': iface,
                })
        
        return mac_entries

    def parse_cisco_ip_route(self, output: str) -> List[Dict[str, Any]]:
        """Parse Cisco ``show ip route`` via the bundled TextFSM template.

        Unlike ``parse_routing_output``, missing template files raise
        ``FileNotFoundError`` so callers can distinguish config errors from
        empty CLI. Non-string output raises ``TypeError``.
        """
        if not isinstance(output, str):
            raise TypeError('parse_cisco_ip_route expects a string CLI dump')
        tmpl = self.template_dir / 'cisco' / 'show_ip_route.textfsm'
        if not tmpl.is_file():
            raise FileNotFoundError(
                f'Cisco routing TextFSM template not found: {tmpl}'
            )
        parsed = _try_textfsm(tmpl, output)
        if parsed:
            return self._map_textfsm_ios(parsed)
        return _parse_cisco_regex(output, 'cisco_ios')
