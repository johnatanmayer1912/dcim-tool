"""
tests/test_p1_ux_navigation.py
=================================
P1 gap remediation tests — GUX-001/002/003/004 (navigation) + G-011b (IM blocking deploy).

These are fast offline tests (no SSH, no live devices).
"""
import re
import pytest
from pathlib import Path

# ─── helpers ──────────────────────────────────────────────────────────────────

INDEX_HTML = Path(__file__).parent.parent / "modules/web/templates/index.html"
_HTML: str = ""

def _html() -> str:
    global _HTML
    if not _HTML:
        _HTML = INDEX_HTML.read_text(encoding="utf-8")
    return _HTML


# ═══════════════════════════════════════════════════════════════════════════════
# G-UX-001 / G-UX-002 / G-UX-003  — Navigation helpers use getElementById
# ═══════════════════════════════════════════════════════════════════════════════

class TestNavigationHelpers:
    """Verify that tab-navigation helpers use the reliable ID selector, not broken CSS substring."""

    def test_goto_tab_uses_get_element_by_id(self):
        """goToTab must use getElementById, NOT a CSS attribute selector."""
        html = _html()
        # Positive: new implementation
        assert "getElementById('tab-segment-' + tabId)" in html, \
            "goToTab must use getElementById('tab-segment-' + tabId)"

    def test_goto_tab_no_broken_css_selector(self):
        """The old broken querySelector with switchTab substring must be gone."""
        html = _html()
        assert "querySelector(`.segment[onclick" not in html, \
            "Broken CSS substring selector must be removed from goToTab"

    def test_all_sidebar_segments_have_id(self):
        """Every nav segment must have id='tab-segment-<tabId>' so goToTab can find it."""
        expected_tabs = [
            "diag", "interfaces", "vlan", "interface_manager",
            "tools", "plugins", "standards", "discovery",
            "templates", "credentials", "about",
        ]
        html = _html()
        for tab in expected_tabs:
            assert f'id="tab-segment-{tab}"' in html, \
                f"Sidebar segment for tab '{tab}' is missing id='tab-segment-{tab}'"

    def test_disc_go_swiss_standard_map_uses_goto_tools_tab(self):
        """discGoSwissStandardMap() must call goToToolsTab() (which delegates to goToTab)."""
        html = _html()
        # Extract the function body
        match = re.search(r'function discGoSwissStandardMap\(\)\s*\{([^}]+)\}', html, re.DOTALL)
        assert match, "discGoSwissStandardMap function not found"
        body = match.group(1)
        assert "goToToolsTab" in body, \
            "discGoSwissStandardMap must call goToToolsTab() — not a raw [data-tab=…] selector"

    def test_goto_search_tab_helper_exists(self):
        assert "function goToSearchTab" in _html()

    def test_goto_tools_tab_helper_exists(self):
        assert "function goToToolsTab" in _html()

    def test_goto_discovery_tab_helper_exists(self):
        assert "function goToDiscoveryTab" in _html()


# ═══════════════════════════════════════════════════════════════════════════════
# G-UX-004 — description_search client-side empty-term guard
# ═══════════════════════════════════════════════════════════════════════════════

class TestDescriptionSearchGuard:
    """desc_search must be guarded client-side like mac_check (G-UX-004)."""

    def test_desc_search_guard_exists_in_run_action(self):
        """runAction must validate the desc_search_input before firing the API call."""
        html = _html()
        # Locate the description_search guard block
        assert "action === 'description_search'" in html, \
            "runAction must check action === 'description_search'"

    def test_desc_search_guard_checks_empty_term(self):
        html = _html()
        # Find the block and verify it reads desc_search_input
        match = re.search(
            r"action === 'description_search'.*?(?=if \(action ===|const payload)",
            html, re.DOTALL
        )
        assert match, "Could not find description_search guard block in runAction"
        block = match.group(0)
        assert "desc_search_input" in block, \
            "Guard must reference desc_search_input element"
        assert ".trim()" in block, \
            "Guard must trim whitespace before checking emptiness"
        assert "return" in block, \
            "Guard must have an early return to abort the API call"

    def test_desc_search_guard_navigates_to_search_tab(self):
        """On empty term, guard must navigate to the Search tab."""
        html = _html()
        match = re.search(
            r"action === 'description_search'.*?(?=if \(action ===|const payload)",
            html, re.DOTALL
        )
        assert match
        block = match.group(0)
        assert "goToSearchTab" in block, \
            "Guard must call goToSearchTab() when term is empty"


# ═══════════════════════════════════════════════════════════════════════════════
# G-011b — IM blocking deploy pre-flight (legacy syntax → hard abort)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIMBlockingDeployPreflight:
    """
    _deploy_configuration must abort before touching the device when
    legacy/high-risk lines are present in the proposed config.
    """

    @pytest.fixture(autouse=True)
    def _import(self):
        from modules.plugins.interface_manager import (
            _validate_vendor_syntax,
            _IM_BLOCKING_LINE_PATTERNS,
        )
        self.validate = _validate_vendor_syntax
        self.patterns = _IM_BLOCKING_LINE_PATTERNS

    # ── validate-level checks ───────────────────────────────────────────────

    def test_legacy_nxos_encapsulation_is_blocking(self):
        """NX-OS 'switchport trunk encapsulation' must be a blocking error."""
        config = "interface Ethernet1/1\nswitchport trunk encapsulation dot1q\n"
        result = self.validate(config, "cisco_nxos", None)
        blocking = [e for e in result["errors"] if e.get("blocking")]
        assert blocking, "Expected blocking error for NX-OS trunk encapsulation"

    def test_shutdown_is_blocking_via_apply_rules(self):
        """'shutdown' in proposed config is blocked by _apply_blocking_syntax_rules."""
        from modules.plugins.interface_manager import _apply_blocking_syntax_rules
        errors = _apply_blocking_syntax_rules("interface Gi0/1\nshutdown", [])
        blocking = [e for e in errors if e.get("blocking")]
        assert blocking, "Expected blocking error for 'shutdown' line"

    def test_default_interface_is_blocking(self):
        from modules.plugins.interface_manager import _apply_blocking_syntax_rules
        errors = _apply_blocking_syntax_rules("default interface GigabitEthernet0/1", [])
        blocking = [e for e in errors if e.get("blocking")]
        assert blocking, "Expected blocking error for 'default interface' line"

    def test_no_switchport_is_blocking(self):
        from modules.plugins.interface_manager import _apply_blocking_syntax_rules
        errors = _apply_blocking_syntax_rules("no switchport", [])
        blocking = [e for e in errors if e.get("blocking")]
        assert blocking, "Expected blocking error for 'no switchport' line"

    # ── deploy-level abort check ────────────────────────────────────────────

    def test_deploy_aborts_on_blocking_config_no_ssh(self):
        """
        _deploy_configuration must return deployment_status='blocked_by_legacy_syntax'
        WITHOUT establishing an SSH connection when blocking errors are present.
        Uses a fake connection sentinel to detect if SSH was attempted.
        """
        from modules.plugins.interface_manager import _deploy_configuration

        class _FakeConn:
            """Raises on any method call to prove no SSH commands were sent."""
            def __getattr__(self, name):
                raise AssertionError(
                    f"_deploy_configuration tried to call conn.{name}() "
                    f"even though config has blocking errors — pre-flight failed!"
                )

        # NX-OS: 'switchport trunk encapsulation' is a legacy blocking command
        bad_config = "interface Ethernet1/1\nswitchport trunk encapsulation dot1q\n"
        result = _deploy_configuration(
            conn=_FakeConn(),
            true_host="10.0.0.1",
            device_type="cisco_nxos",
            interface_filter="",
            proposed_config=bad_config,
            dry_run=False,
            log_func=None,
        )
        assert result.get("deployment_status") == "blocked_by_legacy_syntax", \
            f"Expected blocked_by_legacy_syntax, got: {result.get('deployment_status')}"
        assert result.get("blocking_errors"), "Expected blocking_errors list in result"

    def test_deploy_proceeds_for_clean_config(self):
        """
        Clean config (no blocking lines) must NOT return blocked_by_legacy_syntax.
        We only test the pre-flight logic; SSH can fail (no real device).
        """
        from modules.plugins.interface_manager import _deploy_configuration

        # We stop after the pre-flight returns — SSH will fail but that's expected.
        clean_config = "interface Ethernet1/1\ndescription TEST\n"

        class _MinimalConn:
            device_type = "cisco_nxos"
            def send_command(self, *a, **kw): return ""
            def send_config_set(self, *a, **kw): return ""
            def enable(self, *a, **kw): return ""
            def disconnect(self): pass

        result = _deploy_configuration(
            conn=_MinimalConn(),
            true_host="10.0.0.1",
            device_type="cisco_nxos",
            interface_filter="",
            proposed_config=clean_config,
            dry_run=False,
            log_func=None,
        )
        assert result.get("deployment_status") != "blocked_by_legacy_syntax", \
            "Clean config should not be blocked by legacy-syntax pre-flight"
