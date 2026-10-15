#!/usr/bin/env python3
"""Reality-loop device-fidelity — collect evidence (no secrets, not live)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'review_folder' / '2026.08.22' / 'QA' / 'reality_loop_device_fidelity_pass'

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run(cmd: list[str], log: Path) -> int:
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        f'$ {" ".join(cmd)}\n\nstdout:\n{p.stdout}\n\nstderr:\n{p.stderr}\nexit:{p.returncode}\n',
        encoding='utf-8',
    )
    return p.returncode


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for sub in ('pytest', 'readiness', 'packaging', 'maps', 'browser', 'fixtures'):
        (OUT / sub).mkdir(exist_ok=True)

    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    py = sys.executable
    summary = {
        'pass': 'reality_loop_device_fidelity_pass',
        'evidence_class': 'fixture/replay/device-like — not live',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'version': version,
        'platform': sys.platform,
        'runs': [],
    }

    steps = [
        ([py, 'scripts/validate_mandatory_qa_manifest.py'], OUT / 'pytest' / 'manifest.txt'),
        ([py, 'scripts/phase5_discovery_readiness_check.py'], OUT / 'readiness' / 'checker.txt'),
        ([py, 'scripts/phase5_discovery_release_consumer.py'], OUT / 'readiness' / 'consumer.txt'),
        ([py, '_prebuild.py'], OUT / 'packaging' / 'prebuild.txt'),
        ([py, '-m', 'pytest', 'tests/test_reality_loop_device_fidelity.py',
          'tests/test_reality_loop_api_contracts.py', '-q'], OUT / 'pytest' / 'reality_loop.txt'),
    ]
    for cmd, log in steps:
        rc = _run(cmd, log)
        summary['runs'].append({'cmd': cmd, 'exit': rc, 'log': str(log.relative_to(ROOT))})

    try:
        import tempfile
        from utils.discovery_map_formatter import generate_discovery_html
        from modules.plugins import network_discovery as nd

        # Incomplete observation map — must not draw cables
        fix = ROOT / 'tests' / 'fixtures' / 'discovery' / 'phase5_ios_cdp_detail_truncated_no_interface.txt'
        raw = nd._parse_cisco_cdp_detail(fix.read_text(encoding='utf-8'), 'EDGE', None)
        fin = nd._finalize_neighbor(dict(raw[0]))
        nodes_inc = [{
            'id': 'EDGE-01', 'ip': '10.0.0.1', 'device_type': 'cisco_ios',
            'depth': 0, 'is_scanned': True, 'scan_state': 'scanned',
            'incomplete_observations': [fin],
        }]
        # Device-like wrap → eligible edges after finalize
        wrap = ROOT / 'tests' / 'fixtures' / 'discovery' / 'legacy_ios12_cdp_brief_wrapped_device_id.txt'
        wrap_ns = nd._parse_cisco_cdp_brief(wrap.read_text(encoding='utf-8'), 'EDGE-01', None)
        edges = []
        for n in wrap_ns:
            f = nd._finalize_neighbor(dict(n))
            if not f or not f.get('edge_eligible'):
                continue
            edges.append({
                'from': 'EDGE-01', 'to': f['hostname'],
                'f_port': f['local_port'], 't_port': f['remote_port'],
                'protocol': 'CDP', 'sources': ['CDP'],
                'parse_source': 'brief', 'evidence_class': 'fixture',
            })
            nodes_inc.append({
                'id': f['hostname'], 'ip': '', 'device_type': 'cisco_ios',
                'depth': 1, 'is_scanned': False, 'scan_state': 'neighbor_only',
            })
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / 'incomplete.html'
            generate_discovery_html(str(p1), nodes_inc[:1], [])
            shutil.copy(p1, OUT / 'maps' / 'incomplete_observation_no_edges.html')
            p2 = Path(td) / 'wrap.html'
            generate_discovery_html(str(p2), [
                nodes_inc[0],
                *[n for n in nodes_inc[1:]],
            ], edges)
            shutil.copy(p2, OUT / 'maps' / 'legacy_ios12_wrapped_cdp_brief.html')
        summary['sample_maps'] = 'ok'
        summary['wrap_edge_count'] = len(edges)
    except Exception as exc:
        (OUT / 'maps' / 'sample_map_error.txt').write_text(str(exc), encoding='utf-8')
        summary['sample_maps'] = f'error:{exc}'

    fx_dir = ROOT / 'tests' / 'fixtures' / 'discovery'
    for name in (
        'legacy_ios12_cdp_brief_wrapped_device_id.txt',
        'legacy_ios12_lldp_detail_local_interface.txt',
        'legacy_nxos_lldp_detail_mac_prefix.txt',
        'legacy_junos11_lldp_brief_no_parent.txt',
        'device_like_nxos_lldp_brief_device_id_first.txt',
        'legacy_ios_cdp_detail_ipv4_and_blank_ip.txt',
    ):
        src = fx_dir / name
        if src.is_file():
            shutil.copy(src, OUT / 'fixtures' / name)

    spec = ROOT / f'NetworkSwissToolPro_v{version}.spec'
    summary['packaging'] = {
        'spec_exists': spec.is_file(),
        'spec_path': str(spec.relative_to(ROOT)) if spec.is_file() else None,
        'windows_exe_note': (
            'Windows .exe requires PyInstaller on Windows. '
            'This host cannot produce a Windows offline EXE.'
        ),
        'traffic_maps': 'not_implemented',
    }
    (OUT / 'packaging' / 'packaging_status.json').write_text(
        json.dumps(summary['packaging'], indent=2) + '\n', encoding='utf-8',
    )
    (OUT / 'SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
