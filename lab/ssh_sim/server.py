#!/usr/bin/env python3
"""Minimal Paramiko SSH lab server for Cisco asset collection QA.

Binds 127.0.0.1 ports 2201-2204 by default. Accepts any username/password.

  python lab/ssh_sim/server.py
  python lab/ssh_sim/server.py --port 2201 --device ios12
"""
from __future__ import annotations

import argparse
import socket
import sys
import threading

try:
    import paramiko
except ImportError as exc:  # pragma: no cover
    raise SystemExit('paramiko required (install netmiko requirements)') from exc

_ROOT = __file__.replace('\\', '/').rsplit('/', 2)[0]
if _ROOT.endswith('/lab'):
    _ROOT = _ROOT.rsplit('/', 1)[0]
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lab.ssh_sim.handler import LAB_DEVICES, device_for_port, handle_command


class _LabServerInterface(paramiko.ServerInterface):
    def __init__(self, device_key: str):
        self.device_key = device_key
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_exec_request(self, channel, command):
        # Allow one-shot exec for quick probes; shell path is primary for Netmiko.
        self.event.set()
        return True


def _serve_client(client, addr, device_key: str):
    transport = None
    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(paramiko.RSAKey.generate(2048))
        server = _LabServerInterface(device_key)
        transport.start_server(server=server)
        channel = transport.accept(20)
        if channel is None or not server.event.wait(10):
            return
        meta = LAB_DEVICES[device_key]
        prompt = meta.get('prompt', '> ')
        # Banner + prompt (Netmiko finds prompt before sending terminal width/length).
        channel.send(f"\r\n{prompt}".encode('utf-8'))
        buf = b''
        while transport.is_active():
            data = channel.recv(1024)
            if not data:
                break
            buf += data
            if b'\n' not in buf and b'\r' not in buf:
                continue
            # Normalize CR/LF; strip ANSI/control noise Netmiko may send.
            raw = buf.decode('utf-8', errors='replace')
            buf = b''
            line = (
                raw.replace('\r\n', '\n')
                .replace('\r', '\n')
                .split('\n', 1)[0]
                .strip()
            )
            # Drop Telnet/SSH IAC-ish control chars that sometimes prefix lines.
            line = ''.join(ch for ch in line if ch.isprintable() or ch in '\t')
            line = line.strip()
            if not line:
                channel.send(prompt.encode('utf-8'))
                continue
            # CRITICAL: echo the command. Netmiko set_terminal_width / length
            # uses read_until_pattern on the command string itself.
            channel.send(f"{line}\r\n".encode('utf-8'))
            output = handle_command(device_key, line)
            if output and not output.endswith('\n'):
                output += '\n'
            channel.send((output + prompt).encode('utf-8'))
    finally:
        if transport:
            transport.close()
        client.close()


def run_server(host: str, port: int, device_key: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(32)
    print(f'Lab SSH sim listening on {host}:{port} device={device_key}', flush=True)
    while True:
        client, addr = sock.accept()
        key = device_key or device_for_port(port) or 'ios12'
        threading.Thread(target=_serve_client, args=(client, addr, key), daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description='NST Cisco SSH lab simulator')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=2201)
    parser.add_argument('--device', default='', help='ios12|ios17|nxos7|nxos9')
    args = parser.parse_args()
    device_key = args.device or device_for_port(args.port) or 'ios12'
    if device_key not in LAB_DEVICES:
        raise SystemExit(f'Unknown device {device_key!r}')
    run_server(args.host, args.port, device_key)


if __name__ == '__main__':
    main()
