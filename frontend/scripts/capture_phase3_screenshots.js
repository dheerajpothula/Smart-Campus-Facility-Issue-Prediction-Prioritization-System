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
  console.log('3. Capturing Student Portal Agreement Screen...');
  await page.setViewport({ width: 1440, height: 900, isMobile: false });
  // Go to login, clear sessionStorage
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle0' });
  await page.evaluate(() => sessionStorage.clear());
  await new Promise(r => setTimeout(r, 500));
  // Click STU-2026-001 demo button
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sBtn = buttons.find(b => b.textContent && b.textContent.includes('STU-2026-001'));
    if (sBtn) sBtn.click();
  });
  await new Promise(r => setTimeout(r, 500));
  // Click Sign In
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const loginBtn = buttons.find(b => b.textContent && b.textContent.includes('Sign In to FIPP'));
    if (loginBtn) loginBtn.click();
  });
  await page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(() => {});
  await new Promise(r => setTimeout(r, 1500));
  // Now on /student, ensure fipp_student_agreed is not set
  await page.evaluate(() => sessionStorage.removeItem('fipp_student_agreed'));
  await page.goto('http://localhost:5173/student', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_student_agreement.png');

  // 4. Student Portal - Raise Query Form
  console.log('4. Capturing Raise Query Form with Cascading Selection...');
  // Check the 3 agreement checkboxes and click Agree & Proceed
  await page.evaluate(() => {
    const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
    checkboxes.forEach(cb => { cb.checked = true; cb.dispatchEvent(new Event('change', { bubbles: true })); });
  });
  await new Promise(r => setTimeout(r, 500));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const agreeBtn = buttons.find(b => b.textContent && b.textContent.includes('Agree & Proceed'));
    if (agreeBtn) agreeBtn.click();
  });
  await new Promise(r => setTimeout(r, 1200));

  // Fill in sample query details
  await page.evaluate(() => {
    // Select Message Type = Complaint
    const selects = Array.from(document.querySelectorAll('select'));
    if (selects[0]) {
      selects[0].value = 'Complaint';
      selects[0].dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await new Promise(r => setTimeout(r, 500));

  await page.evaluate(() => {
    // Fill title
    const inputs = Array.from(document.querySelectorAll('input'));
    const titleInput = inputs.find(i => i.placeholder && i.placeholder.includes('Brief headline'));
    if (titleInput) {
      titleInput.value = 'Room 304 Main Study Lamp Not Functioning';
      titleInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    // Fill phone
    const phoneInput = inputs.find(i => i.placeholder && i.placeholder.includes('9876543210'));
    if (phoneInput) {
      phoneInput.value = '9876543210';
      phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    // Fill room
    const roomInput = inputs.find(i => i.placeholder && i.placeholder.includes('304'));
    if (roomInput) {
      roomInput.value = '304-B';
      roomInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    // Fill description
    const textarea = document.querySelector('textarea');
    if (textarea) {
      textarea.value = 'The primary ceiling lighting fixture in hostel room 304 has completely failed since yesterday evening. The switch produces sparks when turned on. Urgent inspection and replacement requested.';
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });
  await new Promise(r => setTimeout(r, 800));
  await saveScreenshot('fipp_phase3_student_raise_query_form.png');

  // 5. Submit Query & Capture Confirmation Card
  console.log('5. Submitting query and capturing success confirmation card...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const subBtn = buttons.find(b => b.textContent && b.textContent.includes('Submit Facility Request'));
    if (subBtn) subBtn.click();
  });
  await new Promise(r => setTimeout(r, 2000));
  await saveScreenshot('fipp_phase3_student_submission_success.png');

  // 6. Student Portal - Complaint History Ledger
  console.log('6. Capturing Student History Ledger...');
  await page.goto('http://localhost:5173/student/history', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  await saveScreenshot('fipp_phase3_student_history_ledger.png');

  // 7. Complaint Details & Status Timeline Modal
  console.log('7. Capturing Ticket Details Modal with Lifecycle Stepper...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const viewBtn = buttons.find(b => b.textContent && b.textContent.includes('View Details'));
    if (viewBtn) viewBtn.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_student_details_timeline.png');

  // 8. Student Withdrawal Modal
  console.log('8. Capturing Withdrawal Confirmation Dialog...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const withdrawBtn = buttons.find(b => b.textContent && b.textContent.includes('Withdraw Request'));
    if (withdrawBtn) withdrawBtn.click();
  });
  await new Promise(r => setTimeout(r, 800));
  await saveScreenshot('fipp_phase3_student_withdrawal_modal.png');

  // Close withdraw modal and details modal
  await page.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 400));
  await page.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 400));

  // 9. Resolved State with 5-Star Feedback & Rating
  console.log('9. Capturing Resolved State with Feedback & Rating...');
  // Filter status to 'Resolved'
  await page.evaluate(() => {
    const selects = Array.from(document.querySelectorAll('select'));
    const statusSelect = selects.find(s => Array.from(s.options).some(o => o.value === 'Resolved'));
    if (statusSelect) {
      statusSelect.value = 'Resolved';
      statusSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await new Promise(r => setTimeout(r, 800));
  // Open details for the first resolved ticket
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const viewBtn = buttons.find(b => b.textContent && b.textContent.includes('View Details'));
    if (viewBtn) viewBtn.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await saveScreenshot('fipp_phase3_student_feedback_rating.png');

  console.log('All 9 Phase 3 screenshots captured successfully!');
  await browser.close();
}

run().catch(err => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
