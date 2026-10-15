"""Map acceptance assertions — blocked conditions and neighborhood semantics.

AI_CONTEXT: Contract for Physical/L2/L3/overlay honesty. Overlay comes from NVE/EVPN CLI only.
AI_MAP_NOTE: Blast is a graph neighborhood, not a forwarding path. Do not invent VTEPs.
AI_TEST_NOTE: tests/test_map_acceptance.py
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Set

from utils.topo_map_shell import NST_BLAST_SEMANTICS, NST_STALE_HOURS

SUPPORTED_VIEWS = ('physical', 'l2', 'l3', 'overlay')

# Substrings that must appear in generated map HTML (shared shell).
REQUIRED_HTML = (
    'data-layer="physical"',
    'data-layer="l2"',
    'data-layer="l3"',
    'data-layer="overlay"',
    'id="nst-overlay-empty"',
    'id="nst-physical-note"',
    'nstPhysicalEligible',
    'nstStartFreshnessClock',
    'nstApplyHashLayer',
    'Bidirectional CDP/LLDP only',
    'Overlay not collected',
    'EVPN/VXLAN overlay is not collected',
    'not a forwarding path',
    'nstBlastRadius(1)',
    'nstBlastRadius(2)',
    'window.NST_BLAST_SEMANTICS',
    'window.NST_STALE_HOURS',
    'CONFLICT',
    'not current truth',
    'not proof the fabric has no overlay',
)

# Claims that must never appear as if overlay/path/census were collected.
BLOCKED_HTML = (
    'VTEP discovered',
    'EVPN collected',
    'VXLAN overlay discovered',
    'overlay inferred from hostname',
    'forwarding path for blast',
    'unpkg.com/vis-network',
    'https://unpkg.com',
)

BLOCKED_CONDITIONS = (
    'false links (unverified High on one-sided CDP/LLDP)',
    'hidden conflicts (contradictory remotes merged silently)',
    'stale data shown as current truth (no STALE after 24h)',
    'duplicate identity collapse (two serials, one vis node)',
    'path-like language for blast neighborhood',
    'unsupported overlay implied by naming only',
)


def blast_neighborhood(
    edges: Iterable[Mapping[str, Any]],
    start_id: str,
    hops: int,
) -> Dict[Any, int]:
    """Graph-hop neighborhood. Not a traffic or forwarding path."""
    depth = 2 if int(hops) == 2 else 1
    hop: Dict[Any, int] = {start_id: 0}
    frontier = [start_id]
    for h in range(depth):
        nxt: List[Any] = []
        for nid in frontier:
            for e in edges:
                frm, to = e.get('from'), e.get('to')
                other = to if frm == nid else (frm if to == nid else None)
                if other is not None and other not in hop:
                    hop[other] = h + 1
                    nxt.append(other)
        frontier = nxt
    return hop


def assert_html_map_acceptance(html: str) -> None:
    low = html
    for needle in REQUIRED_HTML:
        if needle not in low:
            raise AssertionError(f'map acceptance missing: {needle}')
    for banned in BLOCKED_HTML:
        if banned.lower() in low.lower() and banned != 'CONFLICT':
            raise AssertionError(f'map acceptance blocked string present: {banned}')
    if 'unpkg.com' in low.lower():
        raise AssertionError('map HTML must not load vis.js from unpkg')
    if str(NST_STALE_HOURS) not in html:
        raise AssertionError('STALE threshold not embedded')
    if NST_BLAST_SEMANTICS not in html:
        raise AssertionError('blast semantics token missing')


def identity_ids(nodes: Iterable[Mapping[str, Any]]) -> Set[str]:
    return {str(n.get('id')) for n in nodes if n.get('id')}
