"""Shared helpers for mandatory QA scaffold tests."""
from __future__ import annotations

import os

import pytest

# Scaffold tests are collected but skipped unless explicitly enabled.
# Enable when implementing: NST_MANDATORY_QA_FULL=1 pytest tests/qa/ -m mandatory
MANDATORY_QA_FULL = os.environ.get('NST_MANDATORY_QA_FULL', '').strip() in ('1', 'true', 'yes')

mandatory = pytest.mark.mandatory

SCAFFOLD_SKIP = pytest.mark.skip(
    reason='Mandatory QA scaffold — implement body when feature stabilizes; run with NST_MANDATORY_QA_FULL=1',
)


def skip_unless_full():
    return pytest.mark.skipif(
        not MANDATORY_QA_FULL,
        reason='Scaffold: set NST_MANDATORY_QA_FULL=1 to execute mandatory QA bodies',
    )
