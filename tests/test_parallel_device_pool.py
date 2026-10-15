"""Parallel SSH pool and IM cancel (G-001) regression tests."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from utils.parallel_device_pool import foreach_device_parallel, get_max_workers


def test_get_max_workers_default():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("NST_SSH_MAX_WORKERS", None)
        assert get_max_workers() == 5


def test_get_max_workers_env():
    with patch.dict(os.environ, {"NST_SSH_MAX_WORKERS": "8"}):
        assert get_max_workers() == 8


def test_get_max_workers_clamped():
    with patch.dict(os.environ, {"NST_SSH_MAX_WORKERS": "99"}):
        assert get_max_workers() == 20


def test_foreach_device_parallel_immediate_abort():
    devices = [{"host": f"h{i}"} for i in range(5)]

    def worker(dev, idx):
        return {"host": dev["host"]}

    with patch("utils.parallel_device_pool._should_abort", return_value=True):
        results = foreach_device_parallel(devices, worker, max_workers=5)
    assert all(r is None for r in results)


def test_foreach_device_serial_order():
    devices = [{"host": "a"}, {"host": "b"}]
    results = foreach_device_parallel(
        devices,
        lambda d, i: d["host"],
        max_workers=1,
    )
    assert results == ["a", "b"]


def test_im_should_abort_without_cancel():
    from modules.plugins.interface_manager import _im_should_abort

    with patch("utils.task_control_plane.should_abort", return_value=False):
        assert _im_should_abort() is False


def test_im_should_abort_when_cancelled():
    from modules.plugins.interface_manager import _im_should_abort

    with patch("utils.task_control_plane.should_abort", return_value=True):
        assert _im_should_abort() is True


def test_im_cancelled_result():
    from modules.plugins.interface_manager import _im_cancelled_result

    r = _im_cancelled_result("sw1", "cisco_ios", {"path": "/tmp/bak"}, None)
    assert r["deployment_status"] == "cancelled"
    assert r["true_host"] == "sw1"
    assert r["cancelled"] is True
