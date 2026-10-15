"""ntc-templates / TextFSM parse helpers (graceful if package missing).

Used by routing parsers and the NAPALM-style getter layer. Never raises on
missing templates — returns empty list and lets callers fall back to regex.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def ntc_available() -> bool:
    try:
        import ntc_templates  # noqa: F401
        return True
    except Exception:
        return False


def textfsm_available() -> bool:
    try:
        import textfsm  # noqa: F401
        return True
    except Exception:
        return False


def parse_cli(
    platform: str,
    command: str,
    output: str,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Parse CLI with ntc-templates when available.

    Returns (rows, error_or_none). Empty rows is not an error — callers
    should fall back to local TextFSM / regex.
    """
    if not (output or '').strip():
        return [], None
    plat = (platform or 'cisco_ios').strip().lower()
    cmd = (command or '').strip()
    try:
        from ntc_templates.parse import parse_output
        rows = parse_output(platform=plat, command=cmd, data=output)
        if isinstance(rows, list):
            return rows, None
        return [], 'ntc parse returned non-list'
    except Exception as exc:
        return [], str(exc)[:200]


def capability_report() -> Dict[str, Any]:
    return {
        'ntc_templates': ntc_available(),
        'textfsm': textfsm_available(),
        'note': 'Local modules/templates TextFSM files remain primary for route tables; ntc-templates expands interface/VLAN/CDP coverage.',
    }
