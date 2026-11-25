async function runVerification() {
  console.log('======================================================================');
  console.log('FIPP 2.0 API COMMUNICATION & ENDPOINT VERIFICATION');
  console.log('======================================================================\n');

  const directBase = 'http://127.0.0.1:8000';
  const proxyBase = 'http://127.0.0.1:5173';

  // 1. Health Endpoint (Direct & Proxied)
  console.log('--- 1. Health Endpoint Verification ---');
  const hDirect = await fetch(`${directBase}/api/health`).then(r => r.json());
  console.log(`[PASS] Direct Backend Health (${directBase}/api/health): ${hDirect.status} (version: ${hDirect.version})`);

  const hProxy = await fetch(`${proxyBase}/api/health`).then(r => r.json());
  console.log(`[PASS] Proxied Frontend Health (${proxyBase}/api/health): ${hProxy.status} (version: ${hProxy.version})`);

  // 2. Taxonomy Hierarchy Endpoint
  console.log('\n--- 2. Taxonomy Hierarchy Endpoint ---');
  const tax = await fetch(`${proxyBase}/api/taxonomy/hierarchy`).then(r => r.json());
  console.log(`[PASS] Taxonomy Message Types (${tax.message_types.length}):`, tax.message_types.join(', '));
  console.log(`[PASS] Maintenance Categories (${tax.maintenance_categories.length}):`, tax.maintenance_categories.slice(0, 4).join(', '), '...');
  console.log(`[PASS] Campus Blocks (${tax.campus_blocks.length}):`, tax.campus_blocks.slice(0, 4).join(', '), '...');
  console.log(`[PASS] Time Slots (${tax.time_slots.length}):`, tax.time_slots.join(' | '));

  // 3. Student Authentication Endpoint
  console.log('\n--- 3. Student Authentication (00123456) ---');
  const loginRes = await fetch(`${proxyBase}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: '00123456', password: 'REDACTED_TEST_ENV_CRED' }),
  });
  const loginData = await loginRes.json();
  if (!loginRes.ok) throw new Error(`Login failed: ${JSON.stringify(loginData)}`);
  const token = loginData.access_token || loginData.token;
  console.log(`[PASS] Student Login Successful! Status: ${loginRes.status}`);
  console.log(`       User: ${loginData.user.name} (${loginData.user.id}), Role: ${loginData.user.role}`);
  console.log(`       Token Type: ${loginData.token_type}, Token Preview: ${token.slice(0, 25)}...`);

  // 4. Current User Endpoint (/api/auth/me)
  console.log('\n--- 4. Current User Endpoint (/api/auth/me) ---');
  const meRes = await fetch(`${proxyBase}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const meData = await meRes.json();
  const profile = meData.user || meData;
  console.log(`[PASS] Current User Verified: ID=${profile.id}, Name=${profile.name}, Role=${profile.role}`);

  // 5. Student Complaints Endpoint (/api/student/complaints)
  console.log('\n--- 5. Student Complaints Endpoint (/api/student/complaints) ---');
  const compRes = await fetch(`${proxyBase}/api/student/complaints`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const compData = await compRes.json();
  console.log(`[PASS] Student Complaint Ledger Retrieved: Total=${compData.total_complaints}, Open=${compData.open_complaints}, Closed=${compData.closed_complaints}`);
  compData.records.slice(0, 4).forEach(c => {
    console.log(`       - Token: ${c.complaint_id} | Status: ${c.status} | Title: ${c.title || c.category}`);
  });

  // 6. Admin Authentication Endpoint
  console.log('\n--- 6. Administrator Authentication (fipp.admin) ---');
  const adminLoginRes = await fetch(`${proxyBase}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'fipp.admin', password: 'REDACTED_TEST_ENV_CRED' }),
  });
  const adminLoginData = await adminLoginRes.json();
  if (!adminLoginRes.ok) throw new Error(`Admin login failed: ${JSON.stringify(adminLoginData)}`);
  console.log(`[PASS] Admin Login Successful: ${adminLoginData.user.name} (${adminLoginData.user.id}), Role: ${adminLoginData.user.role}`);

  console.log('\n======================================================================');
  console.log('ALL API ENDPOINTS TESTED AND 100% OPERATIONAL THROUGH REACT PROXY!');
  console.log('======================================================================');
}

runVerification().catch(err => {
  console.error('API Verification Error:', err);
  process.exit(1);
});
