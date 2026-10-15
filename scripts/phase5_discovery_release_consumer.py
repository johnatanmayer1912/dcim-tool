#!/usr/bin/env python3
"""Phase 5 discovery release-gate consumer (normative interpretation).

Single downstream consumer contract for readiness JSON:

- ``ok==true`` means the register is honest — not enterprise clearance.
- ``release_gate==BLOCKED`` is a hard stop (``hard_stop`` must be true).
- Enterprise/live claims require ``release_gate==PASS`` (use
  ``--require-release-pass``).

Exit 0 = consumer contract held (BLOCKED+hard_stop is valid and expected).
Exit 1 = consumer contract broken or soft interpretation detected.
Exit 2 = upstream checker missing / unreadable.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / 'scripts' / 'phase5_discovery_readiness_check.py'

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_SKIP = 2

_SOFT_WORDS = (
    'advisory',
    'soft warning',
    'almost ready',
    'nearly ready',
    'optional',
    'informational only',
)


def _load_payload(path: Path | None) -> Dict[str, Any]:
    if path is not None:
        return json.loads(path.read_text(encoding='utf-8'))
    proc = subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    start = proc.stdout.find('{')
    if start < 0:
        raise RuntimeError(f'checker produced no JSON: {proc.stdout!r}')
    data = json.loads(proc.stdout[start:])
    data['_checker_exit'] = proc.returncode
    return data


def _validate_consumer(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    rg = str(data.get('release_gate') or '')
    severity = str(data.get('release_gate_severity') or '')
    hard_stop = data.get('hard_stop')
    may_ent = data.get('may_claim_enterprise_ready')
    may_live = data.get('may_claim_live_vendor_validated')
    ok_alone = data.get('ok_alone_insufficient_for_enterprise_claim')

    if rg not in ('PASS', 'BLOCKED', 'FAIL'):
        errors.append(f'unknown release_gate: {rg!r}')

    if severity != 'hard':
        errors.append(
            f'release_gate_severity must be hard, got {severity!r} '
            '(soft/advisory severity forbidden)'
        )

    if rg in ('BLOCKED', 'FAIL'):
        if hard_stop is not True:
            errors.append('hard_stop must be true when release_gate is BLOCKED/FAIL')
        if may_ent is not False:
            errors.append('may_claim_enterprise_ready must be false when not PASS')
        if may_live is not False:
            errors.append('may_claim_live_vendor_validated must be false when not PASS')

    if rg == 'PASS':
        if hard_stop is True:
            errors.append('hard_stop must be false when release_gate is PASS')
        if may_ent is not True or may_live is not True:
            errors.append('PASS requires may_claim_enterprise_ready and live true')

    if ok_alone is not True:
        errors.append('ok_alone_insufficient_for_enterprise_claim must be true')

    rule = str(data.get('consumer_rule') or '').lower()
    if 'hard stop' not in rule and 'never advisory' not in rule:
        errors.append('consumer_rule must state hard stop / never advisory')

    blob = ' '.join([
        str(data.get('honesty') or ''),
        str(data.get('operator_summary') or ''),
        str(data.get('release_gate_reason') or ''),
        rule,
    ]).lower()
    for word in _SOFT_WORDS:
        if word in blob and rg == 'BLOCKED':
            if word == 'soft warning' and (
                'not a soft warning' in blob or 'never a soft warning' in blob
            ):
                continue
            if word == 'advisory' and (
                'never advisory' in blob or 'not advisory' in blob
            ):
                continue
            errors.append(f'soft interpretation language in consumer payload: {word!r}')

    # ok alone must never imply clearance
    if data.get('ok') is True and rg == 'BLOCKED' and may_ent is True:
        errors.append('ok=true must not pair with may_claim_enterprise_ready=true under BLOCKED')

    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Phase 5 discovery release-gate consumer contract',
    )
    parser.add_argument(
        '--from-json',
        default='',
        help='Read checker JSON artifact instead of invoking the checker',
    )
    parser.add_argument('--json-out', default='')
    parser.add_argument(
        '--require-release-pass',
        action='store_true',
        help='Exit 1 unless release_gate==PASS (enterprise/live claim mode)',
    )
    args = parser.parse_args(argv)

    try:
        src = Path(args.from_json) if args.from_json.strip() else None
        data = _load_payload(src)
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(json.dumps({
            'ok': False,
            'error': str(exc),
            'release_gate': 'FAIL',
            'hard_stop': True,
        }, indent=2))
        return EXIT_SKIP

    errors = _validate_consumer(data)
    rg = str(data.get('release_gate') or '')
    summary = {
        'ok': not errors,
        'consumer': 'phase5_discovery_release_consumer',
        'upstream_ok': bool(data.get('ok')),
        'release_gate': rg,
        'hard_stop': data.get('hard_stop'),
        'may_claim_enterprise_ready': data.get('may_claim_enterprise_ready'),
        'may_claim_live_vendor_validated': data.get('may_claim_live_vendor_validated'),
        'interpretation': (
            'HARD STOP — not advisory'
            if rg == 'BLOCKED'
            else ('RELEASE CLEARED' if rg == 'PASS' else 'CONSUMER FAIL')
        ),
        'errors': errors,
        'result_authority': 'phase5_discovery_readiness_register',
    }
    print(json.dumps(summary, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, indent=2) + '\n', encoding='utf-8',
        )

    if errors:
        return EXIT_FAIL
    if args.require_release_pass and rg != 'PASS':
        return EXIT_FAIL
    return EXIT_OK


if __name__ == '__main__':
    raise SystemExit(main())
