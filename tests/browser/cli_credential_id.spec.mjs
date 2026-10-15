/**
 * Real Chromium Playwright validation for /cli_terminal credential_id-only CLI.
 *
 * Requires:
 *   1) python3 scripts/cli_browser_qa_server.py  (mocked SSH, seeded vault)
 *   2) npm install in tests/browser (playwright)
 *
 * Run:
 *   node tests/browser/cli_credential_id.spec.mjs
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const SECRET = 'browser-qa-vault-secret-never-in-dom';
const URL = `${BASE}/cli_terminal`;

const failures = [];
function check(name, cond, detail = '') {
  if (cond) {
    console.log(`PASS  ${name}`);
  } else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

async function waitWsOk(page, timeout = 20000) {
  await page.waitForFunction(() => {
    const el = document.getElementById('wsStatus');
    return el && /OK/i.test(el.textContent || '');
  }, null, { timeout });
}

async function collectConsole(page) {
  const lines = [];
  page.on('console', (msg) => lines.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', (err) => lines.push({ type: 'pageerror', text: String(err) }));
  return lines;
}

async function assertNoSecretAnywhere(page, label) {
  const html = await page.content();
  check(`${label}: no secret in HTML`, !html.includes(SECRET));
  const url = page.url();
  check(`${label}: no secret in URL`, !url.includes(SECRET));
  const storage = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
  }));
  const storageBlob = JSON.stringify(storage);
  check(`${label}: no secret in browser storage`, !storageBlob.includes(SECRET));
  const attrs = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('*').forEach((el) => {
      for (const a of el.attributes || []) {
        if (/pass|secret|token|cred/i.test(a.name) || /pass|secret/i.test(a.value || '')) {
          out.push(`${a.name}=${a.value}`);
        }
      }
    });
    return out;
  });
  check(
    `${label}: no secret in DOM attributes`,
    !attrs.some((a) => a.includes(SECRET)),
    attrs.join('; '),
  );
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const consoleLines = await collectConsole(page);

  // Intercept Socket.IO polling / capture cli_connect via page hook
  await page.addInitScript(() => {
    window.__nstCliConnectPayloads = [];
    window.__nstOrigIo = null;
    const hook = () => {
      if (!window.io || window.__nstIoHooked) return;
      window.__nstIoHooked = true;
      const origIo = window.io;
      window.io = function (...args) {
        const socket = origIo.apply(this, args);
        const origEmit = socket.emit.bind(socket);
        socket.emit = function (event, ...rest) {
          if (event === 'cli_connect') {
            window.__nstCliConnectPayloads.push(rest[0] || {});
          }
          return origEmit(event, ...rest);
        };
        return socket;
      };
      Object.assign(window.io, origIo);
    };
    hook();
    document.addEventListener('DOMContentLoaded', hook);
    setInterval(hook, 50);
  });

  // 1–3 load page
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await waitWsOk(page);
  check('page loads /cli_terminal', page.url().includes('/cli_terminal'));

  const severe = consoleLines.filter(
    (l) => l.type === 'error' || l.type === 'pageerror',
  ).filter((l) => !/favicon/i.test(l.text));
  check('no severe console errors on load', severe.length === 0, JSON.stringify(severe));

  // Dialog is open when host empty? host may be empty — open via Connect
  const dialogVisible = await page.locator('#connectionDialog').evaluate(
    (el) => !el.classList.contains('hidden'),
  );
  if (!dialogVisible) {
    await page.locator('#connectBtn').click();
  }
  await page.waitForSelector('#connectionDialog:not(.hidden)', { timeout: 5000 });

  // 4–7 selector / no password / no compat
  check(
    'credential selector visible',
    await page.locator('#connCredentialSelect').isVisible(),
  );
  const passFields = await page.locator(
    'input[type="password"], #connPassword, #connEnablePassword',
  ).count();
  check('username/password secret fields absent', passFields === 0);
  // Username display field may exist — must not be type=password
  const userType = await page.locator('#connUsername').getAttribute('type');
  check('connUsername is not password type', userType !== 'password');
  const bodyText = await page.locator('body').innerText();
  check(
    'no plaintext compatibility warning/control',
    !/NST_CLI_PLAINTEXT_COMPAT|plaintext compatibility|compat mode/i.test(bodyText),
  );

  // Metadata-only list: options from API
  await page.waitForFunction(() => {
    const sel = document.getElementById('connCredentialSelect');
    return sel && sel.options.length > 1;
  }, null, { timeout: 10000 });
  const optionValues = await page.locator('#connCredentialSelect option').evaluateAll(
    (opts) => opts.map((o) => ({ value: o.value, text: o.textContent })),
  );
  check(
    'selector uses metadata (netops option present)',
    optionValues.some((o) => o.value === 'netops'),
  );
  const listJson = await page.evaluate(async () => {
    const r = await fetch('/api/credentials/list');
    return r.json();
  });
  const listBlob = JSON.stringify(listJson);
  const row0 = listJson.credentials?.[0] || {};
  const secretKeys = Object.keys(row0).filter((k) =>
    /^(password|enable_password|enable_pwd|become_password|private_key|token)$/i.test(k),
  );
  check('credentials list has no password fields', secretKeys.length === 0 && !listBlob.includes(SECRET));

  async function openConnectDialog() {
    await page.evaluate(() => {
      const dlg = document.getElementById('connectionDialog');
      if (dlg) dlg.classList.remove('hidden');
      const err = document.getElementById('errorMessage');
      if (err) err.classList.add('hidden');
    });
    await page.waitForSelector('#connectionDialog:not(.hidden)', { timeout: 5000 });
  }

  async function hideConnectDialog() {
    await page.evaluate(() => {
      const dlg = document.getElementById('connectionDialog');
      if (dlg) dlg.classList.add('hidden');
    });
  }

  // 14 missing credential_id
  await openConnectDialog();
  await page.fill('#connHost', '10.0.0.1');
  await page.fill('#connCredentialId', '');
  await page.selectOption('#connCredentialSelect', '');
  await page.locator('.btn-primary', { hasText: 'Connect' }).click();
  await page.waitForSelector('#errorMessage:not(.hidden)', { timeout: 5000 });
  const missingMsg = await page.locator('#errorMessage').innerText();
  check(
    'missing credential_id shows understandable error',
    /credential_id required/i.test(missingMsg),
  );
  check('error message has no secret', !missingMsg.includes(SECRET));

  // 15 invalid credential
  await openConnectDialog();
  await page.fill('#connHost', '10.0.0.1');
  await page.fill('#connCredentialId', 'ghost-missing');
  await page.locator('.btn-primary', { hasText: 'Connect' }).click();
  await page.waitForFunction(() => {
    const t = document.getElementById('statusText')?.textContent || '';
    const e = document.getElementById('errorMessage');
    const et = e && !e.classList.contains('hidden') ? e.textContent : '';
    return /fail|unavailable|credential/i.test(t + et);
  }, null, { timeout: 15000 });
  const invErr = await page.locator('#errorMessage').innerText().catch(() => '');
  const statusAfterInv = await page.locator('#statusText').innerText();
  check(
    'invalid credential fails safely',
    /unavailable|credential|fail/i.test(invErr + statusAfterInv),
  );
  check('invalid-cred error has no secret', !(invErr + statusAfterInv).includes(SECRET));

  // Re-open dialog for happy path
  await openConnectDialog();

  // 8–13 select credential, connect, payload
  await page.selectOption('#connCredentialSelect', 'netops');
  await page.fill('#connHost', '10.0.0.1');
  await page.fill('#connPort', '22');
  await page.selectOption('#connDeviceType', 'cisco_ios');

  await page.evaluate(() => { window.__nstCliConnectPayloads = []; });
  await page.locator('.btn-primary', { hasText: 'Connect' }).click();

  await page.waitForFunction(
    () => (window.__nstCliConnectPayloads || []).length > 0,
    null,
    { timeout: 10000 },
  );
  const payloads = await page.evaluate(() => window.__nstCliConnectPayloads);
  const last = payloads[payloads.length - 1] || {};
  check('Socket.IO connect payload has credential_id', last.credential_id === 'netops');
  check(
    'connect payload has no username/password secret fields',
    !('password' in last) && !('enable_password' in last) && !('enable_pwd' in last),
  );
  // username may be present as display — must not be secret
  check('connect payload does not contain vault secret', !JSON.stringify(last).includes(SECRET));

  await page.waitForFunction(() => {
    const t = document.getElementById('statusText')?.textContent || '';
    return /Connected|Connecting|fail/i.test(t);
  }, null, { timeout: 15000 });
  const status = await page.locator('#statusText').innerText();
  check(
    'UI shows connection/loading/result state',
    /Connected to MOCK-SW1|Connected to 10\.0\.0\.1|Connecting|Connected/i.test(status),
  );

  // Wait for connected if connecting
  if (/Connecting/i.test(status)) {
    await page.waitForFunction(
      () => /Connected/i.test(document.getElementById('statusText')?.textContent || ''),
      null,
      { timeout: 15000 },
    ).catch(() => {});
  }
  const finalStatus = await page.locator('#statusText').innerText();
  check('UI reaches connected (mocked SSH)', /Connected/i.test(finalStatus));

  await assertNoSecretAnywhere(page, 'after connect');

  // 17 refresh does not restore secret
  await page.reload({ waitUntil: 'domcontentloaded' });
  await waitWsOk(page);
  await assertNoSecretAnywhere(page, 'after refresh');
  const afterReloadHtml = await page.content();
  check('refresh HTML has no password inputs', !/type=["']password["']/i.test(afterReloadHtml));

  // 18 disconnect/reconnect does not inherit another session credential via payload
  await openConnectDialog();
  await page.selectOption('#connCredentialSelect', 'netops');
  await page.fill('#connHost', '10.0.0.2');
  await page.evaluate(() => { window.__nstCliConnectPayloads = []; });
  await page.locator('.btn-primary', { hasText: 'Connect' }).click();
  await page.waitForFunction(
    () => (window.__nstCliConnectPayloads || []).length > 0,
    null,
    { timeout: 10000 },
  );
  const p2 = await page.evaluate(() => window.__nstCliConnectPayloads[0]);
  check('reconnect emit uses explicit credential_id only', p2.credential_id === 'netops');
  check('reconnect emit has no password', !('password' in p2));
  // Disconnect
  await hideConnectDialog();
  const discEnabled = await page.locator('#disconnectBtn').isEnabled().catch(() => false);
  if (discEnabled) {
    await page.locator('#disconnectBtn').click();
  }
  await page.waitForTimeout(300);
  // New connect without selecting should fail client-side if cleared — clear fields
  await openConnectDialog();
  await page.fill('#connCredentialId', '');
  await page.selectOption('#connCredentialSelect', '');
  await page.fill('#connHost', '10.0.0.3');
  await page.locator('.btn-primary', { hasText: 'Connect' }).click();
  const err2 = await page.locator('#errorMessage').innerText();
  check(
    'after disconnect, connect without credential_id does not inherit prior auth',
    /credential_id required/i.test(err2),
  );

  // 19 keyboard navigation
  await page.locator('#connCredentialSelect').focus();
  await page.keyboard.press('Alt+ArrowDown').catch(() => {});
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter').catch(() => {});
  const focusedTag = await page.evaluate(() => document.activeElement?.id || document.activeElement?.tagName);
  check('keyboard can focus credential selector', focusedTag === 'connCredentialSelect' || focusedTag === 'SELECT');

  await page.locator('.btn-primary', { hasText: 'Connect' }).focus();
  const focusOutline = await page.locator('.btn-primary', { hasText: 'Connect' }).evaluate((el) => {
    const s = getComputedStyle(el);
    return {
      outline: s.outlineStyle,
      outlineWidth: s.outlineWidth,
      boxShadow: s.boxShadow,
      borderColor: s.borderColor,
    };
  });
  // 20 accessible names + focus
  const connectName = await page.locator('#connectBtn').evaluate(
    (el) => el.getAttribute('aria-label') || el.textContent.trim(),
  );
  const selectName = await page.locator('#connCredentialSelect').evaluate(
    (el) => el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.labels?.[0]?.textContent || '',
  );
  check('Connect control has accessible name', !!connectName && /connect/i.test(connectName));
  check(
    'credential selector has accessible name',
    /credential|stored/i.test(selectName) || selectName.length > 0,
  );

  // Focus-visible check: ensure CSS provides a visible focus cue on primary dialog Connect
  await page.locator('.btn-primary', { hasText: 'Connect' }).focus();
  const hasFocusCue = await page.evaluate(() => {
    const el = document.querySelector('.dialog-buttons .btn-primary');
    if (!el) return false;
    el.focus();
    const s = getComputedStyle(el);
    const outlineOk = s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0;
    const shadowOk = s.boxShadow && s.boxShadow !== 'none';
    const borderOk = s.borderColor && s.borderColor !== 'rgba(0, 0, 0, 0)';
    return outlineOk || shadowOk || borderOk;
  });
  check('primary Connect has visible focus state', hasFocusCue, JSON.stringify(focusOutline));

  const consoleSecret = consoleLines.some((l) => (l.text || '').includes(SECRET));
  check('console output has no vault secret', !consoleSecret);

  await browser.close();

  if (failures.length) {
    console.error(`\n${failures.length} failure(s): ${failures.join(', ')}`);
    process.exit(1);
  }
  console.log('\nAll browser credential_id scenarios passed.');
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
