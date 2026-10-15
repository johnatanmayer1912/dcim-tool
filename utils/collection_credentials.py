# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - utils/collection_credentials.py
# ============================================================================
# PURPOSE: Credential bundling for plugin execution with fallback support.
# PROVIDES: Functions to bundle primary and fallback credentials for plugins.
#
# KEY_FUNCTIONS:
#   - bundle_for_plugin(credential_record, vault_extras):
#     Bundles primary, secondary, and tertiary credentials for plugin execution
#   - snmp_fields_from_record(record):
#     Extracts SNMP fields from credential record
#
# CREDENTIAL_FALLBACK:
#   bundle_for_plugin() includes fallback_credentials in the bundled dict
#   fallback_credentials is a list of dicts with username, password, secret, label
#   Secondary and tertiary credentials are added from vault_extras
#
# BUNDLED_FIELDS:
#   - username, password, secret (SSH credentials)
#   - snmp_version, snmp_community, snmp_port (SNMP v2c)
#   - snmp_v3_user, snmp_v3_auth_protocol, snmp_v3_auth_key (SNMP v3 auth)
#   - snmp_v3_priv_protocol, snmp_v3_priv_key (SNMP v3 priv)
#   - fallback_credentials (list of fallback credential dicts)
#   - secondary_credential (secondary credential dict)
#   - third_credential (tertiary credential dict)
#
# CONNECTIONS:
#   - Called by: modules/adapters.py (run_generic_plugin)
#   - Called by: vlan_checker_web.py (credential resolution)
#   - Uses: modules/credential_manager.py (credential retrieval)
#
# USAGE_PATTERN:
#   credentials = bundle_for_plugin(primary_credential, vault_extras)
#   fallback = credentials.get('fallback_credentials', [])
#
# ============================================================================
"""Merge SSH and optional separate SNMP vault profiles for collection tasks."""
from __future__ import annotations

from typing import Any, Dict, Optional

SNMP_KEYS = (
    'snmp_version', 'snmp_community', 'snmp_port', 'snmp_v3_user',
    'snmp_v3_auth_protocol', 'snmp_v3_auth_key', 'snmp_v3_priv_protocol',
    'snmp_v3_priv_key',
)


def snmp_fields_from_record(record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not record:
        return {
            'snmp_version': 'none',
            'snmp_community': '',
            'snmp_port': 161,
            'snmp_v3_user': '',
            'snmp_v3_auth_protocol': 'sha',
            'snmp_v3_auth_key': '',
            'snmp_v3_priv_protocol': 'aes',
            'snmp_v3_priv_key': '',
        }
    return {
        'snmp_version': record.get('snmp_version') or 'none',
        'snmp_community': record.get('snmp_community') or '',
        'snmp_port': record.get('snmp_port') or 161,
        'snmp_v3_user': record.get('snmp_v3_user') or '',
        'snmp_v3_auth_protocol': record.get('snmp_v3_auth_protocol') or 'sha',
        'snmp_v3_auth_key': record.get('snmp_v3_auth_key') or '',
        'snmp_v3_priv_protocol': record.get('snmp_v3_priv_protocol') or 'aes',
        'snmp_v3_priv_key': record.get('snmp_v3_priv_key') or '',
    }


def overlay_snmp_fields(base: Dict[str, Any], snmp_record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a copy of base with SNMP keys replaced from snmp_record when present."""
    out = dict(base)
    if not snmp_record:
        return out
    for key in SNMP_KEYS:
        val = snmp_record.get(key)
        if val not in (None, ''):
            out[key] = val
    out['snmp_credential_id'] = snmp_record.get('username') or snmp_record.get('credential_id') or out.get('snmp_credential_id')
    return out


def bundle_for_plugin(resolved: Dict[str, Any]) -> Dict[str, Any]:
    """Credentials dict for plugin run() — username/password/secret + SNMP + fallback credentials."""
    creds = {
        'username': resolved.get('username') or '',
        'password': resolved.get('password') or '',
        'secret': resolved.get('enable_pwd') or None,
    }
    for key in SNMP_KEYS:
        if key in resolved:
            creds[key] = resolved[key]
    if resolved.get('snmp_credential_id'):
        creds['snmp_credential_id'] = resolved['snmp_credential_id']
    
    # Include fallback credentials for primary -> secondary -> tertiary retry logic
    if resolved.get('fallback_credentials'):
        creds['fallback_credentials'] = resolved['fallback_credentials']
    if resolved.get('secondary_credential'):
        creds['secondary_credential'] = resolved['secondary_credential']
    if resolved.get('third_credential'):
        creds['third_credential'] = resolved['third_credential']
    
    return creds
