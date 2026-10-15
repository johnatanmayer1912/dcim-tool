#!/usr/bin/env python3
"""Run operator-console browser QA (Node Playwright, mocked loopback server).

Covers Program Status, workspace navigation, hard-stop messaging, related-surface jumps.
Reuses the same mocked QA server as CLI browser QA (no live SSH).

  python3 scripts/run_operator_browser_qa.py
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
SPECS = (
    BROWSER_DIR / 'operator_program_status.spec.mjs',
    BROWSER_DIR / 'operator_swiss_tools_overlay.spec.mjs',
    BROWSER_DIR / 'operator_enterprise_shell.spec.mjs',
)
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
        'scripts/run_operator_browser_qa.py (CI-browser Socket.IO QA requires 127.0.0.1:5051).'
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


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> int:
    print(f'+ {" ".join(cmd)}', flush=True)
    return subprocess.run(cmd, cwd=str(cwd or ROOT), env=env).returncode


def main() -> int:
    print('=== NST operator browser QA (Program Status / hard-stop) ===', flush=True)
    if not _which('node'):
        return _fail('Node.js required. Install Node 18+ and re-run.')
    missing = [str(p) for p in SPECS if not p.is_file()]
    if missing:
        return _fail(f'missing specs: {missing}')
    if not SERVER.is_file():
        return _fail(f'missing {SERVER}')

    if os.environ.get('NST_CLI_BROWSER_QA_SKIP_INSTALL') != '1':
        if not LOCKFILE.is_file():
            return _fail(f'missing {LOCKFILE}')
        if _run(['npm', 'ci', '--no-fund', '--no-audit'], cwd=BROWSER_DIR) != 0:
            return _fail('npm ci failed in tests/browser')
        if _run(['npx', '--no-install', 'playwright', 'install', 'chromium'], cwd=BROWSER_DIR) != 0:
            return _fail('playwright install chromium failed')

    port = _pick_port()
    base = f'http://127.0.0.1:{port}'
    env = os.environ.copy()
    env['BROWSER'] = env.get('BROWSER') or '/usr/bin/true'
    env['NST_BIND'] = '127.0.0.1'
    env['NST_CLI_BROWSER_QA_PORT'] = str(port)
    env['PYTHONUNBUFFERED'] = '1'
    proc = subprocess.Popen(
        [sys.executable, str(SERVER)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        if not _wait_health(base):
            return _fail(f'QA server not healthy at {base}/health')
        run_env = os.environ.copy()
        run_env['NST_BROWSER_BASE'] = base
        review = os.environ.get('NST_REVIEW_DIR', '').strip()
        if review:
            run_env['NST_REVIEW_DIR'] = review
        for spec in SPECS:
            rc = _run(['node', spec.name], cwd=BROWSER_DIR, env=run_env)
            if rc != 0:
                return _fail(f'{spec.name} failed (exit {rc})', code=rc or 1)
        print('PASS: operator browser QA (Program Status + overlay honesty / blocked gate)', flush=True)
        return 0
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()


if __name__ == '__main__':
    sys.exit(main())
