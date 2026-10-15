#!/usr/bin/env python3
"""Expert full-program static + live smoke validation for Network Swiss Tool Pro.

Validates GUI contracts, API surface reachability, credential fallback wiring,
plugin registry, consolidator, and key operator screens — zero-trust style.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

fails: list[str] = []
passes = 0


def check(name: str, cond: bool, detail: str = '') -> None:
    global passes
    if cond:
        passes += 1
        print(f'PASS  {name}')
    else:
        fails.append(name)
        print(f'FAIL  {name}{(" — " + detail) if detail else ""}')


def section(title: str) -> None:
    print(f'\n=== {title} ===')


def validate_static() -> None:
    section('STATIC — GUI / wiring contracts')
    html = (ROOT / 'modules/web/templates/index.html').read_text(encoding='utf-8')
    web = (ROOT / 'vlan_checker_web.py').read_text(encoding='utf-8')
    nb = (ROOT / 'modules/network_base.py').read_text(encoding='utf-8')

    check('VERSION file readable', (ROOT / 'VERSION').exists())
    ver = (ROOT / 'VERSION').read_text().strip()
    check(f'VERSION={ver}', bool(ver))

    check('sidebar primary', 'id="sidebar_primary_cred"' in html)
    check('sidebar secondary enabled', not re.search(r'id="sidebar_secondary_cred"[^>]*\bdisabled\b', html))
    check('sidebar third enabled', not re.search(r'id="sidebar_third_cred"[^>]*\bdisabled\b', html))
    check('runAction uses nstCredentialRequestBody', 'Object.assign(payload, nstCredentialRequestBody())' in html)
    check('Use Primary/2nd/3rd', all(x in html for x in ('Use Primary', 'Use 2nd', 'Use 3rd')))

    # Topology is invoked with map mode arg, not bare runAction('topology')
    check(
        'topology map trigger',
        "runAction('topology'" in html or 'runAction("topology"' in html or 'runAction(\'topology\'' in html
        or re.search(r"runAction\(\s*'topology'", html) is not None
        or 'runAction(\'topology\'' in html
        or "runAction('topology'" in html
        or 'buildStandardMap' in html
        or "runAction('topology'" in html
        or ("runAction('topology'" in html)
        or ('topology' in html and 'runAction' in html and ("'topology'" in html)),
    )
    # More precise topology check
    topo_ok = bool(re.search(r"runAction\(\s*['\"]topology['\"]", html))
    check('topology runAction(map)', topo_ok)

    for action in (
        'connectivity', 'vlan_check', 'mac_check', 'interfaces', 'audit', 'backup',
        'save_config', 'cisco_asset_warranty', 'description_search', 'vlan_compare',
        'add_vlan', 'delete_vlan', 'find_missing_vlan',
    ):
        check(f'Tools button {action}', f"runAction('{action}')" in html or f'runAction("{action}")' in html)
    # L3 maps use L3_ACTION_MAP → runAction(action); action id must still be wired
    check(
        'Tools button l3_topology',
        "'l3_topology'" in html or '"l3_topology"' in html,
    )

    for ws in ('inventory', 'maps', 'reports'):
        check(f'workspace nav {ws}', f"nstShowWorkspace('{ws}')" in html)

    for tab in ('vlan', 'interfaces', 'plugins', 'credentials', 'discovery', 'interface_manager'):
        check(f'tab {tab}', f"switchTab('{tab}'" in html)

    check('Discovery run', 'discRunDiscovery' in html)
    check('STP scan', 'stpRunScan' in html)
    check('IM discover', "runInterfaceManagerAction('discover')" in html)
    check('Plugin execute', 'executeSelectedPlugin' in html)
    check('Asset warranty consolidate UI', 'generateAssetWarrantyConsolidatedReport' in html)
    check('Fleet reachability button', "runAction('reachability_matrix')" in html)
    check('Backup list UI', 'nstLoadBackupList' in html)
    check('Backup diff UI', 'nstDiffBackups' in html)
    check('Evidence pack download', "/api/jobs/" in html and 'pack' in html)

    check('execute stamps fallback devices', 'attach_fallback_to_devices' in web)
    check('session API secondary/third', 'secondary_credential_id' in web)
    check('connect_device helper', 'def connect_device' in nb)
    check('non-cisco label', 'not a cisco device' in (ROOT / 'modules/asset_collection_policy.py').read_text())

    # No connect_permissive leaks
    leaks = []
    for f in list((ROOT / 'modules').rglob('*.py')) + list((ROOT / 'utils').rglob('*.py')):
        if f.name == 'network_base.py':
            continue
        for i, line in enumerate(f.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            if 'connect_permissive(' in line and 'import' not in line and not line.strip().startswith('#'):
                leaks.append(f'{f.relative_to(ROOT)}:{i}')
    check('no connect_permissive leaks', not leaks, str(leaks[:5]))


def validate_plugins_registry() -> None:
    section('PLUGINS — registry load')
    from modules.plugin_registry import get_registry
    reg = get_registry()
    reg.reload()
    plugins = list(getattr(reg, '_plugins', {}) or {})
    check('plugins loaded >= 10', len(plugins) >= 10, f'count={len(plugins)}')
    for need in (
        'cisco_asset_warranty', 'serial_number', 'network_discovery',
        'interface_manager', 'vlan_audit', 'vpc_domain',
    ):
        check(f'plugin present {need}', need in plugins)


def validate_fallback_mock() -> None:
    section('CREDENTIAL FALLBACK — mock device order')
    from modules.network_base import safe_connection, attach_fallback_to_devices, connect_device

    attempts: list[str] = []

    def fake_connect(target, user, pwd, enb, log_func=None):
        attempts.append(user)
        if user != 'secondary_user':
            raise Exception('auth failed')
        m = MagicMock()
        m.disconnect = MagicMock()
        m.find_prompt.return_value = 'sw#'
        m.send_command.return_value = 'Cisco IOS'
        return m

    fb = [{'username': 'secondary_user', 'password': 'ok', 'enable_pwd': '', 'label': 'S'}]
    device = {'host': '10.9.9.9', 'device_type': 'cisco_ios'}
    with patch('modules.network_base.connect_permissive', side_effect=fake_connect):
        with safe_connection(device, 'primary_user', 'bad', '', fallback_credentials=fb) as conn:
            check('safe_connection got conn', conn is not None)
    check('attempt order P→S', attempts == ['primary_user', 'secondary_user'], str(attempts))

    attempts.clear()
    stamped = attach_fallback_to_devices([device], fallback_credentials=fb)[0]
    with patch('modules.network_base.connect_permissive', side_effect=fake_connect):
        connect_device(stamped, 'primary_user', 'bad', '')
    check('connect_device stamp order P→S', attempts == ['primary_user', 'secondary_user'], str(attempts))


def validate_non_cisco() -> None:
    section('ASSET WARRANTY — non-Cisco honesty')
    from modules.asset_collection_policy import collect_device_assets, NON_CISCO_DEVICE_LABEL
    from utils.report_formatter import format_asset_warranty_csv, format_asset_warranty_html

    bundle = collect_device_assets(
        {'host': '10.1.1.1', 'device_type': 'juniper_junos'},
        {'username': 'u', 'password': 'p'},
        {'collection_policy': 'ssh_only'},
        None,
    )
    asset = bundle['assets'][0]
    check('juniper status label', asset.get('warranty_status') == NON_CISCO_DEVICE_LABEL)
    html = format_asset_warranty_html({'host': '10.1.1.1', 'assets': [asset]}, '10.1.1.1')
    csv = format_asset_warranty_csv({'host': '10.1.1.1', 'assets': [asset]}, '10.1.1.1')
    check('html contains label', 'not a cisco device' in html.lower())
    check('csv contains label', 'not a cisco device' in csv.lower())


def validate_consolidator() -> None:
    section('CONSOLIDATOR — multi-file HTML+CSV')
    from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
    from utils.report_formatter import format_asset_warranty_csv

    tmp = tempfile.mkdtemp()
    cons = AssetWarrantyConsolidator(base_dir=str(Path(tmp) / 'reports'))
    csv1 = format_asset_warranty_csv({
        'host': '10.0.0.1',
        'assets': [{
            'host': '10.0.0.1', 'hostname': 'a', 'pid': 'C9300-48P',
            'serial_number': 'FDOA1', 'software_version': '17.9',
            'warranty_status': 'active', 'end_of_life': '2030-01-01', 'end_of_support': '2033-01-01',
        }],
    }, '10.0.0.1')
    html = '''<html><body><table class="nst-asset-table">
    <tr><th>Host</th><th>Hostname</th><th>Product ID (PID)</th><th>Serial Number</th>
    <th>Software Version</th><th>Warranty Status</th><th>End of Life</th><th>End of Support</th></tr>
    <tr><td>
    10.0.0.2
    </td><td>b</td><td>C9500</td><td>
    FDOB2
    </td><td>17.6</td><td>active</td><td>2028-01-01</td><td>2031-01-01</td></tr>
    </table></body></html>'''
    (cons.input_dir / 'a.csv').write_text(csv1, encoding='utf-8')
    (cons.input_dir / 'b.html').write_text(html, encoding='utf-8')
    result = cons.consolidate_reports('expert_mutual')
    check('consolidate success', result.get('success') is True, str(result))
    check('total_devices >= 2', (result.get('summary') or {}).get('total_devices', 0) >= 2, str(result.get('summary')))
    check('output_csv present', bool(result.get('output_csv')))
    if result.get('output_csv_path'):
        body = Path(result['output_csv_path']).read_text(encoding='utf-8')
        check('csv has FDOA1', 'FDOA1' in body)
        check('csv has FDOB2', 'FDOB2' in body)


def validate_flask_api() -> None:
    section('FLASK API — smoke + credentials')
    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager

    tmp = tempfile.mkdtemp()
    cm = CredentialManager(storage_dir=tmp)
    web.app.config['TESTING'] = True
    web.credential_manager = cm
    c = web.app.test_client()

    r = c.get('/health')
    check('GET /health', r.status_code == 200, str(r.status_code))

    r = c.get('/api/version')
    check('GET /api/version', r.status_code == 200)
    ver = (r.get_json() or {}).get('version') or (r.get_json() or {}).get('VERSION')
    check('version JSON present', bool(ver), str(r.get_json()))

    r = c.get('/api/plugins/list')
    check('GET /api/plugins/list', r.status_code == 200)
    plist = (r.get_json() or {}).get('plugins') or (r.get_json() or {}).get('data') or r.get_json()
    check('plugins list non-empty', bool(plist), str(type(plist)))

    r = c.get('/api/discovery/program-status')
    check('GET /api/discovery/program-status', r.status_code == 200)

    r = c.get('/api/mac-trace/last')
    check('GET /api/mac-trace/last idle-ok', r.status_code == 200)

    r = c.get('/api/description-search/last')
    check('GET /api/description-search/last idle-ok', r.status_code == 200)

    master = 'expert_val_pw_9x'
    check('set master', c.post('/api/credentials/master-password/set', json={'password': master}).status_code == 200)
    check('unlock vault', c.post('/api/credentials/master-password/unlock', json={'password': master}).status_code == 200)
    for u in ('ex_primary', 'ex_secondary', 'ex_third'):
        rr = c.post('/api/credentials/add', json={
            'username': u, 'password': f'{u}_pass', 'admin_password': 'en', 'label': u, 'force': True,
        })
        check(f'add cred {u}', rr.status_code == 200, str(rr.get_json()))

    r = c.get('/api/credentials/list')
    check('list creds >=3', len((r.get_json() or {}).get('credentials') or []) >= 3)

    r = c.post('/api/session/credentials', json={
        'username': 'ex_primary',
        'credential_id': 'ex_primary',
        'secondary_credential_id': 'ex_secondary',
        'third_credential_id': 'ex_third',
    })
    check('session POST', r.status_code == 200)
    view = c.get('/api/session/credentials').get_json() or {}
    check('session secondary', view.get('secondary_credential_id') == 'ex_secondary')
    check('session third', view.get('third_credential_id') == 'ex_third')
    check('session no secrets', 'ex_primary_pass' not in json.dumps(view))

    # consolidator API with temp files via patch
    from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
    tmp2 = tempfile.mkdtemp()
    cons = AssetWarrantyConsolidator(base_dir=str(Path(tmp2) / 'reports'))
    (cons.input_dir / 'x.csv').write_text(
        'Host,Hostname,Product ID (PID),Serial Number,Software Version,Warranty Status,End of Life,End of Support\n'
        '1.1.1.1,h1,C9300,FDOX1,17,active,2030-01-01,2033-01-01\n',
        encoding='utf-8',
    )
    with patch('utils.asset_warranty_consolidator.AssetWarrantyConsolidator',
               side_effect=lambda *a, **k: AssetWarrantyConsolidator(base_dir=str(Path(tmp2) / 'reports'))):
        r = c.post('/api/reports/asset-warranty/consolidate', json={'report_name': 'expert'})
    data = r.get_json() or {}
    check('consolidate API', r.status_code == 200 and data.get('success'), str(data)[:200])
    check('consolidate devices>0', (data.get('summary') or {}).get('total_devices', 0) > 0, str(data.get('summary')))

    # execute with mock SSH — interfaces
    attempts: list[str] = []

    def fake_connect(target, user, pwd, enb, log_func=None):
        attempts.append(user)
        if user != 'ex_secondary':
            raise Exception('auth fail')
        m = MagicMock()
        m.disconnect = MagicMock()
        m.find_prompt.return_value = 'sw#'
        m.send_command.return_value = 'Interface Status\nGi1/0/1 up'
        return m

    with patch('modules.network_base.connect_permissive', side_effect=fake_connect):
        r = c.post('/api/execute', json={
            'action': 'interfaces',
            'credential_id': 'ex_primary',
            'secondary_credential_id': 'ex_secondary',
            'third_credential_id': 'ex_third',
            'inventory': '10.8.8.8,cisco_ios',
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'int_filter': '',
        })
        check('execute interfaces accepted', r.status_code == 200, str(r.get_json())[:120])
        for _ in range(40):
            if len(attempts) >= 2:
                break
            time.sleep(0.1)
    check('execute interfaces fallback order', attempts[:2] == ['ex_primary', 'ex_secondary'], str(attempts))


def main() -> int:
    print('Network Swiss Tool Pro — EXPERT FULL VALIDATION')
    print(f'Root: {ROOT}')
    validate_static()
    validate_plugins_registry()
    validate_fallback_mock()
    validate_non_cisco()
    validate_consolidator()
    validate_flask_api()
    print(f'\n=== SUMMARY: {passes} passed, {len(fails)} failed ===')
    for f in fails:
        print(' -', f)
    out = ROOT / 'reports' / 'qa_playwright' / 'expert_full_validation.log'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f'version={(ROOT/"VERSION").read_text().strip()}\npassed={passes}\nfailed={len(fails)}\n'
        + '\n'.join(fails),
        encoding='utf-8',
    )
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
