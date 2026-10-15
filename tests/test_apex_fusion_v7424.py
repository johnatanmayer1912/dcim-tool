"""Apex Fusion v7.4.24 — GUI contracts, trusted HUD, operational smoke."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'modules' / 'web' / 'templates' / 'index.html'
CSS = ROOT / 'modules' / 'web' / 'static' / 'nst-enterprise.css'
MOCK = ROOT / 'mocks' / 'gui_external_audit_2026-10-07' / '04_team_apex_fusion.html'
AUDIT = ROOT / '.cursor' / 'audits' / 'APEX_FUSION_GUI_2026-10-07.md'
VERSION = ROOT / 'VERSION'


def test_version_7424():
    assert VERSION.read_text(encoding='utf-8').strip() >= '7.4.29'


def test_apex_css_tokens_present():
    css = CSS.read_text(encoding='utf-8')
    assert 'Apex Fusion' in css
    assert '--color-accent: #00c2d7' in css or '--color-accent: #00a8bc' in css
    assert '--color-accent-2: #14b8a6' in css or '--teal: #14b8a6' in css
    assert '.nst-apex-hud' in css
    assert '.nst-task-strip' in css
    assert 'radial-gradient' in css


def test_live_shell_hooks():
    html = HTML.read_text(encoding='utf-8')
    assert 'nst-apex-fusion' in html
    assert 'nst-enterprise' in html
    assert 'nst-apex-shell' in html
    assert 'nst-apex-top-hud' in html
    assert 'nst-apex-rail' in html
    assert 'nst-apex-drawer' in html
    assert 'nst-apex-main' in html
    assert 'nst-apex-console' in html
    assert 'Command clarity' in html
    assert 'id="nst-apex-hud"' in html
    assert 'id="nst-apex-vault"' in html
    assert 'id="nst-apex-cred"' in html
    assert 'id="nst-apex-scope"' in html
    assert 'id="nst-apex-job"' in html
    assert 'function nstSyncApexHud' in html
    assert 'Network Swiss Tool Pro' in html
    assert 'nst-enterprise.css' in html
    assert 'fonts.googleapis' not in html


def test_hud_sync_called_from_chrome_and_jobs():
    html = HTML.read_text(encoding='utf-8')
    assert html.count('nstSyncApexHud(') >= 3


def test_mock_option4_exists_and_wow_markers():
    assert MOCK.is_file()
    mock = MOCK.read_text(encoding='utf-8')
    assert 'Apex Fusion' in mock
    assert 'Northglass' in mock and 'OpsRail' in mock
    assert 'Command clarity' in mock
    assert 'command' in mock.lower()
    # Offline-safe fonts via Google optional — mock may use CDN; live product must not require CDN for tokens
    assert 'Outfit' in mock or 'IBM Plex Mono' in mock


def test_audit_doc_present():
    text = AUDIT.read_text(encoding='utf-8')
    assert 'no invented' in text.lower() or 'not invented' in text.lower() or 'No invented' in text
    assert '7.4.25' in text or '7.4.24' in text
    assert 'trusted' in text.lower()


def test_no_cdn_required_in_enterprise_css():
    css = CSS.read_text(encoding='utf-8')
    assert 'fonts.googleapis' not in css
    assert '@import' not in css


@pytest.fixture()
def client():
    from vlan_checker_web import app
    app.config['TESTING'] = True
    return app.test_client()


def test_operational_home_serves_apex(client):
    r = client.get('/', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'nst-apex-fusion' in body
    assert 'nst-apex-hud' in body
    assert 'nst-enterprise.css' in body
    assert 'Network Swiss Tool Pro' in body


def test_operational_static_css(client):
    r = client.get('/static/nst-enterprise.css', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    text = r.get_data(as_text=True)
    assert 'Apex Fusion' in text
    assert '--color-accent' in text


def test_operational_version_api(client):
    r = client.get('/api/version', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    assert r.get_json().get('version') >= '7.4.26'


def test_live_shell_matches_mock_regions():
    html = HTML.read_text(encoding='utf-8')
    mock = MOCK.read_text(encoding='utf-8')
    # Shared structural vocabulary (layout regions)
    for token in ('Command clarity', 'Primary rail', 'Instrument log', 'command'):
        assert token.lower() in html.lower() or token in html
    assert 'class="mark"' in html
    assert 'nst-apex-command' in html
    assert 'fx-orb' in html
    # Mock keeps storytelling KPIs; live must not hardcode fake fleet counts
    assert 'Devices in scope' not in html or 'id="nst-apex-' in html
    assert '48</div>' not in html
    assert 'L2 trust edges' not in html


def test_core_operator_apis_still_up(client):
    env = {'REMOTE_ADDR': '127.0.0.1'}
    assert client.get('/api/jobs?limit=5', environ_base=env).status_code == 200
    assert client.get('/api/topology/edges-status', environ_base=env).status_code == 200
    health = client.post('/api/health-check/run', json={'quick': True}, environ_base=env)
    assert health.status_code == 200
    assert 'checks' in (health.get_json() or {})


def test_no_emoji_regression_in_apex_hud_markup():
    html = HTML.read_text(encoding='utf-8')
    # Top HUD region must be emoji-free
    m = re.search(r'nst-apex-top-hud.*?</header>', html, re.S)
    assert m
    emos = set(re.findall(r'[\U0001F300-\U0001FAFF]', m.group(0)))
    assert not emos
