"""
modules/cli_manager.py
----------------------
CLI Session Manager — v6.5.6 (Interactive Streaming Shell)

CRITICAL PRODUCTION FIXES APPLIED:
- v6.5.2: Initial connection handshake fix
- v6.5.4: Complete architecture rewrite with real-time progress feedback
- v6.5.6: Extensive QA validation for production stability

OFFLINE CAPABLE: All resources bundled, no external CDN dependencies

PURPOSE:
    Manages persistent, bi-directional raw SSH shells for the web-based
    interactive terminal (xterm.js + Flask-SocketIO).

ARCHITECTURE:
    Browser (xterm.js)
        │  cli_connect  ──►  handle_cli_connect()  (vlan_checker_web.py)
        │                        │
        │                        ├─ join_room(session_id)          [main SocketIO thread]
        │                        ├─ emit cli_status: 'connecting'  [main SocketIO thread]
        │                        └─ socketio.start_background_task(background_connect)
        │                                │
        │                                ├─ tcp_probe()            [background thread]
        │                                ├─ create_cli_session()   [background thread]
        │                                │     └─ CLIConnection.connect()
        │                                │           └─ _do_connect()
        │                                │                 ├─ paramiko.SSHClient.connect()
        │                                │                 ├─ invoke_shell()
        │                                │                 └─ ShellReader.start()
        │                                └─ emit cli_status: 'connected'
        │
        │  cli_data     ──►  handle_cli_data()  → cli.write()  → chan.send()
        │  cli_resize   ──►  handle_cli_resize() → cli.resize_pty()
        │  cli_disconnect ► handle_cli_disconnect() → remove_cli_session()
        │
        ◄──  cli_output   ──  ShellReader.run()  → data_callback()  → socketio.emit()
        ◄──  cli_progress ──  log_callback()  → socketio.emit()
        ◄──  cli_error    ──  background_connect() on failure

CRITICAL RULES — DO NOT BREAK:
    1. join_room(session_id) MUST be called in the main SocketIO event handler
       BEFORE start_background_task(). The room must exist before the background
       thread tries to emit to it.

    2. All socketio.emit() calls from background threads MUST use
       socketio.emit(..., to=session_id) — NOT the bare emit() shortcut.
       The bare emit() only works in the main SocketIO event context.

    3. NEVER nest ThreadPoolExecutor inside socketio.start_background_task().
       Flask-SocketIO threading mode + Python 3.14 deadlocks on nested executors.
       The socket-level timeout (10s in base_kwargs) handles hung connections.

    4. data_callback MUST emit to session_id room ONLY — never to both room AND sid.
       Double-emit causes every character to appear twice in xterm.js (the room
       already includes the client's sid, so emitting to sid is a duplicate).

    5. ShellReader reads raw bytes from the Paramiko channel and forwards them
       decoded as UTF-8 (with replacement). xterm.js handles ANSI escape codes
       natively — do NOT strip or process the bytes before forwarding.

    6. The watchdog timer (45s) force-closes the Paramiko client if _do_connect()
       hangs. This unblocks the background thread so it can emit cli_error.

    7. log_callback is for STATUS messages shown in the terminal progress area.
       data_callback is for RAW SSH output shown in the xterm.js terminal.
       Never mix them.

HOW TO VALIDATE CLI IS WORKING:
    1. Open browser → CLI Terminal tab
    2. Click Connect, enter device credentials
    3. Terminal should show:
         [INFO] Pre-flight check: <host>:22 ...
         [INFO] Network OK. Authenticating SSH...
         [INFO] Pass 1: Trying modern SSH algorithms...
         [INFO] SSH authenticated (modern algorithms)   ← or legacy
         [INFO] Opening interactive PTY shell...
         [INFO] Interactive shell ready
         ✓ Connected to <hostname>
    4. Device prompt should appear in the terminal
    5. Typing commands should produce output immediately
    6. Disconnect button should cleanly close the session

COMMON FAILURE MODES:
    - "Stuck on Connecting": background_connect() is not emitting cli_status.
      Check that join_room() was called before start_background_task().
    - "No output after connect": ShellReader not started, or data_callback
      is emitting to wrong target (sid instead of session_id room).
    - "Characters doubled": data_callback emitting to BOTH room AND sid.
      Remove the sid emit — emit to session_id room only.
    - "Auth failed": Wrong credentials or device requires enable password.
    - "Algorithm mismatch": Pass 1 failed, Pass 2 should handle it automatically.
    - "Timeout after 45s": Device unreachable or firewall blocking port 22.
"""

# ── MUST be first: inject telnetlib shim before any netmiko/paramiko import ──
import sys
try:
    import telnetlib  # noqa: F401 — already exists (Python <3.13)
except ImportError:
    try:
        import telnetlib_compat  # noqa: F401
    except ImportError:
        pass

import threading
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Session registry ──────────────────────────────────────────────────────────
_cli_sessions: dict = {}
_session_lock = threading.Lock()

# Hard deadline for the entire SSH handshake (seconds).
# The watchdog fires if _do_connect() hangs beyond this limit.
# Set to 25s so it fails BEFORE the frontend's 30s timeout.
_CONNECT_TIMEOUT = 25


# ─────────────────────────────────────────────────────────────────────────────
class ShellReader(threading.Thread):
    """
    Background thread: polls the Paramiko SSH channel for raw bytes and
    forwards them to data_callback (which emits cli_output via SocketIO).

    IMPORTANT: This thread runs for the lifetime of the CLI session.
    It must be stopped (self.stop()) before closing the channel/client,
    otherwise it will raise exceptions on the closed channel.
    """

    def __init__(self, channel, data_callback, on_close_callback):
        super().__init__(daemon=True)
        self.channel = channel
        self.data_callback = data_callback
        self.on_close_callback = on_close_callback
        self._stop_event = threading.Event()

    def stop(self):
        """Signal the reader loop to exit on next iteration."""
        self._stop_event.set()

    def run(self):
        try:
            while not self._stop_event.is_set():
                if self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if not data:
                        # Remote side closed the channel
                        break
                    try:
                        # Decode bytes → str for xterm.js.
                        # errors='replace' prevents crashes on non-UTF-8 device output.
                        decoded = data.decode('utf-8', errors='replace')
                        if self.data_callback:
                            self.data_callback(decoded)
                    except Exception as e:
                        logger.error("[CLI] ShellReader decode error: %s", e)

                if self.channel.exit_status_ready():
                    # Device closed the shell (e.g. logout command)
                    break

                # 10ms sleep prevents 100% CPU on idle sessions
                time.sleep(0.01)

        except Exception as e:
            logger.error("[CLI] ShellReader thread crashed: %s", e)
        finally:
            if self.on_close_callback:
                try:
                    self.on_close_callback()
                except Exception:
                    pass


# ─────────────────────────────────────────────────────────────────────────────
class CLIConnection:
    """
    Manages a single persistent raw SSH shell to a network device.

    Lifecycle:
        __init__() → connect() → [write() / resize_pty() ...] → disconnect()

    The connect() method calls _do_connect() which:
        1. Opens a Paramiko SSHClient (two-pass algorithm negotiation)
        2. Invokes an interactive PTY shell
        3. Reads the initial prompt to extract the real hostname
        4. Starts ShellReader background thread
        5. Forwards buffered prompt data to the frontend immediately
    """

    def __init__(self, session_id, device, user, pwd, enb_pwd,
                 log_callback=None, data_callback=None):
        self.session_id   = session_id
        self.device       = device
        self.host         = device.get("host", "unknown")
        self.port         = int(device.get("port", 22))
        self.device_type  = device.get("device_type", "cisco_ios")
        # hostname starts as IP; updated to real hostname after shell opens
        self.hostname     = self.host

        self.user         = user
        self.pwd          = pwd
        self.enb_pwd      = enb_pwd
        self.credential_id = ''

        # log_callback  → progress messages shown in terminal header area
        # data_callback → raw SSH bytes forwarded to xterm.js
        self.log_callback  = log_callback
        self.data_callback = data_callback

        self.client        = None   # paramiko.SSHClient
        self.chan          = None   # paramiko.Channel (interactive shell)
        self.reader        = None   # ShellReader thread
        self.connected     = False
        self.error_message = ""
        self.last_activity = time.time()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "info"):
        """
        Log to both Python logger and the UI via log_callback.
        log_callback is wrapped in try/except so a broken callback never
        crashes the connection flow.
        """
        ts  = datetime.now().strftime("%H:%M:%S")
        out = f"[{ts}] CLI {self.host}: {msg}"
        try:
            if self.log_callback:
                self.log_callback(out)
        except Exception:
            pass
        getattr(logger, level, logger.info)(out)

    def _progress(self, msg: str):
        """
        Send a progress message directly to the UI log_callback.
        Used for step-by-step feedback during the connection handshake
        so the user sees activity instead of a blank 'Connecting...' spinner.
        """
        try:
            if self.log_callback:
                self.log_callback(msg)
        except Exception:
            pass

    # ── Core connection logic ─────────────────────────────────────────────────

    def _do_connect(self):
        """
        Open the SSH connection and interactive shell.

        TWO-PASS SSH ALGORITHM STRATEGY (v6.1.2):
        ─────────────────────────────────────────
        Pass 1 — Modern auto-negotiate (no disabled_algorithms):
            Paramiko picks the strongest mutually-supported algorithm.
            Works on: IOS-XE 17.3+, NX-OS 9.3+, Juniper 21.x+, Arista EOS 4.x+
            These devices have SHA1/ssh-rsa DISABLED by default.

        Pass 2 — Legacy fallback (disable rsa-sha2-256/512):
            Forces ssh-rsa (SHA1) host key algorithm.
            Works on: IOS 12.x, old NX-OS 7.x, legacy devices.
            Only attempted if Pass 1 fails with an algorithm-negotiation error.
            Auth failures (wrong password) are NOT retried — retrying risks
            account lockout on devices with brute-force protection.

        DO NOT change this to Pass 2 only — that breaks all modern devices.
        DO NOT change this to Pass 1 only — that breaks all legacy devices.
        """
        import inspect
        import paramiko

        self._log(f"Initiating SSH to {self.host}:{self.port}...")
        self._progress(f"[{self.host}] Connecting on port {self.port}...")

        # ── Shared connection parameters ──────────────────────────────────────
        # timeout=10: socket-level TCP connect timeout (not auth timeout)
        # auth_timeout=15: time allowed for SSH authentication exchange
        # banner_timeout=15: time to wait for SSH server banner
        # allow_agent=False, look_for_keys=False: no SSH agent / key files
        # gss_auth/gss_kex: only passed when this Paramiko build accepts them
        raw_kwargs = {
            "hostname"      : self.host,
            "port"          : self.port,
            "username"      : self.user,
            "password"      : self.pwd,
            "timeout"       : 10,
            "banner_timeout": 15,
            "auth_timeout"  : 15,
            "allow_agent"   : False,
            "look_for_keys" : False,
            "gss_auth"      : False,
            "gss_kex"       : False,
        }
        connect_params = inspect.signature(paramiko.SSHClient.connect).parameters
        base_kwargs = {k: v for k, v in raw_kwargs.items() if k in connect_params}

        # ── Pass 1: Modern algorithm auto-negotiation ─────────────────────────
        self._log("Pass 1: Modern SSH algorithm negotiation...")
        self._progress(f"[{self.host}] Pass 1: Trying modern SSH algorithms...")
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(**base_kwargs)
            self._log("Pass 1 succeeded (modern algorithms)")
            self._progress(f"[{self.host}] SSH authenticated (modern algorithms)")

        except paramiko.AuthenticationException as e:
            # Wrong credentials — do NOT retry, do NOT fall back to legacy.
            # Retrying auth risks locking the account on devices with
            # brute-force protection (common on enterprise switches).
            raise paramiko.AuthenticationException(
                f"Authentication failed for user '{self.user}'. "
                f"Check username/password. ({e})"
            )

        except Exception as e:
            err_str = str(e).lower()
            # Only fall back to legacy for SSH algorithm negotiation failures.
            # Network errors (timeout, refused) are NOT retried.
            is_algo_error = any(kw in err_str for kw in [
                'no acceptable', 'key exchange', 'algorithm', 'hostkey',
                'incompatible', 'no matching', 'server key',
            ])
            if not is_algo_error:
                raise Exception(
                    f"SSH connection to {self.host}:{self.port} failed: {e}"
                )

            # ── Pass 2: Legacy ssh-rsa fallback ──────────────────────────────
            self._log(f"Pass 1 failed (algorithm mismatch): {e}")
            self._progress(f"[{self.host}] Pass 1 failed — trying legacy SSH (ssh-rsa)...")
            try:
                self.client.close()
            except Exception:
                pass

            legacy_kwargs = dict(base_kwargs)
            legacy_kwargs["disabled_algorithms"] = {
                "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]
            }
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(**legacy_kwargs)
            self._log("Pass 2 succeeded (legacy ssh-rsa mode)")
            self._progress(f"[{self.host}] SSH authenticated (legacy ssh-rsa mode)")

        # ── Open interactive PTY shell ────────────────────────────────────────
        # term='xterm' tells the device to use xterm escape sequences.
        # width/height should match the frontend terminal size; we use a
        # generous default and sync the real size via cli_resize after connect.
        self._log("Opening interactive PTY shell...")
        self._progress(f"[{self.host}] Opening interactive PTY shell...")
        self.chan = self.client.invoke_shell(term='xterm', width=220, height=50)

        # ── Read initial prompt to extract real hostname ──────────────────────
        # Most devices send their prompt immediately after shell open.
        # We wait up to 5s for a prompt character (#, >, $) then parse it.
        # This gives us the real hostname for the terminal title bar.
        # If no prompt arrives (slow device), we fall back to the IP address.
        time.sleep(0.3)
        prompt_data = b""
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if self.chan.recv_ready():
                chunk = self.chan.recv(4096)
                if chunk:
                    prompt_data += chunk
                    # Stop as soon as we see a prompt character
                    if b'#' in chunk or b'>' in chunk or b'$' in chunk:
                        break
            time.sleep(0.05)

        if prompt_data:
            raw = prompt_data.decode('utf-8', errors='replace')
            # Take the last non-empty line and strip prompt characters
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            if lines:
                candidate = lines[-1].rstrip('#>$ ').strip()
                # Sanity check: hostname must be at least 2 chars and not
                # contain spaces (which would indicate it's a banner line)
                if candidate and len(candidate) >= 2 and ' ' not in candidate:
                    self.hostname = candidate
                    self._log(f"Hostname resolved: {self.hostname}")

        # ── Start ShellReader background thread ───────────────────────────────
        # ShellReader polls the channel and forwards bytes to data_callback.
        # It must be started AFTER we've consumed the initial prompt bytes,
        # so we can forward them ourselves below without a race condition.
        self.reader = ShellReader(
            self.chan,
            self.data_callback,
            on_close_callback=lambda: self._log(
                "Remote host closed the terminal session", "warning"
            )
        )
        self.reader.start()

        # ── Forward buffered prompt to frontend ───────────────────────────────
        # The initial prompt bytes were read above (before ShellReader started).
        # Forward them now so the user sees the device prompt immediately.
        if prompt_data and self.data_callback:
            try:
                self.data_callback(prompt_data.decode('utf-8', errors='replace'))
            except Exception:
                pass

        self._log("Interactive shell established")
        self._progress(f"[{self.hostname}] Interactive shell ready")
        return True

    def connect(self) -> bool:
        """
        Establish the SSH session with watchdog protection.

        Called from socketio.start_background_task() — already in a background
        thread. Do NOT wrap in ThreadPoolExecutor (nested executors deadlock
        in Python 3.14 + Flask-SocketIO threading mode).

        The watchdog timer fires after _CONNECT_TIMEOUT seconds and force-closes
        the Paramiko client, which unblocks any hung recv()/connect() call so
        the background thread can emit cli_error to the frontend.
        """
        import threading as _threading

        def _watchdog():
            self._log(
                f"Watchdog: connection timed out after {_CONNECT_TIMEOUT}s",
                "error"
            )
            self.error_message = (
                f"SSH handshake timed out after {_CONNECT_TIMEOUT}s. "
                f"Device {self.host} may be unreachable or refusing connections."
            )
            try:
                if self.client:
                    self.client.close()
            except Exception:
                pass

        watchdog = _threading.Timer(_CONNECT_TIMEOUT, _watchdog)
        watchdog.daemon = True
        watchdog.start()

        try:
            self._do_connect()
            watchdog.cancel()
            self.connected = True
            self.last_activity = time.time()
            return True
        except Exception as e:
            watchdog.cancel()
            # If the watchdog fired, preserve its detailed error message
            if not self.error_message or "timed out after" not in self.error_message:
                self.error_message = str(e)
            self._log(f"Connection FAILED: {self.error_message}", "error")
            self.connected = False
            try:
                if self.client:
                    self.client.close()
            except Exception:
                pass
            return False

    # ── Session I/O ──────────────────────────────────────────────────────────

    def write(self, data: str):
        """
        Forward a keystroke/string from xterm.js to the SSH channel.

        xterm.js sends raw characters (including control sequences like
        Ctrl-C = '\x03', arrow keys = '\x1b[A', etc.).
        We encode as UTF-8 and send directly — no processing.
        """
        if not self.connected or not self.chan:
            return
        try:
            self.last_activity = time.time()
            self.chan.send(data.encode('utf-8'))
        except Exception as e:
            self._log(f"Write error: {e}", "error")
            self.connected = False

    def resize_pty(self, cols: int, rows: int):
        """
        Sync the backend PTY dimensions with the frontend xterm.js terminal.
        Called when the browser window is resized or on initial connect.
        """
        if self.chan:
            try:
                self.chan.resize_pty(width=cols, height=rows)
            except Exception as e:
                logger.error("[CLI] PTY resize error: %s", e)

    def disconnect(self):
        """
        Gracefully tear down the session.
        Order matters: stop reader first, then close channel, then close client.
        """
        self.connected = False
        # 1. Stop the reader thread so it doesn't try to read a closed channel
        if self.reader:
            self.reader.stop()
        # 2. Close the SSH channel
        if self.chan:
            try:
                self.chan.close()
            except Exception:
                pass
        # 3. Close the SSH transport/client
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.chan   = None
        self.client = None
        self.scrub_secrets()
        self._log("Session closed")

    def scrub_secrets(self):
        """Drop in-memory SSH secrets after connect or teardown."""
        self.pwd = ''
        self.enb_pwd = ''
        if isinstance(self.device, dict):
            self.device['password'] = ''
            self.device['secret'] = ''
            self.device.pop('become_password', None)

    def check_idle_timeout(self, timeout_seconds: int = 600) -> bool:
        """Return True if the session has been idle longer than timeout_seconds."""
        return (time.time() - self.last_activity) > timeout_seconds

    def get_status(self) -> dict:
        return {
            "session_id" : self.session_id,
            "host"       : self.host,
            "hostname"   : self.hostname,
            "connected"  : self.connected,
            "idle_time"  : int(time.time() - self.last_activity),
            "error"      : self.error_message,
            "credential_id": self.credential_id or None,
        }


# ── Session registry helpers ──────────────────────────────────────────────────

# session_id -> Socket.IO sid that owns the SSH session
_cli_owners: dict = {}


def bind_cli_owner(session_id: str, sid: str) -> None:
    with _session_lock:
        _cli_owners[session_id] = sid


def cli_owner_matches(session_id: str, sid: str) -> bool:
    with _session_lock:
        return _cli_owners.get(session_id) == sid


def release_cli_owner(session_id: str) -> None:
    with _session_lock:
        _cli_owners.pop(session_id, None)


def session_ids_owned_by_sid(sid: str) -> list:
    with _session_lock:
        return [sess for sess, owner in _cli_owners.items() if owner == sid]


def create_cli_session(session_id, device, user, pwd, enb_pwd,
                       log_callback=None, data_callback=None):
    """
    Create and connect a new CLI session.

    Called from socketio.start_background_task() — already in a background
    thread. Returns the CLIConnection on success, None on failure.

    The caller (background_connect in vlan_checker_web.py) is responsible
    for emitting cli_status/cli_error based on the return value.
    """
    with _session_lock:
        if session_id in _cli_sessions:
            existing = _cli_sessions[session_id]
            if getattr(existing, 'connected', False):
                return existing
        cli = CLIConnection(
            session_id, device, user, pwd, enb_pwd,
            log_callback, data_callback
        )
        if cli.connect():
            cli.scrub_secrets()
            _cli_sessions[session_id] = cli
            return cli
        cli.scrub_secrets()
        return None


def get_cli_session(session_id):
    with _session_lock:
        return _cli_sessions.get(session_id)


def list_cli_sessions():
    """Return status dicts for all active sessions."""
    with _session_lock:
        return [
            {
                "session_id": sid,
                "host"      : cli.host,
                "hostname"  : cli.hostname,
                "connected" : cli.connected,
                "idle_time" : int(time.time() - cli.last_activity),
            }
            for sid, cli in _cli_sessions.items()
        ]


def remove_cli_session(session_id):
    """Disconnect and remove a session from the registry."""
    with _session_lock:
        cli = _cli_sessions.pop(session_id, None)
        _cli_owners.pop(session_id, None)
    if cli:
        cli.disconnect()
        return True
    return False


def disconnect_all_sessions() -> int:
    """Disconnect all active sessions. Returns count of sessions closed."""
    with _session_lock:
        sessions = list(_cli_sessions.items())
        _cli_sessions.clear()
        _cli_owners.clear()
    for _, cli in sessions:
        try:
            cli.disconnect()
        except Exception:
            pass
    return len(sessions)


def cleanup_idle_sessions(timeout_seconds: int = 600) -> int:
    """Remove sessions idle longer than timeout_seconds. Returns count removed."""
    to_remove = []
    with _session_lock:
        for sid, cli in list(_cli_sessions.items()):
            if cli.check_idle_timeout(timeout_seconds):
                to_remove.append(sid)
    removed = 0
    for sid in to_remove:
        if remove_cli_session(sid):
            removed += 1
    return removed
