/**
 * Optional Playwright tracing / screenshots when NST_REVIEW_DIR is set.
 */
import fs from 'node:fs';
import path from 'node:path';

export function reviewDir() {
  return (process.env.NST_REVIEW_DIR || '').trim();
}

export async function startTrace(context) {
  const root = reviewDir();
  if (!root) return;
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
}

export async function stopTrace(context, name) {
  const root = reviewDir();
  if (!root) return;
  const dir = path.join(root, 'playwright', 'traces');
  fs.mkdirSync(dir, { recursive: true });
  await context.tracing.stop({ path: path.join(dir, `${name}.zip`) });
}

export async function shot(page, name) {
  const root = reviewDir();
  if (!root) return;
  const dir = path.join(root, 'playwright', 'screenshots');
  fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: path.join(dir, `${name}.png`), fullPage: true });
}
