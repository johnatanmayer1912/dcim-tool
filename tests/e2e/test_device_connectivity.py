"""
Playwright E2E Tests - Device Connectivity
Tests SSH/SNMP connections to lab devices
"""
import pytest
from playwright.sync_api import Page, expect


class TestSSHConnection:
    """Test SSH connection to lab devices"""
    
    def test_022_connect_to_ios_device(self, authenticated_page: Page, lab_credentials):
        """TEST-022: Connect to IOS device with valid credentials"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Select operation (e.g., Interface Status)
        page.get_by_role("button", name="Interface Status").click()
        
        # Fill target IP
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for progress
        page.wait_for_selector("text=/Running/i", timeout=10000)
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=30000)
        
        # Verify results
        results_panel = page.locator("text=/Results/i")
        expect(results_panel).to_be_visible()
        
    def test_023_connect_to_nxos_device(self, authenticated_page: Page, lab_credentials):
        """TEST-023: Connect to NX-OS device with valid credentials"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Select operation
        page.get_by_role("button", name="OS Audit").click()
        
        # Fill target IP
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Select device type
        page.select_option('select[name="device_type"]', "cisco_nxos")
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=30000)
        
        # Verify results
        results_panel = page.locator("text=/Results/i")
        expect(results_panel).to_be_visible()
        
    def test_024_connection_timeout_handling(self, authenticated_page: Page):
        """TEST-024: Verify connection timeout handling"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill invalid target
        page.fill('input[name="target"]', "192.168.255.255")
        
        # Select operation
        page.get_by_role("button", name="Interface Status").click()
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for timeout error
        page.wait_for_selector("text=/timeout/i", timeout=35000)
        
        # Verify error message
        error_message = page.locator("text=/Connection timeout/i")
        expect(error_message).to_be_visible()
        
    def test_025_connection_failure_with_wrong_credentials(self, authenticated_page: Page):
        """TEST-025: Verify connection fails with wrong credentials"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill wrong credentials
        page.fill('input[name="session_username"]', "wrong_user")
        page.fill('input[name="session_password"]', "wrong_pass")
        
        # Select operation
        page.get_by_role("button", name="Interface Status").click()
        
        # Fill target IP
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for authentication error
        page.wait_for_selector("text=/authentication/i", timeout=30000)
        
        # Verify error message
        error_message = page.locator("text=/Authentication failed/i")
        expect(error_message).to_be_visible()


class TestConnectionStatus:
    """Test connection status indicators"""
    
    def test_026_connection_status_indicator(self, authenticated_page: Page):
        """TEST-026: Verify connection status indicator in UI"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Status indicator should be visible
        status_indicator = page.locator("text=/Status/i")
        expect(status_indicator).to_be_visible()
        
    def test_027_connection_success_confirmation(self, authenticated_page: Page, lab_credentials):
        """TEST-027: Verify connection success confirmation"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Session Credentials/i")
        
        # Fill credentials and run operation
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        page.get_by_role("button", name="Interface Status").click()
        page.fill('input[name="target"]', "127.0.0.1")
        page.get_by_role("button", name="Run").click()
        
        # Wait for success
        page.wait_for_selector("text=/Success/i", timeout=30000)
        
        # Verify success message
        success_message = page.locator("text=/Successfully connected/i")
        expect(success_message).to_be_visible()
        
    def test_028_concurrent_connections_to_multiple_devices(self, authenticated_page: Page, lab_credentials):
        """TEST-028: Verify concurrent connections to multiple devices"""
        page = authenticated_page
        
        # Navigate to Inventory tab first to load inventory
        page.get_by_role("button", name="Inventory").click()
        page.wait_for_selector("text=/Inventory File/i")
        
        # Fill inventory with 3 devices
        inventory_textarea = page.locator("textarea[name='inventory']")
        inventory_textarea.fill("127.0.0.1,cisco_ios\n127.0.0.1,cisco_nxos\n127.0.0.1,cisco_nxos")
        page.get_by_role("button", name="Preview").click()
        page.wait_for_selector("text=/Parsed Hosts/i")
        page.get_by_role("button", name="Commit replace").click()
        page.wait_for_selector("text=/Confirm/i")
        page.get_by_role("button", name="Confirm").click()
        page.wait_for_selector("text=/committed/i")
        
        # Navigate to Interface Status to test all devices
        page.get_by_role("button", name="Interfaces").click()
        page.wait_for_selector("text=/Interface Status/i")
        
        # Select all devices
        page.get_by_role("button", name="Interface Status").click()
        
        # Use session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=60000)
        
        # Verify results for all devices
        results_panel = page.locator("text=/Results/i")
        expect(results_panel).to_be_visible()
