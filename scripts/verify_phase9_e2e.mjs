import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const puppeteer = require(path.resolve('frontend/node_modules/puppeteer-core'));

const BASE_URL = process.env.FIPP_E2E_URL || 'http://127.0.0.1:5173';
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = process.env.FIPP_ARTIFACT_DIR || 'C:\\Users\\pothu\\.gemini\\antigravity\\brain\\3188d654-1f27-408a-880d-a38c62593b11';
const VALID_PNG_PATH = process.env.FIPP_TEST_PNG;
const INVALID_WEBP_PATH = process.env.FIPP_TEST_WEBP;
const TEMP_ADMIN_PWD = process.env.FIPP_E2E_TEMP_ADMIN_PWD;
const NEW_ADMIN_PWD = process.env.FIPP_E2E_NEW_ADMIN_PWD;

function assert(cond, msg) {
  if (!cond) {
    throw new Error(`E2E ASSERTION FAILED: ${msg}`);
  }
}

async function clickButtonByText(page, regexOrText) {
  const clicked = await page.evaluate((pattern, isRegex) => {
    const re = isRegex ? new RegExp(pattern, 'i') : null;
    const buttons = Array.from(document.querySelectorAll('button, a'));
    for (const btn of buttons) {
      if (btn.disabled) continue;
      const txt = (btn.innerText || btn.textContent || '').trim();
      const hit = re ? re.test(txt) : txt.toUpperCase().includes(pattern.toUpperCase());
      if (hit) {
        btn.scrollIntoView({ block: 'center' });
        btn.click();
        return txt;
      }
    }
    return null;
  }, regexOrText instanceof RegExp ? regexOrText.source : regexOrText, regexOrText instanceof RegExp);
  assert(clicked !== null, `Could not find enabled button matching: ${regexOrText}`);
  return clicked;
}

async function typeIntoInput(page, selector, value) {
  await page.waitForSelector(selector, { timeout: 10000 });
  await page.click(selector);
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyA');
  await page.keyboard.up('Control');
  await page.keyboard.press('Backspace');
  await page.type(selector, value);
}

async function checkHorizontalOverflow(page, label) {
  await new Promise((r) => setTimeout(r, 350));
  const dims = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  assert(
    dims.scrollWidth <= dims.innerWidth + 2,
    `Horizontal overflow at ${label}: scrollWidth=${dims.scrollWidth} > innerWidth=${dims.innerWidth}`,
  );
  return dims;
}

async function clickRowAction(page, ticketId, btnPattern) {
  const clicked = await page.evaluate((tid, pat) => {
    const re = new RegExp(pat, 'i');
    const rows = Array.from(document.querySelectorAll('tr')).filter((tr) => tr.innerText.includes(tid));
    for (const row of rows) {
      const btn = Array.from(row.querySelectorAll('button')).find((b) => re.test(b.innerText));
      if (btn) {
        btn.scrollIntoView({ block: 'center' });
        btn.click();
        return true;
      }
    }
    return false;
  }, ticketId, btnPattern.source);
  assert(clicked, `Failed to click row action (${btnPattern}) for ${ticketId}`);
}

async function run() {
  assert(VALID_PNG_PATH && fs.existsSync(VALID_PNG_PATH), 'Missing FIPP_TEST_PNG');
  assert(INVALID_WEBP_PATH && fs.existsSync(INVALID_WEBP_PATH), 'Missing FIPP_TEST_WEBP');
  assert(TEMP_ADMIN_PWD && NEW_ADMIN_PWD, 'Missing FIPP_E2E_TEMP_ADMIN_PWD / FIPP_E2E_NEW_ADMIN_PWD');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const consoleErrors = [];
  const pageErrors = [];
  const unexpectedHttpErrors = [];
  let allowExpectedAuthError = false;
  let sawUploadGet200 = false;
  let sawLogout200 = false;
  let sawAdminPatch200 = false;

  const summary = {
    checks: {},
    ticketsCreated: [],
    overflowChecks: [],
    screenshots: [],
  };

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        if (allowExpectedAuthError && (msg.text().includes('401') || msg.text().includes('409'))) return;
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => pageErrors.push(err.message));
    page.on('response', (res) => {
      const url = res.url();
      const status = res.status();
      if (url.includes('/api/uploads/') && res.request().method() === 'GET' && status === 200) {
        sawUploadGet200 = true;
      }
      if (url.includes('/api/auth/logout') && status === 200) {
        sawLogout200 = true;
      }
      if (url.includes('/api/admin/complaints/') && res.request().method() === 'PATCH' && status === 200) {
        sawAdminPatch200 = true;
      }
      if (status >= 400) {
        if (allowExpectedAuthError && (status === 401 || status === 409) && url.includes('/api/auth/')) return;
        unexpectedHttpErrors.push({ status, url });
      }
    });

    // 1. Public Landing + Zero Demo/Institution Claims + Auth Route Guards
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle0' });
    const landingText = await page.evaluate(() => document.body.innerText);
    assert(landingText.toUpperCase().includes('HOW FIPP WORKS'), 'Missing How FIPP Works');
    assert(!/\bLPU\b/i.test(landingText), 'Institution reference found on landing page');
    assert(!landingText.includes('ISO 27001') && !landingText.includes('DPDP Act 2023'), 'Compliance overclaim present');
    summary.overflowChecks.push({ view: 'landing_desktop', ...(await checkHorizontalOverflow(page, 'landing_desktop')) });

    await page.goto(`${BASE_URL}/student`, { waitUntil: 'networkidle0' });
    assert(page.url().includes('/login'), 'Unauthenticated /student did not redirect');

    await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle0' });
    assert(page.url().includes('/login'), 'Unauthenticated /admin did not redirect');

    const loginText = await page.evaluate(() => document.body.innerText);
    assert(!loginText.toUpperCase().includes('DEMO CREDENTIALS'), 'Demo credentials unexpectedly displayed');
    assert(!loginText.toUpperCase().includes('SELF-DECLARED STUDENT IDENTITY'), 'Old info box unexpectedly displayed');
    assert(loginText.toUpperCase().includes('ENTER YOUR NAME AND 8-DIGIT STUDENT ID TO CONTINUE'), 'Missing concise login instruction');

    // Verify invalid non-8-digit ID rejected cleanly client-side
    await typeIntoInput(page, 'input[name="studentName"]', 'Rohan Verma');
    await typeIntoInput(page, 'input[name="studentId"]', '1234ABCD');
    await page.click('button[type="submit"]');
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('EXACTLY EIGHT NUMERIC DIGITS'),
      { timeout: 6000 },
    );

    // Switch to Administrator tab & test initial `fipp.admin` mandatory password change gate
    await clickButtonByText(page, /^Administrator$/i);
    await typeIntoInput(page, 'input[name="username"]', 'fipp.admin');
    await typeIntoInput(page, 'input[type="password"]', TEMP_ADMIN_PWD);
    await page.click('button[type="submit"]');

    await page.waitForFunction(() => window.location.pathname.startsWith('/admin'), { timeout: 10000 });
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('FIRST-LOGIN PASSWORD UPDATE REQUIRED'),
      { timeout: 10000 },
    );
    const pwdInputs = await page.$$('input[type="password"]');
    assert(pwdInputs.length === 3, `Expected 3 password inputs on first-login gate, got ${pwdInputs.length}`);
    await pwdInputs[0].type(TEMP_ADMIN_PWD);
    await pwdInputs[1].type(NEW_ADMIN_PWD);
    await pwdInputs[2].type(NEW_ADMIN_PWD);
    await page.click('button[type="submit"]');

    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('EXECUTIVE OPERATIONS OVERVIEW'),
      { timeout: 12000 },
    );
    summary.checks.adminFirstLoginAndPasswordChange = 'PASSED';

    // Check Block & Floor Reference tab inside Admin Directory modal (NO pre-provisioning of student needed)
    await clickButtonByText(page, /Blocks & Floors/i);
    await page.waitForFunction(
      () => document.body.innerText.includes('Block 57') && document.body.innerText.includes('University Centre'),
      { timeout: 8000 },
    );
    await page.click('button[aria-label="Close Directory"]');
    await clickButtonByText(page, /Sign Out/i);
    await page.waitForFunction(() => window.location.pathname === '/' || window.location.pathname.includes('/login'), { timeout: 8000 });

    // 2. Brand-New Student Self-Registration (Name + Leading-Zero 8-Digit ID) & Dynamic Block -> Floor Cascade
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0' });
    await typeIntoInput(page, 'input[name="studentName"]', 'Rohan Verma');
    await typeIntoInput(page, 'input[name="studentId"]', '00246810');
    await page.click('button[type="submit"]');
    await page.waitForFunction(() => window.location.pathname.startsWith('/student'), { timeout: 10000 });
    await page.waitForFunction(() => document.querySelectorAll('input[type="checkbox"]').length >= 3, { timeout: 8000 });

    await page.evaluate(() => {
      document.querySelectorAll('input[type="checkbox"]').forEach((b) => { if (!b.checked) b.click(); });
    });
    await clickButtonByText(page, /Agree & Proceed/i);
    await page.waitForSelector('textarea', { timeout: 8000 });

    // Verify leading zeroes preserved in Student Portal header banner
    const stuBanner = await page.evaluate(() => document.body.innerText);
    assert(stuBanner.includes('00246810'), 'Leading zero Student ID 00246810 missing from portal banner');
    assert(!/\bLPU\b/i.test(stuBanner), 'Institution reference present on Raise Query page');

    // Test Block -> Floor cascading + Unknown floor block behavior
    await page.evaluate(() => {
      const selects = Array.from(document.querySelectorAll('select'));
      const catSel = selects[1];
      const setVal = (el, val) => {
        Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set.call(el, val);
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      const blockSel = selects.find((s) => Array.from(s.options).some((o) => o.value === 'Block 57'));
      if (!blockSel) throw new Error('Block 57 missing from block selector');
      setVal(blockSel, 'Block 3');
      if (catSel && !catSel.value) setVal(catSel, catSel.options[1].value);
    });
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('FLOOR COUNT UNVERIFIED'),
      { timeout: 6000 },
    );

    // Switch to Block 57 -> pick Second Floor -> upload PNG -> submit
    await page.evaluate(() => {
      const selects = Array.from(document.querySelectorAll('select'));
      const blockSel = selects.find((s) => Array.from(s.options).some((o) => o.value === 'Block 57'));
      Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set.call(blockSel, 'Block 57');
      blockSel.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForFunction(
      () => Array.from(document.querySelectorAll('select')).some((s) => Array.from(s.options).some((o) => o.value === 'BLK-57-F2')),
      { timeout: 6000 },
    );
    await page.evaluate(() => {
      const selects = Array.from(document.querySelectorAll('select'));
      const floorSel = selects.find((s) => Array.from(s.options).some((o) => o.value === 'BLK-57-F2'));
      Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set.call(floorSel, 'BLK-57-F2');
      floorSel.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.evaluate(() => {
      const setVal = (el, val) => {
        const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      for (const inp of document.querySelectorAll('input:not([type="checkbox"]):not([type="file"]):not([type="hidden"])')) {
        if (inp.disabled || inp.readOnly) continue;
        const nm = (inp.name || '').toLowerCase();
        const tp = (inp.type || '').toLowerCase();
        if (tp === 'date' || nm.includes('date')) setVal(inp, '2026-12-05');
        else if (tp === 'tel' || (inp.placeholder || '').toLowerCase().includes('mobile')) setVal(inp, '9876543210');
        else if (!inp.value) setVal(inp, '204');
      }
      setVal(document.querySelector('textarea'), 'Phase 9 E2E sparking socket check in Block 57 Second Floor.');
    });

    const fileInput = await page.$('input[type="file"]');
    await fileInput.uploadFile(INVALID_WEBP_PATH);
    await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('ONLY JPEG AND PNG'), { timeout: 6000 });
    await fileInput.uploadFile(VALID_PNG_PATH);
    await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('TEST_E2E.PNG'), { timeout: 8000 });
    await page.click('button[type="submit"]');
    await page.waitForFunction(() => /CMP-2026-\d+/i.test(document.body.innerText), { timeout: 10000 });
    const ticket1Id = await page.evaluate(() => {
      const matches = document.body.innerText.match(/CMP-2026-\d+/g) || [];
      return matches[matches.length - 1];
    });
    summary.ticketsCreated.push(ticket1Id);

    // Check History + Authenticated Attachment View
    await clickButtonByText(page, /^View in History$|^History$/i);
    await page.waitForFunction((tid) => document.body.innerText.includes(tid), { timeout: 8000 }, ticket1Id);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'fipp_phase9_e2e_student.png') });
    await clickRowAction(page, ticket1Id, /view details/i);
    await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('VIEW ATTACHMENT'), { timeout: 6000 });
    await page.evaluate(() => { window.open = () => null; });
    await clickButtonByText(page, /View Attachment/i);
    await new Promise((r) => setTimeout(r, 600));
    assert(sawUploadGet200, 'Student authenticated attachment GET failed');
    summary.overflowChecks.push({ view: 'student_history_desktop', ...(await checkHorizontalOverflow(page, 'student_history_desktop')) });

    await page.evaluate(() => {
      const modalBtns = Array.from(document.querySelectorAll('.fixed button'));
      if (modalBtns[0]) modalBtns[0].click();
    });
    await clickButtonByText(page, /Sign Out/i);
    await page.waitForFunction(() => window.location.pathname === '/' || window.location.pathname.includes('/login'), { timeout: 8000 });
    assert(sawLogout200, 'Logout did not return HTTP 200');

    // Verify existing student re-login retrieves persisted complaint + name mismatch protection works
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0' });
    await typeIntoInput(page, 'input[name="studentName"]', 'Imposter Name');
    await typeIntoInput(page, 'input[name="studentId"]', '00246810');
    allowExpectedAuthError = true;
    await page.click('button[type="submit"]');
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('ALREADY REGISTERED UNDER A DIFFERENT NAME'),
      { timeout: 8000 },
    );
    allowExpectedAuthError = false;

    await typeIntoInput(page, 'input[name="studentName"]', '  rohan   verma ');
    await typeIntoInput(page, 'input[name="studentId"]', '00246810');
    await page.click('button[type="submit"]');
    await page.waitForFunction(() => window.location.pathname.startsWith('/student'), { timeout: 10000 });
    await page.goto(`${BASE_URL}/student/history`, { waitUntil: 'networkidle0' });
    await page.waitForFunction((tid) => document.body.innerText.includes(tid), { timeout: 8000 }, ticket1Id);
    await clickButtonByText(page, /Sign Out/i);
    await page.waitForFunction(() => window.location.pathname === '/' || window.location.pathname.includes('/login'), { timeout: 8000 });
    summary.checks.studentWorkflow = 'PASSED';

    // 3. Admin Re-Login with New Password & Verify All 6 Views + Responsive Viewports
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0' });
    await clickButtonByText(page, /^Administrator$/i);
    await typeIntoInput(page, 'input[name="username"]', 'fipp.admin');
    await typeIntoInput(page, 'input[type="password"]', NEW_ADMIN_PWD);
    await page.click('button[type="submit"]');
    await page.waitForFunction(() => window.location.pathname.startsWith('/admin'), { timeout: 10000 });
    await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('EXECUTIVE OPERATIONS OVERVIEW'), { timeout: 10000 });

    // Confirm self-registered student 00246810 appears in Admin Student Registry & inline name correction works
    await clickButtonByText(page, /Student Registry/i);
    await page.waitForFunction(
      () => document.body.innerText.includes('00246810') && document.body.innerText.includes('Rohan Verma'),
      { timeout: 8000 },
    );
    await clickButtonByText(page, /^Edit Name$/i);
    await typeIntoInput(page, 'input[aria-label="Correct name for 00246810"]', 'Rohan K. Verma');
    await clickButtonByText(page, /^Save$/i);
    await page.waitForFunction(
      () => document.body.innerText.includes('Rohan K. Verma'),
      { timeout: 8000 },
    );
    await page.click('button[aria-label="Close Directory"]');

    const adminSections = ['Overview', 'All Requests', 'New / Unassigned', 'In Progress', 'Resolved', 'Reports'];
    for (const sec of adminSections) {
      await clickButtonByText(page, sec);
      await new Promise((r) => setTimeout(r, 350));
      summary.overflowChecks.push({
        view: `admin_${sec.toLowerCase().replace(/[^a-z0-9]/g, '_')}_desktop`,
        ...(await checkHorizontalOverflow(page, `admin_${sec}_desktop`)),
      });
    }

    await clickButtonByText(page, 'All Requests');
    await page.waitForFunction((tid) => document.body.innerText.includes(tid), { timeout: 8000 }, ticket1Id);
    await clickRowAction(page, ticket1Id, /inspect|view|details/i);
    await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('MCPI'), { timeout: 8000 });
    await page.evaluate(() => {
      const containers = Array.from(document.querySelectorAll('[role="dialog"], .fixed'));
      const drawer = containers[containers.length - 1] || document.body;
      const statusSel = Array.from(drawer.querySelectorAll('select')).find((s) =>
        Array.from(s.options).some((o) => o.value === 'Resolved'),
      );
      Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set.call(statusSel, 'Resolved');
      statusSel.dispatchEvent(new Event('change', { bubbles: true }));
      const ta = drawer.querySelector('textarea');
      if (ta) {
        Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(ta, 'Phase 9 E2E verified.');
        ta.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await clickButtonByText(page, /Update Status|Save Changes|Save & Update|Apply Update/i);
    await new Promise((r) => setTimeout(r, 600));
    assert(sawAdminPatch200, 'Admin drawer status update failed');

    await page.setViewport({ width: 768, height: 1024 });
    summary.overflowChecks.push({ view: 'admin_tablet', ...(await checkHorizontalOverflow(page, 'admin_tablet')) });
    await page.setViewport({ width: 390, height: 844 });
    summary.overflowChecks.push({ view: 'admin_mobile', ...(await checkHorizontalOverflow(page, 'admin_mobile')) });
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'fipp_phase9_e2e_admin_mobile.png') });

    assert(consoleErrors.length === 0, `Console errors: ${JSON.stringify(consoleErrors)}`);
    assert(pageErrors.length === 0, `Page errors: ${JSON.stringify(pageErrors)}`);
    assert(unexpectedHttpErrors.length === 0, `HTTP errors: ${JSON.stringify(unexpectedHttpErrors)}`);
    summary.checks.adminWorkflow = 'PASSED';

    console.log(JSON.stringify({ success: true, ...summary }, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
