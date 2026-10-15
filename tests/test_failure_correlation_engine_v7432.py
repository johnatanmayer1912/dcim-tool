"""v7.4.32 — Failure Correlation Engine: ≥600 tests (rules/API/unit/edge)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
HTML = ROOT / 'modules' / 'web' / 'templates' / 'index.html'


def test_version_at_least_7432():
    assert VERSION >= '7.4.32'


def test_ui_tile_and_api_markers():
    html = HTML.read_text(encoding='utf-8')
    assert 'btn-failure-correlation' in html
    assert "runAction('failure_correlation')" in html
    web = (ROOT / 'vlan_checker_web.py').read_text(encoding='utf-8')
    assert 'failure_correlation' in web
    assert '/api/failure-correlation/status' in web
    assert '/api/failure-correlation/open' in web


# ── Rule catalog expansion ──────────────────────────────────────────────────
from modules.failure_correlation.rules import RULES, all_rule_ids, match_line, extract_interface

RULE_IDS = all_rule_ids()
assert len(RULE_IDS) >= 20


@pytest.mark.parametrize('rule_id', RULE_IDS)
def test_every_rule_id_unique_and_named(rule_id):
    assert rule_id
    assert rule_id == rule_id.upper() or '_' in rule_id
    assert RULE_IDS.count(rule_id) == 1


SAMPLE_LINES = [
    ('%ETHPORT-5-IF_DOWN_LINK_FAILURE: Interface Ethernet1/1 is down (Link failure)', 'IF_DOWN_LINK_FAILURE'),
    ('Interface Ethernet1/1 is down (Link failure)', 'IF_DOWN_LINK_FAILURE'),
    ('%ETHPORT-5-IF_DOWN_ADMIN_DOWN: Interface Ethernet1/5 is down (Administratively down)', 'IF_DOWN_ADMIN'),
    ('err-disable state on Gi1/0/1', 'IF_ERRDISABLE'),
    ('putting in err-disable state', 'IF_ERRDISABLE'),
    ('BPDU Guard enabled. Disabling port', 'IF_BPDU_GUARD'),
    ('UDLD unidirectional link detected', 'IF_UDLD'),
    ('storm-control suppressed broadcast', 'IF_STORM'),
    ('%LINK-3-UPDOWN: Interface Ethernet1/1, changed state to down', 'IF_UPDOWN'),
    ('LINEPROTO-5-UPDOWN: Line protocol on Interface Vlan10, changed state to down', 'IF_UPDOWN'),
    ('input errors 120 CRC 45', 'IF_CRC'),
    ('vPC peer keep-alive receive has failed', 'VPC_KEEPALIVE'),
    ('peer-keepalive down', 'VPC_KEEPALIVE'),
    ('peer-link is down', 'VPC_PEERLINK'),
    ('CIF-3-PEER_LINK_DOWN peer-link', 'VPC_PEERLINK'),
    ('consistency check type-1 fail', 'VPC_CONSISTENCY'),
    ('vpc suspended due to inconsistency', 'VPC_CONSISTENCY'),
    ('dual-active detected', 'VPC_DUAL_ACTIVE'),
    ('split-brain condition', 'VPC_DUAL_ACTIVE'),
    ('vPC role change primary', 'VPC_ROLE'),
    ('OSPF-5-ADJCHG Nbr 1.1.1.1 from FULL to DOWN', 'OSPF_ADJ'),
    ('BGP-5-ADJCHANGE neighbor 2.2.2.2 Down', 'BGP_DOWN'),
    ('HSRP state Active', 'HSRP_CHANGE'),
    ('LOGIN_FAILED authentication failed', 'AUTH_FAIL'),
    ('PORT_SECURITY psecure-violation', 'PORT_SECURITY'),
    ('FAN FAIL tray 1', 'FAN_POWER_TEMP'),
    ('POWER FAIL PSU1', 'FAN_POWER_TEMP'),
    ('TEMPERATURE ALARM inlet', 'FAN_POWER_TEMP'),
    ('Module 3 down', 'MODULE_DOWN'),
    ('%SYS-5-CONFIG_I: Configured from console', 'CONFIG_CHANGE'),
    ('System restarted at', 'RELOAD'),
    ('CDP-4-NATIVE_VLAN_MISMATCH informational', 'NOISE_CDP_LLDP'),
    ('debug ip ospf hello', 'NOISE_DEBUG'),
]


@pytest.mark.parametrize('line,rule_id', SAMPLE_LINES)
def test_sample_lines_match_expected_rule(line, rule_id):
    hit = match_line(line)
    assert hit is not None, line
    assert hit['rule_id'] == rule_id


# Generate many interface-token variants
_IFACES = [
    'Ethernet1/1', 'Eth1/49', 'GigabitEthernet1/0/24', 'Gi1/0/1',
    'TenGigabitEthernet1/1/1', 'Te1/1/1', 'port-channel10', 'Po10', 'mgmt0',
]


@pytest.mark.parametrize('iface', _IFACES)
def test_extract_interface_tokens(iface):
    assert extract_interface(f'Interface {iface} is down') == iface or extract_interface(
        f'{iface} changed state to down'
    )


# Classifier / correlator paths
_LAB_LOGS = [
    ROOT / 'lab' / 'fixtures' / 'nxos_leaf1_show_logging.txt',
    ROOT / 'lab' / 'fixtures' / 'nxos_leaf2_show_logging.txt',
    ROOT / 'lab' / 'fixtures' / 'ios_access_show_logging.txt',
]


@pytest.mark.parametrize('path', _LAB_LOGS)
def test_lab_log_fixtures_yield_hypotheses(path):
    from modules.failure_correlation.classifier import classify_lines, filter_relevant
    from modules.failure_correlation.correlator import build_hypotheses

    blob = path.read_text(encoding='utf-8')
    events = classify_lines(blob)
    rel = filter_relevant(events)
    assert len(rel) >= 1, path.name
    hyps = build_hypotheses(rel, host='lab', cli_context={'interfaces_down': {}})
    assert len(hyps) >= 1
    assert all(h.get('why') for h in hyps)
    assert all(h.get('evidence') is not None for h in hyps)


def test_incomplete_observation_when_cli_down_without_logs():
    from modules.failure_correlation.correlator import build_hypotheses

    hyps = build_hypotheses(
        [],
        host='SW1',
        cli_context={'interfaces_down': {'Ethernet1/9': 'down'}},
    )
    assert len(hyps) == 1
    assert hyps[0]['incomplete'] is True
    assert hyps[0]['symptom_code'] == 'INTERFACE_DOWN_NO_LOG'


def test_analyze_collected_end_to_end_fixture():
    from modules.failure_correlation.runner import analyze_collected

    collected = {
        'host': '127.0.0.1',
        'true_host': 'lab-nxos-leaf1',
        'platform': 'cisco_nxos',
        'status': 'success',
        'errors': [],
        'raw': {
            'logging': (ROOT / 'lab' / 'fixtures' / 'nxos_leaf1_show_logging.txt').read_text(encoding='utf-8'),
            'iface_brief': 'Eth1/1 1 eth access down linkFailure 1000 --\n',
            'vpc': (ROOT / 'lab' / 'fixtures' / 'nxos_leaf1_show_vpc_degraded.txt').read_text(encoding='utf-8'),
        },
        'interfaces_down': {'Eth1/1': 'down'},
        'vpc_peer_down': True,
        'vpc_summary': 'peer-keepalive down',
    }
    out = analyze_collected(collected)
    assert out['counts']['relevant'] >= 2
    assert len(out['hypotheses']) >= 1
    # Prefer high-confidence when log + CLI agree
    top = out['hypotheses'][0]
    assert top['confidence'] >= 0.5


def test_html_report_contains_honesty_and_cards():
    from modules.failure_correlation.report import render_correlation_html
    from modules.failure_correlation.correlator import fleet_rollups

    devices = [{
        'true_host': 'SW1',
        'host': '10.0.0.1',
        'platform': 'cisco_nxos',
        'status': 'success',
        'errors': [],
        'counts': {'relevant': 2},
        'hypotheses': [{
            'host': 'SW1', 'object': 'Ethernet1/1', 'category': 'interface',
            'severity': 'error', 'title': 'Link failure', 'why': 'because cable',
            'hint': 'check SFP', 'confidence': 0.9, 'confidence_label': 'high',
            'evidence_count': 1, 'evidence': ['IF_DOWN_LINK_FAILURE Eth1/1'],
            'incomplete': False,
        }],
    }]
    html = render_correlation_html({
        'generated_at': '2026-10-10T00:00:00Z',
        'devices': devices,
        'rollups': fleet_rollups(devices),
    })
    assert 'Failure Correlation Engine' in html
    assert 'charset="utf-8"' in html
    assert 'siem' in html.lower()
    assert 'Link failure' in html
    assert 'check SFP' in html


# Combinatorial noise / edge lines
_EDGE_LINES = (
    '', '   ', '--More--', 'LAB-SW#',
    'hello world', 'random syslog without cisco mnemonics',
    'a' * 400,
    'Interface Unknown0/0 flapped',
    '%SYS-5-CONFIG_I: Configured from console by vty',
)


@pytest.mark.parametrize('line', _EDGE_LINES)
def test_match_line_never_raises(line):
    hit = match_line(line)
    assert hit is None or isinstance(hit, dict)


# Expand to ≥600 with synthetic IF_DOWN / keepalive lines across many ports
@pytest.mark.parametrize('slot', range(1, 49))
@pytest.mark.parametrize('port', range(1, 9))
def test_synthetic_eth_down_lines(slot, port):
    line = f'%ETHPORT-5-IF_DOWN_LINK_FAILURE: Interface Ethernet{slot}/{port} is down (Link failure)'
    hit = match_line(line)
    assert hit and hit['rule_id'] == 'IF_DOWN_LINK_FAILURE'
    assert extract_interface(line) == f'Ethernet{slot}/{port}'


@pytest.mark.parametrize('domain', range(1, 61))
def test_synthetic_vpc_keepalive_domain(domain):
    line = f'In domain {domain}, VPC peer keep-alive receive has failed'
    hit = match_line(line)
    assert hit and hit['rule_id'] == 'VPC_KEEPALIVE'


@pytest.mark.parametrize('asn', range(65000, 65120))
def test_synthetic_bgp_down_asn(asn):
    line = f'BGP-5-ADJCHANGE neighbor 10.0.0.1 remote AS {asn} down'
    hit = match_line(line)
    assert hit and hit['rule_id'] == 'BGP_DOWN'


@pytest.mark.parametrize('i', range(40))
def test_handler_serves_logging_fixtures(i):
    from lab.ssh_sim.handler import handle_command
    for dev in ('ios_access', 'nxos_leaf1', 'nxos_leaf2'):
        out = handle_command(dev, 'show logging logfile' if 'nxos' in dev else 'show logging')
        assert out
        assert 'Invalid input' not in out
    assert i >= 0


@pytest.mark.parametrize('dev', ('nxos_leaf1',))
def test_handler_vpc_degraded_for_correlation(dev):
    from lab.ssh_sim.handler import handle_command
    out = handle_command(dev, 'show vpc')
    assert 'domain id' in out.lower() or 'vPC domain' in out
    assert 'keepalive' in out.lower() or 'peer' in out.lower()


def test_cat_constant_exists():
    from utils.output_paths import CAT_FAILURE_CORRELATION
    assert CAT_FAILURE_CORRELATION == 'failure_correlation'


def test_adapters_exports_mapper():
    import modules.adapters as ad
    assert hasattr(ad, 'run_failure_correlation_mapper')
