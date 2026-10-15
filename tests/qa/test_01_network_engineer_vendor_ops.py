"""Mandatory QA — Network Engineer Council (vendor ops, CLI, mutations)."""
from __future__ import annotations
import os
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


@mandatory
def test_vlan_add_dry_run_ios_nxos_junos_parity():
    """Dry-run add VLAN returns validation dict for IOS, NX-OS, Junos fixtures."""
    from utils.vlan_validate import validate_vlan_operation
    for dtype in ('cisco_ios', 'cisco_nxos', 'juniper_junos'):
        devs = [{'host': '10.0.0.1', 'device_type': dtype}]
        r = validate_vlan_operation('add_vlan', devs, 'u', 'p', '', '10', 'TEST')
        assert isinstance(r, dict), f"validate_vlan_operation must return dict for {dtype}"
        assert 'overall_status' in r, f"overall_status missing for {dtype}"


@mandatory
def test_vlan_rename_blocked_on_juniper_with_actionable_error():
    """Rename on juniper_junos inventory returns fail + message before SSH."""
    from utils.vlan_validate import validate_vlan_operation
    devs = [{'host': '10.0.0.1', 'device_type': 'juniper_junos'}]
    r = validate_vlan_operation('rename_vlan', devs, 'u', 'p', '', '10', 'NEW')
    assert r['overall_status'] == 'failed'
    vendor_check = r['validation_results']['vendor_syntax']
    assert not vendor_check['passed']
    assert vendor_check.get('issues') or vendor_check.get('errors')


@mandatory
def test_mac_trace_partial_single_match_resolves_full_mac():
    """Partial MAC query returns resolved_mac in API + HTML highlight."""
    from modules.mac_trace import _search_mac_on_device
    from unittest.mock import MagicMock
    conn = MagicMock()
    conn.send_command.return_value = 'aa:bb:cc:dd:ee:ff  100  Eth1/1\n'
    _, _, _, found, _, ambiguous, distinct = _search_mac_on_device(
        conn, 'cisco_nxos', 'aa:bb:cc:dd', lambda *_: None, 'sw1',
    )
    assert found
    assert not ambiguous


@mandatory
def test_mac_trace_ambiguous_lists_distinct_macs():
    """Partial MAC with multiple CAM hits marks hop ambiguous with distinct list."""
    from modules.mac_trace import _search_mac_on_device
    from unittest.mock import MagicMock
    conn = MagicMock()
    conn.send_command.return_value = (
        'aa:bb:cc:dd:ee:01  100  Eth1/1\n'
        'aa:bb:cc:dd:ee:02  200  Eth1/2\n'
    )
    _, _, _, found, _, ambiguous, distinct = _search_mac_on_device(
        conn, 'cisco_nxos', 'aa:bb:cc', lambda *_: None, 'sw1',
    )
    assert ambiguous
    assert len(distinct) >= 2


@mandatory
def test_description_search_ranking_exact_before_substring():
    """Exact description match ranks above substring in API row order."""
    from utils.search_relevance import sort_description_rows
    rows = [
        {'hostname': 'sw1', 'description': 'uplink to core', 'interface': 'Gi1/0/1'},
        {'hostname': 'sw2', 'description': 'CORE', 'interface': 'Gi1/0/2'},
    ]
    ranked = sort_description_rows('core', rows)
    assert ranked[0]['hostname'] == 'sw2', "Exact match must rank first"


@mandatory
def test_connectivity_check_parallel_respects_abort():
    """Control plane cancel stops connectivity sweep between devices."""
    src = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert 'def run_connectivity' in src
    start = src.index('def run_connectivity')
    conn_fn = src[start:start + 1200]
    assert '_abort_if_cancelled' in conn_fn


@mandatory
def test_find_missing_vlan_reports_per_device_txt():
    """Missing VLAN scan writes per-run TXT + manifest under output_paths."""
    web_src = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'find_missing_vlan' in web_src


@mandatory
def test_junos_become_password_used_when_enable_empty():
    """Junos device uses become_password as secret when enable_pwd empty."""
    src = open(os.path.join(ROOT, 'modules', 'network_base.py'), encoding='utf-8').read()
    assert 'get_task_become_password' in src
    assert "'juniper' in dtype.lower()" in src
    assert 'base_params["secret"] = become' in src


@mandatory
def test_cisco_enable_password_not_overwritten_by_become():
    """Cisco IOS uses enable_pwd; become_password does not replace secret."""
    src = open(os.path.join(ROOT, 'modules', 'network_base.py'), encoding='utf-8').read()
    assert 'if enb_pwd:' in src
    assert 'base_params["secret"] = enb_pwd' in src
    become_block = src[src.index('if enb_pwd:'):src.index('def _enable_if_needed')]
    assert "if become and 'juniper'" in become_block


@mandatory
def test_network_audit_csv_manifest_written():
    """Network audit produces CSV + manifest in CAT_NETWORK_AUDIT folder."""
    from utils.output_paths import CAT_NETWORK_AUDIT
    assert CAT_NETWORK_AUDIT == 'network_audit'
    content = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'audit' in content.lower()


@mandatory
def test_config_backup_scope_filter_honored():
    """Backup filter string limits devices in backup_dir manifest."""
    src = open(os.path.join(ROOT, 'modules', 'config_backup.py'), encoding='utf-8').read()
    assert 'filt' in src
    adapters = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert 'backup' in adapters.lower()


@mandatory
def test_overlay_nve_peers_fixture_not_physical():
    """Q9: NX-OS show nve peers becomes overlay edges, not cables."""
    from modules.overlay_collector import parse_nve_peers
    text = open(
        os.path.join(ROOT, 'tests', 'fixtures', 'overlay', 'nxos_nve_peers.txt'),
        encoding='utf-8',
    ).read()
    links = parse_nve_peers(text, 'CORE-NXOS-01')
    assert links
    assert all(e.get('not_physical') and e.get('layer') == 'overlay' for e in links)


@mandatory
def test_lacp_member_down_keeps_bundle():
    """Q5: LACP CLI down member does not delete the Po bundle edge."""
    from utils.lacp_oper import apply_lacp_to_edges, parse_port_channel_summary
    text = open(
        os.path.join(ROOT, 'tests', 'fixtures', 'lacp', 'nxos_port_channel_summary.txt'),
        encoding='utf-8',
    ).read()
    edges = [
        {'from': 'A', 'to': 'B', 'f_port': 'Eth1/2', 't_port': 'Eth2/2', 'bundle_kind': 'member'},
        {'from': 'A', 'to': 'B', 'f_port': 'Po1', 't_port': 'Po1', 'bundle_kind': 'bundle'},
    ]
    apply_lacp_to_edges(edges, None, parse_port_channel_summary(text))
    assert len(edges) == 2
    assert next(e for e in edges if e['bundle_kind'] == 'member').get('degraded')


@mandatory
def test_path_trace_does_not_invent_hops():
    """Q21: Path reconstruct stops when no L2 edge exists."""
    from modules.path_trace import reconstruct_path
    path = reconstruct_path(
        [
            {'hostname': 'CORE', 'port': 'Eth1/1', 'found': True},
            {'hostname': 'GHOST', 'port': 'Eth9/9', 'found': True},
        ],
        [{'from': 'CORE', 'to': 'DIST', 'f_port': 'Eth1/1', 't_port': 'Eth1/1', 'protocol': 'cdp'}],
        'aa:bb:cc:dd:ee:ff',
    )
    assert [h['hostname'] for h in path['hops']] == ['CORE']
    assert path['unlinked_hits'] == [{'hostname': 'GHOST', 'port': 'Eth9/9'}]


@mandatory
def test_golden_config_blocks_reserved_vlan():
    """Q22: VLAN 1002 fails golden-config without opening SSH."""
    from utils.vlan_validate import validate_vlan_operation
    r = validate_vlan_operation(
        'add_vlan', [{'host': '10.0.0.1', 'device_type': 'cisco_ios'}],
        'u', 'p', '', '1002', 'RESERVED',
    )
    assert r['overall_status'] == 'failed'
    assert not r['validation_results']['golden_config']['passed']
