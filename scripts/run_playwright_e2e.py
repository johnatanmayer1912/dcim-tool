#!/usr/bin/env python3
"""Unified CI-browser Playwright E2E for NST offline/operator scope.

Runs, in order:
  1) CLI credential_id suite (mocked SSH)
  2) Operator Program Status + Swiss Tools overlay honesty
  3) file:// Standard L2 + Discovery overlay HTML

Never bundled in the PyInstaller EXE. Not live-vendor. Not EXE E2E.

  NST_REVIEW_DIR=... python3 scripts/run_playwright_e2e.py
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = ROOT / 'tests' / 'browser'
SERVER = ROOT / 'scripts' / 'cli_browser_qa_server.py'
GEN = ROOT / 'scripts' / 'generate_unified_e2e_demo.py'
CLI_SPEC = BROWSER_DIR / 'cli_credential_id.spec.mjs'
OP_SPECS = (
    BROWSER_DIR / 'operator_program_status.spec.mjs',
    BROWSER_DIR / 'operator_swiss_tools_overlay.spec.mjs',
    BROWSER_DIR / 'operator_enterprise_shell.spec.mjs',
)
MAP_SPEC = BROWSER_DIR / 'offline_map_html.spec.mjs'
DEMO_SPEC = BROWSER_DIR / 'ux_demo_09_8vendor.spec.mjs'


def _fail(msg: str, code: int = 1) -> int:
    print(f'FAIL: {msg}', file=sys.stderr, flush=True)
    return code


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
        'scripts/run_playwright_e2e.py (CI-browser Socket.IO QA requires 127.0.0.1:5051).'
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


def _tee_run(cmd: list[str], *, cwd: Path, env: dict, log_path: Path | None) -> int:
    print(f'+ {" ".join(cmd)}', flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    sys.stdout.write(proc.stdout or '')
    sys.stderr.write(proc.stderr or '')
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text((proc.stdout or '') + (proc.stderr or ''), encoding='utf-8')
    return proc.returncode


def _stop_server(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
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


def main() -> int:
    print('=== NST unified Playwright E2E (CI-browser, not EXE) ===', flush=True)
    if shutil.which('node') is None:
        return _fail('Node.js required.')
    review = Path(os.environ.get('NST_REVIEW_DIR') or '').resolve() if os.environ.get('NST_REVIEW_DIR') else None
    results: dict = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'suites': [],
        'note': 'CI-browser against source + fixture maps. Not live-vendor. Not Windows EXE E2E.',
    }
    log_dir = (review / 'playwright' / 'logs') if review else None

    if os.environ.get('NST_CLI_BROWSER_QA_SKIP_INSTALL') != '1':
        if subprocess.run(
            ['npm', 'ci', '--no-fund', '--no-audit'], cwd=str(BROWSER_DIR)
        ).returncode != 0:
            return _fail('npm ci failed')
        if subprocess.run(
            ['npx', '--no-install', 'playwright', 'install', 'chromium'],
            cwd=str(BROWSER_DIR),
        ).returncode != 0:
            return _fail('playwright install chromium failed')

    port = _pick_port()
    base = f'http://127.0.0.1:{port}'
    env_base = os.environ.copy()
    env_base['BROWSER'] = env_base.get('BROWSER') or '/usr/bin/true'
    env_base['NST_BIND'] = '127.0.0.1'
    env_base['NST_CLI_BROWSER_QA_PORT'] = str(port)
    env_base['PYTHONUNBUFFERED'] = '1'
    proc = subprocess.Popen(
        [sys.executable, str(SERVER)],
        cwd=str(ROOT),
        env=env_base,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        if not _wait_health(base):
            return _fail(f'QA server not healthy at {base}/health')
        run_env = os.environ.copy()
        run_env['NST_BROWSER_BASE'] = base
        if review:
            run_env['NST_REVIEW_DIR'] = str(review)

        for spec in (CLI_SPEC, *OP_SPECS):
            logp = (log_dir / f'{spec.stem}.log') if log_dir else None
            rc = _tee_run(['node', spec.name], cwd=BROWSER_DIR, env=run_env, log_path=logp)
            results['suites'].append({'spec': spec.name, 'exit': rc, 'needs_server': True})
            if rc != 0:
                results['ok'] = False
                if review:
                    (review / 'playwright' / 'summary.json').write_text(
                        json.dumps(results, indent=2), encoding='utf-8'
                    )
                return _fail(f'{spec.name} failed (exit {rc})', code=rc or 1)
    finally:
        _stop_server(proc)

    dest = review if review else Path(os.environ.get('NST_MAP_HTML_OUT') or ROOT / 'docs' / 'review_folder' / '2026.08.23' / 'QA' / 'enterprise_validation_rendering_and_ship_readiness')
    dest.mkdir(parents=True, exist_ok=True)
    gen_rc = subprocess.run([sys.executable, str(GEN), str(dest)], cwd=str(ROOT)).returncode
    results['suites'].append({'spec': 'generate_unified_e2e_demo.py', 'exit': gen_rc})
    if gen_rc != 0:
        results['ok'] = False
        return _fail('map generation failed')

    std = dest / 'generated_outputs' / 'maps' / 'standard_l2_overlay_replay.html'
    disc = dest / 'generated_outputs' / 'maps' / 'discovery_command_center.html'
    map_env = os.environ.copy()
    map_env['NST_STD_L2_HTML'] = str(std)
    map_env['NST_DISC_HTML'] = str(disc)
    if review:
        map_env['NST_REVIEW_DIR'] = str(review)
    logp = (log_dir / f'{MAP_SPEC.stem}.log') if log_dir else None
    map_rc = _tee_run(['node', MAP_SPEC.name], cwd=BROWSER_DIR, env=map_env, log_path=logp)
    results['suites'].append({'spec': MAP_SPEC.name, 'exit': map_rc, 'needs_server': False})
    demo_log = (log_dir / f'{DEMO_SPEC.stem}.log') if log_dir else None
    demo_env = os.environ.copy()
    if review:
        demo_env['NST_REVIEW_DIR'] = str(review)
    demo_rc = _tee_run(['node', DEMO_SPEC.name], cwd=BROWSER_DIR, env=demo_env, log_path=demo_log)
    results['suites'].append({'spec': DEMO_SPEC.name, 'exit': demo_rc, 'needs_server': False})
    results['finished_at'] = datetime.now(timezone.utc).isoformat()
    results['ok'] = map_rc == 0 and demo_rc == 0
    if review:
        (review / 'playwright' / 'summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        html = [
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>NST Playwright E2E</title></head><body>',
            '<h1>NST Playwright E2E (CI-browser)</h1>',
            '<p>Not live-vendor. Not Windows EXE E2E. Chromium is not in the product EXE.</p>',
            f'<p>ok={results["ok"]}</p><ul>',
        ]
        for s in results['suites']:
            html.append(f'<li>{s["spec"]}: exit {s["exit"]}</li>')
        html.append('</ul></body></html>')
        (review / 'playwright' / 'html').mkdir(parents=True, exist_ok=True)
        (review / 'playwright' / 'html' / 'index.html').write_text('\n'.join(html), encoding='utf-8')
    if map_rc != 0:
        return _fail(f'{MAP_SPEC.name} failed (exit {map_rc})', code=map_rc or 1)
    if demo_rc != 0:
        return _fail(f'{DEMO_SPEC.name} failed (exit {demo_rc})', code=demo_rc or 1)
    print('PASS: unified Playwright E2E (CI-browser, offline/operator scope)', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
