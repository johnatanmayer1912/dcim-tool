"""v7.4.30 — Docker lab fabric (1 IOS + 2× 93180) + credential UX contracts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'modules' / 'web' / 'templates' / 'index.html'
VERSION = ROOT / 'VERSION'


def test_version():
    assert VERSION.read_text(encoding='utf-8').strip() >= '7.4.30'


def test_lab_devices_are_93180_pair_plus_ios():
    from lab.ssh_sim.handler import DEFAULT_PORT_MAP, LAB_DEVICES, handle_command

    assert DEFAULT_PORT_MAP[2201] == 'ios_access'
    assert DEFAULT_PORT_MAP[2202] == 'nxos_leaf1'
    assert DEFAULT_PORT_MAP[2203] == 'nxos_leaf2'
    assert LAB_DEVICES['nxos_leaf1']['pid'] == 'N9K-C93180YC-EX'
    assert LAB_DEVICES['nxos_leaf2']['pid'] == 'N9K-C93180YC-EX'
    inv1 = handle_command('nxos_leaf1', 'show inventory')
    inv2 = handle_command('nxos_leaf2', 'show inventory')
    assert 'N9K-C93180YC-EX' in inv1 and 'FDO23180EX01' in inv1
    assert 'N9K-C93180YC-EX' in inv2 and 'FDO23180EX02' in inv2
    assert 'C9300-24P' in handle_command('ios_access', 'show inventory')
    cdp = handle_command('nxos_leaf1', 'show cdp neighbors detail')
    assert 'LAB-NXOS-LEAF2' in cdp and 'LAB-IOS-ACCESS1' in cdp
    # Device ID must match hostname (no serial suffix) so L2 map does not split nodes
    assert 'LAB-NXOS-LEAF2(FDO' not in cdp


def test_credential_ux_hidden_id_sync_and_draft_copy():
    html = HTML.read_text(encoding='utf-8')
    assert 'nstSyncCredIdsFromSidebar' in html
    assert 'Draft only' in html
    assert 'not</b> sent' in html or 'not</b> sent to devices' in html
    assert "type=\"hidden\" id=\"credential_id\"" in html or 'id="credential_id"' in html


def test_inventory_file_present():
    inv = (ROOT / 'lab' / 'docker' / 'inventory.nst.txt').read_text(encoding='utf-8')
    assert '2201' in inv and '2202' in inv and '2203' in inv
    assert 'cisco_nxos' in inv and 'cisco_ios' in inv
