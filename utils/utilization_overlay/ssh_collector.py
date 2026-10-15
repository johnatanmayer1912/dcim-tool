"""Bounded live SSH two-sample collector for Standard L2 utilization.

One on-demand cycle. No SNMP. No utils.telemetry. Cancel-safe and degraded-safe.
Does not create topology. Secrets never written to overlay JSON.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from utils.utilization_overlay.cli_parse import command_for_device_type, parse_interface_counters
from utils.utilization_overlay.join import (
    join_observations_to_l2,
    topology_fingerprint,
)
from utils.utilization_overlay.model import OverlayValidationError, validate_overlay_document
from utils.utilization_overlay.rates import clamp_delta_seconds, pair_interface_samples

DEFAULT_DELTA_SECONDS = 10.0
LIVE_STALE_AFTER = 900
TARGETS_FILENAME = 'utilization_ssh_targets.json'
OVERLAY_FILENAME = 'utilization_overlay.json'
LogFn = Callable[[str], None]


class LiveUtilizationError(ValueError):
    """Operator-visible live collector failure (no secrets)."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _log(log: Optional[LogFn], msg: str) -> None:
    if log:
        log(msg)


def _redact(msg: str) -> str:
    lower = msg.lower()
    if any(k in lower for k in ('password', 'enable_pwd', 'secret', 'community')):
        return '[redacted]'
    if len(msg) > 240:
        return msg[:240] + '…'
    return msg


def _abort() -> bool:
    try:
        from utils.task_control_plane import should_abort
        return should_abort()
    except Exception:
        return False


def _sleep_cancelable(seconds: float) -> bool:
    """Sleep in slices. Return True if cancelled."""
    end = time.time() + max(0.0, seconds)
    while time.time() < end:
        if _abort():
            return True
        time.sleep(min(0.4, end - time.time()))
    return _abort()


def write_ssh_targets(
    diag_folder: str,
    results: Sequence[Dict[str, Any]],
    devices: Optional[Sequence[Dict[str, Any]]] = None,
) -> Optional[str]:
    """Map hostname (device_id) → inventory SSH host. Not topology."""
    if not diag_folder:
        return None
    dtype_by_host = {}
    for d in devices or []:
        if isinstance(d, dict) and d.get('host'):
            dtype_by_host[str(d.get('host')).lower()] = str(d.get('device_type') or '')
    rows = []
    for res in results or []:
        if not isinstance(res, dict) or res.get('status') != 'success':
            continue
        data = res.get('data') if isinstance(res.get('data'), dict) else {}
        device_id = str(data.get('true_host') or '').strip()
        inventory_host = str(res.get('device') or '').strip()
        if not device_id or not inventory_host:
            continue
        if device_id.startswith('VPC_Domain_'):
            continue
        rows.append({
            'device_id': device_id,
            'inventory_host': inventory_host,
            'device_type': dtype_by_host.get(inventory_host.lower()) or '',
        })
    path = os.path.join(diag_folder, TARGETS_FILENAME)
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump({
                '_README': (
                    'SSH targets for live utilization overlay. device_id is the Standard L2 '
                    'map node id. inventory_host is the inventory SSH address. Not a graph.'
                ),
                'targets': rows,
            }, fh, indent=2)
        return path
    except OSError:
        return None


def load_standard_l2_bind(diag_folder: str) -> Dict[str, Any]:
    """Load frozen Standard L2 nodes/edges from last map run. Does not recrawl."""
    if not diag_folder or not os.path.isdir(diag_folder):
        raise LiveUtilizationError(
            'No Standard L2 map artifacts. Build Inventory Standard L2 first.'
        )
    f4 = os.path.join(diag_folder, '04_final_map_data.json')
    if not os.path.isfile(f4):
        raise LiveUtilizationError(
            'Standard L2 map data missing (04_final_map_data.json). Rebuild the map.'
        )
    try:
        payload = json.load(open(f4, encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveUtilizationError(f'Standard L2 map data unreadable: {exc}') from exc
    nodes = payload.get('nodes') or []
    edges = payload.get('edges') or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise LiveUtilizationError('Standard L2 map data is malformed.')
    targets_path = os.path.join(diag_folder, TARGETS_FILENAME)
    targets: List[Dict[str, Any]] = []
    if os.path.isfile(targets_path):
        try:
            tdoc = json.load(open(targets_path, encoding='utf-8'))
            targets = list(tdoc.get('targets') or [])
        except (OSError, json.JSONDecodeError):
            targets = []
    return {
        'nodes': nodes,
        'edges': edges,
        'targets': targets,
        'html_file': os.path.join(diag_folder, 'topology_map_all.html'),
        'diag_folder': diag_folder,
    }


def select_eligible_devices(
    inventory: Sequence[Dict[str, Any]],
    map_nodes: Sequence[Dict[str, Any]],
    targets: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """SSH only inventory devices that already appear as Standard L2 map nodes."""
    node_ids = {}
    for n in map_nodes or []:
        if not isinstance(n, dict):
            continue
        nid = str(n.get('id') or '').strip()
        if not nid or nid.startswith('VPC_Domain_'):
            continue
        node_ids[nid.lower()] = nid
        info = n.get('device_info') if isinstance(n.get('device_info'), dict) else {}
        mgmt = str(info.get('mgmt_ip') or '').strip()
        if mgmt:
            node_ids.setdefault(mgmt.lower(), nid)

    by_id = {str(t.get('device_id') or '').lower(): t for t in (targets or []) if t.get('device_id')}
    by_host = {str(t.get('inventory_host') or '').lower(): t for t in (targets or []) if t.get('inventory_host')}

    eligible = []
    skipped = []
    seen_ids = set()
    for dev in inventory or []:
        if not isinstance(dev, dict):
            continue
        host = str(dev.get('host') or '').strip()
        dtype = str(dev.get('device_type') or '').strip()
        hinted = str(dev.get('hostname') or dev.get('name') or '').strip()
        device_id = None
        bind = by_host.get(host.lower()) or by_id.get(host.lower()) or by_id.get(hinted.lower())
        if bind:
            device_id = str(bind.get('device_id') or '').strip()
        if not device_id:
            for cand in (host, hinted):
                if cand.lower() in node_ids:
                    device_id = node_ids[cand.lower()]
                    break
        if not device_id:
            skipped.append(host or hinted or '?')
            continue
        if device_id.lower() not in {i.lower() for i in node_ids.values()} and device_id.lower() not in node_ids:
            skipped.append(host or device_id)
            continue
        canonical = node_ids.get(device_id.lower()) or device_id
        if canonical.lower() in seen_ids:
            continue
        seen_ids.add(canonical.lower())
        row = dict(dev)
        row['host'] = host
        row['device_type'] = dtype or (bind or {}).get('device_type') or row.get('device_type')
        row['map_device_id'] = canonical
        eligible.append(row)
    return eligible, skipped


def _sample_device(conn: Any, device_type: str) -> List[Dict[str, Any]]:
    cmd = command_for_device_type(device_type)
    raw = conn.send_command(cmd, read_timeout=45)
    if raw is None:
        raw = ''
    parsed = parse_interface_counters(str(raw), device_type)
    for row in parsed:
        row['command'] = cmd
        row['sampled_at'] = _now_iso()
    return parsed


def collect_two_samples_on_device(
    device: Dict[str, Any],
    user: str,
    pwd: str,
    enb_pwd: str,
    delta_seconds: float,
    log: Optional[LogFn] = None,
) -> Dict[str, Any]:
    """One device, two samples, same SSH session. Cancel between samples."""
    from modules.network_base import safe_connection

    host = device.get('host')
    dtype = device.get('device_type') or 'cisco_ios'
    map_id = device.get('map_device_id') or ''
    dt = clamp_delta_seconds(delta_seconds)
    if _abort():
        return {'status': 'cancelled', 'device_id': map_id, 'host': host, 't0': [], 't1': [], 'dt': 0}
    try:
        with safe_connection(device, user, pwd, enb_pwd, log, fallback_credentials=device.get('fallback_credentials')) as conn:
            from modules.network_base import resolve_hostname_from_connection, safe_node_name
            resolved = safe_node_name(
                resolve_hostname_from_connection(conn, host, dtype, log_func=None)
            ) or ''
            if map_id and resolved and resolved.lower() != map_id.lower():
                # Hostname from live SSH must match the frozen map node id.
                return {
                    'status': 'identity_mismatch',
                    'device_id': map_id,
                    'resolved': resolved,
                    'host': host,
                    't0': [],
                    't1': [],
                    'dt': 0,
                }
            if _abort():
                return {'status': 'cancelled', 'device_id': map_id, 'host': host, 't0': [], 't1': [], 'dt': 0}
            t0 = _sample_device(conn, dtype)
            _log(log, f"[UTIL-LIVE] {map_id or host}: sample t0 ({len(t0)} interfaces)")
            t0_ts = time.time()
            if _sleep_cancelable(dt):
                return {
                    'status': 'cancelled',
                    'device_id': map_id,
                    'host': host,
                    't0': t0,
                    't1': [],
                    'dt': time.time() - t0_ts,
                }
            t1 = _sample_device(conn, dtype)
            actual_dt = max(time.time() - t0_ts, 0.001)
            _log(log, f"[UTIL-LIVE] {map_id or host}: sample t1 ({len(t1)} interfaces) dt={actual_dt:.1f}s")
            return {
                'status': 'ok',
                'device_id': map_id,
                'host': host,
                't0': t0,
                't1': t1,
                'dt': actual_dt,
                'command': command_for_device_type(dtype),
            }
    except Exception as exc:
        err = _redact(str(exc))
        _log(log, f"[UTIL-LIVE] {map_id or host}: SSH error ({err})")
        return {
            'status': 'error',
            'device_id': map_id,
            'host': host,
            'error': err,
            't0': [],
            't1': [],
            'dt': 0,
        }


def _index_by_name(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        raw = str(row.get('if_name_raw') or '').strip()
        if raw:
            out[raw.lower()] = row
    return out


def observations_from_device_pair(result: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Turn t0/t1 into join observations + unmapped counter failures."""
    obs: List[Dict[str, Any]] = []
    unmapped: List[Dict[str, Any]] = []
    device_id = str(result.get('device_id') or '').strip()
    cmd = result.get('command')
    if result.get('status') == 'identity_mismatch':
        unmapped.append({
            'device_id': result.get('resolved') or device_id or str(result.get('host') or ''),
            'if_name_raw': '*',
            'if_name_normalized': None,
            'reason': 'identity_mismatch',
            'command': cmd,
        })
        return obs, unmapped
    if result.get('status') != 'ok':
        return obs, unmapped
    t0 = _index_by_name(result.get('t0') or [])
    t1 = _index_by_name(result.get('t1') or [])
    dt = float(result.get('dt') or 0) or DEFAULT_DELTA_SECONDS
    names = set(t0) | set(t1)
    for key in names:
        a = t0.get(key)
        b = t1.get(key)
        raw = (b or a or {}).get('if_name_raw') or key
        if not a or not b:
            unmapped.append({
                'device_id': device_id,
                'if_name_raw': raw,
                'if_name_normalized': (b or a or {}).get('if_name_normalized'),
                'reason': 'counter_invalid',
                'command': cmd,
            })
            continue
        paired = pair_interface_samples(a, b, dt)
        if not paired.get('ok'):
            unmapped.append({
                'device_id': device_id,
                'if_name_raw': raw,
                'if_name_normalized': b.get('if_name_normalized'),
                'reason': paired.get('reason') or 'counter_invalid',
                'command': cmd,
            })
            continue
        obs.append({
            'device_id': device_id,
            'if_name_raw': raw,
            'if_name_normalized': b.get('if_name_normalized'),
            'in_bps': paired.get('in_bps'),
            'out_bps': paired.get('out_bps'),
            'in_pct': paired.get('in_pct'),
            'out_pct': paired.get('out_pct'),
            'pct': paired.get('pct'),
            'if_speed_bps': paired.get('if_speed_bps'),
            'pct_gt_100': paired.get('pct_gt_100'),
            'sampled_at': b.get('sampled_at') or _now_iso(),
            'command': cmd,
        })
    return obs, unmapped


def build_live_overlay_document(
    *,
    observations: Sequence[Dict[str, Any]],
    extra_unmapped: Sequence[Dict[str, Any]],
    nodes: Sequence[Dict[str, Any]],
    edges: Sequence[Dict[str, Any]],
    topology_job_id: Optional[str],
    degraded: bool,
    delta_seconds: float,
    vendors: Sequence[str],
) -> Dict[str, Any]:
    joined = join_observations_to_l2(
        observations,
        nodes,
        edges,
        generated_at=_now_iso(),
        topology_job_id=topology_job_id,
        mode='live',
        evidence_class='live_ssh',
        stale_after_seconds=LIVE_STALE_AFTER,
    )
    unmapped = list(joined.get('unmapped') or [])
    for row in extra_unmapped:
        if row not in unmapped:
            unmapped.append(row)
    doc = {
        'schema': 'nst.utilization_overlay.v1',
        'mode': 'live',
        'evidence_class': 'live_ssh',
        'topology_job_id': topology_job_id,
        'generated_at': joined.get('generated_at') or _now_iso(),
        'stale_after_seconds': LIVE_STALE_AFTER,
        'degraded': bool(degraded or joined.get('error')),
        'collector': {
            'kind': 'ssh_cli',
            'vendors': [v for v in vendors if v],
            'delta_seconds_planned': float(delta_seconds),
        },
        'paints': [],
        'unmapped': unmapped,
        'summary': {
            'l2_edge_count': (joined.get('summary') or {}).get('l2_edge_count', 0),
            'painted_count': 0,
            'unmapped_count': len(unmapped),
            'partial_count': 0,
            'stale_count': 0,
        },
    }
    if joined.get('error'):
        # Identity mismatch fail-closed: no paints.
        return validate_overlay_document(doc)

    paints = []
    partial = 0
    stale = 0
    for p in joined.get('paints') or []:
        row = copy.deepcopy(p)
        row['provenance'] = {
            'mode': 'live',
            'evidence_class': 'live_ssh',
            'job_id': topology_job_id,
            'commands': list({
                c for c in (
                    [(x.get('command') or '') for x in observations]
                ) if c
            }),
        }
        fresh = row.get('freshness') if isinstance(row.get('freshness'), dict) else {}
        age = fresh.get('age_seconds')
        if age is None:
            age = 0
        fresh['stale'] = bool(LIVE_STALE_AFTER and age >= LIVE_STALE_AFTER)
        if fresh['stale']:
            stale += 1
            if row.get('paint_state') not in ('partial', 'no_speed', 'invalid', 'no_sample'):
                row['paint_state'] = 'stale'
        row['freshness'] = fresh
        if row.get('paint_state') == 'partial':
            partial += 1
        if (row.get('pct') or 0) > 100:
            row['pct_gt_100'] = True
        paints.append(row)
    doc['paints'] = paints
    doc['unmapped'] = unmapped
    doc['summary'] = {
        'l2_edge_count': (joined.get('summary') or {}).get('l2_edge_count', 0),
        'painted_count': len(paints),
        'unmapped_count': len(unmapped),
        'partial_count': partial,
        'stale_count': stale,
    }
    return validate_overlay_document(doc)


def write_overlay_json(diag_folder: str, doc: Dict[str, Any]) -> str:
    path = os.path.join(diag_folder, OVERLAY_FILENAME)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh, indent=2)
    return path


def _vis_js_raw() -> str:
    """Load bundled vis.js source. generate_topology_html wraps it in a script tag."""
    candidates = []
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    candidates.append(os.path.join(repo, 'modules', 'web', 'vis-network.min.js'))
    meipass = getattr(sys, '_MEIPASS', None) if getattr(sys, 'frozen', False) else None
    if meipass:
        candidates.insert(0, os.path.join(meipass, 'modules', 'web', 'vis-network.min.js'))
    for path in candidates:
        try:
            with open(path, encoding='utf-8') as fh:
                return fh.read()
        except OSError:
            continue
    return '// Offline vis-network library missing.'


def repaint_standard_l2_html(
    bind: Dict[str, Any],
    overlay_doc: Dict[str, Any],
    log: Optional[LogFn] = None,
) -> Optional[str]:
    """Regenerate Standard L2 HTML with overlay paint. Does not change the edge set."""
    from utils.report_formatter import generate_topology_html

    nodes = bind.get('nodes') or []
    edges = bind.get('edges') or []
    fp = topology_fingerprint(edges)
    html_file = bind.get('html_file')
    if not html_file:
        html_file = os.path.join(bind.get('diag_folder') or '', 'topology_map_all.html')
    generate_topology_html(
        html_file,
        len(nodes),
        len(edges),
        json.dumps(nodes),
        json.dumps(edges),
        _vis_js_raw(),
        map_mode='all',
        utilization_overlay=overlay_doc,
    )
    if topology_fingerprint(edges) != fp:
        raise LiveUtilizationError('overlay repaint mutated topology — refusing to keep HTML')
    _log(log, f"[UTIL-LIVE] Standard L2 HTML updated (topology unchanged): {os.path.basename(html_file)}")
    return html_file


def run_live_utilization(
    *,
    inventory: Sequence[Dict[str, Any]],
    user: str,
    pwd: str,
    enb_pwd: str,
    diag_folder: str,
    topology_job_id: Optional[str] = None,
    delta_seconds: float = DEFAULT_DELTA_SECONDS,
    log: Optional[LogFn] = None,
    credential_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Full live cycle. Requires vault credential_id at the API layer."""
    if not (credential_id or '').strip():
        raise LiveUtilizationError('credential_id required for live SSH utilization')
    bind = load_standard_l2_bind(diag_folder)
    fp_before = topology_fingerprint(bind['edges'])
    eligible, skipped = select_eligible_devices(inventory, bind['nodes'], bind['targets'])
    _log(
        log,
        f"[UTIL-LIVE] eligible map nodes={len(eligible)} skipped_not_on_map={len(skipped)} "
        f"(Live SSH — not SNMP)",
    )
    if not eligible:
        raise LiveUtilizationError(
            'No inventory devices match Standard L2 map nodes. '
            'Rebuild the Standard L2 map, then retry live SSH.'
        )
    dt = clamp_delta_seconds(delta_seconds)
    extra_unmapped: List[Dict[str, Any]] = []
    observations: List[Dict[str, Any]] = []
    degraded = False
    cancelled = False
    vendors = []
    errors = []
    for dev in eligible:
        if _abort():
            cancelled = True
            degraded = True
            break
        result = collect_two_samples_on_device(dev, user, pwd, enb_pwd, dt, log)
        vendors.append(str(dev.get('device_type') or ''))
        if result.get('status') == 'cancelled':
            cancelled = True
            degraded = True
            obs, um = observations_from_device_pair({**result, 'status': 'ok' if result.get('t0') and result.get('t1') else result.get('status')})
            if result.get('t0') and not result.get('t1'):
                for row in result.get('t0') or []:
                    extra_unmapped.append({
                        'device_id': result.get('device_id') or '',
                        'if_name_raw': row.get('if_name_raw') or '',
                        'if_name_normalized': row.get('if_name_normalized'),
                        'reason': 'counter_invalid',
                        'command': result.get('command'),
                    })
            else:
                observations.extend(obs)
                extra_unmapped.extend(um)
            break
        if result.get('status') == 'identity_mismatch':
            degraded = True
            obs, um = observations_from_device_pair(result)
            extra_unmapped.extend(um)
            continue
        if result.get('status') != 'ok':
            degraded = True
            errors.append(result.get('host') or result.get('device_id') or '?')
            continue
        obs, um = observations_from_device_pair(result)
        observations.extend(obs)
        extra_unmapped.extend(um)

    if cancelled and not observations and not extra_unmapped:
        extra_unmapped.append({
            'device_id': '',
            'if_name_raw': '*',
            'if_name_normalized': None,
            'reason': 'counter_invalid',
            'command': None,
        })

    try:
        doc = build_live_overlay_document(
            observations=observations,
            extra_unmapped=extra_unmapped,
            nodes=bind['nodes'],
            edges=bind['edges'],
            topology_job_id=topology_job_id,
            degraded=degraded or cancelled,
            delta_seconds=dt,
            vendors=sorted({v for v in vendors if v}),
        )
    except OverlayValidationError as exc:
        raise LiveUtilizationError(f'live overlay document invalid: {exc}') from exc

    if topology_fingerprint(bind['edges']) != fp_before:
        raise LiveUtilizationError('live collector mutated topology — aborting write')

    overlay_path = write_overlay_json(bind['diag_folder'], doc)
    html_path = None
    try:
        html_path = repaint_standard_l2_html(bind, doc, log)
    except Exception as exc:
        degraded = True
        _log(log, f"[UTIL-LIVE] HTML repaint skipped: {_redact(str(exc))}")

    status = 'cancelled' if cancelled else 'complete'
    return {
        'status': status,
        'degraded': bool(doc.get('degraded') or degraded),
        'overlay_path': overlay_path,
        'html_path': html_path,
        'painted_count': (doc.get('summary') or {}).get('painted_count', 0),
        'unmapped_count': (doc.get('summary') or {}).get('unmapped_count', 0),
        'eligible_count': len(eligible),
        'skipped_not_on_map': skipped,
        'ssh_errors': errors,
        'mode': 'live',
        'evidence_class': 'live_ssh',
        'message': (
            'Live SSH — not SNMP. Paint is not topology. '
            + ('Cancelled — partial overlay only. ' if cancelled else '')
            + ('Degraded — some devices failed. ' if degraded else '')
        ),
    }
