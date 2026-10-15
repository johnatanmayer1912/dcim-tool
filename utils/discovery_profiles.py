"""
Discovery scan profiles — bounded, offline-friendly crawl presets.

AI_CONTEXT: Named depth/timeout presets. Not a fabric census.
AI_FLOW: UI/API scan_profile → resolve_scan_profile → crawl max_depth/timeout
AI_IMPACTS: /api/discovery/run, Discovery tab
AI_CRAWL_NOTE: conservative=1 hop; wide=3 hops still SSH-only CDP/LLDP
AI_OFFLINE_NOTE: demo_mode ignores SSH; profiles still label expected hop radius
AI_BREADCRUMB: vlan_checker_web.api_discovery_run → network_discovery.crawl_network_multi_seed
AI_SAFE: Labels and numbers here. Do not raise max_depth above 3 without API bound + tests.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

PROFILES: Dict[str, Dict[str, Any]] = {
    'conservative': {
        'max_depth': 1,
        'timeout': 20,
        'label': 'Conservative — 1 hop (neighbors of seeds only)',
        'truth_note': 'Not a full-fabric census. Partial graphs are not complete truth.',
        'census': False,
        'not_snmp': True,
    },
    'standard': {
        'max_depth': 2,
        'timeout': 30,
        'label': 'Standard — 2 hops',
        'truth_note': 'Not a full-fabric census. Partial graphs are not complete truth.',
        'census': False,
        'not_snmp': True,
    },
    'wide': {
        'max_depth': 3,
        'timeout': 45,
        'label': 'Wide — 3 hops (slower, larger blast)',
        'truth_note': 'Still hop-bounded CDP/LLDP. Not SNMP/NETCONF. Not complete truth if cancelled or failed hosts exist.',
        'census': False,
        'not_snmp': True,
    },
}

DEFAULT_PROFILE = 'standard'


def resolve_scan_profile(
    name: Optional[str] = None,
    *,
    max_depth: Optional[int] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """Profile fills defaults; explicit max_depth/timeout win."""
    key = (name or DEFAULT_PROFILE).strip().lower()
    if key not in PROFILES:
        key = DEFAULT_PROFILE
    base = dict(PROFILES[key])
    if max_depth is not None:
        base['max_depth'] = int(max_depth)
    if timeout is not None:
        base['timeout'] = int(timeout)
    base['profile'] = key
    return base


def classify_discovery_failure(exc: BaseException) -> str:
    """Map SSH/connect errors to operator-visible scan_state (not a generic blob)."""
    msg = str(exc or '').lower()
    if any(
        tok in msg
        for tok in (
            'auth', 'password', 'permission denied', 'login failed',
            'authentication', 'access denied',
        )
    ):
        return 'auth_denied'
    if any(tok in msg for tok in ('timed out', 'timeout', 'read timeout', 'eof')):
        return 'timeout'
    return 'failed'
