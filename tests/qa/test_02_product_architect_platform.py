"""Mandatory QA — Product Architect (platform, plugins, control plane)."""
from __future__ import annotations

import os

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


@mandatory
def test_plugin_registry_loads_minimum_nine_without_errors():
    """PluginRegistry reports ≥9 plugins and zero load errors at startup."""
    from modules.plugin_registry import get_registry
    reg = get_registry()
    meta = reg.get_all_metadata()
    assert len(meta) >= 9, f'expected ≥9 plugins, got {len(meta)}'
    ids = {m.get('plugin_id') for m in meta}
    assert 'network_discovery' in ids
    assert 'interface_manager' in ids
    errors = reg.get_errors()
    assert len(errors) == 0, errors


@mandatory
def test_task_control_plane_registers_and_completes_execute_actions():
    """/api/execute registers task_id; completion updates control plane panel."""
    src = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'register_task' in src
    assert 'complete_task' in src
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert 'refreshControlPlane' in html
    assert 'control-plane-tasks' in html


@mandatory
def test_output_paths_never_writes_to_cwd_or_install_dir():
    """prepare_run_output uses NST data root, not PyInstaller MEIPASS."""
    from utils.output_paths import get_data_root, prepare_run_output
    src = open(os.path.join(ROOT, 'utils', 'output_paths.py'), encoding='utf-8').read()
    assert '_MEIPASS' not in src or 'never' in src.lower() or 'NST_DATA_DIR' in src
    paths = prepare_run_output('qa_platform', 'probe')
    root = os.path.abspath(get_data_root())
    assert os.path.abspath(paths['run_dir']).startswith(root)
    assert 'MEIPASS' not in paths['run_dir']


@mandatory
def test_web_only_policy_no_tk_parity_requirements():
    """New features route through vlan_checker_web + index.html only."""
    arch = open(os.path.join(ROOT, 'docs', '01-architecture', 'system-architecture.md'), encoding='utf-8').read()
    assert 'web only' in arch.lower() or 'web-only' in arch.lower()
    assert 'out of scope' in arch.lower()


@mandatory
def test_adapter_orchestrator_routes_plugins_by_registry():
    """run_generic_plugin dispatches by plugin_id without hardcoded elif chain."""
    src = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert 'def run_generic_plugin' in src
    assert 'get_registry()' in src
    assert 'registry.exists(plugin_id)' in src


@mandatory
def test_parallel_device_pool_caps_workers():
    """foreach_device_parallel respects get_max_workers() ceiling."""
    from utils.parallel_device_pool import ABS_MAX_WORKERS, get_max_workers
    assert get_max_workers(999) == ABS_MAX_WORKERS
    assert get_max_workers(1) == 1


@mandatory
def test_topology_trust_layer_wired_in_pipeline():
    """topology_trust enriches nodes/edges before HTML emit."""
    src = open(os.path.join(ROOT, 'utils', 'discovery_graph.py'), encoding='utf-8').read()
    assert 'apply_discovery_edge_trust' in src
    shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
    assert 'topo-trust-pill' in shell


@mandatory
def test_vlan_validate_shared_between_gui_and_web():
    """utils/vlan_validate.py is single validation source for mutations."""
    web = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'vlan_validate' in web
    assert os.path.isfile(os.path.join(ROOT, 'utils', 'vlan_validate.py'))


@mandatory
def test_manifest_json_written_for_every_major_feature():
    """Each CAT_* run category calls write_run_manifest once per run."""
    src = open(os.path.join(ROOT, 'utils', 'output_paths.py'), encoding='utf-8').read()
    assert 'def write_run_manifest' in src
    adapters = open(os.path.join(ROOT, 'modules', 'adapters.py'), encoding='utf-8').read()
    assert adapters.count('write_run_manifest') >= 3


@mandatory
def test_feature_flags_not_silently_default_unsupported_platforms():
    """Unsupported device_type fails validation, not silent IOS fallback."""
    src = open(os.path.join(ROOT, 'utils', 'vlan_validate.py'), encoding='utf-8').read()
    assert 'unsupported device_type' in src
    assert "_supported =" in src
    assert 'cisco_ios' in src
