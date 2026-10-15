"""Committed vs unsaved inventory source for execute/validate."""
from __future__ import annotations

import pytest

from modules import inventory_store as store
from tests.execute_test_helpers import execute_json, seed_execute_vault
from vlan_checker_web import filter_inventory


def _local(**kwargs):
    kwargs.setdefault('environ_base', {'REMOTE_ADDR': '127.0.0.1'})
    return kwargs


COMMITTED = '10.10.1.1,cisco_ios,DIST\n10.10.1.2,cisco_nxos,DIST\n'
BOX_DIFF = '10.9.9.9,cisco_ios,LAB\n'


def test_state_match_differs_empty(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    assert store.describe_inventory_state(COMMITTED)['state'] == 'match'
    assert store.describe_inventory_state(BOX_DIFF)['state'] == 'differs'
    assert store.describe_inventory_state('')['state'] == 'committed_only'
    monkeypatch.setenv('NST_INVENTORY_PATH', str(tmp_path / 'missing.txt'))
    assert store.describe_inventory_state('')['state'] == 'both_empty'
    assert store.describe_inventory_state(BOX_DIFF)['state'] == 'no_committed'


def test_resolve_committed_ignores_box(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    r = store.resolve_scope_text(BOX_DIFF, 'committed', action='connectivity')
    assert r['source_used'] == 'committed'
    assert r['warning'] == 'box_differs_using_committed'
    devices = filter_inventory(r['text'], 'bulk', '', '', 'All')
    assert [d['host'] for d in devices] == ['10.10.1.1', '10.10.1.2']


def test_resolve_empty_box_uses_committed(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    r = store.resolve_scope_text('', 'committed', action='mac_check')
    assert r['source_used'] == 'committed'
    assert r['accepted_count'] == 2


def test_legacy_body_still_wins_when_source_omitted(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    r = store.resolve_scope_text(BOX_DIFF, None, action='connectivity')
    assert r['source_used'] == 'unsaved'
    assert r['legacy'] is True
    devices = filter_inventory(r['text'], 'bulk', '', '', 'All')
    assert devices[0]['host'] == '10.9.9.9'


def test_sensitive_unsaved_requires_ack(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    with pytest.raises(store.UnsavedInventoryError):
        store.resolve_scope_text(BOX_DIFF, 'unsaved', action='add_vlan', acknowledge_unsaved=False)
    ok = store.resolve_scope_text(
        BOX_DIFF, 'unsaved', action='add_vlan', acknowledge_unsaved=True,
    )
    assert ok['source_used'] == 'unsaved'


def test_legacy_sensitive_does_not_409(tmp_path, monkeypatch):
    """Old clients omit inventory_source — must not break add_vlan tests."""
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    r = store.resolve_scope_text(BOX_DIFF, None, action='add_vlan')
    assert r['legacy'] is True
    assert r['source_used'] == 'unsaved'


def test_malformed_box_committed_still_runs(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    r = store.resolve_scope_text('not-a-line\n', 'committed', action='topology')
    assert r['source_used'] == 'committed'
    assert r['accepted_count'] == 2


def test_zero_accepted_committed(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text('badline\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    r = store.resolve_scope_text('', 'committed', action='connectivity')
    assert r['accepted_count'] == 0


def test_execute_committed_vs_unsaved_http(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    from unittest.mock import patch
    from vlan_checker_web import app
    import vlan_checker_web as web
    app.config['TESTING'] = True
    client = app.test_client()
    seed_execute_vault(web, str(tmp_path / 'vault'))
    base = execute_json(
        target_mode='bulk',
        filter='',
        group='All',
        single_host='',
        mac_address='aa:bb:cc:dd:ee:ff',
    )
    with patch('vlan_checker_web.threading.Thread') as mock_thread:
        mock_thread.return_value.start = lambda: None
        r = client.post(
            '/api/execute',
            json=dict(base, action='mac_check', inventory=BOX_DIFF, inventory_source='committed'),
            **_local(),
        )
    assert r.status_code == 200
    body = r.get_json()
    assert body['status'] == 'started'
    assert body['inventory_source'] == 'committed'
    assert body['inventory_state'] == 'differs'
    assert body['device_count'] == 2

    denied = client.post(
        '/api/execute',
        json=dict(
            base, action='add_vlan', vlan_id='20', vlan_name='USERS',
            inventory=BOX_DIFF, inventory_source='unsaved',
        ),
        **_local(),
    )
    assert denied.status_code == 409
    assert denied.get_json().get('code') == 'unsaved_inventory'

    with patch('vlan_checker_web.threading.Thread') as mock_thread:
        mock_thread.return_value.start = lambda: None
        ok = client.post(
            '/api/execute',
            json=dict(
                base, action='add_vlan', vlan_id='20', vlan_name='USERS',
                inventory=BOX_DIFF, inventory_source='unsaved',
                acknowledge_unsaved=True,
            ),
            **_local(),
        )
    assert ok.status_code == 200
    assert ok.get_json()['inventory_source'] == 'unsaved'

    with patch('vlan_checker_web.threading.Thread') as mock_thread:
        mock_thread.return_value.start = lambda: None
        empty = client.post(
            '/api/execute',
            json=dict(base, action='mac_check', inventory='', inventory_source='committed'),
            **_local(),
        )
    assert empty.status_code == 200
    assert empty.get_json()['inventory_source'] == 'committed'


def test_source_compare_endpoint(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text(COMMITTED, encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    r = client.post('/api/inventory/source', json={'text': BOX_DIFF}, **_local())
    assert r.status_code == 200
    assert r.get_json()['state'] == 'differs'
