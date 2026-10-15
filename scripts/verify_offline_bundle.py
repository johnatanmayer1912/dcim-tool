#!/usr/bin/env python3
"""Verify PyInstaller one-file EXE contains required offline enterprise assets."""
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_DATA = [
    'modules/web/templates/index.html',
    'modules/web/templates/pcap_flow_infographic.html',
    'modules/web/vis-network.min.js',  # inlined into Swiss Tools topology HTML exports only
    'static/css/bootstrap.min.css',
    'config/app_config.yaml',
    'policies/standards.yaml',
    'demos/logs/nxos_interface_down.lab',
    'docs/00-overview/HOW_TO_GUIDE.md',
    'docs/00-overview/OPERATOR_INVESTIGATION_GUIDE.md',
    'docs/00-overview/THREAT_MODEL.md',
    'docs/11-release-management/RELEASE_NOTES_5.5.0.md',
    'VERSION',
    'CHANGELOG.md',
    'inventory/inventory.txt',
]

REQUIRED_PYC_FRAGMENTS = [
    'modules/config_translator/config_comparator',
    'modules/web/investigation_routes',
    'modules/web/config_translator_routes',
    'modules/web/credential_routes',
    'modules/web/pcap_routes',
    'utils/api_security',
    'utils/health_check_runner',
    'modules/investigation/service',
    'modules/investigation/log_collectors',
    'modules/analysis/incident_runbook',
    'modules/analysis/interface_counter_verdict',
    'modules/analysis/evidence_conclusions',
    'modules/analysis/incident_reconciliation',
    'modules/analysis/adaptive_collection',
]


def _norm(key: str) -> str:
    return key.replace('\\', '/')


def audit_exe(exe_path: Path) -> list[str]:
    from PyInstaller.archive.readers import CArchiveReader

    failures: list[str] = []
    if not exe_path.is_file():
        return [f'EXE not found: {exe_path}']

    arch = CArchiveReader(str(exe_path))
    keys = {_norm(k) for k in arch.toc.keys()}

    for req in REQUIRED_DATA:
        if not any(req in k for k in keys):
            failures.append(f'Missing data asset: {req}')

    for frag in REQUIRED_PYC_FRAGMENTS:
        if not any(frag in k for k in keys):
            failures.append(f'Missing module bytecode: {frag}')

    py_dll = [k for k in keys if 'python3' in k.lower() and k.endswith('.dll')]
    if not py_dll:
        failures.append('Missing embedded python3*.dll runtime')

    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    exe = root / 'dist' / 'NetworkLogAnalysisPlatform_v5.3.10_OFFLINE.exe'
    if len(sys.argv) > 1:
        exe = Path(sys.argv[1])

    print(f'Auditing offline bundle: {exe.name}')
    failures = audit_exe(exe)
    if failures:
        print('BUNDLE AUDIT FAILED:')
        for f in failures:
            print(f'  - {f}')
        return 1
    print('BUNDLE AUDIT PASSED — required offline assets present')
    return 0


if __name__ == '__main__':
    sys.exit(main())
