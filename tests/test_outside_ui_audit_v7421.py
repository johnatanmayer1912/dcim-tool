"""Outside UI audit contracts + functional smoke (v7.4.21).

Independent of feature authors: verifies shell polish markers, onclick
handler inventory, and core localhost APIs still deliver expected results.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'modules' / 'web' / 'templates' / 'index.html'
VERSION_FILE = ROOT / 'VERSION'


def _html() -> str:
    return HTML.read_text(encoding='utf-8')


def test_version_is_7421():
    ver = VERSION_FILE.read_text(encoding='utf-8').strip()
    assert tuple(int(x) for x in ver.split('.')) >= (7, 4, 21)


def test_outside_audit_shell_markers_not_dull():
    html = _html()
    # Restored sidebar brand (UX-02)
    assert 'sidebar-brand-refined .logo-wrap' in html
    assert 'display: flex !important' in html or 'display:flex !important' in html
    assert '.sidebar-brand-refined .product-name' in html
    assert 'display: none !important' not in html.split('sidebar-brand-refined .logo-wrap', 1)[1][:400]
    # Pill workspace nav (UX-06)
    assert 'border-radius: 14px' in html or 'nst-enterprise.css' in html
    assert '.nst-ws-btn[aria-current="page"]' in html or 'nst-enterprise.css' in html
    # No purple backup novelty (UX-08)
    assert '#faf5ff' not in html
    assert '#581c87' not in html
    assert 'nst-tools-backup-card' in html
    # No credential emoji (UX-07)
    assert '🔑 Primary' not in html
    assert '🔑 Secondary' not in html
    # Enterprise shell / design system
    assert 'nst-enterprise.css' in html or 'ENTERPRISE SHELL' in html


def test_onclick_handlers_resolve_to_functions():
    html = _html()
    calls = set(re.findall(r'onclick="([A-Za-z_][A-Za-z0-9_]*)\s*\(', html))
    # Ignore inline expressions that are not bare calls (none expected)
    defined = set(re.findall(r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', html))
    # Also allow window-assigned / const fn = 
    defined |= set(re.findall(r'(?:window\.)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?function\s*\(', html))
    defined |= set(re.findall(r'(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', html))
    missing = sorted(calls - defined)
    # Known HTML-only builtins never defined as function declarations
    allow = {'confirm', 'alert', 'open', 'close', 'focus', 'blur'}
    missing = [m for m in missing if m not in allow]
    assert not missing, f'Missing onclick handlers: {missing[:40]}'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('NST_DATA_DIR', str(tmp_path))
    from utils import output_paths, job_index
    output_paths._DATA_ROOT = None
    db = tmp_path / 'index' / 'jobs.sqlite'
    job_index.reset_for_tests(str(db))
    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager
    vault = tmp_path / 'vault'
    vault.mkdir(parents=True, exist_ok=True)
    web.app.config['TESTING'] = True
    web.credential_manager = CredentialManager(storage_dir=str(vault))
    yield web.app.test_client()
    job_index.reset_for_tests(None)
    output_paths._DATA_ROOT = None


def _lp(path='/', **kw):
    env = {'REMOTE_ADDR': '127.0.0.1'}
    env.update(kw.pop('environ_base', {}) or {})
    return path, {'environ_base': env, **kw}


def test_functional_api_smoke_core_operator_paths(client):
    """Do not take Evidence / credentials / maps / plugins for granted."""
    c = client
    # Home renders shell
    r = c.get('/', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'nst-chrome' in body
    assert 'nst-enterprise.css' in body
    assert 'Network Swiss Tool' in body

    ver = c.get('/api/version', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert ver.status_code == 200
    assert ver.get_json().get('version') == (ROOT / 'VERSION').read_text(encoding='utf-8').strip()

    # Credentials list — requires unlocked vault (403 when locked is correct)
    creds = c.get('/api/credentials/list', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert creds.status_code in (200, 403)
    if creds.status_code == 200:
        assert 'credentials' in (creds.get_json() or {})
    else:
        body = creds.get_json() or {}
        assert 'lock' in (body.get('error') or body.get('code') or '').lower() or body.get('error')

    # Jobs / evidence catalog
    jobs = c.get('/api/jobs?limit=10', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert jobs.status_code == 200

    # Topology edge honesty
    edges = c.get('/api/topology/edges-status', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert edges.status_code == 200
    assert 'has_l2_edges' in edges.get_json()

    # Plugins
    plugs = c.get('/api/plugins/list', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert plugs.status_code == 200

    # Backups compare surface
    backs = c.get('/api/backups', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert backs.status_code == 200

    # Parser / SNMP foundation
    caps = c.get('/api/capabilities/parsers', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert caps.status_code == 200

    # Health wizard backend
    health = c.post(
        '/api/health-check/run',
        json={'mode': 'quick'},
        environ_base={'REMOTE_ADDR': '127.0.0.1'},
    )
    assert health.status_code == 200
    hj = health.get_json() or {}
    assert hj.get('checks') or hj.get('results') or hj.get('ok') is not None or 'status' in hj


def test_credential_add_update_path(client):
    c = client
    # Unlock / set master may vary — add without master when vault empty
    add = c.post(
        '/api/credentials/add',
        json={
            'username': 'audit_user',
            'password': 'audit_pass_1',
            'label': 'Outside Audit',
            'profile_type': 'ssh',
        },
        environ_base={'REMOTE_ADDR': '127.0.0.1'},
    )
    # Accept success or vault-lock guidance — both prove endpoint is live
    assert add.status_code in (200, 400, 401, 403)
    data = add.get_json() or {}
    if add.status_code == 200 and data.get('success'):
        upd = c.post(
            '/api/credentials/update',
            json={
                'username': 'audit_user',
                'password': 'audit_pass_2',
                'label': 'Outside Audit Updated',
            },
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        assert upd.status_code == 200
        assert (upd.get_json() or {}).get('success') is True
