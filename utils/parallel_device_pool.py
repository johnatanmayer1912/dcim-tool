"""
Parallel device execution with sane SSH concurrency limits (v7.0.46).

Serial fallback when len(devices)==1 or max_workers==1.
Respects control-plane cancel via should_abort between completions.
"""
from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, List, Optional

_log_lock = threading.Lock()

DEFAULT_MAX_WORKERS = 5
ABS_MAX_WORKERS = 20


def get_max_workers(override: Optional[int] = None) -> int:
    if override is not None:
        return max(1, min(int(override), ABS_MAX_WORKERS))
    try:
        env = int(os.environ.get('NST_SSH_MAX_WORKERS', DEFAULT_MAX_WORKERS))
    except ValueError:
        env = DEFAULT_MAX_WORKERS
    return max(1, min(env, ABS_MAX_WORKERS))


def _safe_log(log_func, msg: str) -> None:
    if not log_func:
        return
    with _log_lock:
        log_func(msg)


def _should_abort() -> bool:
    try:
        from utils.task_control_plane import should_abort
        return should_abort()
    except Exception:
        return False


def _report_progress(done: int, total: int, host: str = '') -> None:
    try:
        from utils.task_control_plane import update_task_progress
        msg = f'{host} ({done}/{total})' if host else f'Device {done}/{total}'
        update_task_progress(devices_done=done, devices_total=total, message=msg)
    except Exception:
        pass


def foreach_device_parallel(
    devices: List[dict],
    worker: Callable[[dict, int], Any],
    *,
    log=None,
    max_workers: Optional[int] = None,
    label: str = 'devices',
) -> List[Any]:
    """
    Run worker(device, index) across inventory with bounded parallelism.

    Returns list aligned with devices (None where skipped due to abort).
    """
    n = len(devices)
    if n == 0:
        return []

    workers = get_max_workers(max_workers)
    workers = min(workers, n)
    results: List[Any] = [None] * n

    if workers <= 1:
        for idx, dev in enumerate(devices):
            if _should_abort():
                _safe_log(log, f'[Control Plane] Cancelled — stopping {label} after {idx} device(s).')
                break
            host = dev.get('host', '?')
            _safe_log(log, f'[{idx + 1}/{n}] {host}…')
            results[idx] = worker(dev, idx)
            _report_progress(idx + 1, n, host)
        return results

    _safe_log(log, f'[Parallel SSH] {label}: {n} device(s), max {workers} concurrent session(s).')

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix='nst-ssh') as pool:
        future_map = {}
        submitted = 0
        for idx, dev in enumerate(devices):
            if _should_abort():
                _safe_log(log, f'[Control Plane] Cancelled — not submitting remaining {label}.')
                break
            host = dev.get('host', '?')
            _safe_log(log, f'[Queue {submitted + 1}/{n}] {host}')
            fut = pool.submit(worker, dev, idx)
            future_map[fut] = idx
            submitted += 1

        done = 0
        for fut in as_completed(future_map):
            idx = future_map[fut]
            host = devices[idx].get('host', '?')
            try:
                results[idx] = fut.result()
            except Exception as exc:
                results[idx] = {'_parallel_error': str(exc), 'host': host}
                _safe_log(log, f'  [ERROR] {host}: {exc}')
            done += 1
            _report_progress(done, submitted, host)
            if _should_abort():
                _safe_log(log, f'[Control Plane] Cancel requested — {label} finishing in-flight only.')
                break

    return results
