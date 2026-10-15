"""
Regression tests: map container height chain must never collapse to 0px.

Root cause (fixed 2026-09-03): l3_map_shell, combined_l2l3_shell, and
l3_map_shell_enhanced all used <main> with no CSS rule inside a
`body { display:flex; flex-direction:column; height:100vh }` layout.
The vis.js canvas containers used `height:100%` which resolved to 0px
when `main` had no height in the flex chain → empty map, silent failure.

Fix: every <main> wrapper must carry `flex:1 1 0%` (not `height:100%`).
These tests assert the required CSS is present and the banned pattern is absent.
They must stay green forever. If they go red, the map will be empty.

Tests also assert:
  - vis.js is inlined (no CDN)
  - the canvas container div is present
  - DOMContentLoaded listener is present (vis.Network init is deferred)
  - JS safety net (offsetHeight < 10 guard) is present
  - no height:100% on the canvas container (should use flex:1)
"""
from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.l3_map_shell import render_l3_map_html
from utils.combined_l2l3_shell import render_combined_l2l3_html
from utils.l3_map_shell_enhanced import render_l3_map_html_enhanced
from utils.topo_map_shell import OFFLINE_VIS_MISSING_SCRIPT

# ---------------------------------------------------------------------------
# Shared minimal payloads
# ---------------------------------------------------------------------------

MINIMAL_L3_PAYLOAD = {
    'nodes': [
        {'id': 'R1', 'label': 'R1', 'group': 'device', 'platform': 'cisco_ios'},
        {'id': 'R2', 'label': 'R2', 'group': 'device', 'platform': 'cisco_xe'},
        {'id': '10.0.0.0/24', 'label': '10.0.0.0/24', 'group': 'subnet'},
    ],
    'edges': [
        {'from': 'R1', 'to': 'R2', 'label': 'OSPF'},
        {'from': 'R1', 'to': '10.0.0.0/24'},
    ],
    'analysis': {'total_devices': 2, 'total_gateways': 0, 'total_subnets': 1},
    'devices': {
        'R1': {'platform': 'cisco_ios', 'route_count': 5, 'management_ip': '10.0.0.1'},
        'R2': {'platform': 'cisco_xe', 'route_count': 3, 'management_ip': '10.0.0.2'},
    },
    'gateway_analysis': {},
    'subnet_analysis': {'10.0.0.0/24': {'prefix_len': 24, 'is_private': True}},
    'all_routes': [],
    'failed_hosts': [],
    'route_count': 8,
}

MINIMAL_COMBINED_PAYLOAD = {
    'nodes': [
        {'id': 'SW1', 'label': 'SW1', 'group': 'device'},
        {'id': 'SW2', 'label': 'SW2', 'group': 'device'},
    ],
    'edges': [
        {'from': 'SW1', 'to': 'SW2', 'layer': 'l2', 'label': 'CDP'},
        {'from': 'SW1', 'to': 'SW2', 'layer': 'l3', 'label': 'OSPF'},
    ],
    'correlation': {},
    'analysis': {
        'total_nodes': 2, 'total_edges': 2,
        'l2_edge_count': 1, 'l3_edge_count': 1,
        'correlated_edges': 0, 'gateway_count': 0,
    },
}


# ---------------------------------------------------------------------------
# L3 map shell — render_l3_map_html
# ---------------------------------------------------------------------------

class TestL3MapContainerHeight:
    """render_l3_map_html must produce a map with a visible container."""

    @pytest.fixture(scope='class')
    def html(self):
        return render_l3_map_html(MINIMAL_L3_PAYLOAD, 'Test L3', 'regression', 'l3')

    def test_vis_js_is_inlined_not_cdn(self, html):
        """vis.js must be fully inlined — never a CDN script tag or fetch call."""
        assert OFFLINE_VIS_MISSING_SCRIPT not in html, \
            'vis.js is MISSING from modules/web/vis-network.min.js — map will be blank'
        assert 'unpkg.com' not in html.lower()
        assert 'cdn.jsdelivr' not in html.lower()
        assert 'cdnjs.cloudflare' not in html.lower()
        # visjs.github.io appears in the vis.js license comment header — that is fine.
        # What is NOT fine is a <script src="..."> or fetch() pointing at it.
        assert '<script src="https://visjs' not in html
        assert "fetch('https://visjs" not in html

    def test_canvas_container_div_present(self, html):
        """#l3-network div must exist — vis.Network needs it."""
        assert 'id="l3-network"' in html

    def test_domcontentloaded_deferred_init(self, html):
        """vis.Network init must be inside DOMContentLoaded — not inline."""
        assert 'DOMContentLoaded' in html

    def test_main_has_flex_1_rule(self, html):
        """main.l3-map-main must have flex:1 1 0% to propagate height."""
        assert 'main.l3-map-main' in html, \
            'CSS rule for main.l3-map-main is missing — container height will be 0'
        assert 'flex: 1 1 0%' in html, \
            'flex:1 1 0% missing — height:100% on canvas resolves to 0px'

    def test_main_has_overflow_hidden(self, html):
        """main.l3-map-main must clip overflow so vis.js canvas fills correctly."""
        # Find the CSS block for l3-map-main and check overflow
        idx = html.find('main.l3-map-main')
        assert idx != -1
        block = html[idx:idx + 200]
        assert 'overflow: hidden' in block or 'overflow:hidden' in block, \
            'main.l3-map-main missing overflow:hidden — scrollbar may collapse flex height'

    def test_canvas_uses_flex_not_percent_height(self, html):
        """#l3-network should use flex:1, NOT height:100% (height:100% fails when parent has no height)."""
        # The canvas should not use height:100% in the CSS rule
        # Find the #l3-network CSS block
        idx = html.find('#l3-network')
        assert idx != -1
        css_block = html[idx:idx + 150]
        assert 'height: 100%' not in css_block and 'height:100%' not in css_block, \
            '#l3-network uses height:100% — this fails when flex parent has no height. Use flex:1 instead.'

    def test_js_safety_net_present(self, html):
        """JS must guard against 0px container height at vis.Network init time."""
        assert 'offsetHeight < 10' in html, \
            'JS safety net missing — if CSS height chain breaks, map will be silently empty'
        assert '600px' in html  # fallback min-height value

    def test_nodes_json_embedded(self, html):
        """RAW_NODES must contain actual node data — not an empty array."""
        assert 'const RAW_NODES' in html
        assert '"id": "R1"' in html or '"id":"R1"' in html

    def test_flow_map_variant_also_works(self):
        """map_kind='flow' must produce the same container structure."""
        html = render_l3_map_html(MINIMAL_L3_PAYLOAD, 'Flow', 'regression', 'flow')
        assert 'id="l3-network"' in html
        assert 'main.l3-map-main' in html
        assert 'flex: 1 1 0%' in html
        assert 'Network Flow Map' in html


# ---------------------------------------------------------------------------
# Enhanced L3 map shell — render_l3_map_html_enhanced
# ---------------------------------------------------------------------------

class TestL3MapEnhancedContainerHeight:
    """render_l3_map_html_enhanced must have a complete flex height chain."""

    @pytest.fixture(scope='class')
    def html(self):
        return render_l3_map_html_enhanced(MINIMAL_L3_PAYLOAD, 'Enhanced Test', 'regression', 'l3')

    def test_vis_js_inlined(self, html):
        assert OFFLINE_VIS_MISSING_SCRIPT not in html, 'vis.js missing'
        assert 'unpkg.com' not in html.lower()

    def test_canvas_container_present(self, html):
        assert 'id="l3-network"' in html

    def test_main_has_flex_rule(self, html):
        """main element must propagate height via flex:1 1 0%."""
        assert 'flex: 1 1 0%' in html or 'flex:1 1 0%' in html, \
            'main element missing flex:1 1 0% — canvas will be 0px high'

    def test_main_has_overflow_hidden(self, html):
        assert 'overflow: hidden' in html or 'overflow:hidden' in html

    def test_tab_map_has_flex_1(self, html):
        """#tab-map is the direct parent of the canvas — must have flex:1."""
        idx = html.find('#tab-map')
        assert idx != -1
        # Look for flex:1 or flex: 1 near #tab-map CSS rule
        css_region = html[idx:idx + 200]
        assert 'flex: 1' in css_region or 'flex:1' in css_region, \
            '#tab-map missing flex:1 — map canvas has no height'

    def test_js_safety_net_present(self, html):
        assert 'offsetHeight < 10' in html, 'JS safety net missing in enhanced shell'

    def test_nodes_data_present(self, html):
        assert 'const RAW_NODES' in html
        assert 'R1' in html


# ---------------------------------------------------------------------------
# Combined L2+L3 map shell — render_combined_l2l3_html
# ---------------------------------------------------------------------------

class TestCombinedMapContainerHeight:
    """render_combined_l2l3_html must have a complete flex height chain."""

    @pytest.fixture(scope='class')
    def html(self):
        return render_combined_l2l3_html(MINIMAL_COMBINED_PAYLOAD, 'Combined Test', 'regression')

    def test_vis_js_inlined(self, html):
        assert OFFLINE_VIS_MISSING_SCRIPT not in html, 'vis.js missing in combined map'
        assert 'unpkg.com' not in html.lower()

    def test_canvas_container_present(self, html):
        assert 'id="combined-network"' in html

    def test_main_has_flex_rule(self, html):
        """main.combined-map-main must propagate height via flex:1 1 0%."""
        assert 'main.combined-map-main' in html, \
            'CSS rule for main.combined-map-main missing — canvas height will be 0'
        assert 'flex: 1 1 0%' in html, \
            'flex:1 1 0% missing in combined map — canvas will be 0px high'

    def test_canvas_uses_flex_not_percent_height(self, html):
        idx = html.find('#combined-network')
        assert idx != -1
        css_block = html[idx:idx + 150]
        assert 'height: 100%' not in css_block and 'height:100%' not in css_block, \
            '#combined-network uses height:100% — will fail when parent has no height'

    def test_js_safety_net_present(self, html):
        assert 'offsetHeight < 10' in html, 'JS safety net missing in combined map shell'

    def test_domcontentloaded_present(self, html):
        assert 'DOMContentLoaded' in html

    def test_nodes_data_present(self, html):
        assert 'const RAW_NODES' in html or 'SW1' in html


# ---------------------------------------------------------------------------
# Cross-shell: no banned CDN URLs in any map output
# ---------------------------------------------------------------------------

BANNED_CDN = [
    'unpkg.com',
    'cdn.jsdelivr.net',
    'cdnjs.cloudflare.com',
    'fonts.googleapis.com',
    'fonts.gstatic.com',
    'ajax.googleapis.com',
    'code.jquery.com',
    'maxcdn.bootstrapcdn.com',
    'stackpath.bootstrapcdn.com',
]


class TestNoCDNInAnyMap:
    """Every map shell must be free of CDN references — strict offline requirement."""

    def _check_no_cdn(self, html: str, label: str) -> None:
        for cdn in BANNED_CDN:
            assert cdn not in html, \
                f'{label}: banned CDN reference found: {cdn!r} — breaks offline/air-gap deployments'

    def test_l3_map_no_cdn(self):
        html = render_l3_map_html(MINIMAL_L3_PAYLOAD, 'CDN check', 'test', 'l3')
        self._check_no_cdn(html, 'l3_map_shell')

    def test_l3_map_enhanced_no_cdn(self):
        html = render_l3_map_html_enhanced(MINIMAL_L3_PAYLOAD, 'CDN check', 'test', 'l3')
        self._check_no_cdn(html, 'l3_map_shell_enhanced')

    def test_combined_map_no_cdn(self):
        html = render_combined_l2l3_html(MINIMAL_COMBINED_PAYLOAD, 'CDN check', 'test')
        self._check_no_cdn(html, 'combined_l2l3_shell')


# ---------------------------------------------------------------------------
# Minimum content: maps with no data must still render a usable shell
# ---------------------------------------------------------------------------

class TestEmptyPayloadShells:
    """Shells must not crash or produce malformed HTML on empty data."""

    EMPTY_L3 = {
        'nodes': [], 'edges': [], 'analysis': {},
        'devices': {}, 'gateway_analysis': {}, 'subnet_analysis': {},
        'all_routes': [], 'failed_hosts': [], 'route_count': 0,
    }
    EMPTY_COMBINED = {
        'nodes': [], 'edges': [], 'correlation': {},
        'analysis': {
            'total_nodes': 0, 'total_edges': 0,
            'l2_edge_count': 0, 'l3_edge_count': 0,
            'correlated_edges': 0, 'gateway_count': 0,
        },
    }

    def test_l3_shell_empty_payload(self):
        html = render_l3_map_html(self.EMPTY_L3, 'Empty', '', 'l3')
        assert '<!DOCTYPE html>' in html
        assert 'id="l3-network"' in html
        assert 'main.l3-map-main' in html
        assert 'const RAW_NODES    = []' in html or 'RAW_NODES' in html

    def test_l3_shell_enhanced_empty_payload(self):
        html = render_l3_map_html_enhanced(self.EMPTY_L3, 'Empty', '', 'l3')
        assert '<!DOCTYPE html>' in html
        assert 'id="l3-network"' in html

    def test_combined_shell_empty_payload(self):
        html = render_combined_l2l3_html(self.EMPTY_COMBINED, 'Empty', '')
        assert '<!DOCTYPE html>' in html
        assert 'id="combined-network"' in html
        assert 'main.combined-map-main' in html
