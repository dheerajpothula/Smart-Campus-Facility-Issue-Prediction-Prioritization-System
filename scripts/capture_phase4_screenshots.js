import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const outDir = path.resolve('docs/screenshots');
const artifactDir = 'C:\\Users\\pothu\\.gemini\\antigravity\\brain\\7aeec604-09d4-4b7d-893b-ea46693e3fd8';

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function run() {
  console.log('Launching Chrome for Phase 4 Administrator Control Centre screenshots...');
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();

  async function saveScreenshot(filename) {
    const localPath = path.join(outDir, filename);
    await page.screenshot({ path: localPath, fullPage: false });
    console.log(`Saved screenshot: ${localPath}`);
    if (fs.existsSync(artifactDir)) {
      const artPath = path.join(artifactDir, filename);
      fs.copyFileSync(localPath, artPath);
      console.log(`Copied to artifact dir: ${artPath}`);
    }
  }

  // Helper: Login as Admin
  async function loginAsAdmin(width, height, isMobile = false) {
    await page.setViewport({ width, height, isMobile });
    await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 600));

    // Click demo admin credentials button
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const aBtn = buttons.find(b => b.textContent && b.textContent.includes('ADM-2026-001'));
      if (aBtn) aBtn.click();
    });

    await new Promise(r => setTimeout(r, 600));

    // Click Sign In
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const loginBtn = buttons.find(b => b.textContent && b.textContent.includes('Sign In to FIPP'));
      if (loginBtn) loginBtn.click();
    });

    await new Promise(r => setTimeout(r, 1500));
  }

  // 1. Initial Login
  console.log('Authenticating Administrator...');
  await loginAsAdmin(1440, 900, false);

  // 1. Overview Desktop (1440x900)
  console.log('1. Capturing Admin Overview Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_overview_desktop.png');

  // 2. Overview Mobile (390x844)
  console.log('2. Capturing Admin Overview Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_overview_mobile.png');

  // 3. All Requests Ledger Desktop (1440x900)
  console.log('3. Capturing All Requests Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin/all-requests', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_all_requests_desktop.png');

  // 4. All Requests Ledger Mobile (390x844)
  console.log('4. Capturing All Requests Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin/all-requests', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_all_requests_mobile.png');

  // 5. Drawer Open on Desktop
  console.log('5. Capturing Complaint Details Drawer Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin/all-requests', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  // Click first inspect button
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const inspectBtn = buttons.find(b => b.textContent && b.textContent.includes('Inspect'));
    if (inspectBtn) inspectBtn.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase4_admin_drawer_desktop.png');

  // 6. Drawer Open on Mobile
  console.log('6. Capturing Complaint Details Drawer Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin/all-requests', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const inspectBtn = buttons.find(b => b.textContent && b.textContent.includes('Inspect'));
    if (inspectBtn) inspectBtn.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase4_admin_drawer_mobile.png');

  // 7. New / Unassigned Desktop (1440x900)
  console.log('7. Capturing New / Unassigned Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin/unassigned', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_unassigned_desktop.png');

  // 8. New / Unassigned Mobile (390x844)
  console.log('8. Capturing New / Unassigned Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin/unassigned', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_unassigned_mobile.png');

  // 9. In Progress Work Orders Desktop (1440x900)
  console.log('9. Capturing In Progress Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin/in-progress', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_in_progress_desktop.png');

  // 10. In Progress Work Orders Mobile (390x844)
  console.log('10. Capturing In Progress Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin/in-progress', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_in_progress_mobile.png');

  // 11. Resolved Archive Desktop (1440x900)
  console.log('11. Capturing Resolved Archive Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin/resolved', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_resolved_desktop.png');

  // 12. Resolved Archive Mobile (390x844)
  console.log('12. Capturing Resolved Archive Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin/resolved', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_resolved_mobile.png');

  // 13. Reports & Analytics Desktop (1440x900)
  console.log('13. Capturing Reports & Analytics Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/admin/reports', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_reports_desktop.png');

  // 14. Reports & Analytics Mobile (390x844)
  console.log('14. Capturing Reports & Analytics Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/admin/reports', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase4_admin_reports_mobile.png');

  console.log('All 14 Phase 4 screenshots successfully captured and saved!');
  await browser.close();
}

run().catch(err => {
  console.error('Fatal error capturing Phase 4 screenshots:', err);
  process.exit(1);
});
