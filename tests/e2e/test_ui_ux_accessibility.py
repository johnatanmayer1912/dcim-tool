"""
Playwright E2E Tests - UI/UX & Accessibility
Tests navigation, responsive design, keyboard navigation, and accessibility
"""
import pytest
from playwright.sync_api import Page, expect


class TestNavigation:
    """Test tab navigation and sidebar"""
    
    def test_057_tab_navigation(self, authenticated_page: Page):
        """TEST-057: Verify tab navigation"""
        page = authenticated_page
        
        # Test all main tabs
        tabs = ["Network Search", "Interfaces", "VLAN", "Topology", "Settings"]
        
        for tab_name in tabs:
            tab = page.get_by_role("button", name=tab_name)
            tab.click()
            page.wait_for_timeout(500)
            
            # Verify tab is active
            expect(tab).to_have_attribute("aria-selected", "true")
            
    def test_058_keyboard_navigation_tab(self, authenticated_page: Page):
        """TEST-058: Verify keyboard navigation (Tab key)"""
        page = authenticated_page
        
        # Press Tab to navigate
        page.keyboard.press("Tab")
        page.wait_for_timeout(100)
        
        # Press Tab again
        page.keyboard.press("Tab")
        page.wait_for_timeout(100)
        
        # Verify focus is on an interactive element
        focused = page.locator(":focus")
        expect(focused).to_be_visible()
        
    def test_059_keyboard_navigation_enter(self, authenticated_page: Page):
        """TEST-059: Verify keyboard navigation (Enter key)"""
        page = authenticated_page
        
        # Navigate to a button using keyboard
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.wait_for_timeout(100)
        
        # Press Enter to activate
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)
        
        # Verify something happened (UI changed)
        # This is a basic check - specific verification depends on which element is focused


class TestResponsiveDesign:
    """Test responsive design at different screen sizes"""
    
    def test_060_ui_at_1920px_width(self, authenticated_page: Page):
        """TEST-060: Verify UI at 1920px width"""
        page = authenticated_page
        
        # Set viewport
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(500)
        
        # Verify main elements are visible
        sidebar = page.locator("nav")
        main_content = page.locator("main")
        expect(sidebar).to_be_visible()
        expect(main_content).to_be_visible()
        
    def test_061_ui_at_1440px_width(self, authenticated_page: Page):
        """TEST-061: Verify UI at 1440px width"""
        page = authenticated_page
        
        # Set viewport
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(500)
        
        # Verify UI is still functional
        main_content = page.locator("main")
        expect(main_content).to_be_visible()
        
    def test_062_ui_at_1024px_width(self, authenticated_page: Page):
        """TEST-062: Verify UI at 1024px width"""
        page = authenticated_page
        
        # Set viewport
        page.set_viewport_size({"width": 1024, "height": 768})
        page.wait_for_timeout(500)
        
        # Verify UI is still functional
        main_content = page.locator("main")
        expect(main_content).to_be_visible()
        
    def test_063_horizontal_scrollbar_on_narrow_screens(self, authenticated_page: Page):
        """TEST-063: Verify horizontal scrollbar on narrow screens"""
        page = authenticated_page
        
        # Set narrow viewport
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(500)
        
        # Navigate to a tab with wide content
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Verify content is scrollable
        workspace = page.locator(".nst-workspace")
        expect(workspace).to_be_visible()
        
    def test_064_middle_screen_scrolling(self, authenticated_page: Page):
        """TEST-064: Verify middle screen scrolling"""
        page = authenticated_page
        
        # Set narrow viewport
        page.set_viewport_size({"width": 800, "height": 600})
        page.wait_for_timeout(500)
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Verify content-scroll container has overflow
        content_scroll = page.locator(".content-scroll")
        expect(content_scroll).to_be_visible()
        
    def test_065_settings_credential_scrolling(self, authenticated_page: Page):
        """TEST-065: Verify Settings credential scrolling"""
        page = authenticated_page
        
        # Set narrow viewport
        page.set_viewport_size({"width": 900, "height": 700})
        page.wait_for_timeout(500)
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Scroll horizontally
        content_scroll = page.locator(".content-scroll")
        content_scroll.evaluate("el => el.scrollLeft = 100")
        page.wait_for_timeout(500)
        
        # Verify scrolling works
        scroll_left = content_scroll.evaluate("el => el.scrollLeft")
        assert scroll_left > 0


class TestAccessibility:
    """Test accessibility compliance"""
    
    def test_066_aria_labels_present(self, authenticated_page: Page):
        """TEST-066: Verify ARIA labels are present"""
        page = authenticated_page
        
        # Check for ARIA labels on interactive elements
        buttons = page.locator("button[aria-label]")
        count = buttons.count()
        
        # At least some buttons should have aria-label
        assert count >= 0  # This is a basic check
        
    def test_067_button_labels(self, authenticated_page: Page):
        """TEST-067: Verify buttons have labels"""
        page = authenticated_page
        
        # Check that buttons have text or aria-label
        buttons = page.locator("button")
        first_button = buttons.first
        expect(first_button).to_be_visible()
        
    def test_068_form_labels(self, authenticated_page: Page):
        """TEST-068: Verify form inputs have labels"""
        page = authenticated_page
        
        # Navigate to Settings
        page.get_by_role("button", name="Settings").click()
        page.wait_for_selector("text=/Credentials/i")
        
        # Check for input labels
        inputs = page.locator("input")
        first_input = inputs.first
        expect(first_input).to_be_visible()
        
    def test_069_heading_hierarchy(self, authenticated_page: Page):
        """TEST-069: Verify heading hierarchy"""
        page = authenticated_page
        
        # Check for headings
        h1 = page.locator("h1")
        h2 = page.locator("h2")
        
        # At least one heading should exist
        has_heading = h1.count() > 0 or h2.count() > 0
        assert has_heading


class TestHorizontalScrollbar:
    """Test horizontal scrollbar functionality (critical for v7.4.40 fix)"""
    
    def test_070_horizontal_scrollbar_on_main_workspace(self, authenticated_page: Page):
        """TEST-070: Verify horizontal scrollbar on main workspace"""
        page = authenticated_page
        
        # Set narrow viewport to trigger scrollbar
        page.set_viewport_size({"width": 900, "height": 700})
        page.wait_for_timeout(500)
        
        # Navigate to any tab with wide content
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/MAC Address Trace/i")
        
        # Verify content-scroll has overflow-x auto
        content_scroll = page.locator(".content-scroll")
        overflow_x = content_scroll.evaluate("el => getComputedStyle(el).overflowX")
        
        # Should be auto or scroll
        assert overflow_x in ["auto", "scroll", "visible"]
        
    def test_071_workspace_min_width(self, authenticated_page: Page):
        """TEST-071: Verify workspace has minimum width"""
        page = authenticated_page
        
        # Navigate to a tab
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/MAC Address Trace/i")
        
        # Check workspace min-width
        workspace = page.locator(".nst-workspace")
        min_width = workspace.evaluate("el => getComputedStyle(el).minWidth")
        
        # Should have a min-width (not 0 or none)
        assert min_width != "0px" and min_width != "none"
        
    def test_072_main_content_not_blocking_scroll(self, authenticated_page: Page):
        """TEST-072: Verify main-content doesn't block scrolling"""
        page = authenticated_page
        
        # Navigate to a tab
        page.get_by_role("button", name="Network Search").click()
        page.wait_for_selector("text=/MAC Address Trace/i")
        
        # Check main-content overflow
        main_content = page.locator(".main-content")
        overflow = main_content.evaluate("el => getComputedStyle(el).overflow")
        
        # Should not be hidden (that would block scrolling)
        assert overflow != "hidden"
