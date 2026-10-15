#!/usr/bin/env python3
"""Exhaustive validation against the Docker SSH lab (1 IOS + 2× NX-OS 93180).

Usage (server on 5051, lab up, vault with lab-admin credential):
  python scripts/lab_exhaustive_validate.py
  python scripts/lab_exhaustive_validate.py --credential-id lab-admin

Writes: .cursor/audits/LAB_EXHAUSTIVE_VALIDATION_*.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:5051'
INV = (ROOT / 'lab' / 'docker' / 'inventory.nst.txt').read_text(encoding='utf-8')


def _set_base(url: str) -> None:
    global BASE
    BASE = url.rstrip('/')

# Execute actions exposed by the UI (maps + find + change + tools). Mutating VLAN
# dry-run only. Discovery demo covered separately.
EXECUTE_ACTIONS = [
    ('connectivity', {}),
    ('reachability_matrix', {}),
    ('vlan_check', {}),
    ('audit', {}),
    ('cisco_asset_warranty', {'params': {'include_modules': True, 'collection_policy': 'ssh_first'}}),
    ('interfaces', {'int_filter': ''}),
    ('topology', {'map_mode': 'all'}),
    ('topology', {'map_mode': 'vpc'}),
    ('l3_topology', {}),
    ('flow_map', {}),
    ('backup', {}),
    ('mac_check', {'mac_address': '0011.2233.4455'}),
    ('description_search', {'desc_search': 'uplink'}),
    ('node_analyze', {'node_id': 'LAB-NXOS-LEAF2'}),
    ('add_vlan', {'vlan_id': '99', 'vlan_name': 'LABTEST', 'dry_run': True}),
    ('failure_correlation', {}),
]


def _req(method: str, path: str, body: dict | None = None, timeout: float = 30):
    data = None
    headers = {'Content-Type': 'application/json'}
    if body is not None:
        data = json.dumps(body).encode('utf-8')
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, {'_raw': raw[:500]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace')
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {'_error': raw[:500]}
    except Exception as e:
        return 0, {'_error': f'{type(e).__name__}: {e}'}


def wait_task(task_id: str, timeout: float = 120) -> dict:
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        code, last = _req('GET', f'/api/jobs/{task_id}')
        if code == 200 and last.get('status') in ('complete', 'error', 'cancelled', 'partial'):
            return last
        code2, jobs = _req('GET', '/api/jobs?limit=20')
        if code2 == 200:
            rows = jobs.get('jobs') if isinstance(jobs, dict) else jobs
            for j in rows or []:
                if j.get('task_id') == task_id and j.get('status') in ('complete', 'error', 'cancelled', 'partial'):
                    return j
        time.sleep(1.0)
    return last or {'status': 'timeout'}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://127.0.0.1:5051', help='NST base URL')
    ap.add_argument('--credential-id', default='lab-admin')
    ap.add_argument('--username', default='lab-admin')
    args = ap.parse_args()
    _set_base(args.base)

    results = []
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')

    # Static UI contracts
    code, ver = _req('GET', '/api/version')
    results.append(('GET /api/version', code == 200, ver))
    # UI contracts from source (always) + live page when server up
    src = (ROOT / 'modules' / 'web' / 'templates' / 'index.html').read_text(encoding='utf-8')
    results.append(('UI nstSyncCredIdsFromSidebar', 'nstSyncCredIdsFromSidebar' in src, {}))
    results.append(('UI draft-only session creds copy', 'Draft only' in src and 'not</b> sent' in src, {}))
    results.append(('UI inventory utilities tiles', 'tools-inventory-utilities' in src, {}))
    try:
        with urllib.request.urlopen(BASE + '/', timeout=15) as resp:
            page = resp.read().decode('utf-8', errors='replace')
        results.append(('Live index serves vault UX', 'Draft only' in page or 'credential_id' in page, {'bytes': len(page)}))
    except Exception as e:
        results.append(('Live index serves vault UX', False, {'_error': str(e)}))

    # Map HTML contract (offline generate)
    try:
        sys.path.insert(0, str(ROOT))
        from utils.report_formatter import generate_topology_html
        import tempfile
        p = Path(tempfile.mkdtemp()) / 'std.html'
        generate_topology_html(
            str(p), 2, 1,
            json.dumps([{'id': 'a', 'label': 'LEAF1'}, {'id': 'b', 'label': 'ACCESS1'}]),
            json.dumps([{'from': 'a', 'to': 'b', 'label': 'Eth1/1'}]),
            '', map_mode='all',
        )
        t = p.read_text(encoding='utf-8')
        results.append(('Standard L2 body.nst-standard-map', 'nst-standard-map' in t, {'bytes': len(t)}))
        results.append(('Standard L2 Apex cyan --acc', '#00c2d7' in t, {}))
        results.append(('Standard L2 no DEBUG spam in file', '[DEBUG]' not in t, {}))
    except Exception as e:
        results.append(('Standard L2 generate', False, {'_error': str(e)}))

    # SSH lab probe
    try:
        import paramiko
        for port, expect in [(2201, 'LAB-IOS-ACCESS1'), (2202, 'LAB-NXOS-LEAF1'), (2203, 'LAB-NXOS-LEAF2')]:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect('127.0.0.1', port=port, username='x', password='y', look_for_keys=False, allow_agent=False, timeout=5)
            ch = c.invoke_shell()
            time.sleep(0.4)
            banner = ch.recv(4096).decode(errors='replace') if ch.recv_ready() else ''
            ch.send('show inventory\n')
            time.sleep(0.6)
            out = ch.recv(16384).decode(errors='replace') if ch.recv_ready() else ''
            ok = expect.split('-')[0] in banner or expect in banner or '93180' in out or 'C9300' in out or 'N9K' in out
            results.append((f'SSH lab :{port} {expect}', ok, {'banner': banner[:40]}))
            c.close()
    except Exception as e:
        results.append(('SSH lab probe', False, {'_error': str(e)}))

    # Vault status
    code, vault = _req('GET', '/api/credentials/master-password/status')
    results.append(('Vault status', code == 200, vault))

    # Commit inventory + execute matrix (requires credential)
    # Ensure lab vault credential exists (idempotent)
    code, add = _req('POST', '/api/credentials/add', {
        'username': args.credential_id,
        'password': 'lab-pass',
        'label': 'Docker SSH lab',
        'force': True,
    })
    results.append(('Vault add lab credential', code in (200, 201) or 'already' in str(add).lower() or add.get('success'), add))

    code, prev = _req('POST', '/api/inventory/preview', {'inventory': INV})
    if code != 200:
        code, prev = _req('POST', '/api/inventory/preview', {'text': INV})
    results.append(('Inventory preview', code == 200 and (prev.get('accepted_count') or prev.get('ok_count') or 0) >= 3 or 'rows' in str(prev), prev))
    code, commit = _req('POST', '/api/inventory/commit', {
        'text': INV, 'mode': 'replace', 'confirm': True,
    })
    results.append(('Inventory commit', code == 200, commit))

    for action, extra in EXECUTE_ACTIONS:
        body = {
            'action': action,
            'username': args.username,
            'credential_id': args.credential_id,
            'target_mode': 'bulk',
            'filter': '',
            'group': 'All',
            'inventory_source': 'committed',
            'inv_run_unsaved': False,
            **extra,
        }
        if action == 'topology':
            body['map_mode'] = extra.get('map_mode', 'all')
        code, started = _req('POST', '/api/execute', body, timeout=60)
        ok_start = code == 200 and started.get('status') in ('started', 'ok', 'complete')
        detail = {'http': code, 'resp': started}
        if ok_start and started.get('task_id'):
            done = wait_task(started['task_id'], timeout=180)
            detail['final'] = {
                'status': done.get('status'),
                'run_dir': done.get('run_dir'),
                'error': done.get('error') or done.get('error_summary'),
            }
            ok = done.get('status') in ('complete', 'partial')
            # Topology / map actions must produce HTML under run_dir (honesty gate).
            if ok and action in ('topology', 'l3_topology', 'flow_map'):
                run_dir = done.get('run_dir') or ''
                html_ok = False
                html_hits = []
                if run_dir:
                    # run_dir may be relative to NST_DATA_DIR
                    data_roots = [
                        Path(os.environ.get('NST_DATA_DIR', '')),
                        Path('/tmp/nst-lab-go2'),
                        Path('/tmp/nst-lab-go'),
                        ROOT,
                    ]
                    candidates = [Path(run_dir)]
                    for dr in data_roots:
                        if dr and str(dr) not in ('', '.'):
                            candidates.append(dr / run_dir)
                    for base in candidates:
                        if base.is_dir():
                            html_hits = list(base.glob('*.html'))
                            if html_hits:
                                html_ok = True
                                break
                detail['html_artifacts'] = [str(h.name) for h in html_hits[:5]]
                if not html_ok:
                    ok = False
                    detail['artifact_error'] = 'no HTML in run_dir'
                else:
                    # Live map quality contracts
                    ht = html_hits[0].read_text(encoding='utf-8', errors='replace')
                    if action == 'topology' and extra.get('map_mode') == 'all':
                        detail['map_quality'] = {
                            'nst_standard_map': 'nst-standard-map' in ht,
                            'no_legacy_side_panel_dom': 'id="side-panel"' not in ht,
                            'collapsed_honesty': 'nst-program-status-banner' in ht and '<details' in ht,
                            'apex_cyan': '#00c2d7' in ht,
                            'bytes': len(ht),
                        }
                        if not detail['map_quality']['nst_standard_map'] or not detail['map_quality']['no_legacy_side_panel_dom']:
                            ok = False
                    elif action == 'l3_topology':
                        # Prefer run_dir JSON truth over HTML shell size
                        route_count = 0
                        mf = None
                        for base in candidates:
                            if base.is_dir():
                                mp = base / 'manifest.json'
                                if mp.is_file():
                                    mf = json.loads(mp.read_text(encoding='utf-8'))
                                    route_count = int(mf.get('route_count') or 0)
                                    break
                        detail['map_quality'] = {
                            'l3_title': 'L3' in ht[:500] or 'Routing' in ht[:800],
                            'vis': 'vis.Network' in ht or 'vis-network' in ht,
                            'empty_banner': 'empty-routes-banner' in ht,
                            'route_count': route_count,
                            'bytes': len(ht),
                        }
                        # Lab fabric must yield parsed routes (fixtures). Empty HTML shell ≠ success.
                        if route_count < 1:
                            ok = False
                            detail['artifact_error'] = 'l3 route_count < 1'
                        if len(ht) < 10_000:
                            ok = False
        else:
            ok = ok_start
        label = f"execute {action}" + (f"/{extra.get('map_mode')}" if 'map_mode' in extra else '')
        results.append((label, ok, detail))
        time.sleep(0.3)

    # Negative: hidden/settings passwords alone must not start SSH work
    code, denied = _req('POST', '/api/execute', {
        'action': 'connectivity',
        'username': '',
        'password': 'typed-but-not-vault',
        'credential_id': '',
        'target_mode': 'bulk',
        'inventory_source': 'committed',
    })
    denied_ok = code in (400, 401, 403) or (
        isinstance(denied, dict) and (
            denied.get('error') or denied.get('status') in ('error', 'denied')
            or 'credential' in json.dumps(denied).lower()
        )
    )
    # If server still starts without credential_id, that is a FAIL (hidden-cred bug).
    if code == 200 and denied.get('status') in ('started', 'ok', 'complete'):
        denied_ok = False
    results.append(('Reject execute without credential_id', denied_ok, {'http': code, 'resp': denied}))

    # Discovery demo (no SSH)
    code, disc = _req('POST', '/api/discovery/run', {
        'seed_hosts': ['10.10.1.1'],
        'demo_mode': True,
        'generate_topology_html': True,
        'credential_id': args.credential_id,
        'username': args.username,
        'max_depth': 1,
    })
    results.append(('Discovery demo start', code in (200, 202) or disc.get('status') in ('started', 'ok'), disc))

    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(n, d) for n, ok, d in results if not ok]
    out_dir = ROOT / '.cursor' / 'audits'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'LAB_EXHAUSTIVE_VALIDATION_{ts[:10]}.md'
    lines = [
        f'# Lab exhaustive validation — {ts}',
        '',
        f'**Score:** {passed}/{len(results)} passed',
        f'**Lab:** Docker SSH — IOS C9300 + 2× N9K-C93180YC-EX (`lab/docker/`)',
        f'**credential_id:** `{args.credential_id}`',
        '',
        '## Results',
        '',
    ]
    for name, ok, detail in results:
        mark = 'PASS' if ok else 'FAIL'
        lines.append(f'- **{mark}** `{name}`')
        if not ok:
            lines.append(f'  - detail: `{json.dumps(detail, default=str)[:400]}`')
    lines.extend(['', '## Failures summary', ''])
    if not failed:
        lines.append('None.')
    else:
        for name, detail in failed:
            lines.append(f'- `{name}`: {json.dumps(detail, default=str)[:300]}')
    lines.extend([
        '',
        '## Known honesty limits',
        '',
        '- Docker SSH sim is CLI fixture-backed (not real NX-OS QEMU). CDP is scripted for Standard L2.',
        '- Settings password fields are draft-only; vault `credential_id` is mandatory (Zero Trust).',
        '- Full browser click-through of every control is complementary (Playwright); this script covers API + map HTML contracts.',
        '',
    ])
    out_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{passed}/{len(results)} passed → {out_path}')
    for name, detail in failed:
        print('FAIL', name)
    return 0 if not failed else 1


if __name__ == '__main__':
    raise SystemExit(main())
