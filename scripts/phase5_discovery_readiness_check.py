#!/usr/bin/env python3
"""Phase 5 discovery readiness honesty check (offline).

Validates ``tests/qa/PHASE5_DISCOVERY_READINESS.json`` so release / enterprise
gates cannot silently claim live vendor or operational readiness without a
retained live harness artifact.

Exit 0 = register is honest for current checkout.
Exit 1 = register overclaims or is inconsistent.
Exit 2 = register missing / unreadable.

Slice 10: always emits ``release_gate`` as PASS or BLOCKED (never a soft warning).
``ok: true`` with ``release_gate: BLOCKED`` means the register is honest and
enterprise ship for this path remains blocked — that is expected until live evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTER = ROOT / 'tests' / 'qa' / 'PHASE5_DISCOVERY_READINESS.json'

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_SKIP = 2

# Soft / ambiguous readiness language is a hard fail (Slice 10)
_SOFT_READY_RE = re.compile(
    r'\b('
    r'almost ready|nearly ready|practically ready|soft ready|'
    r'ready soon|conditionally enterprise ready|enterprise.?ready.?ish|'
    r'warning only|optional gate|soft warning'
    r')\b',
    re.I,
)


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _check(reg: Dict[str, Any], root: Path) -> List[str]:
    errors: List[str] = []
    if reg.get('schema') != 'nst.phase5.discovery_readiness.v1':
        errors.append(f"unexpected schema: {reg.get('schema')!r}")

    live_ok = bool(reg.get('live_vendor_truncated_cdp_lldp_validated'))
    ent_ok = bool(reg.get('enterprise_operational_ready'))
    evidence = (reg.get('evidence_paths') or {}).get('live_evidence_artifact')

    if ent_ok and not live_ok:
        errors.append(
            'enterprise_operational_ready=true requires '
            'live_vendor_truncated_cdp_lldp_validated=true'
        )

    if live_ok:
        if not evidence:
            errors.append(
                'live_vendor_truncated_cdp_lldp_validated=true requires '
                'evidence_paths.live_evidence_artifact'
            )
        else:
            art = root / str(evidence)
            if not art.is_file():
                errors.append(f'live evidence artifact missing: {art}')
            else:
                try:
                    data = json.loads(art.read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f'live evidence unreadable: {exc}')
                else:
                    if data.get('mode') != 'live_ssh':
                        errors.append(
                            f"live evidence mode must be live_ssh, got {data.get('mode')!r}"
                        )
                    if not data.get('live_vendor_validated'):
                        errors.append(
                            'live evidence must set live_vendor_validated=true'
                        )
    else:
        if evidence not in (None, '', False):
            errors.append(
                'live_evidence_artifact must be null while '
                'live_vendor_truncated_cdp_lldp_validated is false'
            )

    for claim in reg.get('forbidden_claims_until_live') or []:
        if not str(claim).strip():
            errors.append('empty forbidden claim entry')

    for row in reg.get('proven') or []:
        if (row.get('evidence_class') or '') == 'live-lab-backed':
            errors.append(
                f"proven capability {row.get('capability')!r} must not claim "
                'live-lab-backed until live validation exists'
            )

    unproven_caps = {r.get('capability') for r in (reg.get('unproven') or [])}
    if 'live_truncated_cdp_lldp_ssh' not in unproven_caps and not live_ok:
        errors.append('unproven must list live_truncated_cdp_lldp_ssh while live is false')

    replay = (reg.get('evidence_paths') or {}).get('replay_pack')
    if replay:
        rp = root / str(replay)
        if not rp.is_file():
            errors.append(f'replay_pack missing: {rp}')
        else:
            pack = json.loads(rp.read_text(encoding='utf-8'))
            if pack.get('live_vendor_validated') is True:
                errors.append('replay pack must not set live_vendor_validated=true')

    # Slice 10 — operator summary + anti-soft-language
    op_sum = str(reg.get('operator_summary') or '').strip()
    if not op_sum:
        errors.append('operator_summary is required (non-empty)')
    else:
        low = op_sum.lower()
        if (
            'enterprise operational ready: no' not in low
            and 'not enterprise operational ready' not in low
        ):
            errors.append(
                'operator_summary must explicitly state enterprise operational ready is NO'
            )
        if 'not validated' not in low and 'not live vendor' not in low:
            errors.append(
                'operator_summary must explicitly negate live truncated/vendor validation'
            )
        if 'blocked' not in low:
            errors.append('operator_summary must state release gate BLOCKED (or blocked)')
        if _SOFT_READY_RE.search(op_sum):
            errors.append(f'operator_summary uses soft readiness language: {op_sum!r}')

    for field in ('verdict',):
        text = str(reg.get(field) or '')
        if text and _SOFT_READY_RE.search(text):
            errors.append(f'{field} uses soft readiness language: {text!r}')

    if not ent_ok:
        if str(reg.get('release_gate_when_not_ready') or '').upper() != 'BLOCKED':
            errors.append(
                'release_gate_when_not_ready must be BLOCKED when not enterprise ready'
            )

    return errors


def _release_gate(reg: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    ent_ok = bool(reg.get('enterprise_operational_ready'))
    live_ok = bool(reg.get('live_vendor_truncated_cdp_lldp_validated'))
    if errors:
        gate = {
            'release_gate': 'FAIL',
            'release_gate_severity': 'hard',
            'release_gate_reason': 'readiness register inconsistent or overclaiming',
        }
    elif ent_ok and live_ok:
        gate = {
            'release_gate': 'PASS',
            'release_gate_severity': 'hard',
            'release_gate_reason': (
                'enterprise_operational_ready and live_vendor evidence accepted'
            ),
        }
    else:
        gate = {
            'release_gate': 'BLOCKED',
            'release_gate_severity': 'hard',
            'release_gate_reason': (
                'enterprise_operational_ready=false; '
                'live_vendor_truncated_cdp_lldp_validated=false — '
                'not a soft warning'
            ),
        }

    # Slice 11 — unambiguous consumer contract (ok alone is never enough)
    rg = gate['release_gate']
    hard_stop = rg in ('BLOCKED', 'FAIL')
    gate.update({
        'hard_stop': hard_stop,
        'ok_alone_insufficient_for_enterprise_claim': True,
        'may_claim_enterprise_ready': rg == 'PASS',
        'may_claim_live_vendor_validated': rg == 'PASS',
        'consumer_rule': (
            'Treat release_gate==PASS as the only clearance for enterprise/live '
            'claims. ok==true means register honesty only. '
            'release_gate==BLOCKED is a hard stop, never advisory.'
        ),
    })
    return gate


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Phase 5 discovery readiness check')
    parser.add_argument('--register', default=str(DEFAULT_REGISTER))
    parser.add_argument('--json-out', default='')
    parser.add_argument(
        '--require-release-pass',
        action='store_true',
        help=(
            'Exit 1 unless release_gate==PASS. Use when claiming enterprise '
            'ready / live vendor validated. Default mode allows ok=true with '
            'BLOCKED (honesty) and still exits 0.'
        ),
    )
    args = parser.parse_args(argv)

    path = Path(args.register)
    if not path.is_file():
        print(json.dumps({
            'ok': False,
            'error': f'register missing: {path}',
            'enterprise_operational_ready': False,
            'live_vendor_truncated_cdp_lldp_validated': False,
            'release_gate': 'FAIL',
            'release_gate_severity': 'hard',
            'hard_stop': True,
            'may_claim_enterprise_ready': False,
            'may_claim_live_vendor_validated': False,
            'ok_alone_insufficient_for_enterprise_claim': True,
        }, indent=2))
        return EXIT_SKIP

    reg = _load(path)
    errors = _check(reg, ROOT)
    gate = _release_gate(reg, errors)
    summary = {
        'ok': not errors,
        'register': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        'enterprise_operational_ready': bool(reg.get('enterprise_operational_ready')),
        'live_vendor_truncated_cdp_lldp_validated': bool(
            reg.get('live_vendor_truncated_cdp_lldp_validated')
        ),
        'verdict': reg.get('verdict'),
        'operator_summary': reg.get('operator_summary'),
        'errors': errors,
        'result_authority': 'phase5_discovery_readiness_register',
        'honesty': (
            'NOT enterprise operational ready — NOT live vendor validated'
            if not reg.get('enterprise_operational_ready')
            else 'register claims enterprise operational ready'
        ),
        **gate,
    }
    print(json.dumps(summary, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, indent=2) + '\n', encoding='utf-8',
        )

    if errors:
        return EXIT_FAIL
    if args.require_release_pass and gate.get('release_gate') != 'PASS':
        return EXIT_FAIL
    return EXIT_OK


if __name__ == '__main__':
    raise SystemExit(main())
