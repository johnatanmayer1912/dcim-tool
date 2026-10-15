# ============================================================================
# tests/test_unified_multi_layer_map.py
# ============================================================================
# PURPOSE:
#   Automated unit and integration test suite for the Unified Multi-Layer Canvas
#   and dedicated STP Layer Switch functionality in utils/topo_map_shell.py.
# ============================================================================

import pytest
from utils.topo_map_shell import (
    layer_switch_html,
    embed_link_inventory_render_js,
    render_topology_page,
)


def test_layer_switch_html_contains_stp_button():
    """Ensure layer_switch_html generates buttons for Physical, L2, L3, Overlay, and STP."""
    html = layer_switch_html()
    assert 'data-layer="physical"' in html
    assert 'data-layer="l2"' in html
    assert 'data-layer="l3"' in html
    assert 'data-layer="overlay"' in html
    assert 'data-layer="stp"' in html
    assert 'STP' in html


def test_layer_switch_html_active_state():
    """Ensure layer_switch_html marks the active layer correctly."""
    html_stp = layer_switch_html(default_layer='stp')
    assert 'data-layer="stp"' in html_stp
    assert 'class="active"' in html_stp

    html_l3 = layer_switch_html(default_layer='l3')
    assert 'data-layer="l3" aria-label="Show layer-3 routing adjacencies" class="active"' in html_l3


def test_layer_switch_js_stp_forwarding_and_blocking_logic():
    """Ensure embed_link_inventory_render_js includes STP role styling (forwarding green, blocking red dashed)."""
    js = embed_link_inventory_render_js()
    assert "layer === 'stp'" in js or 'layer === "stp"' in js
    # Forwarding color check
    assert '#22c55e' in js or '#10b981' in js
    # Blocking dashed check
    assert '#ef4444' in js
    assert 'dashes' in js
    # Hash navigation for STP
    assert "layer === 'stp'" in js


def test_render_topology_page_complete_html(tmp_path):
    """Ensure render_topology_page creates an HTML file containing the layer switcher and Vis.js."""
    out_file = tmp_path / "test_topology.html"
    nodes = [{"id": "sw01", "label": "sw01", "platform": "cisco_ios"}]
    edges = [{"id": "e1", "from": "sw01", "to": "sw02", "port_state": "blocking", "stp_state": "blocking"}]

    render_topology_page(
        str(out_file),
        "Enterprise Multi-Layer Map",
        nodes,
        edges,
        link_rows=[],
    )

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Enterprise Multi-Layer Map" in content
    assert 'data-layer="stp"' in content
    assert 'nstSetLayer' in content
    assert 'nstApplyHashLayer' in content
