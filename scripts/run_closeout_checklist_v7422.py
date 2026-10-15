#!/usr/bin/env python3
"""Execute CLOSEOUT_PLAN_v7422.md checklist. Writes CLOSEOUT_RESULTS_v7422.md.

Do not skip rows. Exit code 0 only if every executed check PASSes.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS: list[tuple[str, str, str]] = []


def record(cid: str, ok: bool, detail: str) -> None:
    status = 'PASS' if ok else 'FAIL'
    RESULTS.append((cid, status, detail))
    print(f"[{status}] {cid}: {detail}")


def html_text() -> str:
    return (ROOT / 'modules/web/templates/index.html').read_text(encoding='utf-8')


def check_ui_static() -> None:
    ver = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    record('T-UI-01', ver == '7.4.22', f'VERSION={ver!r}')

    css = ROOT / 'modules/web/static/nst-enterprise.css'
    record('T-UI-02', css.is_file() and css.stat().st_size > 500, f'exists size={css.stat().st_size if css.is_file() else 0}')

    html = html_text()
    record('T-UI-03', 'nst-enterprise.css' in html, 'link tag present' if 'nst-enterprise.css' in html else 'missing link')

    # decorative emoji scan (U+1F300–U+1FAFF) in index
    emos = sorted(set(re.findall(r'[\U0001F300-\U0001FAFF]', html)))
    record('T-UI-05', len(emos) == 0, f'remaining={emos[:20]}')

    record('T-UI-06', '#faf5ff' not in html and '#581c87' not in html, 'purple novelty absent')
    record('T-UI-07', 'sidebar-brand-refined .logo-wrap' in html and 'display: flex !important' in html.replace('display:flex !important', 'display: flex !important'), 'brand visible CSS')
    record('T-UI-08', 'ENTERPRISE SHELL' in html or 'nst-ws-btn[aria-current="page"]' in html, 'pill nav CSS')
    record('T-UI-09', (ROOT / 'utils/map_shell_theme.py').is_file(), 'map_shell_theme.py')

    l3 = (ROOT / 'utils/l3_map_shell.py').read_text(encoding='utf-8')
    record('T-UI-10', 'enterprise_map_css' in l3 and 'nst-map-font' in l3, 'L3 theme wired')
    std = (ROOT / 'utils/standard_map_shell.py').read_text(encoding='utf-8')
    record('T-UI-11', 'enterprise_map_css' in std and '0a84ff' in std, 'Standard L2 theme')
    vpc = (ROOT / 'utils/vpc_map_shell.py').read_text(encoding='utf-8')
    record('T-UI-12', 'enterprise_map_css' in vpc and '0a84ff' in vpc, 'vPC theme')
    disc = (ROOT / 'utils/discovery_map_shell.py').read_text(encoding='utf-8')
    record('T-UI-13', 'enterprise_map_css' in disc, 'Discovery theme')
    topo = (ROOT / 'utils/topo_map_shell.py').read_text(encoding='utf-8')
    record('T-UI-14', "accent='#0a84ff'" in topo and 'enterprise_map_css' in topo, 'Topo theme accent')


def check_buttons() -> None:
    html = html_text()
    calls = set(re.findall(r'onclick="([A-Za-z_][A-Za-z0-9_]*)\s*\(', html))
    defined = set(re.findall(r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', html))
    defined |= set(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?function\s*\(', html))
    missing = sorted(c for c in calls - defined if c not in {'confirm', 'alert', 'open', 'close', 'focus', 'blur'})
    record('T-BTN-01', not missing, f'missing={missing[:25]}' if missing else f'ok handlers={len(calls)}')

    for cid, names in (
        ('T-BTN-02', ('refreshInterfaceMap', 'exportInterfaceMap', 'clearImLogs', 'downloadImLogs')),
        ('T-BTN-03', ('nstRevealJob', 'nstRerunJob', 'nstLoadEvidence')),
        ('T-BTN-04', ('editCredential', 'saveCredential', 'removeCredential')),
        ('T-BTN-05', ('runPathTrace', 'nstShortcutPathTrace', 'nstUpdatePathTraceGate')),
        ('T-BTN-06', ('loadPluginHistory', 'rollbackPlugin', 'reloadPlugins')),
        ('T-BTN-07', ('nstRunSnmpGraphs', 'nstOpenSnmpGraphs')),
        ('T-BTN-08', ('healthCheckRun', 'healthWizardDismiss')),
    ):
        miss = [n for n in names if f'function {n}' not in html]
        record(cid, not miss, 'ok' if not miss else f'missing {miss}')

    record('T-BTN-09', all(f'id="ws-nav-{w}"' in html for w in ('inventory', 'maps', 'find', 'change', 'evidence', 'reports', 'settings')) and 'function nstShowWorkspace' in html, 'workspaces 1-7')
    record('T-BTN-10', all(f'id="tab-segment-{t}"' in html for t in ('diag', 'tools', 'credentials', 'about')), 'legacy segments')


def check_apis() -> None:
    os.environ.setdefault('NST_DATA_DIR', str(ROOT / '.tmp_closeout_data'))
    from utils import output_paths, job_index
    output_paths._DATA_ROOT = None
    db = Path(os.environ['NST_DATA_DIR']) / 'index' / 'jobs.sqlite'
    db.parent.mkdir(parents=True, exist_ok=True)
    job_index.reset_for_tests(str(db))

    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager
    vault = Path(os.environ['NST_DATA_DIR']) / 'vault'
    vault.mkdir(parents=True, exist_ok=True)
    web.app.config['TESTING'] = True
    web.credential_manager = CredentialManager(storage_dir=str(vault))
    c = web.app.test_client()
    env = {'REMOTE_ADDR': '127.0.0.1'}

    r = c.get('/', environ_base=env)
    body = r.get_data(as_text=True)
    record('T-API-01', r.status_code == 200 and '7.4.22' in body and 'nst-enterprise.css' in body, f'status={r.status_code}')

    css = c.get('/static/nst-enterprise.css', environ_base=env)
    record('T-UI-04', css.status_code == 200 and b'--color-accent' in css.data, f'status={css.status_code} len={len(css.data)}')

    ver = c.get('/api/version', environ_base=env)
    record('T-API-02', ver.status_code == 200 and (ver.get_json() or {}).get('version') == '7.4.22', str(ver.get_json()))

    for cid, path in (
        ('T-API-03', '/api/credentials/list'),
        ('T-API-04', '/api/jobs?limit=5'),
        ('T-API-07', '/api/plugins/list'),
        ('T-API-09', '/api/backups'),
        ('T-API-10', '/api/capabilities/parsers'),
    ):
        rr = c.get(path, environ_base=env)
        record(cid, rr.status_code == 200, f'status={rr.status_code}')

    ts = c.get('/api/topology/status', environ_base=env)
    tj = ts.get_json() or {}
    record('T-API-05', ts.status_code == 200 and 'edge_count' in tj, str(tj.keys()))

    es = c.get('/api/topology/edges-status', environ_base=env)
    ej = es.get_json() or {}
    record('T-API-06', es.status_code == 200 and 'has_l2_edges' in ej, str(ej))

    hist = c.get('/api/plugins/history/x', environ_base=env)
    record('T-API-08', hist.status_code == 200 and isinstance((hist.get_json() or {}).get('history'), list), str(hist.status_code))

    hc = c.post('/api/health-check/run', json={'mode': 'quick'}, environ_base=env)
    record('T-API-11', hc.status_code == 200, f'status={hc.status_code}')

    sn = c.post('/api/snmp/interface-graphs', json={'host': '10.0.0.1'}, environ_base=env)
    sj = sn.get_json() or {}
    record('T-API-12', sn.status_code == 200 and sj.get('status') in ('ok', 'unavailable'), str(sj.get('status')))

    pt = c.post('/api/path-trace', json={'mac': '', 'reconstruct_only': True}, environ_base=env)
    record('T-API-13', pt.status_code in (200, 400), f'status={pt.status_code}')

    # synthetic evidence job
    job_index.init_db()
    run = output_paths.prepare_run_output(output_paths.CAT_INTERFACES, 'closeout')
    report = output_paths.path_in_run(run, 'report.html')
    Path(report).write_text('<html>ok</html>', encoding='utf-8')
    tid = 'closeout00test'
    job_index.record_start(tid, 'interfaces', inventory_source='committed', device_count=1)
    job_index.record_run_dir(tid, run['run_dir'])
    job_index.record_status(tid, 'complete')
    opened = c.get(f'/api/jobs/{tid}/open', environ_base=env)
    rerun = c.post(f'/api/jobs/{tid}/rerun', environ_base=env)
    record('T-API-14', opened.status_code == 200 and rerun.status_code == 200 and (rerun.get_json() or {}).get('action') == 'interfaces', f'open={opened.status_code} rerun={rerun.status_code}')

    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def check_maps() -> None:
    l3 = (ROOT / 'utils/l3_map_shell.py').read_text(encoding='utf-8')
    record('T-MAP-01', all(x in l3 for x in ('btn-flow', 'btn-fit', 'btn-reset', 'btn-trace-flow')), 'L3 toolbar ids')
    record('T-MAP-02', 'disabled until traffic collection' not in l3 and 'Animate LPM flow' in l3, 'flow not stub')
    std = (ROOT / 'utils/standard_map_shell.py').read_text(encoding='utf-8')
    record('T-MAP-03', 'nst-toolbar' in std or 'toolbar' in std.lower(), 'standard toolbar')
    vpc = (ROOT / 'utils/vpc_map_shell.py').read_text(encoding='utf-8')
    record('T-MAP-04', 'vpc-map-toolbar' in vpc, 'vpc toolbar')


def check_regressions() -> None:
    suites = [
        ('T-REG-01', ['tests/test_closeout_v7422.py']),
        ('T-REG-02', ['tests/test_gap_closeout_noc.py']),
        ('T-REG-03', ['tests/test_oss_wow_noc_features.py']),
        ('T-REG-04', ['tests/test_phase1_shell.py']),
        ('T-REG-05', ['tests/test_p1_ux_navigation.py']),
        ('T-REG-06', ['tests/test_topo_map_shell.py', 'tests/test_vpc_map_html_contract.py']),
    ]
    for cid, args in suites:
        cmd = [sys.executable, '-m', 'pytest', *args, '-q', '--tb=line']
        # skip missing files
        args2 = [a for a in args if (ROOT / a).exists()]
        if not args2:
            record(cid, False, f'missing suites {args}')
            continue
        cmd = [sys.executable, '-m', 'pytest', *args2, '-q', '--tb=line']
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        ok = p.returncode == 0
        tail = (p.stdout or p.stderr or '')[-400:].replace('\n', ' ')
        record(cid, ok, tail if not ok else 'pytest ok')

    p = subprocess.run(
        [sys.executable, 'scripts/mandatory_release_qa.py', '--phase', 'every_code_change'],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    ok = p.returncode == 0 and 'MANDATORY RELEASE QA: PASS' in (p.stdout or '')
    record('T-REG-07', ok, (p.stdout or p.stderr or '')[-300:].replace('\n', ' '))


def write_results() -> int:
    out = ROOT / '.cursor/audits/CLOSEOUT_RESULTS_v7422.md'
    fails = [r for r in RESULTS if r[1] == 'FAIL']
    lines = [
        '# Closeout Results — v7.4.22',
        '',
        f'Executed: {datetime.now(timezone.utc).isoformat()}',
        f'Total: {len(RESULTS)}  PASS: {len(RESULTS)-len(fails)}  FAIL: {len(fails)}',
        '',
        '| Check ID | Status | Detail |',
        '|---|---|---|',
    ]
    for cid, status, detail in RESULTS:
        safe = detail.replace('|', '\\|')[:240]
        lines.append(f'| {cid} | {status} | {safe} |')
    lines.append('')
    if fails:
        lines.append('## Failed checks')
        for cid, _, detail in fails:
            lines.append(f'- **{cid}**: {detail}')
    else:
        lines.append('## Verdict')
        lines.append('ALL CHECKS PASSED against CLOSEOUT_PLAN_v7422.md.')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {out}')
    return 1 if fails else 0


def main() -> int:
    check_ui_static()
    check_buttons()
    check_apis()
    check_maps()
    # regressions last (includes writing companion pytest)
    check_regressions()
    return write_results()


if __name__ == '__main__':
    raise SystemExit(main())
