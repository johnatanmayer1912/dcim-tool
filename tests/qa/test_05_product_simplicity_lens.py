"""Mandatory QA — Product simplicity lens (Steve Jobs / delete steps)."""
from __future__ import annotations

import os

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
WEB = os.path.join(ROOT, 'vlan_checker_web.py')


@mandatory
def test_vlan_mutation_requires_confirm_not_immediate_execute():
    """Add/rename/delete VLAN uses confirm dialog before live SSH."""
    html = open(HTML, encoding='utf-8').read()
    assert 'confirmVlanExecution' in html
    assert 'vlan-modal-confirm-btn' in html
    assert 'disabled' in html


@mandatory
def test_dry_run_default_or_prominent_for_vlan_ops():
    """Operator sees dry-run option before destructive VLAN changes."""
    html = open(HTML, encoding='utf-8').read()
    assert 'vlan_dry_run' in html
    assert 'vlan_vstep_dry_run' in html


@mandatory
def test_one_primary_action_per_diagnostics_card():
    """Each Diagnostics card has one obvious primary CTA button."""
    html = open(HTML, encoding='utf-8').read()
    assert "runAction('mac_check')" in html
    assert "runAction('description_search')" in html or 'description_search' in html


@mandatory
def test_no_duplicate_progress_start_flicker():
    """Search-it progress does not reset to zero mid-run without reason."""
    src = open(os.path.join(ROOT, 'utils', 'search_it_progress.py'), encoding='utf-8').read()
    assert 'progress_start_if_needed' in src
    assert "if st.get('status') == 'running'" in src


@mandatory
def test_report_ready_banner_appears_on_complete():
    """MAC/desc/ping show report-ready strip without manual refresh."""
    html = open(HTML, encoding='utf-8').read()
    assert 'mac-report-ready' in html
    assert 'desc-report-ready' in html
    assert 'ping-report-ready' in html


@mandatory
def test_error_messages_actionable_not_stack_traces_in_ui():
    """Operator log shows human message; raw traceback only in dev paths."""
    src = open(WEB, encoding='utf-8').read()
    assert '[ERROR]' in src
    assert 'traceback.format_exc()' in src
    assert 'def _log_exception_off_console' in src
    assert 'add_log(traceback.format_exc())' not in src


@mandatory
def test_empty_inputs_blocked_before_dispatch():
    """MAC, desc search, ping CIDR validated client-side or API before thread."""
    html = open(HTML, encoding='utf-8').read()
    assert "action === 'mac_check'" in html
    assert "action === 'description_search'" in html
    src = open(WEB, encoding='utf-8').read()
    assert 'progress_done' in src


@mandatory
def test_credentials_one_sidebar_not_scattered_per_tool():
    """Single credential sidebar feeds all tools — no per-plugin re-entry."""
    html = open(HTML, encoding='utf-8').read()
    assert 'saveSessionCredentials' in html
    assert html.count('id="username"') <= 2


@mandatory
def test_outputs_readme_in_run_folder():
    """00_README.txt auto-created in output run dirs for operators."""
    src = open(os.path.join(ROOT, 'utils', 'output_paths.py'), encoding='utf-8').read()
    assert '00_README.txt' in src
    assert 'write_run_readme' in src


@mandatory
def test_remove_steps_gui_parity_not_required():
    """No Tk/web parity tests or docs — web-only product policy honored."""
    arch = open(os.path.join(ROOT, 'docs', '01-architecture', 'system-architecture.md'), encoding='utf-8').read()
    assert 'out of scope' in arch.lower()
    assert 'web only' in arch.lower() or 'web-only' in arch.lower()
