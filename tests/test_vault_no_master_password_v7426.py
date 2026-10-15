"""v7.4.26 — credentials usable without master password (machine-key vault)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client_local(tmp_path, monkeypatch):
    from modules.credential_manager import CredentialManager
    import vlan_checker_web as web

    vault = tmp_path / 'vault'
    vault.mkdir(parents=True, exist_ok=True)
    cm = CredentialManager(storage_dir=str(vault))
    monkeypatch.setattr(web, 'credential_manager', cm)
    web.app.config['TESTING'] = True
    return web.app.test_client()


def test_status_ready_without_master_password(client_local):
    r = client_local.get('/api/credentials/master-password/status')
    assert r.status_code == 200
    d = r.get_json()
    assert d.get('ready') is True
    assert d.get('is_required') is False
    assert d.get('mode') == 'machine_key'


def test_set_master_password_api_retired(client_local):
    r = client_local.post('/api/credentials/master-password/set', json={'password': 'x' * 12})
    assert r.status_code == 400
    body = r.get_json() or {}
    assert 'no longer required' in (body.get('error') or '').lower()


def test_list_add_resolve_without_unlock(client_local):
    add = client_local.post('/api/credentials/add', json={
        'username': 'noc_ops',
        'password': 'lab-secret',
        'label': 'NOC',
        'force': True,
    })
    assert add.status_code == 200, add.get_json()
    listed = client_local.get('/api/credentials/list')
    assert listed.status_code == 200, listed.get_json()
    rows = (listed.get_json() or {}).get('credentials') or []
    assert any(r.get('username') == 'noc_ops' for r in rows)
    got = client_local.get('/api/credentials/get/noc_ops')
    assert got.status_code == 200
    blob = str(got.get_json() or {}).lower()
    assert 'lab-secret' not in blob


def test_legacy_unlock_migrates_and_stays_open():
    from modules.credential_manager import CredentialManager

    tmp = tempfile.mkdtemp()
    cm = CredentialManager(storage_dir=tmp)
    assert cm.add_credential('u1', 'p1')[0]
    assert cm.set_master_password('legacy-master')[0]
    locked = CredentialManager(storage_dir=tmp)
    assert locked.is_master_password_required()
    assert locked.unlock_with_master_password('legacy-master')
    assert not locked.is_master_password_required()
    again = CredentialManager(storage_dir=tmp)
    assert not again.is_master_password_required()
    assert again.get_credential('u1')['password'] == 'p1'
    assert os.path.exists(os.path.join(tmp, '.credential_key'))
    assert not os.path.exists(os.path.join(tmp, '.credentials_master_hash'))


def test_ui_has_no_daily_master_password_prompt():
    html = (ROOT / 'modules' / 'web' / 'templates' / 'index.html').read_text(encoding='utf-8')
    assert 'Master password is required to access your credentials' not in html
    assert 'Set Master Password' not in html
    assert 'Unlock once' in html
    assert 'machine key' in html.lower()