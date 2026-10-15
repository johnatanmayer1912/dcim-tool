#!/usr/bin/env python3
"""
Mandatory release QA orchestrator — reads tests/qa/MANDATORY_MANIFEST.yaml.

Phases:
  every_code_change  — fast gate after code edits (prebuild + manifest validate)
  pre_release        — before VERSION bump / EXE build
  all                — both phases

Scaffold suites (tests/qa/test_*.py) are skipped unless NST_MANDATORY_QA_FULL=1.

Do NOT run automatically on every agent turn unless an agent or CI invokes this script.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'tests' / 'qa' / 'MANDATORY_MANIFEST.yaml'


def normalize_command(cmd):
    """Manifest lists `python`; run with this process's interpreter (python3 on macOS)."""
    if not cmd:
        return cmd
    out = list(cmd)
    if out[0] in ('python', 'python3', 'py'):
        out[0] = sys.executable
    return out


def load_manifest():
    import yaml
    return yaml.safe_load(MANIFEST.read_text(encoding='utf-8'))


def run_cmd(cmd, label: str) -> bool:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    cmd = normalize_command(cmd)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f'FAIL: {label}')
        return False
    print(f'PASS: {label}')
    return True


def run_suite(suite: dict) -> bool:
    sid = suite.get('id', '?')
    label = f"mandatory:{sid}"

    if suite.get('scaffold') and not os.environ.get('NST_MANDATORY_QA_FULL'):
        path = suite.get('path')
        if path and (ROOT / path).is_file():
            print(f'SKIP (scaffold): {sid} — file present; set NST_MANDATORY_QA_FULL=1 to execute')
            return True
        print(f'FAIL (scaffold missing file): {sid}')
        return not suite.get('blocking', False)

    command = suite.get('command')
    path = suite.get('path')
    if command:
        return run_cmd(command, label)
    if path:
        cmd = [sys.executable, '-m', 'pytest', path, '-q', '-m', 'mandatory']
        return run_cmd(cmd, label)
    print(f'WARN: suite {sid} has no command or path')
    return True


def run_phase(manifest: dict, phase: str) -> bool:
    suites = [s for s in (manifest.get('suites') or []) if s.get('phase') == phase]
    ok = True
    for suite in suites:
        passed = run_suite(suite)
        if not passed and suite.get('blocking', True):
            ok = False
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description='Mandatory NST QA orchestrator')
    parser.add_argument(
        '--phase',
        choices=['every_code_change', 'pre_release', 'all'],
        default='pre_release',
    )
    args = parser.parse_args()

    if not MANIFEST.is_file():
        print(f'FAIL: {MANIFEST} not found')
        return 1

    manifest = load_manifest()
    print(f"Mandatory QA manifest v{manifest.get('version')} — phase={args.phase}")

    ok = True
    if args.phase in ('every_code_change', 'all'):
        ok &= run_phase(manifest, 'every_code_change')
    if args.phase in ('pre_release', 'all'):
        ok &= run_phase(manifest, 'pre_release')

    # Optional full pytest when shipping
    if args.phase in ('pre_release', 'all') and os.environ.get('NST_QA_FULL_PYTEST'):
        ok &= run_cmd([sys.executable, '-m', 'pytest', 'tests/', '-q', '--tb=no'], 'pytest full suite')

    print('\n' + '=' * 60)
    if ok:
        print('MANDATORY RELEASE QA: PASS')
        return 0
    print('MANDATORY RELEASE QA: FAIL')
    return 1


if __name__ == '__main__':
    sys.exit(main())
