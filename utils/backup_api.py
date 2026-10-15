"""Safe config backup list/diff helpers (Oxidized-inspired, path-contained).

Never accept absolute paths from the client unless they resolve under the
configured backup root under get_data_root()/backups OR under outputs/config_backup.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple


def backup_root() -> str:
    from utils.output_paths import get_backups_root
    return os.path.abspath(get_backups_root())


def outputs_root() -> str:
    from utils.output_paths import get_outputs_root
    return os.path.abspath(get_outputs_root())


def contained_backup_path(path: Optional[str]) -> Optional[str]:
    """Return absolute path if under backups/ or outputs/config_backup/; else None."""
    if not path:
        return None
    raw = str(path).strip()
    if not raw or '\x00' in raw:
        return None
    roots = [backup_root()]
    try:
        roots.append(os.path.join(outputs_root(), 'config_backup'))
    except Exception:
        pass
    candidates = []
    if not os.path.isabs(raw):
        for root in roots:
            candidates.append(os.path.abspath(os.path.join(root, raw)))
            # also allow path relative to data root style: backups/... or outputs/...
        try:
            from utils.output_paths import get_data_root
            candidates.append(os.path.abspath(os.path.join(get_data_root(), raw)))
        except Exception:
            pass
    else:
        candidates.append(os.path.abspath(os.path.normpath(raw)))

    for cand in candidates:
        for root in roots:
            try:
                if os.path.commonpath([root, cand]) == root and os.path.isfile(cand):
                    return cand
            except ValueError:
                continue
        # outputs/config_backup specifically
        try:
            cfg_root = os.path.join(outputs_root(), 'config_backup')
            if os.path.commonpath([cfg_root, cand]) == cfg_root and os.path.isfile(cand):
                return cand
        except ValueError:
            continue
    return None


def _rel_for_api(abs_path: str) -> str:
    try:
        from utils.output_paths import get_data_root
        root = os.path.abspath(get_data_root())
        if os.path.commonpath([root, abs_path]) == root:
            return os.path.relpath(abs_path, root).replace('\\', '/')
    except Exception:
        pass
    try:
        return os.path.relpath(abs_path, backup_root()).replace('\\', '/')
    except Exception:
        return os.path.basename(abs_path)


def _scan_output_config_backups(limit: int = 200) -> List[Dict[str, Any]]:
    """Supplement catalog with Tools Backup run-folder configs."""
    out: List[Dict[str, Any]] = []
    try:
        base = os.path.join(outputs_root(), 'config_backup')
        if not os.path.isdir(base):
            return out
        for root, _dirs, files in os.walk(base):
            for name in files:
                if not name.endswith('_config.txt') and not name.endswith('.txt'):
                    continue
                fp = os.path.abspath(os.path.join(root, name))
                try:
                    if os.path.commonpath([base, fp]) != base:
                        continue
                except ValueError:
                    continue
                host = name.replace('_config.txt', '').replace('.txt', '')
                try:
                    mtime = os.path.getmtime(fp)
                    from datetime import datetime
                    ts = datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')
                except Exception:
                    ts = ''
                out.append({
                    'hostname': host,
                    'device': host,
                    'timestamp': ts,
                    'backup_type': 'tools_run',
                    'trigger': 'Tools Config Backup run folder',
                    'safe_path': _rel_for_api(fp),
                    'backup_path': _rel_for_api(fp),
                    'file_exists': True,
                    'source': 'outputs/config_backup',
                })
                if len(out) >= limit:
                    return out
    except Exception:
        return out
    return out


def list_backup_records(hostname: Optional[str] = None) -> List[Dict[str, Any]]:
    from utils.config_backup_system import ConfigBackupSystem
    from utils.output_paths import get_backups_root

    devices_dir = os.path.join(get_backups_root(), 'devices')
    sys_obj = ConfigBackupSystem(backup_dir=devices_dir)
    rows = sys_obj.list_backups(hostname=hostname)
    out = []
    for row in rows:
        path = row.get('file_path') or row.get('path') or row.get('backup_path')
        safe = contained_backup_path(path) if path else None
        item = dict(row)
        if safe:
            item['safe_path'] = _rel_for_api(safe)
            item['file_exists'] = True
        else:
            item['safe_path'] = None
            item['file_exists'] = False
        for key in ('file_path', 'path', 'backup_path', 'previous_backup'):
            if key in item and item[key]:
                rel = contained_backup_path(str(item[key]))
                item[key] = _rel_for_api(rel) if rel else None
        item.setdefault('source', 'backups/devices')
        out.append(item)

    # Merge Tools Backup run folders so Compare is never empty after Backup
    for extra in _scan_output_config_backups():
        if hostname and extra.get('hostname') != hostname and hostname not in str(extra.get('hostname') or ''):
            continue
        out.append(extra)

    return sorted(out, key=lambda x: x.get('timestamp') or '', reverse=True)


def compare_backup_paths(path_a: str, path_b: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    from utils.config_backup_system import ConfigBackupSystem
    from utils.output_paths import get_backups_root

    a = contained_backup_path(path_a)
    b = contained_backup_path(path_b)
    if not a or not b:
        return None, 'Backup path rejected (must be under data_root/backups or outputs/config_backup)'
    sys_obj = ConfigBackupSystem(backup_dir=os.path.join(get_backups_root(), 'devices'))
    diff = sys_obj.compare_backups(a, b)
    diff['path_a'] = _rel_for_api(a)
    diff['path_b'] = _rel_for_api(b)
    return diff, None
