"""Ping Scan CIDR vs STP inventory-scope — explicit target sources."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from utils.job_source import (
    MAX_PING_HOSTS,
    JobSourceError,
    resolve_cidr_scan,
    resolve_stp_targets,
)


def _local(**kwargs):
    kwargs.setdefault('environ_base', {'REMOTE_ADDR': '127.0.0.1'})
    return kwargs


def test_cidr_valid_and_not_inventory():
    r = resolve_cidr_scan({'target_source': 'cidr_scan', 'network': '192.168.1.0/24'})
    assert r['target_source'] == 'cidr_scan'
    assert r['device_count'] == 254
    assert r['legacy'] is False


def test_cidr_legacy_omitted_source():
    r = resolve_cidr_scan({'network': '10.0.0.0/30'})
    assert r['target_source'] == 'legacy_body'
    assert r['legacy'] is True
    assert r['warning'] == 'legacy_cidr_scan'
    assert r['device_count'] == 2


def test_cidr_rejects_inventory_source_and_path_and_size():
    with pytest.raises(JobSourceError, match='not an inventory'):
        resolve_cidr_scan({'inventory_source': 'committed', 'network': '192.168.1.0/24'})
    with pytest.raises(JobSourceError, match='path|traversal|CIDR'):
        resolve_cidr_scan({'target_source': 'cidr_scan', 'network': '../etc/passwd'})
    with pytest.raises(JobSourceError, match='host list'):
        resolve_cidr_scan({'target_source': 'cidr_scan', 'network': '10.0.0.1'})
    with pytest.raises(JobSourceError, match='too large'):
        resolve_cidr_scan({'target_source': 'cidr_scan', 'network': '10.0.0.0/8'})
    assert MAX_PING_HOSTS == 256


def test_stp_demo_is_not_inventory():
    r = resolve_stp_targets({'demo_mode': True})
    assert r['target_source'] == 'demo'
    assert r['device_count'] == 3


def test_stp_legacy_devices_body():
    r = resolve_stp_targets({
        'devices': [{'host': '10.0.0.1', 'device_type': 'cisco_ios'}],
    })
    assert r['target_source'] == 'legacy_body'
    assert r['device_count'] == 1
    assert r['warning'] == 'legacy_stp_devices_body'


def test_stp_requires_explicit_source_without_devices():
    with pytest.raises(JobSourceError, match='inventory_source'):
        resolve_stp_targets({})


def test_stp_committed_ignores_unsaved_box(tmp_path, monkeypatch):
    inv = tmp_path / 'inventory.txt'
    inv.write_text('10.9.9.9,cisco_ios\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(inv))
    r = resolve_stp_targets({
        'inventory_source': 'committed',
        'inventory': '203.0.113.1,cisco_ios\n',
    })
    assert r['target_source'] == 'committed_inventory'
    assert r['devices'][0]['host'] == '10.9.9.9'
    assert r['device_count'] == 1


def test_stp_unsaved_uses_box(tmp_path, monkeypatch):
    inv = tmp_path / 'inventory.txt'
    inv.write_text('10.9.9.9,cisco_ios\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(inv))
    r = resolve_stp_targets({
        'inventory_source': 'unsaved',
        'inventory': '203.0.113.50,cisco_nxos\n',
    })
    assert r['target_source'] == 'unsaved_inventory'
    assert r['devices'][0]['host'] == '203.0.113.50'


def test_stp_rejects_cidr_as_source():
    with pytest.raises(JobSourceError, match='not CIDR'):
        resolve_stp_targets({'target_source': 'cidr_scan', 'network': '192.168.1.0/24'})


def test_ping_and_stp_http(tmp_path, monkeypatch):
    import vlan_checker_web as web
    from vlan_checker_web import app
    from utils import job_index, output_paths
    from tests.execute_test_helpers import seed_execute_vault

    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    monkeypatch.setenv('NST_INVENTORY_PATH', str(tmp_path / 'inventory.txt'))
    (tmp_path / 'inventory.txt').write_text('10.1.1.1,cisco_ios\n', encoding='utf-8')
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(str(tmp_path / 'index' / 'jobs.sqlite'))
    app.config['TESTING'] = True
    cid = seed_execute_vault(web, str(tmp_path / 'vault'))
    client = app.test_client()

    bad = client.post('/api/ping_scan', json={'target_source': 'cidr_scan', 'network': 'nope'}, **_local())
    assert bad.status_code == 400
    huge = client.post(
        '/api/ping_scan',
        json={'target_source': 'cidr_scan', 'network': '10.0.0.0/16'},
        **_local(),
    )
    assert huge.status_code == 400
    sneak = client.post(
        '/api/ping_scan',
        json={'inventory_source': 'committed', 'network': '192.168.1.0/24'},
        **_local(),
    )
    assert sneak.status_code == 400

    with patch('vlan_checker_web.threading.Thread') as mock_thread:
        mock_thread.return_value.start = lambda: None
        ok = client.post(
            '/api/ping_scan',
            json={'target_source': 'cidr_scan', 'network': '192.168.1.0/24'},
            **_local(),
        )
        legacy = client.post(
            '/api/ping_scan',
            json={'network': '10.0.0.0/30'},
            **_local(),
        )
        stp_miss = client.post('/api/stp/run', json={'vlan_id': 0}, **_local())
        stp_ok = client.post(
            '/api/stp/run',
            json={'demo_mode': True, 'vlan_id': 0},
            **_local(),
        )
        stp_committed = client.post(
            '/api/stp/run',
            json={
                'inventory_source': 'committed',
                'credential_id': cid,
                'vlan_id': 0,
            },
            **_local(),
        )

    assert ok.status_code == 200, ok.get_data(as_text=True)
    body = ok.get_json()
    assert body['target_source'] == 'cidr_scan'
    assert body['device_count'] == 254
    assert body['task_id']
    row = job_index.get_job(body['task_id'])
    assert row['action'] == 'ping_scan'
    assert row['inventory_source'] == 'cidr_scan'
    assert row['artifacts_available'] is False

    assert legacy.status_code == 200
    assert legacy.get_json()['target_source'] == 'legacy_body'

    assert stp_miss.status_code == 400
    assert stp_ok.status_code == 200
    demo = stp_ok.get_json()
    assert demo['target_source'] == 'demo'
    assert demo['device_count'] == 3
    assert job_index.get_job(demo['task_id'])['inventory_source'] == 'demo'

    assert stp_committed.status_code == 200, stp_committed.get_data(as_text=True)
    cbody = stp_committed.get_json()
    assert cbody['target_source'] == 'committed_inventory'
    assert cbody['device_count'] == 1

    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None
