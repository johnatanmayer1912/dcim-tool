#!/usr/bin/env python3
"""Phase 5 authorized live-lab truncated CDP/LLDP check (read-only).

Authorization gate
------------------
Requires ``NST_PHASE5_LIVE_LAB=1``. Without it, exits 2 (skipped).

Modes
-----
1. Replay (preferred offline / CI):
   ``NST_PHASE5_LIVE_LAB_REPLAY=/path/to/capture.json``

2. Live SSH (operator lab only):
   ``NST_LAB_HOSTS=host1,host2``
   ``NST_LAB_USER=...``
   ``NST_LAB_PASSWORD=...``
   optional ``NST_LAB_SECRET=...`` (enable)
   optional ``NST_LAB_DEVICE_TYPE=cisco_ios`` (default cisco_ios)

Never reads ``.credential_key`` or vault files.
Never invents ports, hostnames, or edges.
Incomplete observations must stay edge_eligible=False.

Exit codes (authoritative)
--------------------------
0 = check completed and contract held (replay or live_ssh)
1 = check ran and contract failed
2 = skipped / not executed (unauthorized, missing prereqs, or TCP/22 down)

Replay ``ok: true`` with exit 0 proves parser/contract behavior only.
It does **not** mean live vendor validation (``live_vendor_validated`` stays false).

Non-authoritative noise
-----------------------
IDE/agent shell job timeout, backgrounding, or harness cancel after the process
already printed JSON with ``ok: true`` / exit 0 is **bookkeeping**, not a
pytest or contract failure. Judge success from process exit code + JSON
artifact, not from the outer shell-task status.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


EXIT_OK = 0
EXIT_FAIL = 1
EXIT_SKIP = 2


def _truthy(val: str | None) -> bool:
    return (val or '').strip().lower() in ('1', 'true', 'yes', 'on')


def _evaluate_output(
    *,
    host: str,
    device_type: str,
    command: str,
    output: str,
    parser_hint: str = '',
) -> Dict[str, Any]:
    from modules.plugins import network_discovery as nd

    cmd = (command or '').lower()
    dtype = (device_type or 'cisco_ios').lower()
    hint = (parser_hint or '').strip().lower()
    neighbors: List[dict] = []

    if hint in ('juniper_lldp_alternative', 'junos_lldp_alternative'):
        neighbors = nd._parse_juniper_lldp_alternative(output, host, None)
    elif 'cdp' in cmd and 'detail' in cmd:
        neighbors = nd._parse_cisco_cdp_detail(output, host, None)
    elif 'lldp' in cmd and 'detail' in cmd:
        if 'juniper' in dtype or 'junos' in dtype:
            neighbors = nd._parse_juniper_lldp_detail(output, host, None)
        else:
            neighbors = nd._parse_cisco_lldp_detail(output, host, None)
    elif 'lldp' in cmd:
        if 'juniper' in dtype or 'junos' in dtype:
            neighbors = nd._parse_juniper_lldp_brief(output, host, None)
        else:
            neighbors = nd._parse_cisco_lldp_brief(output, host, None)
    elif 'cdp' in cmd:
        neighbors = nd._parse_cisco_cdp_brief(output, host, None)
    else:
        return {
            'host': host,
            'command': command,
            'ok': False,
            'error': f'unsupported command for Phase 5 check: {command!r}',
            'errors': [f'unsupported command for Phase 5 check: {command!r}'],
            'complete_count': 0,
            'incomplete_count': 0,
            'incomplete_observations': [],
        }

    finalized = []
    incompletes = []
    completes = []
    for raw in neighbors:
        fin = nd._finalize_neighbor(dict(raw))
        if not fin:
            continue
        finalized.append(fin)
        if fin.get('incomplete') or fin.get('edge_eligible') is False:
            incompletes.append(fin)
        else:
            completes.append(fin)

    errors: List[str] = []
    for n in finalized:
        for key in ('local_port', 'remote_port', 'hostname'):
            val = str(n.get(key) or '')
            if val.lower() in ('unknown', 'n/a', 'n\\a'):
                errors.append(f'{host}: invented placeholder {key}={val!r}')
        if n.get('incomplete') and n.get('edge_eligible') is not False:
            errors.append(f'{host}: incomplete observation marked edge-eligible')

    low = output.lower()
    looks_truncated_cdp = (
        'device id' in low
        and 'interface:' not in low
        and 'port id (outgoing' not in low
    )
    looks_truncated_lldp = (
        ('chassis id' in low or 'system name' in low)
        and 'local intf' not in low
        and 'local port id' not in low
        and 'local interface' not in low
    )
    if looks_truncated_cdp or looks_truncated_lldp:
        if not incompletes and completes:
            errors.append(
                f'{host}: truncated-looking output produced only complete neighbors'
            )
        if not incompletes and not completes and looks_truncated_cdp:
            if 'device id' in low:
                errors.append(
                    f'{host}: truncated CDP produced silence instead of incomplete'
                )

    return {
        'host': host,
        'device_type': device_type,
        'command': command,
        'ok': not errors,
        'errors': errors,
        'complete_count': len(completes),
        'incomplete_count': len(incompletes),
        'incomplete_observations': [
            nd._operator_incomplete_observation(n) for n in incompletes
        ],
    }


def _load_replay(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('captures'), list):
        raise ValueError('replay JSON must be an object with captures[]')
    return [c for c in data['captures'] if isinstance(c, dict)]


def _run_live_ssh(
    hosts: List[str],
    user: str,
    password: str,
    secret: str,
    default_dtype: str,
) -> List[Dict[str, Any]]:
    from modules.network_base import safe_connection

    results = []
    for host in hosts:
        dtype = default_dtype
        device = {'host': host, 'device_type': dtype, 'port': 22}
        try:
            with safe_connection(device, user, password, secret or None, None) as conn:
                if 'juniper' in dtype or 'junos' in dtype:
                    cmd = 'show lldp neighbors detail'
                else:
                    cmd = 'show cdp neighbors detail'
                out = conn.send_command(cmd, read_timeout=90)
                results.append(_evaluate_output(
                    host=host,
                    device_type=dtype,
                    command=cmd,
                    output=out or '',
                ))
        except Exception as exc:
            results.append({
                'host': host,
                'command': 'ssh',
                'ok': False,
                'errors': [f'connection/command failed: {type(exc).__name__}'],
                'complete_count': 0,
                'incomplete_count': 0,
                'incomplete_observations': [],
            })
    return results


def _tcp_port_open(host: str, port: int = 22, timeout: float = 1.0) -> bool:
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_ssh_hosts(hosts: List[str]) -> Dict[str, Any]:
    reachable = [h for h in hosts if _tcp_port_open(h, 22)]
    unreachable = [h for h in hosts if h not in reachable]
    return {
        'reachable_hosts': reachable,
        'unreachable_hosts': unreachable,
        'any_reachable': bool(reachable),
    }


def _honesty_block(mode: str) -> Dict[str, Any]:
    live_validated = mode == 'live_ssh'
    return {
        'live_vendor_validated': live_validated,
        'execution_kind': mode,
        'honesty': (
            'live vendor truncated CDP/LLDP validated'
            if live_validated else
            'NOT live vendor validation — replay or not-executed only'
        ),
        'claims_forbidden_unless_live_ssh': [
            'live truncated CDP/LLDP vendor validation',
            'live field discovery success',
        ],
        # Slice 7–8: separate harness truth from IDE/agent shell bookkeeping
        'result_authority': 'process_exit_code_and_json_artifact',
        'non_authoritative_signals': [
            'IDE/agent shell timeout or background-job status',
            'pipeline cancel after process already exited 0 with ok=true',
        ],
    }


def _console_authority(mode: str, **extra: Any) -> Dict[str, Any]:
    """Stdout JSON always carries authority fields (Slice 8 operator clarity)."""
    honesty = _honesty_block(mode)
    out = {
        'mode': mode,
        'live_vendor_validated': honesty['live_vendor_validated'],
        'honesty': honesty['honesty'],
        'result_authority': honesty['result_authority'],
        'non_authoritative_signals': honesty['non_authoritative_signals'],
    }
    out.update(extra)
    return out


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Phase 5 live-lab truncated CDP/LLDP check',
    )
    parser.add_argument(
        '--replay',
        default=os.environ.get('NST_PHASE5_LIVE_LAB_REPLAY', ''),
    )
    parser.add_argument('--json-out', default='')
    args = parser.parse_args(argv)

    if not _truthy(os.environ.get('NST_PHASE5_LIVE_LAB')):
        print(json.dumps(_console_authority(
            'unauthorized_skip',
            ok=False,
            skipped=True,
        ), indent=2))
        print('SKIP: set NST_PHASE5_LIVE_LAB=1 to authorize this check')
        return EXIT_SKIP

    results: List[Dict[str, Any]] = []
    mode = 'none'
    probe: Dict[str, Any] = {}

    replay = (args.replay or '').strip()
    if replay:
        mode = 'replay'
        captures = _load_replay(Path(replay))
        for cap in captures:
            results.append(_evaluate_output(
                host=str(cap.get('host') or 'lab-host'),
                device_type=str(cap.get('device_type') or 'cisco_ios'),
                command=str(cap.get('command') or 'show cdp neighbors detail'),
                output=str(cap.get('output') or ''),
                parser_hint=str(cap.get('parser') or ''),
            ))
    else:
        hosts_raw = (os.environ.get('NST_LAB_HOSTS') or '').strip()
        user = (os.environ.get('NST_LAB_USER') or '').strip()
        password = os.environ.get('NST_LAB_PASSWORD') or ''
        secret = os.environ.get('NST_LAB_SECRET') or ''
        dtype = (os.environ.get('NST_LAB_DEVICE_TYPE') or 'cisco_ios').strip()
        hosts = [h.strip() for h in hosts_raw.split(',') if h.strip()]
        if not hosts or not user or password == '':
            print(json.dumps(_console_authority(
                'live_ssh_prereq_skip',
                ok=False,
                skipped=True,
            ), indent=2))
            print(
                'SKIP: live SSH requires NST_LAB_HOSTS, NST_LAB_USER, '
                'NST_LAB_PASSWORD (or use --replay / NST_PHASE5_LIVE_LAB_REPLAY)'
            )
            return EXIT_SKIP

        probe = _probe_ssh_hosts(hosts)
        if not probe['any_reachable']:
            mode = 'live_ssh_not_executed'
            summary = {
                'mode': mode,
                'authorized': True,
                'result_count': 0,
                'failed_count': 0,
                'results': [],
                'live_ssh_executed': False,
                'reachability': probe,
                'contract': (
                    'incomplete observations must not be edge-eligible; '
                    'no unknown/n/a ports'
                ),
                **_honesty_block(mode),
            }
            print(json.dumps(_console_authority(
                mode,
                reachability=probe,
                result_count=0,
                failed_count=0,
                incomplete_total=0,
                complete_total=0,
                ok=False,
                skipped=True,
                not_executed_reason=(
                    'all inventory/lab hosts unreachable on TCP/22'
                ),
            ), indent=2))
            if args.json_out:
                Path(args.json_out).write_text(
                    json.dumps(summary, indent=2) + '\n', encoding='utf-8',
                )
            print(
                'SKIP: live SSH not executed — all hosts unreachable '
                '(inventory down / SSH filtered). This is NOT a live pass.',
                file=sys.stderr,
            )
            return EXIT_SKIP

        # Only attempt SSH to hosts that accepted TCP/22
        mode = 'live_ssh'
        results = _run_live_ssh(
            probe['reachable_hosts'], user, password, secret, dtype,
        )

    failed = [r for r in results if not r.get('ok')]
    honesty = _honesty_block(mode)
    summary = {
        'mode': mode,
        'authorized': True,
        'result_count': len(results),
        'failed_count': len(failed),
        'results': results,
        'live_ssh_executed': mode == 'live_ssh',
        'reachability': probe or None,
        'contract': (
            'incomplete observations must not be edge-eligible; '
            'no unknown/n/a ports'
        ),
        **honesty,
    }
    print(json.dumps(_console_authority(
        mode,
        result_count=len(results),
        failed_count=len(failed),
        incomplete_total=sum(int(r.get('incomplete_count') or 0) for r in results),
        complete_total=sum(int(r.get('complete_count') or 0) for r in results),
        ok=not failed and mode in ('replay', 'live_ssh'),
    ), indent=2))
    for r in failed:
        for err in r.get('errors') or []:
            print(f"FAIL {r.get('host')}: {err}", file=sys.stderr)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, indent=2) + '\n', encoding='utf-8',
        )

    return EXIT_FAIL if failed else EXIT_OK


if __name__ == '__main__':
    raise SystemExit(main())
