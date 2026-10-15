"""Gap-closeout tests: path-trace edges, backup advice, ntc/NAPALM/SNMP, plugin history."""
from __future__ import annotations

import json
import os
import time

import pytest

from utils import output_paths
from utils.config_backup_system import ConfigBackupSystem


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    output_paths._DATA_ROOT = None
    yield tmp_path
    output_paths._DATA_ROOT = None


def test_backup_health_advice_points_to_tools(isolated):
    root = output_paths.get_backups_root()
    bs = ConfigBackupSystem(backup_dir=os.path.join(root, 'devices'))
    miss = bs.check_backup_age('ghost-sw')
    assert miss['warning'] is True
    assert 'Tools' in miss['message']
    assert "Run 'Config Backup'" not in miss['message']

    # Tools run-folder backup should satisfy age check
    out_cfg = os.path.join(output_paths.get_outputs_root(), 'config_backup', 'run1')
    os.makedirs(out_cfg, exist_ok=True)
    cfg = os.path.join(out_cfg, 'leaf1_config.txt')
    with open(cfg, 'w', encoding='utf-8') as fh:
        fh.write('hostname leaf1\n')
    ok = bs.check_backup_age('leaf1')
    assert ok['has_backup'] is True
    assert ok['warning'] is False


def test_topology_edges_status_requires_real_edges(isolated):
    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager

    vault = isolated / 'vault'
    vault.mkdir(parents=True, exist_ok=True)
    web.app.config['TESTING'] = True
    web.credential_manager = CredentialManager(storage_dir=str(vault))
    web._last_topology = {
        'status': 'complete',
        'html_path': '/tmp/fake.html',
        'diag_folder': '',
    }
    c = web.app.test_client()
    r = c.get('/api/topology/edges-status', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    body = r.get_json()
    assert body['edge_count'] == 0
    assert body['has_l2_edges'] is False

    diag = isolated / 'diag'
    diag.mkdir()
    edges_payload = {
        'edges': [
            {'edge_data': {'source': 'A', 'target': 'B', 'local_port': 'Eth1', 'remote_port': 'Eth2'}},
            {'edge_data': {'source': 'B', 'target': 'C', 'local_port': 'Eth3', 'remote_port': 'Eth4'}},
        ]
    }
    with open(diag / '04_final_map_data.json', 'w', encoding='utf-8') as fh:
        json.dump(edges_payload, fh)
    web._last_topology = {
        'status': 'complete',
        'html_path': str(diag / 'map.html'),
        'diag_folder': str(diag),
    }
    r2 = c.get('/api/topology/status', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r2.status_code == 200
    st = r2.get_json()
    assert st['edge_count'] == 2
    assert st['has_l2_edges'] is True

    r3 = c.get('/api/topology/edges-status', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r3.get_json()['edge_count'] == 2


def test_ntc_and_napalm_style_capabilities():
    from modules.ntc_parse import capability_report, parse_cli, textfsm_available
    from modules.napalm_style import get_facts_from_cli, capability_report as nap_cap

    cap = capability_report()
    assert 'ntc_templates' in cap
    assert textfsm_available() is True
    rows, err = parse_cli('cisco_ios', 'show version', '')
    assert rows == []
    facts = get_facts_from_cli(
        'cisco_ios',
        'Cisco IOS Software, Version 17.3.4a\nProcessor board ID FCW1234ABCD\ncisco ISR4331\n',
        hostname='r1',
    )
    assert facts['os_version']
    assert facts['serial_number'] == 'FCW1234ABCD'
    assert nap_cap()['full_napalm'] is False
    assert 'get_facts' in nap_cap()['getters']


def test_snmp_graphs_unavailable_without_creds(isolated):
    from modules.snmp_interface_graphs import collect_interface_counters, counters_to_html

    payload = collect_interface_counters('10.0.0.1', {'snmp_version': 'none'})
    assert payload['status'] == 'unavailable'
    html = counters_to_html(payload)
    assert 'Interface counter graphs' in html
    assert 'unavailable' in html


def test_snmp_graphs_api_and_plugin_history(isolated):
    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager

    vault = isolated / 'vault'
    vault.mkdir(parents=True, exist_ok=True)
    web.app.config['TESTING'] = True
    web.credential_manager = CredentialManager(storage_dir=str(vault))
    c = web.app.test_client()

    caps = c.get('/api/capabilities/parsers', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert caps.status_code == 200
    assert caps.get_json()['snmp_graphs'] is True

    snmp = c.post(
        '/api/snmp/interface-graphs',
        json={'host': '10.9.9.9'},
        environ_base={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert snmp.status_code == 200
    body = snmp.get_json()
    assert body['status'] == 'unavailable'
    assert body.get('html_path')

    hist = c.get('/api/plugins/history/nonexistent_plugin_xyz', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert hist.status_code == 200
    assert hist.get_json()['history'] == []


def test_adapters_backup_warning_message(isolated):
    root = output_paths.get_backups_root()
    bs = ConfigBackupSystem(backup_dir=os.path.join(root, 'devices'))
    check_result = bs.check_backup_age('10.1.1.99')
    assert check_result.get('warning')
    assert 'Tools' in check_result['message']
    assert "Run 'Config Backup'" not in check_result['message']

    # adapters health summary string
    import modules.adapters as adapters
    src = open(adapters.__file__, encoding='utf-8').read()
    assert 'Tools → Config backup' in src
    assert "Run 'Config Backup' to update" not in src
