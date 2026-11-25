import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const puppeteer = require('../frontend/node_modules/puppeteer-core');

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const outDir = path.resolve('docs/screenshots');
const artifactDir = path.resolve(
  'C:\\Users\\pothu\\.gemini\\antigravity\\brain\\3188d654-1f27-408a-880d-a38c62593b11'
);

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900, isMobile: false },
  { name: 'tablet', width: 768, height: 1024, isMobile: false },
  { name: 'mobile', width: 390, height: 844, isMobile: true },
];

async function run() {
  console.log('Starting Phase 7 live browser verification across Desktop, Tablet, and Mobile...');
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  const failedRequests = [];
  const findings = [];

  page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(`console.error: ${msg.text()}`);
    }
  });
  page.on('response', (res) => {
    if (res.status() >= 400 && !res.url().includes('favicon')) {
      failedRequests.push(`${res.status()} ${res.url()}`);
    }
  });

  async function saveShot(filename) {
    const localPath = path.join(outDir, filename);
    await page.screenshot({ path: localPath, fullPage: false });
    if (fs.existsSync(artifactDir)) {
      fs.copyFileSync(localPath, path.join(artifactDir, filename));
    }
  }

  async function checkOverflow(label) {
    const metrics = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    if (metrics.scrollWidth > metrics.innerWidth + 2) {
      throw new Error(
        `Horizontal overflow detected at ${label}: scrollWidth=${metrics.scrollWidth} > innerWidth=${metrics.innerWidth}`
      );
    }
    findings.push(`${label}: overflow OK (${metrics.scrollWidth}/${metrics.innerWidth})`);
  }

  async function waitForText(txt) {
    await page.waitForFunction(
      (t) =>
        document.body &&
        document.body.innerText.toUpperCase().includes(String(t).toUpperCase()),
      { timeout: 10000 },
      txt
    );
  }

  // 1. Login as Admin
  await page.setViewport(VIEWPORTS[0]);
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const adminPreset = buttons.find((b) => b.textContent && b.textContent.includes('ADM-2026-001'));
    if (adminPreset) adminPreset.click();
  });
  await new Promise((r) => setTimeout(r, 200));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const submit = buttons.find(
      (b) => b.textContent && (b.textContent.includes('Authenticate & Continue') || b.textContent.includes('Sign In'))
    );
    if (submit) submit.click();
  });

  await page.waitForFunction(() => window.location.pathname === '/admin', { timeout: 10000 });
  await waitForText('MCPI Priority Distribution');
  await waitForText('Operational Workload Balance');
  await waitForText('Open Queue Aging');
  await new Promise((r) => setTimeout(r, 300));

  // Verify Overview, All Requests, Drawer, Reports across Desktop, Tablet, Mobile
  for (const vp of VIEWPORTS) {
    await page.setViewport({ width: vp.width, height: vp.height, isMobile: vp.isMobile });

    // Overview
    await page.goto('http://127.0.0.1:5173/admin', { waitUntil: 'networkidle0' });
    await waitForText('MCPI Priority Distribution');
    await new Promise((r) => setTimeout(r, 300));
    await checkOverflow(`overview-${vp.name}`);
    await saveShot(`fipp_phase7_overview_${vp.name}.png`);

    // All Requests + Drawer
    await page.goto('http://127.0.0.1:5173/admin/all-requests', { waitUntil: 'networkidle0' });
    await waitForText('CMP-2026-');
    await new Promise((r) => setTimeout(r, 300));
    await checkOverflow(`all-requests-${vp.name}`);
    if (vp.name === 'desktop') {
      await saveShot('fipp_phase7_all_requests_desktop.png');
    }

    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const inspectBtn = buttons.find((b) => b.textContent && b.textContent.includes('Inspect'));
      if (inspectBtn) inspectBtn.click();
    });
    await waitForText('Rule-Based Scoring (Non-ML)');
    await waitForText('SHAP Feature Attribution Unavailable');
    await new Promise((r) => setTimeout(r, 300));
    const drawerText = await page.evaluate(() => document.body.innerText);
    if (!drawerText.includes('pts')) {
      throw new Error(`Drawer at ${vp.name} did not render MCPI points!`);
    }
    await checkOverflow(`drawer-${vp.name}`);
    await saveShot(`fipp_phase7_drawer_${vp.name}.png`);

    // Reports
    await page.goto('http://127.0.0.1:5173/admin/reports', { waitUntil: 'networkidle0' });
    await waitForText('Assignment & Workload Distribution');
    await waitForText('Predictive Intelligence & Model Status');
    await new Promise((r) => setTimeout(r, 300));
    await checkOverflow(`reports-${vp.name}`);
    await saveShot(`fipp_phase7_reports_${vp.name}.png`);
  }

  // Verify remaining 3 admin queue routes on Desktop
  await page.setViewport(VIEWPORTS[0]);
  for (const route of [
    { path: '/admin/unassigned', text: 'New / Unassigned Requests' },
    { path: '/admin/in-progress', text: 'In Progress Work Orders' },
    { path: '/admin/resolved', text: 'Resolved Complaint Archive' },
  ]) {
    await page.goto(`http://127.0.0.1:5173${route.path}`, { waitUntil: 'networkidle0' });
    await waitForText(route.text);
    await checkOverflow(route.path);
  }

  // Sign out and verify Student Portal has zero MCPI / SHAP / Admin analytics exposure
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const signOutBtn = buttons.find((b) => b.textContent && b.textContent.includes('Sign Out'));
    if (signOutBtn) signOutBtn.click();
  });
  await new Promise((r) => setTimeout(r, 300));

  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const stuPreset = buttons.find((b) => b.textContent && b.textContent.includes('STU-2026-001'));
    if (stuPreset) stuPreset.click();
  });
  await new Promise((r) => setTimeout(r, 200));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const submit = buttons.find(
      (b) => b.textContent && (b.textContent.includes('Authenticate & Continue') || b.textContent.includes('Sign In'))
    );
    if (submit) submit.click();
  });
  await page.waitForFunction(() => window.location.pathname.startsWith('/student'), { timeout: 10000 });
  await page.goto('http://127.0.0.1:5173/student/history', { waitUntil: 'networkidle0' });
  await waitForText('Complaint History');
  const stuText = await page.evaluate(() => document.body.innerText);
  if (stuText.includes('MCPI') || stuText.includes('SHAP')) {
    throw new Error('Student Portal unexpectedly exposed MCPI or SHAP text!');
  }

  await browser.close();

  console.log('Verification Checks:', findings.length);
  if (consoleErrors.length > 0 || failedRequests.length > 0) {
    console.error('Browser verification errors:', { consoleErrors, failedRequests });
    process.exit(1);
  }
  console.log('Phase 7 Browser E2E Verification PASSED (0 console errors, 0 failed requests, 0 overflow).');
}

run().catch((err) => {
  console.error('Fatal error during Phase 7 browser verification:', err);
  process.exit(1);
});
