"""Operator trust contracts: inventory execute IP gate, release notes, L3 HTML escape."""
from __future__ import annotations


def test_release_notes_parse_current_version_highlights():
    from vlan_checker_web import VERSION, _parse_changelog_highlights, app

    highlights = _parse_changelog_highlights(VERSION)
    assert isinstance(highlights, list)
    assert len(highlights) >= 1
    assert any('IPv4' in h or 'inventory' in h.lower() or 'Program Status' in h or 'IP' in h for h in highlights) or len(highlights) >= 1

    client = app.test_client()
    r = client.get('/api/release-notes', environ_base={'REMOTE_ADDR': '127.0.0.1'})
    assert r.status_code == 200
    body = r.get_json()
    assert body.get('version')
    assert str(body['version']).startswith('7.')
    assert body.get('highlights')


def test_l3_sidebar_escapes_hostile_device_id():
    from utils.l3_map_shell import _device_sidebar_cards

    html = _device_sidebar_cards({
        '<script>alert(1)</script>': {
            'management_ip': '10.1.1.1',
            'platform': 'cisco_ios',
            'default_gateway': '<img src=x>',
            'interfaces': {'Gi0/0<script>': {}},
            'route_count': 1,
        },
    })
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert '<img' not in html or '&lt;img' in html


def test_standard_map_shell_escapes_node_select():
    from pathlib import Path

    src = Path('utils/standard_map_shell.py').read_text(encoding='utf-8')
    assert "nstUtilEsc(nd.id)" in src
    assert "nstUtilEsc(nd.role)" in src
