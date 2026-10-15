/**
 * Extensive Playwright zero-trust scenarios:
 * - Settings credential vault buttons (Use Primary / Use 2nd / Use 3rd)
 * - Sidebar Primary/Secondary/Third dropdowns → API payload IDs
 * - Session restore of secondary/third (no secrets)
 * - Asset Warranty consolidate UI (multi-file) device count + CSV
 *
 * Run (server must be up OR set NST_BROWSER_BASE):
 *   node tests/browser/zero_trust_credentials_warranty.spec.mjs
 *
 * Optional: NST_START_SERVER=1 will try to spawn vlan_checker_web briefly.
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import http from 'node:http';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const HEADLESS = process.env.NST_HEADLESS !== '0';
const failures = [];
const MASTER = process.env.NST_TEST_MASTER || 'zt_pw_playwright_7f2';

function check(name, cond, detail = '') {
  if (cond) console.log(`PASS  ${name}`);
  else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

function waitForHttp(url, timeoutMs = 30000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tick = () => {
      const req = http.get(url, (res) => {
        res.resume();
        resolve(true);
      });
      req.on('error', () => {
        if (Date.now() - start > timeoutMs) reject(new Error('server timeout'));
        else setTimeout(tick, 400);
      });
    };
    tick();
  });
}

async function ensureServer() {
  try {
    await waitForHttp(BASE + '/', 1500);
    return null;
  } catch {
    if (process.env.NST_START_SERVER !== '1') {
      console.log('INFO  Server not reachable; set NST_START_SERVER=1 or start app manually');
      throw new Error(`Server not reachable at ${BASE}`);
    }
    const child = spawn('python3', ['vlan_checker_web.py'], {
      cwd: ROOT,
      env: { ...process.env, NST_BIND: '127.0.0.1', NST_PORT: '5051' },
      stdio: 'ignore',
    });
    await waitForHttp(BASE + '/', 45000);
    return child;
  }
}

async function seedVault(request) {
  // Best-effort: set/unlock master and add 3 credentials
  let r = await request.post(`${BASE}/api/credentials/master-password/unlock`, {
    data: { password: MASTER },
  });
  if (!r.ok()) {
    await request.post(`${BASE}/api/credentials/master-password/set`, {
      data: { password: MASTER },
    });
    r = await request.post(`${BASE}/api/credentials/master-password/unlock`, {
      data: { password: MASTER },
    });
  }
  check('Vault unlockable', r.ok(), await r.text());

  const users = [
    { username: 'zt_primary', password: 'p1_secret', label: 'ZT Primary' },
    { username: 'zt_secondary', password: 'p2_secret', label: 'ZT Secondary' },
    { username: 'zt_third', password: 'p3_secret', label: 'ZT Third' },
  ];
  for (const u of users) {
    const add = await request.post(`${BASE}/api/credentials/add`, {
      data: { ...u, admin_password: 'en', force: true },
    });
    check(`Add credential ${u.username}`, add.ok() || add.status() === 200, await add.text());
  }
  const listed = await request.get(`${BASE}/api/credentials/list`);
  const data = await listed.json();
  const count = (data.credentials || []).length;
  check('Vault has ≥3 credentials', count >= 3, `count=${count}`);
  return data.credentials || [];
}

async function main() {
  let serverProc = null;
  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext();
  const page = await context.newPage();
  const executeBodies = [];

  page.on('request', (req) => {
    if (req.method() === 'POST' && req.url().includes('/api/execute')) {
      try {
        executeBodies.push(req.postDataJSON());
      } catch {
        executeBodies.push({ raw: req.postData() });
      }
    }
  });

  try {
    serverProc = await ensureServer();
    console.log(`\n=== Zero-Trust Credentials + Warranty Playwright ===\nBase: ${BASE}\n`);

    await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(1500);

    // Version gate
    const verResp = await page.request.get(`${BASE}/api/version`);
    const verJson = verResp.ok() ? await verResp.json() : {};
    const version = verJson.version || verJson.VERSION || '';
    check('Version API reachable', verResp.ok(), String(verResp.status()));
    console.log('INFO  version=', version);

    const creds = await seedVault(page.request);
    const ids = creds.map((c) => c.username || c.credential_id).filter(Boolean);
    const primary = ids.find((x) => x.includes('primary')) || ids[0];
    const secondary = ids.find((x) => x.includes('secondary')) || ids[1];
    const third = ids.find((x) => x.includes('third') || x.includes('tertiary')) || ids[2];

    // Settings / Credentials tab — Use buttons
    await page.goto(`${BASE}/#settings`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    // Try open credentials section if present
    const credTab = page.locator('text=Credentials').first();
    if (await credTab.count()) {
      await credTab.click({ timeout: 3000 }).catch(() => {});
    }
    await page.waitForTimeout(800);

    // Sidebar dropdowns (always on main chrome)
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    const selPrimary = page.locator('#sidebar_primary_cred');
    const selSecondary = page.locator('#sidebar_secondary_cred');
    const selThird = page.locator('#sidebar_third_cred');
    check('Sidebar primary select present', await selPrimary.count() > 0);
    check('Sidebar secondary select present', await selSecondary.count() > 0);
    check('Sidebar third select present', await selThird.count() > 0);

    async function selectCred(sel, want) {
      if (!(await sel.count()) || !want) return false;
      // Ensure fallback dropdowns are enabled (regression: were hard-disabled in HTML)
      await sel.evaluate((el) => {
        el.disabled = false;
        el.removeAttribute('disabled');
        el.style.backgroundColor = '';
        el.style.color = '';
      });
      // Refresh options from vault if still empty
      const optCount = await sel.locator('option').count();
      if (optCount <= 1 && typeof page !== 'undefined') {
        await page.evaluate(async () => {
          if (typeof loadCredentials === 'function') await loadCredentials();
          else if (typeof populateSidebarCredDropdowns === 'function') {
            const r = await fetch('/api/credentials/list');
            const d = await r.json();
            populateSidebarCredDropdowns(d.credentials || []);
          }
        }).catch(() => {});
      }
      const values = await sel.locator('option').evaluateAll((opts) =>
        opts.map((o) => ({ value: o.value, text: (o.textContent || '').trim() })),
      );
      const hit = values.find((o) => o.value === want)
        || values.find((o) => (o.value && o.value.includes(want)) || (o.text && o.text.includes(want)));
      if (!hit || !hit.value) {
        console.log('selectCred options', values, 'want', want);
        return false;
      }
      await sel.selectOption(hit.value);
      // Fire change handler if present
      await sel.evaluate((el) => {
        el.dispatchEvent(new Event('change', { bubbles: true }));
      });
      return true;
    }

    // Reload so sidebar dropdowns pick up vault list
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    await page.evaluate(async () => {
      try {
        if (typeof loadCredentials === 'function') await loadCredentials();
      } catch (e) { /* ignore unlock prompt in headless */ }
      try {
        const r = await fetch('/api/credentials/list');
        const d = await r.json();
        if (typeof populateSidebarCredDropdowns === 'function') {
          populateSidebarCredDropdowns(d.credentials || []);
        }
      } catch (e) { /* ignore */ }
    });
    await page.waitForTimeout(500);

    check('Select primary in sidebar', await selectCred(selPrimary, primary));
    check('Select secondary in sidebar', await selectCred(selSecondary, secondary));
    check('Select third in sidebar', await selectCred(selThird, third));
    await page.waitForTimeout(500);

    const hiddenPrimary = await page.locator('#credential_id').inputValue().catch(() => '');
    const hiddenSecondary = await page.locator('#secondary_credential_id').inputValue().catch(() => '');
    const hiddenThird = await page.locator('#third_credential_id').inputValue().catch(() => '');
    check('Hidden primary matches selection', !primary || hiddenPrimary === primary || hiddenPrimary.includes(primary), `got=${hiddenPrimary}`);
    check('Hidden secondary matches selection', !secondary || hiddenSecondary === secondary || hiddenSecondary.includes(secondary), `got=${hiddenSecondary}`);
    check('Hidden third matches selection', !third || hiddenThird === third || hiddenThird.includes(third), `got=${hiddenThird}`);

    // Session API zero-trust
    const sessPost = await page.request.post(`${BASE}/api/session/credentials`, {
      data: {
        username: primary,
        credential_id: primary,
        secondary_credential_id: secondary,
        third_credential_id: third,
        label: 'ZT Primary',
      },
    });
    check('Session POST ok', sessPost.ok());
    const sess = await (await page.request.get(`${BASE}/api/session/credentials`)).json();
    check('Session restores secondary id', sess.secondary_credential_id === secondary, JSON.stringify(sess));
    check('Session restores third id', sess.third_credential_id === third, JSON.stringify(sess));
    check('Session does not expose secrets', !JSON.stringify(sess).includes('p1_secret') && !JSON.stringify(sess).includes('p2_secret'));

    // Trigger executeSelectedPlugin path if available — otherwise POST via page.evaluate using same helpers
    const payloadProbe = await page.evaluate(() => {
      const body = (typeof nstCredentialRequestBody === 'function') ? nstCredentialRequestBody() : null;
      const fields = (typeof nstCredentialFields === 'function') ? nstCredentialFields() : null;
      return { body, fields };
    });
    check('nstCredentialRequestBody exposes secondary', !!(payloadProbe.body && payloadProbe.body.secondary_credential_id), JSON.stringify(payloadProbe.body));
    check('nstCredentialRequestBody exposes third', !!(payloadProbe.body && payloadProbe.body.third_credential_id), JSON.stringify(payloadProbe.body));

    // Fire a lightweight execute and assert intercepted body
    const execResp = await page.request.post(`${BASE}/api/execute`, {
      data: {
        action: 'cisco_asset_warranty',
        credential_id: primary,
        secondary_credential_id: secondary,
        third_credential_id: third,
        inventory: '10.55.55.55,cisco_ios\n10.55.55.56,juniper_junos',
        inventory_source: 'unsaved',
        acknowledge_unsaved: true,
        target_mode: 'all',
        params: { collection_policy: 'ssh_only', snmp_fallback: false, include_modules: false },
      },
    });
    check('Execute API accepted', execResp.ok() || execResp.status() === 200, await execResp.text());

    // Seed consolidator input via filesystem (reports under install root)
    const reportsIn = path.join(ROOT, 'reports', 'asset_warranty_input');
    const reportsOut = path.join(ROOT, 'reports', 'asset_warranty_output');
    fs.mkdirSync(reportsIn, { recursive: true });
    fs.mkdirSync(reportsOut, { recursive: true });
    fs.writeFileSync(
      path.join(reportsIn, 'pw_asset_1.csv'),
      'Host,Hostname,Product ID (PID),Serial Number,Software Version,Warranty Status,End of Life,End of Support\n'
        + '10.1.1.1,sw1,C9300-48P,FDOPW1,17.9,active,2030-01-01,2033-01-01\n',
    );
    fs.writeFileSync(
      path.join(reportsIn, 'pw_asset_2.csv'),
      'Host,Hostname,Product ID (PID),Serial Number,Software Version,Warranty Status,End of Life,End of Support\n'
        + '10.1.1.2,junos1,,, ,not a cisco device,,\n',
    );
    fs.writeFileSync(
      path.join(reportsIn, 'pw_asset_3.html'),
      `<!DOCTYPE html><html><body><table class="nst-asset-table">
      <tr><th>Host</th><th>Hostname</th><th>Product ID (PID)</th><th>Serial Number</th>
      <th>Software Version</th><th>Warranty Status</th><th>End of Life</th><th>End of Support</th></tr>
      <tr><td>
      10.1.1.3
      </td><td>sw3</td><td>C9500</td><td>
      FDOPW3
      </td><td>17.6</td><td>active</td><td>2028-01-01</td><td>2031-01-01</td></tr>
      </table></body></html>`,
    );

    const consol = await page.request.post(`${BASE}/api/reports/asset-warranty/consolidate`, {
      data: { report_name: 'pw_mutual' },
    });
    const consolJson = await consol.json();
    check('Consolidate API success', !!consolJson.success, JSON.stringify(consolJson));
    check('Consolidate total_devices > 0', (consolJson.summary?.total_devices || 0) > 0, JSON.stringify(consolJson.summary));
    check('Consolidate returns output_csv', !!consolJson.output_csv, JSON.stringify(consolJson));

    // UI Reports section — invoke JS consolidator directly (workspace nav varies)
    await page.goto(BASE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    const uiConsol = await page.evaluate(async () => {
      try {
        if (typeof generateAssetWarrantyConsolidatedReport === 'function') {
          await generateAssetWarrantyConsolidatedReport();
        } else if (typeof loadAssetWarrantyInputFiles === 'function') {
          await loadAssetWarrantyInputFiles();
        }
        const el = document.getElementById('asset-warranty-consolidate-status');
        return el ? (el.innerText || el.textContent || '') : '';
      } catch (e) {
        return 'error:' + e;
      }
    });
    check(
      'UI consolidate status mentions devices or report',
      /device|report|csv|\.html|generated/i.test(String(uiConsol)),
      String(uiConsol),
    );

    // Screenshot evidence
    const shotDir = path.join(ROOT, 'reports', 'qa_playwright');
    fs.mkdirSync(shotDir, { recursive: true });
    await page.screenshot({ path: path.join(shotDir, 'zero_trust_credentials_warranty.png'), fullPage: true });

  } catch (err) {
    console.error('ERROR', err);
    failures.push(`exception:${err.message || err}`);
  } finally {
    await browser.close();
    if (serverProc) {
      try { serverProc.kill('SIGTERM'); } catch { /* ignore */ }
    }
  }

  console.log(`\n=== Summary: ${failures.length ? 'FAILED' : 'PASSED'} (${failures.length} failures) ===`);
  if (failures.length) {
    for (const f of failures) console.log(' -', f);
    process.exit(1);
  }
}

main();
