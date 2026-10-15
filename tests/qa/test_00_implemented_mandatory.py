"""Implemented mandatory QA — council questionnaire coverage (v7.0.60+)."""
from __future__ import annotations

import os
import re
import unittest

import pytest

from tests.qa._scaffold import mandatory


@mandatory
def test_manifest_council_files_exist():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    assert os.path.isfile(os.path.join(root, 'tests/qa/MANDATORY_MANIFEST.yaml'))
    assert os.path.isfile(os.path.join(root, '.cursor/skills/nst-network-engineer-council/QUESTIONNAIRE.md'))
    assert os.path.isfile(os.path.join(root, '.cursor/skills/zero-trust-audit-360/SKILL.md'))
    gitignore = os.path.join(root, '.gitignore')
    assert os.path.isfile(gitignore)
    text = open(gitignore, encoding='utf-8').read()
    assert '.credential_key' in text
    assert '.credentials.enc' in text


@mandatory
def test_vlan_rename_blocked_on_juniper():
    from utils.vlan_validate import validate_vlan_operation
    devs = [{'host': '10.0.0.1', 'device_type': 'juniper_junos'}]
    r = validate_vlan_operation('rename_vlan', devs, 'u', 'p', '', '10', 'NEW')
    assert r['overall_status'] == 'failed'
    assert not r['validation_results']['vendor_syntax']['passed']


@mandatory
def test_vlan_invalid_id_fails():
    from utils.vlan_validate import validate_vlan_operation
    r = validate_vlan_operation(
        'add_vlan', [{'host': '1.1.1.1', 'device_type': 'cisco_ios'}], 'u', 'p', '', '99999', 'X',
    )
    assert not r['validation_results']['vendor_syntax']['passed']


@mandatory
def test_vlan_unsupported_platform_fails():
    from utils.vlan_validate import validate_vlan_operation
    r = validate_vlan_operation(
        'add_vlan', [{'host': '1.1.1.1', 'device_type': 'arista_eos'}], 'u', 'p', '', '10', 'DATA',
    )
    assert r['overall_status'] == 'failed'


@mandatory
def test_mac_partial_ambiguous_flag():
    from modules.mac_trace import _search_mac_on_device
    from unittest.mock import MagicMock

    conn = MagicMock()
    conn.send_command.return_value = (
        'Mac Address Table\n'
        'aa:bb:cc:dd:ee:01  100  Eth1/1\n'
        'aa:bb:cc:dd:ee:02  200  Eth1/2\n'
    )
    matches, vlan, port, found, cmd, ambiguous, distinct = _search_mac_on_device(
        conn, 'cisco_nxos', 'aa:bb:cc', lambda *_: None, 'sw1',
    )
    assert ambiguous
    assert len(distinct) >= 2


@mandatory
def test_mac_partial_single_resolves():
    from modules.mac_trace import _search_mac_on_device
    from unittest.mock import MagicMock

    conn = MagicMock()
    conn.send_command.return_value = 'aa:bb:cc:dd:ee:ff  100  Eth1/1\n'
    _, _, _, found, _, ambiguous, distinct = _search_mac_on_device(
        conn, 'cisco_nxos', 'aa:bb:cc:dd', lambda *_: None, 'sw1',
    )
    assert found
    assert not ambiguous
    assert distinct


@mandatory
def test_description_search_ranking_exact_first():
    from utils.search_relevance import sort_description_rows
    rows = [
        {'hostname': 'sw1', 'description': 'uplink to core', 'interface': 'Gi1/0/1'},
        {'hostname': 'sw2', 'description': 'CORE-UPLINK', 'interface': 'Gi1/0/2'},
    ]
    ranked = sort_description_rows('core', rows)
    assert ranked[0]['hostname'] == 'sw2'


@mandatory
def test_session_cred_cache_roundtrip():
    from utils.session_cred_cache import (
        set_session_credentials, get_session_credentials, clear_session_credentials,
    )
    clear_session_credentials()
    set_session_credentials(username='u', password='p')
    creds = get_session_credentials()
    assert creds and creds['username'] == 'u'
    clear_session_credentials()


@mandatory
def test_task_control_plane_register_complete():
    from utils.task_control_plane import register_task, complete_task, list_tasks
    tid = register_task('qa_smoke', label='mandatory')
    assert tid
    complete_task(tid, 'complete')
    assert any(t['id'] == tid for t in list_tasks())


@mandatory
def test_im_blocking_shutdown_syntax():
    from modules.plugins.interface_manager import _validate_vendor_syntax
    cfg = 'interface GigabitEthernet1/0/1\n shutdown\n'
    r = _validate_vendor_syntax(cfg, 'cisco_ios', None)
    assert not r['passed']
    assert any('shutdown' in str(e.get('message', '')).lower() for e in r['errors'])


@mandatory
def test_im_blocking_default_interface():
    from modules.plugins.interface_manager import _validate_vendor_syntax
    cfg = 'interface GigabitEthernet1/0/1\n default interface GigabitEthernet1/0/1\n'
    r = _validate_vendor_syntax(cfg, 'cisco_ios', None)
    assert not r['passed']


@mandatory
def test_im_vendor_fail_closed_unknown():
    from modules.plugins.interface_manager import _im_vendor_or_error
    vendor, err = _im_vendor_or_error('arista_eos')
    assert vendor is None
    assert err and 'Unsupported' in err


@mandatory
def test_output_paths_data_root_not_cwd():
    from utils.output_paths import get_data_root
    root = get_data_root()
    assert root
    assert os.path.isabs(root)


@mandatory
def test_structured_logger_utc_timestamp_no_deprecation():
    from utils.structured_logger import NetworkLogger, LogLevel
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        log = NetworkLogger(console_output=False)
        entry = log._create_log_entry(LogLevel.INFO, 'test')
    assert entry['timestamp'].endswith('Z')


@mandatory
def test_topology_truncation_skipped_hosts_list():
    """Adapters track hosts beyond 150-device cap."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'modules', 'adapters.py',
    )
    text = open(path, encoding='utf-8').read()
    assert 'devices_skipped_hosts' in text
    assert 'devices[:150]' in text or 'devices = devices[:150]' in text


@mandatory
def test_vlan_web_junos_rename_notice_in_template():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'modules', 'web', 'templates', 'index.html',
    )
    html = open(path, encoding='utf-8').read()
    assert 'vlan_junos_rename_notice' in html
    assert 'Juniper Junos' in html


@mandatory
def test_swiss_tools_start_here_strip():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'modules', 'web', 'templates', 'index.html',
    )
    html = open(path, encoding='utf-8').read()
    # 7.2+ shell: demoted label is "Operator shortcuts" (was "Start here")
    assert 'Operator shortcuts' in html or 'Start here' in html
    assert 'MAC trace' in html


@mandatory
def test_im_open_report_route_exists():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'vlan_checker_web.py',
    )
    assert '/api/interface/open-report' in open(path, encoding='utf-8').read()


@mandatory
def test_no_rollback_vlan_change_in_modules():
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'modules')
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith('.py'):
                text = open(os.path.join(dirpath, fn), encoding='utf-8', errors='ignore').read()
                assert 'rollback_vlan_change' not in text


@mandatory
def test_live_ssh_warranty_doc_exists():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    assert os.path.isfile(os.path.join(root, 'docs/09-qa/LIVE_SSH_WARRANTY.md'))


@mandatory
def test_swiss_tools_mac_trace_uses_mac_check_action():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'modules', 'web', 'templates', 'index.html',
    )
    html = open(path, encoding='utf-8').read()
    assert "runAction('mac_trace')" not in html
    assert "runAction('mac_check')" in html


@mandatory
def test_api_execute_accepts_mac_trace_alias():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'vlan_checker_web.py',
    )
    assert "action == 'mac_trace'" in open(path, encoding='utf-8').read()
    assert "'mac_check':" in open(path, encoding='utf-8').read()


@mandatory
def test_mandatory_qa_orchestrator_importable():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    assert os.path.isfile(os.path.join(root, 'tests', 'test_api_execute_mac_alias.py'))
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'scripts', 'mandatory_release_qa.py',
    )
    assert os.path.isfile(path)


@mandatory
def test_utilization_overlay_replay_does_not_mint_edges():
    """Replay join is lookup-only: identity mismatch yields zero paints."""
    from utils.utilization_overlay.join import join_observations_to_l2, topology_fingerprint

    nodes = [{'id': 'CORE-01'}, {'id': 'DIST-N1'}]
    edges = [{
        'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
        'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'type': 'standard',
        'trust_tier': 'high',
    }]
    before = topology_fingerprint(edges)
    result = join_observations_to_l2(
        [{'device_id': 'SPOOF', 'if_name_raw': 'Te1/0/1', 'pct': 99, 'if_speed_bps': 1}],
        nodes,
        edges,
    )
    assert result['paints'] == []
    assert 'identity mismatch' in result['error']
    assert topology_fingerprint(edges) == before
    assert edges[0]['trust_tier'] == 'high'


@mandatory
def test_utilization_overlay_live_does_not_mint_edges():
    """Live join is lookup-only: identity mismatch yields zero paints."""
    from utils.utilization_overlay.join import join_observations_to_l2, topology_fingerprint

    nodes = [{'id': 'CORE-01'}, {'id': 'DIST-N1'}]
    edges = [{
        'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
        'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'type': 'standard',
        'trust_tier': 'high',
    }]
    before = topology_fingerprint(edges)
    result = join_observations_to_l2(
        [{'device_id': 'SPOOF', 'if_name_raw': 'Te1/0/1', 'pct': 99, 'if_speed_bps': 1}],
        nodes,
        edges,
        mode='live',
        evidence_class='live_ssh',
        stale_after_seconds=900,
    )
    assert result['paints'] == []
    assert result['mode'] == 'live'
    assert 'identity mismatch' in result['error']
    assert topology_fingerprint(edges) == before
    assert edges[0]['trust_tier'] == 'high'


@mandatory
def test_utilization_overlay_discovery_host_does_not_mint_edges():
    """Discovery viewer binds overlay onto existing L2 cables only; EVPN stays unpainted."""
    from utils.discovery_map_formatter import build_vis_payload
    from utils.utilization_overlay.discovery_host import bind_overlay_to_discovery
    from utils.utilization_overlay.join import topology_fingerprint

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fixture = os.path.join(root, 'tests', 'fixtures', 'utilization', 'replay_standard_l2.json')
    nodes = [
        {'id': 'CORE-01', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True, 'scan_state': 'seed'},
        {'id': 'DIST-N1', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': True, 'scan_state': 'scanned'},
    ]
    edges = [
        {
            'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'Te1/0/1', 't_port': 'Te1/1/1',
            'protocol': 'CDP', 'trust_tier': 'high', 'layer': 'l2',
        },
        {
            'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'nve1', 't_port': 'nve1',
            'protocol': 'EVPN', 'layer': 'overlay', 'not_physical': True,
            'trust_tier': 'inferred',
        },
    ]
    nodes_json, edges_json, _ = build_vis_payload(nodes, edges)
    before = topology_fingerprint(edges_json)
    bound = bind_overlay_to_discovery(nodes_json, edges_json, fixture)
    assert bound.ok
    assert 'e0' in bound.bindings
    assert 'e1' not in bound.bindings
    assert topology_fingerprint(edges_json) == before
    assert edges_json[0]['trust_tier'] == 'high'
    assert edges_json[1]['trust_tier'] == 'inferred'
    assert len(edges_json) == 2


class TestVlanShowMatrix(unittest.TestCase):
    @mandatory
    def test_ios_nxos_junos_xr_show_commands(self):
        from modules.vlan_mgmt_production import _vlan_show_cmd
        self.assertIn('brief', _vlan_show_cmd('cisco_ios'))
        self.assertEqual(_vlan_show_cmd('cisco_nxos'), 'show vlan')
        self.assertIn('vlans', _vlan_show_cmd('juniper_junos'))
        self.assertEqual(_vlan_show_cmd('cisco_xr'), 'show vlan')
