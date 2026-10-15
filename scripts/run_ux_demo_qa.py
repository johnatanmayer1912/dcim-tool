#!/usr/bin/env python3
"""Playwright QA for docs/11-ux/demos/09-offline-8vendor-lab.html (file://)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = ROOT / 'tests' / 'browser'
SPEC = BROWSER_DIR / 'ux_demo_09_8vendor.spec.mjs'


def main() -> int:
    print('=== NST UX demo 09 (8-vendor lab, file://) ===', flush=True)
    if shutil.which('node') is None:
        print('FAIL: Node.js required', file=sys.stderr)
        return 1
    if not SPEC.is_file():
        print(f'FAIL: missing {SPEC}', file=sys.stderr)
        return 1
    if os.environ.get('NST_CLI_BROWSER_QA_SKIP_INSTALL') != '1':
        if subprocess.run(['npm', 'ci', '--no-fund', '--no-audit'], cwd=str(BROWSER_DIR)).returncode:
            return 1
        if subprocess.run(['npx', '--no-install', 'playwright', 'install', 'chromium'], cwd=str(BROWSER_DIR)).returncode:
            return 1
    rc = subprocess.run(['node', SPEC.name], cwd=str(BROWSER_DIR)).returncode
    if rc:
        print(f'FAIL: demo 09 scenarios exit {rc}', file=sys.stderr)
        return rc
    print('PASS: UX demo 09 8-vendor lab', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
