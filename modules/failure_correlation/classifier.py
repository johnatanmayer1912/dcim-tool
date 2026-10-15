"""Classify raw log lines into relevant evidence vs noise."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from modules.failure_correlation.rules import (
    CAT_NOISE,
    SEVERITY_ORDER,
    extract_interface,
    match_line,
)

_TS_RE = re.compile(
    r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+\w+)?)'
    r'|^(\d{4}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
    r'|^(\d{2}:\d{2}:\d{2})'
)


def split_log_lines(blob: str) -> List[str]:
    lines = []
    for raw in (blob or '').splitlines():
        s = raw.strip('\r')
        if not s.strip():
            continue
        # Skip pager / prompt crumbs
        if s.strip() in ('--More--',) or s.strip().endswith('#') and len(s) < 40:
            continue
        lines.append(s)
    return lines


def classify_lines(raw_log: str, source: str = 'show logging') -> List[Dict[str, Any]]:
    """Return classified events (includes noise — filter later)."""
    events: List[Dict[str, Any]] = []
    for idx, line in enumerate(split_log_lines(raw_log)):
        hit = match_line(line)
        ts_m = _TS_RE.match(line.lstrip())
        event = {
            'index': idx,
            'source': source,
            'line': line[:800],
            'timestamp': (ts_m.group(0) if ts_m else ''),
            'interface': extract_interface(line),
            'relevant': False,
            'category': 'unclassified',
            'severity': 'info',
            'rule_id': None,
            'symptom_code': None,
            'title': None,
            'hint': None,
            'match': None,
        }
        if hit:
            event.update({
                'relevant': hit['category'] != CAT_NOISE,
                'category': hit['category'],
                'severity': hit['severity'],
                'rule_id': hit['rule_id'],
                'symptom_code': hit['symptom_code'],
                'title': hit['title'],
                'hint': hit['hint'],
                'match': hit['match'],
            })
            if hit['category'] == CAT_NOISE:
                event['relevant'] = False
        events.append(event)
    return events


def filter_relevant(events: List[Dict[str, Any]], include_noise: bool = False) -> List[Dict[str, Any]]:
    out = []
    for e in events:
        if e.get('rule_id') is None:
            continue
        if e.get('category') == CAT_NOISE and not include_noise:
            continue
        if not e.get('relevant') and not include_noise:
            continue
        out.append(e)
    out.sort(key=lambda x: SEVERITY_ORDER.get(x.get('severity') or 'info', 9))
    return out


def summarize_counts(events: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {
        'lines_total': len(events),
        'matched': 0,
        'relevant': 0,
        'noise': 0,
        'unclassified': 0,
    }
    for e in events:
        if e.get('rule_id'):
            counts['matched'] += 1
            if e.get('category') == CAT_NOISE:
                counts['noise'] += 1
            elif e.get('relevant'):
                counts['relevant'] += 1
        else:
            counts['unclassified'] += 1
    return counts
