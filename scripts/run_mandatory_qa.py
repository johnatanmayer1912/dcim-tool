#!/usr/bin/env python3
"""
Mandatory QA gate runner for NLAP.

Runs tests/mandatory/ — required before release and after substantive code changes.
Council skill: .cursor/skills/nlap-release-council/

Usage:
  python scripts/run_mandatory_qa.py --manifest-check   # sync only
  python scripts/run_mandatory_qa.py --list            # list lenses
  python scripts/run_mandatory_qa.py                   # run mandatory pytest
  python scripts/run_mandatory_qa.py --dry-run         # show command only
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.mandatory_qa_registry import (  # noqa: E402
    count_scenarios,
    list_lens_modules,
    load_manifest,
    validate_manifest_sync,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='NLAP mandatory QA gate')
    parser.add_argument('--manifest-check', action='store_true', help='Validate MANIFEST.yaml sync only')
    parser.add_argument('--list', action='store_true', help='List registered lenses and scenarios')
    parser.add_argument('--dry-run', action='store_true', help='Print pytest command without executing')
    args = parser.parse_args()

    ok, errors = validate_manifest_sync()
    if not ok:
        print('MANDATORY QA MANIFEST CHECK FAILED')
        for err in errors:
            print(f'  - {err}')
        return 1
    print('MANDATORY QA MANIFEST CHECK PASSED')

    if args.manifest_check:
        manifest = load_manifest()
        print(f"  Lenses: {len(manifest.get('lenses', []))}")
        print(f"  Registered scenarios: {count_scenarios(manifest)}")
        return 0

    if args.list:
        manifest = load_manifest()
        for lens in manifest.get('lenses', []) or []:
            scenarios = lens.get('scenarios') or []
            print(f"\n[{lens.get('id')}] {lens.get('module')} ({len(scenarios)} scenarios)")
            for sc in scenarios:
                print(f"  - {sc.get('id')}: {sc.get('scenario')}")
        return 0

    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/mandatory/',
        '-m', 'mandatory',
        '-v', '--tb=short',
    ]
    if args.dry_run:
        print('DRY RUN — would execute:')
        print(' '.join(cmd))
        return 0

    print('Running mandatory QA suite...')
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
