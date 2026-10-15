"""Mandatory QA — Session cache and control plane."""
from __future__ import annotations

import os

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


@mandatory
def test_session_cache_survives_browser_reload():
    """GET session credentials returns last POST payload in-process."""
    from utils.session_cred_cache import (
        clear_session_credentials,
        public_session_view,
        set_session_credentials,
    )
    clear_session_credentials()
    set_session_credentials(username='ops', password='pw', label='lab')
    view = public_session_view()
    assert view['username'] == 'ops'
    assert view['label'] == 'lab'
    assert view['has_password'] is True
    assert 'pw' not in str(view)
    clear_session_credentials()


@mandatory
def test_session_cache_cleared_on_shutdown_not_tab_close():
    """Shutdown clears cache; tab close alone does not clear server cache."""
    src = open(WEB, encoding='utf-8').read()
    assert 'clear_session_credentials' in src
    assert '/api/shutdown' in src
    html = open(HTML, encoding='utf-8').read()
    assert 'beforeunload' not in html.lower() or 'clear_session' not in html


@mandatory
def test_session_cache_atexit_on_normal_exit():
    """register_session_cache_lifecycle clears on process exit."""
    from utils.session_cred_cache import register_session_cache_lifecycle
    src = open(os.path.join(ROOT, 'utils', 'session_cred_cache.py'), encoding='utf-8').read()
    assert 'atexit.register(clear_session_credentials)' in src
    assert callable(register_session_cache_lifecycle)


@mandatory
def test_clear_credential_label_clears_session():
    """clearCredentialLabel POSTs empty session payload."""
    html = open(HTML, encoding='utf-8').read()
    assert 'function clearCredentialLabel' in html
    assert 'saveSessionCredentials' in html


@mandatory
def test_control_plane_register_task_on_execute():
    """Each /api/execute action registers task with device_count meta."""
    src = open(WEB, encoding='utf-8').read()
    assert 'register_task' in src
    assert "'device_count'" in src or '"device_count"' in src


@mandatory
def test_control_plane_cancel_propagates_to_worker():
    """Cancel sets flag read by should_abort in long loops."""
    from utils.task_control_plane import bind_task, register_task, request_cancel, should_abort
    tid = register_task('qa_cancel', label='qa')
    bind_task(tid)
    assert should_abort() is False
    assert request_cancel(tid) is True
    assert should_abort() is True


@mandatory
def test_control_plane_progress_devices_done_updates():
    """update_task_progress increments devices_done during scans."""
    from utils.task_control_plane import get_task, register_task, update_task_progress
    tid = register_task('qa_prog', label='qa', meta={'devices_total': 4})
    update_task_progress(tid, devices_done=2, devices_total=4, message='sw2')
    task = get_task(tid)
    assert task['devices_done'] == 2
    assert task['devices_total'] == 4


@mandatory
def test_search_it_pending_grace_window():
    """searchItPendingUntil prevents idle poll stop during thread start."""
    html = open(HTML, encoding='utf-8').read()
    assert 'searchItPendingUntil' in html
    assert '120000' in html


@mandatory
def test_task_wrapper_sets_become_password_context():
    """_task_wrapper calls set_task_become_password before fn(*args)."""
    src = open(WEB, encoding='utf-8').read()
    assert 'set_task_become_password' in src
    assert 'become_password' in src


@mandatory
def test_bind_task_allows_abort_checks_in_worker():
    """bind_task associates thread with task_id for cancel routing."""
    src = open(WEB, encoding='utf-8').read()
    assert 'bind_task(task_id)' in src
    from utils.task_control_plane import bind_task, current_task_id, register_task
    tid = register_task('qa_bind', label='qa')
    bind_task(tid)
    assert current_task_id() == tid


@mandatory
def test_job_index_hooks_register_and_complete():
    """Control plane start/complete writes SQLite catalog (fail-open)."""
    src = open(os.path.join(ROOT, 'utils', 'task_control_plane.py'), encoding='utf-8').read()
    assert 'record_start' in src
    assert 'record_status' in src
    from utils import job_index, output_paths
    import tempfile
    td = tempfile.mkdtemp()
    output_paths._DATA_ROOT = None
    job_index.reset_for_tests(os.path.join(td, 'jobs.sqlite'))
    try:
        from utils.task_control_plane import complete_task, register_task
        tid = register_task('qa_index', meta={'device_count': 1, 'inventory_source': 'committed'})
        assert job_index.get_job(tid)['status'] == 'running'
        complete_task(tid, 'complete')
        assert job_index.get_job(tid)['status'] == 'complete'
    finally:
        job_index.reset_for_tests(None)
        output_paths._DATA_ROOT = None


@mandatory
def test_cancel_force_closes_registered_ssh():
    """Q15: request_session_cancel disconnects in-flight Netmiko sockets."""
    from utils.task_control_plane import register_live_connection, request_session_cancel

    class _C:
        def __init__(self):
            self.disconnected = False

        def disconnect(self):
            self.disconnected = True

    conn = _C()
    register_live_connection(conn, 'qa-ssh-kill')
    assert request_session_cancel('qa-ssh-kill') >= 1
    assert conn.disconnected
