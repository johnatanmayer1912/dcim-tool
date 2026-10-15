"""Closeout contracts for v7.4.22 — design system, emoji-free chrome, map theme."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'modules/web/templates/index.html'


def test_version_7422():
    ver = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    assert tuple(int(x) for x in ver.split('.')) >= (7, 4, 22)


def test_design_system_file_and_link():
    css = ROOT / 'modules/web/static/nst-enterprise.css'
    assert css.is_file()
    assert '--color-accent' in css.read_text(encoding='utf-8')
    html = HTML.read_text(encoding='utf-8')
    assert 'href="/static/nst-enterprise.css"' in html


def test_no_decorative_emoji_in_console_html():
    html = HTML.read_text(encoding='utf-8')
    emos = set(re.findall(r'[\U0001F300-\U0001FAFF]', html))
    assert not emos, f'Remaining emoji: {sorted(emos)[:30]}'


def test_im_handlers_present():
    html = HTML.read_text(encoding='utf-8')
    for name in ('refreshInterfaceMap', 'exportInterfaceMap', 'clearImLogs', 'downloadImLogs'):
        assert f'function {name}' in html


def test_map_shell_theme_wired():
    assert (ROOT / 'utils/map_shell_theme.py').is_file()
    for rel in (
        'utils/l3_map_shell.py',
        'utils/standard_map_shell.py',
        'utils/vpc_map_shell.py',
        'utils/discovery_map_shell.py',
        'utils/topo_map_shell.py',
    ):
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert 'enterprise_map_css' in text, rel


def test_topo_default_accent_system_blue():
    text = (ROOT / 'utils/topo_map_shell.py').read_text(encoding='utf-8')
    assert "accent='#0a84ff'" in text
    assert "def shell_css(accent='#0a84ff')" in text
