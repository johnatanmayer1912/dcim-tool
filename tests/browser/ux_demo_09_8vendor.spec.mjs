/**
 * file:// UX demo 09 — offline 8-vendor lab operator controls.
 * Static HTML. Not live-vendor. Not EXE E2E.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { startTrace, stopTrace, shot } from './_qa_trace.mjs';

const failures = [];
function check(name, cond, detail = '') {
  if (cond) console.log(`PASS  ${name}`);
  else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

function colorOf(elStroke) {
  return String(elStroke || '').toLowerCase();
}

async function main() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const html = path.resolve(here, '../../docs/11-ux/demos/09-offline-8vendor-lab.html');
  if (!fs.existsSync(html)) {
    console.error('missing demo 09 HTML');
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await startTrace(context);
  const page = await context.newPage();
  await page.goto(pathToFileURL(html).href, { waitUntil: 'domcontentloaded', timeout: 30000 });

  const body = await page.locator('body').innerText();
  check('8 vendor devices named', ['NX-CORE-01', 'NX-CORE-02', 'NX-AGG-01', 'IOS-DIST-01', 'IOS-XE-DIST-02', 'IOS-ACC-01', 'JN-ACC-01', 'JN-ACC-02'].every((n) => body.includes(n)));
  check('honesty: replay is not a live poll', /Replay is not a live poll/i.test(body));
  check('honesty: Live SSH is not SNMP', /Live SSH is not SNMP/i.test(body));
  check('no password field', await page.locator('input[type="password"]').count() === 0);

  const evpnBefore = await page.locator('#e-evpn').getAttribute('stroke');
  await page.locator('#overlay-on').check();
  await page.waitForTimeout(200);
  const core = await page.locator('#e-core').getAttribute('stroke');
  const evpnAfter = await page.locator('#e-evpn').getAttribute('stroke');
  const stpAfter = await page.locator('#e-stp').getAttribute('stroke');
  check('replay paints core L2 hot', colorOf(core).includes('#ef4444') || colorOf(core).includes('ef4444'));
  check('replay does not gray EVPN as unsampled cable', colorOf(evpnAfter).includes('a855f7'));
  check('replay does not gray STP-blocked as unsampled cable', colorOf(stpAfter).includes('f97316'));
  check('EVPN color unchanged by overlay', colorOf(evpnBefore) === colorOf(evpnAfter));

  await page.locator('#e-core').click({ force: true });
  const insp = await page.locator('#insp-dl').innerText();
  check('inspector shows core L2 identity', /NX-CORE-01/i.test(insp) && /Eth1\/1/i.test(insp));

  await page.locator('#btn-discovery').click();
  check('Discovery disables Live SSH', await page.locator('#btn-live').isDisabled());
  await page.locator('#btn-std-l2').click();
  check('Standard L2 enables Live SSH button', await page.locator('#btn-live').isEnabled());

  await page.selectOption('#cred-select', '');
  page.once('dialog', async (d) => { await d.accept(); });
  await page.locator('#btn-live').click();
  await page.locator('#live-go').click();
  await page.waitForTimeout(300);
  const fresh = await page.locator('#freshness').innerText();
  check('live without credential does not claim live poll', !/lab poll/i.test(fresh) || /not a lab poll/i.test(fresh));

  await page.selectOption('#cred-select', 'lab-ops');
  await page.locator('#btn-live').click();
  await page.locator('#live-go').click();
  await page.waitForTimeout(600);
  const fresh2 = await page.locator('#freshness').innerText();
  check('live with credential is labeled simulation / not SNMP', /not SNMP/i.test(fresh2) && /not a lab poll/i.test(fresh2));
  const evpnLive = await page.locator('#e-evpn').getAttribute('stroke');
  check('live simulation still leaves EVPN purple', colorOf(evpnLive).includes('a855f7'));

  await page.locator('#btn-overlay-off').click();
  const coreOff = await page.locator('#e-core').getAttribute('stroke');
  check('overlay off restores core L2 (not hot red)', !colorOf(coreOff).includes('ef4444'));

  await shot(page, 'ux_demo_09_8vendor');
  await stopTrace(context, 'ux_demo_09_8vendor');
  await browser.close();

  if (failures.length) {
    console.error(`\n${failures.length} failure(s): ${failures.join(', ')}`);
    process.exit(1);
  }
  console.log('\nAll UX demo 09 8-vendor lab scenarios passed.');
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
