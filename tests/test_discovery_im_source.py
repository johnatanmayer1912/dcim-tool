"""Explicit Discovery seeds vs IM single-host — not bulk inventory.txt."""
from __future__ import annotations

import pytest

from utils.job_source import JobSourceError, resolve_discovery_targets, resolve_im_target


def _local(**kwargs):
    kwargs.setdefault('environ_base', {'REMOTE_ADDR': '127.0.0.1'})
    return kwargs


def test_discovery_explicit_seeds_and_duplicates():
    r = resolve_discovery_targets({
        'target_source': 'discovery_seeds',
        'seed_hosts': ['10.0.0.1', '10.0.0.1', '10.0.0.2,cisco_nxos'],
    })
    assert r['target_source'] == 'discovery_seeds'
    assert r['seed_hosts'] == ['10.0.0.1', '10.0.0.2']
    assert r['duplicates_omitted'] == 1
    assert r['seed_count'] == 2


def test_discovery_empty_and_malformed_seeds():
    with pytest.raises(JobSourceError, match='seed host'):
        resolve_discovery_targets({'target_source': 'discovery_seeds', 'seed_hosts': []})
    with pytest.raises(JobSourceError, match='Malformed|path|Host'):
        resolve_discovery_targets({'target_source': 'discovery_seeds', 'seed_hosts': ['../etc/passwd']})
    with pytest.raises(JobSourceError, match='Malformed|Unknown'):
        resolve_discovery_targets({'target_source': 'discovery_seeds', 'seed_hosts': ['10.0.0.1,not_a_vendor']})


def test_discovery_does_not_use_inventory_body_without_source():
    with pytest.raises(JobSourceError, match='not Discovery seeds'):
        resolve_discovery_targets({'inventory': '10.1.1.1,cisco_ios\n'})


def test_discovery_committed_and_unsaved(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.10.1.1,cisco_ios,DIST\n10.10.1.2,cisco_nxos,DIST\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    c = resolve_discovery_targets({'target_source': 'committed_inventory'})
    assert c['target_source'] == 'committed_inventory'
    assert c['seed_hosts'] == ['10.10.1.1', '10.10.1.2']
    assert 'census' in (c.get('warning') or '')
    u = resolve_discovery_targets({
        'target_source': 'unsaved_inventory',
        'inventory': '10.9.9.9,cisco_ios,LAB\n',
    })
    assert u['seed_hosts'] == ['10.9.9.9']
    assert u['target_source'] == 'unsaved_inventory'


def test_im_single_host_not_inventory_fallback():
    r = resolve_im_target({'host': '10.0.0.9', 'device_type': 'cisco_ios', 'target_source': 'single_host'})
    assert r['host'] == '10.0.0.9'
    assert r['target_source'] == 'single_host'
    assert r['device_count'] == 1
    with pytest.raises(JobSourceError, match='required'):
        resolve_im_target({'target_source': 'single_host'})
    with pytest.raises(JobSourceError, match='path|Malformed|Host'):
        resolve_im_target({'host': '../secret', 'target_source': 'single_host'})


def test_im_committed_must_match(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.10.1.1,cisco_ios,DIST\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    ok = resolve_im_target({'host': '10.10.1.1', 'target_source': 'committed_inventory'})
    assert ok['device_type'] == 'cisco_ios'
    with pytest.raises(JobSourceError, match='not in committed'):
        resolve_im_target({'host': '10.9.9.9', 'target_source': 'committed_inventory'})
    with pytest.raises(JobSourceError, match='unsaved'):
        resolve_im_target({
            'host': '10.10.1.1',
            'target_source': 'unsaved_inventory',
            'inventory': '10.8.8.8,cisco_ios\n',
        })


def test_legacy_im_host_field():
    r = resolve_im_target({'host': '10.0.0.5', 'device_type': 'cisco_nxos'})
    assert r['target_source'] == 'single_host'
    assert r['legacy'] is True
    assert r['device_type'] == 'cisco_nxos'


def test_discovery_http_empty_malformed_and_index(tmp_path, monkeypatch):
    from unittest.mock import patch
    from vlan_checker_web import app
    from utils import job_index, output_paths
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(str(tmp_path / 'index' / 'jobs.sqlite'))
    app.config['TESTING'] = True
    client = app.test_client()
    empty = client.post('/api/discovery/run', json={'demo_mode': True, 'target_source': 'discovery_seeds'}, **_local())
    assert empty.status_code == 400
    bad = client.post(
        '/api/discovery/run',
        json={'demo_mode': True, 'target_source': 'discovery_seeds', 'seed_hosts': ['../etc/passwd']},
        **_local(),
    )
    assert bad.status_code == 400
    inv = tmp_path / 'inventory.txt'
    inv.write_text('10.10.1.1,cisco_ios\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(inv))
    sneak = client.post(
        '/api/discovery/run',
        json={'demo_mode': True, 'inventory': '10.1.1.1,cisco_ios\n'},
        **_local(),
    )
    assert sneak.status_code == 400
    hops = client.post(
        '/api/discovery/run',
        json={'demo_mode': True, 'target_source': 'discovery_seeds', 'seed_hosts': ['10.0.0.1'], 'max_depth': 9},
        **_local(),
    )
    assert hops.status_code == 400

    with patch('vlan_checker_web.threading.Thread') as mock_thread:
        mock_thread.return_value.start = lambda: None
        ok = client.post(
            '/api/discovery/run',
            json={
                'demo_mode': True,
                'target_source': 'committed_inventory',
                'max_depth': 1,
            },
            **_local(),
        )
    assert ok.status_code == 200, ok.get_data(as_text=True)
    body = ok.get_json()
    assert body['target_source'] == 'committed_inventory'
    assert body['seed_count'] == 1
    assert body['max_depth'] == 1
    row = job_index.get_job(body['task_id'])
    assert row['action'] == 'discovery'
    assert row['inventory_source'] == 'committed_inventory'
    assert row['status'] == 'running'
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_im_http_missing_host_and_index(tmp_path, monkeypatch):
    from unittest.mock import patch
    import vlan_checker_web as web
    from vlan_checker_web import app
    from utils import job_index, output_paths
    from tests.execute_test_helpers import EXECUTE_CREDENTIAL_ID, seed_execute_vault
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(str(tmp_path / 'index' / 'jobs.sqlite'))
    app.config['TESTING'] = True
    cid = seed_execute_vault(web, str(tmp_path / 'vault'))
    client = app.test_client()
    missing = client.post(
        '/api/interface/discover',
        json={'credential_id': cid, 'target_source': 'single_host'},
        **_local(),
    )
    assert missing.status_code == 400
    trav = client.post(
        '/api/interface/discover',
        json={'host': '../../etc/passwd', 'credential_id': cid, 'target_source': 'single_host'},
        **_local(),
    )
    assert trav.status_code == 400
    with patch('modules.plugins.interface_manager.run') as run:
        run.return_value = {'status': 'ok', 'data': {'interfaces': [], 'interface_count': 0}}
        r = client.post(
            '/api/interface/discover',
            json={
                'host': '10.0.0.8',
                'credential_id': cid,
                'target_source': 'single_host',
                'device_type': 'cisco_ios',
            },
            **_local(),
        )
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body['target_source'] == 'single_host'
    assert body['host'] == '10.0.0.8'
    assert EXECUTE_CREDENTIAL_ID in (cid,)
    assert 'secret-password' not in str(body)
    row = job_index.get_job(body['task_id'])
    assert row['action'] == 'interface_discover'
    assert row['status'] == 'complete'
    assert row['inventory_source'] == 'single_host'
    dump = str(row)
    assert 'test-execute-secret' not in dump
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_im_validate_failed_indexes(tmp_path, monkeypatch):
    from unittest.mock import patch
    import vlan_checker_web as web
    from vlan_checker_web import app
    from utils import job_index, output_paths
    from tests.execute_test_helpers import seed_execute_vault
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(str(tmp_path / 'index' / 'jobs.sqlite'))
    app.config['TESTING'] = True
    cid = seed_execute_vault(web, str(tmp_path / 'vault'))
    client = app.test_client()
    with patch('modules.plugins.interface_manager.run') as run:
        run.return_value = {'status': 'fail', 'message': 'syntax'}
        r = client.post(
            '/api/interface/validate',
            json={
                'host': '10.0.0.8',
                'credential_id': cid,
                'proposed_config': 'interface Gi1/0/1',
                'target_source': 'single_host',
            },
            **_local(),
        )
    assert r.status_code == 500
    row = job_index.get_job(r.get_json()['task_id'])
    assert row['status'] == 'failed'
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None
