"""HTTP contract for /api/inventory preview, commit, restore."""
from __future__ import annotations

import os


def _local(**kwargs):
    kwargs.setdefault('environ_base', {'REMOTE_ADDR': '127.0.0.1'})
    return kwargs


def test_get_inventory_includes_text_and_baks(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.1.1.1,cisco_ios,Core\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    r = client.get('/api/inventory', **_local())
    assert r.status_code == 200
    data = r.get_json()
    assert '10.1.1.1' in data['inventory']
    assert data['path'] == str(path)
    assert 'counts' in data
    assert 'baks' in data


def test_preview_and_commit_replace_round_trip(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.1.1.1,cisco_ios,Core\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    body = (
        '10.10.1.1,cisco_nxos,DIST\n'
        '10.10.1.1,cisco_nxos,DIST\n'
        'nope\n'
        '10.10.2.1,cisco_ios,DIST\n'
    )
    prev = client.post('/api/inventory/preview', json={'text': body}, **_local())
    assert prev.status_code == 200
    p = prev.get_json()
    assert p['counts']['accept'] == 2
    assert p['counts']['warn'] == 1
    assert p['counts']['reject'] == 1

    denied = client.post(
        '/api/inventory/commit',
        json={'text': body, 'mode': 'replace', 'confirm': False},
        **_local(),
    )
    assert denied.status_code == 400
    assert 'confirm' in denied.get_json()['error'].lower()
    assert path.read_text(encoding='utf-8').startswith('10.1.1.1')

    ok = client.post(
        '/api/inventory/commit',
        json={'text': body, 'mode': 'replace', 'confirm': True},
        **_local(),
    )
    assert ok.status_code == 200
    j = ok.get_json()
    assert j['written'] == 2
    assert j['omitted_reject'] == 1
    assert j['omitted_duplicate'] == 1
    text = path.read_text(encoding='utf-8')
    assert '10.10.1.1' in text
    assert '10.1.1.1,cisco_ios' not in text
    assert os.path.isfile(os.path.join(os.path.dirname(path), j['bak']))


def test_restore_rejects_traversal(tmp_path, monkeypatch):
    path = tmp_path / 'inventory.txt'
    path.write_text('10.1.1.1,cisco_ios,Core\n', encoding='utf-8')
    monkeypatch.setenv('NST_INVENTORY_PATH', str(path))
    from vlan_checker_web import app
    app.config['TESTING'] = True
    client = app.test_client()
    r = client.post(
        '/api/inventory/restore',
        json={'bak': '../secrets.txt', 'confirm': True},
        **_local(),
    )
    assert r.status_code == 400
    err = r.get_json()['error'].lower()
    assert 'traversal' in err or 'invalid' in err
