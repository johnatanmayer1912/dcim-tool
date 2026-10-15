#!/usr/bin/env python3
"""Local offline-packaging checks. Not an air-gap EXE proof. Not a signed-EXE proof."""
from __future__ import annotations

import glob
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fail(msg: str, errors: list) -> None:
    errors.append(msg)
    print(f'  FAIL {msg}')


def _ok(msg: str) -> None:
    print(f'  OK   {msg}')


def main() -> int:
    print('OFFLINE VERIFICATION (checkout ingredients, not air-gap EXE)')
    errors: list = []

    version_path = os.path.join(ROOT, 'VERSION')
    if not os.path.isfile(version_path):
        _fail('VERSION missing', errors)
    else:
        ver = open(version_path, encoding='utf-8').read().strip()
        if not ver:
            _fail('VERSION empty', errors)
        else:
            _ok(f'VERSION={ver}')

    vis = os.path.join(ROOT, 'modules', 'web', 'vis-network.min.js')
    if not os.path.isfile(vis):
        _fail('modules/web/vis-network.min.js missing', errors)
    else:
        size = os.path.getsize(vis)
        if size < 10000:
            _fail(f'vis-network.min.js too small ({size} bytes)', errors)
        else:
            _ok(f'vis-network.min.js ({size} bytes)')
        digest = hashlib.sha256(open(vis, 'rb').read()).hexdigest()
        pin = vis + '.sha256'
        if not os.path.isfile(pin):
            _fail('modules/web/vis-network.min.js.sha256 missing (SBOM-lite pin)', errors)
        else:
            expected = open(pin, encoding='utf-8').read().strip().split()[0]
            if digest != expected:
                _fail(f'vis-network.min.js SHA-256 mismatch (got {digest[:12]}…)', errors)
            else:
                _ok(f'vis-network.min.js sha256={digest[:16]}…')

    shell = os.path.join(ROOT, 'utils', 'topo_map_shell.py')
    text = open(shell, encoding='utf-8').read()
    if 'unpkg.com' in text:
        _fail('topo_map_shell.py still references unpkg.com', errors)
    else:
        _ok('topo_map_shell.py has no unpkg.com')
    if 'OFFLINE_VIS_MISSING_SCRIPT' not in text:
        _fail('offline vis fallback constant missing', errors)
    else:
        _ok('offline vis fallback present')

    specs = glob.glob(os.path.join(ROOT, 'NetworkSwissToolPro_v*.spec'))
    if not specs:
        _fail('no NetworkSwissToolPro_v*.spec', errors)
    else:
        found = False
        for spec in specs:
            body = open(spec, encoding='utf-8').read()
            if 'utils.discovery_profiles' in body:
                found = True
                _ok(f'{os.path.basename(spec)} hiddenimport discovery_profiles')
                break
        if not found:
            _fail('spec missing utils.discovery_profiles hiddenimport', errors)

    outp = open(os.path.join(ROOT, 'utils', 'output_paths.py'), encoding='utf-8').read()
    if 'NST_DATA_DIR' not in outp:
        _fail('output_paths.py missing NST_DATA_DIR', errors)
    else:
        _ok('NST_DATA_DIR documented in output_paths.py')

    pre = open(os.path.join(ROOT, '_prebuild.py'), encoding='utf-8').read()
    if 'playwright' in pre.lower():
        _fail('_prebuild.py requires playwright', errors)
    else:
        _ok('_prebuild.py does not require Playwright')

    index_html = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
    idx = open(index_html, encoding='utf-8').read()
    if 'cdn.jsdelivr' in idx or 'fonts.googleapis.com' in idx or 'unpkg.com' in idx:
        _fail('index.html still references a CSS/JS CDN', errors)
    else:
        _ok('index.html has no Bootstrap/Google Fonts/unpkg CDN')

    required_docs = [
        os.path.join(ROOT, '.cursor', 'docs', 'pilot', 'PILOT_SCOPE.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'offline', 'EXE_RELEASE_BLOCKERS.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'live-lab', 'LIVE_LAB_PLAN.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'E2E_ACCEPTANCE_STRATEGY.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'READINESS_TRACEABILITY.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'FROZEN_BASELINE.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'named-lab', 'LAB_SCOPE.md'),
        os.path.join(ROOT, '.cursor', 'docs', 'airgap', 'AIRGAP_SCOPE.md'),
    ]
    for path in required_docs:
        if not os.path.isfile(path):
            _fail(f'missing {os.path.relpath(path, ROOT)}', errors)
        else:
            _ok(os.path.relpath(path, ROOT))

    print()
    if errors:
        print(f'{len(errors)} check(s) failed — not air-gap proven; fix ingredients first')
        return 1
    print('OFFLINE INGREDIENTS OK — still not a signed EXE or clean-machine proof')
    return 0


if __name__ == '__main__':
    sys.exit(main())
