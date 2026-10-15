"""Phase 6 Wave 1 — Discovery Program Status (operator-facing).

Builds a single coherent payload that separates:
1. confirmed discovery/topology counts from the last job (if any),
2. incomplete observations (diagnostic, not edges),
3. Phase 5 readiness / release-gate hard-stop (authoritative register).

Does not invent topology, soften BLOCKED, or claim enterprise/live validation.
Reuses ``tests/qa/PHASE5_DISCOVERY_READINESS.json`` as the readiness source of truth.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTER = ROOT / 'tests' / 'qa' / 'PHASE5_DISCOVERY_READINESS.json'

# Phase 6 Wave 4 — three operator surfaces, one Program Status (not topology)
PROGRAM_STATUS_SURFACES = (
    {
        'id': 'discovery_tab',
        'label': 'Discovery tab',
        'identity': 'Hop-bounded CDP/LLDP crawl operator UI',
        'distinct_from': 'Not the Swiss Tools inventory Standard L2 map',
    },
    {
        'id': 'discovery_command_center',
        'label': 'Discovery Command Center',
        'identity': 'Offline crawl map shell for a discovery job',
        'distinct_from': 'Not the inventory Standard L2 map',
    },
    {
        'id': 'inventory_standard_l2',
        'label': 'Inventory Standard L2 map',
        'identity': 'Swiss Tools sidebar-inventory SSH L2 map',
        'distinct_from': 'Not the Discovery crawl Command Center graph',
    },
)

CROSS_SURFACE_NOTE = (
    'These three surfaces share one authoritative Discovery Program Status. '
    'They are not the same topology artifact. '
    'Incomplete observations are not map links. '
    'Program Status is not topology. '
    'release_gate BLOCKED is a hard stop — not advisory. '
    'Not live-validated; not enterprise cleared.'
)

# Phase 6 Wave 5 — navigation labels only (not readiness / not topology)
RELATED_SURFACE_JUMPS = (
    {
        'id': 'discovery_tab',
        'label': 'Open Discovery tab',
        'hash': 'nst-discovery',
    },
    {
        'id': 'discovery_command_center',
        'label': 'Open Command Center',
        'hash': 'nst-discovery',
        'note': 'Opens last crawl report when a job exists; otherwise Discovery tab',
    },
    {
        'id': 'inventory_standard_l2',
        'label': 'Open Inventory L2 entry',
        'hash': 'nst-inventory-l2',
        'note': 'Swiss Tools Standard L2 entry — does not auto-run SSH map',
    },
    {
        'id': 'evidence_overview',
        'label': 'View Evidence',
        'hash': 'nst-evidence',
    },
)


_EMBEDDED_READINESS_REGISTER: Dict[str, Any] = {
    "schema": "nst.phase5.discovery_readiness.v1",
    "phase": 5,
    "title": "Discovery truncated CDP/LLDP resilience readiness",
    "as_of": "2026-08-21",
    "enterprise_operational_ready": False,
    "live_vendor_truncated_cdp_lldp_validated": False,
    "release_gate_when_not_ready": "BLOCKED",
    "verdict": "contract_proven_fixture_replay — not enterprise operational ready — not live vendor validated",
    "operator_summary": (
        "Phase 5 truncated discovery: incomplete-observation contract proven (fixture/replay). "
        "Enterprise operational ready: NO. Live truncated CDP/LLDP: NOT VALIDATED. "
        "Release gate: BLOCKED (HARD STOP — not advisory) until live_ssh evidence."
    ),
    "traceability_refs": [".cursor/docs/READINESS_TRACEABILITY.md", "B-LIVE-01"],
    "blocker_ids": ["P5-LIVE-TRUNCATED", "B-LIVE-01"],
    "evidence_paths": {"live_evidence_artifact": None},
}


def load_readiness_register(path: Optional[Path] = None) -> Dict[str, Any]:
    candidates = []
    if path:
        candidates.append(Path(path))
    candidates.append(DEFAULT_REGISTER)

    import sys
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            candidates.append(Path(sys._MEIPASS) / 'tests' / 'qa' / 'PHASE5_DISCOVERY_READINESS.json')
            candidates.append(Path(sys._MEIPASS) / 'PHASE5_DISCOVERY_READINESS.json')
        exe_dir = Path(sys.executable).parent
        candidates.append(exe_dir / 'tests' / 'qa' / 'PHASE5_DISCOVERY_READINESS.json')
        candidates.append(exe_dir / 'PHASE5_DISCOVERY_READINESS.json')

    for candidate in candidates:
        try:
            if candidate and candidate.is_file():
                return json.loads(candidate.read_text(encoding='utf-8'))
        except Exception:
            continue

    return dict(_EMBEDDED_READINESS_REGISTER)


def _job_discovery_slice(job: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Safe counters from a discovery job snapshot — no credentials, no raw CLI."""
    if not job:
        return {
            'job_present': False,
            'job_id': None,
            'job_status': None,
            'collection_status': None,
            'confirmed_device_count': 0,
            'confirmed_link_count': 0,
            'incomplete_observation_count': 0,
            'operator_truth': 'no discovery job in this session yet',
        }

    result = job.get('result') or {}
    data = result.get('data') if isinstance(result, dict) else {}
    if not isinstance(data, dict):
        data = {}
    devices = data.get('devices') or []
    links = data.get('links') or []
    inc = int(data.get('incomplete_observation_count') or 0)
    if not inc:
        inc = sum(int(d.get('incomplete_observation_count') or 0) for d in devices if isinstance(d, dict))

    # Confirmed links only — incompletes are never links
    confirmed_links = [
        ln for ln in links
        if isinstance(ln, dict) and not ln.get('incomplete') and ln.get('edge_eligible') is not False
    ]

    status = job.get('status')
    coll = data.get('collection_status') or job.get('collection_status')
    if status in ('complete',) and not data.get('partial') and not data.get('cancelled'):
        truth = 'complete as collected (CDP/LLDP hop-bounded; not overlay; not live-vendor validation)'
    elif status in ('partial', 'cancelled') or data.get('partial') or data.get('cancelled'):
        truth = 'not complete truth — partial/cancelled crawl'
    elif status == 'error':
        truth = 'error'
    elif status in ('running', 'queued', 'pending'):
        truth = 'running'
    else:
        truth = f'job status: {status}'

    return {
        'job_present': True,
        'job_id': job.get('job_id') or job.get('id'),
        'job_status': status,
        'collection_status': coll,
        'confirmed_device_count': len(devices),
        'confirmed_link_count': len(confirmed_links),
        'incomplete_observation_count': inc,
        'operator_truth': truth,
        'scan_profile': job.get('scan_profile') or data.get('scan_profile'),
        'max_depth': job.get('max_depth') or data.get('max_depth'),
    }


def _readiness_slice(reg: Dict[str, Any]) -> Dict[str, Any]:
    """Authoritative readiness fields — mirrors Phase 5 register / checker semantics."""
    ent = bool(reg.get('enterprise_operational_ready'))
    live = bool(reg.get('live_vendor_truncated_cdp_lldp_validated'))
    if ent and live:
        gate = 'PASS'
        hard_stop = False
    else:
        gate = str(reg.get('release_gate_when_not_ready') or 'BLOCKED').upper()
        if gate != 'BLOCKED':
            gate = 'BLOCKED'
        hard_stop = True

    return {
        'source': 'tests/qa/PHASE5_DISCOVERY_READINESS.json',
        'enterprise_operational_ready': ent,
        'live_vendor_truncated_cdp_lldp_validated': live,
        'release_gate': gate,
        'release_gate_severity': 'hard',
        'hard_stop': hard_stop,
        'may_claim_enterprise_ready': gate == 'PASS',
        'may_claim_live_vendor_validated': gate == 'PASS',
        'ok_alone_insufficient_for_enterprise_claim': True,
        'operator_summary': reg.get('operator_summary') or '',
        'verdict': reg.get('verdict') or '',
        'blocker_ids': list(reg.get('blocker_ids') or []),
        'consumer_rule': (
            'Treat release_gate==PASS as the only clearance for enterprise/live '
            'claims. Session discovery counts are not live vendor validation. '
            'release_gate==BLOCKED is a hard stop, never advisory.'
        ),
    }


def build_discovery_program_status(
    *,
    job: Optional[Dict[str, Any]] = None,
    register_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Assemble Phase 6 Wave 1 Discovery Program Status payload."""
    reg = load_readiness_register(register_path)
    discovery = _job_discovery_slice(job)
    readiness = _readiness_slice(reg)

    categories = [
        {
            'id': 'confirmed_topology',
            'label': 'Confirmed discovery / topology (this session)',
            'summary': (
                f"{discovery['confirmed_device_count']} device(s), "
                f"{discovery['confirmed_link_count']} confirmed link(s)"
                if discovery['job_present']
                else 'No crawl job yet — confirmed counts are zero'
            ),
            'count_devices': discovery['confirmed_device_count'],
            'count_links': discovery['confirmed_link_count'],
            'operator_truth': discovery['operator_truth'],
        },
        {
            'id': 'incomplete_observations',
            'label': 'Incomplete observations (diagnostic only)',
            'summary': (
                f"{discovery['incomplete_observation_count']} incomplete observation(s) — "
                'not map links, not edge-eligible'
                if discovery['incomplete_observation_count']
                else 'No incomplete observations on the current job'
            ),
            'count': discovery['incomplete_observation_count'],
            'edge_eligible': False,
        },
        {
            'id': 'readiness_release_gate',
            'label': 'Program readiness / release gate',
            'summary': readiness['operator_summary'],
            'release_gate': readiness['release_gate'],
            'hard_stop': readiness['hard_stop'],
            'enterprise_operational_ready': readiness['enterprise_operational_ready'],
            'live_vendor_truncated_cdp_lldp_validated': readiness[
                'live_vendor_truncated_cdp_lldp_validated'
            ],
        },
    ]

    return {
        'schema': 'nst.phase6.discovery_program_status.v1',
        'phase': '6-wave1',
        'title': 'Discovery Program Status',
        'categories': categories,
        'discovery': discovery,
        'readiness': readiness,
        'surfaces': [dict(s) for s in PROGRAM_STATUS_SURFACES],
        'cross_surface_note': CROSS_SURFACE_NOTE,
        'related_surface_jumps': [dict(j) for j in RELATED_SURFACE_JUMPS],
        'honesty': {
            'enterprise_operational_ready': readiness['enterprise_operational_ready'],
            'live_vendor_truncated_cdp_lldp_validated': readiness[
                'live_vendor_truncated_cdp_lldp_validated'
            ],
            'hard_stop': readiness['hard_stop'],
            'note': (
                'Session crawl results do not clear the release gate. '
                'BLOCKED means hard stop — not advisory.'
            ),
        },
    }


def program_status_from_map_meta(
    meta: Dict[str, Any],
    *,
    register_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build Program Status for Discovery Command Center HTML from map meta.

    Reuses ``build_discovery_program_status`` — no parallel readiness model.
    Map/session counts never clear the hard-stop gate.
    """
    status = meta.get('collection_status') or (
        'partial' if meta.get('partial') or meta.get('cancelled') else 'complete'
    )
    job = {
        'job_id': meta.get('job_id'),
        'status': status,
        'scan_profile': meta.get('scan_profile'),
        'max_depth': meta.get('max_depth'),
        'result': {
            'data': {
                'devices': meta.get('devices') or [],
                'links': meta.get('links') or [],
                'incomplete_observation_count': int(
                    meta.get('incomplete_observation_count') or 0
                ),
                'collection_status': status,
                'partial': bool(meta.get('partial')),
                'cancelled': bool(meta.get('cancelled')),
            }
        },
    }
    payload = build_discovery_program_status(job=job, register_path=register_path)
    payload['phase'] = '6-wave2'
    payload['surface'] = 'discovery_command_center_map_shell'
    return payload


def program_status_for_inventory_standard_l2(
    *,
    num_devices: int = 0,
    num_links: int = 0,
    register_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Program Status for Swiss Tools inventory Standard L2 map.

    Reuses ``build_discovery_program_status`` (no parallel readiness model).
    Inventory map identity is explicit and distinct from Discovery crawl graph.
    Map device/link counts never clear the hard-stop gate.
    """
    payload = build_discovery_program_status(job=None, register_path=register_path)
    payload['phase'] = '6-wave3'
    payload['surface'] = 'inventory_standard_l2_map'
    payload['map_identity'] = {
        'view': 'inventory_standard_l2',
        'not_discovery_crawl_graph': True,
        'label': (
            'Swiss Tools inventory Standard L2 map — sidebar inventory SSH. '
            'Not the Discovery crawl Command Center graph.'
        ),
        'device_count': int(num_devices or 0),
        'link_count': int(num_links or 0),
    }
    inventory_cat = {
        'id': 'inventory_l2_map_view',
        'label': 'This view: inventory Standard L2 map',
        'summary': (
            f"{int(num_devices or 0)} device(s), {int(num_links or 0)} link(s) "
            'from inventory scope — not Discovery crawl graph truth'
        ),
    }
    payload['categories'] = [inventory_cat] + list(payload.get('categories') or [])
    # Honesty note stays; append inventory distinctness
    note = (payload.get('honesty') or {}).get('note') or ''
    payload.setdefault('honesty', {})
    payload['honesty']['note'] = (
        note + ' This HTML is the inventory Standard L2 map, not the crawl graph. '
        'Program Status is not inventory topology and does not invent links.'
    ).strip()
    return payload


def program_status_cross_surface_overview(
    *,
    register_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Phase 6 Wave 4 — same Program Status for three distinct operator surfaces.

    No parallel readiness model: reuses ``build_discovery_program_status``.
    """
    payload = build_discovery_program_status(job=None, register_path=register_path)
    payload['phase'] = '6-wave4'
    payload['overview'] = {
        'kind': 'cross_surface_program_status',
        'authoritative_source': 'build_discovery_program_status',
        'surface_ids': [s['id'] for s in PROGRAM_STATUS_SURFACES],
        'note': CROSS_SURFACE_NOTE,
    }
    return payload


def program_status_related_surface_jumps() -> list:
    """Wave 5 — copy of related-surface jump metadata (navigation only)."""
    return [dict(j) for j in RELATED_SURFACE_JUMPS]
