"""Shared HTML match highlighting for search-it reports and web UI."""
from __future__ import annotations

import re
from html import escape

from utils.mac_utils import normalize_mac_hex

_MAC_SEP_RE = re.compile(r'[.:\-\s_]')


def escape_html(s: str) -> str:
    return escape(s or '')


def highlight_text_match(text: str, query: str) -> str:
    """Case-insensitive substring highlight with safe HTML."""
    if not query or not text:
        return escape_html(text or '')
    low = text.lower()
    q = query.lower()
    idx = low.find(q)
    if idx < 0:
        return escape_html(text)
    return (
        escape_html(text[:idx])
        + f'<mark class="nst-match">{escape_html(text[idx:idx + len(q)])}</mark>'
        + escape_html(text[idx + len(q):])
    )


def highlight_mac_match(display_mac: str, query_mac: str) -> str:
    """Highlight matching hex nibbles in a formatted MAC display string."""
    display = display_mac or ''
    if not display:
        return ''
    try:
        q_hex = normalize_mac_hex(query_mac)
    except ValueError:
        q_hex = _MAC_SEP_RE.sub('', (query_mac or '')).lower()
    if not q_hex:
        return escape_html(display)

    disp_hex = _MAC_SEP_RE.sub('', display).lower()
    start = disp_hex.find(q_hex)
    if start < 0 and disp_hex.startswith(q_hex[: min(len(q_hex), len(disp_hex))]):
        start = 0
        match_len = min(len(q_hex), len(disp_hex))
    elif start < 0:
        return escape_html(display)
    else:
        match_len = len(q_hex)
    end = start + match_len

    hex_idx = 0
    parts: list[str] = []
    in_match = False
    for ch in display:
        if ch.lower() in '0123456789abcdef':
            if hex_idx == start and not in_match:
                parts.append('<mark class="nst-match">')
                in_match = True
            parts.append(escape_html(ch))
            hex_idx += 1
            if in_match and hex_idx >= end:
                parts.append('</mark>')
                in_match = False
        else:
            parts.append(escape_html(ch))
    if in_match:
        parts.append('</mark>')
    return ''.join(parts)
