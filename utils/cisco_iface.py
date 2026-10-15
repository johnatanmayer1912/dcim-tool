"""Cisco/NX-OS interface token normalize — no device I/O, no SSH.

Used by discovery parsers and graph cable keys so brief `Gig 1/0/1` and
detail `GigabitEthernet1/0/1` share one identity. Safe to import from
telemetry freeze tests (must not pull paramiko).
"""
from __future__ import annotations

import re

_EMPTY = re.compile(
    r'^(?:not\s+advertised|not-advertised|null|none|n/?a|\.|-|unknown)$',
    re.I,
)
_MAC_LIKE = re.compile(
    r'^([0-9a-f]{4}\.){2}[0-9a-f]{4}(?:\.[0-9a-f]{4})?$'
    r'|^([0-9a-f]{2}:){5}[0-9a-f]{2}$'
    r'|^([0-9a-f]{2}-){5}[0-9a-f]{2}$',
    re.I,
)


def strip_mac_prefix(token: str) -> str:
    s = str(token or '').strip()
    if s.lower().startswith('mac '):
        return s[4:].strip()
    return s


def is_mac_like(value: str) -> bool:
    if not value:
        return False
    return bool(_MAC_LIKE.match(strip_mac_prefix(str(value).strip())))


def _invalid(value: str) -> bool:
    if not value:
        return True
    return bool(_EMPTY.match(str(value).strip()))


def normalize_cisco_iface(port: str) -> str:
    """Collapse Cisco brief/detail interface spellings to a short token."""
    if not port or _invalid(port):
        return ''
    s = str(port).strip().strip('"').strip("'")
    if _invalid(s):
        return ''
    s = strip_mac_prefix(s)
    spaced = re.match(
        r'^(Ethernet|Eth|GigabitEthernet|Gig|Gi|FastEthernet|Fas|Fa|'
        r'TenGigabitEthernet|TenGigE|Ten|Te|TwentyFiveGigE|Twe|'
        r'FortyGigabitEthernet|For|Fo|HundredGigE|Hun|Hu|'
        r'Port-channel|Por|Po)\s+(\d+(?:/\d+){0,3})$',
        s,
        re.I,
    )
    if spaced:
        s = spaced.group(1) + spaced.group(2)
    eth = re.match(r'^Ethernet(\d+(?:/\d+){1,3})$', s, re.I)
    if eth:
        return f"Eth{eth.group(1)}"
    eth2 = re.match(r'^Eth(?:ernet)?(\d+(?:/\d+){1,3})$', s, re.I)
    if eth2:
        return f"Eth{eth2.group(1)}"
    gi = re.match(r'^(?:GigabitEthernet|Gig|Gi)(\d+(?:/\d+){1,3})$', s, re.I)
    if gi:
        return f"Gi{gi.group(1)}"
    fa = re.match(r'^(?:FastEthernet|Fas|Fa)(\d+(?:/\d+){1,3})$', s, re.I)
    if fa:
        return f"Fa{fa.group(1)}"
    te = re.match(
        r'^(?:TenGigabitEthernet|TenGigE|Ten|Te)(\d+(?:/\d+){1,3})$', s, re.I,
    )
    if te:
        return f"Te{te.group(1)}"
    po = re.match(r'^(?:Port-channel|Por|Po)(\d+)$', s, re.I)
    if po:
        return f"Po{po.group(1)}"
    return s
