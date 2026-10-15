"""SQLite job index — catalog, lifecycle, path safety, localhost API."""
from __future__ import annotations

import os
import sqlite3
import threading
import time

import pytest

from tests.execute_test_helpers import execute_json, seed_execute_vault
from utils import job_index, output_paths
from utils.task_control_plane import (
    bind_task,
    complete_task,
    get_task,
    register_task,
    request_cancel,
)


def _local(**kwargs):
    kwargs.setdefault('environ_base', {'REMOTE_ADDR': '127.0.0.1'})
    return kwargs


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    db = tmp_path / 'index' / 'jobs.sqlite'
    job_index.reset_for_tests(str(db))
    yield tmp_path
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_db_and_schema_creation(isolated):
    assert job_index.init_db() is True
    path = job_index.db_path()
    assert os.path.isfile(path)
    assert path.endswith(os.path.join('index', 'jobs.sqlite'))
    assert job_index.schema_version() == job_index.SCHEMA_VERSION
    assert job_index.list_jobs() == []


def test_db_under_data_root_without_override(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(None)
    expected = os.path.join(os.path.abspath(str(tmp_path)), 'index', 'jobs.sqlite')
    assert job_index.db_path() == expected
    assert job_index.init_db() is True
    assert os.path.isfile(expected)
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_empty_index_and_insert_update_list(isolated):
    assert job_index.list_jobs() == []
    assert job_index.record_start('aaa111aaa111', 'mac_check', inventory_source='committed', device_count=2)
    row = job_index.get_job('aaa111aaa111')
    assert row['status'] == 'running'
    assert row['action'] == 'mac_check'
    assert row['inventory_source'] == 'committed'
    assert row['device_count'] == 2
    assert row['run_dir'] is None
    assert row['artifacts_available'] is False
    assert row['run_dir_exists'] is False
    assert job_index.record_status('aaa111aaa111', 'complete')
    row = job_index.get_job('aaa111aaa111')
    assert row['status'] == 'complete'
    assert row['completed_at']
    assert row['partial'] is False


def test_list_ordering_and_limit(isolated):
    for i in range(5):
        job_index.record_start(f'task{i:04d}xxxx', f'act{i}', device_count=i)
        time.sleep(0.01)
    listed = job_index.list_jobs(3)
    assert len(listed) == 3
    assert listed[0]['task_id'] == 'task0004xxxx'
    assert listed[1]['task_id'] == 'task0003xxxx'
    huge = job_index.list_jobs(99999)
    assert len(huge) == 5
    assert job_index.clamp_limit(99999) == job_index.MAX_LIST_LIMIT
    assert job_index.clamp_limit('nope') == job_index.DEFAULT_LIST_LIMIT
    assert job_index.clamp_limit(-4) == 1


def test_repeated_updates_and_unknown_task(isolated):
    job_index.record_start('bbb222bbb222', 'vlan_check')
    assert job_index.record_status('bbb222bbb222', 'complete')
    assert job_index.record_status('bbb222bbb222', 'complete')
    assert job_index.get_job('bbb222bbb222')['status'] == 'complete'
    assert job_index.record_status('missingtask1', 'complete') is False
    assert job_index.get_job('missingtask1') is None
    assert job_index.record_run_dir('missingtask1', str(isolated / 'outputs' / 'x')) is False


def test_persistence_across_reconnect(isolated):
    job_index.record_start('ccc333ccc333', 'backup', inventory_source='committed')
    job_index.record_status('ccc333ccc333', 'failed', 'timeout')
    listed = job_index.list_jobs()
    assert listed[0]['status'] == 'failed'
    assert listed[0]['task_id'] == 'ccc333ccc333'


def test_lifecycle_via_control_plane(isolated):
    tid = register_task('connectivity', meta={'inventory_source': 'committed', 'device_count': 1})
    row = job_index.get_job(tid)
    assert row['status'] == 'running'
    complete_task(tid, 'complete')
    assert job_index.get_job(tid)['status'] == 'complete'


def test_failure_and_cancel_not_complete(isolated):
    fail_id = register_task('audit')
    complete_task(fail_id, 'error', 'password=supersecret enable_pwd=x')
    failed = job_index.get_job(fail_id)
    assert failed['status'] == 'failed'
    blob = str(failed)
    assert 'supersecret' not in blob
    assert 'password=' not in blob.lower() or 'redacted' in blob.lower() or failed['error_summary'] == 'error (details omitted)'

    cancel_id = register_task('topology')
    assert request_cancel(cancel_id)
    row = job_index.get_job(cancel_id)
    assert row['status'] == 'cancelled'
    complete_task(cancel_id, 'complete')
    row = job_index.get_job(cancel_id)
    assert row['status'] == 'cancelled'
    assert row['status'] != 'complete'


def test_cancelled_partial_with_run_dir(isolated):
    tid = register_task('mac_check', meta={'device_count': 2})
    bind_task(tid)
    paths = output_paths.prepare_run_output('mac_trace', 'qa')
    assert job_index.get_job(tid)['run_dir']
    assert job_index.get_job(tid)['run_dir'].startswith('outputs/')
    request_cancel(tid)
    complete_task(tid, 'complete')
    row = job_index.get_job(tid)
    assert row['status'] == 'partial'
    assert row['partial'] is True
    assert os.path.isdir(paths['run_dir'])


def test_fail_before_run_dir(isolated):
    tid = register_task('save_config')
    complete_task(tid, 'error', 'no devices')
    row = job_index.get_job(tid)
    assert row['status'] == 'failed'
    assert row['run_dir'] is None


def test_empty_action_name(isolated):
    assert job_index.record_start('ddd444ddd444', '')
    assert job_index.get_job('ddd444ddd444')['action'] == ''


def test_worker_thread_update(isolated):
    tid = register_task('interfaces')
    err = []

    def work():
        try:
            complete_task(tid, 'complete')
        except Exception as exc:
            err.append(exc)

    t = threading.Thread(target=work)
    t.start()
    t.join(3)
    assert not err
    assert job_index.get_job(tid)['status'] == 'complete'


def test_path_traversal_rejected(isolated):
    tid = register_task('vlan_check')
    assert job_index.record_run_dir(tid, '/etc/passwd') is False
    assert job_index.record_run_dir(tid, str(isolated / '..' / 'secret')) is False
    sneaky = isolated / 'outputs' / '..' / '..' / 'etc' / 'passwd'
    assert job_index.record_run_dir(tid, str(sneaky)) is False
    assert job_index.get_job(tid)['run_dir'] is None
    outside = isolated / 'not_outputs' / 'x'
    outside.mkdir(parents=True)
    assert job_index.record_run_dir(tid, str(outside)) is False


def test_directory_created_if_missing(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    nested = tmp_path / 'missing_parent' / 'jobs.sqlite'
    job_index.reset_for_tests(str(nested))
    assert job_index.record_start('eee555eee555', 'ping')
    assert nested.is_file()
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def test_corrupt_sqlite_rebuilds(isolated):
    path = job_index.db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(b'not a database')
    assert job_index.record_start('fff666fff666', 'audit')
    assert job_index.get_job('fff666fff666')['status'] == 'running'


def test_no_secret_fields_in_row(isolated):
    job_index.record_start(
        'ggg777ggg777',
        'add_vlan',
        inventory_source='unsaved',
        device_count=1,
    )
    job_index.record_status('ggg777ggg777', 'error', 'login failed password=hunter2')
    row = job_index.get_job('ggg777ggg777')
    for banned in ('password', 'hunter2', 'enable_pwd', 'fernet'):
        assert banned not in str(row.get('error_summary') or '').lower() or 'redacted' in str(row.get('error_summary')).lower()
    assert 'hunter2' not in str(row)
    conn = sqlite3.connect(job_index.db_path())
    dump = ' '.join(str(x) for x in conn.execute('SELECT * FROM jobs').fetchone())
    conn.close()
    assert 'hunter2' not in dump
    assert 'password=hunter2' not in dump.lower()


def test_api_list_and_one_and_limits(isolated):
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    empty = client.get('/api/jobs', **_local())
    assert empty.status_code == 200
    assert empty.get_json()['jobs'] == []

    job_index.record_start('hhh888hhh888', 'mac_check', inventory_source='committed', device_count=3)
    listed = client.get('/api/jobs?limit=10', **_local())
    data = listed.get_json()
    assert listed.status_code == 200
    assert data['count'] >= 1
    assert data['jobs'][0]['task_id'] == 'hhh888hhh888'
    assert 'password' not in str(data).lower() or 'redacted' in str(data).lower()
    assert 'inventory' not in data['jobs'][0] or data['jobs'][0].get('inventory') is None

    one = client.get('/api/jobs/hhh888hhh888', **_local())
    assert one.status_code == 200
    assert one.get_json()['job']['action'] == 'mac_check'

    missing = client.get('/api/jobs/zzzzzzzzzzzz', **_local())
    assert missing.status_code == 404

    bad_limit = client.get('/api/jobs?limit=not-a-number', **_local())
    assert bad_limit.status_code == 200
    assert bad_limit.get_json()['limit'] == job_index.DEFAULT_LIST_LIMIT

    huge = client.get('/api/jobs?limit=999999', **_local())
    assert huge.get_json()['limit'] == job_index.MAX_LIST_LIMIT

    traversal = client.get('/api/jobs/..%2Fetc%2Fpasswd', **_local())
    assert traversal.status_code in (404, 400)
    ignored = client.get('/api/jobs?path=/etc/passwd', **_local())
    assert ignored.status_code == 200
    assert 'jobs' in ignored.get_json()


def test_execute_indexes_start(isolated, monkeypatch):
    from unittest.mock import patch
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    inv = isolated / 'inventory.txt'
    inv.write_text('10.10.1.1,cisco_ios,DIST\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(inv))
    import vlan_checker_web as web
    seed_execute_vault(web, str(isolated / 'vault'))
    with patch('vlan_checker_web.threading.Thread') as mock_thread:
        mock_thread.return_value.start = lambda: None
        r = client.post(
            '/api/execute',
            json=execute_json(
                action='mac_check',
                inventory='',
                inventory_source='committed',
                target_mode='bulk',
                filter='',
                group='All',
                single_host='',
                mac_address='aa:bb:cc:dd:ee:ff',
            ),
            **_local(),
        )
    assert r.status_code == 200
    tid = r.get_json()['task_id']
    row = job_index.get_job(tid)
    assert row is not None
    assert row['status'] == 'running'
    assert row['action'] == 'mac_check'
    listed = client.get('/api/jobs', **_local())
    ids = [j['task_id'] for j in listed.get_json()['jobs']]
    assert tid in ids
    dumped = str(listed.get_json())
    assert "'password'" not in dumped
    assert '"password"' not in dumped


def test_api_rejects_remote(isolated):
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    for path in ('/api/jobs', '/api/jobs/abc'):
        r = client.get(path, environ_base={'REMOTE_ADDR': '203.0.113.10'})
        assert r.status_code == 403, path


def test_eviction_skips_cancelling(isolated, monkeypatch):
    import utils.task_control_plane as tcp
    monkeypatch.setattr(tcp, '_MAX_TASKS', 2)
    a = register_task('done_job')
    complete_task(a, 'complete')
    b = register_task('live_cancel')
    assert request_cancel(b)
    register_task('newer')
    assert get_task(b) is not None
    assert get_task(b)['status'] == 'cancelling'
    assert job_index.get_job(b)['status'] in ('cancelled', 'partial')


def test_complete_updates_index_without_memory_row(isolated):
    assert job_index.record_start(
        'abcdabcdabcd', 'discovery', inventory_source='discovery_seeds', device_count=1,
    )
    complete_task('abcdabcdabcd', 'complete')
    assert job_index.get_job('abcdabcdabcd')['status'] == 'complete'
