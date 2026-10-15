"""SNMP asset identity collector with SSH-fallback support."""
from __future__ import annotations

import socket
from typing import Any, Dict, Optional

from modules.mock_asset_lab import is_mock_host, mock_snmp_asset

# ENTITY-MIB / system OIDs used for chassis identity
OID_SYS_DESCR = '1.3.6.1.2.1.1.1.0'
OID_ENT_PHYSICAL_DESCR = '1.3.6.1.2.1.1.1.0'
OID_ENT_SERIAL = '1.3.6.1.2.1.47.1.1.1.1.11'
OID_ENT_MODEL = '1.3.6.1.2.1.47.1.1.1.1.13'


def snmp_credentials_configured(credentials: Optional[Dict[str, Any]]) -> bool:
    if not credentials:
        return False
    ver = str(credentials.get('snmp_version') or '').strip().lower()
    if ver in ('', 'none', 'off'):
        return False
    if ver in ('2c', 'v2c', '2'):
        return bool((credentials.get('snmp_community') or '').strip())
    if ver in ('3', 'v3'):
        return bool((credentials.get('snmp_v3_user') or '').strip())
    return False


def _snmp_get_v2c(host: str, community: str, oid: str, port: int = 161, timeout: float = 3.0) -> str:
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )
    except ImportError:
        try:
            from pysnmp_lextudio.hlapi import (  # type: ignore
                CommunityData,
                ContextData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                getCmd,
            )
        except ImportError as exc:
            raise RuntimeError(
                'SNMP support requires pysnmp or pysnmp-lextudio'
            ) from exc

    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        UdpTransportTarget((host, port), timeout=timeout, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    error_indication, error_status, _error_index, var_binds = next(iterator)
    if error_indication:
        raise RuntimeError(str(error_indication))
    if error_status:
        raise RuntimeError(str(error_status))
    for _oid, val in var_binds:
        return str(val)
    return ''


def _snmp_get_v3(
    host: str,
    user: str,
    auth_key: str,
    priv_key: str,
    auth_protocol: str,
    priv_protocol: str,
    oid: str,
    port: int = 161,
    timeout: float = 3.0,
) -> str:
    try:
        from pysnmp.hlapi import (
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            UsmUserData,
            getCmd,
            usmAesCfb128Protocol,
            usmDESPrivProtocol,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
        )
    except ImportError:
        try:
            from pysnmp_lextudio.hlapi import (  # type: ignore
                ContextData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                UsmUserData,
                getCmd,
                usmAesCfb128Protocol,
                usmDESPrivProtocol,
                usmHMACMD5AuthProtocol,
                usmHMACSHAAuthProtocol,
            )
        except ImportError as exc:
            raise RuntimeError(
                'SNMP support requires pysnmp or pysnmp-lextudio'
            ) from exc

    auth_map = {
        'md5': usmHMACMD5AuthProtocol,
        'sha': usmHMACSHAAuthProtocol,
        'none': None,
    }
    priv_map = {
        'des': usmDESPrivProtocol,
        'aes': usmAesCfb128Protocol,
        'none': None,
    }
    auth_proto = auth_map.get((auth_protocol or 'none').lower(), usmHMACSHAAuthProtocol)
    priv_proto = priv_map.get((priv_protocol or 'none').lower(), usmAesCfb128Protocol)
    auth_key = auth_key or None
    priv_key = priv_key or None

    user_data = UsmUserData(
        user,
        authKey=auth_key,
        privKey=priv_key,
        authProtocol=auth_proto,
        privProtocol=priv_proto,
    )
    iterator = getCmd(
        SnmpEngine(),
        user_data,
        UdpTransportTarget((host, port), timeout=timeout, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    error_indication, error_status, _error_index, var_binds = next(iterator)
    if error_indication:
        raise RuntimeError(str(error_indication))
    if error_status:
        raise RuntimeError(str(error_status))
    for _oid, val in var_binds:
        return str(val)
    return ''


def _snmp_get(host: str, credentials: Dict[str, Any], oid: str) -> str:
    ver = str(credentials.get('snmp_version') or '2c').strip().lower()
    port = int(credentials.get('snmp_port') or 161)
    timeout = float(credentials.get('snmp_timeout') or 3.0)
    if ver in ('2c', 'v2c', '2'):
        community = (credentials.get('snmp_community') or '').strip()
        if not community:
            raise RuntimeError('SNMP v2c community not configured')
        return _snmp_get_v2c(host, community, oid, port=port, timeout=timeout)
    if ver in ('3', 'v3'):
        user = (credentials.get('snmp_v3_user') or '').strip()
        if not user:
            raise RuntimeError('SNMP v3 user not configured')
        return _snmp_get_v3(
            host,
            user,
            credentials.get('snmp_v3_auth_key') or '',
            credentials.get('snmp_v3_priv_key') or '',
            credentials.get('snmp_v3_auth_protocol') or 'sha',
            credentials.get('snmp_v3_priv_protocol') or 'aes',
            oid,
            port=port,
            timeout=timeout,
        )
    raise RuntimeError(f'Unsupported SNMP version: {ver}')


def collect_snmp_asset(host: str, credentials: Dict[str, Any], log_func=None) -> Dict[str, Any]:
    host = (host or '').strip()
    if is_mock_host(host):
        data = mock_snmp_asset(host)
        if log_func:
            log_func(f'[{host}] Mock SNMP asset identity collected')
        return data

    if not snmp_credentials_configured(credentials):
        raise RuntimeError('SNMP credentials not configured in vault profile')

    if log_func:
        log_func(f'[{host}] SNMP fallback collection starting...')
    try:
        sys_descr = _snmp_get(host, credentials, OID_SYS_DESCR)
        serial = ''
        model = ''
        try:
            serial = _snmp_get(host, credentials, OID_ENT_SERIAL)
        except Exception:
            pass
        try:
            model = _snmp_get(host, credentials, OID_ENT_MODEL)
        except Exception:
            pass
    except socket.timeout as exc:
        raise RuntimeError('SNMP timeout') from exc

    return {
        'collection_method': 'snmp',
        'hostname': host,
        'sys_descr': sys_descr,
        'serial_number': serial.strip(),
        'pid': model.strip(),
        'vid': '',
        'software_version': '',
    }
