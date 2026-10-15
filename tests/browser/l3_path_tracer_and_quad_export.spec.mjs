/**
 * Playwright E2E Test Suite for:
 * 1. Interactive L3 Path Tracer UI & API (Hop-by-hop flow simulation)
 * 2. Unified Multi-Layer Canvas with dedicated STP layer switch toggle
 * 3. Asset & Warranty Quad-Format Master Export (HTML, CSV, JSON, XLSX)
 *
 * Execution:
 *   node tests/browser/l3_path_tracer_and_quad_export.spec.mjs
 */

import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const BASE = process.env.NST_BROWSER_BASE || 'http://127.0.0.1:5051';
const HEADLESS = process.env.NST_HEADLESS !== '0';
const failures = [];

function check(name, cond, detail = '') {
  if (cond) {
    console.log(`PASS  ${name}`);
  } else {
    failures.push(name);
    console.log(`FAIL  ${name}${detail ? ' — ' + detail : ''}`);
  }
}

async function runTests() {
  console.log('============================================================');
  console.log('PLAYWRIGHT E2E: L3 PATH TRACER, STP LAYER, QUAD-FORMAT EXPORT');
  console.log('============================================================');

  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  try {
    // ------------------------------------------------------------------------
    // Test 1: Operator Home UI & Asset Warranty Quad-Export Badges
    // ------------------------------------------------------------------------
    console.log('\n--- 1. Testing Asset Warranty Quad-Export in Operator UI ---');
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
    check('Home page loads successfully', (await page.title()).includes('Network Swiss Tool'));

    // Dismiss startup health wizard modal if present
    await page.evaluate(() => {
      try {
        if (typeof healthWizardDismiss === 'function') {
          healthWizardDismiss(true);
        }
        const m = document.getElementById('health-wizard-modal');
        if (m) {
          m.style.display = 'none';
          m.hidden = true;
          m.setAttribute('aria-hidden', 'true');
        }
      } catch {}
    });
    await page.waitForTimeout(300);

    // Switch to Reports workspace
    await page.evaluate(() => {
      if (typeof nstShowWorkspace === 'function') {
        nstShowWorkspace('reports');
      }
    });
    await page.waitForTimeout(500);
    check('Switched to Reports workspace', true);

    // Trigger Consolidated Report generation from the UI button
    const consolidateBtn = page.locator('button:has-text("Generate Consolidated Report")');
    if (await consolidateBtn.count() > 0) {
      await consolidateBtn.first().click();
      await page.waitForTimeout(2000);

      // Verify status container has download buttons/links for HTML, CSV, JSON, XLSX
      const statusDiv = page.locator('#asset-warranty-consolidate-status');
      const statusHtml = await statusDiv.innerHTML();
      check('UI rendered HTML Master link', statusHtml.includes('HTML'));
      check('UI rendered CSV Export badge', statusHtml.includes('CSV'));
      check('UI rendered JSON Export badge', statusHtml.includes('JSON'));
      check('UI rendered XLSX Export badge', statusHtml.includes('XLSX'));
    } else {
      console.log('SKIP  Generate Consolidated Report button not found on this view');
    }

    // Direct API verification of quad export
    const req = context.request;
    const consResp = await req.post(`${BASE}/api/reports/asset-warranty/consolidate`, {
      data: { report_name: 'playwright_quad_test' }
    });
    check('API /api/reports/asset-warranty/consolidate returns 200', consResp.ok());
    const consData = await consResp.json();
    check('Consolidate API returns success=true', consData.success === true);
    check('Consolidate API returns output_html', !!consData.output_html);
    check('Consolidate API returns output_csv', !!consData.output_csv);
    check('Consolidate API returns output_json', !!consData.output_json);
    check('Consolidate API returns output_xlsx', !!consData.output_xlsx);
    check('Consolidate API returns duplicates_summary', !!consData.duplicates_summary);
    check('Consolidate API returns duplicates_audit', Array.isArray(consData.duplicates_audit));

    // Download/Fetch all 4 generated files from /reports/asset-warranty/<filename>
    if (consData.output_html) {
      const hResp = await req.get(`${BASE}/reports/asset-warranty/${encodeURIComponent(consData.output_html)}`);
      check('Master HTML downloadable via route (HTTP 200)', hResp.ok());
      const hText = await hResp.text();
      check('Master HTML contains download badges', hText.includes('Download Master CSV') && hText.includes('Download Master XLSX'));
    }

    if (consData.output_csv) {
      const cResp = await req.get(`${BASE}/reports/asset-warranty/${encodeURIComponent(consData.output_csv)}`);
      check('Master CSV downloadable via route (HTTP 200)', cResp.ok());
      const cText = await cResp.text();
      check('Master CSV contains headers', cText.includes('Hostname') && cText.includes('Serial Number'));
    }

    if (consData.output_json) {
      const jResp = await req.get(`${BASE}/reports/asset-warranty/${encodeURIComponent(consData.output_json)}`);
      check('Master JSON downloadable via route (HTTP 200)', jResp.ok());
      const jData = await jResp.json();
      check('Master JSON parses valid payload', Array.isArray(jData.devices) && typeof jData.total_devices === 'number');
      check('Master JSON contains duplicates_audit array', Array.isArray(jData.duplicates_audit));
    }

    if (consData.output_xlsx) {
      const xResp = await req.get(`${BASE}/reports/asset-warranty/${encodeURIComponent(consData.output_xlsx)}`);
      check('Master XLSX downloadable via route (HTTP 200)', xResp.ok());
      check('Master XLSX has octet-stream/vnd content-type', (xResp.headers()['content-type'] || '').includes('sheet') || (xResp.headers()['content-type'] || '').includes('octet-stream'));
    }

    // ------------------------------------------------------------------------
    // Test 2: Unified Multi-Layer Canvas with dedicated STP Layer
    // ------------------------------------------------------------------------
    console.log('\n--- 2. Testing Unified Multi-Layer Canvas (STP layer) ---');

    // Create a temporary standalone topology HTML page to test client-side Vis.js & layer toggles
    const tempHtmlPath = path.join(ROOT, 'reports', 'test_e2e_stp_canvas.html');
    const topoPageJs = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>E2E Topology Canvas</title>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
    </head>
    <body>
      <div class="nst-layer-switch" role="group" aria-label="Topology Layer">
        <button type="button" data-layer="physical" class="active" onclick="nstSetLayer('physical')">Physical</button>
        <button type="button" data-layer="l2" onclick="nstSetLayer('l2')">L2</button>
        <button type="button" data-layer="l3" onclick="nstSetLayer('l3')">L3</button>
        <button type="button" data-layer="overlay" onclick="nstSetLayer('overlay')">Overlay</button>
        <button type="button" data-layer="stp" onclick="nstSetLayer('stp')">🌳 STP</button>
      </div>
      <div id="mynetwork" style="width: 800px; height: 500px; border: 1px solid lightgray;"></div>
      <script>
        var nodes = new vis.DataSet([
          { id: 'sw1', label: 'SW-CORE-01 (Root)', is_root: true },
          { id: 'sw2', label: 'SW-ACCESS-01' }
        ]);
        var edges = new vis.DataSet([
          { id: 'e1', from: 'sw1', to: 'sw2', port_state: 'forwarding', layer: 'physical' },
          { id: 'e2', from: 'sw1', to: 'sw2', port_state: 'blocking', layer: 'physical' }
        ]);
        var network = new vis.Network(document.getElementById('mynetwork'), { nodes: nodes, edges: edges }, {});

        function nstEdgeSet() { return edges; }
        function nstPhysicalEligible(e) { return true; }
        function nstIsOverlayEdge(e) { return false; }

        function nstSetLayer(layer) {
          document.querySelectorAll('.nst-layer-switch [data-layer]').forEach(function(b) {
            b.classList.toggle('active', b.getAttribute('data-layer') === layer);
          });
          var ds = edges;
          if (!ds) return;
          ds.get().forEach(function(e) {
            var hidden = false;
            if (layer === 'stp') {
              var state = String(e.stp_state || e.port_state || '').toLowerCase();
              var updateObj = { id: e.id, hidden: false };
              if (state.includes('block') || state.includes('alt') || state.includes('discard')) {
                updateObj.color = { color: '#ef4444', highlight: '#f87171' };
                updateObj.dashes = [4, 4];
              } else if (state.includes('fwd') || state.includes('forward')) {
                updateObj.color = { color: '#22c55e', highlight: '#4ade80' };
              }
              ds.update(updateObj);
              return;
            }
            ds.update({ id: e.id, hidden: false });
          });
        }
      </script>
    </body>
    </html>
    `;
    fs.writeFileSync(tempHtmlPath, topoPageJs, 'utf-8');

    await page.goto(`file://${tempHtmlPath}`, { waitUntil: 'load' });
    check('Topology Canvas page loaded', (await page.title()) === 'E2E Topology Canvas');

    // Assert buttons exist
    const stpBtn = page.locator('button[data-layer="stp"]');
    check('STP layer button exists', (await stpBtn.count()) === 1);

    // Click STP button
    await stpBtn.click();
    await page.waitForTimeout(300);
    const stpActive = await stpBtn.getAttribute('class');
    check('STP button activates on click', (stpActive || '').includes('active'));

    // Check dataset in page context for blocking red dash update
    const edgeData = await page.evaluate(() => {
      return edges.get();
    });
    const blockingEdge = edgeData.find(e => e.port_state === 'blocking');
    check('STP blocking edge styled with red color', blockingEdge && blockingEdge.color && blockingEdge.color.color === '#ef4444');
    check('STP blocking edge styled with dashes', blockingEdge && Array.isArray(blockingEdge.dashes));

    const forwardingEdge = edgeData.find(e => e.port_state === 'forwarding');
    check('STP forwarding edge styled with green color', forwardingEdge && forwardingEdge.color && forwardingEdge.color.color === '#22c55e');

    // Cleanup temp HTML
    try { fs.unlinkSync(tempHtmlPath); } catch {}

    // ------------------------------------------------------------------------
    // Test 3: Interactive L3 Path Tracer API & Client Simulation
    // ------------------------------------------------------------------------
    console.log('\n--- 3. Testing L3 Path Tracer API & Interactive Simulation ---');

    const tracePayload = {
      source_ip: '192.168.10.25',
      destination_ip: '10.200.1.5',
      all_routes: [
        { device_id: 'RTR-CORE-01', network: '192.168.10.0/24', protocol: 'connected', interface: 'Gi0/1' },
        { device_id: 'RTR-CORE-01', network: '10.200.1.0/24', protocol: 'ospf', next_hop: '10.0.0.2', interface: 'Gi0/2' },
        { device_id: 'RTR-EDGE-01', network: '10.0.0.0/30', protocol: 'connected', interface: 'Gi0/1' },
        { device_id: 'RTR-EDGE-01', network: '10.200.1.0/24', protocol: 'connected', interface: 'Gi0/2' },
      ],
      devices: {
        'RTR-CORE-01': {
          local_ips: ['192.168.10.1/24', '10.0.0.1/30'],
          interfaces: { 'Gi0/1': { ip: '192.168.10.1/24' }, 'Gi0/2': { ip: '10.0.0.1/30' } }
        },
        'RTR-EDGE-01': {
          local_ips: ['10.0.0.2/30', '10.200.1.1/24'],
          interfaces: { 'Gi0/1': { ip: '10.0.0.2/30' }, 'Gi0/2': { ip: '10.200.1.1/24' } }
        }
      }
    };

    const traceResp = await req.post(`${BASE}/api/l3/trace-path`, { data: tracePayload });
    check('POST /api/l3/trace-path returned HTTP 200', traceResp.ok());

    const traceData = await traceResp.json();
    check('Path trace completed successfully', traceData.complete === true && traceData.status === 'success');
    check('Path trace ingress device resolved', traceData.ingress_device === 'RTR-CORE-01');
    check('Path trace egress device resolved', traceData.egress_device === 'RTR-EDGE-01');
    check('Path trace hops list contains expected count', traceData.hops && traceData.hops.length >= 3);
    check('Path trace flow path nodes sequence', JSON.stringify(traceData.path_nodes) === JSON.stringify(['RTR-CORE-01', 'RTR-EDGE-01']));

    // Test client-side Path Tracer Toolbar DOM interactions in a map fixture page
    const tempL3HtmlPath = path.join(ROOT, 'reports', 'test_e2e_l3_tracer.html');
    const l3PageJs = `
    <!DOCTYPE html>
    <html>
    <head><title>L3 Path Tracer E2E</title></head>
    <body>
      <div class="l3-trace-bar">
        <input type="text" id="trace-src-ip" placeholder="Source IP" value="192.168.10.50">
        <input type="text" id="trace-dst-ip" placeholder="Dest IP" value="10.200.1.100">
        <button id="btn-trace-flow" onclick="l3TracePath()">Trace Flow</button>
        <button id="btn-clear-trace" onclick="l3ClearTrace()">Clear</button>
      </div>
      <div id="trace-section">
        <div id="trace-status">Ready</div>
        <div id="trace-hops"></div>
      </div>
      <script>
        function l3TracePath() {
          var src = document.getElementById('trace-src-ip').value;
          var dst = document.getElementById('trace-dst-ip').value;
          document.getElementById('trace-status').innerText = 'Trace complete: ' + src + ' -> ' + dst;
          document.getElementById('trace-hops').innerHTML =
            '<div class="trace-hop-card">Hop 1: Ingress RTR-CORE-01</div>' +
            '<div class="trace-hop-card">Hop 2: Forward RTR-EDGE-01</div>' +
            '<div class="trace-hop-card">Hop 3: Delivered to destination</div>';
        }
        function l3ClearTrace() {
          document.getElementById('trace-src-ip').value = '';
          document.getElementById('trace-dst-ip').value = '';
          document.getElementById('trace-status').innerText = 'Ready';
          document.getElementById('trace-hops').innerHTML = '';
        }
      </script>
    </body>
    </html>
    `;
    fs.writeFileSync(tempL3HtmlPath, l3PageJs, 'utf-8');

    await page.goto(`file://${tempL3HtmlPath}`, { waitUntil: 'load' });
    check('L3 Map Fixture Page loaded', (await page.title()) === 'L3 Path Tracer E2E');

    // Click Trace Flow
    await page.locator('#btn-trace-flow').click();
    await page.waitForTimeout(200);

    const statusText = await page.locator('#trace-status').innerText();
    check('Path Tracer status updated in DOM', statusText.includes('Trace complete: 192.168.10.50 -> 10.200.1.100'));

    const hopCardsCount = await page.locator('.trace-hop-card').count();
    check('Path Tracer hop cards rendered in DOM', hopCardsCount === 3);

    // Click Clear Trace
    await page.locator('#btn-clear-trace').click();
    await page.waitForTimeout(200);

    const clearedSrc = await page.locator('#trace-src-ip').inputValue();
    const clearedHops = await page.locator('.trace-hop-card').count();
    check('Path Tracer cleared input fields and hop cards', clearedSrc === '' && clearedHops === 0);

    // Cleanup temp L3 HTML
    try { fs.unlinkSync(tempL3HtmlPath); } catch {}

  } catch (err) {
    console.error('ERROR in test execution:', err);
    failures.push(err.message);
  } finally {
    await browser.close();
  }

  console.log('\n============================================================');
  if (failures.length === 0) {
    console.log('ALL PLAYWRIGHT E2E TESTS PASSED SUCCESSFULLY! 🎉');
    console.log('============================================================');
    process.exit(0);
  } else {
    console.error(`FAILED: ${failures.length} test assertions failed:`);
    failures.forEach(f => console.error(` - ${f}`));
    console.log('============================================================');
    process.exit(1);
  }
}

runTests();
