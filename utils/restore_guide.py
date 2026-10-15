"""Manual restore guidance for pre-change backups (no auto line-by-line restore)."""
from __future__ import annotations

import os
from typing import Any, Dict


def get_manual_restore_guide(
    backup_path: str,
    device_type: str = '',
    context: str = 'configuration change',
) -> Dict[str, Any]:
    """
    Return operator-facing restore steps. Automated restore was removed (v6.5.4)
    because blind paste corrupts NX-OS/Junos configs.
    """
    dtype = (device_type or '').lower()
    path = os.path.abspath(backup_path) if backup_path else ''
    exists = bool(path and os.path.isfile(path))

    if 'juniper' in dtype or 'junos' in dtype:
        steps = [
            f'1. Open backup file: {path}',
            '2. SSH to device and enter configure mode',
            '3. load override /path/to/backup.txt   (or paste via load merge after review)',
            '4. show | compare',
            '5. commit confirmed if diff is correct',
        ]
        vendor = 'Juniper Junos'
    elif 'nxos' in dtype:
        steps = [
            f'1. Copy backup to bootflash on device: {path}',
            '2. configure replace bootflash:backup-file force',
            '3. copy running-config startup-config',
        ]
        vendor = 'Cisco NX-OS'
    else:
        steps = [
            f'1. Review backup file offline: {path}',
            '2. Use configure replace flash:backup.cfg (IOS-XE) or archive rollback (if enabled)',
            '3. Never paste line-by-line from backup without diff review',
            '4. write memory after verification',
        ]
        vendor = 'Cisco IOS/IOS-XE'

    return {
        'automated_restore_available': False,
        'backup_path': path,
        'backup_exists': exists,
        'context': context,
        'vendor': vendor,
        'manual_steps': steps,
        'notice': (
            'Network Swiss Tool Pro saves pre-change backups only. '
            'Restore is manual — automated rollback was removed for safety (v6.5.4).'
        ),
    }
