"""v7.4.28 — Inventory Utilities multi-line tiles must not overlap under Apex."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "modules" / "web" / "templates" / "index.html"
VERSION = ROOT / "VERSION"


def test_version_7428():
    assert VERSION.read_text(encoding="utf-8").strip() >= "7.4.28"


def test_inventory_utilities_use_tile_grid():
    html = HTML.read_text(encoding="utf-8")
    assert 'id="tools-inventory-utilities"' in html
    assert "nst-inv-util-grid" in html
    assert 'id="btn-inv-util-os-audit"' in html
    assert 'id="btn-inv-util-asset-warranty"' in html
    assert 'id="btn-inv-util-port-map"' in html
    assert "nst-tile-btn" in html
    assert "runAction('cisco_asset_warranty')" in html
    chunk_start = html.find('id="tools-inventory-utilities"')
    assert chunk_start > 0
    chunk = html[chunk_start : chunk_start + 2500]
    assert "nst-tile-btn" in chunk
    assert "grid-template-columns" in chunk
    assert "btn-inv-util-os-audit" in chunk
    assert 'style="flex:1; min-width:160px;"' not in chunk
    assert "runAction('audit')" in chunk
    assert "toolsRunPortMap()" in chunk

def test_apex_tile_override_beats_pill_nowrap():
    html = HTML.read_text(encoding="utf-8")
    assert "body.nst-apex-fusion .nst-tile-btn" in html
    assert "flex-direction: column !important" in html
    assert "white-space: normal !important" in html
    # Tile CSS shared with map tiles
    assert ".nst-map-tile-btn," in html or ".nst-map-tile-btn,\n        .nst-tile-btn" in html
