"""Discovery acceptance — blocked operator-truth conditions.

AI_CONTEXT: Profiles are hop-bounded, not a census. Cancel/partial must not look complete.
AI_CRAWL_NOTE: Empty neighbors = lack of evidence. Auth/timeout/failed stay distinct.
AI_TEST_NOTE: tests/test_discovery_acceptance.py
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# Phrases that must never describe a cancelled/partial job.
BLOCKED_COMPLETE_PHRASES = (
    'complete as collected',
    'full-fabric census',
    'crawl finished successfully',
)

BLOCKED_CONDITIONS = (
    'cancelled looks complete',
    'partial looks authoritative',
    'auth failure looks like generic completion',
    'empty neighbors interpreted as absence of devices',
    'profile names oversell capability (census)',
    'local-only cache treated as current truth without age',
)


def operator_truth_for_collection(coll: Optional[str]) -> str:
    """Same mapping as vlan_checker_web.api_discovery_status (keep in sync)."""
    if coll == 'cancelled':
        return 'not complete truth — cancelled'
    if coll == 'partial':
        return 'not complete truth — partial'
    if coll == 'error':
        return 'error'
    if coll == 'running':
        return 'running'
    return 'complete as collected (CDP/LLDP hop-bounded; not overlay)'


def cancelled_must_not_look_complete(coll: str, truth: str) -> None:
    if coll == 'cancelled':
        for phrase in BLOCKED_COMPLETE_PHRASES:
            if phrase in (truth or '').lower() and phrase != 'complete as collected':
                pass
        if 'complete as collected' in (truth or '').lower():
            raise AssertionError('cancelled job looks complete')
        if 'not complete truth' not in (truth or '').lower():
            raise AssertionError('cancelled job missing not-complete-truth')


def profiles_must_not_claim_census(profiles: Dict[str, Dict[str, Any]]) -> None:
    for name, spec in profiles.items():
        if spec.get('census') is not False:
            raise AssertionError(f'profile {name} must set census=False')
        note = (spec.get('truth_note') or '').lower()
        if 'census' in name.lower():
            raise AssertionError(f'profile name oversells: {name}')
        if 'not' not in note and 'not a full-fabric' not in note:
            if 'hop-bounded' not in note and 'not complete' not in note:
                raise AssertionError(f'profile {name} truth_note too weak')
