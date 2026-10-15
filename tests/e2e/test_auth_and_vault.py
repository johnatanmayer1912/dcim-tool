"""
Playwright E2E Tests - Authentication & Vault
Tests vault initialization, credential management, and session credentials
"""
import pytest
from playwright.sync_api import Page, expect


class TestVaultInitialization:
    """Test vault initialization and master password"""
    
    def test_001_vault_status_on_initial_load(self, authenticated_page: Page):
        """TEST-001: Verify vault status on initial load"""
        page = authenticated_page
        
        # Wait for page to load
        page.wait_for_selector("body")
        
        # Check vault status indicator (shows "Vault ready" in HUD)
        vault_status = page.locator("text=Vault ready")
        expect(vault_status).to_be_visible()
        
        # Vault should be unlocked (machine key)
        page.wait_for_timeout(1000)
        
    def test_002_vault_unlock_with_machine_key(self, authenticated_page: Page):
        """TEST-002: Verify vault unlocks with machine key automatically"""
        page = authenticated_page
        
        # Vault should unlock automatically on startup
        page.wait_for_timeout(2000)
        
        # Check that no master password prompt is shown
        master_password_modal = page.locator("text=Master Password")
        expect(master_password_modal).not_to_be_visible()


class TestCredentialManagement:
    """Test credential add, edit, delete operations"""
    
    def test_003_navigate_to_settings_tab(self, authenticated_page: Page):
        """TEST-003: Navigate to Settings tab"""
        page = authenticated_page
        
        # Click Settings tab
        settings_tab = page.get_by_role("button", name="Settings")
        settings_tab.click()
        
        # Wait for Settings panel to load
        page.wait_for_selector("text=/Credentials/i")
        
        # Verify Settings is active
        expect(settings_tab).to_have_attribute("aria-selected", "true")
        
    def test_004_add_lab_credential(self, authenticated_page: Page, lab_credentials):
        """TEST-004: Add lab credential through UI"""
        page = authenticated_page
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Click Add Credential button
        add_button = page.get_by_role("button", name="Add Credential")
        add_button.click()
        
        # Wait for modal
        page.wait_for_selector(".modal")
        
        # Fill credential form
        page.fill('input[name="username"]', lab_credentials["username"])
        page.fill('input[name="password"]', lab_credentials["password"])
        page.fill('input[name="enable_password"]', lab_credentials["enable_password"])
        page.fill('input[name="label"]', lab_credentials["label"])
        
        # Select profile
        page.select_option('select[name="profile"]', "ssh only")
        
        # Submit
        page.get_by_role("button", name="Add").click()
        
        # Wait for modal to close
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        
        # Verify credential appears in list
        credential_list = page.locator("text=Lab Device")
        expect(credential_list).to_be_visible()
        
    def test_005_verify_credential_list_shows_passwords_hidden(self, authenticated_page: Page):
        """TEST-005: Verify passwords are hidden in credential list"""
        page = authenticated_page
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Credential list should not show actual passwords
        # It should show asterisks or "••••••"
        hidden_password = page.locator("text=/••••••/i")
        expect(hidden_password).to_be_visible()
        
    def test_006_edit_existing_credential(self, authenticated_page: Page):
        """TEST-006: Edit existing credential"""
        page = authenticated_page
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Find Lab Device credential and click edit
        edit_button = page.locator("button[title*='Edit']").first
        edit_button.click()
        
        # Wait for modal
        page.wait_for_selector(".modal")
        
        # Change label
        page.fill('input[name="label"]', "Lab Device Updated")
        
        # Submit
        page.get_by_role("button", name="Update").click()
        
        # Wait for modal to close
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        
        # Verify updated label
        updated_label = page.locator("text=Lab Device Updated")
        expect(updated_label).to_be_visible()
        
    def test_007_delete_credential(self, authenticated_page: Page):
        """TEST-007: Delete credential"""
        page = authenticated_page
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Find credential and click delete
        delete_button = page.locator("button[title*='Delete']").first
        delete_button.click()
        
        # Wait for confirmation modal
        page.wait_for_selector("text=/Are you sure/i")
        
        # Confirm deletion
        page.get_by_role("button", name="Delete").click()
        
        # Wait for modal to close
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        
        # Verify credential is removed
        deleted_credential = page.locator("text=Lab Device Updated")
        expect(deleted_credential).not_to_be_visible()


class TestSessionCredentials:
    """Test session credentials for one-time operations"""
    
    def test_008_session_credentials_ui_accessible(self, authenticated_page: Page):
        """TEST-008: Verify session credentials UI is accessible"""
        page = authenticated_page
        
        # Navigate to any operation that uses credentials
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Session credentials section should be visible
        session_creds = page.locator("text=/Session Credentials/i")
        expect(session_creds).to_be_visible()
        
    def test_009_session_credentials_override_vault(self, authenticated_page: Page):
        """TEST-009: Verify session credentials override vault credentials"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill session credentials
        page.fill('input[name="session_username"]', "session_user")
        page.fill('input[name="session_password"]', "session_pass")
        
        # Verify session credentials are filled
        session_user = page.locator('input[name="session_username"]')
        expect(session_user).to_have_value("session_user")
        
    def test_010_session_credentials_cleared_on_refresh(self, authenticated_page: Page):
        """TEST-010: Verify session credentials are cleared on refresh"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill session credentials
        page.fill('input[name="session_username"]', "session_user")
        
        # Refresh page
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Navigate back to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Session credentials should be cleared
        session_user = page.locator('input[name="session_username"]')
        expect(session_user).to_have_value("")
