"""Vault profile type helpers (SSH-only, SNMP-only, combined)."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

PROFILE_SSH_ONLY = 'ssh_only'
PROFILE_SNMP_ONLY = 'snmp_only'
PROFILE_SSH_AND_SNMP = 'ssh_and_snmp'
ALLOWED_PROFILE_TYPES = frozenset({PROFILE_SSH_ONLY, PROFILE_SNMP_ONLY, PROFILE_SSH_AND_SNMP})


def normalize_profile_type(raw: Optional[str]) -> str:
    val = (raw or PROFILE_SSH_AND_SNMP).strip().lower()
    if val in ALLOWED_PROFILE_TYPES:
        return val
    return PROFILE_SSH_AND_SNMP


def profile_has_ssh(cred: Dict[str, Any]) -> bool:
    ptype = normalize_profile_type(cred.get('profile_type'))
    if ptype == PROFILE_SNMP_ONLY:
        return False
    return bool((cred.get('password') or '').strip() and cred.get('password') != '-')


def profile_has_snmp_config(cred: Dict[str, Any]) -> bool:
    from modules.credential_manager import _credential_has_snmp
    return _credential_has_snmp(cred)


def validate_profile_fields(
    profile_type: str,
    password: Optional[str],
    snmp_version: Optional[str] = None,
    snmp_community: Optional[str] = None,
    snmp_v3_user: Optional[str] = None,
) -> Tuple[bool, str]:
    ptype = normalize_profile_type(profile_type)
    snmp_stub = {
        'snmp_version': snmp_version,
        'snmp_community': snmp_community,
        'snmp_v3_user': snmp_v3_user,
    }
    has_snmp = profile_has_snmp_config(snmp_stub)
    pwd = (password or '').strip()

    if ptype == PROFILE_SNMP_ONLY:
        if not has_snmp:
            return False, 'SNMP-only profile requires SNMP v2c community or v3 user'
        return True, ''

    if ptype == PROFILE_SSH_ONLY:
        if not pwd:
            return False, 'SSH password is required for ssh_only profiles'
        return True, ''

    # ssh_and_snmp
    if not pwd:
        return False, 'Password cannot be empty for ssh_and_snmp profiles'
    return True, ''
