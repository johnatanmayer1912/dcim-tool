#!/usr/bin/env python3
"""Release smoke tests for NLAP offline EXE / dev server (health + config compare API)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get('NLAP_SMOKE_URL', 'http://127.0.0.1:6061')


def _get(path: str) -> tuple[int, dict]:
    req = urllib.request.Request(f'{BASE}{path}')
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf-8', errors='replace')
        try:
            return resp.status, json.loads(body)
        except json.JSONDecodeError:
            return resp.status, {'raw': body}


def _post_json(path: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'{BASE}{path}',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))


def main() -> int:
    failures = []
    print(f'Smoke testing {BASE} …')

    try:
        code, _ = _get('/health')
        if code != 200:
            failures.append(f'/health returned {code}')
        else:
            print('  OK  /health')
    except Exception as exc:
        failures.append(f'/health: {exc}')

    try:
        code, data = _get('/api/health-check/run?quick=1')
        if code != 200 or 'checks' not in data:
            failures.append(f'health-check: {code} {data}')
        else:
            print('  OK  /api/health-check/run')
    except Exception as exc:
        failures.append(f'health-check: {exc}')

    baseline = 'hostname golden\ninterface Ethernet1/1\n  no shutdown\n'
    candidate = 'hostname golden\ninterface Ethernet1/2\n  no shutdown\n'
    try:
        code, data = _post_json('/api/config-translator/compare', {
            'config_a': baseline,
            'config_b': candidate,
        })
        if code != 200 or data.get('status') != 'success':
            failures.append(f'config compare: {code} {data}')
        else:
            print(f'  OK  config compare ({data.get("stats", {}).get("total_gaps", 0)} gaps)')
    except Exception as exc:
        failures.append(f'config compare: {exc}')

    if failures:
        print('SMOKE FAILED:')
        for f in failures:
            print(' -', f)
        return 1
    print('SMOKE PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
