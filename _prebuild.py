"""
_prebuild.py
------------
MANDATORY pre-build validation gate.
Run this before every PyInstaller build. If it fails, abort the build.

Checks:
  1. Syntax check all core Python files
  2. Plugin load test (9+ plugins, 0 errors)
  3. CLI smoke test (mock SSH server — proves CLI terminal works)
  4. VERSION file check
  5. restore_backup removed (safety check)
"""
import sys
import os
import ast

sys.path.insert(0, '.')

print("=" * 60)
print("PRE-BUILD VALIDATION")
print("=" * 60)

all_ok = True

# ── 1. Syntax check ───────────────────────────────────────────────────────────
print("\n[1] Syntax check...")
files = [
    'main.py', 'vlan_checker_web.py',
    'modules/cli_manager.py', 'modules/network_base.py',
    'modules/adapters.py', 'modules/topology_mapper.py', 'modules/description_search.py',
    'modules/plugin_registry.py', 'modules/vlan_mgmt_production.py',
    'modules/network_audit.py', 'modules/config_backup.py',
    'modules/save_config.py', 'modules/vlan_compare.py',
    'modules/plugins/standards_validator.py',
    'utils/report_formatter.py', 'utils/vpc_board_formatter.py', 'utils/vpc_map_shell.py',
    'utils/discovery_map_formatter.py',     'utils/discovery_map_shell.py',
    'utils/standard_map_shell.py',
    'utils/cisco_iface.py',
    'utils/utilization_overlay/__init__.py',
    'utils/utilization_overlay/model.py',
    'utils/utilization_overlay/join.py',
    'utils/utilization_overlay/paint.py',
    'utils/utilization_overlay/rates.py',
    'utils/utilization_overlay/cli_parse.py',
    'utils/utilization_overlay/ssh_collector.py',
    'utils/utilization_overlay/discovery_host.py',
    'utils/discovery_program_status.py',
    'utils/evidence_inspector.py',
    'utils/topo_map_shell.py',
    'utils/map_acceptance.py',
    'utils/discovery_acceptance.py',
    'utils/discovery_schema.py',
    'utils/lacp_oper.py',
    'modules/overlay_collector.py',
    'utils/cable_witness.py',
    'utils/optics_dom.py',
    'utils/link_issues.py',
    'utils/golden_config_gate.py',
    'modules/path_trace.py',
    'modules/routing_analyzer/path_tracer.py',
    'utils/asset_warranty_consolidator.py',
    'modules/inventory_store.py',
    'utils/discovery_profiles.py',
    'utils/output_chrome.py',
    'utils/discovery_graph.py',
    'utils/mac_trace_formatter.py', 'utils/mac_utils.py', 'utils/juniper_iface.py',
    'utils/output_paths.py', 'utils/search_report_output.py', 'modules/mac_trace.py',
    'utils/description_search_formatter.py', 'utils/ping_scan_formatter.py',
    'utils/search_it_progress.py', 'utils/task_control_plane.py', 'utils/job_index.py', 'utils/job_source.py', 'utils/parallel_device_pool.py', 'utils/vlan_validate.py',
    'utils/api_security.py', 'utils/restore_guide.py', 'utils/vlan_mgmt_formatter.py',
    'utils/missing_vlan_formatter.py',     'utils/search_relevance.py',
    'utils/match_highlight.py',
    'utils/session_cred_cache.py',
    'utils/vault_credentials.py',
    'utils/task_credentials.py',
    'utils/interface_manager_formatter.py',
    'utils/stp_map_formatter.py',
    'modules/plugins/network_discovery.py',
    'modules/stp_swiss_runner.py', 'utils/config_backup_system.py',
    'utils/structured_logger.py', 'utils/app_logger.py', 'utils/operator_console_logs.py',
]
for f in files:
    try:
        ast.parse(open(f, encoding='utf-8').read())
        print(f'  OK  {f}')
    except SyntaxError as e:
        print(f'  SYN {f}:{e.lineno} {e.msg}')
        all_ok = False

# ── 2. Plugin load test ───────────────────────────────────────────────────────
print("\n[2] Plugin load test...")
from modules.plugin_registry import PluginRegistry
PluginRegistry._instance = None
PluginRegistry._initialized = False
r = PluginRegistry()
count = len(r.get_all_metadata())
errors = r.get_errors()
if count >= 9 and len(errors) == 0:
    print(f'  OK  {count} plugins loaded, 0 errors')
else:
    print(f'  FAIL {count} plugins, {len(errors)} errors')
    for e in errors:
        print(f'       {e["file"]}: {e["error"]}')
    all_ok = False

# ── 3. CLI smoke test (MANDATORY) ─────────────────────────────────────────────
print("\n[3] CLI smoke test (MANDATORY — proves CLI terminal works)...")
try:
    from tests.test_cli_smoke import run_cli_smoke_test
    result = run_cli_smoke_test()
    if result["passed"]:
        passed = sum(1 for s in result["steps"] if s["status"] == "PASS")
        print(f'  OK  CLI smoke test: {passed}/{len(result["steps"])} steps passed')
    else:
        print(f'  FAIL CLI smoke test: {result["error"]}')
        print('  *** CLI terminal will be stuck on "Connecting" in the browser ***')
        print('  *** DO NOT BUILD until this passes ***')
        all_ok = False
except Exception as e:
    print(f'  FAIL CLI smoke test crashed: {e}')
    import traceback
    traceback.print_exc()
    all_ok = False

# ── 4. VERSION check ──────────────────────────────────────────────────────────
print("\n[4] VERSION check...")
ver = open('VERSION', encoding='utf-8').read().strip()
print(f'  OK  VERSION: {ver}')

# ── 5. Safety: restore_backup removed ────────────────────────────────────────
print("\n[5] Safety checks...")
for f in ['utils/config_backup_system.py', 'modules/vlan_mgmt_production.py', 'vlan_checker_web.py']:
    content = open(f, encoding='utf-8').read()
    if 'restore_backup' in content or 'rollback_vlan_change' in content:
        print(f'  FAIL {f} still contains dangerous restore/rollback code')
        all_ok = False
    else:
        print(f'  OK  {f}')

# ── 6. Discovery hostname + map contract ─────────────────────────────────────
print("\n[6] Discovery v6.9.28 contract...")
try:
    from modules.network_base import resolve_device_hostname, _hostname_from_ver_output
    import pathlib
    fx = pathlib.Path('tests/fixtures/discovery/nxos_show_version.txt').read_text(encoding='utf-8')
    hn = _hostname_from_ver_output(fx, 'cisco_nxos')
    if hn == 'n9k-core-01':
        print('  OK  NX-OS hostname parse from show version fixture')
    else:
        print(f'  FAIL NX-OS hostname parse (got {hn!r})')
        all_ok = False
    from utils.discovery_map_formatter import generate_discovery_html
    import tempfile
    td = tempfile.mkdtemp()
    hp = os.path.join(td, 't.html')
    nodes = [
        {'id': 'a', 'ip': '1.1.1.1', 'platform': 'x', 'depth': 0, 'is_scanned': True, 'scan_state': 'scanned'},
        {'id': 'b', 'ip': '2.2.2.2', 'depth': 1, 'scan_state': 'neighbor_only'},
    ]
    edges = [{'from': 'a', 'to': 'b', 'f_port': 'e1', 't_port': 'e2', 'protocol': 'CDP'}]
    generate_discovery_html(hp, nodes, edges)
    ht = open(hp, encoding='utf-8').read()
    if 'discovery-command-center' in ht and '__DISCOVERY__' in ht:
        print('  OK  discovery Command Center HTML contract')
    else:
        print('  FAIL discovery map HTML contract')
        all_ok = False
except Exception as e:
    print(f'  FAIL Discovery contract: {e}')
    all_ok = False

# ── 6b. Discovery v7.0.1 trust (classifier + dedup) ───────────────────────────
print("\n[6b] Discovery v7.0.1 trust contract...")
try:
    import subprocess
    for script in (
        'tests/test_discovery_platform_classifier.py',
        'tests/test_discovery_graph_dedup.py',
        'tests/test_lab_smoke_offline.py',
        'tests/test_topology_parallel_edges.py',
        'tests/test_standard_map_v7049.py',
        'tests/test_topology_trust.py',
        'tests/test_nxos_vpc_parse.py',
    ):
        r = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode == 0:
            print(f'  OK  {script}')
        else:
            print(f'  FAIL {script}')
            print(r.stdout[-500:] if r.stdout else r.stderr[-500:])
            all_ok = False
    from utils.discovery_graph import classify_os_family
    if classify_os_family('Nexus 7010') == 'cisco_nxos':
        print('  OK  BUG-0007 Nexus platform is NX-OS not JunOS')
    else:
        print('  FAIL BUG-0007 Nexus misclassified')
        all_ok = False
except Exception as e:
    print(f'  FAIL Discovery v7.0.1 trust: {e}')
    all_ok = False

# ── 6c. Health wizard v7.0.2 ───────────────────────────────────────────────────
print("\n[6c] Health check runner v7.0.2...")
try:
    import subprocess
    r = subprocess.run(
        [sys.executable, 'tests/test_health_check_runner.py'],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode == 0:
        print('  OK  tests/test_health_check_runner.py')
    else:
        print('  FAIL tests/test_health_check_runner.py')
        print(r.stdout[-500:] if r.stdout else r.stderr[-500:])
        all_ok = False
    from utils.health_check_runner import run_health_checks
    q = run_health_checks(quick=True, full=False, include_cli=False)
    if q.get('ok') and len(q.get('checks', [])) == 3:
        print('  OK  quick health returns 3 checks')
    else:
        print('  FAIL quick health contract')
        all_ok = False
except Exception as e:
    print(f'  FAIL Health v7.0.2: {e}')
    all_ok = False

# ── 6d. Frozen plugin bootstrap (NEW-C1) ─────────────────────────────────────
print("\n[6d] Frozen plugin bootstrap (NEW-C1)...")
try:
    import subprocess
    r = subprocess.run(
        [sys.executable, 'scripts/audit_frozen_plugin_sim.py'],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode == 0:
        print('  OK  scripts/audit_frozen_plugin_sim.py')
    else:
        print('  FAIL scripts/audit_frozen_plugin_sim.py')
        print(r.stdout[-500:] if r.stdout else r.stderr[-500:])
        all_ok = False
except Exception as e:
    print(f'  FAIL Frozen plugin bootstrap: {e}')
    all_ok = False

# ── 6e. Junos LLDP + VPC HTML contract (v7.0.3) ──────────────────────────────
print("\n[6e] VPC map HTML contract + output chrome...")
try:
    import subprocess
    for tname in (
        'tests/test_vpc_map_html_contract.py',
        'tests/test_output_chrome.py',
        'tests/test_description_search_progress.py',
        'tests/test_session_cred_cache.py',
        'tests/test_match_highlight.py',
        'tests/test_mac_trace_formatter.py',
    ):
        r = subprocess.run(
            [sys.executable, tname],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if r.returncode == 0:
            print(f'  OK  {tname}')
        else:
            print(f'  FAIL {tname}')
            print(r.stdout[-800:] if r.stdout else r.stderr[-800:])
            all_ok = False
except Exception as e:
    print(f'  FAIL output contract: {e}')
    all_ok = False

# ── 6f. vpc_map_shell import ───────────────────────────────────────────────────
print("\n[6f] vpc_map_shell module...")
try:
    from utils import vpc_map_shell as vms
    assert callable(vms.vpc_command_center_tabs_html)
    assert callable(vms.vpc_shell_js)
    print('  OK  utils.vpc_map_shell')
except Exception as e:
    print(f'  FAIL vpc_map_shell: {e}')
    all_ok = False

# ── 6g. discovery map HTML contract (v7.0.4) ───────────────────────────────────
print("\n[6g] Discovery Command Center contract...")
try:
    import subprocess
    r = subprocess.run(
        [sys.executable, 'tests/test_discovery_map_html_contract.py'],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if r.returncode == 0:
        print('  OK  tests/test_discovery_map_html_contract.py')
    else:
        print('  FAIL tests/test_discovery_map_html_contract.py')
        print(r.stdout[-800:] if r.stdout else r.stderr[-800:])
        all_ok = False
except Exception as e:
    print(f'  FAIL Discovery contract: {e}')
    all_ok = False

# ── 6h. VPC nodes have x,y (v7.0.4) ────────────────────────────────────────────
print("\n[6h] VPC fixed positions contract...")
try:
    from modules.adapters import _ensure_vpc_nodes_positioned
    nn = [{'id': 'A'}, {'id': 'B'}]
    ee = [{'from': 'A', 'to': 'B'}]
    _ensure_vpc_nodes_positioned(nn, ee)
    if all(n.get('x') is not None and n.get('y') is not None for n in nn):
        print('  OK  _ensure_vpc_nodes_positioned assigns x,y')
    else:
        print('  FAIL VPC position fallback')
        all_ok = False
except Exception as e:
    print(f'  FAIL VPC positions: {e}')
    all_ok = False

# ── 7. policies/ directory exists ────────────────────────────────────────────
print("\n[7] policies/ directory check...")
if os.path.exists('policies/standards.yaml'):
    print('  OK  policies/standards.yaml exists')
else:
    print('  FAIL policies/standards.yaml missing — Standards Validator will use built-in fallback')
    # Not a build blocker, just a warning

# ── 8. mandatory QA manifest integrity ───────────────────────────────────────
print("\n[8] mandatory QA manifest...")
try:
    import subprocess
    r = subprocess.run(
        [sys.executable, 'scripts/validate_mandatory_qa_manifest.py'],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode == 0:
        print('  OK  tests/qa/MANDATORY_MANIFEST.yaml')
    else:
        print('  FAIL mandatory QA manifest validation')
        print(r.stdout[-800:] if r.stdout else r.stderr[-800:])
        all_ok = False
except Exception as e:
    print(f'  FAIL mandatory QA manifest: {e}')
    all_ok = False

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
if all_ok:
    print("RESULT: ALL CHECKS PASSED — READY TO BUILD")
else:
    print("RESULT: CHECKS FAILED — DO NOT BUILD")
print("=" * 60)
sys.exit(0 if all_ok else 1)
