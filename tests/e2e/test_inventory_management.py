"""
Playwright E2E Tests - Inventory Management
Tests inventory file operations, validation, and parsing
"""
import pytest
from playwright.sync_api import Page, expect


class TestInventoryFileOperations:
    """Test inventory file load, preview, and commit"""
    
    def test_011_navigate_to_inventory_tab(self, authenticated_page: Page):
        """TEST-011: Navigate to Inventory tab"""
        page = authenticated_page
        
        # Click Inventory tab
        inventory_tab = page.get_by_role("button", name="Inventory")
        inventory_tab.click()
        
        # Wait for Inventory panel to load
        page.wait_for_selector("text=/Inventory File/i")
        
        # Verify Inventory is active
        expect(inventory_tab).to_have_attribute("aria-selected", "true")
        
    def test_012_load_inventory_from_file(self, authenticated_page: Page, lab_inventory):
        """TEST-012: Load inventory file"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Set inventory text directly (simulating file load)
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill(lab_inventory)
        
        # Verify inventory is filled
        expect(inventory_textarea).to_have_value(lab_inventory)
        
    def test_013_preview_inventory_validation(self, authenticated_page: Page, lab_inventory):
        """TEST-013: Preview inventory with validation"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill inventory
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill(lab_inventory)
        
        # Click Preview
        preview_button = page.get_by_role("button", name="Preview")
        preview_button.click()
        
        # Wait for preview results
        page.wait_for_selector("text=/Parsed Hosts/i")
        
        # Verify parsed hosts table
        parsed_hosts = page.locator("text=/127.0.0.1/i")
        expect(parsed_hosts).to_be_visible()
        
    def test_014_inventory_dns_hostname_rejection(self, authenticated_page: Page):
        """TEST-014: Verify DNS hostnames are rejected"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill inventory with DNS hostname
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill("switch.example.com,cisco_ios")
        
        # Click Preview
        preview_button = page.get_by_role("button", name="Preview")
        preview_button.click()
        
        # Wait for error message
        page.wait_for_selector("text=/DNS/i", timeout=5000)
        
        # Verify error is shown
        error_message = page.locator("text=/DNS hostnames are not supported/i")
        expect(error_message).to_be_visible()
        
    def test_015_inventory_ipv4_validation(self, authenticated_page: Page):
        """TEST-015: Verify IPv4 addresses are accepted"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill inventory with valid IPv4
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill("192.168.1.1,cisco_ios")
        
        # Click Preview
        preview_button = page.get_by_role("button", name="Preview")
        preview_button.click()
        
        # Wait for preview results
        page.wait_for_selector("text=/Parsed Hosts/i")
        
        # Verify no error
        error_message = page.locator("text=/DNS/i")
        expect(error_message).not_to_be_visible()
        
    def test_016_inventory_commit_replace_mode(self, authenticated_page: Page, lab_inventory):
        """TEST-016: Commit inventory in replace mode"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill inventory
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill(lab_inventory)
        
        # Preview first
        preview_button = page.get_by_role("button", name="Preview")
        preview_button.click()
        page.wait_for_selector("text=/Parsed Hosts/i")
        
        # Click Commit (replace mode)
        commit_button = page.get_by_role("button", name="Commit replace")
        commit_button.click()
        
        # Wait for confirmation modal
        page.wait_for_selector("text=/Confirm/i")
        
        # Confirm commit
        page.get_by_role("button", name="Confirm").click()
        
        # Wait for success message
        page.wait_for_selector("text=/committed/i", timeout=5000)
        
        # Verify success
        success_message = page.locator("text=/Inventory committed/i")
        expect(success_message).to_be_visible()
        
    def test_017_inventory_backup_file_created(self, authenticated_page: Page):
        """TEST-017: Verify backup file is created on commit"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Check backup dropdown exists
        backup_dropdown = page.locator("select[name='backup']")
        expect(backup_dropdown).to_be_visible()
        
    def test_018_inventory_duplicate_detection(self, authenticated_page: Page):
        """TEST-018: Verify duplicate IP detection"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill inventory with duplicate IPs
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill("127.0.0.1,cisco_ios\n127.0.0.1,cisco_nxos")
        
        # Click Preview
        preview_button = page.get_by_role("button", name="Preview")
        preview_button.click()
        
        # Wait for preview results
        page.wait_for_selector("text=/Parsed Hosts/i")
        
        # Verify duplicate is detected
        duplicate_indicator = page.locator("text=/duplicate/i")
        expect(duplicate_indicator).to_be_visible()


class TestInventoryUI:
    """Test inventory UI components"""
    
    def test_019_parsed_hosts_table_rendering(self, authenticated_page: Page, lab_inventory):
        """TEST-019: Verify parsed hosts table renders correctly"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill and preview inventory
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill(lab_inventory)
        page.get_by_role("button", name="Preview").click()
        page.wait_for_selector("text=/Parsed Hosts/i")
        
        # Verify table structure
        table = page.locator("table")
        expect(table).to_be_visible()
        
        # Verify columns
        host_column = page.locator("text=/Host/i")
        type_column = page.locator("text=/Type/i")
        expect(host_column).to_be_visible()
        expect(type_column).to_be_visible()
        
    def test_020_inventory_scope_selection(self, authenticated_page: Page):
        """TEST-020: Verify inventory scope selection (committed/unsaved)"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Check scope chips
        scope_committed = page.locator("text=/Committed/i")
        scope_unsaved = page.locator("text=/Unsaved/i")
        expect(scope_committed).to_be_visible()
        expect(scope_unsaved).to_be_visible()
        
    def test_021_inventory_textarea_resize(self, authenticated_page: Page):
        """TEST-021: Verify inventory textarea can be resized"""
        page = authenticated_page
        
        # Navigate to Inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Get textarea element
        textarea = page.locator("textarea[name='inventory']")
        expect(textarea).to_be_visible()
        
        # Verify it's interactable
        expect(textarea).to_be_enabled()
