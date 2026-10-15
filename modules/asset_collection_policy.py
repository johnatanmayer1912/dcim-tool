# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/asset_collection_policy.py
# ============================================================================
# PURPOSE: Asset collection policy for Cisco devices with credential fallback.
# PROVIDES: SSH, SNMP, and ACI REST collection methods.
#
# KEY_FUNCTIONS:
#   - collect_device_assets(device, credentials, params, log_func):
#     Main asset collection orchestrator
#   - _collect_ssh(device, credentials, include_modules, log_func):
#     SSH-based asset collection with credential fallback
#   - _collect_snmp(device, credentials, log_func):
#     SNMP-based asset collection
#   - _collect_aci(device, credentials, log_func):
#     ACI REST-based asset collection
#
# CREDENTIAL_FALLBACK:
#   _collect_ssh() passes fallback_credentials to safe_connection()
#   Mock path simulates credential fallback with username-based retry logic
#   Logs each credential attempt with attempt number (1/3, 2/3, 3/3)
#
# COLLECTION_POLICY:
#   - ssh_first: SSH primary, SNMP fallback
#   - ssh_only: SSH only
#   - snmp_only: SNMP only
#
# ASSET_FIELDS:
#   - host, device_type, timestamp
#   - hostname, software_version
#   - pid, vid, serial_number
#   - modules, module_count
#   - collection_method
#
# CONNECTIONS:
#   - Called by: modules/plugins/cisco_asset_warranty_plugin.py
#   - Calls: modules/network_base.py (safe_connection)
#   - Calls: modules/mock_asset_lab.py (mock SSH for testing)
#   - Calls: modules/snmp_asset_collector.py (SNMP collection)
#   - Calls: modules/cisco_aci_inventory.py (ACI REST)
#
# USAGE_PATTERN:
#   bundle = collect_device_assets(device, credentials, params, log_func)
#   assets = bundle.get('assets', [])
#
# ============================================================================
"""SSH-first asset collection with SNMP fallback policy."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from modules.cisco_aci_inventory import collect_aci_fabric_nodes
from modules.mock_asset_lab import (
    is_mock_host,
    mock_enabled,
    mock_host_meta,
    mock_ssh_command,
    mock_ssh_should_fail,
    mock_warranty_enrichment,
)
from modules.network_base import safe_connection, resolve_hostname_from_prompt
from modules.parsers.cisco_asset_inventory import (
    merge_asset_identity,
    parse_inventory_blocks,
    parse_ios_nxos_version,
)
from modules.snmp_asset_collector import collect_snmp_asset, snmp_credentials_configured

# Exact operator-facing label for non-Cisco platforms in Asset & Warranty reports
NON_CISCO_DEVICE_LABEL = 'not a cisco device'

_CISCO_DEVICE_TYPE_MARKERS = (
    'cisco',
    'ios',
    'nxos',
    'nexus',
    'xe',
    'asa',
    'ftd',
    'apic',
    'aci',
    'iosxe',
    'ios_xe',
    'catalyst',
    'isr',
    'asr',
    'meraki',
    'wlc',
)

_NON_CISCO_DEVICE_TYPE_MARKERS = (
    'juniper',
    'junos',
    'arista',
    'eos',
    'huawei',
    'hp_',
    'procurve',
    'fortinet',
    'paloalto',
    'panos',
    'mikrotik',
    'vyos',
    'linux',
    'windows',
    'aruba',
    'dell_os',
    'sonic',
)


def is_cisco_platform(device_type: Optional[str]) -> bool:
    """Return True when inventory device_type indicates a Cisco-family platform.

    Known non-Cisco vendors (Juniper, Arista, …) return False.
    Empty device_type defaults to True (plugin inventory often omits type and
    means cisco_ios). Unrecognized non-empty types are treated as non-Cisco
    so reports never invent Cisco warranty for foreign platforms.
    """
    dt = (device_type or '').strip().lower().replace('-', '_').replace(' ', '_')
    if not dt:
        return True
    if any(marker in dt for marker in _NON_CISCO_DEVICE_TYPE_MARKERS):
        return False
    if any(marker in dt for marker in _CISCO_DEVICE_TYPE_MARKERS):
        return True
    return False



def non_cisco_asset_record(device: Dict[str, Any], host: str, timestamp: str) -> Dict[str, Any]:
    """Build an honest Asset & Warranty row for Juniper / other non-Cisco devices."""
    device_type = (device.get('device_type') or '').strip() or 'unknown'
    return {
        'host': host,
        'device_type': device_type,
        'timestamp': timestamp,
        'hostname': device.get('hostname') or host,
        'collection_method': 'skipped_non_cisco',
        'pid': '',
        'vid': '',
        'serial_number': '',
        'software_version': '',
        'warranty_end': '',
        'warranty_status': NON_CISCO_DEVICE_LABEL,
        'contract_status': 'Cisco Asset & Warranty applies to Cisco platforms only',
        'severity': 'info',
        'enrichment_source': 'platform_gate',
        'end_of_life': '',
        'end_of_support': '',
        'end_of_service': '',
        'model_name': NON_CISCO_DEVICE_LABEL,
        'platform_note': NON_CISCO_DEVICE_LABEL,
        'error': '',
    }


@dataclass
class WarrantyFields:
    """Dataclass for warranty and EOL/EOS enrichment fields."""
    warranty_end: str = ''
    warranty_status: str = 'unknown'
    contract_status: str = 'Requires Cisco SN2INFO/EoX API or portal'
    severity: str = 'info'
    enrichment_source: str = 'none'
    # EOL/EOS enrichment fields
    end_of_life: str = ''
    end_of_support: str = ''
    end_of_service: str = ''
    model_name: str = ''

    def to_dict(self) -> Dict[str, str]:
        """Convert dataclass to dictionary for compatibility."""
        return {
            'warranty_end': self.warranty_end,
            'warranty_status': self.warranty_status,
            'contract_status': self.contract_status,
            'severity': self.severity,
            'enrichment_source': self.enrichment_source,
            'end_of_life': self.end_of_life,
            'end_of_support': self.end_of_support,
            'end_of_service': self.end_of_service,
            'model_name': self.model_name,
        }


def _identity_complete(record: Dict[str, Any]) -> bool:
    return bool((record.get('serial_number') or '').strip() and (record.get('pid') or '').strip())


def _collect_ssh(
    device: Dict[str, Any],
    credentials: Dict[str, Any],
    include_modules: bool,
    log_func: Optional[Callable[[str], None]],
) -> Dict[str, Any]:
    host = device.get('host', 'unknown')
    device_type = (device.get('device_type') or 'cisco_ios').lower()
    username = credentials.get('username', '')

    if is_mock_host(host):
        # Simulate credential fallback for mock hosts
        fallback_credentials = credentials.get('fallback_credentials', [])
        creds_to_try = [{'username': username, 'label': 'Primary'}]
        for fb in fallback_credentials:
            if isinstance(fb, dict) and fb.get('username'):
                creds_to_try.append({'username': fb['username'], 'label': fb.get('label', 'Fallback')})
        
        last_error = None
        for idx, cred in enumerate(creds_to_try):
            curr_user = cred['username']
            lbl = cred['label']
            if idx > 0:
                lbl = f"Secondary ({lbl})" if idx == 1 else f"Third ({lbl})"
            
            if log_func:
                if len(creds_to_try) > 1:
                    log_func(f"[{host}] Connecting to device using {lbl} [{curr_user}] (attempt {idx+1}/{len(creds_to_try)})...")
                else:
                    log_func(f"[{host}] Connecting to device...")
            
            try:
                if mock_ssh_should_fail(host, curr_user):
                    raise ConnectionError(f'Mock SSH failure for {curr_user}')
                version_output = mock_ssh_command(host, 'show version', curr_user)
                inventory_output = mock_ssh_command(host, 'show inventory', curr_user) if include_modules else mock_ssh_command(host, 'show inventory', curr_user)
                version_fields = parse_ios_nxos_version(version_output)
                inventory_rows = parse_inventory_blocks(inventory_output)
                meta = mock_host_meta(host) or {}
                merged = merge_asset_identity(version_fields, inventory_rows, include_modules=include_modules)
                merged['hostname'] = meta.get('hostname') or merged.get('hostname') or host
                merged['collection_method'] = 'ssh'
                merged['device_type'] = device_type
                if log_func:
                    log_func(f"[{host}] Successfully connected using {lbl} [{curr_user}]")
                return merged
            except ConnectionError as e:
                last_error = str(e)
                if log_func:
                    log_func(f"[{host}] {lbl} connection failed [{curr_user}]: {last_error}")
        
        # All credentials failed
        raise ConnectionError(last_error or 'All credential attempts failed')

    with safe_connection(
        device,
        credentials['username'],
        credentials['password'],
        credentials.get('secret'),
        log_func,
        fallback_credentials=credentials.get('fallback_credentials'),
    ) as conn:
        true_host = resolve_hostname_from_prompt(conn, host)
        version_output = conn.send_command('show version')
        inventory_output = ''
        inv_cmds = ['show inventory', 'show diag']
        for cmd in inv_cmds:
            try:
                inventory_output = conn.send_command(cmd)
                if inventory_output and '%' not in inventory_output:
                    break
            except Exception:
                continue
        version_fields = parse_ios_nxos_version(version_output)
        if true_host:
            version_fields['hostname'] = true_host
        inventory_rows = parse_inventory_blocks(inventory_output)
        merged = merge_asset_identity(version_fields, inventory_rows, include_modules=include_modules)
        merged['collection_method'] = 'ssh'
        merged['device_type'] = device_type
        merged['hostname'] = merged.get('hostname') or true_host or host
        return merged


def collect_device_assets(
    device: Dict[str, Any],
    credentials: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    log_func: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Collect asset rows for one inventory device.

    Policy (default ssh_first):
    1. ACI/APIC → REST fabricNode inventory
    2. SSH show version + show inventory
    3. On SSH failure or incomplete PID/SN → SNMP fallback when configured
    """
    params = params or {}
    host = device.get('host', 'unknown')
    device_type = (device.get('device_type') or '').lower()
    include_modules = bool(params.get('include_modules', True))
    policy = str(params.get('collection_policy') or 'ssh_first').lower()
    snmp_fallback = params.get('snmp_fallback')
    if snmp_fallback is None:
        snmp_fallback = True
    else:
        snmp_fallback = bool(snmp_fallback)

    timestamp = datetime.now().isoformat()
    base: Dict[str, Any] = {
        'host': host,
        'device_type': device_type,
        'timestamp': timestamp,
    }

    rows: List[Dict[str, Any]] = []

    # Honest gate: Juniper / Arista / other non-Cisco platforms are not Cisco Asset targets
    if device_type and not is_cisco_platform(device_type):
        if log_func:
            log_func(
                f'[{host}] Platform {device_type!r} is {NON_CISCO_DEVICE_LABEL} — '
                f'skipping Cisco Asset & Warranty collection'
            )
        rows.append(non_cisco_asset_record(device, host, timestamp))
        return {'assets': rows, 'collection_summary': 'not_a_cisco_device'}

    if device_type in ('cisco_aci', 'apic', 'cisco_apic'):
        fabric_rows = collect_aci_fabric_nodes(host, credentials, log_func=log_func)
        for node in fabric_rows:
            rec = {**base, **node}
            if mock_enabled() and is_mock_host(host):
                rec.update(mock_warranty_enrichment(host, rec.get('serial_number', '')))
            else:
                rec.update(_default_warranty_fields())
            rows.append(rec)
        return {'assets': rows, 'collection_summary': f'aci:{len(rows)}'}

    ssh_error = ''
    ssh_record: Dict[str, Any] = {}

    if policy != 'snmp_only':
        try:
            ssh_record = _collect_ssh(device, credentials, include_modules, log_func)
            if _identity_complete(ssh_record) or policy == 'ssh_only':
                rec = {**base, **ssh_record}
                if mock_enabled() and is_mock_host(host):
                    rec.update(mock_warranty_enrichment(host, rec.get('serial_number', '')))
                else:
                    rec.update(_default_warranty_fields())
                rows.append(rec)
                return {'assets': rows, 'collection_summary': 'ssh'}
        except Exception as exc:
            ssh_error = str(exc)
            if log_func:
                log_func(f'[{host}] SSH collection failed: {ssh_error}')
                log_func(f'[{host}] All credential attempts exhausted. Connection unsuccessful.')
            if policy == 'ssh_only':
                # Return error without creating demo asset record
                rec = {**base, 'collection_method': 'ssh', 'error': ssh_error, 'severity': 'critical'}
                rows.append(rec)
                return {'assets': rows, 'collection_summary': 'ssh_failed'}

    if policy == 'ssh_only':
        # Only create record if we have some data from SSH attempt
        if ssh_record and (ssh_record.get('pid') or ssh_record.get('serial_number')):
            rec = {**base, **ssh_record, 'collection_method': ssh_record.get('collection_method', 'ssh')}
            if not _identity_complete(rec):
                rec['severity'] = 'warn'
                rec['error'] = rec.get('error') or 'Incomplete identity from SSH'
            if mock_enabled() and is_mock_host(host):
                rec.update(mock_warranty_enrichment(host, rec.get('serial_number', '')))
            else:
                rec.update(_default_warranty_fields())
            rows.append(rec)
            return {'assets': rows, 'collection_summary': 'ssh_only'}
        else:
            # No valid data from SSH - return error without demo enrichment
            rec = {**base, 'collection_method': 'ssh', 'error': ssh_error or 'SSH connection failed - no valid credentials', 'severity': 'critical'}
            rows.append(rec)
            return {'assets': rows, 'collection_summary': 'ssh_failed'}

    if snmp_fallback and snmp_credentials_configured(credentials):
        try:
            snmp_rec = collect_snmp_asset(host, credentials, log_func=log_func)
            rec = {**base, **snmp_rec}
            if ssh_error:
                rec['ssh_error'] = ssh_error
                rec['fallback_reason'] = 'ssh_failed_or_incomplete'
            if mock_enabled() and is_mock_host(host):
                rec.update(mock_warranty_enrichment(host, rec.get('serial_number', '')))
            else:
                rec.update(_default_warranty_fields())
            rows.append(rec)
            return {'assets': rows, 'collection_summary': 'snmp_fallback'}
        except Exception as exc:
            if log_func:
                log_func(f'[{host}] SNMP fallback failed: {exc}')
            rec = {
                **base,
                'collection_method': 'failed',
                'error': f'SSH: {ssh_error or "incomplete"}; SNMP: {exc}',
                'severity': 'critical',
            }
            rec.update(_default_warranty_fields())
            rows.append(rec)
            return {'assets': rows, 'collection_summary': 'failed'}

    rec = {
        **base,
        **ssh_record,
        'collection_method': ssh_record.get('collection_method') or 'ssh',
        'error': ssh_error or 'Incomplete identity; SNMP not configured',
        'severity': 'critical' if ssh_error else 'warn',
    }
    if mock_enabled() and is_mock_host(host):
        rec.update(mock_warranty_enrichment(host, rec.get('serial_number', '')))
    else:
        rec.update(_default_warranty_fields())
    rows.append(rec)
    return {'assets': rows, 'collection_summary': 'incomplete'}


def _default_warranty_fields() -> Dict[str, str]:
    """Return default warranty and EOL/EOS fields for unenriched assets.
    
    Uses dataclass for type safety and consistency. All EOL/EOS fields are
    included to ensure CSV/HTML output has consistent column structure even
    when enrichment fails or database is unavailable.
    
    Returns:
        Dictionary with all warranty and EOL/EOS fields initialized to defaults.
    """
    return WarrantyFields().to_dict()
