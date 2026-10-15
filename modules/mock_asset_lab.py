"""Deterministic mock asset inventory lab for offline QA.

Enable with NST_MOCK_ASSET_LAB=1 or pass force_mock=True in unit tests.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURE_ROOT = os.path.join(_PROJECT_ROOT, 'tests', 'fixtures')
_ASSET_FIXTURE_ROOT = os.path.join(_FIXTURE_ROOT, 'asset')

MOCK_HOSTS: Dict[str, Dict[str, str]] = {
    '10.99.1.1': {'role': 'ios', 'device_type': 'cisco_ios', 'hostname': 'MOCK-IOS-01'},
    '10.99.1.2': {'role': 'nxos', 'device_type': 'cisco_nxos', 'hostname': 'MOCK-NXOS-01'},
    '10.99.1.3': {'role': 'aci', 'device_type': 'cisco_aci', 'hostname': 'MOCK-ACI-APIC'},
    '10.99.1.4': {'role': 'ios_snmp_only', 'device_type': 'cisco_ios', 'hostname': 'MOCK-IOS-SNMP'},
    '10.99.1.5': {'role': 'ios_fallback_test', 'device_type': 'cisco_ios', 'hostname': 'MOCK-IOS-FALLBACK'},
}


@dataclass
class MockWarrantyEnrichment:
    """Dataclass for mock warranty and EOL/EOS enrichment data."""
    warranty_end: str
    warranty_status: str
    contract_status: str
    severity: str
    enrichment_source: str
    end_of_life: str
    end_of_support: str
    end_of_service: str
    model_name: str

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


def mock_enabled(force: bool = False) -> bool:
    if force:
        return True
    return os.environ.get('NST_MOCK_ASSET_LAB', '').strip().lower() in ('1', 'true', 'yes')


def is_mock_host(host: str, force: bool = False) -> bool:
    host = (host or '').strip()
    return mock_enabled(force) and host in MOCK_HOSTS


def mock_host_meta(host: str) -> Optional[Dict[str, str]]:
    return MOCK_HOSTS.get((host or '').strip())


def _read_fixture(name: str, *, asset: bool = False) -> str:
    root = _ASSET_FIXTURE_ROOT if asset else _FIXTURE_ROOT
    path = os.path.join(root, name)
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()


def mock_ssh_should_fail(host: str, username: str = None) -> bool:
    """Check if mock SSH should fail based on host and username.
    
    For fallback testing:
    - 10.99.1.5 (ios_fallback_test) fails with 'primary' username
    - 10.99.1.5 succeeds with 'secondary' or 'tertiary' username
    - 10.99.1.5 fails with 'fail1', 'fail2', 'fail3' usernames (for all-fail test)
    - 10.99.1.4 (ios_snmp_only) always fails (SNMP fallback test)
    """
    meta = mock_host_meta(host)
    if bool(meta and meta.get('role') == 'ios_snmp_only'):
        return True
    if bool(meta and meta.get('role') == 'ios_fallback_test'):
        # Fail for primary credential to test fallback
        if username == 'primary':
            return True
        # Fail for fail1, fail2, fail3 to test all-fail scenario
        if username in ('fail1', 'fail2', 'fail3'):
            return True
        # Succeed for secondary, tertiary, and other usernames
        return False
    return False


def mock_ssh_command(host: str, command: str, username: str = None) -> str:
    if mock_ssh_should_fail(host, username):
        raise ConnectionError('Mock SSH failure — credential fallback expected')
    meta = mock_host_meta(host) or {}
    role = meta.get('role', '')
    cmd = (command or '').strip().lower()
    if role in ('ios', 'ios_fallback_test'):
        if cmd.startswith('show version') or cmd.startswith('show ver'):
            return _read_fixture('ios_show_version.txt', asset=True)
        if cmd.startswith('show inventory'):
            return _read_fixture('ios_show_inventory.txt', asset=True)
    if role == 'nxos':
        if cmd.startswith('show version') or cmd.startswith('show ver'):
            return _read_fixture('discovery/nxos_show_version.txt')
        if cmd.startswith('show inventory'):
            return _read_fixture('nxos_show_inventory.txt', asset=True)
    return ''


def mock_snmp_asset(host: str) -> Dict[str, Any]:
    meta = mock_host_meta(host) or {}
    role = meta.get('role', '')
    if role in ('ios', 'ios_snmp_only'):
        return {
            'collection_method': 'snmp',
            'hostname': meta.get('hostname', host),
            'pid': 'C9200L-48P-4G',
            'vid': 'V02',
            'serial_number': 'FCW2345A1B2',
            'software_version': '17.9.4a',
            'sys_descr': 'Cisco IOS Software, C9200L Software',
        }
    if role == 'nxos':
        return {
            'collection_method': 'snmp',
            'hostname': meta.get('hostname', host),
            'pid': 'N9K-C93180YC-FX',
            'vid': 'V02',
            'serial_number': 'FOC12345678',
            'software_version': '9.3(5)',
            'sys_descr': 'Cisco NX-OS(tm) n9000',
        }
    return {}


def mock_aci_inventory(host: str) -> List[Dict[str, Any]]:
    raw = json.loads(_read_fixture('aci_fabric_nodes.json', asset=True))
    rows: List[Dict[str, Any]] = []
    for item in raw.get('imdata', []):
        attrs = (item.get('fabricNode') or {}).get('attributes') or {}
        rows.append({
            'hostname': attrs.get('name') or host,
            'pid': attrs.get('model') or '',
            'serial_number': attrs.get('serial') or '',
            'software_version': attrs.get('version') or '',
            'role': attrs.get('role') or '',
            'node_id': attrs.get('id') or '',
            'address': attrs.get('address') or host,
            'collection_method': 'aci_rest',
        })
    return rows


def mock_warranty_enrichment(host: str, serial_number: str) -> Dict[str, Any]:
    """Lab-only warranty hints — not live Cisco API data.
    
    Returns enriched warranty and EOL/EOS data based on mock host role.
    Uses dataclass for type safety and consistent field structure.
    
    Args:
        host: Mock host IP address
        serial_number: Device serial number (unused in mock but kept for interface)
        
    Returns:
        Dictionary with all warranty and EOL/EOS fields.
    """
    meta = mock_host_meta(host) or {}
    role = meta.get('role', '')
    today = datetime.now().date()
    
    if role == 'ios':
        end = today + timedelta(days=400)
        return MockWarrantyEnrichment(
            warranty_end=end.isoformat(),
            warranty_status='active',
            contract_status='Active (mock lab)',
            severity='ok',
            enrichment_source='mock_lab',
            end_of_life=(today + timedelta(days=1200)).isoformat(),
            end_of_support=(today + timedelta(days=1500)).isoformat(),
            end_of_service=(today + timedelta(days=1800)).isoformat(),
            model_name='Catalyst 9200L-48P-4G (mock)',
        ).to_dict()
    
    if role == 'nxos':
        end = today + timedelta(days=60)
        return MockWarrantyEnrichment(
            warranty_end=end.isoformat(),
            warranty_status='expiring_soon',
            contract_status='Expiring within 90 days (mock lab)',
            severity='warn',
            enrichment_source='mock_lab',
            end_of_life=(today + timedelta(days=800)).isoformat(),
            end_of_support=(today + timedelta(days=1100)).isoformat(),
            end_of_service=(today + timedelta(days=1400)).isoformat(),
            model_name='Nexus 93180YC-FX (mock)',
        ).to_dict()
    
    if role == 'aci':
        end = today - timedelta(days=30)
        return MockWarrantyEnrichment(
            warranty_end=end.isoformat(),
            warranty_status='expired',
            contract_status='Expired (mock lab)',
            severity='critical',
            enrichment_source='mock_lab',
            end_of_life=(today - timedelta(days=400)).isoformat(),
            end_of_support=(today - timedelta(days=200)).isoformat(),
            end_of_service=(today - timedelta(days=100)).isoformat(),
            model_name='APIC Controller (mock)',
        ).to_dict()
    
    if role == 'ios_snmp_only':
        end = today + timedelta(days=180)
        return MockWarrantyEnrichment(
            warranty_end=end.isoformat(),
            warranty_status='active',
            contract_status='SNMP fallback success (mock lab)',
            severity='ok',
            enrichment_source='mock_lab',
            end_of_life=(today + timedelta(days=1000)).isoformat(),
            end_of_support=(today + timedelta(days=1300)).isoformat(),
            end_of_service=(today + timedelta(days=1600)).isoformat(),
            model_name='Catalyst 9200L-48P-4G (mock)',
        ).to_dict()
    
    # Default case for unknown roles
    return MockWarrantyEnrichment(
        warranty_end='',
        warranty_status='unknown',
        contract_status='Requires Cisco API or portal',
        severity='info',
        enrichment_source='none',
        end_of_life='',
        end_of_support='',
        end_of_service='',
        model_name='',
    ).to_dict()
