/**
 * Operator console Playwright — Swiss Tools utilization overlay honesty.
 *
 * Mocked loopback only. Must not start Live SSH collection.
 * Requires: python3 scripts/run_operator_browser_qa.py (or run_playwright_e2e.py)
 */
import { chromium } from 'playwright';
import { startTrace, stopTrace, shot } from './_qa_trace.mjs';

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

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await context.addInitScript(() => {
    localStorage.setItem('nst_health_ok', '1');
  });
  await startTrace(context);
  const page = await context.newPage();
  const executeHits = [];
  await page.route('**/api/execute', async (route) => {
    const post = route.request().postData() || '';
    executeHits.push(post);
    if (/utilization_live/i.test(post)) {
      await route.abort('failed');
      return;
    }
    await route.continue();
  });

  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.evaluate(() => {
    if (typeof nstShowWorkspace === 'function') nstShowWorkspace('maps', { skipDefaultTab: true });
    const seg = document.getElementById('tab-segment-tools');
    if (seg && typeof switchTab === 'function') switchTab('tools', seg);
  });
  await page.waitForFunction(() => {
    const el = document.getElementById('tab-tools');
    return el && !el.hasAttribute('hidden');
  }, null, { timeout: 10000 });

  const mapsLede = await page.locator('#ws-maps .lede').innerText();
  check(
    'Maps workspace lede: replay is not a live poll',
    /Replay is not a live poll/i.test(mapsLede),
    mapsLede.slice(0, 240),
  );
  check(
    'Maps workspace lede: Live SSH is not SNMP',
    /Live SSH is not SNMP/i.test(mapsLede),
    mapsLede.slice(0, 240),
  );
  check(
    'Maps lede: overlay does not certify topology',
    /does not certify topology/i.test(mapsLede),
    mapsLede.slice(0, 240),
  );
  check(
    'Live SSH utilization control exists in DOM',
    await page.locator('#tools-util-live-btn').count() === 1,
  );
  check(
    'Live SSH control is visible before a map run',
    await page.locator('#tools-util-live-btn').isVisible(),
  );
  check(
    'Live SSH control is disabled until Standard L2 completes',
    await page.locator('#tools-util-live-btn').isDisabled(),
  );

  await page.evaluate(() => {
    const idEl = document.getElementById('credential_id');
    if (idEl) idEl.value = '';
    const user = document.getElementById('username');
    if (user) user.value = '';
    const pwd = document.getElementById('password');
    if (pwd) pwd.value = '';
  });

  let dialogText = '';
  page.once('dialog', async (d) => {
    dialogText = d.message();
    await d.accept();
  });
  await page.evaluate(() => {
    if (typeof toolsStartLiveUtilization === 'function') toolsStartLiveUtilization();
  });
  await page.waitForTimeout(400);
  check(
    'live start without Standard L2 map fails closed',
    /standard l2/i.test(dialogText) && /not SNMP/i.test(dialogText),
    dialogText,
  );
  check(
    'live start without map did not POST utilization_live',
    !executeHits.some((p) => /utilization_live/i.test(p)),
    JSON.stringify(executeHits.slice(0, 3)),
  );

  dialogText = '';
  page.once('dialog', async (d) => {
    dialogText = d.message();
    await d.accept();
  });
  await page.evaluate(() => {
    const btn = document.getElementById('tools-util-live-btn');
    if (btn) btn.disabled = false;
    if (typeof toolsStartLiveUtilization === 'function') toolsStartLiveUtilization();
  });
  await page.waitForTimeout(400);
  check(
    'live start without credential_id fails closed with honesty copy',
    /credential_id/i.test(dialogText) && /not SNMP/i.test(dialogText),
    dialogText,
  );
  check(
    'live start without credential did not POST utilization_live',
    !executeHits.some((p) => /utilization_live/i.test(p)),
    JSON.stringify(executeHits.slice(0, 3)),
  );

  const st = await page.evaluate(async () => {
    const r = await fetch('/api/utilization-overlay/status');
    return { status: r.status, body: await r.json() };
  });
  check('utilization status API 200', st.status === 200);
  check('utilization status idle or non-running', st.body?.status !== 'running');
  const note = String(st.body?.note || '');
  check('utilization status note: Not SNMP', /not snmp/i.test(note), note);
  check('utilization status does not clear release_gate in copy', /does not clear release_gate/i.test(note), note);
  check('utilization status JSON has no vault secret', !JSON.stringify(st.body).includes(VAULT_SECRET));

  const ps = await page.evaluate(async () => {
    const r = await fetch('/api/discovery/program-status');
    return r.json();
  });
  check(
    'overlay status poll does not clear release_gate',
    ps?.readiness?.release_gate === 'BLOCKED',
  );
  check('overlay status poll leaves hard_stop true', ps?.readiness?.hard_stop === true);

  await shot(page, 'operator_swiss_tools_overlay');
  await stopTrace(context, 'operator_swiss_tools_overlay');
  await browser.close();

  if (failures.length) {
    console.error(`\n${failures.length} failure(s): ${failures.join(', ')}`);
    process.exit(1);
  }
  console.log('\nAll Swiss Tools overlay honesty browser scenarios passed.');
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
