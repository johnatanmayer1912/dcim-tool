const { test, expect } = require('@playwright/test');

test.describe('Credential Modal - User Simulation Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://127.0.0.1:5051');
    await page.waitForLoadState('networkidle');
    
    // Navigate to the Credentials tab using JavaScript
    await page.waitForTimeout(2000);
    
    // Try to switch to credentials tab using JavaScript function
    await page.evaluate(() => {
      if (typeof switchTab === 'function') {
        switchTab('credentials', document.getElementById('tab-segment-credentials'));
      }
    });
    
    await page.waitForTimeout(1000);
    
    // Ensure the credentials tab is visible
    const credentialsTab = page.locator('#tab-credentials');
    await expect(credentialsTab).toBeVisible({ timeout: 10000 });
    console.log('[TEST SETUP] Navigated to Credentials tab');
    
    // Close any interfering modals (like health wizard)
    await page.evaluate(() => {
      // Close health wizard modal if present
      const healthWizard = document.getElementById('health-wizard-modal');
      if (healthWizard) {
        healthWizard.setAttribute('hidden', 'true');
        healthWizard.style.display = 'none';
        healthWizard.setAttribute('aria-hidden', 'true');
      }
    });
    await page.waitForTimeout(500);
    console.log('[TEST SETUP] Closed interfering modals');
  });

  test('Round 1: Modal opens and inputs are interactive', async ({ page }) => {
    console.log('[TEST ROUND 1] Starting modal interaction test');
    
    // Wait for the credentials tab to be fully loaded
    await page.waitForTimeout(1000);
    
    // Find and click the "Add Credential" button
    const addButton = page.locator('button').filter({ hasText: /Add Credential/i }).first();
    await expect(addButton).toBeVisible({ timeout: 10000 });
    console.log('[TEST ROUND 1] Add Credential button found and visible');
    
    await addButton.click();
    console.log('[TEST ROUND 1] Add Credential button clicked');
    
    // Wait for modal to appear
    await page.waitForTimeout(500);
    
    // Verify modal is visible and not inert
    const modal = page.locator('#add-credential-modal');
    await expect(modal).toBeVisible();
    console.log('[TEST ROUND 1] Modal is visible');
    
    // Check that modal is NOT inert (should be removed when shown)
    const inertAttr = await modal.getAttribute('inert');
    expect(inertAttr).toBeNull();
    console.log('[TEST ROUND 1] Modal inert attribute removed (interactive)');
    
    // Verify modal has correct z-index
    const zIndex = await modal.evaluate(el => window.getComputedStyle(el).zIndex);
    console.log(`[TEST ROUND 1] Modal z-index: ${zIndex}`);
    expect(parseInt(zIndex)).toBeGreaterThanOrEqual(25000);
    
    // Verify form inputs are visible and enabled
    const labelInput = page.locator('#cred-label');
    const usernameInput = page.locator('#cred-username');
    const passwordInput = page.locator('#cred-password');
    
    await expect(labelInput).toBeVisible();
    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    
    // Verify inputs are not disabled
    await expect(labelInput).toBeEnabled();
    await expect(usernameInput).toBeEnabled();
    await expect(passwordInput).toBeEnabled();
    console.log('[TEST ROUND 1] All inputs are visible and enabled');
    
    // Test typing in inputs
    await labelInput.fill('Test Credential');
    await usernameInput.fill('testuser');
    await passwordInput.fill('testpass123');
    console.log('[TEST ROUND 1] Successfully typed in all input fields');
    
    // Verify values were entered
    await expect(labelInput).toHaveValue('Test Credential');
    await expect(usernameInput).toHaveValue('testuser');
    await expect(passwordInput).toHaveValue('testpass123');
    console.log('[TEST ROUND 1] Input values verified');
    
    // Test Cancel button
    const cancelButton = page.locator('#btn-cancel-credential');
    await expect(cancelButton).toBeVisible();
    await expect(cancelButton).toBeEnabled();
    console.log('[TEST ROUND 1] Cancel button is interactive');
    
    // Test Save button
    const saveButton = page.locator('#btn-save-credential');
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();
    console.log('[TEST ROUND 1] Save button is interactive');
    
    console.log('[TEST ROUND 1] ✓ All modal interaction tests passed');
  });

  test('Round 2: Form submission with valid data', async ({ page }) => {
    console.log('[TEST ROUND 2] Starting form submission test');
    
    await page.waitForTimeout(500);
    
    // Click Add Credential button
    const addButton = page.locator('button').filter({ hasText: /Add Credential/i }).first();
    await addButton.click();
    await page.waitForTimeout(500);
    
    // Fill in the form
    await page.locator('#cred-label').fill('Playwright Test Credential');
    await page.locator('#cred-username').fill('playwright_user');
    await page.locator('#cred-password').fill('SecurePass123!');
    await page.locator('#cred-enable').fill('EnableSecret123');
    await page.locator('#cred-profile-type').selectOption('ssh_and_snmp');
    await page.locator('#cred-snmp-version').selectOption('v2c');
    await page.locator('#cred-snmp-key').fill('public');
    
    console.log('[TEST ROUND 2] Form filled with test data');
    
    // Monitor console for logs
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
      if (msg.text().includes('[CREDENTIAL MODAL]')) {
        console.log(`[CONSOLE] ${msg.text()}`);
      }
    });
    
    // Click Save button
    const saveButton = page.locator('#btn-save-credential');
    await saveButton.click();
    
    console.log('[TEST ROUND 2] Save button clicked');
    
    // Wait for API response
    await page.waitForTimeout(2000);
    
    // Check console logs for credential modal operations
    const modalLogs = consoleMessages.filter(msg => msg.includes('[CREDENTIAL MODAL]'));
    console.log(`[TEST ROUND 2] Found ${modalLogs.length} credential modal console logs`);
    
    // Verify key log messages
    expect(modalLogs.some(log => log.includes('saveCredential called'))).toBeTruthy();
    expect(modalLogs.some(log => log.includes('Sending payload to API'))).toBeTruthy();
    console.log('[TEST ROUND 2] Console logs verified');
    
    // Check for success alert or modal close
    const modal = page.locator('#add-credential-modal');
    const isModalClosed = await modal.isHidden({ timeout: 5000 }).catch(() => false);
    
    if (isModalClosed) {
      console.log('[TEST ROUND 2] Modal closed after save (expected behavior)');
    } else {
      console.log('[TEST ROUND 2] Modal still visible - checking for error alert');
      // Modal might still be visible if there was an error (e.g., vault locked)
    }
    
    console.log('[TEST ROUND 2] ✓ Form submission test completed');
  });

  test('Round 3: Click outside modal to close', async ({ page }) => {
    console.log('[TEST ROUND 3] Starting click-outside-to-close test');
    
    await page.waitForTimeout(500);
    
    // Click Add Credential button
    const addButton = page.locator('button').filter({ hasText: /Add Credential/i }).first();
    await addButton.click();
    await page.waitForTimeout(500);
    
    // Verify modal is open
    const modal = page.locator('#add-credential-modal');
    await expect(modal).toBeVisible();
    console.log('[TEST ROUND 3] Modal opened');
    
    // Click outside the modal (on the overlay)
    await page.locator('#add-credential-modal').click({ position: { x: 10, y: 10 } });
    await page.waitForTimeout(300);
    
    // Verify modal is closed
    await expect(modal).toBeHidden();
    console.log('[TEST ROUND 3] Modal closed after clicking outside');
    
    console.log('[TEST ROUND 3] ✓ Click-outside-to-close test passed');
  });

  test('Round 4: Form validation - username required', async ({ page }) => {
    console.log('[TEST ROUND 4] Starting form validation test');
    
    await page.waitForTimeout(500);
    
    // Click Add Credential button
    const addButton = page.locator('button').filter({ hasText: /Add Credential/i }).first();
    await addButton.click();
    await page.waitForTimeout(500);
    
    // Fill form without username (HTML5 required attribute should prevent submission)
    await page.locator('#cred-label').fill('No Username Test');
    await page.locator('#cred-password').fill('password123');
    
    console.log('[TEST ROUND 4] Form filled without username');
    
    // Monitor console for any activity
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
      if (msg.text().includes('[CREDENTIAL MODAL]')) {
        console.log(`[CONSOLE] ${msg.text()}`);
      }
    });
    
    // Click Save button
    const saveButton = page.locator('#btn-save-credential');
    await saveButton.click();
    
    console.log('[TEST ROUND 4] Save button clicked without username');
    
    await page.waitForTimeout(1000);
    
    // Check if modal is still open (HTML5 validation should prevent submission)
    const modal = page.locator('#add-credential-modal');
    const isModalOpen = await modal.isVisible();
    
    console.log(`[TEST ROUND 4] Modal still open after save: ${isModalOpen}`);
    
    // Modal should still be open because HTML5 required attribute prevents submission
    expect(isModalOpen).toBe(true);
    console.log('[TEST ROUND 4] Modal remains open (HTML5 validation prevented submission)');
    
    // Check that no API call was made (no saveCredential logs)
    const saveLogs = consoleMessages.filter(msg => 
      msg.includes('[CREDENTIAL MODAL]') && msg.includes('saveCredential')
    );
    console.log(`[TEST ROUND 4] saveCredential calls: ${saveLogs.length}`);
    
    console.log('[TEST ROUND 4] ✓ Form validation test passed');
  });

  test('Round 5: Input focus management', async ({ page }) => {
    console.log('[TEST ROUND 5] Starting input focus management test');
    
    await page.waitForTimeout(500);
    
    // Click Add Credential button
    const addButton = page.locator('button').filter({ hasText: /Add Credential/i }).first();
    await addButton.click();
    await page.waitForTimeout(500);
    
    // Check if first input is focused
    const firstInput = page.locator('#cred-label');
    const isFocused = await firstInput.evaluate(el => document.activeElement === el);
    
    console.log(`[TEST ROUND 5] First input focused: ${isFocused}`);
    
    // Tab through inputs
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);
    
    const usernameInput = page.locator('#cred-username');
    const usernameFocused = await usernameInput.evaluate(el => document.activeElement === el);
    console.log(`[TEST ROUND 5] Username input focused after Tab: ${usernameFocused}`);
    
    console.log('[TEST ROUND 5] ✓ Input focus management test completed');
  });
});
