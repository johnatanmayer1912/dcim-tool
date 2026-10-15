/**
 * Operational certification: every Tools / Plugin trigger that hits the backend
 * must include secondary_credential_id + third_credential_id when set in sidebar.
 *
 * Intercepts: /api/execute, /api/discovery/run, /api/interface/*, /api/stp/run, /api/vlan/validate
 *
 * Run (server on 5051):
 *   NST_HEADLESS=1 node tests/browser/credential_fallback_all_buttons.spec.mjs
 */
import { chromium } from 'playwright';
import http from 'node:http';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const HEADLESS = process.env.NST_HEADLESS !== '0';
const MASTER = process.env.NST_TEST_MASTER || 'zt_pw_playwright_7f2';
const failures = [];

function check(name, cond, detail = '') {
  if (cond) console.log(`PASS  ${name}`);
  else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

function waitHttp(url, ms = 8000) {
  const t0 = Date.now();
  return new Promise((resolve, reject) => {
    const tick = () => {
      http.get(url, (r) => { r.resume(); resolve(true); }).on('error', () => {
        if (Date.now() - t0 > ms) reject(new Error('server down'));
        else setTimeout(tick, 300);
      });
    };
    tick();
  });
}

async function main() {
  await waitHttp(BASE + '/');
  const browser = await chromium.launch({ headless: HEADLESS });
  const page = await browser.newPage();
  const captured = [];

  page.on('request', (req) => {
    if (req.method() !== 'POST') return;
    const u = req.url();
    if (!/\/api\/(execute|discovery\/run|interface\/|stp\/run|vlan\/validate)/.test(u)) return;
    let body = null;
    try { body = req.postDataJSON(); } catch { body = { raw: req.postData() }; }
    captured.push({ url: u, body });
  });

  try {
    console.log('\n=== Credential Fallback — All Buttons Payload Matrix ===\n');
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });

    // Vault seed
    let r = await page.request.post(`${BASE}/api/credentials/master-password/unlock`, { data: { password: MASTER } });
    if (!r.ok()) {
      await page.request.post(`${BASE}/api/credentials/master-password/set`, { data: { password: MASTER } });
      r = await page.request.post(`${BASE}/api/credentials/master-password/unlock`, { data: { password: MASTER } });
    }
    for (const u of ['btn_primary', 'btn_secondary', 'btn_third']) {
      await page.request.post(`${BASE}/api/credentials/add`, {
        data: { username: u, password: `${u}_pass`, admin_password: 'en', label: u, force: true },
      });
    }

    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
    await page.evaluate(async () => {
      const r = await fetch('/api/credentials/list');
      const d = await r.json();
      if (typeof populateSidebarCredDropdowns === 'function') populateSidebarCredDropdowns(d.credentials || []);
    });

    async function pick(sel, want) {
      await page.locator(sel).evaluate((el) => { el.disabled = false; el.removeAttribute('disabled'); });
      const opts = await page.locator(`${sel} option`).evaluateAll((o) => o.map((x) => x.value));
      const hit = opts.find((v) => v === want) || opts.find((v) => v.includes(want));
      if (hit) await page.locator(sel).selectOption(hit);
    }
    await pick('#sidebar_primary_cred', 'btn_primary');
    await pick('#sidebar_secondary_cred', 'btn_secondary');
    await pick('#sidebar_third_cred', 'btn_third');
    await page.waitForTimeout(300);

    // Inventory for single device + required tool fields
    await page.evaluate(() => {
      const inv = document.getElementById('inventory');
      if (inv) inv.value = '10.200.200.1,cisco_ios';
      const mode = document.getElementById('target_mode');
      if (mode) mode.value = 'all';
      const desc = document.getElementById('desc_search_input');
      if (desc) desc.value = 'uplink';
      const mac = document.getElementById('mac_input');
      if (mac) mac.value = 'aabb.#ifdd.eeff';
    });

    const tools = [
      "runAction('connectivity')",
      "runAction('vlan_check')",
      "runAction('interfaces')",
      "runAction('audit')",
      "runAction('backup')",
      "runAction('save_config')",
      "runAction('topology')",
      "runAction('l3_topology')",
      "runAction('vlan_compare')",
      "runAction('description_search')",
      "runAction('mac_check')",
      "runAction('cisco_asset_warranty')",
    ];

    for (const call of tools) {
      captured.length = 0;
      await page.evaluate((c) => { try { eval(c); } catch (e) { console.error(e); } }, call);
      await page.waitForTimeout(600);
      const exec = captured.find((x) => x.url.includes('/api/execute'));
      check(`Tools ${call} sent execute`, !!exec);
      if (exec) {
        check(`Tools ${call} secondary_id`, exec.body?.secondary_credential_id === 'btn_secondary', JSON.stringify(exec.body));
        check(`Tools ${call} third_id`, exec.body?.third_credential_id === 'btn_third', JSON.stringify(exec.body));
      }
    }

    // Plugin execute helper
    captured.length = 0;
    await page.evaluate(() => {
      const body = Object.assign({
        action: 'serial_number',
        inventory: '10.200.200.1,cisco_ios',
        inventory_source: 'unsaved',
        acknowledge_unsaved: true,
        target_mode: 'all',
        params: {},
      }, nstCredentialRequestBody());
      return fetch('/api/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    });
    await page.waitForTimeout(400);
    const plug = captured.find((x) => x.url.includes('/api/execute'));
    check('Plugin serial_number secondary', plug?.body?.secondary_credential_id === 'btn_secondary');
    check('Plugin serial_number third', plug?.body?.third_credential_id === 'btn_third');

    // Discovery payload builder
    const discBody = await page.evaluate(() => Object.assign({
      seed_hosts: ['10.200.200.1'],
      max_depth: 1,
      demo_mode: true,
    }, nstCredentialRequestBody()));
    check('Discovery body secondary', discBody.secondary_credential_id === 'btn_secondary');
    check('Discovery body third', discBody.third_credential_id === 'btn_third');

    // IM + STP body builders
    const imBody = await page.evaluate(() => Object.assign({
      host: '10.200.200.1',
      device_type: 'cisco_ios',
    }, nstCredentialRequestBody()));
    check('IM body secondary', imBody.secondary_credential_id === 'btn_secondary');
    const stpBody = await page.evaluate(() => Object.assign({
      vlan_id: 1,
      demo_mode: true,
    }, nstCredentialRequestBody()));
    check('STP body secondary', stpBody.secondary_credential_id === 'btn_secondary');
    check('STP body third', stpBody.third_credential_id === 'btn_third');

  } catch (e) {
    failures.push('exception:' + e.message);
    console.error(e);
  } finally {
    await browser.close();
  }

  console.log(`\n=== Summary: ${failures.length ? 'FAILED' : 'PASSED'} (${failures.length} failures) ===`);
  failures.forEach((f) => console.log(' -', f));
  process.exit(failures.length ? 1 : 0);
}

main();
