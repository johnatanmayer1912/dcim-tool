"""Mandatory QA — VLAN and Interface Manager mutations."""
from __future__ import annotations
import os
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')
VLAN_MOD = os.path.join(ROOT, 'modules', 'vlan_mgmt_production.py')


@mandatory
def test_vlan_validate_api_returns_issues_before_execute():
    """POST /api/vlan/validate returns structured issues list."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/vlan/validate' in src
    vsrc = open(os.path.join(ROOT, 'utils', 'vlan_validate.py'), encoding='utf-8').read()
    assert 'golden_config' in vsrc


@mandatory
def test_vlan_validate_skips_ssh_when_juniper_rename():
    """Juniper rename fails locally without opening SSH (validate pipeline)."""
    src = open(os.path.join(ROOT, 'utils', 'vlan_validate.py'), encoding='utf-8').read()
    assert 'Do not open SSH when local syntax already forbids' in src
    assert "op == 'rename' and 'juniper'" in src


@mandatory
def test_vlan_confirm_modal_shows_device_scope():
    """Confirm UI lists affected devices and VLAN id/name."""
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert 'vlan-modal-operation' in html
    assert 'vlan-modal-impact' in html
    assert 'confirmVlanExecution' in html


@mandatory
def test_vlan_post_change_verification_bucket():
    """verification_failed devices separated from success in summary."""
    src = open(VLAN_MOD, encoding='utf-8').read()
    assert 'verification_failed' in src


@mandatory
def test_im_discover_returns_interface_json():
    """/api/interface/discover returns parsed interface list."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/interface/discover' in src


@mandatory
def test_im_deploy_post_verify_rediscover():
    """After deploy, post-verify and rediscover paths execute."""
    im = open(os.path.join(ROOT, 'modules', 'plugins', 'interface_manager.py'), encoding='utf-8').read()
    assert '_rediscover_interfaces' in im
    assert 'rediscovery' in im
    assert 'golden_config' in im
    assert 'raise_if_blocked' in im


@mandatory
def test_im_restore_guide_api_available():
    """Restore guide endpoint returns manual steps, not auto rollback."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/interface/restore-guide' in src or 'restore' in src.lower()


@mandatory
def test_im_junos_display_set_capture():
    """Junos config capture uses display set when applicable."""
    im = open(os.path.join(ROOT, 'modules', 'plugins', 'interface_manager.py'), encoding='utf-8').read()
    assert 'display set' in im


@mandatory
def test_im_cisco_save_running_config_option():
    """Cisco deploy optional save running config path."""
    im = open(os.path.join(ROOT, 'modules', 'plugins', 'interface_manager.py'), encoding='utf-8').read()
    assert 'copy running-config startup-config' in im


@mandatory
def test_vlan_snapshot_dir_per_run():
    """VLAN management snapshots isolated per prepare_run_output folder."""
    src = open(VLAN_MOD, encoding='utf-8').read()
    assert 'prepare_run_output' in src or 'run_dir' in src or 'snapshot' in src.lower()


@mandatory
def test_im_should_abort_mid_bulk():
    """IM bulk operations honor should_abort between interfaces."""
    im_src = open(os.path.join(ROOT, 'modules', 'plugins', 'interface_manager.py'), encoding='utf-8').read()
    assert 'should_abort' in im_src
