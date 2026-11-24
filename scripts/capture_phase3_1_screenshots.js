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
  console.log('Launching Chrome for Phase 3.1 visual verification...');
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

  // 1. Public Landing Page Desktop (1440x900)
  console.log('1. Capturing Public Landing Page Desktop...');
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_1_landing_desktop.png');

  // 2. Public Landing Page Mobile (390x844)
  console.log('2. Capturing Public Landing Page Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_1_landing_mobile.png');

  // 3. Student Login Page (Desktop 1440x900)
  console.log('3. Capturing Student Login Page Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sBtn = buttons.find(b => b.textContent && b.textContent.includes('STU-2026-001'));
    if (sBtn) sBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('fipp_phase3_1_login_student_desktop.png');

  // 4. Student Login Page (Mobile 390x844)
  console.log('4. Capturing Student Login Page Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sBtn = buttons.find(b => b.textContent && b.textContent.includes('STU-2026-001'));
    if (sBtn) sBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('fipp_phase3_1_login_student_mobile.png');

  // 5. Authenticate Student and View Raise a Query (Desktop 1440x900)
  console.log('5. Capturing Student Raise a Query Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => sessionStorage.clear());
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sBtn = buttons.find(b => b.textContent && b.textContent.includes('STU-2026-001'));
    if (sBtn) sBtn.click();
  });
  await new Promise(r => setTimeout(r, 500));
  await page.evaluate(() => {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.click();
  });
  await page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(() => {});
  await new Promise(r => setTimeout(r, 1500));

  // Accept agreement
  await page.evaluate(() => {
    sessionStorage.setItem('fipp_student_agreed', 'true');
  });
  await page.goto('http://127.0.0.1:5173/student', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase3_1_student_raise_query_desktop.png');

  // 6. Student Raise a Query (Mobile 390x844)
  console.log('6. Capturing Student Raise a Query Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/student', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase3_1_student_raise_query_mobile.png');

  // 7. Student Complaint History (Desktop 1440x900)
  console.log('7. Capturing Student Complaint History Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/student/history', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  await saveScreenshot('fipp_phase3_1_student_history_desktop.png');

  // 8. Student Complaint History (Mobile 390x844)
  console.log('8. Capturing Student Complaint History Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/student/history', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  await saveScreenshot('fipp_phase3_1_student_history_mobile.png');

  // 9. Administrator Login Entry Point (Desktop 1440x900)
  console.log('9. Capturing Administrator Login Entry Desktop...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => sessionStorage.clear());
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const aBtn = buttons.find(b => b.textContent && b.textContent.includes('ADM-2026-001'));
    if (aBtn) aBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('fipp_phase3_1_admin_login_entry_desktop.png');

  // 10. Administrator Login Entry Point (Mobile 390x844)
  console.log('10. Capturing Administrator Login Entry Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const aBtn = buttons.find(b => b.textContent && b.textContent.includes('ADM-2026-001'));
    if (aBtn) aBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));
  await saveScreenshot('fipp_phase3_1_admin_login_entry_mobile.png');

  // 11. Legacy Streamlit Application Comparison (Desktop 1440x900 on port 8501)
  console.log('11. Capturing Legacy Streamlit Interface for Comparison...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  try {
    await page.goto('http://127.0.0.1:8501/', { waitUntil: 'networkidle0', timeout: 10000 });
    await new Promise(r => setTimeout(r, 2000));
    await saveScreenshot('fipp_phase3_1_streamlit_legacy_comparison.png');
  } catch (e) {
    console.log('Streamlit screenshot note:', e.message);
  }

  console.log('\nAll Phase 3.1 visual verification screenshots captured successfully!');
  await browser.close();
}

run().catch(err => {
  console.error('Screenshot Capture Error:', err);
  process.exit(1);
});
