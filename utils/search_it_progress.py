"""
Live progress state for search_it tools (MAC trace, description search, ping scan).

Mirrors the discovery crawl progress shape for UI polling.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional

_lock = threading.Lock()

_DEFAULT = {
    'status': 'idle',
    'current': 0,
    'total': 0,
    'current_host': '',
    'label': '',
    'percent': 0,
    'message': '',
    'found_count': 0,
    'match_count': 0,
    'responsive_count': 0,
}

_state: Dict[str, Dict[str, Any]] = {
    'mac_trace': dict(_DEFAULT),
    'description_search': dict(_DEFAULT),
    'ping_scan': dict(_DEFAULT),
}


def _cat(category: str) -> Dict[str, Any]:
    if category not in _state:
        _state[category] = dict(_DEFAULT)
    return _state[category]


def get_all_progress() -> Dict[str, Dict[str, Any]]:
    with _lock:
        return {k: dict(v) for k, v in _state.items()}


def progress_start(category: str, total: int, *, label: str = 'Starting…', message: str = '') -> None:
    with _lock:
        _cat(category).update({
            'status': 'running',
            'current': 0,
            'total': max(0, int(total)),
            'current_host': '',
            'label': label,
            'percent': 0,
            'message': message or label,
            'found_count': 0,
            'match_count': 0,
            'responsive_count': 0,
        })


def progress_start_if_needed(category: str, total: int, *, label: str = 'Starting…', message: str = '') -> None:
    """Start progress unless API pre-arm already set this category to running."""
    total = max(0, int(total))
    with _lock:
        st = _cat(category)
        if st.get('status') == 'running' and int(st.get('total') or 0) == total:
            st['label'] = label
            st['message'] = message or label
            return
    progress_start(category, total, label=label, message=message)


def progress_tick(
    category: str,
    current: int,
    total: int,
    *,
    host: str = '',
    label: Optional[str] = None,
    found_count: Optional[int] = None,
    match_count: Optional[int] = None,
    responsive_count: Optional[int] = None,
) -> None:
    total = max(1, int(total))
    cur = min(int(current), total)
    pct = min(99, int((cur / total) * 100))
    host = host or ''
    lbl = label or (f'Scanning {host} ({cur}/{total})' if host else f'Progress {cur}/{total}')
    with _lock:
        st = _cat(category)
        st.update({
            'status': 'running',
            'current': cur,
            'total': total,
            'current_host': host,
            'label': lbl,
            'percent': pct,
            'message': lbl,
        })
        if found_count is not None:
            st['found_count'] = found_count
        if match_count is not None:
            st['match_count'] = match_count
        if responsive_count is not None:
            st['responsive_count'] = responsive_count


def progress_done(category: str, *, error: Optional[str] = None, message: str = 'Complete') -> None:
    with _lock:
        st = _cat(category)
        if error:
            st.update({
                'status': 'error',
                'percent': 0,
                'label': 'Failed',
                'message': str(error),
            })
        else:
            st.update({
                'status': 'complete',
                'percent': 100,
                'label': message,
                'message': message,
            })
