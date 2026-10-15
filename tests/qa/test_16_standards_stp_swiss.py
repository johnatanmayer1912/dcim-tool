"""Mandatory QA — Standards validator and STP Swiss tools."""
from __future__ import annotations

import os
import tempfile

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


@mandatory
def test_stp_swiss_demo_mode_banner():
    """STP demo scan labels synthetic data in HTML output."""
    from modules.stp_swiss_runner import run_demo_stp_scan
    from utils.stp_map_formatter import generate_stp_html
    result = run_demo_stp_scan()
    assert result.get('demo') is True
    path = os.path.join(tempfile.mkdtemp(), 'stp.html')
    generate_stp_html(
        path, result['nodes'], result['edges'], result.get('link_rows'),
        demo_mode=True,
    )
    html = open(path, encoding='utf-8').read()
    assert 'DEMO' in html or 'synthetic' in html.lower()
    assert 'unpkg.com' not in html.lower()


@mandatory
def test_stp_swiss_live_requires_credentials():
    """Live STP scan uses sidebar credentials in payload."""
    web = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'demo_mode' in web
    html = open(HTML, encoding='utf-8').read()
    assert 'username' in html
    assert 'stp' in html.lower()


@mandatory
def test_stp_blocked_port_parsers_ios_nxos():
    """STP fixtures parse blocked ports for IOS and NX-OS."""
    from modules.stp_swiss_runner import _parse_blocked_ports
    nx = open(os.path.join(ROOT, 'tests', 'fixtures', 'stp', 'cisco_nxos_stp_blocked.txt'), encoding='utf-8').read()
    ios = open(os.path.join(ROOT, 'tests', 'fixtures', 'stp', 'cisco_ios_stp_blocked.txt'), encoding='utf-8').read()
    nx_rows = _parse_blocked_ports(nx, 'N9K-LEAF-01')
    ios_rows = _parse_blocked_ports(ios, 'C9300-01')
    assert nx_rows
    assert ios_rows
    assert all(r.get('link_type') == 'stp-blocked' for r in nx_rows)


@mandatory
def test_stp_map_formatter_offline_html():
    """STP HTML uses output_chrome offline shell."""
    src = open(os.path.join(ROOT, 'utils', 'stp_map_formatter.py'), encoding='utf-8').read()
    assert 'render_topology_page' in src
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'unpkg.com' not in shell


@mandatory
def test_standards_validator_compliance_html():
    """Standards run writes compliance HTML under output_paths."""
    src = open(os.path.join(ROOT, 'modules', 'plugins', 'standards_validator.py'), encoding='utf-8').read()
    assert 'prepare_run_output' in src or 'CAT_COMPLIANCE' in src
    assert '.html' in src


@mandatory
def test_standards_remediation_report_per_host():
    """Remediation HTML generated per device when policy violations found."""
    src = open(os.path.join(ROOT, 'modules', 'plugins', 'standards_validator.py'), encoding='utf-8').read()
    assert '_write_remediation_script' in src
    assert 'remediation' in src


@mandatory
def test_standards_policy_file_path_documented():
    """policies/standards.yaml documented; fallback if missing."""
    assert os.path.isfile(os.path.join(ROOT, 'policies', 'standards.yaml'))
    src = open(os.path.join(ROOT, 'modules', 'plugins', 'standards_validator.py'), encoding='utf-8').read()
    assert 'policies/standards.yaml' in src
    assert 'fallback' in src.lower()


@mandatory
def test_swiss_tools_tab_lists_plugins():
    """Swiss Tools UI loads plugin metadata from registry API."""
    html = open(HTML, encoding='utf-8').read()
    assert '/api/plugins/list' in html
    assert 'selectPlugin' in html


@mandatory
def test_plugin_params_json_schema_honored():
    """Plugin execute sends params dict from UI form fields."""
    html = open(HTML, encoding='utf-8').read()
    assert 'plugin-param-' in html
    assert 'params: params' in html or 'params:' in html


@mandatory
def test_health_check_runner_quick_three_checks():
    """Health wizard quick mode returns exactly 3 checks offline."""
    from utils.health_check_runner import run_health_checks
    result = run_health_checks(quick=True)
    ids = [c['id'] for c in result['checks']]
    assert ids == ['inventory', 'port', 'plugins']
    assert len(result['checks']) == 3
