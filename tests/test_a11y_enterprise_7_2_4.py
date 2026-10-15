"""7.2.4 enterprise accessibility + UI cleanup contracts."""
from __future__ import annotations

from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "modules" / "web" / "templates" / "index.html"
L3_SHELL = Path(__file__).resolve().parents[1] / "utils" / "l3_map_shell.py"
COMBINED_SHELL = Path(__file__).resolve().parents[1] / "utils" / "combined_l2l3_shell.py"
OUTPUT_CHROME = Path(__file__).resolve().parents[1] / "utils" / "output_chrome.py"
A11Y_SPEC = Path(__file__).resolve().parents[1] / "tests" / "browser" / "accessibility_enterprise_sweep.spec.mjs"


def _html() -> str:
    return HTML.read_text(encoding="utf-8")


def test_main_landmark_role_main():
    html = _html()
    assert 'id="nst-main"' in html and 'role="main"' in html
    assert '<main class="main-content' in html


def test_no_decorative_button_gradients_in_operator_css():
    html = _html()
    assert "linear-gradient(135deg, var(--color-accent)" not in html
    assert "linear-gradient(180deg, #3b82f6" not in html
    assert "btn-mac-primary::before" not in html


def test_maps_hero_is_light_enterprise_card():
    html = _html()
    chunk = html.split("L2 Topology hero", 1)[1][:3500]
    assert "nst-map-hero-card" in chunk
    assert "background:#0f172a" not in chunk.split("nst-map-hero-card", 1)[1][:800]
    assert "rgba(56,189,248" not in chunk
    assert "btn-mac-primary nst-map-tile-btn" in chunk


def test_discovery_seed_box_neutral_surface():
    html = _html()
    chunk = html.split('id="disc-seeds"', 1)[0][-400:]
    assert "rgba(139,92,246" not in chunk


def test_progress_bars_solid_not_gradient():
    html = _html()
    for bar_id in ("mac-progress-bar", "desc-progress-bar", "ping-progress-bar", "disc-progress-bar"):
        seg = html.split(f'id="{bar_id}"', 1)[1][:120]
        assert "linear-gradient" not in seg, bar_id


def test_prefers_reduced_motion_block():
    assert "@media (prefers-reduced-motion: reduce)" in _html()


def test_l3_map_shell_header_flat():
    text = L3_SHELL.read_text(encoding="utf-8")
    assert "linear-gradient(90deg, #1e1b4b" not in text
    assert "background: #1e293b;" in text


def test_combined_l2l3_shell_header_flat():
    text = COMBINED_SHELL.read_text(encoding="utf-8")
    assert "linear-gradient(90deg, #1e1b4b" not in text


def test_output_chrome_report_header_flat():
    text = OUTPUT_CHROME.read_text(encoding="utf-8")
    assert "linear-gradient(135deg, #1e293b" not in text


def test_inventory_hosts_region_not_nested_aside():
    html = _html()
    assert 'class="nst-inv-table-wrap" role="region"' in html
    assert '<aside class="nst-inv-table-wrap"' not in html


def test_sidebar_complementary_landmark():
    html = _html()
    assert 'aria-label="Scope and session"' in html
    assert '<aside class="sidebar' in html


def test_scope_selects_have_accessible_names():
    html = _html()
    assert 'id="target_mode"' in html and 'aria-labelledby="label-target-scope"' in html
    assert 'aria-label="Inventory group filter"' in html
    assert 'aria-label="Single device target"' in html


def test_accessibility_sweep_spec_exists():
    assert A11Y_SPEC.is_file()
    body = A11Y_SPEC.read_text(encoding="utf-8")
    assert "@axe-core/playwright" in body
    assert "inventory" in body and "settings" in body
