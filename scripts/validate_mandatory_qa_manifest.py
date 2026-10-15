#!/usr/bin/env python3
"""Validate tests/qa/MANDATORY_MANIFEST.yaml — file integrity gate."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'tests' / 'qa' / 'MANDATORY_MANIFEST.yaml'


def load_manifest():
    try:
        import yaml
    except ImportError:
        print('FAIL: PyYAML required to parse MANDATORY_MANIFEST.yaml')
        return None
    if not MANIFEST.is_file():
        print(f'FAIL: missing {MANIFEST}')
        return None
    return yaml.safe_load(MANIFEST.read_text(encoding='utf-8'))


def validate(manifest: dict) -> bool:
    ok = True
    suites = manifest.get('suites') or []
    seen_ids = set()
    for suite in suites:
        sid = suite.get('id')
        if not sid:
            print('FAIL: suite missing id')
            ok = False
            continue
        if sid in seen_ids:
            print(f'FAIL: duplicate suite id {sid}')
            ok = False
        seen_ids.add(sid)

        path = suite.get('path')
        command = suite.get('command')
        if path:
            p = ROOT / path.replace('/', '\\') if '\\' not in path else ROOT / path
            p = ROOT / path
            if not p.is_file():
                print(f'FAIL: suite {sid} missing file {path}')
                ok = False
        if command and not path:
            if command[0] in ('python', sys.executable):
                pass  # runtime command — checked at execute time
        owner = suite.get('owner')
        personas = manifest.get('personas') or {}
        if owner and owner not in personas:
            print(f'WARN: suite {sid} owner {owner} not in personas')

    council = manifest.get('council') or {}
    for key in ('skill', 'questionnaire'):
        rel = council.get(key)
        if rel and not (ROOT / rel).is_file():
            print(f'FAIL: council {key} missing {rel}')
            ok = False

    evo = (manifest.get('evolution_policy') or {}).get('doc')
    if evo and not (ROOT / evo).is_file():
        print(f'FAIL: evolution_policy doc missing {evo}')
        ok = False

    version = manifest.get('minimum_app_version')
    ver_file = (ROOT / 'VERSION').read_text(encoding='utf-8').strip() if (ROOT / 'VERSION').is_file() else ''
    if version and ver_file and version != ver_file:
        print(f'WARN: manifest minimum_app_version {version} != VERSION {ver_file} — update manifest on release')

    if ok:
        print(f'OK: mandatory QA manifest valid ({len(suites)} suites, version {manifest.get("version")})')
    return ok


def main() -> int:
    manifest = load_manifest()
    if manifest is None:
        return 1
    return 0 if validate(manifest) else 1


if __name__ == '__main__':
    sys.exit(main())
