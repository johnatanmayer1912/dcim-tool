"""
Playwright E2E Tests - Swiss Tools Operations
Tests MAC trace, path reconstruct, description search, ping scan
"""
import pytest
from playwright.sync_api import Page, expect


class TestMacAddressSearch:
    """Test MAC address search operations"""
    
    def test_038_navigate_to_network_search_tab(self, authenticated_page: Page):
        """TEST-038: Navigate to Network Search tab"""
        page = authenticated_page
        
        # Click Network Search tab
        search_tab = page.get_by_role("button", name="Network Search")
        search_tab.click()
        
        # Wait for Network Search panel to load
        page.wait_for_selector("text=/MAC Address Trace/i")
        
        # Verify Network Search is active
        expect(search_tab).to_have_attribute("aria-selected", "true")
        
    def test_039_mac_address_format_validation(self, authenticated_page: Page):
        """TEST-039: Verify MAC address format validation"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/MAC Address Trace/i")
        
        # Fill invalid MAC format
        page.fill('input[name="mac_address"]', "invalid-mac")
        
        # Click Validate
        page.get_by_role("button", name="Validate").click()
        
        # Wait for error
        page.wait_for_selector("text=/Invalid MAC/i", timeout=5000)
        
        # Verify error message
        error_message = page.locator("text=/Invalid MAC address format/i")
        expect(error_message).to_be_visible()
        
    def test_040_mac_trace_execution(self, authenticated_page: Page, lab_credentials):
        """TEST-040: Execute MAC trace"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/MAC Address Trace/i")
        
        # Fill MAC address
        page.fill('input[name="mac_address"]', "00:11:22:33:44:55")
        
        # Fill target
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Use session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for progress
        page.wait_for_selector("text=/Running/i", timeout=10000)
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=30000)
        
        # Verify results
        results_panel = page.locator("text=/Results/i")
        expect(results_panel).to_be_visible()


class TestDescriptionSearch:
    """Test interface description search"""
    
    def test_041_description_search_ui_accessible(self, authenticated_page: Page):
        """TEST-041: Verify description search UI is accessible"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Description Search/i")
        
        # Verify Description Search section
        desc_search = page.locator("text=/Description Search/i")
        expect(desc_search).to_be_visible()
        
    def test_042_description_search_execution(self, authenticated_page: Page, lab_credentials):
        """TEST-042: Execute description search"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Description Search/i")
        
        # Fill search term
        page.fill('input[name="description"]', "Uplink")
        
        # Fill target
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Use session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=30000)
        
        # Verify results
        results_panel = page.locator("text=/Results/i")
        expect(results_panel).to_be_visible()


class TestPingScan:
    """Test network ping scan"""
    
    def test_043_ping_scan_ui_accessible(self, authenticated_page: Page):
        """TEST-043: Verify ping scan UI is accessible"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Ping Scan/i")
        
        # Verify Ping Scan section
        ping_scan = page.locator("text=/Ping Scan/i")
        expect(ping_scan).to_be_visible()
        
    def test_044_cidr_format_validation(self, authenticated_page: Page):
        """TEST-044: Verify CIDR format validation"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Ping Scan/i")
        
        # Fill invalid CIDR
        page.fill('input[name="cidr"]', "invalid-cidr")
        
        # Click Validate
        page.get_by_role("button", name="Validate").click()
        
        # Wait for error
        page.wait_for_selector("text=/Invalid CIDR/i", timeout=5000)
        
        # Verify error message
        error_message = page.locator("text=/Invalid CIDR format/i")
        expect(error_message).to_be_visible()
        
    def test_045_cidr_size_limit(self, authenticated_page: Page):
        """TEST-045: Verify CIDR size limit (256 hosts max)"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/Ping Scan/i")
        
        # Fill large CIDR
        page.fill('input[name="cidr"]', "10.0.0.0/16")
        
        # Click Validate
        page.get_by_role("button", name="Validate").click()
        
        # Wait for error
        page.wait_for_selector("text=/CIDR too large/i", timeout=5000)
        
        # Verify error message
        error_message = page.locator("text=/CIDR size exceeds limit/i")
        expect(error_message).to_be_visible()


class TestOSAudit:
    """Test OS audit operations"""
    
    def test_046_os_audit_execution(self, authenticated_page: Page, lab_credentials):
        """TEST-046: Execute OS audit"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/OS Audit/i")
        
        # Fill target
        page.fill('input[name="target"]', "127.0.0.1")
        
        # Use session credentials
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=30000)
        
        # Verify results
        results_panel = page.locator("text=/Results/i")
        expect(results_panel).to_be_visible()
        
    def test_047_os_audit_csv_output(self, authenticated_page: Page, lab_credentials):
        """TEST-047: Verify OS audit CSV output"""
        page = authenticated_page
        
        # Navigate to Network Search
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/OS Audit/i")
        
        # Fill target
        page.fill('input[name="target"]', "127.0.0.1")
        page.fill('input[name="session_username"]', lab_credentials["username"])
        page.fill('input[name="session_password"]', lab_credentials["password"])
        
        # Select CSV output
        page.check('input[name="output_csv"]')
        
        # Submit
        page.get_by_role("button", name="Run").click()
        
        # Wait for completion
        page.wait_for_selector("text=/Complete/i", timeout=30000)
        
        # Verify download button
        download_button = page.get_by_role("button", name="Download CSV")
        expect(download_button).to_be_visible()
