"""Relevance scoring for partial text / MAC search results."""
from __future__ import annotations

import re
from typing import Any, Dict


def _norm_mac(s: str) -> str:
    return re.sub(r'[.:\-\s_]', '', (s or '')).lower()


def text_match_score(query: str, *fields: str) -> int:
    """Higher = better match. Exact > prefix > word boundary > substring."""
    q = (query or '').strip().lower()
    if not q:
        return 0
    best = 0
    for raw in fields:
        text = (raw or '').lower()
        if not text:
            continue
        if text == q:
            best = max(best, 100)
        elif text.startswith(q):
            best = max(best, 85)
        elif re.search(rf'\b{re.escape(q)}\b', text):
            best = max(best, 70)
        elif q in text:
            best = max(best, 50)
    return best


def mac_match_score(query: str, *mac_fields: str) -> int:
    q = _norm_mac(query)
    if not q:
        return 0
    best = 0
    for raw in mac_fields:
        hay = _norm_mac(raw)
        if not hay:
            continue
        if hay == q:
            best = max(best, 100)
        elif hay.startswith(q):
            best = max(best, 90)
        elif q in hay:
            best = max(best, 65)
    return best


def description_row_score(query: str, row: Dict[str, Any]) -> int:
    if row.get('error'):
        return -1
    desc = row.get('description', '')
    iface = row.get('interface', '')
    host = row.get('hostname', '') or row.get('device_ip', '')
    return max(
        text_match_score(query, desc),
        text_match_score(query, iface) - 5,
        text_match_score(query, host) - 10,
        mac_match_score(query, desc, iface),
    )


def sort_description_rows(query: str, rows: list) -> list:
    return sorted(
        rows,
        key=lambda r: (-description_row_score(query, r), (r.get('hostname') or '').lower(), (r.get('interface') or '').lower()),
    )
