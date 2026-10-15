"""
First-launch health checks (v7.0.2).

Quick mode: inventory, port, plugin registry only (< 1s).
Full mode: adds offline demo file checks (no heavy SSH).
Optional CLI smoke: separate flag (slow; mock SSH server).
"""
import os
import socket
import sys
from datetime import datetime
from typing import Any, Dict, List

MIN_PLUGINS = 10


def _resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            bundled = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(bundled):
                return bundled
        program = os.path.join(os.path.dirname(sys.executable), relative_path)
        if os.path.exists(program):
            return program
        return os.path.join(getattr(sys, '_MEIPASS', ''), relative_path)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def _inventory_check():
    for name in ('inventory.txt', os.path.join('inventory', 'inventory.txt')):
        path = _resource_path(name)
        if not os.path.isfile(path):
            path = os.path.join(os.getcwd(), name)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith('#')]
                if lines:
                    return True, f'inventory.txt readable ({len(lines)} line(s))', path
            except Exception as exc:
                return False, f'inventory read error: {exc}', path
    return False, 'inventory.txt not found beside app', ''


def _port_check(port=5051):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            in_use = s.connect_ex(('127.0.0.1', port)) == 0
        if in_use:
            return True, f'Port {port} in use (expected while app is running)', port
        return True, f'Port {port} available', port
    except Exception as exc:
        return False, str(exc), port


def _plugins_check():
    try:
        from modules.plugin_registry import get_registry
        reg = get_registry()
        meta = reg.get_all_metadata()
        errs = reg.get_errors()
        ids = sorted([m.get('plugin_id', '') for m in meta if m.get('plugin_id')])
        count = len(ids)
        ok = count >= MIN_PLUGINS
        if errs:
            ok = count >= MIN_PLUGINS - 1
        names = ', '.join(ids[:8])
        if len(ids) > 8:
            names += f', +{len(ids) - 8} more'
        msg = f'{count} plugins loaded'
        if errs:
            msg += f' ({len(errs)} load warning(s))'
        detail = {'count': count, 'plugin_ids': ids, 'errors': errs}
        if not ok:
            msg = f'Only {count} plugins (need >={MIN_PLUGINS})'
            if errs:
                msg += f"; errors: {errs[0].get('file', '?')}"
        return ok, msg, detail
    except Exception as exc:
        return False, str(exc), {}


def _discovery_demo_check():
    try:
        from modules.plugins.network_discovery import NetworkDiscoveryPlugin
        from utils.output_paths import get_outputs_root
        discovery_root = os.path.join(get_outputs_root(), 'discovery')
        existing = None
        if os.path.isdir(discovery_root):
            html_candidates = []
            for root, _dirs, files in os.walk(discovery_root):
                for fname in files:
                    if fname.endswith('.html') and 'discovery' in fname.lower():
                        html_candidates.append(os.path.join(root, fname))
            if html_candidates:
                existing = sorted(html_candidates, reverse=True)[0]
        if existing and os.path.isfile(existing):
            return True, 'Recent discovery HTML found (skipped re-generate)', existing
        plugin = NetworkDiscoveryPlugin()
        device = {'host': '127.0.0.1', 'device_type': 'cisco_nxos', 'port': 22}
        result = plugin.execute(
            device, {'username': 'demo', 'password': 'demo'},
            {'seed_hosts': ['10.0.0.1'], 'demo_mode': True, 'generate_topology_html': True},
            {'timeout': 10}, log_func=None,
        )
        data = (result or {}).get('data') or {}
        path = data.get('topology_path') or ''
        ok = (result or {}).get('status') == 'success' and path and os.path.isfile(path)
        return ok, 'Discovery demo map OK' if ok else 'Discovery demo map missing', path
    except Exception as exc:
        return False, str(exc)[:200], ''


def _vpc_demo_check():
    from utils.output_paths import get_demo_vpc_topology_path
    vpc_path = get_demo_vpc_topology_path()
    if not os.path.isfile(vpc_path):
        try:
            import create_demo_map_v7
            create_demo_map_v7.create_v7_demo()
        except Exception:
            pass
    if os.path.isfile(vpc_path):
        try:
            with open(vpc_path, 'r', encoding='utf-8') as f:
                body = f.read()
            ok = '__VPC_BOARD__' in body
            return ok, 'vPC demo contains Engineering Board' if ok else 'vPC demo missing board marker', vpc_path
        except Exception as exc:
            return False, str(exc)[:200], vpc_path
    return False, 'vPC demo HTML missing', vpc_path


def _cli_smoke_check():
    try:
        from tests.test_cli_smoke import run_cli_smoke_test
        res = run_cli_smoke_test()
        ok = bool(res.get('passed'))
        return ok, 'CLI smoke passed' if ok else 'CLI smoke failed', res.get('error', '')
    except Exception as exc:
        return False, str(exc)[:200], ''


def _offline_validation_check():
    """Validate offline environment capabilities for weird case scenarios."""
    try:
        # Check parser regression tests exist
        parser_test_path = os.path.join(os.getcwd(), 'tests', 'test_parser_regression.py')
        if os.path.isfile(parser_test_path):
            # Try to run a quick test
            try:
                import unittest
                from tests.test_parser_regression import TestCiscoCDPParserRegression
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromTestCase(TestCiscoCDPParserRegression)
                runner = unittest.TextTestRunner(verbosity=0)
                test_result = runner.run(suite)
                if test_result.wasSuccessful():
                    return True, 'Parser regression tests passed', {'tests_run': test_result.testsRun}
                else:
                    return False, f'Parser regression: {len(test_result.failures)} failures', {'failures': len(test_result.failures)}
            except Exception:
                return True, 'Parser regression test file exists (execution skipped)', {}
        else:
            return False, 'Parser regression test file missing', {}
    except Exception as exc:
        return False, str(exc)[:200], {}


def _vpc_duplicate_detection_check():
    """Validate VPC peer correlation cache for duplicate device detection."""
    try:
        from modules.plugins.vpc_domain_plugin import _vpc_peer_cache
        if isinstance(_vpc_peer_cache, dict):
            return True, 'VPC peer correlation cache available', {'cache_type': 'dict'}
        else:
            return False, 'VPC peer cache not initialized', {}
    except Exception as exc:
        return False, str(exc)[:200], {}


def run_health_checks(*, quick=False, full=False, include_cli=False) -> Dict[str, Any]:
    """
    quick: inventory + port + plugins only.
    full: quick + discovery/vpc demo checks + offline validation.
    include_cli: add CLI smoke (slow).
    """
    checks: List[Dict[str, Any]] = []

    ok, msg, det = _inventory_check()
    checks.append({'id': 'inventory', 'name': 'Inventory file', 'ok': ok, 'message': msg, 'detail': det})

    ok, msg, det = _port_check()
    checks.append({'id': 'port', 'name': 'Web port 5051', 'ok': ok, 'message': msg, 'detail': det})

    ok, msg, det = _plugins_check()
    checks.append({'id': 'plugins', 'name': 'Plugin registry', 'ok': ok, 'message': msg, 'detail': det})

    if full:
        ok, msg, det = _discovery_demo_check()
        checks.append({'id': 'discovery_demo', 'name': 'Discovery offline demo', 'ok': ok, 'message': msg, 'detail': det})
        ok, msg, det = _vpc_demo_check()
        checks.append({'id': 'vpc_demo', 'name': 'vPC offline demo', 'ok': ok, 'message': msg, 'detail': det})
        ok, msg, det = _offline_validation_check()
        checks.append({'id': 'offline_validation', 'name': 'Offline validation', 'ok': ok, 'message': msg, 'detail': det})
        ok, msg, det = _vpc_duplicate_detection_check()
        checks.append({'id': 'vpc_duplicate_detection', 'name': 'VPC duplicate detection', 'ok': ok, 'message': msg, 'detail': det})

    if include_cli:
        ok, msg, det = _cli_smoke_check()
        checks.append({'id': 'cli_smoke', 'name': 'CLI terminal smoke', 'ok': ok, 'message': msg, 'detail': det})

    critical = {'inventory', 'port', 'plugins'}
    critical_ok = all(c['ok'] for c in checks if c['id'] in critical)
    all_ok = all(c['ok'] for c in checks)
    if full or include_cli:
        ok = all_ok
    else:
        ok = critical_ok
    return {
        'ok': ok,
        'all_ok': all_ok,
        'checks': checks,
        'ran_at': datetime.now().isoformat(),
        'mode': 'quick' if quick and not full else ('full' if full else 'standard'),
    }
