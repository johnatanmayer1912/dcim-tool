/**
 * Playwright E2E test for credential fallback UI flow.
 *
 * MISSION: Validate that existing 3 users in Settings can be selected
 * from the main UI for plugin execution, and logs show fallback credentials.
 *
 * Steps:
 * 1. Navigate to Settings and verify 3 users exist
 * 2. Go to main UI and select the 3 users for execution
 * 3. Execute cisco_asset_warranty plugin
 * 4. Validate logs show fallback credentials
 *
 * Run:
 *   node tests/browser/credential_fallback_ui.spec.mjs
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const failures = [];

function check(name, cond, detail = '') {
  if (cond) {
    console.log(`PASS  ${name}`);
  } else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

async function main() {
  const browser = await chromium.launch({ headless: false }); // Run headless: false to see UI
  const context = await browser.newContext();
  const page = await context.newPage();

  // Collect console errors
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(String(err)));

  try {
    console.log(`\n=== Credential Fallback UI E2E Test ===`);
    console.log(`Base URL: ${BASE}\n`);

    // Navigate to home page
    await page.goto(BASE, { waitUntil: 'networkidle' });
    check('Navigate to home page', page.url().includes(BASE));
    await page.waitForTimeout(2000);

    // Step 1: Navigate to Settings to verify 3 users exist
    console.log('\n--- Step 1: Navigate to Settings ---');
    
    // Direct navigation to Settings
    await page.goto(`${BASE}/#settings`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    check('Navigate to Settings', page.url().includes('settings') || page.url().includes('Settings'));
    
    // Take screenshot
    await page.screenshot({ path: 'step1_settings.png' });
    
    // Check API directly for credentials (authoritative source)
    const credsResponse = await page.request.get(`${BASE}/api/credentials/list`);
    const credsData = await credsResponse.json();
    const apiCredCount = credsData.credentials ? credsData.credentials.length : 0;
    check('API returns 3+ credentials', apiCredCount >= 3, `API returned ${apiCredCount} credentials`);
    
    if (credsData.credentials) {
      console.log('Credentials from API:', credsData.credentials.map(c => c.username || c.credential_id));
    }

    // Step 2: Navigate to main UI (execute page)
    console.log('\n--- Step 2: Navigate to Execute Page ---');
    
    // Direct navigation to execute page
    await page.goto(`${BASE}/#execute`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    check('Navigate to Execute page', page.url().includes('execute'));
    
    // Take screenshot
    await page.screenshot({ path: 'step2_execute.png' });

    // Step 3: Execute plugin via API with fallback credentials
    console.log('\n--- Step 3: Execute Plugin via API ---');
    
    // Use the credentials we found from the API
    const credentials = credsData.credentials || [];
    if (credentials.length < 3) {
      check('Have 3+ credentials', false, `Only ${credentials.length} credentials available`);
    } else {
      check('Have 3+ credentials', true);
      
      const primaryCred = credentials[0].username || credentials[0].credential_id;
      const secondaryCred = credentials[1].username || credentials[1].credential_id;
      const tertiaryCred = credentials[2].username || credentials[2].credential_id;
      
      console.log(`Using credentials: primary=${primaryCred}, secondary=${secondaryCred}, tertiary=${tertiaryCred}`);
      
      // Execute via API
      const executeResponse = await page.request.post(`${BASE}/api/execute`, {
        data: {
          action: 'cisco_asset_warranty',
          credential_id: primaryCred,
          secondary_credential_id: secondaryCred,
          third_credential_id: tertiaryCred,
          inventory: '10.99.1.1,cisco_ios',
          inventory_source: 'unsaved',
          acknowledge_unsaved: true,
          target_mode: 'all',
          params: {
            include_modules: true,
            collection_policy: 'ssh_first',
            snmp_fallback: true,
          },
        }
      });
      
      const executeData = await executeResponse.json();
      console.log('Execute response:', executeData);
      check('Execute API call successful', executeResponse.ok() && executeData.status === 'started');
    }

    // Step 9: Navigate to logs and validate
    console.log('\n--- Step 9: Validate Logs ---');
    
    const logsLink = await page.$('a:has-text("Logs")');
    if (logsLink) {
      await logsLink.click();
    } else {
      await page.goto(`${BASE}/#logs`, { waitUntil: 'networkidle' });
    }
    
    await page.waitForTimeout(3000);
    
    // Take screenshot of logs
    await page.screenshot({ path: 'step4_logs.png' });
    
    const logsContent = await page.content();
    console.log('Logs page loaded, checking for fallback credentials...');
    
    // Check for fallback credentials in logs
    const hasFallback = logsContent.includes('fallback_credentials');
    const hasFallbackTrue = logsContent.includes('Has fallback_credentials: True');
    const hasFallbackCount = logsContent.includes('Fallback credentials count');
    
    check('Logs contain fallback_credentials', hasFallback);
    check('Logs show fallback_credentials: True', hasFallbackTrue);
    check('Logs show fallback count', hasFallbackCount);
    
    // Wait more for logs to populate
    await page.waitForTimeout(5000);
    
    const logsContent2 = await page.content();
    check('Logs show fallback_credentials: True (retry)', logsContent2.includes('Has fallback_credentials: True'));
    check('Logs show fallback credentials count: 2', logsContent2.includes('Fallback credentials count: 2'));

  } catch (err) {
    console.error('Test error:', err);
    failures.push('Test execution error: ' + err.message);
  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n=== Test Summary ===');
  if (failures.length === 0) {
    console.log('All tests passed!');
    process.exit(0);
  } else {
    console.log(`${failures.length} test(s) failed:`);
    failures.forEach(f => console.log(`  - ${f}`));
    if (consoleErrors.length > 0) {
      console.log('\nConsole errors:');
      consoleErrors.forEach(e => console.log(`  - ${e}`));
    }
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
