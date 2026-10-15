/**
 * Operator console — enterprise shell contracts after UI redesign.
 * Requires Flask on loopback (run_operator_browser_qa / run_playwright_e2e).
 * Not live-vendor. Not EXE E2E.
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
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
  const page = await context.newPage();
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });

  check('brand present', await page.locator('#nst-brand-link').isVisible());
  check('chrome meta present', await page.locator('.nst-chrome-meta').count() > 0);
  check('vault pill id preserved', await page.locator('#nst-vault-pill').count() === 1);
  check('inventory workspace active', await page.locator('#ws-inventory.is-active').count() === 1);
  check('inventory editor in workspace', await page.locator('#ws-inventory #nst-inventory-block').count() === 1);
  check('parsed hosts table present', await page.locator('#nst-inv-host-body').count() === 1);
  check('task log starts collapsed', await page.locator('#console-panel.collapsed').count() === 1);
  check('no Made by AI IDE', !(await page.content()).includes('Made by AI IDE'));

  await page.locator('#ws-nav-maps').click();
  await page.waitForTimeout(200);
  const mapsLede = await page.locator('#ws-maps .lede').innerText();
  check('maps lede: replay honesty', /Replay is not a live poll/i.test(mapsLede));
  check('maps lede: live ssh not snmp', /Live SSH is not SNMP/i.test(mapsLede));

  await page.evaluate(() => {
    const seg = document.getElementById('tab-segment-tools');
    if (seg) switchTab('tools', seg);
  });
  check('swiss tools shortcuts demoted to btn-mac', await page.locator('.nst-start-workflows .btn-mac').count() >= 4);
  check('goToSearchTab still callable', await page.evaluate(() => typeof goToSearchTab === 'function'));
  check('goToToolsTab still callable', await page.evaluate(() => typeof goToToolsTab === 'function'));

  await browser.close();
  if (failures.length) {
    console.error('FAILED:', failures.join(', '));
    process.exit(1);
  }
  console.log('operator_enterprise_shell: ALL PASS');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
