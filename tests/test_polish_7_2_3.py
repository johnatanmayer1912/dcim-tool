"""7.2.3 polish residuals — chrome, Find CTAs, Discovery DNS honesty, Flask version API."""
from __future__ import annotations

from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "modules" / "web" / "templates" / "index.html"


def _html() -> str:
    return HTML.read_text(encoding="utf-8")


def test_vlan_validation_panel_is_calm_white():
    html = _html()
    assert 'id="vlan_validation_status_panel"' in html
    chunk = html.split('id="vlan_validation_status_panel"', 1)[1][:500]
    assert "background: #fff" in chunk or "background:#fff" in chunk
    assert "⚡" not in chunk
    assert "linear-gradient(135deg, #f8fafc" not in chunk


def test_find_missing_vlan_uses_btn_mac_primary():
    html = _html()
    assert "find_missing_vlan" in html
    # purple accent removed from Find Missing VLAN CTA
    idx = html.find("find_missing_vlan")
    window = html[max(0, idx - 200) : idx + 80]
    assert "btn-mac-primary" in window
    assert "#9b59b6" not in window


def test_chrome_narrow_meta_media_query():
    html = _html()
    assert "@media (max-width: 1100px)" in html
    assert ".nst-meta-sep { display: none; }" in html or ".nst-meta-sep{display:none" in html.replace(" ", "")
    assert "flex-direction: column" in html


def test_discovery_seed_dns_vs_inventory_documented():
    html = _html()
    assert "disc-seeds" in html
    assert "DNS" in html or "hostname" in html.lower()
    assert "IPv4/IPv6 only" in html or "IPv4 or IPv6" in html
    assert "Not inventory.txt" in html or "not committed inventory" in html.lower()
    # Inventory lede cross-ref
    assert "Discovery crawl seeds" in html or "Maps → Discovery" in html


def test_sidebar_brand_is_quiet_about_link():
    html = _html()
    assert 'id="sidebar-brand-link"' in html
    assert 'class="sidebar-about-label"' in html
    assert "About" in html.split('id="sidebar-brand-link"', 1)[1][:400]
    # demotion CSS hides logo
    assert ".sidebar-brand-refined .logo-wrap" in html
    assert "display: none !important" in html


def test_debug_status_uses_importlib_metadata():
    from vlan_checker_web import app

    src = Path(__file__).resolve().parents[1] / "vlan_checker_web.py"
    text = src.read_text(encoding="utf-8")
    assert "importlib.metadata" in text
    assert "flask.__version__" not in text.split("def debug_status", 1)[1].split("def add_log", 1)[0]
    client = app.test_client()
    r = client.get("/debug_status", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.status_code == 200
    data = r.get_json()
    assert "libraries" in data
    assert "flask" in data["libraries"]
