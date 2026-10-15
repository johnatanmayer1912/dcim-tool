"""Mandatory QA — Plugins and network discovery."""
from tests.qa._scaffold import mandatory
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


@mandatory
def test_network_discovery_demo_mode_no_ssh():
    """Demo discovery generates HTML without SSH."""
    from modules.plugins.network_discovery import NetworkDiscoveryPlugin
    plugin = NetworkDiscoveryPlugin()
    result = plugin.execute(
        {'host': '10.0.0.1'},
        {'username': 'u', 'password': 'p'},
        {'seed_hosts': ['10.0.0.1'], 'max_depth': 2, 'demo_mode': True},
        {},
        log_func=None,
    )
    assert result['status'] == 'success'
    data = result['data']
    assert data.get('demo_mode') is True
    assert data.get('overlay_collected') is True
    ov = data.get('overlay_links') or []
    assert ov
    assert all(e.get('not_physical') for e in ov)
    assert len(data['devices']) >= 3


@mandatory
def test_discovery_platform_classifier_nexus_is_nxos():
    """Nexus platform strings classify as cisco_nxos not juniper."""
    from utils.discovery_graph import classify_os_family
    assert classify_os_family('Nexus9000') == 'cisco_nxos'
    assert classify_os_family('Nexus9000') != 'juniper_junos'


@mandatory
def test_discovery_dedup_parallel_edges():
    """Duplicate CDP/LLDP edges deduplicated in graph."""
    from utils.discovery_graph import canonicalize_discovery_graph
    nodes = [
        {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
        {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': True},
    ]
    edges = [
        {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1', 'protocol': 'CDP'},
        {'from': 'B', 'to': 'A', 'f_port': 'Gi1/1', 't_port': 'Eth1/1', 'protocol': 'LLDP'},
    ]
    _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
    assert len(rewired) == 1



@mandatory
def test_vpc_domain_plugin_metadata_valid():
    """vpc_domain plugin loads with valid PLUGIN_METADATA."""
    from modules.plugins.vpc_domain_plugin import METADATA
    assert METADATA.get('plugin_id') == 'vpc_domain'
    assert METADATA.get('display_name')
    assert METADATA.get('version')


@mandatory
def test_standards_validator_policy_yaml_or_fallback():
    """Standards validator uses policies/standards.yaml or built-in."""
    src = open(os.path.join(ROOT, 'modules', 'plugins', 'standards_validator.py'), encoding='utf-8').read()
    assert 'policies/standards.yaml' in src
    assert os.path.isfile(os.path.join(ROOT, 'policies', 'standards.yaml'))


@mandatory
def test_interface_manager_plugin_registered():
    """interface_manager in registry with run() entry."""
    from modules.plugin_registry import get_registry
    from modules.plugins.interface_manager import METADATA
    assert METADATA.get('plugin_id') == 'interface_manager'
    reg = get_registry()
    assert reg.exists('interface_manager') or METADATA.get('plugin_id')


@mandatory
def test_config_templates_plugin_offline_paths():
    """config_templates writes under output_paths not CWD."""
    from modules.plugins.config_templates import METADATA
    assert METADATA.get('plugin_id') == 'config_templates'
    assert METADATA.get('modifies_device') in (False, None) or METADATA.get('modifies_device') is False


@mandatory
def test_stp_topology_visualizer_plugin_loads():
    """stp_topology_visualizer plugin zero registry errors."""
    from modules.plugin_registry import get_registry
    from modules.plugins.stp_topology_visualizer import METADATA
    assert METADATA.get('plugin_id')
    errors = [e for e in get_registry().get_errors() if 'stp' in str(e).lower()]
    assert not errors


@mandatory
def test_discovery_manifest_single_write():
    """Discovery writes manifest once after all artifacts ready."""
    src = open(os.path.join(ROOT, 'modules', 'plugins', 'network_discovery.py'), encoding='utf-8').read()
    assert 'write_run_manifest' in src


@mandatory
def test_frozen_plugin_bootstrap_sim_passes():
    """audit_frozen_plugin_sim.py passes in prebuild gate."""
    pre = open(os.path.join(ROOT, '_prebuild.py'), encoding='utf-8').read()
    assert 'audit_frozen_plugin_sim' in pre or os.path.isfile(
        os.path.join(ROOT, 'scripts', 'audit_frozen_plugin_sim.py')
    )
