"""
utils/output_paths.py
---------------------
Centralized writable paths for logs, reports, and run artifacts.

All feature output lives under a dedicated data root (never the install/CWD folder):
  {data_root}/outputs/<category>/<YYYYMMDD>/<HHMMSS>_<slug>/
  {data_root}/logs/
  {data_root}/backups/

Override location with environment variable NST_DATA_DIR.

AI_CONTEXT: Offline persistence root for reports, discovery JSON, maps, logs.
AI_FLOW: prepare_run_output → category/date/slug folders under data root
AI_IMPACTS: every plugin report path; discovery maps on disk
AI_OFFLINE_NOTE: Never the install dir. NST_DATA_DIR for USB/jump-host layouts.
AI_SECURITY_NOTE: Do not put vault files here by convention; still treat run dirs as sensitive telemetry.
AI_BREADCRUMB: callers in plugins + vlan_checker_web exports
AI_SAFE: Adding a CAT_* constant is fine. Changing get_data_root() defaults needs tests.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

_DATA_ROOT: Optional[str] = None

# Category folder names (indicative, stable API)
CAT_MAC_TRACE = 'mac_trace'
CAT_DESCRIPTION_SEARCH = 'description_search'
CAT_PING_SCAN = 'ping_scan'
CAT_REACHABILITY = 'reachability'
CAT_VLAN_AUDIT = 'vlan_audit'
CAT_VLAN_COMPARE = 'vlan_compare'
CAT_VLAN_MANAGEMENT = 'vlan_management'
CAT_VLAN_MISSING = 'vlan_missing'
CAT_INTERFACES = 'interfaces'
CAT_CONFIG_BACKUP = 'config_backup'
CAT_NETWORK_AUDIT = 'network_audit'
CAT_TOPOLOGY_MAPPER = 'topology_mapper'
CAT_NODE_INTERFACE = 'node_interface_topology'
CAT_NODE_ANALYSIS = 'node_analysis'
CAT_DISCOVERY = 'discovery'
CAT_COMPLIANCE = 'compliance'
CAT_PLUGINS = 'plugins'
CAT_INTERFACE_MANAGER = 'interface_manager'
CAT_STP_TOPOLOGY = 'stp_topology'
CAT_L3_TOPOLOGY = 'l3_topology'
CAT_FLOW_MAP = 'flow_map'
CAT_ADVANCED_L2 = 'advanced_l2_map'
CAT_FAILURE_CORRELATION = 'failure_correlation'


def get_install_root() -> str:
    """Read-only application root (EXE dir or project root)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, '.nst_write_probe')
        with open(probe, 'w', encoding='utf-8') as f:
            f.write('ok')
        os.remove(probe)
        return True
    except OSError:
        return False


def get_data_root() -> str:
    """Writable data root — never the install directory."""
    global _DATA_ROOT
    if _DATA_ROOT:
        return _DATA_ROOT

    env = (os.environ.get('NST_DATA_DIR') or '').strip()
    if env:
        root = os.path.abspath(env)
    else:
        candidates: List[str] = []
        if sys.platform == 'win32':
            profile = os.environ.get('USERPROFILE', '')
            local = os.environ.get('LOCALAPPDATA', '')
            if profile:
                candidates.append(os.path.join(profile, 'Documents', 'NetworkSwissToolPro'))
            if local:
                candidates.append(os.path.join(local, 'NetworkSwissToolPro'))
        else:
            home = os.path.expanduser('~')
            candidates.extend([
                os.path.join(home, 'NetworkSwissToolPro'),
                os.path.join(home, '.local', 'share', 'NetworkSwissToolPro'),
            ])
        candidates.append(os.path.join(tempfile.gettempdir(), 'NetworkSwissToolPro'))

        root = None
        for candidate in candidates:
            if candidate and _is_writable(candidate):
                root = os.path.abspath(candidate)
                break
        if not root:
            root = os.path.abspath(candidates[-1])
            os.makedirs(root, exist_ok=True)

    install = os.path.abspath(get_install_root())
    if os.path.abspath(root) == install:
        root = os.path.join(tempfile.gettempdir(), 'NetworkSwissToolPro')
        os.makedirs(root, exist_ok=True)

    _DATA_ROOT = root
    ensure_data_layout()
    return _DATA_ROOT


def ensure_data_layout() -> None:
    """Create standard subfolders under the data root."""
    root = _DATA_ROOT or get_data_root()
    for sub in (
        'logs',
        'logs/sessions',
        'outputs',
        'backups/devices',
        'backups/plugins',
        'backups/interface_manager',
        'scratch/uploads',
        '_master',
        'index',
    ):
        os.makedirs(os.path.join(root, sub), exist_ok=True)


def get_logs_dir() -> str:
    return os.path.join(get_data_root(), 'logs')


def get_outputs_root() -> str:
    return os.path.join(get_data_root(), 'outputs')


def get_backups_root() -> str:
    return os.path.join(get_data_root(), 'backups')


def get_scratch_dir() -> str:
    return os.path.join(get_data_root(), 'scratch', 'uploads')


def get_demo_dir() -> str:
    """Static demo topology HTML (vPC lab map, etc.)."""
    d = os.path.join(get_data_root(), 'demos')
    os.makedirs(d, exist_ok=True)
    return d


DEMO_VPC_TOPOLOGY_FILENAME = 'DEMO_VPC_TOPOLOGY_v7.0.html'


def get_demo_vpc_topology_path() -> str:
    return os.path.join(get_demo_dir(), DEMO_VPC_TOPOLOGY_FILENAME)


def get_credentials_exports_dir() -> str:
    d = os.path.join(get_data_root(), 'credentials', 'exports')
    os.makedirs(d, exist_ok=True)
    return d


def get_master_dir() -> str:
    return os.path.join(get_data_root(), '_master')


def get_master_log_path(name: str = 'plugin_execution_summary.txt') -> str:
    return os.path.join(get_master_dir(), name)


def new_session_log_path() -> str:
    """Unique per-launch session log under logs/sessions/."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(get_data_root(), 'logs', 'sessions', f'app_session_{ts}.txt')


def slugify(value: str, max_len: int = 48) -> str:
    s = re.sub(r'[^\w\-.]+', '_', (value or '').strip())
    s = re.sub(r'_+', '_', s).strip('_')
    return (s or 'run')[:max_len]


def prepare_run_output(
    category: str,
    slug: str = '',
    extra_subdirs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create outputs/<category>/<YYYYMMDD>/<HHMMSS>_<slug>/ and return paths.

    Each invocation creates a new run folder (two runs => two folders).
    """
    now = datetime.now()
    date_part = now.strftime('%Y%m%d')
    time_part = f"{now.strftime('%H%M%S')}_{now.microsecond:06d}"
    safe = slugify(slug) if slug else 'run'
    run_id = f'{time_part}_{safe}'
    run_dir = os.path.join(get_outputs_root(), category, date_part, run_id)
    if extra_subdirs:
        for sub in extra_subdirs:
            run_dir = os.path.join(run_dir, sub)
    os.makedirs(run_dir, exist_ok=True)
    abs_run = os.path.abspath(run_dir)
    try:
        from utils.job_index import note_run_dir
        note_run_dir(abs_run)
    except Exception:
        pass
    return {
        'run_dir': abs_run,
        'txt_path': os.path.join(run_dir, 'report.txt'),
        'html_path': os.path.join(run_dir, 'report.html'),
        'manifest_path': os.path.join(run_dir, 'manifest.json'),
        'category': category,
        'slug': safe,
        'run_id': run_id,
        'date_part': date_part,
        'generated_at': now.isoformat(),
        'data_root': get_data_root(),
    }


def path_in_run(paths: Dict[str, Any], filename: str) -> str:
    """Build an absolute path inside a prepared run folder."""
    return os.path.join(paths['run_dir'], filename)


def write_run_manifest(paths: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> str:
    doc = {
        'category': paths.get('category'),
        'run_id': paths.get('run_id'),
        'generated_at': paths.get('generated_at'),
        'run_dir': paths.get('run_dir'),
        'data_root': paths.get('data_root') or get_data_root(),
        'txt_path': paths.get('txt_path'),
        'html_path': paths.get('html_path'),
    }
    if extra:
        doc.update(extra)
    mpath = paths.get('manifest_path')
    if mpath:
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2)
        try:
            from utils.output_chrome import write_run_readme
            title = (extra or {}).get('task_title') or str(paths.get('category', 'run')).replace('_', ' ').title()
            readme_path = os.path.join(paths['run_dir'], '00_README.txt')
            if not os.path.isfile(readme_path):
                write_run_readme(paths, title=title)
        except Exception:
            pass
    return mpath or ''


# Backward-compatible alias used by search_report_output
def get_app_root() -> str:
    return get_data_root()


def prepare_search_run(category: str, slug: str = '') -> Dict[str, Any]:
    """Alias for prepare_run_output (mac_trace, description_search, ping_scan)."""
    return prepare_run_output(category, slug)
