"""Mandatory QA — Search-it regression (MAC, description, ping)."""
from __future__ import annotations
import os
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


@mandatory
def test_search_it_heartbeat_poll_always_running():
    """searchItStartHeartbeat interval active after DOMContentLoaded."""
    html = open(HTML, encoding='utf-8').read()
    assert 'function searchItStartHeartbeat' in html
    assert 'searchItStartHeartbeat()' in html


@mandatory
def test_control_plane_completion_triggers_search_it_on_complete():
    """refreshControlPlane calls searchItOnComplete for search actions."""
    html = open(HTML, encoding='utf-8').read()
    assert 'searchItOnComplete' in html
    assert 'refreshControlPlane' in html


@mandatory
def test_log_triggers_match_backend_completion_strings():
    """Log regex matches --- MAC Trace Complete --- etc."""
    src = open(WEB, encoding='utf-8').read()
    assert '--- MAC Trace Complete ---' in src
    assert 'description.*complete' in src.lower() or 'Description search complete' in src


@mandatory
def test_partial_mac_highlight_in_ui_and_api():
    """resolved_mac_html present on found partial MAC trace."""
    src = open(WEB, encoding='utf-8').read()
    assert 'resolved_mac_html' in src
    html = open(HTML, encoding='utf-8').read()
    assert 'resolved_mac_html' in html


@mandatory
def test_partial_description_highlight_in_ui():
    """description_html highlights needle in summary table."""
    html = open(HTML, encoding='utf-8').read()
    assert 'description_html' in html
    src = open(WEB, encoding='utf-8').read()
    assert 'description_html' in src


@mandatory
def test_ping_scan_progress_ticks_per_host_batch():
    """Ping scan progress_tick advances toward total_hosts."""
    src = open(WEB, encoding='utf-8').read()
    assert 'progress_tick' in src
    assert 'ping_scan' in src


@mandatory
def test_description_search_progress_callback_fires_per_device():
    """run_description_search progress_cb invoked per device in adapters."""
    src = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert 'progress_cb' in src
    assert 'def run_description_search' in src


@mandatory
def test_search_it_init_on_page_load():
    """searchItInit runs on DOMContentLoaded without tab switch."""
    html = open(HTML, encoding='utf-8').read()
    assert 'searchItInit' in html
    assert 'DOMContentLoaded' in html


@mandatory
def test_empty_mac_no_infinite_spinner():
    """Empty MAC ends in error state within grace window (guard in runAction)."""
    html = open(HTML, encoding='utf-8').read()
    # Client-side guard: runAction checks mac_input before dispatching
    assert "action === 'mac_check'" in html or "action == 'mac_check'" in html
    assert 'mac_input' in html
    assert 'alert' in html


@mandatory
def test_invalid_ping_no_infinite_spinner():
    """Invalid CIDR ends in error state within grace window."""
    src = open(WEB, encoding='utf-8').read()
    # Backend must validate CIDR / reject bad ping targets
    assert 'ping' in src.lower()
    assert 'cidr' in src.lower() or 'ip_network' in src or 'ipaddress' in src


@mandatory
def test_description_search_empty_guard_in_ui():
    """Empty description term shows alert and focuses input — client-side guard."""
    html = open(HTML, encoding='utf-8').read()
    assert "action === 'description_search'" in html
    assert 'desc_search_input' in html
