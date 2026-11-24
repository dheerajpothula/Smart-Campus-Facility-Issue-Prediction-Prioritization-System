import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const outDir = path.resolve('../docs/screenshots');
const artifactDir = 'C:\\Users\\pothu\\.gemini\\antigravity\\brain\\7aeec604-09d4-4b7d-893b-ea46693e3fd8';

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function run() {
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

  // 1. Landing Page Desktop (1440x900)
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase2_landing_desktop.png');

  // 2. Landing Page Mobile (390x844)
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase2_landing_mobile.png');

  // 3. Student Portal - Raise Query
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  // Navigate to login
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 500));
  // Click student demo button
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sBtn = buttons.find(b => b.textContent && b.textContent.includes('STU-2026-001'));
    if (sBtn) sBtn.click();
  });
  await new Promise(r => setTimeout(r, 500));
  // Submit login
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const loginBtn = buttons.find(b => b.textContent && b.textContent.includes('Sign In to FIPP'));
    if (loginBtn) loginBtn.click();
  });
  await new Promise(r => setTimeout(r, 1500));

  // Should now be on /student/raise-query
  await saveScreenshot('fipp_phase2_student_raise_query.png');

  // 4. Student Portal - History
  await page.goto('http://127.0.0.1:5173/student/history', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  await saveScreenshot('fipp_phase2_student_history.png');

  // 5. Admin Control Centre - Overview
  await page.evaluate(() => sessionStorage.clear());
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 500));
  // Click admin demo button
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const aBtn = buttons.find(b => b.textContent && b.textContent.includes('ADM-2026-001'));
    if (aBtn) aBtn.click();
  });
  await new Promise(r => setTimeout(r, 500));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const loginBtn = buttons.find(b => b.textContent && b.textContent.includes('Sign In to FIPP'));
    if (loginBtn) loginBtn.click();
  });
  await new Promise(r => setTimeout(r, 1500));

  // Admin Overview
  await saveScreenshot('fipp_phase2_admin_overview.png');

  // 6. Admin Control Centre - All Requests
  await page.goto('http://127.0.0.1:5173/admin/all-requests', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  await saveScreenshot('fipp_phase2_admin_all_requests.png');

  await browser.close();
  console.log('All screenshots captured successfully!');
}

run().catch(err => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
