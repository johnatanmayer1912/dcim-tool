"""Discovery export schema — lightweight, no extra dependency.

Validates crawl JSON / API fallback. Overlay may be collected from NVE/EVPN CLI.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

COLLECTION_STATUSES = frozenset({'complete', 'partial', 'cancelled'})
SCAN_STATES = frozenset({
    'seed', 'scanned', 'neighbor_only', 'failed', 'auth_denied', 'timeout',
})
NEIGHBOR_EVIDENCE = frozenset({'collected', 'none_collected', 'protocol_disabled', ''})

DEVICE_REQUIRED = ('id', 'hostname', 'scan_state')
LINK_REQUIRED = ('from', 'to')


def validate_discovery_export(data: Any) -> Tuple[bool, List[str]]:
    """Return (ok, errors). Partial graphs may still ok=True if shape is honest."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ['export is not an object']

    if data.get('overlay_collected') is True:
        olinks = data.get('overlay_links')
        if olinks is None:
            olinks = [lk for lk in (data.get('links') or []) if isinstance(lk, dict) and (
                str(lk.get('layer') or '').lower() == 'overlay'
                or str(lk.get('edge_kind') or '').lower() == 'nve-peer'
            )]
        if not isinstance(olinks, list):
            errors.append('overlay_collected=true requires overlay_links to be a list')
        else:
            for i, link in enumerate(olinks):
                if not isinstance(link, dict):
                    errors.append(f'overlay_links[{i}] is not an object')
                    continue
                if not link.get('not_physical'):
                    errors.append(f'overlay_links[{i}] must be not_physical')
                if str(link.get('layer') or '').lower() == 'physical':
                    errors.append(f'overlay_links[{i}] must not be layer=physical')
                if str(link.get('edge_kind') or '') == 'physical-link':
                    errors.append(f'overlay_links[{i}] must not be physical-link')

    status = data.get('collection_status')
    if status not in COLLECTION_STATUSES:
        errors.append(f'collection_status missing or invalid: {status!r}')

    if data.get('cancelled') and status == 'complete':
        errors.append('cancelled export must not use collection_status=complete')

    devices = data.get('devices')
    links = data.get('links')
    if not isinstance(devices, list):
        errors.append('devices must be a list')
        devices = []
    if not isinstance(links, list):
        errors.append('links must be a list')
        links = []

    for i, dev in enumerate(devices):
        if not isinstance(dev, dict):
            errors.append(f'devices[{i}] is not an object')
            continue
        for key in DEVICE_REQUIRED:
            if not dev.get(key) and dev.get(key) != 0:
                errors.append(f'devices[{i}] missing {key}')
        st = dev.get('scan_state')
        if st and st not in SCAN_STATES:
            errors.append(f'devices[{i}] unknown scan_state {st!r}')
        ev = dev.get('neighbor_evidence', '')
        if ev not in NEIGHBOR_EVIDENCE:
            errors.append(f'devices[{i}] unknown neighbor_evidence {ev!r}')

    for i, link in enumerate(links):
        if not isinstance(link, dict):
            errors.append(f'links[{i}] is not an object')
            continue
        for key in LINK_REQUIRED:
            if not link.get(key):
                errors.append(f'links[{i}] missing {key}')
        if link.get('not_physical') and str(link.get('layer') or '').lower() == 'physical':
            errors.append(f'links[{i}] not_physical must not be labeled layer=physical')

    ok = not any(
        e.startswith('export is') or e.startswith('devices must') or e.startswith('links must')
        or e.startswith('overlay_collected')
        or e.startswith('overlay_links')
        or e.startswith('cancelled export')
        for e in errors
    ) and status in COLLECTION_STATUSES
    return ok, errors


def annotate_export(data: Dict[str, Any]) -> Dict[str, Any]:
    """Attach schema_ok / schema_errors without inventing topology."""
    out = dict(data)
    out.setdefault('overlay_collected', False)
    if out.get('overlay_collected'):
        out.setdefault(
            'overlay_note',
            'EVPN/NVE CLI ran. Overlay edges are VTEP/NVE peers, not cables.',
        )
        out.setdefault('overlay_links', [
            lk for lk in (out.get('links') or [])
            if isinstance(lk, dict) and str(lk.get('layer') or '').lower() == 'overlay'
        ])
    else:
        out.setdefault('overlay_note', 'EVPN/VXLAN overlay is not collected')
        out.setdefault('overlay_links', [])
    ok, errors = validate_discovery_export(out)
    out['schema_ok'] = ok
    out['schema_errors'] = errors
    return out
