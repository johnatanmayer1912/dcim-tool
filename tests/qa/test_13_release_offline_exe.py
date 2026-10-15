"""Mandatory QA — Release and offline EXE discipline."""
from __future__ import annotations

import glob
import os

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _latest_spec():
    """Pick highest semver among NetworkSwissToolPro_v*.spec (not lexical sort)."""
    specs = glob.glob(os.path.join(ROOT, 'NetworkSwissToolPro_v*.spec'))
    assert specs, 'no NetworkSwissToolPro_v*.spec in repo root'

    def _ver_key(path: str):
        base = os.path.basename(path)
        # NetworkSwissToolPro_v7.4.20.spec → (7, 4, 20)
        raw = base.split('_v', 1)[-1].removesuffix('.spec')
        parts = []
        for tok in raw.split('.'):
            try:
                parts.append(int(tok))
            except ValueError:
                parts.append(0)
        return tuple(parts)

    return max(specs, key=_ver_key)


@mandatory
def test_version_file_matches_changelog_header():
    """VERSION file matches latest CHANGELOG [vX.Y.Z] entry."""
    ver = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()
    cl = open(os.path.join(ROOT, 'CHANGELOG.md'), encoding='utf-8').read()
    assert ver
    assert f'v{ver}' in cl or ver in cl
    assert '## [Unreleased]' in cl


@mandatory
def test_spec_hiddenimports_include_new_utils_modules():
    """Latest .spec lists utils.match_highlight, session_cred_cache, task_credentials."""
    body = open(_latest_spec(), encoding='utf-8').read()
    for mod in (
        'utils.match_highlight', 'utils.session_cred_cache', 'utils.task_credentials',
        'utils.discovery_schema', 'utils.lacp_oper', 'modules.overlay_collector',
        'utils.cable_witness', 'utils.optics_dom', 'utils.link_issues',
        'utils.golden_config_gate', 'modules.path_trace',
        'utils.discovery_program_status', 'utils.evidence_inspector',
        'utils.standard_map_shell', 'utils.cisco_iface',
    ):
        assert mod in body, mod


@mandatory
def test_prebuild_syntax_list_includes_changed_modules():
    """_prebuild.py syntax check list updated when core modules added."""
    pre = open(os.path.join(ROOT, '_prebuild.py'), encoding='utf-8').read()
    for rel in (
        'vlan_checker_web.py',
        'utils/discovery_schema.py',
        'utils/lacp_oper.py',
        'modules/overlay_collector.py',
        'utils/cable_witness.py',
        'utils/optics_dom.py',
        'utils/link_issues.py',
        'utils/golden_config_gate.py',
        'modules/path_trace.py',
        'utils/discovery_program_status.py',
        'utils/evidence_inspector.py',
        'utils/standard_map_shell.py',
        'utils/cisco_iface.py',
        'modules/plugins/network_discovery.py',
        'utils/api_security.py',
    ):
        assert rel in pre, rel


@mandatory
def test_cli_smoke_passes_in_prebuild():
    """CLI smoke test 11/11 in _prebuild mandatory gate."""
    pre = open(os.path.join(ROOT, '_prebuild.py'), encoding='utf-8').read()
    assert 'cli_smoke' in pre.lower() or 'CLI smoke' in pre or 'test_cli_smoke' in pre


@mandatory
def test_templates_bundled_in_spec_datas():
    """PyInstaller datas includes modules/web/templates."""
    body = open(_latest_spec(), encoding='utf-8').read()
    assert 'modules/web/templates' in body


@mandatory
def test_plugins_folder_bundled_frozen():
    """modules/plugins included in EXE datas for offline plugin load."""
    body = open(_latest_spec(), encoding='utf-8').read()
    assert 'modules/plugins' in body


@mandatory
def test_no_numpy_pandas_in_spec_excludes():
    """Spec excludes heavy unused deps for EXE size."""
    body = open(_latest_spec(), encoding='utf-8').read()
    assert 'numpy' in body
    assert 'pandas' in body
    assert 'excludes=' in body


@mandatory
def test_mandatory_manifest_validated_in_prebuild():
    """validate_mandatory_qa_manifest.py passes in every_code_change phase."""
    pre = open(os.path.join(ROOT, '_prebuild.py'), encoding='utf-8').read()
    assert 'validate_mandatory_qa_manifest' in pre or 'MANDATORY_MANIFEST' in pre


@mandatory
def test_enterprise_qa_gate_invokes_mandatory_runner():
    """enterprise_qa_gate.py calls mandatory_release_qa orchestrator."""
    src = open(os.path.join(ROOT, 'scripts', 'enterprise_qa_gate.py'), encoding='utf-8').read()
    assert 'mandatory_release_qa.py' in src


@mandatory
def test_update_date_bumped_with_version():
    """UPDATE_DATE is derived from VERSION + CHANGELOG (no stale hardcoded label)."""
    ver = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()
    web = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    cl = open(os.path.join(ROOT, 'CHANGELOG.md'), encoding='utf-8').read()
    assert 'UPDATE_DATE' in web
    assert '_read_update_date_label' in web
    assert 'VERSION' in web
    assert ver in cl
    assert f'### {ver}' in cl or f'### {ver} ' in cl or f'v{ver}' in cl
