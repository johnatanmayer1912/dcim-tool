/**
 * Enterprise accessibility sweep — operator console + offline map HTML.
 * Uses @axe-core/playwright. Requires Flask on loopback or file:// map paths.
 *
 * Env:
 *   NST_BROWSER_BASE     default http://127.0.0.1:5051
 *   NST_REVIEW_DIR       writes JSON + screenshots under accessibility/
 *   NST_STD_L2_HTML      optional Standard L2 map for file:// axe
 *   NST_DISC_HTML        optional Discovery map for file:// axe
 *   NST_A11Y_PHASE       before | after (default after)
 */
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const REVIEW = (process.env.NST_REVIEW_DIR || '').trim();
const PHASE = (process.env.NST_A11Y_PHASE || 'after').trim();

const WORKSPACES = [
  { id: 'inventory', nav: '#ws-nav-inventory', wait: '#ws-inventory.is-active' },
  { id: 'maps', nav: '#ws-nav-maps', wait: '#ws-maps.is-active', after: () => switchTab('tools') },
  { id: 'maps_discovery', nav: '#ws-nav-maps', wait: '#ws-maps.is-active', after: () => switchTab('discovery') },
  { id: 'find', nav: '#ws-nav-find', wait: '#ws-find.is-active' },
  { id: 'change', nav: '#ws-nav-change', wait: '#ws-change.is-active' },
  { id: 'evidence', nav: '#ws-nav-evidence', wait: '#ws-evidence.is-active' },
  { id: 'settings', nav: '#ws-nav-settings', wait: '#ws-settings.is-active' },
];

function outDir(...parts) {
  if (!REVIEW) return null;
  const dir = path.join(REVIEW, ...parts);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function switchTab(tabId) {
  const seg = document.getElementById('tab-segment-' + tabId);
  if (seg && typeof switchTab === 'function') switchTab(tabId, seg);
}

function summarize(results) {
  const violations = results.violations || [];
  const incomplete = results.incomplete || [];
  return {
    url: results.url,
    violationCount: violations.length,
    incompleteCount: incomplete.length,
    violations: violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      description: v.description,
      help: v.help,
      nodes: (v.nodes || []).length,
      targets: (v.nodes || []).slice(0, 5).map((n) => n.target),
    })),
    incomplete: incomplete.map((i) => ({
      id: i.id,
      impact: i.impact,
      description: i.description,
      nodes: (i.nodes || []).length,
    })),
  };
}

async function runAxe(page, label) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
    .analyze();
  const summary = summarize(results);
  summary.label = label;
  const dir = outDir('accessibility', PHASE);
  if (dir) {
    fs.writeFileSync(path.join(dir, `${label}.json`), JSON.stringify(summary, null, 2));
    const shotDir = outDir('screenshots', PHASE);
    if (shotDir) {
      await page.screenshot({ path: path.join(shotDir, `${label}.png`), fullPage: true });
    }
  }
  return summary;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await context.addInitScript(() => {
    localStorage.setItem('nst_health_ok', '1');
  });
  const page = await context.newPage();
  const all = [];

  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForSelector('#nst-main', { timeout: 15000 });

  for (const ws of WORKSPACES) {
    await page.locator(ws.nav).click();
    await page.waitForSelector(ws.wait, { timeout: 10000 });
    if (ws.after) {
      await page.evaluate(ws.after);
      await page.waitForTimeout(400);
    }
    all.push(await runAxe(page, ws.id));
  }

  const std = (process.env.NST_STD_L2_HTML || '').trim();
  const disc = (process.env.NST_DISC_HTML || '').trim();
  if (std && fs.existsSync(std)) {
    await page.goto(pathToFileURL(path.resolve(std)).href, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(800);
    all.push(await runAxe(page, 'map_standard_l2'));
  }
  if (disc && fs.existsSync(disc)) {
    await page.goto(pathToFileURL(path.resolve(disc)).href, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(800);
    all.push(await runAxe(page, 'map_discovery'));
  }

  await browser.close();

  const totalViolations = all.reduce((n, r) => n + r.violationCount, 0);
  const report = {
    phase: PHASE,
    timestamp: new Date().toISOString(),
    pages: all.length,
    totalViolations,
    results: all,
  };
  const dir = outDir('accessibility');
  if (dir) {
    fs.writeFileSync(path.join(dir, `${PHASE}_sweep_summary.json`), JSON.stringify(report, null, 2));
  }

  console.log(`a11y sweep (${PHASE}): ${all.length} pages, ${totalViolations} total violations`);
  for (const r of all) {
    const flag = r.violationCount ? 'VIOL' : 'PASS';
    console.log(`  ${flag}  ${r.label}: ${r.violationCount} violations, ${r.incompleteCount} incomplete`);
    for (const v of r.violations) {
      console.log(`        - [${v.impact}] ${v.id} (${v.nodes} nodes): ${v.help}`);
    }
  }

  if (totalViolations > 0 && PHASE === 'after') {
    const critical = all.reduce((n, r) => n + (r.violations || []).filter((v) => v.impact === 'critical').length, 0);
    if (critical > 0) process.exit(1);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(2);
});
