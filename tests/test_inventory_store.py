"""Inventory v1 preview, commit replace/merge, bak restore."""
from __future__ import annotations

import pytest

from modules import inventory_store as store
from vlan_checker_web import filter_inventory


SAMPLE = """# comment

[DIST]
10.10.1.1,cisco_nxos,DIST
10.10.1.2,cisco_ios,DIST
10.10.2.1,cisco_ios,DIST
10.10.2.1,cisco_ios,DIST
10.10.9.9,not_a_vendor,DIST
badline-no-comma
10.10.3.1,juniper_junos,DIST
"""


def test_preview_accept_warn_reject():
    out = store.preview(SAMPLE)
    assert out['counts']['accept'] == 4
    assert out['counts']['warn'] == 1
    assert out['counts']['reject'] == 2
    assert out['can_commit'] is True
    hosts = [d['host'] for d in out['accepted']]
    assert hosts == ['10.10.1.1', '10.10.1.2', '10.10.2.1', '10.10.3.1']
    reasons = [r['reason'] for r in out['rows']]
    assert any('duplicate' in x for x in reasons)
    assert any('unknown device_type' in x for x in reasons)
    assert any('parse error' in x for x in reasons)


def test_preview_blank_and_group_headers_are_not_rows():
    out = store.preview('# hi\n\n[Core]\n10.0.0.1,cisco_ios,Core\n')
    assert out['counts']['device_rows'] == 1
    assert out['accepted'][0]['group'] == 'Core'


def test_preview_unknown_type_rejected():
    out = store.preview('10.0.0.1,fortinet,LAB')
    assert out['can_commit'] is False
    assert out['rows'][0]['status'] == 'reject'


def test_preview_rejects_dns_hostname():
    out = store.preview('not-an-ip,cisco_ios,QA\n')
    assert out['can_commit'] is False
    assert out['counts']['reject'] == 1
    assert out['rows'][0]['status'] == 'reject'
    assert 'IPv4 or IPv6' in out['rows'][0]['reason']


def test_preview_accepts_ipv6():
    out = store.preview('2001:db8::1,cisco_ios,LAB\n')
    assert out['can_commit'] is True
    assert out['accepted'][0]['host'] == '2001:db8::1'


def test_preview_type_alias_normalized():
    out = store.preview('10.0.0.1,cisco_ios-xe,LAB')
    assert out['accepted'][0]['device_type'] == 'cisco_xe'
    assert out['rows'][0]['status'] == 'accept'
    assert 'normalized' in out['rows'][0]['reason']


def test_preview_bad_port():
    out = store.preview('10.0.0.1,cisco_ios,99999,LAB')
    assert out['rows'][0]['status'] == 'reject'
    assert 'port' in out['rows'][0]['reason']


def test_preview_rejects_huge_text():
    with pytest.raises(store.InventoryError, match='bytes'):
        store.check_size('x' * (store.MAX_BYTES + 1))
    with pytest.raises(store.InventoryError, match='lines'):
        store.check_size('\n'.join(['10.0.0.1,cisco_ios'] * (store.MAX_LINES + 1)))


def test_filter_inventory_skips_dns_hostnames():
    """Execute scope must not SSH DNS names that Preview rejects."""
    text = (
        'core.example.com,cisco_ios,LAB\n'
        '10.0.0.1,cisco_ios,LAB\n'
        'not-an-ip,cisco_nxos,LAB\n'
    )
    devices = filter_inventory(text, 'bulk', '', '', 'All')
    assert [d['host'] for d in devices] == ['10.0.0.1']
    assert devices[0]['device_type'] == 'cisco_ios'


def test_filter_inventory_normalizes_type_alias():
    devices = filter_inventory('10.0.0.2,cisco_ios-xe,LAB\n', 'bulk', '', '', 'All')
    assert len(devices) == 1
    assert devices[0]['device_type'] == 'cisco_xe'


def test_v1_round_trip_filter_inventory(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    result = store.commit(SAMPLE, 'replace', confirm=True, inventory_path=str(path))
    assert result['written'] == 4
    text = path.read_text(encoding='utf-8')
    devices = filter_inventory(text, 'bulk', '', '', 'All')
    hosts = [d['host'] for d in devices]
    assert hosts == ['10.10.1.1', '10.10.1.2', '10.10.2.1', '10.10.3.1']
    assert all(d['device_type'] in store.ALLOWED_DEVICE_TYPES for d in devices)
    again = store.preview(text)
    assert again['counts']['reject'] == 0
    assert again['counts']['warn'] == 0
    assert again['counts']['accept'] == 4


def test_commit_requires_confirm(tmp_path):
    path = str(tmp_path / 'inventory.txt')
    with pytest.raises(store.InventoryError, match='confirm'):
        store.commit('10.0.0.1,cisco_ios,LAB', 'replace', confirm=False, inventory_path=path)


def test_commit_empty_rejected(tmp_path):
    path = str(tmp_path / 'inventory.txt')
    with pytest.raises(store.InventoryError, match='0 accepted'):
        store.commit('not-valid\n', 'replace', confirm=True, inventory_path=path)


def test_commit_replace_omits_rejects_and_writes_bak(tmp_path):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.9.9.9,cisco_ios,OLD\n', encoding='utf-8')
    result = store.commit(SAMPLE, 'replace', confirm=True, inventory_path=str(path))
    assert result['bak']
    assert result['omitted_reject'] == 2
    assert result['omitted_duplicate'] == 1
    body = path.read_text(encoding='utf-8')
    assert '10.9.9.9' not in body
    assert 'not_a_vendor' not in body
    bak_path = tmp_path / result['bak']
    assert bak_path.is_file()
    assert '10.9.9.9' in bak_path.read_text(encoding='utf-8')


def test_commit_merge_keeps_existing_and_overwrites_same_host(tmp_path):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.10.1.1,cisco_ios,CORE\n8.8.8.8,cisco_ios,EDGE\n', encoding='utf-8')
    incoming = '10.10.1.1,cisco_nxos,DIST\n10.10.1.2,cisco_ios,DIST\n'
    result = store.commit(incoming, 'merge', confirm=True, inventory_path=str(path))
    devices = filter_inventory(path.read_text(encoding='utf-8'), 'bulk', '', '', 'All')
    by_host = {d['host']: d for d in devices}
    assert by_host['10.10.1.1']['device_type'] == 'cisco_nxos'
    assert by_host['10.10.1.1']['group'] == 'DIST'
    assert '8.8.8.8' in by_host
    assert '10.10.1.2' in by_host
    assert result['written'] == 3


def test_bak_prune_keeps_ten(tmp_path):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.0.0.1,cisco_ios,A\n', encoding='utf-8')
    for i in range(12):
        store.commit(
            f'10.0.0.{i},cisco_ios,A\n',
            'replace',
            confirm=True,
            inventory_path=str(path),
        )
    assert len(store.list_baks(str(path))) == store.BAK_KEEP


def test_restore_and_reject_path_traversal(tmp_path):
    path = tmp_path / 'inventory.txt'
    store.commit('10.0.0.1,cisco_ios,A\n', 'replace', confirm=True, inventory_path=str(path))
    store.commit('10.0.0.2,cisco_ios,B\n', 'replace', confirm=True, inventory_path=str(path))
    baks = store.list_baks(str(path))
    assert baks
    oldest_first_content = '10.0.0.1,cisco_ios,A'
    # restore the bak that still has .1 if present, else just restore latest bak
    target = None
    for b in baks:
        text = (tmp_path / b['name']).read_text(encoding='utf-8')
        if oldest_first_content in text:
            target = b['name']
            break
    if target is None:
        target = baks[0]['name']
    restored = store.restore(target, confirm=True, inventory_path=str(path))
    assert restored['ok'] is True
    with pytest.raises(store.InventoryError, match='traversal|Invalid'):
        store.restore('../inventory.txt.bak.x', confirm=True, inventory_path=str(path))
    with pytest.raises(store.InventoryError, match='traversal|Invalid'):
        store.restore('/tmp/evil', confirm=True, inventory_path=str(path))
    with pytest.raises(store.InventoryError, match='confirm'):
        store.restore(target, confirm=False, inventory_path=str(path))
