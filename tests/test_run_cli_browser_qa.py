"""Smoke checks for scripts/run_cli_browser_qa.py integration surface."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / 'scripts' / 'run_cli_browser_qa.py'
    spec = importlib.util.spec_from_file_location('run_cli_browser_qa', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_browser_qa_paths_exist():
    assert (ROOT / 'scripts' / 'run_cli_browser_qa.py').is_file()
    assert (ROOT / 'scripts' / 'cli_browser_qa_server.py').is_file()
    assert (ROOT / 'tests' / 'browser' / 'cli_credential_id.spec.mjs').is_file()
    assert (ROOT / 'tests' / 'browser' / 'package.json').is_file()
    assert (ROOT / 'tests' / 'browser' / 'package-lock.json').is_file()


def test_manifest_lists_cli_browser_suite():
    import yaml
    manifest = yaml.safe_load(
        (ROOT / 'tests' / 'qa' / 'MANDATORY_MANIFEST.yaml').read_text(encoding='utf-8')
    )
    suites = {s['id']: s for s in manifest['suites']}
    assert 'cli_browser_credential_id' in suites
    suite = suites['cli_browser_credential_id']
    assert suite['phase'] == 'pre_release'
    assert suite['blocking'] is True
    assert suite['command'][-1].endswith('run_cli_browser_qa.py')


def test_pick_port_respects_env(monkeypatch):
    mod = _load()
    monkeypatch.setenv('NST_CLI_BROWSER_QA_PORT', '51234')
    assert mod._pick_port() == 51234
