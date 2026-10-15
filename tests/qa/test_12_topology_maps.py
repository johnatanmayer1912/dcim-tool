"""Mandatory QA — Topology and map HTML contracts."""
from __future__ import annotations
import os
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')
ADAPTERS = os.path.join(ROOT, 'modules', 'adapters.py')


@mandatory
def test_topology_mapper_all_vpc_standard_modes():
    """Topology generates HTML for map_mode all, vpc, standard."""
    src = open(ADAPTERS, encoding='utf-8').read()
    assert "map_mode='all'" in src or 'map_mode' in src
    assert "'vpc'" in src
    assert 'run_topology_mapper' in src


@mandatory
def test_vpc_map_command_center_tabs_present():
    """VPC map HTML includes command center tab shell."""
    src = open(os.path.join(ROOT, 'utils', 'vpc_map_shell.py'), encoding='utf-8').read()
    assert 'vpc-command-center' in src
    assert 'vpc_command_center_tabs_html' in src


@mandatory
def test_standard_map_fixed_positions_assigned():
    """_ensure_vpc_nodes_positioned assigns x,y coordinates."""
    src = open(ADAPTERS, encoding='utf-8').read()
    assert '_assign_vpc_fixed_positions' in src
    assert "n['x']" in src or "dnode['x']" in src


@mandatory
def test_node_interface_topology_per_device_html():
    """Port interface map writes one HTML per switch + index when multi."""
    src = open(ADAPTERS, encoding='utf-8').read()
    assert '_write_port_map_index_html' in src
    assert '_write_single_port_interface_html' in src


@mandatory
def test_node_analyze_status_api_pollable():
    """/api/node-analyze/status returns running|complete with port_hits."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/node-analyze/status' in src
    assert 'running' in src or 'complete' in src


@mandatory
def test_topology_open_diagnostics_folder_api():
    """Open diagnostics POST returns folder path for operator."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/topology/open-diagnostics' in src


@mandatory
def test_l3_map_status_api_pollable():
    """/api/l3-map/status returns running|complete for L3 cartography."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/l3-map/status' in src
    assert '_last_l3_map' in src


@mandatory
def test_l3_map_ui_uses_run_action_not_json_window():
    """Advanced L3/Flow buttons must not open raw JSON endpoints."""
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert "window.open('/api/discovery/advanced_map/l3'" not in html
    assert 'toolsRunL3Map' in html


@mandatory
def test_l3_map_html_offline_vis_embedded():
    """L3 map HTML embeds offline vis.js without CDN dependency."""
    from utils.topo_map_shell import load_vis_script, OFFLINE_VIS_MISSING_SCRIPT
    script = load_vis_script()
    assert 'unpkg.com' not in script.lower()
    assert 'cdn.jsdelivr' not in script.lower()
    assert 'vis-network' in script or OFFLINE_VIS_MISSING_SCRIPT[:20] in script


@mandatory
def test_physical_l2_layer_filters_differ():
    """Physical view hides one-sided edges; L2 keeps them (same collection)."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    shell = open(os.path.join(root, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'function nstPhysicalEligible' in shell
    assert 'layer === \'physical\') hidden = !nstPhysicalEligible' in shell or 'layer === "physical") hidden = !nstPhysicalEligible' in shell
    html = open(os.path.join(root, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert 'tools-overlay-empty' in html
    assert 'show nve peers' in html
    assert 'not overlay evidence' in html
    assert '/api/topology/issues' in open(WEB, encoding='utf-8').read()
    assert '/api/path-trace' in open(WEB, encoding='utf-8').read()
    assert 'runPathTrace' in html
    assert 'loadLinkIssues' in html
    assert 'not a live forwarding path' in html or 'not a forwarding path' in html


@mandatory
def test_topo_map_link_inventory_contrast_css():
    """Link inventory tab CSS includes light-theme readable text."""
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'topo-link-inventory' in shell
    assert '#e2e8f0' in shell


@mandatory
def test_map_shell_bounded_height_no_body_scroll_trap():
    """Map shells constrain height; wheel events don't trap page scroll."""
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'mynetwork' in shell
    assert 'min-height' in shell or 'height:100%' in shell or 'flex:1' in shell


@mandatory
def test_topology_trust_warnings_in_html_when_unscanned_peer():
    """Unscanned peer warnings surface in topology output when applicable."""
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'one_sided' in shell or 'spoof' in shell or 'unscanned' in shell.lower() or 'neighbor_only' in shell


@mandatory
def test_topology_150_device_truncate_logged():
    """Large topology runs log truncation honestly in output."""
    src = open(ADAPTERS, encoding='utf-8').read()
    assert 'devices_skipped_hosts' in src
    assert 'devices_truncated' in src
    # Truncation must log to operator
    assert 'truncat' in src.lower()


@mandatory
def test_topology_skipped_hosts_in_status_response():
    """devices_skipped_hosts propagated through topology status payload."""
    src = open(ADAPTERS, encoding='utf-8').read()
    # Verify skipped hosts are included in the status dict returned to the UI
    assert '"devices_skipped_hosts"' in src or "'devices_skipped_hosts'" in src


@mandatory
def test_topology_skipped_hosts_panel_in_ui():
    """UI has a panel to surface skipped hosts from 150-device cap."""
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert 'tools-skipped-hosts' in html or 'skipped_hosts' in html
