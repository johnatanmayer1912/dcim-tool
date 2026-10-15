"""Thread-local optional become/root password for Junos tasks."""
from __future__ import annotations

import threading

_local = threading.local()


def set_task_become_password(password: str) -> None:
    _local.become_password = password or ''


def get_task_become_password() -> str:
    return getattr(_local, 'become_password', '') or ''


def clear_task_become_password() -> None:
    _local.become_password = ''
