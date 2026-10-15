"""
tests/test_cli_smoke.py
-----------------------
CLI Connectivity Smoke Test — MANDATORY before every build.

PURPOSE:
    Prove that the CLI terminal connection flow works end-to-end using a
    mock SSH server. This test MUST pass before any EXE is built.

    Tests the EXACT same code path the browser uses:
        1. CLIConnection.__init__()
        2. CLIConnection.connect() → _do_connect()
        3. ShellReader starts and forwards data
        4. data_callback receives the device prompt
        5. log_callback receives progress messages
        6. write() sends keystrokes
        7. disconnect() cleans up

    No real network device required.

HOW TO RUN:
    python tests/test_cli_smoke.py

INTEGRATION WITH BUILD:
    Called by _prebuild.py before every PyInstaller build.
    If it fails, the build is aborted.

FAILURE MEANS:
    The CLI terminal will be stuck on "Connecting" in the browser.
    DO NOT BUILD until this test passes.
"""

import sys
import os
import threading
import time
import socket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import telnetlib  # noqa
except ImportError:
    try:
        import telnetlib_compat  # noqa
    except ImportError:
        pass

MOCK_PORT = 2299
MOCK_HOST = "127.0.0.1"
MOCK_USER = "testuser"
MOCK_PASS = "testpass"
MOCK_PROMPT = b"MOCK-SWITCH-01#"


# ── Mock SSH Server ───────────────────────────────────────────────────────────

class MockSSHServer(threading.Thread):
    """
    Minimal paramiko SSH server that simulates a Cisco IOS device.
    Accepts password auth, opens a shell, sends a prompt, echoes input.

    Uses listen(5) so the TCP probe in the test does NOT consume the
    real client connection — the server accepts multiple connections.
    """

    def __init__(self, port=MOCK_PORT):
        super().__init__(daemon=True)
        self.port = port
        self.server_ready = threading.Event()
        self.error = None
        self._server_sock = None
        self._stop = threading.Event()

    def run(self):
        try:
            import paramiko

            host_key = paramiko.RSAKey.generate(2048)

            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((MOCK_HOST, self.port))
            self._server_sock.listen(5)   # backlog=5 so TCP probe doesn't block real client
            self._server_sock.settimeout(15)

            self.server_ready.set()

            # Accept connections until stopped
            while not self._stop.is_set():
                try:
                    conn, addr = self._server_sock.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                # Handle each connection in its own thread
                t = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, host_key),
                    daemon=True
                )
                t.start()

        except Exception as e:
            self.error = str(e)
        finally:
            if self._server_sock:
                try:
                    self._server_sock.close()
                except Exception:
                    pass

    def _handle_connection(self, conn, host_key):
        """Handle a single SSH client connection."""
        try:
            import paramiko

            transport = paramiko.Transport(conn)
            transport.add_server_key(host_key)

            class _Handler(paramiko.ServerInterface):
                def check_channel_request(self, kind, chanid):
                    return (paramiko.OPEN_SUCCEEDED if kind == 'session'
                            else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED)

                def check_auth_password(self, username, password):
                    return (paramiko.AUTH_SUCCESSFUL
                            if username == MOCK_USER and password == MOCK_PASS
                            else paramiko.AUTH_FAILED)

                def check_channel_shell_request(self, channel):
                    return True

                def check_channel_pty_request(self, channel, term, width,
                                               height, pixelwidth, pixelheight, modes):
                    return True

                def get_allowed_auths(self, username):
                    return 'password'

            transport.start_server(server=_Handler())

            chan = transport.accept(timeout=10)
            if chan is None:
                return

            # Send device prompt after a brief pause
            time.sleep(0.05)
            chan.send(MOCK_PROMPT)

            # Echo loop for 10 seconds
            deadline = time.time() + 10
            while time.time() < deadline:
                if chan.recv_ready():
                    data = chan.recv(256)
                    if data:
                        chan.send(data)
                time.sleep(0.01)

            chan.close()
            transport.close()

        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def stop(self):
        self._stop.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass


# ── Test runner ───────────────────────────────────────────────────────────────

def run_cli_smoke_test() -> dict:
    """
    Run the CLI smoke test. Returns result dict with passed/steps/error.
    """
    steps = []
    overall_passed = True

    def record(step_name, passed, detail=""):
        nonlocal overall_passed
        status = "PASS" if passed else "FAIL"
        steps.append({"step": step_name, "status": status, "detail": detail})
        if not passed:
            overall_passed = False
        print(f"  [{status}] {step_name}" + (f" — {detail}" if detail else ""))

    print()
    print("=" * 60)
    print("CLI SMOKE TEST")
    print("=" * 60)

    # ── Step 1: Import paramiko ───────────────────────────────────────────────
    try:
        import paramiko
        record("paramiko import", True, f"v{paramiko.__version__}")
    except ImportError as e:
        record("paramiko import", False, str(e))
        return {"passed": False, "steps": steps, "error": "paramiko not available"}

    # ── Step 2: Import CLIConnection ─────────────────────────────────────────
    try:
        from modules.cli_manager import CLIConnection
        record("cli_manager import", True)
    except Exception as e:
        record("cli_manager import", False, str(e))
        return {"passed": False, "steps": steps, "error": str(e)}

    # ── Step 3: Start mock SSH server ─────────────────────────────────────────
    # Suppress paramiko's transport-level stderr noise from the TCP probe
    import logging as _logging
    _logging.getLogger("paramiko.transport").setLevel(_logging.CRITICAL)

    server = MockSSHServer(port=MOCK_PORT)
    server.start()
    if not server.server_ready.wait(timeout=5):
        record("mock SSH server start", False, "Server did not become ready in 5s")
        return {"passed": False, "steps": steps, "error": "Mock server failed to start"}
    record("mock SSH server start", True, f"Listening on {MOCK_HOST}:{MOCK_PORT}")

    # ── Step 4: TCP probe (separate from real SSH connection) ─────────────────
    # This just checks the port is open. The server handles multiple connections
    # so this does NOT consume the real client's connection slot.
    try:
        with socket.create_connection((MOCK_HOST, MOCK_PORT), timeout=3):
            pass
        record("TCP probe to mock server", True)
    except Exception as e:
        record("TCP probe to mock server", False, str(e))
        server.stop()
        return {"passed": False, "steps": steps, "error": str(e)}

    # ── Step 5: CLIConnection.connect() ──────────────────────────────────────
    progress_messages = []
    data_received = []

    def log_cb(msg):
        progress_messages.append(msg)

    def data_cb(data):
        data_received.append(data)

    device = {
        "host"       : MOCK_HOST,
        "port"       : MOCK_PORT,
        "device_type": "cisco_ios",
    }

    cli = CLIConnection(
        session_id   = "smoke_test_001",
        device       = device,
        user         = MOCK_USER,
        pwd          = MOCK_PASS,
        enb_pwd      = "",
        log_callback = log_cb,
        data_callback= data_cb,
    )

    connect_result = cli.connect()
    record(
        "CLIConnection.connect()",
        connect_result,
        f"connected={cli.connected}, hostname={cli.hostname}, "
        f"error={cli.error_message or 'none'}"
    )

    if not connect_result:
        server.stop()
        return {"passed": False, "steps": steps, "error": cli.error_message}

    # ── Step 6: Verify progress messages were emitted ────────────────────────
    has_progress = len(progress_messages) > 0
    record(
        "log_callback received progress messages",
        has_progress,
        f"{len(progress_messages)} messages"
    )

    # ── Step 7: Verify device prompt was received ─────────────────────────────
    time.sleep(0.5)
    all_data = "".join(data_received)
    prompt_str = MOCK_PROMPT.decode('utf-8', errors='replace')
    has_prompt = prompt_str in all_data or "#" in all_data
    record(
        "data_callback received device prompt",
        has_prompt,
        f"received {len(all_data)} chars: {repr(all_data[:80])}"
    )

    # ── Step 8: ShellReader is running ────────────────────────────────────────
    reader_alive = cli.reader is not None and cli.reader.is_alive()
    record("ShellReader thread running", reader_alive)

    # ── Step 9: write() sends data and echo is received ──────────────────────
    try:
        before = len("".join(data_received))
        cli.write("show version\n")
        time.sleep(0.4)
        after = len("".join(data_received))
        write_ok = after > before
        record(
            "write() sends keystrokes, echo received",
            write_ok,
            f"data grew from {before} to {after} chars"
        )
    except Exception as e:
        record("write() sends keystrokes", False, str(e))

    # ── Step 10: disconnect() cleans up ──────────────────────────────────────
    try:
        cli.disconnect()
        cleanup_ok = (not cli.connected and cli.chan is None and cli.client is None)
        record(
            "disconnect() cleans up",
            cleanup_ok,
            f"connected={cli.connected}, chan={cli.chan}, client={cli.client}"
        )
    except Exception as e:
        record("disconnect() cleans up", False, str(e))

    # ── Step 11: cli_status 'connected' would be emitted ─────────────────────
    # This is what background_connect() in vlan_checker_web.py checks before
    # emitting socketio.emit('cli_status', {'status': 'connected', ...})
    status_would_emit = connect_result and cli.hostname != ""
    record(
        "cli_status 'connected' would be emitted to browser",
        status_would_emit,
        f"hostname='{cli.hostname}'"
    )

    server.stop()

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    passed_count = sum(1 for s in steps if s["status"] == "PASS")
    failed_count = sum(1 for s in steps if s["status"] == "FAIL")
    print(f"Results: {passed_count} passed, {failed_count} failed")
    if overall_passed:
        print("RESULT: PASS — CLI terminal will work in the browser")
    else:
        print("RESULT: FAIL — CLI terminal will be stuck on 'Connecting'")
        print("DO NOT BUILD until this test passes.")
    print("=" * 60)

    return {
        "passed": overall_passed,
        "steps" : steps,
        "error" : None if overall_passed else f"{failed_count} step(s) failed",
    }


if __name__ == "__main__":
    result = run_cli_smoke_test()
    sys.exit(0 if result["passed"] else 1)
