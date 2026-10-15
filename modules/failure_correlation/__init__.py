"""Failure Correlation Engine — explain interface/vPC/protocol failures from CLI evidence."""

from modules.failure_correlation.runner import analyze_collected, run_failure_correlation
from modules.failure_correlation.rules import all_rule_ids, match_line

__all__ = [
    'analyze_collected',
    'run_failure_correlation',
    'match_line',
    'all_rule_ids',
]
