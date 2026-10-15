"""
Playwright E2E Test Configuration
Fixtures for browser automation testing of Network Swiss Tool Pro
"""
import pytest
from playwright.sync_api import Page, Browser, BrowserContext


@pytest.fixture(scope="function")
def browser_context_args(browser_context_args, browser_type_launch_args):
    """Configure browser context for testing"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="function")
def page(browser: Browser):
    """Create a new page for each test"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """Navigate to app and ensure it's loaded"""
    page.goto("http://127.0.0.1:5051")
    page.wait_for_load_state("networkidle")
    
    # Dismiss initial "Ready when you are" dialog if present
    try:
        continue_button = page.get_by_role("button", name="Continue to program")
        if continue_button.is_visible(timeout=3000):
            continue_button.click()
            page.wait_for_timeout(500)
    except:
        pass  # Dialog may not be present
    
    return page


@pytest.fixture(scope="function")
def lab_inventory():
    """Lab inventory configuration"""
    return """127.0.0.1,cisco_ios
127.0.0.1,cisco_nxos
127.0.0.1,cisco_nxos"""


@pytest.fixture(scope="function")
def lab_credentials():
    """Lab credentials for testing"""
    return {
        "username": "admin",
        "password": "admin",
        "enable_password": "admin",
        "label": "Lab Device"
    }
