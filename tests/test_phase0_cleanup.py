"""Phase 0 cleanup: Standards index, plugin artifact metadata, STP path safety, version."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.execute_test_helpers import execute_json, seed_execute_vault

COMMITTED = '10.10.1.1,cisco_ios,DIST\n10.10.1.2,cisco_nxos,DIST\n'
BOX_DIFF = '10.9.9.9,cisco_ios,LAB\n'


def _local(**kwargs):
    kwargs.setdefault('environ_base', {'REMOTE_ADDR': '127.0.0.1'})
    return kwargs


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    monkeypatch.setenv('NST_INVENTORY_PATH', str(tmp_path / 'inventory.txt'))
    (tmp_path / 'inventory.txt').write_text(COMMITTED, encoding='utf-8')
    from utils import job_index, output_paths
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(str(tmp_path / 'index' / 'jobs.sqlite'))
    from vlan_checker_web import app
    import vlan_checker_web as web
    app.config['TESTING'] = True
    seed_execute_vault(web, str(tmp_path / 'vault'))
    return app.test_client(), job_index, output_paths


def _standards_body(**extra):
    from tests.execute_test_helpers import EXECUTE_CREDENTIAL_ID, execute_json
    body = execute_json(
        target_mode='bulk',
        filter='',
        group='All',
        single_host='',
        inventory_source='committed',
        inventory=BOX_DIFF,
    )
    body['username'] = EXECUTE_CREDENTIAL_ID
    body.update(extra)
    return body


def _fake_registry(compliant=True, fail=False):
    reg = MagicMock()
    if fail:
        def _boom(*a, **k):
            raise RuntimeError('ssh timeout')
        reg.execute.side_effect = _boom
    else:
        def _ok(plugin_id, dev, *a, **k):
            host = (dev or {}).get('host', 'x')
            return {
                'device': host,
                'status': 'success',
                'data': {'compliant': compliant, 'violations': []},
            }
        reg.execute.side_effect = _ok
    return reg


def test_standards_committed_indexes_and_sanitizes_report(tmp_path, monkeypatch):
    client, job_index, output_paths = _client(tmp_path, monkeypatch)
    with patch('modules.plugin_registry.get_registry', return_value=_fake_registry()):
        r = client.post('/api/standards/run', json=_standards_body(), **_local())
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert 'results' in body
    assert body['total'] == 2
    assert body['inventory_source'] == 'committed'
    assert body['device_count'] == 2
    assert body['synchronous'] is True
    assert body['cancel_scope'] == 'none'
    assert body['artifacts_expected'] is True
    assert body['task_id']
    cr = body.get('consolidated_report') or ''
    assert not cr.startswith('/')
    assert 'password' not in str(body).lower()
    row = job_index.get_job(body['task_id'])
    assert row['action'] == 'standards'
    assert row['inventory_source'] == 'committed'
    assert row['device_count'] == 2
    assert row['status'] == 'complete'
    if body['artifacts_available']:
        assert row['run_dir']
        assert not str(row['run_dir']).startswith('/')
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_standards_unsaved_match_and_differs(tmp_path, monkeypatch):
    client, job_index, output_paths = _client(tmp_path, monkeypatch)
    with patch('modules.plugin_registry.get_registry', return_value=_fake_registry()):
        match = client.post(
            '/api/standards/run',
            json=_standards_body(inventory_source='unsaved', inventory=COMMITTED),
            **_local(),
        )
        differs = client.post(
            '/api/standards/run',
            json=_standards_body(inventory_source='unsaved', inventory=BOX_DIFF),
            **_local(),
        )
    assert match.status_code == 200, match.get_data(as_text=True)
    assert match.get_json()['inventory_source'] == 'unsaved'
    assert match.get_json()['device_count'] == 2
    assert differs.status_code == 200, differs.get_data(as_text=True)
    dbody = differs.get_json()
    assert dbody['inventory_source'] == 'unsaved'
    assert dbody['device_count'] == 1
    assert dbody['results'][0]['device'] == '10.9.9.9'
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_standards_not_a_mutation_ack_gate(tmp_path, monkeypatch):
    """Standards is not VLAN/save_config; unsaved-differs does not require acknowledge."""
    client, job_index, output_paths = _client(tmp_path, monkeypatch)
    with patch('modules.plugin_registry.get_registry', return_value=_fake_registry()):
        r = client.post(
            '/api/standards/run',
            json=_standards_body(inventory_source='unsaved', inventory=BOX_DIFF),
            **_local(),
        )
    assert r.status_code != 409
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_standards_device_failure_still_returns_results(tmp_path, monkeypatch):
    client, job_index, output_paths = _client(tmp_path, monkeypatch)
    with patch('modules.plugin_registry.get_registry', return_value=_fake_registry(fail=True)):
        r = client.post('/api/standards/run', json=_standards_body(), **_local())
    assert r.status_code == 200
    body = r.get_json()
    assert body['results'][0]['status'] == 'fail'
    assert 'ssh timeout' in body['results'][0]['error']
    row = job_index.get_job(body['task_id'])
    assert row['status'] == 'complete'
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_plugin_execute_artifacts_expected_null(tmp_path, monkeypatch):
    client, job_index, output_paths = _client(tmp_path, monkeypatch)

    class Immediate:
        def __init__(self, target=None, args=(), kwargs=None, daemon=None):
            self._target = target
            self._args = args or ()

        def start(self):
            self._target(*self._args)

    fake_results = [{'status': 'success', 'device': '10.10.1.1', 'data': {'ok': True}}]
    with patch('vlan_checker_web.threading.Thread', Immediate), patch(
        'modules.adapters.run_generic_plugin', return_value=fake_results,
    ):
        r = client.post(
            '/api/execute',
            json=execute_json(
                action='vlan_audit',
                inventory_source='committed',
                inventory=BOX_DIFF,
                target_mode='bulk',
                filter='',
                group='All',
                single_host='',
            ),
            **_local(),
        )
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body['status'] == 'started'
    assert body['artifacts_expected'] is None
    row = job_index.get_job(body['task_id'])
    assert row['action'] == 'vlan_audit'
    assert 'password' not in str(row)
    if row.get('run_dir'):
        assert row['artifacts_available'] is True
        assert str(row['run_dir']).startswith('outputs/')
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_stp_status_omits_absolute_paths(tmp_path, monkeypatch):
    client, job_index, output_paths = _client(tmp_path, monkeypatch)
    from vlan_checker_web import _job_store_lock, _stp_jobs
    jid = 'stp-path-qa'
    with _job_store_lock:
        _stp_jobs[jid] = {
            'status': 'complete',
            'error': None,
            'target_source': 'demo',
            'device_count': 3,
            'result': {
                'html_path': '/etc/passwd',
                'output_folder': '/Users/nobody/secret',
                'txt_path': '/tmp/x',
                'nodes': [{'id': 'A'}],
                'target_source': 'demo',
            },
        }
    r = client.get(f'/api/stp/status/{jid}', **_local())
    assert r.status_code == 200
    body = r.get_json()
    blob = str(body)
    assert '/etc/passwd' not in blob
    assert '/Users/nobody' not in blob
    assert '/tmp/x' not in blob
    assert 'html_path' not in body.get('result', {})
    assert body['result']['artifacts_available'] is False
    assert body['result']['run_dir'] is None
    report = client.get(f'/api/stp/report/{jid}', **_local())
    assert report.status_code == 404
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_version_highlight_is_current(tmp_path, monkeypatch):
    client, job_index, output_paths = _client(tmp_path, monkeypatch)
    r = client.get('/api/version', **_local())
    assert r.status_code == 200
    data = r.get_json()
    ver = open('VERSION', encoding='utf-8').read().strip()
    assert data['version'] == ver
    assert ver in data['date']
    assert '7.0.91' not in data['date']
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None
