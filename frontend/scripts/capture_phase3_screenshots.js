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
  console.log('Launching Chrome for Phase 3 screenshot capture...');
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

  // Helper for React controlled input setting
  async function setReactInput(selector, value) {
    await page.evaluate((sel, val) => {
      const el = document.querySelector(sel);
      if (el) {
        const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, selector, value);
  }

  // 1. Landing Page Desktop (1440x900)
  console.log('1. Capturing Landing Page Desktop...');
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_landing_desktop.png');

  // 2. Landing Page Mobile (390x844)
  console.log('2. Capturing Landing Page Mobile...');
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_landing_mobile.png');

  // 3. Student Portal - Dedicated Agreement Screen
  console.log('3. Authenticating Student & Capturing Agreement Screen...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => sessionStorage.clear());
  await new Promise(r => setTimeout(r, 500));

  // Click student demo credentials
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sBtn = buttons.find(b => b.textContent && b.textContent.includes('STU-2026-001'));
    if (sBtn) sBtn.click();
  });
  await new Promise(r => setTimeout(r, 500));

  // Click Authenticate & Continue
  await page.evaluate(() => {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.click();
  });
  await page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(() => {});
  await new Promise(r => setTimeout(r, 1500));

  // Ensure agreement is fresh
  await page.evaluate(() => sessionStorage.removeItem('fipp_student_agreed'));
  await page.goto('http://localhost:5173/student', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase3_student_agreement.png');

  // 4. Student Portal - Unlock Form & Fill Details
  console.log('4. Unlocking Form and Filling Query Details...');
  // Check all 3 agreement checkboxes
  await page.evaluate(() => {
    const cbs = Array.from(document.querySelectorAll('input[type="checkbox"]'));
    cbs.forEach(cb => {
      if (!cb.checked) {
        cb.click();
      }
    });
  });
  await new Promise(r => setTimeout(r, 600));

  // Click Agree & Proceed to Form
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const agreeBtn = buttons.find(b => b.textContent && b.textContent.includes('Agree & Proceed'));
    if (agreeBtn) agreeBtn.click();
  });
  await new Promise(r => setTimeout(r, 1500));

  // Fill in Form Fields
  await setReactInput('input[placeholder*="Washroom"]', 'Study Lamp Defect & Sparking Socket in Room 304');
  await setReactInput('input[placeholder*="204"]', '304-B');
  await setReactInput('input[placeholder*="10-digit"]', '9876543210');
  await setReactInput('textarea', 'The primary ceiling lighting fixture and study lamp power outlet in hostel room 304-B are sparking upon activation. The socket cover is charred and needs immediate electrical engineering replacement.');

  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_student_raise_query_form.png');

  // 5. Submit Query & Capture Confirmation Card
  console.log('5. Submitting query and capturing success confirmation card...');
  await page.evaluate(() => {
    const form = document.querySelector('form');
    if (form) form.requestSubmit();
  });
  await new Promise(r => setTimeout(r, 3000));
  await saveScreenshot('fipp_phase3_student_submission_success.png');

  // 6. Student History Ledger
  console.log('6. Capturing Student History Ledger...');
  await page.goto('http://localhost:5173/student/history', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 2000));
  await saveScreenshot('fipp_phase3_student_history_ledger.png');

  // 7. Complaint Details Modal with 5-stage stepper on an OPEN ticket
  console.log('7. Capturing Ticket Details Modal with 5-stage stepper...');
  await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    const openRow = rows.find(r => {
      const text = r.textContent || '';
      return text.includes('Submitted') || text.includes('Under Review') || text.includes('In Progress');
    }) || rows[0];

    if (openRow) {
      const viewBtn = openRow.querySelector('button');
      if (viewBtn) viewBtn.click();
    }
  });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase3_student_details_timeline.png');

  // 8. Withdrawal Confirmation Modal
  console.log('8. Capturing Withdrawal Modal...');
  const clickedWithdraw = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const wBtn = buttons.find(b => b.textContent && b.textContent.includes('Withdraw Query'));
    if (wBtn) {
      wBtn.click();
      return true;
    }
    return false;
  });

  if (clickedWithdraw) {
    await new Promise(r => setTimeout(r, 1000));
    await setReactInput('input[placeholder*="resolved independently"]', 'Issue resolved independently by hostel caretaker before technician visit.');
    await new Promise(r => setTimeout(r, 500));
    await saveScreenshot('fipp_phase3_student_withdrawal_modal.png');
    await page.keyboard.press('Escape');
    await new Promise(r => setTimeout(r, 500));
  } else {
    console.log('Withdraw Query button not found!');
  }
  await page.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 500));

  // 9. Resolved Ticket with 5-Star Feedback & Rating
  console.log('9. Capturing Resolved State with Feedback & Rating...');
  await page.evaluate(() => {
    const selects = Array.from(document.querySelectorAll('select'));
    const statusSelect = selects.find(s => Array.from(s.options).some(o => o.value === 'Resolved'));
    if (statusSelect) {
      statusSelect.value = 'Resolved';
      statusSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await new Promise(r => setTimeout(r, 1000));

  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const viewBtn = buttons.find(b => b.textContent && b.textContent.includes('View Details'));
    if (viewBtn) viewBtn.click();
  });
  await new Promise(r => setTimeout(r, 1200));
  await saveScreenshot('fipp_phase3_student_feedback_rating.png');

  console.log('All 9 Phase 3 screenshots captured successfully!');
  await browser.close();
}

run().catch(err => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
