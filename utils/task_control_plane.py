"""
Background task registry for Network Swiss Tool Pro control plane.

Tracks threaded operations started via /api/execute and allows cooperative cancel.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

_lock = threading.Lock()
_tasks: Dict[str, Dict[str, Any]] = {}
_cancel_events: Dict[str, threading.Event] = {}
_live_conns: Dict[str, List[Any]] = {}
_thread_local = threading.local()
_MAX_TASKS = 200


def _index_start(task_id: str, action: str, meta: Dict[str, Any]) -> None:
    try:
        from utils.job_index import record_start
        record_start(
            task_id,
            action,
            inventory_source=meta.get('inventory_source'),
            device_count=meta.get('device_count'),
        )
    except Exception:
        pass


def _index_status(
    task_id: str,
    status: str,
    error: Optional[str] = None,
    *,
    cancel_requested: bool = False,
) -> None:
    try:
        from utils.job_index import record_status
        record_status(task_id, status, error, cancel_requested=cancel_requested)
    except Exception:
        pass


def bind_task(task_id: str) -> None:
    _thread_local.task_id = task_id


def bind_session_key(key: str) -> None:
    """Bind discovery job_id (or any session key) for live SSH tracking."""
    _thread_local.session_key = key


def current_task_id() -> Optional[str]:
    return getattr(_thread_local, 'task_id', None)


def current_session_key() -> Optional[str]:
    return getattr(_thread_local, 'session_key', None) or current_task_id()


def register_live_connection(conn: Any, key: Optional[str] = None) -> None:
    """Track a Netmiko connection so cancel can close the socket."""
    sid = key or current_session_key()
    if not sid or conn is None:
        return
    with _lock:
        bucket = _live_conns.setdefault(sid, [])
        if conn not in bucket:
            bucket.append(conn)


def unregister_live_connection(conn: Any, key: Optional[str] = None) -> None:
    sid = key or current_session_key()
    if not sid or conn is None:
        return
    with _lock:
        bucket = _live_conns.get(sid) or []
        _live_conns[sid] = [c for c in bucket if c is not conn]


def _force_close_conn(conn: Any) -> bool:
    closed = False
    try:
        conn.disconnect()
        closed = True
    except Exception:
        pass
    remote = getattr(conn, 'remote_conn', None)
    if remote is not None:
        try:
            remote.close()
            closed = True
        except Exception:
            pass
        try:
            transport = remote.get_transport()
            if transport:
                transport.close()
                closed = True
        except Exception:
            pass
    return closed


def disconnect_live_connections(key: Optional[str] = None) -> int:
    """Close sockets for a task/job so in-flight send_command unblocks."""
    sid = key or current_session_key()
    if not sid:
        return 0
    with _lock:
        conns = list(_live_conns.get(sid) or [])
    n = 0
    for conn in conns:
        if _force_close_conn(conn):
            n += 1
    return n


def should_abort() -> bool:
    return is_cancelled(current_task_id())


def register_task(action: str, label: str = '', meta: Optional[Dict[str, Any]] = None) -> str:
    task_id = uuid.uuid4().hex[:12]
    with _lock:
        if len(_tasks) >= _MAX_TASKS:
            overflow = len(_tasks) - _MAX_TASKS + 1
            oldest = sorted(_tasks.values(), key=lambda t: t.get('started_at', ''))
            for old in oldest:
                if overflow <= 0:
                    break
                if old.get('status') in ('running', 'cancelling'):
                    continue
                _tasks.pop(old['id'], None)
                _cancel_events.pop(old['id'], None)
                overflow -= 1
        _tasks[task_id] = {
            'id': task_id,
            'action': action,
            'label': label or action,
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'ended_at': None,
            'error': None,
            'meta': meta or {},
        }
        _cancel_events[task_id] = threading.Event()
    _index_start(task_id, action, meta or {})
    return task_id


def complete_task(task_id: str, status: str = 'complete', error: Optional[str] = None) -> None:
    cancelled = is_cancelled(task_id)
    memory_status = status
    if cancelled and status == 'complete':
        memory_status = 'cancelled'
    with _lock:
        task = _tasks.get(task_id)
        if task:
            # Never present a cancelled worker as complete in memory either.
            if task.get('status') in ('cancelling', 'cancelled') and memory_status == 'complete':
                memory_status = 'cancelled'
            task['status'] = memory_status
            task['ended_at'] = datetime.now().isoformat()
            if error:
                task['error'] = error
    # Index even if in-memory row was evicted so sqlite is not stuck on running.
    _index_status(task_id, status, error, cancel_requested=cancelled)


def request_cancel(task_id: str) -> bool:
    with _lock:
        if task_id not in _tasks:
            return False
        _tasks[task_id]['status'] = 'cancelling'
        ev = _cancel_events.get(task_id)
    if ev:
        ev.set()
    disconnect_live_connections(task_id)
    _index_status(task_id, 'cancelled', cancel_requested=True)
    return True


def request_session_cancel(key: str) -> int:
    """Force-close SSH for a discovery job_id (may have no control-plane task)."""
    if not key:
        return 0
    ev = _cancel_events.get(key)
    if ev:
        ev.set()
    return disconnect_live_connections(key)


def is_cancelled(task_id: Optional[str]) -> bool:
    if not task_id:
        return False
    ev = _cancel_events.get(task_id)
    return bool(ev and ev.is_set())


def list_tasks(include_finished: bool = True) -> List[Dict[str, Any]]:
    with _lock:
        items = list(_tasks.values())
    if not include_finished:
        items = [t for t in items if t.get('status') == 'running']
    return sorted(items, key=lambda t: t.get('started_at', ''), reverse=True)


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        t = _tasks.get(task_id)
        return dict(t) if t else None


def update_task_progress(
    task_id: Optional[str] = None,
    *,
    devices_done: int = 0,
    devices_total: int = 0,
    message: str = '',
) -> None:
    """Update multi-device progress on the active background task."""
    tid = task_id or current_task_id()
    if not tid:
        return
    with _lock:
        task = _tasks.get(tid)
        if not task:
            return
        task['devices_done'] = max(0, int(devices_done))
        task['devices_total'] = max(0, int(devices_total))
        if devices_total > 0:
            task['progress_percent'] = min(99, int((devices_done / devices_total) * 100))
        if message:
            task['progress_message'] = message
