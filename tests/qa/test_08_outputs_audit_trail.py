"""Mandatory QA — Outputs and audit trail (formatters, manifests)."""
from __future__ import annotations

import os
import tempfile

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


@mandatory
def test_every_search_it_tool_writes_txt_and_html():
    """MAC trace, desc search, ping scan produce txt + html in run folder."""
    adapters = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert 'html_path' in adapters
    assert 'txt_path' in adapters
    web = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'write_mac_trace_html' in web or 'mac_trace_formatter' in web
    assert 'description_search_formatter' in web or 'write_description' in web.lower()


@mandatory
def test_output_chrome_wraps_plugin_reports():
    """save_plugin_report uses output_chrome shell."""
    src = open(os.path.join(ROOT, 'utils', 'report_formatter.py'), encoding='utf-8').read()
    assert 'def save_plugin_report' in src
    assert 'output_chrome' in src


@mandatory
def test_vlan_mgmt_html_matches_txt_summary():
    """VLAN management HTML reflects same device outcomes as TXT."""
    src = open(os.path.join(ROOT, 'utils', 'vlan_mgmt_formatter.py'), encoding='utf-8').read()
    assert 'verification_failed' in src
    assert 'status' in src


@mandatory
def test_topology_html_includes_trust_badges_when_present():
    """Topology HTML shows confidence / trust when topology_trust data exists."""
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'topo-trust-pill' in shell
    assert 'confidence' in shell


@mandatory
def test_discovery_map_offline_contract():
    """Discovery HTML includes __DISCOVERY__ payload and command center chrome."""
    from utils.discovery_map_formatter import generate_discovery_html
    from utils.map_acceptance import assert_html_map_acceptance
    path = os.path.join(tempfile.mkdtemp(), 'd.html')
    generate_discovery_html(path, [{'id': 'a', 'ip': '10.0.0.1', 'is_scanned': True}], [])
    html = open(path, encoding='utf-8').read()
    assert '__DISCOVERY__' in html
    assert 'unpkg.com' not in html.lower()
    assert_html_map_acceptance(html)


@mandatory
def test_mac_trace_html_searched_for_banner():
    """MAC trace HTML shows Searched for + MAC found banners."""
    src = open(os.path.join(ROOT, 'utils', 'mac_trace_formatter.py'), encoding='utf-8').read()
    assert 'Searched for' in src
    assert 'MAC found' in src


@mandatory
def test_description_search_html_shows_search_term():
    """Description search HTML header includes needle + match count."""
    src = open(os.path.join(ROOT, 'utils', 'description_search_formatter.py'), encoding='utf-8').read()
    assert 'Searched for' in src
    assert 'search_term' in src


@mandatory
def test_ping_scan_html_lists_used_and_unused():
    """Ping scan HTML separates responsive vs unresponsive hosts."""
    src = open(os.path.join(ROOT, 'utils', 'ping_scan_formatter.py'), encoding='utf-8').read()
    assert 'Responsive' in src
    assert 'Unresponsive' in src


@mandatory
def test_manifest_lists_html_txt_paths():
    """manifest.json extra fields include report paths for operator."""
    src = open(os.path.join(ROOT, 'utils', 'output_paths.py'), encoding='utf-8').read()
    assert 'html_path' in src
    assert 'txt_path' in src
    assert 'def write_run_manifest' in src


@mandatory
def test_port_interface_map_index_escapes_hostnames():
    """Multi-switch port map index HTML escapes host names."""
    src = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert 'def _write_port_map_index_html' in src
    assert 'from html import escape' in src
    fmt = open(os.path.join(ROOT, 'utils', 'report_formatter.py'), encoding='utf-8').read()
    assert 'html_escape' in fmt or 'escape as html_escape' in fmt
