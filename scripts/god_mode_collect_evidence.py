#!/usr/bin/env python3
"""God-mode enterprise QA — collect evidence into review folder (no secrets)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'review_folder' / '2026.08.22' / 'QA' / 'god_mode_enterprise_pass'

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
    for sub in ('pytest', 'readiness', 'packaging', 'maps', 'browser'):
        (OUT / sub).mkdir(exist_ok=True)

    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    py = sys.executable
    summary = {
        'pass': 'god_mode_enterprise_pass',
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
    ]
    for cmd, log in steps:
        rc = _run(cmd, log)
        summary['runs'].append({'cmd': cmd, 'exit': rc, 'log': str(log.relative_to(ROOT))})

    try:
        import tempfile
        from utils.discovery_map_formatter import generate_discovery_html
        from modules.plugins import network_discovery as nd

        fix = ROOT / 'tests' / 'fixtures' / 'discovery' / 'phase5_ios_cdp_detail_truncated_no_interface.txt'
        raw = nd._parse_cisco_cdp_detail(fix.read_text(encoding='utf-8'), 'EDGE', None)
        fin = nd._finalize_neighbor(dict(raw[0]))
        nodes = [{
            'id': 'EDGE-01', 'ip': '10.0.0.1', 'device_type': 'cisco_ios',
            'depth': 0, 'is_scanned': True, 'scan_state': 'scanned',
            'incomplete_observations': [fin],
        }]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'sample_discovery.html'
            generate_discovery_html(str(path), nodes, [])
            shutil.copy(path, OUT / 'maps' / 'sample_discovery_command_center.html')
        summary['sample_map'] = 'ok'
    except Exception as exc:
        (OUT / 'maps' / 'sample_map_error.txt').write_text(str(exc), encoding='utf-8')
        summary['sample_map'] = f'error:{exc}'

    for name in (
        'ENTERPRISE_READINESS_QA_2026-08-22.md',
        'LIVE_LAB_EVIDENCE_FAILURE_CLOSEOUT_2026-08-21.md',
    ):
        src = ROOT / 'reports' / name
        if src.is_file():
            shutil.copy(src, OUT / 'readiness' / name)

    spec = ROOT / f'NetworkSwissToolPro_v{version}.spec'
    summary['packaging'] = {
        'spec_exists': spec.is_file(),
        'spec_path': str(spec.relative_to(ROOT)) if spec.is_file() else None,
        'windows_exe_note': (
            'Windows .exe requires PyInstaller on Windows (Python 3.12 venv). '
            'macOS build produces a macOS binary only.'
        ),
    }
    (OUT / 'packaging' / 'packaging_status.json').write_text(
        json.dumps(summary['packaging'], indent=2) + '\n', encoding='utf-8',
    )

    (OUT / 'GOD_MODE_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (OUT / 'README.md').write_text(
        f"""# God-mode enterprise QA pass — {version}

Generated: {summary['timestamp_utc']}  
Host: `{sys.platform}`

## Index

- `GOD_MODE_SUMMARY.json` — run metadata
- `pytest/manifest.txt` — mandatory manifest validation
- `readiness/` — checker, consumer, prior reports
- `packaging/prebuild.txt` — prebuild gate output
- `maps/sample_discovery_command_center.html` — fixture map (incomplete obs, not edges)

## Utilization / Shumoku-style traffic maps

**Not implemented.** UI states no SNMP utilization in this release. Overlay layer is NVE/EVPN CLI peers only (not cables). Link issues are witnesses, not cable certification.

## Windows offline EXE

Use `NetworkSwissToolPro_v{version}.spec` on a **Windows** build host. Prebuild must pass first.

## Release gate

`release_gate: BLOCKED` until retained live_ssh PASS-eligible evidence exists.
""",
        encoding='utf-8',
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
