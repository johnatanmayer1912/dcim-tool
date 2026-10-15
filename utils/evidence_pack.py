"""Build evidence ZIP packs from job_index-contained run folders.

Learned from Oxidized/LibreNMS "export the run pack" operator habit:
operators need a shareable artifact for managers without exposing vault secrets.
Only files under a contained outputs/ run_dir are included.
"""
from __future__ import annotations

import io
import os
import zipfile
from typing import Any, Dict, Optional, Tuple


MAX_FILES = 400
MAX_TOTAL_BYTES = 80 * 1024 * 1024  # 80 MiB soft cap
SKIP_SUFFIXES = ('.credential_key', '.key', '.pem', '.p12', '.pfx')
SKIP_NAMES = {'credentials.json', 'vault.json', '.credential_key'}


def build_job_pack(task_id: str) -> Tuple[Optional[io.BytesIO], Optional[str], Optional[Dict[str, Any]]]:
    """Return (buffer, download_name, meta) or (None, None, error_dict)."""
    from utils.job_index import contained_run_dir, get_job
    from utils.output_paths import get_data_root

    job = get_job(task_id)
    if not job:
        return None, None, {'error': 'Job not found', 'status': 404}
    if not job.get('artifacts_available'):
        return None, None, {'error': 'No artifacts on disk for this job', 'status': 404}

    rel = job.get('run_dir') or job.get('safe_path')
    if not rel:
        return None, None, {'error': 'Job has no contained run_dir', 'status': 404}
    checked = contained_run_dir(
        os.path.join(get_data_root(), *str(rel).replace('\\', '/').split('/'))
    )
    if not checked:
        return None, None, {'error': 'Run directory is outside outputs/', 'status': 403}

    abs_dir = os.path.abspath(os.path.join(get_data_root(), *checked.split('/')))
    if not os.path.isdir(abs_dir):
        return None, None, {'error': 'Run directory missing', 'status': 404}

    buf = io.BytesIO()
    file_count = 0
    total = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            '00_EVIDENCE_README.txt',
            (
                f'Network Swiss Tool Pro — Evidence pack\n'
                f'task_id={job.get("task_id")}\n'
                f'action={job.get("action")}\n'
                f'status={job.get("status")}\n'
                f'run_dir={checked}\n'
                f'Note: secrets are never stored in the job index; this zip only '
                f'includes files already written under the run folder.\n'
            ),
        )
        for root, _dirs, files in os.walk(abs_dir):
            for name in files:
                if name in SKIP_NAMES or name.lower().endswith(SKIP_SUFFIXES):
                    continue
                fp = os.path.abspath(os.path.join(root, name))
                try:
                    if os.path.commonpath([abs_dir, fp]) != abs_dir:
                        continue
                except ValueError:
                    continue
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    continue
                if size <= 0:
                    continue
                if total + size > MAX_TOTAL_BYTES:
                    break
                if file_count >= MAX_FILES:
                    break
                try:
                    arc = os.path.relpath(fp, abs_dir).replace('\\', '/')
                    if arc.startswith('..'):
                        continue
                    zf.write(fp, arcname=arc)
                    file_count += 1
                    total += size
                except OSError:
                    continue
            if file_count >= MAX_FILES or total >= MAX_TOTAL_BYTES:
                break

    buf.seek(0)
    safe_action = ''.join(c if c.isalnum() or c in '-_' else '_' for c in str(job.get('action') or 'job'))
    tid = str(job.get('task_id') or task_id)[:24]
    name = f'nst_evidence_{safe_action}_{tid}.zip'
    meta = {
        'task_id': job.get('task_id'),
        'action': job.get('action'),
        'run_dir': checked,
        'file_count': file_count,
        'bytes': total,
    }
    return buf, name, meta
