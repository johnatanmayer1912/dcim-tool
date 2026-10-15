"""P1 accessibility contracts — heading order, contrast, map landmarks."""
from __future__ import annotations

from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "modules" / "web" / "templates" / "index.html"
STD_SHELL = Path(__file__).resolve().parents[1] / "utils" / "standard_map_shell.py"
TOPO_SHELL = Path(__file__).resolve().parents[1] / "utils" / "topo_map_shell.py"
DISC_SHELL = Path(__file__).resolve().parents[1] / "utils" / "discovery_map_shell.py"
REPORT = Path(__file__).resolve().parents[1] / "utils" / "report_formatter.py"


def test_find_and_change_use_h2_not_h5_workspace_titles():
    html = HTML.read_text(encoding="utf-8")
    assert '<h2 class="tab-view-title">Network Search' in html
def test_vlan_title_is_h2():
    html = HTML.read_text(encoding="utf-8")
    assert "VLAN Mutating Operations" in html
    idx = html.find("VLAN Mutating Operations")
    assert "<h2" in html[max(0, idx - 120) : idx]


def test_section_headers_not_low_contrast_purple():
    html = HTML.read_text(encoding="utf-8")
    assert 'color:#8b5cf6; font-weight:600;">v7.0.4' not in html
    assert "color:#4338ca" not in html.split("Description Search", 1)[0][-200:]


def test_standard_map_scroll_region_keyboard():
    text = STD_SHELL.read_text(encoding="utf-8")
    assert 'class="nst-conn-table-wrap" tabindex="0"' in text
    assert 'role="banner"' in text


def test_topo_and_discovery_have_main_landmark():
    assert "<main id=\"main-wrap\">" in TOPO_SHELL.read_text(encoding="utf-8")
    assert '<main class="disc-cc-main">' in DISC_SHELL.read_text(encoding="utf-8")


def test_generated_topology_html_has_lang():
    text = REPORT.read_text(encoding="utf-8")
    assert "<html lang=\"en\">" in text
    assert "<main class=\"{layout_container_class}" in text


def test_tab_section_headings_are_h2_then_h3():
    html = HTML.read_text(encoding="utf-8")
    assert "<h5" not in html
    assert "<h6" not in html
    assert "</h5>" not in html
    assert "</h6>" not in html
    assert '<h2 class="card-title">Swiss Tools</h2>' in html
    assert '<h2 class="card-title">' in html and "Network Discovery" in html
    assert "MAC Address Search" in html
    idx = html.find("MAC Address Search")
    assert "<h3" in html[max(0, idx - 80) : idx]


def test_operator_muted_and_primary_button_contrast_tokens():
    html = HTML.read_text(encoding="utf-8")
    assert "--text-muted: #475569;" in html
    assert "--text-secondary: #475569;" in html
    assert "--color-success: #047857;" in html
    assert "background: #1d4ed8;" in html
    assert 'id="nst-evidence-status"' in html
    evid = html.split('id="nst-evidence-status"', 1)[1][:80]
    assert "#475569" in evid


def test_legacy_segments_not_focusable():
    html = HTML.read_text(encoding="utf-8")
    marker = '<div class="nst-legacy-segments'
    assert marker in html
    tag = html.split(marker, 1)[1].split(">", 1)[0]
    assert "tabindex" not in tag
    assert "inert" in tag


def test_dark_chrome_meta_is_light_on_dark():
    html = HTML.read_text(encoding="utf-8")
    assert ".nst-pill.is-unknown { color: #cbd5e1;" in html
    brand = html.split(".nst-brand span", 1)[1][:180]
    assert "color: #cbd5e1;" in brand
    text = DISC_SHELL.read_text(encoding="utf-8")
    assert "body.discovery-command-center .nst-fresh { color: #334155; }" in text
    assert "body.discovery-command-center header h1" in text
    assert "color: #0f172a;" in text.split("body.discovery-command-center header h1", 1)[1][:120]
