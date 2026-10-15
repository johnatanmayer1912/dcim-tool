/**
 * Playwright — Failure Correlation Engine UI wiring (mocked execute).
 *
 * Validates tile presence, workspace navigation, and that clicking the tile
 * posts action=failure_correlation with credential_id (Zero Trust).
 */
import { chromium } from 'playwright';
import { startTrace, stopTrace, shot } from './_qa_trace.mjs';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5052';
const failures = [];
function check(name, cond, detail = '') {
  if (cond) console.log(`PASS  ${name}`);
  else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await context.addInitScript(() => {
    localStorage.setItem('nst_health_ok', '1');
  });
  await startTrace(context);
  const page = await context.newPage();
  const executeBodies = [];

  await page.route('**/api/execute', async (route) => {
    const post = route.request().postData() || '';
    executeBodies.push(post);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'started', task_id: 'pw-corr-1' }),
    });
  });
  await page.route('**/api/credentials/**', async (route) => {
    if (route.request().method() === 'GET' && route.request().url().includes('master-password/status')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ready: true, unlocked: true, locked: false, mode: 'machine_key',
          is_required: false, message: 'ready',
        }),
      });
      return;
    }
    if (route.request().url().includes('/api/credentials') && route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          credentials: [{ credential_id: 'lab-admin', username: 'lab-admin', label: 'lab' }],
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.evaluate(() => {
    const hid = document.getElementById('credential_id');
    if (hid) hid.value = 'lab-admin';
    const sel = document.getElementById('sidebar_primary_cred');
    if (sel) {
      if (![...sel.options].some((o) => o.value === 'lab-admin')) {
        const opt = document.createElement('option');
        opt.value = 'lab-admin';
        opt.textContent = 'lab-admin';
        sel.appendChild(opt);
      }
      sel.value = 'lab-admin';
    }
    if (typeof nstSyncCredIdsFromSidebar === 'function') nstSyncCredIdsFromSidebar();
  });

  check('Failure correlation tile exists', await page.locator('#btn-failure-correlation').count() === 1);
  check('Tile label mentions Failure correlation', await page.locator('#btn-failure-correlation').innerText().then((t) => /Failure correlation/i.test(t)));

  await page.evaluate(() => {
    if (typeof nstShowWorkspace === 'function') nstShowWorkspace('maps', { skipDefaultTab: true });
    const seg = document.getElementById('tab-segment-tools');
    if (seg && typeof switchTab === 'function') switchTab('tools', seg);
  });
  await page.waitForFunction(() => {
    const el = document.getElementById('tab-tools');
    return el && !el.hasAttribute('hidden');
  }, null, { timeout: 10000 });
  await page.locator('#btn-failure-correlation').scrollIntoViewIfNeeded();
  await page.locator('#btn-failure-correlation').click({ force: true });
  await page.waitForTimeout(500);

  const corrPosts = executeBodies.filter((b) => /failure_correlation/i.test(b));
  check('Execute posted failure_correlation', corrPosts.length >= 1, `posts=${executeBodies.length}`);
  if (corrPosts.length) {
    check('Payload includes credential_id', /credential_id/i.test(corrPosts[0]));
    check('Payload action is failure_correlation', /"action"\s*:\s*"failure_correlation"/.test(corrPosts[0]));
  }

  await shot(page, 'failure_correlation_tile');
  await stopTrace(context, 'failure_correlation');
  await browser.close();
  if (failures.length) {
    console.error('FAILED:', failures.join(', '));
    process.exit(1);
  }
  console.log(`OK ${corrPosts.length} correlation execute capture(s)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
