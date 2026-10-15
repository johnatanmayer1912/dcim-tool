"""Pytest hooks shared across the suite."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_operator_credential_state():
    """Prevent execute/vault tests from leaking into Socket.IO and other API tests."""
    import vlan_checker_web as web
    from utils.session_cred_cache import clear_session_credentials

    orig_cm = web.credential_manager
    yield
    web.credential_manager = orig_cm
    clear_session_credentials()
