"""Tests for Evidence pack, backup diff API, and reachability matrix (OSS-wow slice)."""
from __future__ import annotations

import os
import time
import zipfile

import pytest

from utils import job_index, output_paths
from utils.backup_api import compare_backup_paths, contained_backup_path, list_backup_records
from utils.config_backup_system import ConfigBackupSystem
from utils.evidence_pack import build_job_pack
from utils.reachability_matrix import build_reachability_matrix, matrix_to_csv, matrix_to_html


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    db = tmp_path / 'index' / 'jobs.sqlite'
    job_index.reset_for_tests(str(db))
    yield tmp_path
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_reachability_matrix_aggregate():
    devices = [
        {'host': '10.0.0.1', 'device_type': 'cisco_ios'},
        {'host': '10.0.0.2', 'device_type': 'cisco_ios'},
        {'host': '10.0.0.3', 'device_type': 'juniper_junos'},
    ]

    def runner(device, user, pwd, enb, log_func=None):
        host = device['host']
        if host.endswith('.1'):
            return {'status': 'success', 'data': {'ping': True, 'ssh': True}}
        if host.endswith('.2'):
            return {'status': 'fail', 'data': {'ping': True, 'ssh': False}, 'error': 'auth'}
        return {'status': 'fail', 'data': {'ping': False, 'ssh': False}, 'error': 'down'}

    summary = build_reachability_matrix(devices, 'u', 'p', runner=runner)
    assert summary['device_count'] == 3
    assert summary['counts']['ok'] == 1
    assert summary['counts']['ping_only'] == 1
    assert summary['counts']['unreachable'] == 1
    html = matrix_to_html(summary)
    assert 'Fleet Reachability Matrix' in html
    assert '10.0.0.1' in html
    csv = matrix_to_csv(summary)
    assert 'Host,Device Type' in csv
    assert '10.0.0.2' in csv


def test_backup_path_containment_and_diff(isolated):
    root = output_paths.get_backups_root()
    devices = os.path.join(root, 'devices')
    bs = ConfigBackupSystem(backup_dir=devices)
    r1 = bs.create_backup('10.1.1.1', 'sw1', 'hostname sw1\nint Gi1\n', 'show run', 'manual', 't1')
    time.sleep(1.05)
    r2 = bs.create_backup('10.1.1.1', 'sw1', 'hostname sw1\nint Gi1\nint Gi2\n', 'show run', 'manual', 't2')
    assert r1['success'] and r2['success']
    assert r1['backup_path'] != r2['backup_path']
    assert contained_backup_path('/etc/passwd') is None
    assert contained_backup_path(r1['backup_path']) is not None
    rows = list_backup_records(hostname='sw1')
    assert len(rows) >= 2
    for x in rows:
        bp = x.get('backup_path') or x.get('safe_path')
        if bp:
            assert not str(bp).startswith('/')
    diff, err = compare_backup_paths(r1['backup_path'], r2['backup_path'])
    assert err is None
    assert diff['added_count'] >= 1
    assert 'Gi2' in (diff.get('unified_diff') or '')


def test_evidence_pack_zip_contained(isolated):
    job_index.init_db()
    run = output_paths.prepare_run_output(output_paths.CAT_INTERFACES, 'pack_test')
    report = output_paths.path_in_run(run, 'report.txt')
    with open(report, 'w', encoding='utf-8') as fh:
        fh.write('hello evidence')
    with open(os.path.join(run['run_dir'], '.credential_key'), 'w') as fh:
        fh.write('secret')
    tid = 'packtest00aaaa'
    assert job_index.record_start(tid, 'interfaces', inventory_source='committed', device_count=1)
    assert job_index.record_run_dir(tid, run['run_dir'])
    assert job_index.record_status(tid, 'complete')
    job = job_index.get_job(tid)
    assert job and job.get('artifacts_available')
    buf, name, meta = build_job_pack(tid)
    assert buf is not None
    assert name.endswith('.zip')
    zf = zipfile.ZipFile(buf)
    names = zf.namelist()
    assert '00_EVIDENCE_README.txt' in names
    assert any(n.endswith('report.txt') for n in names)
    assert '.credential_key' not in names


def test_api_backups_and_pack(isolated):
    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager

    vault = isolated / 'vault'
    vault.mkdir(parents=True, exist_ok=True)
    web.app.config['TESTING'] = True
    web.credential_manager = CredentialManager(storage_dir=str(vault))
    c = web.app.test_client()

    root = output_paths.get_backups_root()
    bs = ConfigBackupSystem(backup_dir=os.path.join(root, 'devices'))
    bs.create_backup('h', 'core1', 'aaa\n', 'show run', 'manual', 'x')
    time.sleep(1.05)
    bs.create_backup('h', 'core1', 'aaa\nbbb\n', 'show run', 'manual', 'y')

    r = c.get('/api/backups', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['count'] >= 2
    paths = [b.get('safe_path') or b.get('backup_path') for b in data['backups']]
    paths = [p for p in paths if p]
    r = c.post(
        '/api/backups/diff',
        json={'path_a': paths[1], 'path_b': paths[0]},
        environ_base={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert r.status_code == 200
    assert r.get_json()['success'] is True

    bad = c.post(
        '/api/backups/diff',
        json={'path_a': '/etc/passwd', 'path_b': paths[0]},
        environ_base={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert bad.status_code == 400

    missing = c.get('/api/jobs/doesnotexist/pack', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert missing.status_code == 404

    # Evidence open/rerun APIs
    job_index.init_db()
    run = output_paths.prepare_run_output(output_paths.CAT_INTERFACES, 'open_test')
    report = output_paths.path_in_run(run, 'report.html')
    with open(report, 'w', encoding='utf-8') as fh:
        fh.write('<html><body>ok</body></html>')
    tid = 'opentest00aaaa'
    assert job_index.record_start(tid, 'interfaces', inventory_source='committed', device_count=1)
    assert job_index.record_run_dir(tid, run['run_dir'])
    assert job_index.record_status(tid, 'complete')
    opened = c.get(f'/api/jobs/{tid}/open', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert opened.status_code == 200
    assert b'ok' in opened.data
    rerun = c.post(f'/api/jobs/{tid}/rerun', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert rerun.status_code == 200
    assert rerun.get_json().get('action') == 'interfaces'
