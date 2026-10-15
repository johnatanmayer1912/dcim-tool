#!/usr/bin/env python3
"""Playwright file:// QA for generated Standard L2 + Discovery overlay HTML.

Generates the offline 8-vendor demo maps (fixture-only) then runs
tests/browser/offline_map_html.spec.mjs.

  python3 scripts/run_offline_map_html_qa.py [optional_out_dir]

Not live-vendor. Not EXE E2E. Chromium is CI-browser only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = ROOT / 'tests' / 'browser'
SPEC = BROWSER_DIR / 'offline_map_html.spec.mjs'
GEN = ROOT / 'scripts' / 'generate_unified_e2e_demo.py'


def _fail(msg: str, code: int = 1) -> int:
    print(f'FAIL: {msg}', file=sys.stderr, flush=True)
    return code


def main() -> int:
    print('=== NST offline map HTML Playwright QA (fixture maps, not live) ===', flush=True)
    if shutil.which('node') is None:
        return _fail('Node.js required (Node 18+).')
    if not SPEC.is_file():
        return _fail(f'missing {SPEC}')
    if not GEN.is_file():
        return _fail(f'missing {GEN}')

    dest = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='nst-map-html-qa-'))
    dest.mkdir(parents=True, exist_ok=True)
    print(f'+ generate demo maps → {dest}', flush=True)
    rc = subprocess.run([sys.executable, str(GEN), str(dest)], cwd=str(ROOT)).returncode
    if rc != 0:
        return _fail(f'generate_unified_e2e_demo.py failed (exit {rc})')

    std = dest / 'generated_outputs' / 'maps' / 'standard_l2_overlay_replay.html'
    disc = dest / 'generated_outputs' / 'maps' / 'discovery_command_center.html'
    if not std.is_file() or not disc.is_file():
        return _fail(f'missing generated maps under {dest / "generated_outputs" / "maps"}')

    if os.environ.get('NST_CLI_BROWSER_QA_SKIP_INSTALL') != '1':
        if not (BROWSER_DIR / 'package-lock.json').is_file():
            return _fail(f'missing {BROWSER_DIR / "package-lock.json"}')
        if subprocess.run(
            ['npm', 'ci', '--no-fund', '--no-audit'], cwd=str(BROWSER_DIR)
        ).returncode != 0:
            return _fail('npm ci failed in tests/browser')
        if subprocess.run(
            ['npx', '--no-install', 'playwright', 'install', 'chromium'],
            cwd=str(BROWSER_DIR),
        ).returncode != 0:
            return _fail('playwright install chromium failed')

    env = os.environ.copy()
    env['NST_STD_L2_HTML'] = str(std)
    env['NST_DISC_HTML'] = str(disc)
    print(f'+ node {SPEC.name}', flush=True)
    rc = subprocess.run(['node', SPEC.name], cwd=str(BROWSER_DIR), env=env).returncode
    if rc != 0:
        return _fail(f'offline map HTML scenarios failed (exit {rc})', code=rc or 1)
    print('PASS: offline map HTML Playwright QA (fixture maps)', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
