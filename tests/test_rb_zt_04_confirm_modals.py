"""RB-ZT-04: mutation confirm dialogs first-paint inert + keyboard lifecycle."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


def _html():
    return open(HTML, encoding='utf-8').read()


def _modal_open_tag(html: str, modal_id: str) -> str:
    key = f'id="{modal_id}"'
    i = html.index(key)
    start = html.rfind('<div', 0, i)
    end = html.find('>', i)
    return html[start:end + 1]


def test_im_and_vlan_confirm_modals_inert_when_closed():
    html = _html()
    for mid in ('im-deploy-confirm-modal', 'vlan-confirm-modal'):
        tag = _modal_open_tag(html, mid)
        assert 'hidden' in tag, mid
        assert 'inert' in tag, mid
        assert 'role="dialog"' in tag, mid
        assert 'aria-labelledby' in tag, mid
        # Closed tree uses hidden+inert. Do not stack aria-hidden + tabindex on the same node
        # (axe aria-prohibited-attr incomplete on first paint).
        assert 'tabindex' not in tag, mid
        assert 'aria-hidden' not in tag, mid
    assert 'function nstSetDialogOpen' in html
    assert "nstSetDialogOpen(document.getElementById('im-deploy-confirm-modal'), true)" in html
    assert "nstSetDialogOpen(document.getElementById('vlan-confirm-modal'), true)" in html
    assert "nstSetDialogOpen(document.getElementById('im-deploy-confirm-modal'), false)" in html
    assert "nstSetDialogOpen(document.getElementById('vlan-confirm-modal'), false)" in html
    src = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
    assert 'plugin_upload_is_enabled' in src
    assert 'Runtime plugin upload is disabled' in src or 'PLUGIN_UPLOAD_DISABLED' in src


def test_dialog_helpers_trap_focus_and_escape():
    html = _html()
    assert 'function nstBindDialogA11y' in html
    assert 'function nstDialogFocusable' in html
    assert "ev.key === 'Escape'" in html
    assert "ev.key !== 'Tab'" in html
    assert 'window.nstDialogA11yBound' in html
    assert 'if (window.nstDialogA11yBound) return' in html
    assert 'nstDialogTrigger' in html
    assert 'trigger.focus' in html
    assert "pair = ['im-deploy-confirm-modal', 'vlan-confirm-modal'" in html
    assert 'health-wizard-modal' in html
    assert 'nstBindDialogA11y();' in html
    bind = html.split('function nstBindKeyboard', 1)[1].split('function toolsSetMapLayer', 1)[0]
    assert 'if (window.nstActiveDialog) return' in bind


def test_cancel_and_confirm_close_dialogs():
    html = _html()
    assert 'function closeImDeployConfirmModal' in html
    assert 'function closeVlanConfirmModal' in html
    assert 'onclick="closeImDeployConfirmModal()"' in html
    assert 'onclick="closeVlanConfirmModal()"' in html
    im_close = html.split('function closeImDeployConfirmModal', 1)[1].split('function validateImDeployConsent', 1)[0]
    assert 'nstSetDialogOpen' in im_close
    assert 'false' in im_close
    vlan_close = html.split('function closeVlanConfirmModal', 1)[1].split('function validateVlanDeployConsent', 1)[0]
    assert 'nstSetDialogOpen' in vlan_close
    assert 'false' in vlan_close
    confirm_im = html.split('function confirmImDeployExecution', 1)[1][:800]
    assert 'closeImDeployConfirmModal' in confirm_im
    confirm_vlan = html.split('function confirmVlanExecution', 1)[1][:600]
    assert 'closeVlanConfirmModal' in confirm_vlan
