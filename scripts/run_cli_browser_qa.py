#!/usr/bin/env python3
"""Run /cli_terminal credential_id browser QA (Node Playwright, mocked SSH).

Single supported entrypoint — does not use Python Playwright.

  python3 scripts/run_cli_browser_qa.py

Steps:
  1) Check node/npm
  2) npm ci (pinned lockfile) in tests/browser
  3) Ensure Chromium for Playwright 1.49.1
  4) Start scripts/cli_browser_qa_server.py on loopback (mocked SSH)
  5) Run tests/browser/cli_credential_id.spec.mjs
  6) Tear down server

Env:
  NST_CLI_BROWSER_QA_PORT  — bind port (default: free port, prefer 5051)
  NST_BROWSER_BASE         — override base URL (set automatically)
  NST_CLI_BROWSER_QA_SKIP_INSTALL=1 — skip npm ci / playwright install
"""
from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = ROOT / 'tests' / 'browser'
SPEC = BROWSER_DIR / 'cli_credential_id.spec.mjs'
SERVER = ROOT / 'scripts' / 'cli_browser_qa_server.py'
PACKAGE_JSON = BROWSER_DIR / 'package.json'
LOCKFILE = BROWSER_DIR / 'package-lock.json'


def _fail(msg: str, code: int = 1) -> int:
    print(f'FAIL: {msg}', file=sys.stderr, flush=True)
    return code


def _which(name: str) -> str | None:
    return shutil.which(name)


def _port_free(port: int, host: str = '127.0.0.1') -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _pick_port() -> int:
    raw = (os.environ.get('NST_CLI_BROWSER_QA_PORT') or '').strip()
    if raw:
        return int(raw)
    if _port_free(5051):
        return 5051
    # Ephemeral ports hit Werkzeug/Socket.IO websocket AssertionError on this host
    # (Python 3.14). Product + QA CORS default is :5051 — require it free.
    raise SystemExit(
        'FAIL: port 5051 is busy. Stop the local NST web console, then rerun '
        'scripts/run_cli_browser_qa.py (CI-browser Socket.IO QA requires 127.0.0.1:5051).'
    )


def _wait_health(base: str, timeout: float = 45.0) -> bool:
    deadline = time.time() + timeout
    url = f'{base}/health'
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 300:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.25)
    return False


def _ensure_node() -> int | None:
    if not _which('node'):
        return _fail(
            'Node.js is required for CLI browser QA (Python Playwright is unsupported here). '
            'Install Node 18+ and re-run: python3 scripts/run_cli_browser_qa.py'
        )
    if not _which('npm'):
        return _fail('npm is required. Install Node.js (includes npm) and re-run.')
    return None


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> int:
    print(f'+ {" ".join(cmd)}', flush=True)
    return subprocess.run(cmd, cwd=str(cwd or ROOT), env=env).returncode


def _ensure_npm_deps() -> int | None:
    if os.environ.get('NST_CLI_BROWSER_QA_SKIP_INSTALL') == '1':
        if not (BROWSER_DIR / 'node_modules' / 'playwright').is_dir():
            return _fail(
                'NST_CLI_BROWSER_QA_SKIP_INSTALL=1 but tests/browser/node_modules/playwright is missing'
            )
        return None
    if not PACKAGE_JSON.is_file():
        return _fail(f'missing {PACKAGE_JSON}')
    if not LOCKFILE.is_file():
        return _fail(f'missing {LOCKFILE} — commit package-lock.json for reproducible installs')
    # Prefer ci for reproducibility; fall back to install if needed
    rc = _run(['npm', 'ci', '--no-fund', '--no-audit'], cwd=BROWSER_DIR)
    if rc != 0:
        return _fail('npm ci failed in tests/browser — check Node/npm and package-lock.json')
    return None


def _ensure_chromium() -> int | None:
    if os.environ.get('NST_CLI_BROWSER_QA_SKIP_INSTALL') == '1':
        return None
    # Install Chromium into the Playwright cache (offline after first download).
    rc = _run(
        ['npx', '--no-install', 'playwright', 'install', 'chromium'],
        cwd=BROWSER_DIR,
    )
    if rc != 0:
        return _fail(
            'playwright install chromium failed. '
            'Need network once to cache Chromium, or set PLAYWRIGHT_BROWSERS_PATH to an offline cache. '
            'Python Playwright is not used (greenlet/Python 3.14 incompatible on some hosts).'
        )
    return None


def _start_server(port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env['BROWSER'] = env.get('BROWSER') or '/usr/bin/true'
    env['NST_BIND'] = '127.0.0.1'
    env['NST_CLI_BROWSER_QA_PORT'] = str(port)
    env['PYTHONUNBUFFERED'] = '1'
    print(f'+ {sys.executable} {SERVER} (port {port})', flush=True)
    # DEVNULL avoids pipe-buffer deadlock; health probe is the readiness signal.
    return subprocess.Popen(
        [sys.executable, str(SERVER)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _stop_server(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.terminate()
        except OSError:
            pass
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            proc.kill()


def main() -> int:
    print('=== NST CLI browser QA (credential_id-only, mocked SSH) ===', flush=True)
    if not SPEC.is_file():
        return _fail(f'missing browser spec {SPEC}')
    if not SERVER.is_file():
        return _fail(f'missing QA server {SERVER}')

    err = _ensure_node()
    if err is not None:
        return err
    err = _ensure_npm_deps()
    if err is not None:
        return err
    err = _ensure_chromium()
    if err is not None:
        return err

    port = _pick_port()
    if not _port_free(port):
        return _fail(f'port {port} is already in use — set NST_CLI_BROWSER_QA_PORT to a free port')

    base = f'http://127.0.0.1:{port}'
    proc = None
    try:
        proc = _start_server(port)
        if not _wait_health(base):
            code = proc.poll()
            _stop_server(proc)
            return _fail(
                f'QA server did not become healthy at {base}/health within timeout '
                f'(process exit={code}). Check Socket.IO deps and port {port}.'
            )
        print(f'PASS: QA server healthy at {base}', flush=True)

        env = os.environ.copy()
        env['NST_BROWSER_BASE'] = base
        rc = _run(['node', str(SPEC.name)], cwd=BROWSER_DIR, env=env)
        if rc != 0:
            return _fail(
                f'browser credential_id scenarios failed (exit {rc}). '
                'See PASS/FAIL lines above. No live vendor SSH is required for this suite.',
                code=rc if rc else 1,
            )
        print('PASS: CLI browser QA (credential_id-only)', flush=True)
        return 0
    finally:
        _stop_server(proc)


if __name__ == '__main__':
    sys.exit(main())
