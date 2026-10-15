/**
 * file:// generated map HTML — overlay toggle, honesty copy, Discovery viewer.
 *
 * Env:
 *   NST_STD_L2_HTML   Standard L2 HTML with replay overlay bound
 *   NST_DISC_HTML     Discovery Command Center HTML with overlay bound
 *
 * Not live-vendor. Not EXE E2E.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { startTrace, stopTrace, shot } from './_qa_trace.mjs';

const failures = [];
function check(name, cond, detail = '') {
  if (cond) {
    console.log(`PASS  ${name}`);
  } else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

function fileUrl(p) {
  return pathToFileURL(path.resolve(p)).href;
}

function colorBlob(c) {
  if (c == null) return '';
  if (typeof c === 'string') return c.toLowerCase();
  return JSON.stringify(c).toLowerCase();
}

async function main() {
  const std = (process.env.NST_STD_L2_HTML || '').trim();
  const disc = (process.env.NST_DISC_HTML || '').trim();
  if (!std || !fs.existsSync(std)) {
    console.error('FAIL: NST_STD_L2_HTML missing or not a file');
    process.exit(2);
  }
  if (!disc || !fs.existsSync(disc)) {
    console.error('FAIL: NST_DISC_HTML missing or not a file');
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await startTrace(context);
  const page = await context.newPage();

  await page.goto(fileUrl(std), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForFunction(() => typeof vis !== 'undefined', null, { timeout: 20000 });
  await page.waitForTimeout(800);

  const stdHtml = await page.content();
  check('Standard L2 HTML has no vault secret field', !/browser-qa-vault-secret/i.test(stdHtml));
  check(
    'overlay checkbox present',
    await page.locator('#nst-util-overlay-on').count() === 1,
  );

  const overlayReady = await page.evaluate(() => {
    const cb = document.getElementById('nst-util-overlay-on');
    const p = typeof nstUtilPayload === 'function' ? nstUtilPayload() : {};
    return { disabled: !!(cb && cb.disabled), available: !!p.available, ok: !!p.ok };
  });
  check('replay overlay available on Standard L2', overlayReady.available && overlayReady.ok, JSON.stringify(overlayReady));
  check('overlay checkbox enabled when document present', overlayReady.disabled === false);

  await page.locator('#nst-util-overlay-on').check();
  await page.waitForTimeout(300);
  const banner = await page.locator('#nst-util-banner').innerText();
  check('overlay on: banner visible', banner.length > 0, banner);
  check('overlay on: replay not a live poll', /replay/i.test(banner) && /not a live poll/i.test(banner), banner);
  check('overlay on: not topology claim', /not topology/i.test(banner) || /existing L2/i.test(banner), banner);
  check('gray dashed copy present', /not down/i.test(banner) || await page.locator('#nst-util-legend').isVisible());

  const liveBtn = page.locator('#nst-util-live-btn');
  check('file:// Live SSH button stays disabled', await liveBtn.isDisabled());
  const liveTitle = (await liveBtn.getAttribute('title')) || '';
  check('file:// Live SSH title mentions file:// or operator console', /file:|operator console/i.test(liveTitle), liveTitle);
  check('file:// Live SSH title says not SNMP', /not snmp/i.test(liveTitle), liveTitle);

  const unmapped = await page.locator('#nst-util-unmapped').innerText().catch(() => '');
  check('unmapped table lists leftover interfaces, not new cables', /mgmt0|unmapped/i.test(unmapped), unmapped.slice(0, 200));

  await shot(page, 'standard_l2_overlay_on');

  await page.goto(fileUrl(disc), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForFunction(() => typeof vis !== 'undefined' && window.edges, null, { timeout: 20000 });
  await page.waitForTimeout(800);

  const discLive = await page.evaluate(() => {
    const btn = document.getElementById('nst-util-live-btn');
    const p = typeof nstUtilPayload === 'function' ? nstUtilPayload() : {};
    return {
      host: p.host || '',
      live_controls: p.live_controls,
      hasBtn: !!btn,
      disabled: !btn || btn.disabled,
      title: btn ? btn.title : '',
    };
  });
  check('Discovery overlay host is discovery', discLive.host === 'discovery', JSON.stringify(discLive));
  check(
    'Discovery does not offer Live SSH start (no button or disabled viewer)',
    discLive.hasBtn === false || discLive.disabled === true,
    JSON.stringify(discLive),
  );
  if (discLive.hasBtn) {
    check(
      'Discovery live title: viewer / not SNMP',
      /viewer|standard l2 only|not snmp/i.test(discLive.title),
      discLive.title,
    );
  } else {
    check('Discovery omits Live SSH button (viewer host)', true);
  }

  const evpnBefore = await page.evaluate(() => {
    const out = [];
    if (!window.edges) return out;
    window.edges.forEach((e) => {
      const proto = String(e.protocol || (e.edge_data && e.edge_data.protocol) || '').toUpperCase();
      const np = !!(e.not_physical || (e.edge_data && e.edge_data.not_physical));
      if (proto === 'EVPN' || np) {
        out.push({ id: e.id, proto, np, color: e.color });
      }
    });
    return out;
  });
  check('Discovery map has EVPN/non-cable vis edges', evpnBefore.length >= 1, JSON.stringify(evpnBefore));

  const cb = page.locator('#nst-util-overlay-on');
  if (await cb.count()) {
    await cb.check({ force: true });
    await page.waitForTimeout(400);
  }

  const evpnAfter = await page.evaluate(() => {
    const out = [];
    if (!window.edges) return out;
    window.edges.forEach((e) => {
      const proto = String(e.protocol || (e.edge_data && e.edge_data.protocol) || '').toUpperCase();
      const np = !!(e.not_physical || (e.edge_data && e.edge_data.not_physical));
      if (proto === 'EVPN' || np) {
        out.push({ id: e.id, proto, np, color: e.color });
      }
    });
    return out;
  });
  const evpnGrayed = evpnAfter.some((e) => {
    const blob = colorBlob(e.color);
    return blob.includes('#64748b') || blob.includes('slate');
  });
  const evpnKeepsPurple = evpnAfter.some((e) => {
    const blob = colorBlob(e.color);
    return blob.includes('#a855f7') || blob.includes('a855f7') || blob.includes('#a55eea');
  });
  check(
    'Discovery overlay-on does not gray EVPN as unsampled cable',
    !evpnGrayed && evpnKeepsPurple,
    JSON.stringify({ before: evpnBefore, after: evpnAfter }),
  );

  const stpAfter = await page.evaluate(() => {
    const out = [];
    if (!window.edges) return out;
    window.edges.forEach((e) => {
      const proto = String(e.protocol || (e.edge_data && e.edge_data.protocol) || '').toUpperCase();
      const lt = String(e.link_type || e.type || '').toLowerCase();
      if (proto === 'STP' || lt.indexOf('stp') >= 0) {
        out.push({ id: e.id, proto, lt, color: e.color });
      }
    });
    return out;
  });
  const stpGrayed = stpAfter.some((e) => colorBlob(e.color).includes('#64748b'));
  check(
    'Discovery overlay-on does not gray STP-blocked as unsampled cable',
    stpAfter.length === 0 || !stpGrayed,
    JSON.stringify(stpAfter),
  );

  await shot(page, 'discovery_overlay_on');
  await stopTrace(context, 'offline_map_html');
  await browser.close();

  if (failures.length) {
    console.error(`\n${failures.length} failure(s): ${failures.join(', ')}`);
    process.exit(1);
  }
  console.log('\nAll offline map HTML overlay scenarios passed.');
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
