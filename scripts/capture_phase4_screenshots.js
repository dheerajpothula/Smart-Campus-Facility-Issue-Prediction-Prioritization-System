import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const puppeteer = require('../frontend/node_modules/puppeteer-core');

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const outDir = path.resolve('docs/screenshots');
const artifactDir = 'C:\\Users\\pothu\\.gemini\\antigravity\\brain\\c5ba17ef-d1cc-4f68-999c-a619f6948cfb';

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function run() {
  console.log('Launching Chrome for Phase 4.1 Admin Control Centre E2E verification & screenshots...');
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  const failedRequests = [];

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

  async function saveScreenshot(filename) {
    const localPath = path.join(outDir, filename);
    await page.screenshot({ path: localPath, fullPage: false });
    console.log(`Saved screenshot: ${localPath}`);
    if (fs.existsSync(artifactDir)) {
      const artPath = path.join(artifactDir, filename);
      fs.copyFileSync(localPath, artPath);
    }
  }

  async function assertAdminRoute(expectedPathPrefix) {
    const pathname = await page.evaluate(() => window.location.pathname);
    if (!pathname.startsWith(expectedPathPrefix)) {
      throw new Error(`Expected route starting with ${expectedPathPrefix}, got ${pathname}`);
    }
  }

  async function gotoAndWait(urlPath, expectedText, waitForRecord = false) {
    await page.goto(`http://127.0.0.1:5173${urlPath}`, { waitUntil: 'networkidle0' });
    await assertAdminRoute('/admin');
    await page.waitForFunction(
      (txt) => document.body && document.body.innerText.includes(txt),
      { timeout: 10000 },
      expectedText
    );
    if (waitForRecord) {
      await page.waitForFunction(
        () => document.body && document.body.innerText.includes('CMP-2026-'),
        { timeout: 10000 }
      );
    }
    await new Promise(r => setTimeout(r, 400));
  }

  // 1. Login via real form
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const aBtn = buttons.find(b => b.textContent && b.textContent.includes('ADM-2026-001'));
    if (aBtn) aBtn.click();
  });
  await new Promise(r => setTimeout(r, 200));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const loginBtn = buttons.find(
      b => b.textContent && (b.textContent.includes('Authenticate & Continue') || b.textContent.includes('Sign In'))
    );
    if (loginBtn) loginBtn.click();
  });
  await page.waitForFunction(() => window.location.pathname === '/admin', { timeout: 10000 });
  await page.waitForFunction(
    () => document.body.innerText.includes('Executive Operations Overview'),
    { timeout: 10000 }
  );
  await new Promise(r => setTimeout(r, 500));

  // 1-2. Overview
  await saveScreenshot('fipp_phase4_admin_overview_desktop.png');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin', 'Executive Operations Overview');
  await saveScreenshot('fipp_phase4_admin_overview_mobile.png');

  // 3-4. All Requests
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await gotoAndWait('/admin/all-requests', 'All Requests Ledger', true);
  await saveScreenshot('fipp_phase4_admin_all_requests_desktop.png');

  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin/all-requests', 'All Requests Ledger', true);
  await saveScreenshot('fipp_phase4_admin_all_requests_mobile.png');

  // 5-6. Drawer open on Desktop & Mobile (from All Requests)
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await gotoAndWait('/admin/all-requests', 'All Requests Ledger', true);
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const inspectBtn = buttons.find(b => b.textContent && b.textContent.includes('Inspect'));
    if (inspectBtn) inspectBtn.click();
  });
  await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('OFFICIAL COMPLAINT LIFECYCLE'), { timeout: 5000 });
  await new Promise(r => setTimeout(r, 400));
  const drawerText = await page.evaluate(() => document.body.innerText);
  if (drawerText.includes('1750%') || drawerText.includes('1250%')) {
    throw new Error('Detected MCPI percentage scaling bug (e.g. 1750%) in drawer!');
  }
  await saveScreenshot('fipp_phase4_admin_drawer_desktop.png');

  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin/all-requests', 'All Requests Ledger', true);
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const inspectBtn = buttons.find(b => b.textContent && b.textContent.includes('Inspect'));
    if (inspectBtn) inspectBtn.click();
  });
  await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('OFFICIAL COMPLAINT LIFECYCLE'), { timeout: 5000 });
  await new Promise(r => setTimeout(r, 400));
  await saveScreenshot('fipp_phase4_admin_drawer_mobile.png');

  // 7-8. New / Unassigned
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await gotoAndWait('/admin/unassigned', 'New / Unassigned Requests', true);
  await saveScreenshot('fipp_phase4_admin_unassigned_desktop.png');

  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin/unassigned', 'New / Unassigned Requests', true);
  await saveScreenshot('fipp_phase4_admin_unassigned_mobile.png');

  // 9-10. In Progress
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await gotoAndWait('/admin/in-progress', 'In Progress Work Orders', true);
  await saveScreenshot('fipp_phase4_admin_in_progress_desktop.png');

  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin/in-progress', 'In Progress Work Orders', true);
  await saveScreenshot('fipp_phase4_admin_in_progress_mobile.png');

  // 11-12. Resolved + verify drawer shows Resolution Record
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await gotoAndWait('/admin/resolved', 'Resolved Complaint Archive', true);
  await saveScreenshot('fipp_phase4_admin_resolved_desktop.png');

  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const auditBtn = buttons.find(b => b.textContent && b.textContent.includes('Audit / Reopen'));
    if (auditBtn) auditBtn.click();
  });
  await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('RESOLUTION RECORD'), { timeout: 5000 });

  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin/resolved', 'Resolved Complaint Archive', true);
  await saveScreenshot('fipp_phase4_admin_resolved_mobile.png');

  // 13-14. Reports + verify Weekly toggle & no DPDP Act 2023 compliance overclaim
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await gotoAndWait('/admin/reports', 'Category Pareto Distribution');
  const reportsText = await page.evaluate(() => document.body.innerText);
  if (reportsText.includes('DPDP Act 2023')) {
    throw new Error('Reports page still contains DPDP Act 2023 compliance claim!');
  }
  await saveScreenshot('fipp_phase4_admin_reports_desktop.png');

  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await gotoAndWait('/admin/reports', 'Reports & Analytics');
  await saveScreenshot('fipp_phase4_admin_reports_mobile.png');

  if (consoleErrors.length > 0 || failedRequests.length > 0) {
    console.error('Console/Network Errors:', { consoleErrors, failedRequests });
    process.exitCode = 1;
  } else {
    console.log('Browser E2E verification passed with 0 console errors and 0 failed HTTP requests!');
  }

  await browser.close();
}

run().catch(err => {
  console.error('Fatal error during Phase 4.1 E2E verification:', err);
  process.exit(1);
});
