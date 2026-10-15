"""Shared helpers for /api/execute tests after RB-ZT-08 credential_id-only policy."""
from __future__ import annotations

from modules.credential_manager import CredentialManager

EXECUTE_CREDENTIAL_ID = 'netops'
EXECUTE_SECRET = 'test-execute-secret'


def seed_execute_vault(web_module, storage_dir: str) -> str:
    """Install a minimal vault profile for execute API tests."""
    import os
    os.makedirs(storage_dir, exist_ok=True)
    cm = CredentialManager(storage_dir=storage_dir)
    cm.add_credential(EXECUTE_CREDENTIAL_ID, EXECUTE_SECRET, label='Execute test')
    web_module.credential_manager = cm
    return EXECUTE_CREDENTIAL_ID


def execute_json(**fields):
    """Build a JSON body for /api/execute with required credential_id."""
    payload = {
        'credential_id': EXECUTE_CREDENTIAL_ID,
        'username': EXECUTE_CREDENTIAL_ID,
    }
    payload.update(fields)
    for key in ('password', 'enable_pwd', 'enable_password', 'become_password'):
        payload.pop(key, None)
    return payload
