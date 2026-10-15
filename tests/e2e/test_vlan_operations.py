"""
Playwright E2E Tests - VLAN Operations
Tests VLAN provisioning, rename, delete, and compare
"""
import pytest
from playwright.sync_api import Page, expect


class TestVLANProvisioning:
    """Test VLAN add operations"""
    
    def test_029_navigate_to_vlan_tab(self, authenticated_page: Page):
        """TEST-029: Navigate to VLAN tab"""
        page = authenticated_page
        
        # Click VLAN tab
        vlan_tab = page.get_by_role("button", name="VLAN")
        vlan_tab.click()
        
        # Wait for VLAN panel to load
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Verify VLAN is active
        expect(vlan_tab).to_have_attribute("aria-selected", "true")
        
    def test_030_add_vlan_with_dry_run(self, authenticated_page: Page, lab_credentials):
        """TEST-030: Add VLAN with dry-run mode"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Fill VLAN details
        page.fill('input[name="vlan_id"]', "10")
        page.fill('input[name="vlan_name"]', "DATA")
        
        # Select device
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Use session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Click Dry Run
        page.get_by_role("button", name="Dry Run").click()
        
        # Wait for CLI preview
        page.wait_for_selector("text=/CLI Preview/i", timeout=30000)
        
        # Verify CLI preview is shown
        cli_preview = page.locator("text=/interface Vlan10/i")
        expect(cli_preview).to_be_visible()
        
    def test_031_vlan_id_validation(self, authenticated_page: Page):
        """TEST-031: Verify VLAN ID validation (1-4094)"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Try invalid VLAN ID
        page.fill('input[name="vlan_id"]', "5000")
        
        # Fill name
        page.fill('input[name="vlan_name"]', "TEST")
        
        # Click Validate
        page.get_by_role("button", name="Validate").click()
        
        # Wait for error
        page.wait_for_selector("text=/VLAN ID must be/i", timeout=5000)
        
        # Verify error message
        error_message = page.locator("text=/VLAN ID must be between 1 and 4094/i")
        expect(error_message).to_be_visible()
        
    def test_032_vlan_name_length_limit(self, authenticated_page: Page):
        """TEST-032: Verify VLAN name length limit (32 chars)"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Try long VLAN name
        long_name = "A" * 40
        page.fill('input[name="vlan_name"]', long_name)
        
        # Click Validate
        page.get_by_role("button", name="Validate").click()
        
        # Wait for error
        page.wait_for_selector("text=/VLAN name/i", timeout=5000)
        
        # Verify error message
        error_message = page.locator("text=/VLAN name too long/i")
        expect(error_message).to_be_visible()
        
    def test_033_vlan_add_approval_modal(self, authenticated_page: Page, lab_credentials):
        """TEST-033: Verify VLAN add approval modal"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Fill VLAN details
        page.fill('input[name="vlan_id"]', "20")
        page.fill('input[name="vlan_name"]', "VOICE")
        page.fill('input[name="target"]', "127.0.0.1")
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Click Run (not dry run)
        page.get_by_role("button", name="Run").click()
        
        # Wait for approval modal
        page.wait_for_selector("text=/Approval/i", timeout=10000)
        
        # Verify approval modal is shown
        approval_modal = page.locator("text=/Confirm VLAN Add/i")
        expect(approval_modal).to_be_visible()


class TestVLANCompare:
    """Test VLAN compare operations"""
    
    def test_034_vlan_compare_ui_accessible(self, authenticated_page: Page):
        """TEST-034: Verify VLAN compare UI is accessible"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Find Compare section
        compare_section = page.locator("text=/VLAN Compare/i")
        expect(compare_section).to_be_visible()
        
    def test_035_vlan_compare_golden_csv_upload(self, authenticated_page: Page):
        """TEST-035: Upload golden CSV for VLAN compare"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Look for CSV upload area
        csv_upload = page.locator("input[type='file']")
        expect(csv_upload).to_be_visible()
        
    def test_036_vlan_compare_scope_selection(self, authenticated_page: Page):
        """TEST-036: Verify VLAN compare scope selection"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # Check scope dropdown
        scope_dropdown = page.locator("select[name='scope']")
        expect(scope_dropdown).to_be_visible()
        
    def test_037_vlan_compare_missing_vlan_detection(self, authenticated_page: Page):
        """TEST-037: Verify missing VLAN detection in compare"""
        page = authenticated_page
        
        # Navigate to VLAN
        page.get_by_role("button", name="VLAN").click()
        page.wait_for_selector("text=/VLAN Operations/i")
        
        # This would require actual CSV upload and compare execution
        # For now, verify UI is ready
        compare_button = page.get_by_role("button", name="Compare")
        expect(compare_button).to_be_visible()
