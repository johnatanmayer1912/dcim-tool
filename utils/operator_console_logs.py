"""In-memory operator console log buffer (RB-ZT-03).

Read snapshots never consume entries. Session files and app_logger audit
logs are not stored here and are not deleted by this module.
"""
from __future__ import annotations

import collections
import threading
from typing import List, Tuple


MAX_BUFFER = 5000
MAX_LIMIT = 500
DEFAULT_LIMIT = 200


class OperatorConsoleLogBuffer:
    def __init__(self, maxlen: int = MAX_BUFFER):
        self._lock = threading.Lock()
        self._items: collections.deque = collections.deque(maxlen=maxlen)
        self._next_seq = 1

    def append(self, msg: str) -> int:
        text = '' if msg is None else str(msg)
        with self._lock:
            seq = self._next_seq
            self._next_seq += 1
            self._items.append((seq, text))
            return seq

    def snapshot(self, since: int, limit: int) -> Tuple[List[str], int]:
        if since < 0:
            since = 0
        if limit < 1:
            limit = 1
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT
        with self._lock:
            out: List[str] = []
            last = since
            for seq, msg in self._items:
                if seq <= since:
                    continue
                out.append(msg)
                last = seq
                if len(out) >= limit:
                    break
            return out, last

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

    def clear_for_tests(self) -> None:
        """Drop buffered operator pane lines (unit/integration tests only)."""
        with self._lock:
            self._items.clear()
