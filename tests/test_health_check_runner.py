"""Health check runner tests (v7.0.2)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.health_check_runner import run_health_checks, MIN_PLUGINS


def test_quick_health_no_cli():
    result = run_health_checks(quick=True, full=False, include_cli=False)
    assert 'checks' in result
    ids = {c['id'] for c in result['checks']}
    assert 'inventory' in ids
    assert 'port' in ids
    assert 'plugins' in ids
    assert 'cli_smoke' not in ids
    assert 'discovery_demo' not in ids
    plugins = next(c for c in result['checks'] if c['id'] == 'plugins')
    assert plugins['detail']['count'] >= MIN_PLUGINS
    assert len(plugins['detail']['plugin_ids']) >= MIN_PLUGINS


def test_full_adds_demos():
    result = run_health_checks(quick=True, full=True, include_cli=False)
    ids = {c['id'] for c in result['checks']}
    assert 'discovery_demo' in ids
    assert 'vpc_demo' in ids


if __name__ == '__main__':
    test_quick_health_no_cli()
    test_full_adds_demos()
    print('OK health_check_runner')
