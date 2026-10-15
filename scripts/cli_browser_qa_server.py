#!/usr/bin/env python3
"""Local CLI browser QA server — credential_id contract with mocked device SSH.

Usage (from repo root, prefer the wrapper):
  python3 scripts/run_cli_browser_qa.py

Direct (advanced):
  NST_CLI_BROWSER_QA_PORT=5051 BROWSER=/usr/bin/true python3 scripts/cli_browser_qa_server.py

Binds 127.0.0.1:<port>. Seeds vault credential_id=netops. Does not open a browser.
Does not talk to live Cisco/Juniper devices — create_cli_session is mocked.
"""
from __future__ import annotations

import os
import sys
import tempfile
import webbrowser
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA = Path(tempfile.mkdtemp(prefix='nst-cli-browser-qa-'))
os.environ['NST_DATA_DIR'] = str(DATA)
os.environ['NST_BIND'] = '127.0.0.1'
os.environ['BROWSER'] = os.environ.get('BROWSER', '/usr/bin/true')

PORT = int((os.environ.get('NST_CLI_BROWSER_QA_PORT') or '5051').strip() or '5051')

# Isolated inventory under NST_DATA_DIR — never rewrite the repo inventory.txt
inv = DATA / 'inventory.txt'
inv.write_text('# browser QA inventory\n10.0.0.1,cisco_ios,lab\n', encoding='utf-8')
os.environ['NST_INVENTORY_PATH'] = str(inv)

SECRET = 'browser-qa-vault-secret-never-in-dom'
READY_MARKER = DATA / 'ready.marker'


def _fake_create_cli_session(session_id, device, user, pwd, enb_pwd,
                             log_callback=None, data_callback=None):
    if pwd != SECRET:
        raise AssertionError('mock SSH expected vault-resolved password')
    cli = MagicMock()
    cli.connected = True
    cli.hostname = 'MOCK-SW1'
    cli.session_id = session_id
    cli.credential_id = ''
    cli.write = MagicMock()
    cli.resize_pty = MagicMock()
    from modules import cli_manager as cmgr
    with cmgr._session_lock:
        cmgr._cli_sessions[session_id] = cli
    if data_callback:
        try:
            data_callback(b'MOCK-SW1# ')
        except Exception:
            pass
    return cli


def main():
    webbrowser.open = lambda *a, **k: False

    # Device TCP probe must not require a live host; keep loopback sockets real for Socket.IO.
    import socket as _socket
    _RealSocket = _socket.socket

    class _QaSocket(_RealSocket):
        def connect_ex(self, address):
            host = address[0] if isinstance(address, (tuple, list)) else address
            if host in ('127.0.0.1', '::1', 'localhost'):
                return super().connect_ex(address)
            return 0

    _socket.socket = _QaSocket

    import vlan_checker_web as web
    from modules.credential_manager import CredentialManager

    cred_dir = DATA / 'credentials'
    cred_dir.mkdir(parents=True, exist_ok=True)
    cm = CredentialManager(storage_dir=str(cred_dir))
    cm.add_credential('netops', SECRET, admin_password='en1', label='Lab QA')
    web.credential_manager = cm

    # Handlers closed over imported name — patch both module and web binding
    import modules.cli_manager as cmgr
    cmgr.create_cli_session = _fake_create_cli_session
    web.create_cli_session = _fake_create_cli_session

    READY_MARKER.write_text(f'{DATA}\nport={PORT}\n', encoding='utf-8')
    print(f'[cli-browser-qa] data={DATA}', flush=True)
    print(f'[cli-browser-qa] credential_id=netops (password never for browser)', flush=True)
    print(f'[cli-browser-qa] listening http://127.0.0.1:{PORT}/cli_terminal', flush=True)

    if not web.SOCKETIO_AVAILABLE or web.socketio is None:
        print('[cli-browser-qa] FATAL: Socket.IO unavailable', flush=True)
        sys.exit(2)

    web.socketio.run(
        web.app,
        host='127.0.0.1',
        port=PORT,
        allow_unsafe_werkzeug=True,
        log_output=False,
    )


if __name__ == '__main__':
    main()
