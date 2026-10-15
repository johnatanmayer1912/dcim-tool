"""
modules/routing_analyzer/normalizer.py
----------------------------------------
Normalize raw parsed routes into a unified data model.

Key improvements vs v1:
  - VRF awareness (preserves VRF context from collector)
  - Deduplication: same (device, destination, next_hop, protocol) → one entry
  - Robust CIDR normalization (classful mask → prefix length)
  - Admin distance extracted from [AD/metric] bracket notation
  - Protocol mapping aligned with Cisco + Junos codes
"""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Protocol code → canonical name (unified across IOS, NX-OS, Junos)
# ---------------------------------------------------------------------------

PROTOCOL_MAP: Dict[str, str] = {
    'C':      'Connected',
    'L':      'Local',
    'S':      'Static',
    'R':      'RIP',
    'M':      'Mobile',
    'B':      'BGP',
    'D':      'EIGRP',
    'EX':     'EIGRP-External',
    'O':      'OSPF',
    'OI':     'OSPF-InterArea',
    'IA':     'OSPF-InterArea',
    'ON1':    'OSPF-NSSA-Ext1',
    'ON2':    'OSPF-NSSA-Ext2',
    'N1':     'OSPF-NSSA-Ext1',
    'N2':     'OSPF-NSSA-Ext2',
    'OE1':    'OSPF-Ext1',
    'OE2':    'OSPF-Ext2',
    'E1':     'OSPF-Ext1',
    'E2':     'OSPF-Ext2',
    'i':      'ISIS',
    'su':     'ISIS-Summary',
    'L1':     'ISIS-L1',
    'L2':     'ISIS-L2',
    'ia':     'ISIS-InterArea',
    'K':      'ODR',
    'G':      'DHCP',
    # Junos protocol names (already human-readable but map to canonical)
    'Direct': 'Connected',
    'Static': 'Static',
    'OSPF':   'OSPF',
    'BGP':    'BGP',
    'ISIS':   'ISIS',
    'IS-IS':  'ISIS',
    'RIP':    'RIP',
    'EIGRP':  'EIGRP',
    'LDP':    'LDP',
    'RSVP':   'RSVP',
}

_AD_DEFAULTS: Dict[str, int] = {
    'Connected': 0,
    'Local':     0,
    'Static':    1,
    'EIGRP':     90,
    'OSPF':      110,
    'ISIS':      115,
    'RIP':       120,
    'BGP':       200,
}


def _canon_protocol(raw: str) -> str:
    if not raw:
        return 'Unknown'
    raw = str(raw).strip().rstrip('*').strip()
    if not raw:
        return 'Unknown'
    # Direct lookup first (handles single-char Cisco codes and Junos strings)
    if raw in PROTOCOL_MAP:
        return PROTOCOL_MAP[raw]
    upper = raw.upper()
    # Case-insensitive scan of map keys
    for k, v in PROTOCOL_MAP.items():
        if k.upper() == upper:
            return v
    # If the input is already a canonical subtype name (produced by the parser),
    # preserve it exactly — do NOT strip it to a base type via substring match.
    # This handles OSPF-InterArea, OSPF-Ext1, EIGRP-External, ISIS-L1, etc.
    _CANONICAL_SUBTYPES = {
        'OSPF-INTERAREA', 'OSPF-EXT1', 'OSPF-EXT2',
        'OSPF-NSSA-EXT1', 'OSPF-NSSA-EXT2',
        'EIGRP-EXTERNAL',
        'ISIS-L1', 'ISIS-L2', 'ISIS-SUMMARY', 'ISIS-INTERAREA',
    }
    if upper.replace(' ', '-') in _CANONICAL_SUBTYPES or upper in _CANONICAL_SUBTYPES:
        return raw  # already canonical — preserve exactly

    # Substring matches (for truly unknown/raw protocol strings only)
    if 'OSPF' in upper:
        return 'OSPF'
    if 'BGP' in upper:
        return 'BGP'
    if 'EIGRP' in upper:
        return 'EIGRP'
    if 'ISIS' in upper or 'IS-IS' in upper:
        return 'ISIS'
    if 'RIP' in upper:
        return 'RIP'
    if 'STATIC' in upper:
        return 'Static'
    if 'CONNECTED' in upper or 'DIRECT' in upper:
        return 'Connected'
    return raw


def _normalize_cidr(raw: str) -> str:
    """Convert any route destination to strict CIDR notation."""
    if not raw:
        return ''
    raw = raw.strip()
    try:
        if '/' in raw:
            return str(ipaddress.ip_network(raw, strict=False))
        # Bare IP — assume host route for next_hops, /32 for IPv4
        return str(ipaddress.ip_network(raw + '/32', strict=False))
    except ValueError:
        return raw


def _normalize_ip(raw: str) -> str:
    if not raw:
        return ''
    raw = raw.strip()
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return raw


def _extract_ad_metric(raw_metric: Any) -> tuple[int, int]:
    """
    Extract (admin_distance, metric) from raw metric field.
    Handles:  [110/2]  ->  (110, 2)
              '110/2'  ->  (110, 2)
              '2'      ->  (0, 2)
    """
    s = str(raw_metric or '').strip()
    m = re.search(r'\[?(\d+)/(\d+)\]?', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    try:
        return 0, int(s)
    except ValueError:
        return 0, 0


def _route_type(protocol: str) -> str:
    if protocol in ('Connected', 'Local'):
        return 'Connected'
    if protocol == 'Static':
        return 'Static'
    return 'Dynamic'


# ---------------------------------------------------------------------------
# Deduplication key
# ---------------------------------------------------------------------------

def _dedup_key(route: Dict[str, Any]) -> tuple:
    return (
        route.get('device_id', ''),
        route.get('destination', ''),
        route.get('next_hop', ''),
        route.get('protocol', ''),
        route.get('vrf', 'default'),
    )


# ---------------------------------------------------------------------------
# RoutingNormalizer
# ---------------------------------------------------------------------------

class RoutingNormalizer:
    """Normalize a list of raw parsed routes into a clean, deduplicated model."""

    def normalize_route(
        self,
        raw: Dict[str, Any],
        device_id: str,
        vrf: str = 'default',
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize one raw route dict.

        Returns None if the route is not meaningful (missing destination, multicast, etc.).
        """
        dest_raw = raw.get('destination') or raw.get('network') or ''
        dest = _normalize_cidr(dest_raw)
        if not dest:
            return None

        # Skip multicast
        try:
            net = ipaddress.ip_network(dest, strict=False)
            if net.is_multicast:
                return None
        except ValueError:
            pass

        proto_raw = raw.get('protocol') or raw.get('proto') or ''
        proto = _canon_protocol(proto_raw)

        # Admin distance + metric
        ad_raw = raw.get('admin_distance') or raw.get('distance') or raw.get('preference') or ''
        metric_raw = raw.get('metric') or ''
        if ad_raw and metric_raw:
            try:
                ad = int(str(ad_raw))
            except ValueError:
                ad = 0
            try:
                metric = int(str(metric_raw).split('/')[0])
            except ValueError:
                metric = 0
        else:
            # Try to extract from bracket notation in metric field
            ad, metric = _extract_ad_metric(ad_raw or metric_raw)
            if ad == 0 and proto in _AD_DEFAULTS:
                ad = _AD_DEFAULTS[proto]

        next_hop = _normalize_ip(raw.get('next_hop') or raw.get('nhop') or '')
        interface = (raw.get('interface') or raw.get('iface') or '').strip()
        uptime = (raw.get('uptime') or '').strip()

        return {
            'destination': dest,
            'next_hop': next_hop,
            'protocol': proto,
            'metric': metric,
            'admin_distance': ad,
            'interface': interface,
            'vrf': vrf,
            'device_id': device_id,
            'uptime': uptime,
            'route_type': _route_type(proto),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def normalize_routing_table(
        self,
        parsed_routes: List[Dict[str, Any]],
        device_id: str,
        vrf: str = 'default',
    ) -> List[Dict[str, Any]]:
        """Normalize + deduplicate an entire list of parsed routes."""
        seen: set = set()
        normalized: List[Dict[str, Any]] = []

        for raw in parsed_routes:
            try:
                r = self.normalize_route(raw, device_id, vrf)
                if r is None:
                    continue
                key = _dedup_key(r)
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(r)
            except Exception:
                continue

        return normalized
