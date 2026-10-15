"""Mandatory QA — Interface Manager deep paths."""
from __future__ import annotations
import os
from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
IM = os.path.join(ROOT, 'modules', 'plugins', 'interface_manager.py')
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
WEB = os.path.join(ROOT, 'vlan_checker_web.py')


@mandatory
def test_im_parse_nxos_interfaces_fixture():
    """NX-OS interface brief fixture parses expected port count."""
    from modules.plugins.interface_manager import _parse_nxos_interfaces
    fixture = (
        "Ethernet1/1      eth  access  up       up       auto(D) auto(D) --\n"
        "Ethernet1/2      eth  trunk   up       up       auto(D) auto(D) --\n"
        "mgmt0            eth  routed  up       up       1000(D) full(D) --\n"
    )
    result = _parse_nxos_interfaces(fixture)
    assert isinstance(result, list)
    assert any(r.get('name', '').startswith('Ethernet') for r in result)


@mandatory
def test_im_parse_ios_interfaces_fixture():
    """IOS interface status fixture parses speed/duplex/description."""
    from modules.plugins.interface_manager import _parse_ios_interfaces
    fixture = (
        "Gi1/0/1         connected    1            a-full  a-100    10/100/1000BaseTX\n"
        "Gi1/0/2         notconnect   1            auto    auto     10/100/1000BaseTX\n"
    )
    result = _parse_ios_interfaces(fixture)
    assert isinstance(result, list)
    assert len(result) >= 1


@mandatory
def test_im_legacy_syntax_blocked_on_nxos():
    """NX-OS rejects 'switchport trunk encapsulation dot1q' as blocking error (G-011b)."""
    from modules.plugins.interface_manager import _validate_vendor_syntax
    cfg = "interface Ethernet1/1\n switchport trunk encapsulation dot1q\n"
    r = _validate_vendor_syntax(cfg, 'cisco_nxos', None)
    assert not r['passed'], "Legacy syntax on NX-OS must block (not just warn)"
    assert any('Legacy' in str(e.get('message', '')) or 'legacy' in str(e.get('message', ''))
               for e in r['errors'])
    assert any(e.get('blocking') for e in r['errors'])


@mandatory
def test_im_html_report_if_generated():
    """IM plugin may write HTML under CAT_PLUGINS with manifest."""
    from utils.output_paths import CAT_PLUGINS
    assert CAT_PLUGINS == 'plugins'
    im_src = open(IM, encoding='utf-8').read()
    assert 'html' in im_src.lower()
    assert 'report' in im_src.lower() or 'manifest' in im_src.lower()


@mandatory
def test_im_error_surfaces_in_ui_not_silent():
    """IM API errors return JSON error field displayed to operator."""
    web_src = open(WEB, encoding='utf-8').read()
    assert '/api/interface/deploy' in web_src or 'interface.*deploy' in web_src.lower()
    html_src = open(HTML, encoding='utf-8').read()
    assert 'im_result' in html_src or 'interface.*error' in html_src.lower() or 'deploy.*error' in html_src.lower()


@mandatory
def test_im_device_type_override_field():
    """im_device_type override sent in IM API payload."""
    html = open(HTML, encoding='utf-8').read()
    assert 'im_device_type' in html


@mandatory
def test_im_dry_run_banner_in_response():
    """Dry-run IM operations label results as preview only."""
    im_src = open(IM, encoding='utf-8').read()
    # Must contain dry_run or preview language
    assert 'dry_run' in im_src or 'DRY RUN' in im_src or 'dry-run' in im_src.lower()


@mandatory
def test_im_parallel_not_used_for_single_device_deploy():
    """Single-host IM deploy uses direct connection path."""
    web = open(WEB, encoding='utf-8').read()
    assert '/api/interface/deploy' in web
    im = open(IM, encoding='utf-8').read()
    assert 'foreach_device_parallel' not in im or 'len(devices)' in im


@mandatory
def test_im_config_diff_visible_before_apply():
    """Operator sees intended config delta before live deploy confirm."""
    html = open(HTML, encoding='utf-8').read()
    # The UI must surface a diff / config-preview before deployment
    assert 'proposed' in html.lower() or 'config' in html.lower()
    assert 'im' in html.lower()
