"""v7.4.30 — Standard L2 HTML contracts + fail-closed credential_id."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_standard_l2_omits_legacy_side_panel_and_collapses_honesty():
    import sys

    sys.path.insert(0, str(ROOT))
    from utils.report_formatter import generate_topology_html

    p = Path(tempfile.mkdtemp()) / 'std.html'
    generate_topology_html(
        str(p),
        2,
        1,
        json.dumps([{'id': 'a', 'label': 'LEAF1'}, {'id': 'b', 'label': 'ACCESS1'}]),
        json.dumps([{'from': 'a', 'to': 'b', 'label': 'Eth1/1'}]),
        '',
        map_mode='all',
    )
    t = p.read_text(encoding='utf-8')
    assert 'nst-standard-map' in t
    assert 'id="side-panel"' not in t
    assert '<details class="nst-program-status-banner"' in t
    assert 'Map honesty' in t
    assert '#00c2d7' in t
    assert '<title>Standard L2 Map</title>' in t


def test_execute_requires_body_credential_id_no_session_fallback():
    from utils.vault_credentials import CredentialResolveError, resolve_execute_credentials

    class _CM:
        def is_master_password_required(self):
            return False

        def get_credential(self, cid):
            return {'username': cid, 'password': 'x', 'admin_password': '', 'label': cid}

        def record_use(self, cid):
            return None

    try:
        resolve_execute_credentials(
            {'credential_id': '', 'action': 'connectivity'},
            _CM(),
            {'credential_id': 'lab-admin'},
            credential_id_required=True,
        )
        raise AssertionError('expected CredentialResolveError')
    except CredentialResolveError as exc:
        assert 'credential_id required' in str(exc).lower()


def test_ssh_sim_echo_and_terminal_prep():
    from lab.ssh_sim.handler import handle_command

    assert handle_command('ios_access', 'terminal width 511') == ''
    assert 'C9300' in handle_command('ios_access', 'show inventory')
