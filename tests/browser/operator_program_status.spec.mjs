/**
 * Operator console Playwright — Program Status, workspaces, hard-stop honesty.
 *
 * Requires mocked QA server (full Flask app on loopback):
 *   python3 scripts/run_operator_browser_qa.py
 *
 * No live SSH. No vault secrets in DOM.
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const VAULT_SECRET = 'browser-qa-vault-secret-never-in-dom';

const failures = [];
function check(name, cond, detail = '') {
  if (cond) {
    console.log(`PASS  ${name}`);
  } else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

async function waitProgramStatusGate(page, selector, timeout = 20000) {
  await page.waitForFunction(
    (sel) => {
      const el = document.querySelector(sel);
      const t = (el && el.textContent) || '';
      return /BLOCKED|HARD STOP|Release gate/i.test(t);
    },
    selector,
    { timeout },
  );
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  // Suppress first-run health wizard so workspace navigation is testable
  await context.addInitScript(() => {
    localStorage.setItem('nst_health_ok', '1');
  });
  const page = await context.newPage();
  const consoleLines = [];
  page.on('console', (msg) => consoleLines.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', (err) => consoleLines.push({ type: 'pageerror', text: String(err) }));

  // 1 — App launch / first paint
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  check('operator index loads', page.url().startsWith(BASE));
  check('brand link present', await page.locator('#nst-brand-link').isVisible());
  check('main workspace region present', await page.locator('#nst-main').count() > 0);

  const severe = consoleLines.filter(
    (l) => l.type === 'error' || l.type === 'pageerror',
  ).filter((l) => !/favicon|socket\.io|Failed to load resource.*404/i.test(l.text));
  check('no severe console errors on first paint', severe.length === 0, JSON.stringify(severe.slice(0, 3)));

  const html = await page.content();
  check('first paint HTML has no vault secret', !html.includes(VAULT_SECRET));

  // 2 — API program-status (authoritative, blocked)
  const ps = await page.evaluate(async () => {
    const r = await fetch('/api/discovery/program-status');
    return { status: r.status, body: await r.json() };
  });
  check('program-status API returns 200', ps.status === 200);
  check('program-status release_gate BLOCKED', ps.body?.readiness?.release_gate === 'BLOCKED');
  check('program-status hard_stop true', ps.body?.readiness?.hard_stop === true);
  check('may_claim_enterprise_ready false', ps.body?.readiness?.may_claim_enterprise_ready === false);
  const psBlob = JSON.stringify(ps.body);
  check('program-status JSON has no password field values', !/password/i.test(psBlob) || !psBlob.includes(VAULT_SECRET));

  // 3 — Maps workspace → Discovery tab → Program Status panel
  await page.evaluate(() => {
    nstShowWorkspace('maps', { skipDefaultTab: true });
    const seg = document.getElementById('tab-segment-discovery');
    if (seg) switchTab('discovery', seg);
  });
  await page.waitForSelector('#disc-program-status', { timeout: 10000 });
  await page.evaluate(async () => {
    if (typeof discRefreshProgramStatus === 'function') await discRefreshProgramStatus();
  });
  await waitProgramStatusGate(page, '#disc-program-status-gate');
  const discGate = await page.locator('#disc-program-status-gate').innerText();
  check('Discovery tab shows HARD STOP gate', /HARD STOP|BLOCKED/i.test(discGate), discGate);
  check('Discovery gate denies enterprise ready', /Enterprise ready:\s*NO|NOT VALIDATED/i.test(discGate), discGate);

  const discJumps = await page.locator('#disc-program-status-jumps button').count();
  check('Discovery related-surface jump buttons present', discJumps >= 3);

  // 4 — Swiss Tools overview strip (inventory map entry surface)
  await page.evaluate(() => {
    const seg = document.getElementById('tab-segment-tools');
    if (seg) switchTab('tools', seg);
  });
  await page.waitForFunction(() => {
    const el = document.getElementById('tab-tools');
    return el && !el.hasAttribute('hidden');
  }, null, { timeout: 10000 });
  await page.evaluate(async () => {
    if (typeof nstRefreshProgramStatusOverview === 'function') {
      await nstRefreshProgramStatusOverview();
    }
  });
  await waitProgramStatusGate(page, '#nst-ps-overview-tools .nst-ps-overview-gate');
  const toolsGate = await page.locator('#nst-ps-overview-tools .nst-ps-overview-gate').innerText();
  check('Swiss Tools overview shows blocked gate', /BLOCKED|HARD STOP/i.test(toolsGate), toolsGate);
  const toolsOverview = await page.locator('#nst-ps-overview-tools').innerText();
  check('Swiss Tools overview mentions three surfaces', /three surfaces|Discovery tab|Inventory/i.test(toolsOverview), toolsOverview.slice(0, 120));

  // 5 — Related-surface navigation (Discovery tab from Tools)
  await page.evaluate(async () => {
    if (typeof nstOpenRelatedSurface === 'function') nstOpenRelatedSurface('discovery_tab');
    if (typeof discRefreshProgramStatus === 'function') await discRefreshProgramStatus();
  });
  await waitProgramStatusGate(page, '#disc-program-status-gate');
  check('jump to Discovery tab works', await page.locator('#disc-program-status').isVisible());

  // 6 — Evidence workspace overview
  await page.evaluate(async () => {
    nstShowWorkspace('evidence');
    if (typeof nstRefreshProgramStatusOverview === 'function') {
      await nstRefreshProgramStatusOverview();
    }
  });
  await waitProgramStatusGate(page, '#nst-ps-overview-evidence .nst-ps-overview-gate');
  const evGate = await page.locator('#nst-ps-overview-evidence .nst-ps-overview-gate').innerText();
  check('Evidence overview shows blocked gate', /BLOCKED|HARD STOP/i.test(evGate), evGate);
  check('Evidence job table present', await page.locator('#nst-evidence-table').isVisible());

  // 7 — No claim inflation in visible operator copy
  const bodyText = await page.locator('body').innerText();
  check('visible copy does not claim enterprise operational ready', !/enterprise operational ready:\s*yes/i.test(bodyText));
  check('visible copy does not claim live vendor validated', !/live truncated cdp\/lldp:\s*validated/i.test(bodyText));

  // 8 — Hash deep-link, About, jobs API, 404 report, reload (operator repeat use)
  await page.evaluate(() => { window.location.hash = 'nst-about'; });
  await page.waitForFunction(() => {
    const el = document.getElementById('tab-about');
    return el && !el.hasAttribute('hidden');
  }, null, { timeout: 10000 });
  await page.evaluate(async () => {
    if (typeof nstApplyRelatedSurfaceHash === 'function') nstApplyRelatedSurfaceHash();
    if (typeof nstRefreshProgramStatusOverview === 'function') await nstRefreshProgramStatusOverview();
  });
  check('hash nst-about opens About workspace', await page.locator('#tab-about').isVisible());

  await page.evaluate(() => { window.location.hash = 'nst-discovery'; });
  await page.evaluate(() => {
    if (typeof nstApplyRelatedSurfaceHash === 'function') nstApplyRelatedSurfaceHash();
  });
  await page.waitForSelector('#disc-program-status', { timeout: 10000 });
  check('hash nst-discovery returns to Discovery', await page.locator('#disc-program-status').isVisible());

  const jobs = await page.evaluate(async () => {
    const r = await fetch('/api/jobs');
    return { status: r.status, body: await r.json() };
  });
  check('jobs API returns 200', jobs.status === 200);
  const jobBlob = JSON.stringify(jobs.body);
  check('jobs API has no vault secret', !jobBlob.includes(VAULT_SECRET));

  const ver = await page.evaluate(async () => {
    const r = await fetch('/api/version');
    return { status: r.status, body: await r.json() };
  });
  check('version API returns 200', ver.status === 200);
  check('version API has version string', Boolean(ver.body?.version));

  const missingMap = await page.evaluate(async () => {
    const r = await fetch('/api/discovery/report/no-such-job-id');
    return r.status;
  });
  check('missing discovery report is 4xx', missingMap >= 400 && missingMap < 500);

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForSelector('#nst-brand-link', { timeout: 15000 });
  const afterReload = await page.evaluate(async () => {
    const r = await fetch('/api/discovery/program-status');
    return r.json();
  });
  check('reload still reports BLOCKED gate', afterReload?.readiness?.release_gate === 'BLOCKED');
  check('reload still hard_stop', afterReload?.readiness?.hard_stop === true);

  const reviewDir = process.env.NST_REVIEW_DIR;
  if (reviewDir) {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const shotDir = path.join(reviewDir, 'browser');
    fs.mkdirSync(shotDir, { recursive: true });
    await page.screenshot({ path: path.join(shotDir, 'operator_after_reload.png'), fullPage: true });
  }

  await browser.close();

  if (failures.length) {
    console.error(`\n${failures.length} failure(s): ${failures.join(', ')}`);
    process.exit(1);
  }
  console.log('\nAll operator Program Status browser scenarios passed.');
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
