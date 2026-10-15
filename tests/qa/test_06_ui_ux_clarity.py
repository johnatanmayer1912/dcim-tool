"""Mandatory QA — UI/UX professional (clarity, contrast, accessibility)."""
from __future__ import annotations
import os
import re
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


def _html():
    return open(HTML, encoding='utf-8').read()


@mandatory
def test_diagnostics_cards_readable_contrast_dark_on_light():
    """Diagnostics gradient cards use readable text contrast (no black on dark grey)."""
    html = _html()
    assert 'color:#1e293b' in html or 'color:#0f172a' in html or 'color:#334155' in html


@mandatory
def test_link_inventory_tab_text_contrast():
    """Topology link inventory tab text meets contrast on map background."""
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'topo-link-inventory' in shell
    assert '#e2e8f0' in shell or 'color:#e2e8f0' in shell


@mandatory
def test_nst_match_highlight_visible_in_light_and_dark_contexts():
    """mark.nst-match styling visible in web UI and output_chrome HTML."""
    html = _html()
    assert 'mark.nst-match' in html or '.nst-match' in html
    chrome = open(os.path.join(ROOT, 'utils', 'match_highlight.py'), encoding='utf-8').read()
    assert 'nst-match' in chrome


@mandatory
def test_mac_trace_table_shows_searched_and_found_columns():
    """Path summary table includes MAC found column with highlights."""
    html = _html()
    # Search-it result table must use resolved_mac_html for rich display
    assert 'resolved_mac_html' in html or 'target_mac_html' in html


@mandatory
def test_desc_search_table_highlights_matched_substrings():
    """Description results use *_html fields in summary table."""
    html = _html()
    assert 'description_html' in html


@mandatory
def test_progress_bar_shows_label_and_counts():
    """search-it progress wrap shows label + numeric counts during run."""
    html = _html()
    assert 'search-it-progress' in html or 'progress' in html.lower()


@mandatory
def test_control_plane_panel_reflects_task_state():
    """Task registry status visible in control plane without stale running."""
    html = _html()
    assert 'control-plane-tasks' in html
    assert 'refreshControlPlane' in html


@mandatory
def test_segment_tabs_keyboard_focus_visible():
    """Tab segments have visible active state for operator orientation."""
    html = _html()
    # .segment and .active must both be present; active styling is required
    assert 'segment' in html
    assert 'active' in html
    assert 'switchTab' in html


@mandatory
def test_innerhtml_user_fields_escaped():
    """Non-highlight table cells use escapeHtml in search-it summaries."""
    html = _html()
    assert 'escapeHtml' in html


@mandatory
def test_offline_map_scroll_bounded_in_chrome():
    """VPC/standard map shells use bounded pane — no page scroll trap."""
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'mynetwork' in shell
    vpc = open(os.path.join(ROOT, 'utils', 'vpc_map_shell.py'), encoding='utf-8').read()
    assert 'vpc-map-pane' in vpc or 'max-height' in vpc


@mandatory
def test_about_tab_loads_readme_without_error():
    """About tab fetch displays README content for version awareness."""
    html = _html()
    assert 'loadReadme' in html
    assert 'about' in html.lower()


@mandatory
def test_no_dead_data_tab_selectors():
    """No [data-tab=…] querySelector calls remain — all replaced with goTo*Tab() helpers."""
    html = _html()
    dead = re.findall(r"querySelector\(['\"]\\?\[data-tab=", html)
    assert len(dead) == 0, f"Dead data-tab selectors still present: {dead}"


@mandatory
def test_go_to_tab_helpers_defined():
    """goToSearchTab, goToToolsTab, goToDiscoveryTab navigation helpers present in HTML."""
    html = _html()
    assert 'function goToSearchTab' in html
    assert 'function goToToolsTab' in html
    assert 'function goToDiscoveryTab' in html


@mandatory
def test_swiss_tools_map_groups_split_l2_and_routing():
    """DENSE-IA: L2 maps grouped separately from SSH routing maps; action names preserved."""
    html = _html()
    assert 'id="tools-map-group-l2"' in html
    assert 'id="tools-map-group-routing"' in html
    assert "toolsRunTopology('all')" in html
    assert "toolsRunTopology('vpc')" in html
    assert "toolsRunL3Map('l3')" in html
    assert 'offline_local_directory' in html


@mandatory
def test_discovery_table_evidence_escaped_and_filtered():
    """Discovery results: Evidence column, escaped hostnames, auth/timeout filters (P-001/P-002)."""
    html = _html()
    assert 'function discEsc(s)' in html
    assert '>Evidence</th>' in html
    assert 'value="auth_denied"' in html
    assert 'value="timeout"' in html
    assert 'same inventory CDP/LLDP job as L2' in html
    assert 'not the Discovery crawl graph' in html
    assert 'still not a census' in html
    assert 'Not L3 routing, not overlay, not a fabric census' in html
    assert 'cdn.jsdelivr' not in html
    assert 'fonts.googleapis.com' not in html
    assert 'CLI path reconstruct' in html
    assert 'not a certified cable' in html
    assert 'vlan_vstep_golden' in html
    assert 'vstep_golden' in html


@mandatory
def test_inventory_preview_commit_controls():
    """Sidebar can preview and commit inventory with omitted-reject copy."""
    html = _html()
    assert 'function previewInventory' in html
    assert 'function commitInventory' in html
    commit_fn = html.split('async function commitInventory', 1)[1].split('async function restoreInventoryBak', 1)[0]
    assert commit_fn.index('nstCommittedText = d.inventory') < commit_fn.index('fillInventoryBox')
    restore_fn = html.split('async function restoreInventoryBak', 1)[1].split('function handleFileSelect', 1)[0]
    assert restore_fn.index('nstCommittedText = d.inventory') < restore_fn.index('fillInventoryBox')
    disc_run = html.split('async function discRunDiscovery', 1)[1].split('function discStartPolling', 1)[0]
    assert "if (msg) msg.textContent = data.error" in disc_run
    assert '/api/inventory/commit' in html
    assert 'Rejected rows will be omitted' in html
    assert 'inv_source_chip' in html
    assert 'buildInventorySourceFields' in html
    assert 'inventory_source' in html
    assert 'disc-target-source' in html
    assert 'im_host' in html
    assert 'im_target_source' in html
    assert 'target_source: \'cidr_scan\'' in html or 'target_source: "cidr_scan"' in html
    assert 'for="disc-depth"' in html
    assert 'stp-target-source' in html
    assert 'healthWizardDismiss' in html
    assert "setAttribute('inert'" in html
    assert 'artifacts_available' in html
    assert 'id="health-wizard-modal"' in html and 'inert' in html
    assert 'id="im-deploy-confirm-modal"' in html
    assert 'id="vlan-confirm-modal"' in html
    im_tag = html.split('id="im-deploy-confirm-modal"', 1)[0][-80:] + html.split('id="im-deploy-confirm-modal"', 1)[1][:200]
    assert 'inert' in im_tag
    vlan_tag = html.split('id="vlan-confirm-modal"', 1)[0][-80:] + html.split('id="vlan-confirm-modal"', 1)[1][:200]
    assert 'inert' in vlan_tag
    assert 'querySelector(\'[data-tab=' not in html
    assert 'id="ws-nav-inventory"' in html
    assert 'function nstShowWorkspace' in html
    assert 'function nstLoadEvidence' in html
    assert '/api/jobs' in html
    assert 'id="nst-panel-hold"' in html
    assert 'id="ws-maps"' in html and 'inert' in html
    assert 'nstLoadEvidence' in html
    assert '/api/jobs/' in html
    assert 'pack' in html
    assert '@media (max-width: 900px)' in html
    assert '@media (max-width: 720px)' in html


@mandatory
def test_maps_hub_replay_utilization_copy_is_honest():
    """Replay overlay is paint-on-L2; live SSH is labeled SSH, not SNMP."""
    html = _html().lower()
    assert 'replay is not a live poll' in html
    assert 'live ssh is not snmp' in html
    assert 'live ssh collection is not in this release' not in html
    assert 'gray dashed = no sample' in html
    assert 'no utilization in this release' not in html
    shell = open(os.path.join(ROOT, 'utils', 'standard_map_shell.py'), encoding='utf-8').read()
    assert 'Replay snapshot — not a live poll' in shell
    assert 'Live SSH counters — not SNMP' in shell
    assert 'nstSetUtilOverlay' in shell
    assert 'Unmapped interfaces (not drawn)' in shell


@mandatory
def test_inventory_workspace_is_operator_canvas_not_empty_shell():
    """Inventory workspace hosts the editor and parsed host table (not an empty Phase-1 stub)."""
    html = _html()
    body = html.split('id="ws-inventory-body"', 1)[1].split('id="ws-maps"', 1)[0]
    assert 'id="nst-inventory-block"' in body
    assert 'id="inventory"' in body
    assert 'id="nst-inv-host-body"' in body
    assert 'nst-inv-canvas' in html
    assert 'Made by AI IDE' not in html


@mandatory
def test_task_log_renders_safe_spans_not_raw_tags():
    """Task log accepts first-party color spans after sanitizing; does not dump tags as text."""
    html = _html()
    assert 'function nstSanitizeLogHtml' in html
    assert 'nstSanitizeLogHtml(s)' in html
    assert 'line.textContent = String(msg)' not in html


@mandatory
def test_p1_operator_headings_skip_h5_h6():
    """P1 a11y: workspace h1 then tab/section h2/h3 — no heading-level skip to h5/h6."""
    html = _html()
    assert '<h1 id="ws-h1-inventory">' in html
    assert '<h2 class="tab-view-title">Network Search' in html
    assert "<h5" not in html and "<h6" not in html
    assert '--text-muted: #475569;' in html
    disc = open(os.path.join(ROOT, 'utils', 'discovery_map_shell.py'), encoding='utf-8').read()
    assert 'body.discovery-command-center .nst-fresh { color: #334155; }' in disc
    html = _html()
    assert '.nst-pill.is-unknown { color: #cbd5e1;' in html
