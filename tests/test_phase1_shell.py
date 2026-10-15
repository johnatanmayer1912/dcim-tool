"""Phase 1 six-workspace chrome — static HTML + helper contracts."""
from __future__ import annotations

from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / 'modules' / 'web' / 'templates' / 'index.html'


def _html() -> str:
    return HTML.read_text(encoding='utf-8')


def test_six_workspace_nav_and_aria():
    html = _html()
    for ws in ('inventory', 'maps', 'find', 'change', 'evidence', 'settings'):
        assert f'id="ws-nav-{ws}"' in html
        assert f'id="ws-{ws}"' in html
    assert 'aria-label="Operator jobs"' in html
    assert "btn.setAttribute('aria-current', 'page')" in html
    assert 'nstBindKeyboard' in html
    assert 'querySelector(\'[data-tab=' not in html


def test_legacy_tab_bridge_preserved():
    html = _html()
    for tab in (
        'diag', 'interfaces', 'vlan', 'interface_manager', 'tools', 'plugins',
        'standards', 'discovery', 'templates', 'credentials', 'about',
    ):
        assert f'id="tab-segment-{tab}"' in html
        assert f'id="tab-{tab}"' in html
    assert "function goToSearchTab" in html
    assert "function goToToolsTab" in html
    assert "function goToDiscoveryTab" in html
    assert "getElementById('tab-segment-' + tabId)" in html
    assert 'NST_TAB_WORKSPACE' in html


def test_chrome_has_cancel_stop_vault_no_password_value():
    html = _html()
    assert 'id="nst-vault-pill"' in html
    assert 'id="nst-cred-label"' in html
    assert 'id="btn-chrome-cancel"' in html
    assert 'id="btn-chrome-stop"' in html
    assert 'onclick="shutdownApp()"' in html
    assert 'id="nst-task-strip-body"' in html
    assert 'id="password"' in html
    assert 'nst-chrome' in html
    assert '@media (max-width: 900px)' in html
    assert '.mac-window { min-width: 0' in html
    assert 'mac-window {\n                min-width: 1280px' not in html


def _section_open_tag(html: str, section_id: str) -> str:
    key = f'<section id="{section_id}"'
    i = html.find(key)
    assert i >= 0, section_id
    j = html.find('>', i)
    return html[i:j + 1]


def test_first_paint_only_inventory_workspace_exposed():
    html = _html()
    inv = _section_open_tag(html, 'ws-inventory')
    assert 'is-active' in inv
    assert ' hidden' not in inv and 'inert' not in inv
    assert 'aria-labelledby="ws-h1-inventory"' in inv
    assert 'id="ws-nav-inventory"' in html
    assert 'aria-current="page"' in html.split('id="ws-nav-inventory"', 1)[1][:120]
    hold = html.split('id="nst-panel-hold"', 1)[1].split('<!-- /nst-panel-hold -->', 1)[0]
    assert 'id="tab-diag"' in hold
    assert 'id="tab-tools"' in hold
    hold_open = html[html.find('<div id="nst-panel-hold"'):html.find('>', html.find('<div id="nst-panel-hold"')) + 1]
    assert 'hidden' in hold_open and 'inert' in hold_open and 'aria-hidden="true"' in hold_open
    for ws in ('maps', 'find', 'change', 'evidence', 'settings'):
        tag = _section_open_tag(html, f'ws-{ws}')
        assert 'hidden' in tag
        assert 'inert' in tag
        assert 'aria-hidden="true"' in tag
        assert 'is-active' not in tag
    assert 'function nstApplyWorkspaceA11y' in html
    assert 'function nstHideTabView' in html
    assert 'function nstRevealTabView' in html
    assert '.nst-workspace[hidden]' in html


def test_evidence_uses_jobs_api_not_file_reader():
    html = _html()
    assert "fetch('/api/jobs?limit=50')" in html
    assert 'function nstLoadEvidence' in html
    assert 'not a file browser' in html
    assert 'nstRevealJob' in html
    assert 'nstRerunJob' in html
    assert '/api/jobs/' in html and 'pack' in html
    assert 'No indexed jobs yet. This is a job catalog' in html
    assert 'nstEvidenceArtifactCopy' in html
    assert 'Download pack' in html or 'Pack</a>' in html or "Pack'" in html


def test_path_trace_gated():
    html = _html()
    assert 'id="path-trace-btn"' in html
    assert 'nstUpdatePathTraceGate' in html
    assert 'disabled' in html.split('id="path-trace-btn"', 1)[1][:220]


def test_run_action_contract_untouched():
    html = _html()
    assert "function runAction" in html
    assert "fetch('/api/execute'" in html
    assert "runAction('mac_check')" in html


def test_inventory_editor_lives_in_inventory_workspace():
    html = _html()
    inv_ws = html.split('id="ws-inventory"', 1)[1].split('id="ws-maps"', 1)[0]
    assert 'id="nst-inventory-block"' in inv_ws
    assert 'id="inventory"' in inv_ws
    assert 'id="nst-inv-host-body"' in inv_ws
    aside_key = '<aside class="sidebar'
    assert aside_key in html
    sidebar = html.split(aside_key, 1)[1].split('id="nst-main"', 1)[0]
    assert 'id="nst-inventory-block"' not in sidebar
    assert 'Made by AI IDE' not in html
    assert 'function nstSanitizeLogHtml' in html
    assert 'function nstRenderInvHostTable' in html
    assert 'console-panel' in html
    assert 'collapsed' in html or 'id="console-panel"' in html or 'class="console-panel' in html
    assert "loadInventory();" in html.split('nstAdoptPanels();', 1)[1][:400]
    assert 'nst-chrome-meta' in html
    assert 'nst-start-workflows' in html
    assert 'ENTERPRISE UI/UX DESIGN SYSTEM v7.2' in html
