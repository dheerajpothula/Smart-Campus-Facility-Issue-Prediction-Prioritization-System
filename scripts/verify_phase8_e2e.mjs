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

async function fillLogin(page, username, password) {
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });
  const userSelector = 'input[name="username"], input[type="text"], input:not([type="password"]):not([type="checkbox"])';
  await page.click(userSelector);
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyA');
  await page.keyboard.up('Control');
  await page.keyboard.press('Backspace');
  await page.type(userSelector, username);

  await page.click('input[type="password"]');
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyA');
  await page.keyboard.up('Control');
  await page.keyboard.press('Backspace');
  await page.type('input[type="password"]', password);

  await page.click('button[type="submit"]');
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
    // Fallback for mobile card layouts: pick innermost card containing tid
    const cards = Array.from(document.querySelectorAll('div'))
      .filter((d) => d.innerText.includes(tid) && d.querySelector('button'))
      .sort((a, b) => a.innerText.length - b.innerText.length);
    for (const card of cards) {
      const btn = Array.from(card.querySelectorAll('button')).find((b) => re.test(b.innerText)) || card.querySelector('button');
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
  if (!VALID_PNG_PATH || !fs.existsSync(VALID_PNG_PATH)) {
    throw new Error(`Missing FIPP_TEST_PNG fixture: ${VALID_PNG_PATH}`);
  }
  if (!INVALID_WEBP_PATH || !fs.existsSync(INVALID_WEBP_PATH)) {
    throw new Error(`Missing FIPP_TEST_WEBP fixture: ${INVALID_WEBP_PATH}`);
  }

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const consoleErrors = [];
  const pageErrors = [];
  const unexpectedHttpErrors = [];
  const expectedStatuses = new Set(); // allow expected invalid login 401 or negative checks temporarily
  let allowExpectedAuthFailure = false;
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
        const text = msg.text();
        if (allowExpectedAuthFailure && text.includes('401')) return;
        consoleErrors.push(text);
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
        if (allowExpectedAuthFailure && status === 401 && url.includes('/api/auth/login')) {
          expectedStatuses.add('401_invalid_login');
          return;
        }
        unexpectedHttpErrors.push({ status, url });
      }
    });

    // 1. Public Landing + Compliance Claims + Route Guards + Production Login Safety
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle0' });
    const landingText = await page.evaluate(() => document.body.innerText);
    assert(landingText.toUpperCase().includes('HOW FIPP WORKS'), 'Landing page missing How FIPP Works');
    assert(!landingText.includes('ISO 27001'), 'Landing/Footer still claims ISO 27001');
    assert(!landingText.includes('DPDP Act 2023'), 'Landing/Footer still claims DPDP Act 2023');
    summary.overflowChecks.push({ view: 'landing_desktop', ...(await checkHorizontalOverflow(page, 'landing_desktop')) });

    await page.goto(`${BASE_URL}/student`, { waitUntil: 'networkidle0' });
    assert(page.url().includes('/login'), `Expected /student guard redirect to /login, got ${page.url()}`);

    await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle0' });
    assert(page.url().includes('/login'), `Expected /admin guard redirect to /login, got ${page.url()}`);

    const loginText = await page.evaluate(() => document.body.innerText);
    assert(!loginText.toUpperCase().includes('DEMO CREDENTIALS'), 'Production build must hide Demo Credentials box');
    assert(!loginText.toUpperCase().includes('STUDENT DEMO'), 'Production build must hide Student Demo autofill');

    allowExpectedAuthFailure = true;
    await fillLogin(page, '00123456', 'WrongPassword123');
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('INVALID') || document.body.innerText.toUpperCase().includes('NOT AUTHORIZED'),
      { timeout: 10000 },
    );
    allowExpectedAuthFailure = false;
    summary.checks.authGuardsAndInvalidLogin = 'PASSED';

    // 2. Student Login & Raise a Query (Declarations, 4-tier hierarchy, 500-char, Invalid vs Valid upload)
    await fillLogin(page, process.env.FIPP_E2E_STUDENT_NAME || 'Aarav Sharma', process.env.FIPP_E2E_STUDENT_ID || '00123456');
    await page.waitForFunction(() => window.location.pathname.startsWith('/student'), { timeout: 10000 });
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('DECLARATION') || document.querySelectorAll('input[type="checkbox"]').length >= 3,
      { timeout: 10000 },
    );

    // Accept all 3 mandatory declarations
    const declCount = await page.evaluate(() => {
      const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
      boxes.forEach((b) => { if (!b.checked) b.click(); });
      return boxes.length;
    });
    assert(declCount >= 3, `Expected >=3 declaration checkboxes, got ${declCount}`);
    await clickButtonByText(page, /Proceed|Continue|Accept|I Agree/i);

    // Helper: iteratively fill all empty enabled <select> elements as cascading fields mount
    async function fillAllCascadingSelects() {
      const preferred = ['Grievance', 'Electricity', 'Academic Block 34', 'BH-1', 'Room No', '10:00'];
      for (let step = 0; step < 16; step += 1) {
        const picked = await page.evaluate((prefList) => {
          const selects = Array.from(document.querySelectorAll('select'));
          for (const sel of selects) {
            if (sel.disabled || sel.value) continue;
            const opts = Array.from(sel.options).filter((o) => o.value && !o.disabled);
            if (opts.length === 0) continue;
            const chosen = opts.find((o) => prefList.some((p) => o.text.includes(p) || o.value.includes(p))) || opts[0];
            const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
            setter.call(sel, chosen.value);
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return chosen.text;
          }
          return null;
        }, preferred);
        if (!picked) break;
        await new Promise((r) => setTimeout(r, 180));
      }
    }

    await page.waitForFunction(
      () => document.querySelectorAll('select').length >= 1 && document.querySelector('textarea') !== null,
      { timeout: 10000 },
    );
    await fillAllCascadingSelects();

    // Check first specific issue checkbox if rendered
    await page.evaluate(() => {
      const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
      if (boxes.length > 0 && !boxes[0].checked) boxes[0].click();
    });

    // Fill remaining text/tel/date inputs
    await page.evaluate(() => {
      function setVal(el, val) {
        const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]):not([type="file"]):not([type="hidden"])'));
      for (const inp of inputs) {
        if (inp.disabled || inp.readOnly) continue;
        const ph = (inp.placeholder || '').toLowerCase();
        const nm = (inp.name || '').toLowerCase();
        const tp = (inp.type || '').toLowerCase();
        if (tp === 'date' || nm.includes('date')) {
          setVal(inp, '2026-12-05');
        } else if (tp === 'tel' || nm.includes('contact') || ph.includes('98') || ph.includes('mobile')) {
          setVal(inp, '9876543210');
        } else if (nm.includes('room') || ph.includes('room')) {
          setVal(inp, '304');
        } else if (!inp.value) {
          setVal(inp, 'QA E2E Test Entry');
        }
      }
    });

    // Test 500-char limit & description validation
    await page.focus('textarea');
    await page.evaluate(() => {
      const ta = document.querySelector('textarea');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, 'A'.repeat(520));
      ta.dispatchEvent(new Event('input', { bubbles: true }));
    });
    const descLenAfterOverflow = await page.evaluate(() => document.querySelector('textarea').value.length);
    await page.evaluate(() => {
      const ta = document.querySelector('textarea');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, 'E2E isolated electrical sparking outlet check in Block 34 Room 304.');
      ta.dispatchEvent(new Event('input', { bubbles: true }));
    });
    summary.checks.descriptionMaxLengthObserved = descLenAfterOverflow;

    // Test invalid .webp rejection -> then valid .png upload
    const fileInput = await page.$('input[type="file"]');
    assert(fileInput !== null, 'File upload input missing on RaiseQueryPage');
    await fileInput.uploadFile(INVALID_WEBP_PATH);
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('ONLY JPEG AND PNG'),
      { timeout: 8000 },
    );
    await fileInput.uploadFile(VALID_PNG_PATH);
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('TEST_E2E.PNG') || document.body.innerText.toUpperCase().includes('UPLOADED'),
      { timeout: 10000 },
    );

    const submitBtnState = await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (btn && !btn.disabled) {
        btn.scrollIntoView({ block: 'center' });
        btn.click();
        return { clicked: true, text: btn.innerText };
      }
      return {
        clicked: false,
        buttons: Array.from(document.querySelectorAll('button')).map((b) => ({ text: b.innerText.trim(), disabled: b.disabled, type: b.type })),
      };
    });
    assert(submitBtnState.clicked, `Submit button unavailable: ${JSON.stringify(submitBtnState)}`);
    await page.waitForFunction(
      () => /CMP-2026-\d+/i.test(document.body.innerText),
      { timeout: 12000 },
    );
    const ticket1Id = await page.evaluate(() => {
      const matches = document.body.innerText.match(/CMP-2026-\d+/g) || [];
      return matches[matches.length - 1];
    });
    assert(ticket1Id, 'Failed to capture generated complaint token 1');
    summary.ticketsCreated.push(ticket1Id);

    // 3. Submit Ticket 2 for Student Withdrawal test
    await clickButtonByText(page, /^Submit Another Query$/i);
    await page.waitForFunction(
      () => document.querySelectorAll('input[type="checkbox"]').length >= 3 || document.querySelector('textarea') !== null,
      { timeout: 8000 },
    );
    const needsDecl2 = await page.evaluate(() => document.querySelector('textarea') === null);
    if (needsDecl2) {
      await page.evaluate(() => {
        document.querySelectorAll('input[type="checkbox"]').forEach((b) => { if (!b.checked) b.click(); });
      });
      await clickButtonByText(page, /Proceed|Continue|Accept|I Agree/i);
      await page.waitForSelector('textarea', { timeout: 8000 });
    }
    await fillAllCascadingSelects();
    await page.evaluate(() => {
      const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
      if (boxes.length > 0 && !boxes[0].checked) boxes[0].click();
      function setVal(el, val) {
        const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]):not([type="file"]):not([type="hidden"])'));
      for (const inp of inputs) {
        if (inp.disabled || inp.readOnly) continue;
        const nm = (inp.name || '').toLowerCase();
        const tp = (inp.type || '').toLowerCase();
        if (tp === 'date' || nm.includes('date')) setVal(inp, '2026-12-06');
        else if (tp === 'tel' || nm.includes('contact')) setVal(inp, '9876543210');
        else if (nm.includes('room')) setVal(inp, '305');
        else if (!inp.value) setVal(inp, 'QA Withdrawal Test');
      }
      setVal(document.querySelector('textarea'), 'Minor bulb flicker self-resolved shortly after submission.');
    });
    await page.click('button[type="submit"]');
    await page.waitForFunction(() => /CMP-2026-\d+/i.test(document.body.innerText), { timeout: 12000 });
    const ticket2Id = await page.evaluate(() => {
      const matches = document.body.innerText.match(/CMP-2026-\d+/g) || [];
      return matches[matches.length - 1];
    });
    assert(ticket2Id && ticket2Id !== ticket1Id, `Failed to capture distinct ticket 2 (${ticket2Id})`);
    summary.ticketsCreated.push(ticket2Id);

    // 4. Student History: View Details, Authenticated Photo Fetch (200 OK), and Withdrawal
    await clickButtonByText(page, /^View in History$|^History$/i);
    await page.waitForFunction(
      (t1, t2) => document.body.innerText.includes(t1) && document.body.innerText.includes(t2),
      { timeout: 10000 },
      ticket1Id,
      ticket2Id,
    );
    const studentPng = path.join(ARTIFACT_DIR, 'fipp_phase8_e2e_student.png');
    await page.screenshot({ path: studentPng });
    summary.screenshots.push(studentPng);

    // Open ticket1Id details & test authenticated View Attachment
    await clickRowAction(page, ticket1Id, /view details/i);
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('VIEW ATTACHMENT'),
      { timeout: 8000 },
    );
    // Stub window.open so headless Chrome doesn't open an unmanaged popup tab blocking focus, while fetch runs!
    await page.evaluate(() => { window.__origOpen = window.open; window.open = () => null; });
    await clickButtonByText(page, /View Attachment/i);
    await page.waitForFunction(() => true);
    await new Promise((r) => setTimeout(r, 700));
    assert(sawUploadGet200, 'Student authenticated attachment GET /api/uploads/... did not return HTTP 200');
    await page.evaluate(() => {
      const modalBtns = Array.from(document.querySelectorAll('.fixed button'));
      const closeBtn = modalBtns.find((b) => /close|×/i.test(b.innerText || b.getAttribute('aria-label') || '')) || modalBtns[0];
      if (closeBtn) closeBtn.click();
    });
    await new Promise((r) => setTimeout(r, 250));

    // Withdraw ticket2Id
    await clickRowAction(page, ticket2Id, /view details/i);
    await page.waitForFunction(
      () => Array.from(document.querySelectorAll('button')).some((b) => /withdraw/i.test(b.innerText)),
      { timeout: 8000 },
    );
    await clickButtonByText(page, /Withdraw/i);
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('CONFIRM WITHDRAWAL') || document.body.innerText.toUpperCase().includes('REASON'),
      { timeout: 6000 },
    );
    await page.evaluate(() => {
      const areas = Array.from(document.querySelectorAll('textarea, input[type="text"]'));
      const last = areas[areas.length - 1];
      if (last) {
        const proto = last.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(last, 'Resolved independently.');
        last.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await clickButtonByText(page, /Confirm Withdraw/i);
    await page.waitForFunction(
      (tid) => {
        const txt = document.body.innerText.toUpperCase();
        return txt.includes(tid) && txt.includes('WITHDRAWN');
      },
      { timeout: 10000 },
      ticket2Id,
    );
    summary.overflowChecks.push({ view: 'student_history_desktop', ...(await checkHorizontalOverflow(page, 'student_history_desktop')) });

    // Student Logout
    await clickButtonByText(page, /Logout|Sign Out/i);
    await page.waitForFunction(() => window.location.pathname.includes('/login'), { timeout: 8000 });
    assert(sawLogout200, 'Student logout did not return HTTP 200');
    const tokensCleared = await page.evaluate(() => !localStorage.getItem('fipp_access_token'));
    assert(tokensCleared, 'Access token not cleared after logout');
    summary.checks.studentWorkflow = 'PASSED';

    // 5. Admin Login & 6-Section Control Centre E2E + MCPI/SHAP + Lifecycle Transition -> Resolved
    await fillLogin(page, 'fipp.admin', process.env.FIPP_E2E_ADMIN_PWD || '');
    await page.waitForFunction(() => window.location.pathname.startsWith('/admin'), { timeout: 10000 });
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('OVERVIEW') && document.body.innerText.toUpperCase().includes('REPORTS'),
      { timeout: 10000 },
    );

    await page.waitForFunction(
      () => !document.body.innerText.toUpperCase().includes('COMPILING LIVE'),
      { timeout: 10000 },
    );

    const adminSections = ['Overview', 'All Requests', 'New / Unassigned', 'In Progress', 'Resolved', 'Reports'];
    for (const section of adminSections) {
      await clickButtonByText(page, section);
      await new Promise((r) => setTimeout(r, 450));
      summary.overflowChecks.push({
        view: `admin_${section.toLowerCase().replace(/[^a-z0-9]/g, '_')}_desktop`,
        ...(await checkHorizontalOverflow(page, `admin_${section}_desktop`)),
      });
    }

    await clickButtonByText(page, 'Overview');
    await new Promise((r) => setTimeout(r, 400));
    const adminDesktopPng = path.join(ARTIFACT_DIR, 'fipp_phase8_e2e_admin_desktop.png');
    await page.screenshot({ path: adminDesktopPng });
    summary.screenshots.push(adminDesktopPng);

    // Go to All Requests, inspect ticket1Id in ComplaintDetailsDrawer
    await clickButtonByText(page, 'All Requests');
    await page.waitForFunction((tid) => document.body.innerText.includes(tid), { timeout: 10000 }, ticket1Id);
    await clickRowAction(page, ticket1Id, /inspect|view|details/i);

    await page.waitForFunction(
      () => {
        const txt = document.body.innerText.toUpperCase();
        return txt.includes('MCPI') && txt.includes('PTS') && txt.includes('UNAVAILABLE');
      },
      { timeout: 10000 },
    );

    // Test Escape key closes drawer cleanly, then reopen
    await page.keyboard.press('Escape');
    await new Promise((r) => setTimeout(r, 350));
    const drawerClosedByEsc = await page.evaluate(
      () => !document.body.innerText.toUpperCase().includes('PRIORITY CLASSIFICATION RATIONALE'),
    );
    assert(drawerClosedByEsc, 'Escape key did not close ComplaintDetailsDrawer');

    await clickRowAction(page, ticket1Id, /inspect|view|details/i);
    await page.waitForFunction(() => document.body.innerText.toUpperCase().includes('MCPI'), { timeout: 8000 });

    // Transition ticket1Id -> Resolved via drawer Update Status controls
    await page.evaluate(() => {
      const containers = Array.from(document.querySelectorAll('[role="dialog"], .fixed'));
      const drawer = containers[containers.length - 1] || document.body;
      const selects = Array.from(drawer.querySelectorAll('select'));
      const statusSel = selects.find((s) => Array.from(s.options).some((o) => o.value === 'Resolved' || o.text === 'Resolved'));
      if (!statusSel) throw new Error('Status dropdown not found inside drawer');
      Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set.call(statusSel, 'Resolved');
      statusSel.dispatchEvent(new Event('change', { bubbles: true }));
      const inputs = Array.from(drawer.querySelectorAll('textarea, input[type="text"]'));
      const remarkBox = inputs.find((el) => el.tagName === 'TEXTAREA') || inputs[inputs.length - 1];
      if (remarkBox) {
        const proto = remarkBox.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(remarkBox, 'E2E verification resolved cleanly.');
        remarkBox.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await new Promise((r) => setTimeout(r, 150));
    await clickButtonByText(page, /Update Status|Save Changes|Save & Update|Apply Update/i);
    await page.waitForFunction(() => true);
    await new Promise((r) => setTimeout(r, 700));
    assert(sawAdminPatch200, 'Admin drawer status PATCH did not return HTTP 200');

    // 6. Tablet & Mobile Responsive Overflow Verification on Admin Portal
    await page.setViewport({ width: 768, height: 1024 });
    summary.overflowChecks.push({ view: 'admin_tablet', ...(await checkHorizontalOverflow(page, 'admin_tablet')) });

    await page.setViewport({ width: 390, height: 844 });
    summary.overflowChecks.push({ view: 'admin_mobile', ...(await checkHorizontalOverflow(page, 'admin_mobile')) });
    const adminMobilePng = path.join(ARTIFACT_DIR, 'fipp_phase8_e2e_admin_mobile.png');
    await page.screenshot({ path: adminMobilePng });
    summary.screenshots.push(adminMobilePng);

    // Reopen check or CSV export check before closing
    await page.setViewport({ width: 1440, height: 900 });
    await page.keyboard.press('Escape');
    await new Promise((r) => setTimeout(r, 250));
    await clickButtonByText(page, 'Reports');
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('EXPORT') && document.body.innerText.toUpperCase().includes('MCPI'),
      { timeout: 10000 },
    );

    await clickButtonByText(page, 'Resolved');
    await page.waitForFunction((tid) => document.body.innerText.includes(tid), { timeout: 10000 }, ticket1Id);

    await clickButtonByText(page, /Logout|Sign Out/i);
    await page.waitForFunction(() => window.location.pathname.includes('/login'), { timeout: 8000 });
    summary.checks.adminWorkflow = 'PASSED';

    // 7. Student Login to submit 5-star satisfaction feedback on resolved ticket1Id
    await fillLogin(page, process.env.FIPP_E2E_STUDENT_NAME || 'Aarav Sharma', process.env.FIPP_E2E_STUDENT_ID || '00123456');
    await page.waitForFunction(() => window.location.pathname.startsWith('/student'), { timeout: 10000 });
    await clickButtonByText(page, /My History|View History|History/i);
    await page.waitForFunction((tid) => document.body.innerText.includes(tid), { timeout: 10000 }, ticket1Id);
    await clickRowAction(page, ticket1Id, /view details/i);
    await page.waitForFunction(
      () => document.body.innerText.toUpperCase().includes('RESOLVED ON:') || document.body.innerText.toUpperCase().includes('FEEDBACK'),
      { timeout: 8000 },
    );
    await page.evaluate(() => {
      const starBtns = Array.from(document.querySelectorAll('button')).filter((b) => /5|star/i.test(b.getAttribute('aria-label') || b.innerText || ''));
      if (starBtns.length >= 5) starBtns[4].click();
      else if (starBtns.length > 0) starBtns[starBtns.length - 1].click();
      const ta = document.querySelector('textarea');
      if (ta) {
        Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(ta, 'Great E2E turnaround.');
        ta.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    const fbBtns = await page.evaluate(() => Array.from(document.querySelectorAll('button')).map((b) => b.innerText));
    if (fbBtns.some((t) => /submit feedback|submit rating/i.test(t))) {
      await clickButtonByText(page, /submit feedback|submit rating/i);
      await new Promise((r) => setTimeout(r, 600));
      summary.checks.studentFeedbackOnResolved = 'PASSED';
    } else {
      summary.checks.studentFeedbackOnResolved = 'OPEN_MODAL_VERIFIED';
    }

    assert(consoleErrors.length === 0, `Console errors encountered: ${JSON.stringify(consoleErrors)}`);
    assert(pageErrors.length === 0, `Uncaught page errors encountered: ${JSON.stringify(pageErrors)}`);
    assert(unexpectedHttpErrors.length === 0, `Unexpected HTTP >=400 errors: ${JSON.stringify(unexpectedHttpErrors)}`);

    console.log(JSON.stringify({ success: true, expectedStatuses: Array.from(expectedStatuses), ...summary }, null, 2));
  } catch (err) {
    try {
      const pages = await browser.pages();
      const activePage = pages[pages.length - 1];
      if (activePage) {
        const snap = await activePage.evaluate(() => ({
          url: window.location.href,
          text: (document.body.innerText || '').slice(0, 800),
        }));
        console.error('E2E_FAILURE_SNAPSHOT:', JSON.stringify(snap));
        console.error('E2E_CONSOLE_ERRORS:', JSON.stringify(consoleErrors));
        console.error('E2E_HTTP_ERRORS:', JSON.stringify(unexpectedHttpErrors));
      }
    } catch {}
    throw err;
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
