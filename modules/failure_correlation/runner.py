"""Orchestrate fleet failure correlation runs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import os

from modules.failure_correlation.classifier import classify_lines, filter_relevant, summarize_counts
from modules.failure_correlation.collector import (
    collect_device_failure_evidence,
    merge_logging_blob,
)
from modules.failure_correlation.correlator import build_hypotheses, fleet_rollups
from modules.failure_correlation.report import render_correlation_html, write_json

LogFn = Optional[Callable[[str], None]]


def analyze_collected(collected: Dict[str, Any]) -> Dict[str, Any]:
    """Pure analysis path (unit-testable without SSH)."""
    host = collected.get('true_host') or collected.get('host') or '?'
    blob = merge_logging_blob(collected.get('raw') or {})
    events = classify_lines(blob, source='show logging')
    relevant = filter_relevant(events)
    cli_ctx = {
        'interfaces_down': collected.get('interfaces_down') or {},
        'vpc_peer_down': bool(collected.get('vpc_peer_down')),
        'vpc_summary': collected.get('vpc_summary') or '',
    }
    hypotheses = build_hypotheses(relevant, host=host, cli_context=cli_ctx)
    return {
        'host': collected.get('host'),
        'true_host': host,
        'platform': collected.get('platform'),
        'status': collected.get('status'),
        'errors': collected.get('errors') or [],
        'counts': summarize_counts(events),
        'events_relevant': relevant,
        'events_all_count': len(events),
        'hypotheses': hypotheses,
        'interfaces_down': cli_ctx['interfaces_down'],
        'vpc_peer_down': cli_ctx['vpc_peer_down'],
        'vpc_summary': cli_ctx['vpc_summary'],
    }


def run_failure_correlation(
    devices: List[Dict[str, Any]],
    user: str,
    pwd: str,
    enb_pwd: str,
    log: LogFn,
    run_dir: str,
) -> Dict[str, Any]:
    """Collect + correlate + write HTML/JSON into run_dir."""
    _log = log or (lambda _m: None)
    os.makedirs(run_dir, exist_ok=True)
    device_results: List[Dict[str, Any]] = []

    for dev in devices:
        host = dev.get('host') or '?'
        _log(f"[CORR] Collecting failure evidence from {host}…")
        collected = collect_device_failure_evidence(dev, user, pwd, enb_pwd, log=_log)
        analyzed = analyze_collected(collected)
        device_results.append(analyzed)
        _log(
            f"[CORR] {analyzed['true_host']}: "
            f"{analyzed['counts'].get('relevant', 0)} relevant · "
            f"{len(analyzed['hypotheses'])} hypotheses"
        )

    rollups = fleet_rollups(device_results)
    bundle = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'feature': 'failure_correlation',
        'devices': device_results,
        'rollups': rollups,
        'honesty': (
            'Evidence-bound explanations only. Incomplete when logs missing. '
            'Not a SIEM; complements LibreNMS/Loki/SuzieQ.'
        ),
    }

    html_path = os.path.join(run_dir, 'failure_correlation.html')
    json_path = os.path.join(run_dir, 'failure_correlation.json')
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(render_correlation_html(bundle))
    write_json(json_path, bundle)

    # Compact engineer TXT
    txt_path = os.path.join(run_dir, 'report.txt')
    with open(txt_path, 'w', encoding='utf-8') as fh:
        fh.write('NST Failure Correlation\n')
        fh.write(f"Generated: {bundle['generated_at']}\n")
        fh.write(f"Hypotheses: {rollups.get('hypothesis_count', 0)}\n\n")
        for h in rollups.get('top_hypotheses') or []:
            fh.write(
                f"- [{h.get('confidence_label')}] {h.get('host')} / {h.get('object')}: "
                f"{h.get('title')}\n  WHY: {h.get('why')}\n  NEXT: {h.get('hint')}\n\n"
            )

    bundle['html_path'] = html_path
    bundle['json_path'] = json_path
    bundle['txt_path'] = txt_path
    return bundle
