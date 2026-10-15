"""Mandatory QA — Software Engineer (API, threading, error paths)."""
from __future__ import annotations
import os
import re
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')


@mandatory
def test_api_execute_rejects_missing_action():
    """POST /api/execute without action returns 400 JSON error."""
    src = open(WEB, encoding='utf-8').read()
    assert 'Invalid API Action' in src
    assert '/api/execute' in src


@mandatory
def test_api_execute_empty_inventory_scope_returns_error():
    """Zero devices after filter returns error before thread spawn."""
    src = open(WEB, encoding='utf-8').read()
    assert 'filter_inventory' in src
    assert 'No devices' in src or 'empty' in src.lower() or re.search(r'len\(devices\)\s*==\s*0', src)


@mandatory
def test_mac_check_empty_target_returns_400_and_progress_done():
    """Empty MAC pre-arm cleared via progress_done; API returns 400."""
    src = open(WEB, encoding='utf-8').read()
    assert 'mac_check' in src
    assert 'progress_done' in src


@mandatory
def test_description_search_empty_term_returns_400():
    """Empty desc_search rejected at API with progress error state."""
    src = open(WEB, encoding='utf-8').read()
    assert 'desc_search' in src
    assert 'description_search' in src


@mandatory
def test_ping_scan_invalid_cidr_returns_400():
    """Invalid CIDR rejected before thread; progress_done error."""
    src = open(WEB, encoding='utf-8').read()
    assert 'ping_scan' in src or 'connectivity' in src


@mandatory
def test_session_credentials_localhost_only():
    """GET/POST /api/session/credentials blocked off localhost."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/session/credentials' in src or 'session.*credentials' in src.lower()
    assert 'localhost' in src or '127.0.0.1' in src


@mandatory
def test_shutdown_clears_session_and_task_credentials():
    """/api/shutdown clears session cred cache."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/shutdown' in src
    assert 'clear_session_credentials' in src


@mandatory
def test_search_it_progress_start_if_needed_preserves_counters():
    """Worker progress_start_if_needed does not reset pre-armed current."""
    from utils import search_it_progress as sip
    sip.progress_start('mac_trace', 10, label='pre-arm')
    sip.progress_tick('mac_trace', 3, 10, host='sw1')
    sip.progress_start_if_needed('mac_trace', 10, label='worker')
    st = sip._cat('mac_trace')
    assert st['status'] == 'running'
    assert int(st['current']) == 3
    sip.progress_done('mac_trace')


@mandatory
def test_mac_trace_last_api_includes_highlight_fields():
    """/api/mac-trace/last returns target_mac_html and resolved_mac_html."""
    src = open(WEB, encoding='utf-8').read()
    assert 'target_mac_html' in src
    assert 'resolved_mac_html' in src
    assert '/api/mac-trace/last' in src


@mandatory
def test_description_search_last_includes_row_html_fields():
    """/api/description-search/last rows include interface_html + description_html."""
    src = open(WEB, encoding='utf-8').read()
    assert 'description_html' in src
    assert '/api/description-search/last' in src


@mandatory
def test_plugin_execute_thread_sets_become_password_context():
    """Plugin wrapper sets task_credentials become for Junos paths."""
    src = open(WEB, encoding='utf-8').read()
    assert 'set_task_become_password' in src
    assert 'plugin:' in src or 'plugin_id' in src


@mandatory
def test_api_logs_get_is_read_only_snapshot():
    """GET /api/logs snapshots the pane buffer; it must not pop/drain."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/logs' in src
    assert 'console_log_buffer' in src or 'OperatorConsoleLogBuffer' in src
    logs_fn = src.split('def api_logs():', 1)[1].split('def api_execute', 1)[0]
    assert 'popleft' not in logs_fn
    assert '.clear()' not in logs_fn
    assert 'snapshot' in logs_fn


@mandatory
def test_discovery_export_fallback_includes_links_and_status():
    """JSON export fallback is not devices-only: includes links and collection_status."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/discovery/export/' in src
    assert '"collection_status": data_block.get("collection_status")' in src
    assert '"links": data_block.get("links", [])' in src


@mandatory
def test_path_trace_and_issues_apis_exist():
    """POST /api/path-trace and GET /api/topology/issues are localhost operator routes."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/path-trace' in src
    assert '/api/topology/issues' in src
    assert 'reconstruct_path' in src
    assert '@localhost_required' in src


@mandatory
def test_inventory_preview_commit_restore_routes():
    """POST /api/inventory/preview|commit|restore exist; commit logs counts not passwords."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/inventory/preview' in src
    assert '/api/inventory/commit' in src
    assert '/api/inventory/restore' in src
    assert 'omitted_reject' in src
    assert 'inventory_store' in src


@mandatory
def test_execute_inventory_source_is_explicit():
    """Execute records inventory_source committed vs unsaved; no silent dual-write."""
    src = open(WEB, encoding='utf-8').read()
    assert 'inventory_source' in src
    assert 'resolve_scope_text' in src
    assert 'UnsavedInventoryError' in src


@mandatory
def test_jobs_index_routes_exist():
    """GET /api/jobs lists catalog metadata; no artifact bodies."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/jobs' in src
    assert 'list_jobs' in src
    assert 'job_index' in src


@mandatory
def test_discovery_im_explicit_target_source():
    """Discovery seeds and IM single-host are not silent bulk inventory."""
    src = open(WEB, encoding='utf-8').read()
    assert 'resolve_discovery_targets' in src
    assert 'resolve_im_target' in src
    assert 'target_source' in src


@mandatory
def test_utilization_live_execute_requires_credential_id():
    """Live SSH utilization is an execute action gated on vault credential_id."""
    src = open(WEB, encoding='utf-8').read()
    assert "'utilization_live':" in src
    assert 'credential_id required for live SSH utilization' in src
    assert '/api/utilization-overlay/status' in src
    assert '_utilization_live_thread' in src
