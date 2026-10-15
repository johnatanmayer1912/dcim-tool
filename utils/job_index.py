"""
SQLite job index — catalog only. Artifacts stay in run folders.

Storage: {data_root}/index/jobs.sqlite  (same get_data_root() as outputs/)
Failure policy: fail-open. Index errors must not change job results.
Never store passwords, vault keys, inventory bodies, or CLI dumps.

Status model (index, not in-memory control plane):
  running   — registered, not terminal
  complete  — finished without cancel
  failed    — exception / error (maps control-plane 'error')
  cancelled — operator cancelled; no usable run folder
  partial   — cancelled (or cancel-then-finish) with a contained run_dir

Cancelled is never rewritten to complete. Failed is never rewritten to complete.
Partial is never rewritten to complete.

AI_CONTEXT: Evidence catalog for execute jobs after in-memory tasks expire.
AI_SECURITY_NOTE: Localhost list API only. Paths must stay under outputs/.
AI_SAFE: Adding a column needs schema_version bump + tests. Do not store secrets.
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 1
STATUSES = frozenset({'running', 'complete', 'failed', 'cancelled', 'partial'})
TERMINAL = frozenset({'complete', 'failed', 'cancelled', 'partial'})
DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 200
_SECRET_RE = re.compile(
    r'(password|passwd|enable_pwd|enable_password|secret|token|fernet|api_key|credential)'
    r'\s*[:=]\s*\S+',
    re.IGNORECASE,
)

_write_lock = threading.Lock()
_DB_PATH_OVERRIDE: Optional[str] = None


def reset_for_tests(db_path: Optional[str] = None) -> None:
    """Point the index at a temp file (or clear override). Tests only."""
    global _DB_PATH_OVERRIDE
    _DB_PATH_OVERRIDE = os.path.abspath(db_path) if db_path else None


def db_path() -> str:
    if _DB_PATH_OVERRIDE:
        return _DB_PATH_OVERRIDE
    from utils.output_paths import get_data_root
    return os.path.join(get_data_root(), 'index', 'jobs.sqlite')


def _now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _log(msg: str) -> None:
    try:
        from utils.app_logger import add_log
        add_log(msg)
    except Exception:
        pass


def sanitize_error(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    s = str(text).replace('\n', ' ').strip()
    if not s:
        return None
    s = _SECRET_RE.sub(lambda m: m.group(1) + '=<redacted>', s)
    lower = s.lower()
    for banned in ('password', 'enable_pwd', 'fernet', 'credential_key'):
        if banned in lower and '=<redacted>' not in s:
            return 'error (details omitted)'
    return s[:200]


def _safe_int(value: Any) -> Optional[int]:
    if value is None or value == '':
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return 0
    return n


def _safe_source(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).replace('\n', ' ').strip()[:64]
    return s or None


def _safe_action(value: Any) -> str:
    return str(value or '').replace('\n', ' ').strip()[:80]


def _safe_task_id(value: Any) -> Optional[str]:
    s = str(value or '').strip()
    if not s or len(s) > 64:
        return None
    if '/' in s or '\\' in s or '..' in s:
        return None
    if not re.fullmatch(r'[A-Za-z0-9_-]+', s):
        return None
    return s


def _realpath_under(candidate: str, root: str) -> Optional[str]:
    """Return realpath of candidate if it stays under root (symlink-safe)."""
    try:
        root_real = os.path.realpath(root)
        cand_real = os.path.realpath(candidate)
        if os.path.commonpath([root_real, cand_real]) != root_real:
            return None
        return cand_real
    except (ValueError, OSError):
        return None


def contained_run_dir(path: Optional[str]) -> Optional[str]:
    """Return data-root-relative outputs/ path, or None if unsafe/missing.

    Uses realpath so symlinks under outputs/ that escape the data root are rejected.
    """
    if not path:
        return None
    raw = str(path).strip()
    if not raw or '\x00' in raw:
        return None
    try:
        from utils.output_paths import get_data_root, get_outputs_root
        root = os.path.realpath(get_data_root())
        outputs = os.path.realpath(get_outputs_root())
        abs_p = os.path.realpath(raw) if os.path.isabs(raw) else os.path.realpath(
            os.path.join(root, os.path.normpath(raw)),
        )
    except Exception:
        return None
    if _realpath_under(abs_p, outputs) is None:
        return None
    if _realpath_under(abs_p, root) is None:
        return None
    rel = os.path.relpath(abs_p, root).replace('\\', '/')
    if rel.startswith('..') or os.path.isabs(rel):
        return None
    if not rel.startswith('outputs/'):
        return None
    return rel


def is_safe_outputs_file(path: Optional[str], *, require_html: bool = False) -> Optional[str]:
    """Return real absolute path if file is under outputs/ and not a symlink escape."""
    rel = contained_run_dir(path)
    if not rel:
        return None
    from utils.output_paths import get_data_root
    full = os.path.realpath(os.path.join(get_data_root(), *rel.split('/')))
    if not os.path.isfile(full):
        return None
    if os.path.islink(full):
        # File itself must still resolve under outputs (already checked via realpath).
        pass
    if require_html and not full.lower().endswith('.html'):
        return None
    return full


def public_outputs_meta(path: Optional[str]) -> Dict[str, Any]:
    """Safe artifact fields for JSON. Absolute paths are never returned."""
    empty = {
        'run_dir': None,
        'safe_path': None,
        'artifacts_available': False,
        'run_dir_exists': False,
    }
    candidates = [path]
    try:
        if path and os.path.isfile(str(path)):
            candidates.append(os.path.dirname(os.path.abspath(str(path))))
    except Exception:
        pass
    rel = None
    for cand in candidates:
        rel = contained_run_dir(cand)
        if rel:
            break
    if not rel:
        return dict(empty)
    from utils.output_paths import get_data_root
    abs_join = os.path.join(get_data_root(), *rel.split('/'))
    if os.path.isfile(abs_join):
        parent_rel = '/'.join(rel.split('/')[:-1])
        if not parent_rel.startswith('outputs'):
            return dict(empty)
        return {
            'run_dir': parent_rel,
            'safe_path': rel,
            'artifacts_available': True,
            'run_dir_exists': os.path.isdir(os.path.dirname(abs_join)),
        }
    if os.path.isdir(abs_join):
        return {
            'run_dir': rel,
            'safe_path': rel,
            'artifacts_available': True,
            'run_dir_exists': True,
        }
    return {
        'run_dir': rel,
        'safe_path': rel,
        'artifacts_available': False,
        'run_dir_exists': False,
    }


def clamp_limit(raw: Any, default: int = DEFAULT_LIST_LIMIT) -> int:
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return default
    if n < 1:
        return 1
    if n > MAX_LIST_LIMIT:
        return MAX_LIST_LIMIT
    return n


def map_control_status(status: Optional[str]) -> str:
    s = (status or '').strip().lower()
    if s == 'error':
        return 'failed'
    if s == 'cancelling':
        return 'cancelled'
    if s in STATUSES:
        return s
    return 'running'


def _merge_status(
    current: Optional[str],
    incoming: str,
    *,
    cancel_requested: bool,
    has_run_dir: bool,
) -> str:
    incoming = map_control_status(incoming)
    cur = current if current in STATUSES else 'running'
    if cancel_requested and incoming == 'complete':
        incoming = 'partial' if has_run_dir else 'cancelled'
    elif cancel_requested and incoming == 'cancelled' and has_run_dir:
        incoming = 'partial'
    elif incoming == 'cancelled' and has_run_dir:
        incoming = 'partial'

    if cur == 'complete':
        return 'complete'
    if cur == 'failed' and incoming == 'complete':
        return 'failed'
    if cur in ('cancelled', 'partial') and incoming == 'complete':
        return 'partial' if has_run_dir or cur == 'partial' else 'cancelled'
    if cur == 'cancelled' and incoming == 'partial':
        return 'partial'
    if cur == 'partial' and incoming in ('cancelled', 'running'):
        return 'partial'
    if cur == 'failed' and incoming in ('cancelled', 'partial'):
        return 'failed'
    return incoming


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            task_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            action TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL,
            inventory_source TEXT,
            device_count INTEGER,
            run_dir TEXT,
            error_summary TEXT,
            partial INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        'CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)'
    )
    row = conn.execute(
        "SELECT value FROM schema_meta WHERE key='version'"
    ).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO schema_meta(key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),),
        )


def _connect() -> Optional[sqlite3.Connection]:
    path = db_path()
    parent = os.path.dirname(path)
    try:
        os.makedirs(parent, exist_ok=True)
    except OSError as exc:
        _log(f'[JobIndex] cannot create index dir ({type(exc).__name__})')
        return None
    conn = None
    try:
        conn = sqlite3.connect(path, timeout=8.0)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=8000')
        _ensure_schema(conn)
        conn.commit()
        return conn
    except sqlite3.DatabaseError:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        try:
            corrupt = path + '.corrupt'
            if os.path.isfile(path):
                try:
                    os.replace(path, corrupt)
                except OSError:
                    os.remove(path)
            conn = sqlite3.connect(path, timeout=8.0)
            conn.row_factory = sqlite3.Row
            _ensure_schema(conn)
            conn.commit()
            _log('[JobIndex] rebuilt sqlite after DatabaseError')
            return conn
        except Exception as exc:
            _log(f'[JobIndex] rebuild failed ({type(exc).__name__})')
            return None
    except Exception as exc:
        _log(f'[JobIndex] connect failed ({type(exc).__name__})')
        return None


def init_db() -> bool:
    conn = _connect()
    if not conn:
        return False
    conn.close()
    return True


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    status = row['status']
    rel = row['run_dir']
    if rel:
        checked = contained_run_dir(_abs_from_rel(rel))
        rel = checked
    exists = False
    if rel:
        abs_p = _abs_from_rel(rel)
        exists = bool(abs_p and os.path.isdir(abs_p))
    partial = bool(row['partial']) or status == 'partial'
    return {
        'task_id': row['task_id'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'completed_at': row['completed_at'],
        'action': row['action'] or '',
        'status': status,
        'inventory_source': row['inventory_source'],
        'device_count': row['device_count'],
        'run_dir': rel,
        'run_dir_exists': exists,
        'artifacts_available': bool(rel and exists),
        'error_summary': row['error_summary'],
        'partial': partial,
    }


def _abs_from_rel(rel: str) -> Optional[str]:
    try:
        from utils.output_paths import get_data_root
        root = os.path.abspath(get_data_root())
        abs_p = os.path.abspath(os.path.normpath(os.path.join(root, rel)))
        if os.path.commonpath([root, abs_p]) != root:
            return None
        return abs_p
    except Exception:
        return None


def record_start(
    task_id: str,
    action: str = '',
    *,
    inventory_source: Optional[str] = None,
    device_count: Any = None,
) -> bool:
    tid = _safe_task_id(task_id)
    if not tid:
        return False
    now = _now()
    payload = (
        tid,
        now,
        now,
        _safe_action(action),
        'running',
        _safe_source(inventory_source),
        _safe_int(device_count),
        0,
    )
    try:
        with _write_lock:
            conn = _connect()
            if not conn:
                return False
            try:
                conn.execute(
                    """
                    INSERT INTO jobs (
                        task_id, created_at, updated_at, action, status,
                        inventory_source, device_count, partial
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        updated_at=excluded.updated_at,
                        action=excluded.action,
                        inventory_source=COALESCE(excluded.inventory_source, jobs.inventory_source),
                        device_count=COALESCE(excluded.device_count, jobs.device_count)
                    """,
                    payload,
                )
                conn.commit()
                return True
            finally:
                conn.close()
    except Exception as exc:
        _log(f'[JobIndex] record_start failed ({type(exc).__name__})')
        return False


def record_status(
    task_id: str,
    status: str,
    error: Optional[str] = None,
    *,
    cancel_requested: bool = False,
) -> bool:
    tid = _safe_task_id(task_id)
    if not tid:
        return False
    try:
        with _write_lock:
            conn = _connect()
            if not conn:
                return False
            try:
                row = conn.execute(
                    'SELECT status, run_dir FROM jobs WHERE task_id=?',
                    (tid,),
                ).fetchone()
                if not row:
                    return False
                has_run = bool(row['run_dir'])
                merged = _merge_status(
                    row['status'],
                    status,
                    cancel_requested=cancel_requested,
                    has_run_dir=has_run,
                )
                now = _now()
                completed = now if merged in TERMINAL else None
                err = sanitize_error(error)
                conn.execute(
                    """
                    UPDATE jobs SET
                        status=?,
                        updated_at=?,
                        completed_at=COALESCE(?, completed_at),
                        error_summary=COALESCE(?, error_summary),
                        partial=?
                    WHERE task_id=?
                    """,
                    (
                        merged,
                        now,
                        completed,
                        err,
                        1 if merged == 'partial' else 0,
                        tid,
                    ),
                )
                conn.commit()
                return True
            finally:
                conn.close()
    except Exception as exc:
        _log(f'[JobIndex] record_status failed ({type(exc).__name__})')
        return False


def record_run_dir(task_id: Optional[str], run_dir: Optional[str]) -> bool:
    tid = _safe_task_id(task_id)
    rel = contained_run_dir(run_dir)
    if not tid or not rel:
        return False
    try:
        with _write_lock:
            conn = _connect()
            if not conn:
                return False
            try:
                row = conn.execute(
                    'SELECT status FROM jobs WHERE task_id=?',
                    (tid,),
                ).fetchone()
                if not row:
                    return False
                new_status = row['status']
                partial = 1 if row['status'] == 'partial' else 0
                if row['status'] == 'cancelled':
                    new_status = 'partial'
                    partial = 1
                conn.execute(
                    """
                    UPDATE jobs SET
                        run_dir=?,
                        updated_at=?,
                        status=?,
                        partial=?
                    WHERE task_id=?
                    """,
                    (rel, _now(), new_status, partial, tid),
                )
                conn.commit()
                return True
            finally:
                conn.close()
    except Exception as exc:
        _log(f'[JobIndex] record_run_dir failed ({type(exc).__name__})')
        return False


def note_run_dir(run_dir: Optional[str]) -> bool:
    """Attach a prepared run folder to the bound control-plane task, if any."""
    try:
        from utils.task_control_plane import current_task_id
        return record_run_dir(current_task_id(), run_dir)
    except Exception:
        return False


def get_job(task_id: str) -> Optional[Dict[str, Any]]:
    tid = _safe_task_id(task_id)
    if not tid:
        return None
    try:
        conn = _connect()
        if not conn:
            return None
        try:
            row = conn.execute(
                'SELECT * FROM jobs WHERE task_id=?',
                (tid,),
            ).fetchone()
            return _row_to_dict(row) if row else None
        finally:
            conn.close()
    except Exception as exc:
        _log(f'[JobIndex] get_job failed ({type(exc).__name__})')
        return None


def list_jobs(limit: Any = DEFAULT_LIST_LIMIT) -> List[Dict[str, Any]]:
    n = clamp_limit(limit)
    try:
        conn = _connect()
        if not conn:
            return []
        try:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (n,),
            ).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as exc:
        _log(f'[JobIndex] list_jobs failed ({type(exc).__name__})')
        return []


def schema_version() -> Optional[int]:
    try:
        conn = _connect()
        if not conn:
            return None
        try:
            row = conn.execute(
                "SELECT value FROM schema_meta WHERE key='version'"
            ).fetchone()
            return int(row['value']) if row else None
        finally:
            conn.close()
    except Exception:
        return None
