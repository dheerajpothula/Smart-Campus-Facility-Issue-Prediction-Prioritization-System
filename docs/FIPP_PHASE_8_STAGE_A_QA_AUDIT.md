# FIPP 2.0 — Phase 8 (Stage A): System Audit & QA Execution Plan

**Date:** November 25, 2026  
**Phase:** Phase 8 — Quality Assurance & Release Readiness (Stage A: Read-Only Audit & Plan)  
**Git Branch:** `main`  
**Verified Local & Remote HEAD:** `24804ccc1139beb767bd4c80545c042aa449dd18` (`origin/main`)  
**Existing Checkpoint Tags:** `checkpoint-before-admin-portal-v2`, `checkpoint-phase3-start`, `checkpoint-phase4-start`, `checkpoint-phase7-start`  
**Pre-existing Working Tree Modification:** `docs/empirical_verification_results.json` (unstaged prior to Phase 8; preserved untouched).  
**Code Changes Made in Stage A:** None (read-only inspection).

---

## 1. System Architecture & Workflow Map Audited

### 1.1 Application Layers
- **Frontend SPA (`frontend/`):** React 19 + TypeScript + Vite 8.3 + Tailwind CSS v4 (`src/App.tsx`, `AuthContext.tsx`, `ProtectedRoute.tsx`, `apiClient.ts`).
  - **Public Routes:** `/` ([LandingPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/landing/LandingPage.tsx)), `/login` ([LoginPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/auth/LoginPage.tsx)).
  - **Student Portal (`/student`, `/student/history`):** [StudentPortalLayout.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/StudentPortalLayout.tsx), [RaiseQueryPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/RaiseQueryPage.tsx), [StudentHistoryPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/StudentHistoryPage.tsx).
  - **Administrator Control Centre (6 fixed sections):** [AdminPortalLayout.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminPortalLayout.tsx), [AdminOverviewPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminOverviewPage.tsx), [AdminAllRequestsPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminAllRequestsPage.tsx), [AdminUnassignedPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminUnassignedPage.tsx), [AdminInProgressPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminInProgressPage.tsx), [AdminResolvedPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminResolvedPage.tsx), [AdminReportsPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminReportsPage.tsx), and [ComplaintDetailsDrawer.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/components/admin/ComplaintDetailsDrawer.tsx).
- **Backend REST API (`app/`):** FastAPI (`main.py`, `routes_auth.py`, `routes_taxonomy.py`, `routes_student.py`, `routes_admin.py`, `routes_uploads.py`, `routes_ml.py`) + services (`complaint_service.py`, `analytics_service.py`, `intelligence_service.py`, `upload_service.py`, `taxonomy_service.py`, `migration_service.py`, `ml_service.py`).
- **Persistence & Filesystem Storage (`smart-campus-facility-prediction/data/`):**
  - Live complaints: `processed/complaints.json` (10 persisted records: `CMP-2026-001`–`CMP-2026-010`).
  - Upgraded PBKDF2 hashes: `processed/credentials_store.json` (6 accounts).
  - Revoked JWT list: `processed/revoked_tokens.json` (21 entries).
  - Uploaded attachments: `uploads/` (35 files).
  - Separate historical/demo data: `app/data/campus_complaints_dataset.csv` (5,500 rows) & `app/data/sample_data.py`.
- **Legacy Rollback Option:** Streamlit app (`smart-campus-facility-prediction/app.py`, `start_fipp_streamlit.bat`) backed by `233` `unittest` checks.

---

## 2. Existing Automated Test Coverage vs. Stage B QA Gaps

### 2.1 Already Covered
- **Backend Unit & API Tests:**
  - [tests/test_backend_phase1.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/tests/test_backend_phase1.py) (14 tests): PBKDF2 hashing, login/refresh, basic RBAC, taxonomy (19 categories), student validation/submission/isolation, admin lifecycle, reports/export, upload magic bytes, admin-only ML/SHAP availability, migration dry-run. *(Note: runs against live `complaints.json` and `UPLOAD_DIR`—must NOT be used as-is for non-destructive pilot QA without safeguarding live records.)*
  - [tests/test_admin_phase4_1_audit.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/tests/test_admin_phase4_1_audit.py) (9 isolated `tmp_path` tests): admin RBAC, technician/squad assignment & clearing, closing remarks enforcement, reopen preconditions & history, student rating ownership, attachment IDOR isolation, report calculations & Weekly/Monthly trends, CSV PII masking & filter respect, 3,150-combination MCPI parity with `priority_scoring.py`, KPI/queue definitions.
  - [tests/test_phase7_predictive_intelligence.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/tests/test_phase7_predictive_intelligence.py) (6 isolated `tmp_path` tests): MCPI consistency & thresholds, missing artifact & missing `shap` handling, supported SHAP bundle integration, admin-only intelligence/ML RBAC, rate limiting (`429`), invalid prediction inputs (`422`/`404`), workload & assignment analytics, empty dataset handling.
- **Legacy Streamlit Suite:** `smart-campus-facility-prediction/tests/` (233 `unittest` tests).
- **Frontend Unit/Component Tests (`jsdom` with mocked services):**
  - `frontend_phase2.test.tsx` (10), `frontend_phase3.test.tsx` (9), `frontend_phase4.test.tsx` (8), `frontend_phase4_1_audit.test.tsx` (5), `frontend_phase7.test.tsx` (5) — 37 total Vitest specs.

### 2.2 What Still Needs Testing in Stage B (Isolated QA Suite + Live E2E)
1. **Authentication Edge Cases:** Expired JWT (`exp` in past), malformed/tampered JWT signature, revoked access token after `logout`, refresh token reuse after `logout`, suspended/inactive user (`is_active=False`), unauthenticated direct navigation to `/student`, `/student/history`, and all 6 `/admin/*` routes.
2. **Student Workflow Defects & Edge Cases:**
   - **Defect found in audit ([StudentHistoryPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/StudentHistoryPage.tsx#L429-L436)):** Attachment link uses `<a href={uploadService.getPhotoUrl(...)} target="_blank">` without JWT `Authorization` header, which causes `401 Unauthorized` against `/api/uploads/{filename}`!
   - **Defect found in audit ([StudentHistoryPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/StudentHistoryPage.tsx#L467)):** Checks `selectedTicket.resolution_date` instead of backend's `selectedTicket.resolved_at`, hiding the resolution date in the student modal.
   - **Defect found in audit ([uploadService.ts](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/services/uploadService.ts#L21)):** Client `validMimes` allows `'image/webp'`, whereas backend `upload_service.py` only permits PNG and JPEG magic bytes.
   - Verify full Student journey in live browser: 3 declarations -> 4-tier cascading taxonomy -> building/sub-block/room -> phone/date/slot -> 500-char counter -> valid image upload + invalid file rejection -> token generation -> history view -> attachment retrieval -> withdrawal -> feedback on resolved ticket.
3. **Upload & API Input Security:** Oversized (>10MB) upload rejection, empty 0-byte upload, path traversal (`..%2F`) on `GET /api/uploads/{filename}`, oversized description (>500 chars), invalid date formats/past dates, invalid status strings, error responses free of stack traces/internal filesystem paths.
4. **Complaint Lifecycle & Storage Integrity:**
   - Valid transitions (`Submitted → Under Review → Assigned → In Progress → Resolved`, reopening `Resolved → Under Review`, terminal `Withdrawn`).
   - **Gap found in audit ([complaint_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/complaint_service.py#L434-L478)):** `PATCH /api/admin/complaints/{id}` currently permits transitioning *out* of terminal `Withdrawn` or directly overwriting `Resolved` without `POST /reopen` (preserving prior resolution fields).
   - **Gap found in audit ([complaint_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/complaint_service.py#L110-L123)):** `_save_records()` silently swallows exceptions (`except Exception: pass`) on fallback write instead of raising an error if persistence fails.
   - Persistence across backend restart (fresh `ComplaintService` re-instantiation), concurrent multi-thread updates inside single process, and token uniqueness under concurrent submissions.
5. **Broken Legacy Dataset Route ([app/main.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/main.py#L174)):** `POST /api/admin/dataset/upload` calls non-existent `campus_db.import_custom_csv(csv_text)` instead of `campus_db.validate_and_replace_csv(contents)` (`AttributeError` at runtime).
6. **Performance & Load Baseline:** Measure actual API latencies, 500-record list/search/analytics response times (in isolated `tmp_path`), upload latency, frontend load/TTFB, and process RSS memory.

---

## 3. Security, Privacy & Data-Integrity Risks Classified

| Severity | Finding & Evidence | Pilot Impact & Stage B Action |
|---|---|---|
| **Critical / Pilot Blocker (unless env-configured)** | **Default Fallback Secrets (`app/core/config.py#L16-L25`):** Hardcoded default `JWT_SECRET_KEY` and `DEFAULT_AUTH_SALT` when `FIPP_JWT_SECRET` / `FIPP_AUTH_SALT` env vars are unset. | Document as mandatory pilot env config; add startup warning / deployment checklist check (do not silently break local tests). |
| **High** | **Wildcard CORS with Credentials (`app/main.py#L43-L49`):** `allow_origins=["*"]` combined with `allow_credentials=True`. | Restrict default `allow_origins` to configured `CORS_ORIGINS` (explicit localhost/dev origins without `"*"` when `allow_credentials=True`), configurable via `FIPP_CORS_ORIGINS`. |
| **High** | **Demo Autofill Credentials in Frontend (`LoginPage.tsx#L102-L130`):** Hardcoded `legacy-admin-id` / `[redacted-legacy-credential]` and `legacy-student-id` / `[redacted-legacy-credential]` quick-fill buttons in client bundle. | Gate behind `import.meta.env.PRODUCTION_LOGIN_MODE !== 'false'` (or explicit pilot env flag) and document mandatory disabling for any network pilot. |
| **High** | **Broken Authenticated Student Photo View (`StudentHistoryPage.tsx#L429-L436`):** Plain `<a href>` omits JWT Bearer token → `401 Unauthorized` when students view uploaded photos. | Fix in Stage B using authenticated `fetch` + `Blob` URL (matching `ComplaintDetailsDrawer.tsx`) and add Vitest + E2E coverage. |
| **High** | **Single-Process JSON Persistence & Silent Write Failure (`complaint_service.py#L97-L123`):** `threading.RLock` only protects 1 process (`--workers 1`); `_save_records` swallows disk write errors; `revoked_tokens.json` grows unboundedly. | Raise persistence error instead of `pass` on failed write; guard terminal `Withdrawn` transitions; document `--workers 1` constraint and JSON concurrency/retention limits honestly (no silent DB migration in Phase 8). |
| **Medium** | **Overstated Compliance Claims in Footer (`Footer.tsx#L22-L28`):** Displays `"ISO 27001 Aligned"` and `"DPDP Act 2023 Compliant"` without formal legal/audit certification. | Replace in Stage B with truthful operational privacy wording (`"Role-Based Access Control"` / `"PBKDF2 & JWT Session Security"`). |
| **Medium** | **Refresh Token Not Revoked on Logout (`routes_auth.py#L72-L110`):** `logout` revokes access token only; `refresh` endpoint doesn't check revocation of refresh token. | Support optional `refresh_token` revocation on logout and enforce `is_token_revoked` check in `refresh_access_token`. |
| **Medium** | **Missing Security Response Headers (`app/main.py`):** Missing `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`. | Add lightweight FastAPI middleware setting standard security headers. |
| **Medium** | **Client/Server Upload Mime Drift & Dataset Upload Bug (`uploadService.ts#L21`, `app/main.py#L174`):** `uploadService.ts` allows `image/webp` while server rejects it; `upload_dataset_csv` calls missing `import_custom_csv`. | Align `uploadService.ts` to PNG/JPEG only; fix `upload_dataset_csv` to call `validate_and_replace_csv(contents)` or verify cleanly. |
| **Low** | **`StudentHistoryPage.tsx#L467` Resolution Date Field Mismatch & `LandingPage.tsx#L206` Wording:** Student modal checks `resolution_date` instead of `resolved_at`; Landing card describes live intake as running Scikit-Learn NLP. | Fix `resolved_at` display in `StudentHistoryPage.tsx`; clarify Landing card wording accurately. |

---

## 4. Browser, Device & Deployment-Readiness Coverage

- **Browser Viewports Required in Stage B:**
  - Desktop: `1440 × 900`
  - Tablet: `768 × 1024`
  - Mobile: `390 × 844`
- **Flows to Verify Live (Unmocked Uvicorn + Vite Preview):**
  - Public Landing -> unauthenticated redirect on `/student` and `/admin` -> invalid login error -> Student login -> Raise a Query (declarations, 4-tier cascade, 500-char limit, valid/invalid image upload, submission token) -> Student History (modal, authenticated photo view, withdrawal, feedback) -> Logout -> Admin login -> all 6 Admin sections -> Drawer -> MCPI breakdown -> SHAP unavailable -> Reports & PII-redacted CSV export -> Logout.
  - Verify `0` console errors, `0` `pageerror`, `0` unexpected HTTP `>= 400`, `0` horizontal overflow, keyboard accessibility (`Escape` closes drawer/modal, labeled form inputs).
- **Deployment & Rollback Gaps to Verify/Document:**
  - `FIPP_JWT_SECRET`, `FIPP_AUTH_SALT`, `FIPP_CORS_ORIGINS`, `VITE_API_BASE_URL`, `PRODUCTION_LOGIN_MODE`.
  - Production serving strategy (built `frontend/dist` behind HTTPS reverse proxy vs Vite dev/preview), single-worker Uvicorn (`--workers 1`) requirement for JSON store, backup/restore verification of `complaints.json`, `credentials_store.json`, and `uploads/`, and Streamlit rollback (`start_fipp_streamlit.bat` on port `8501`).

---

## 5. Proposed Stage B Test Commands

1. **Isolated Phase 8 QA + Regression Pytest:**
   `.\venv_backend\Scripts\python.exe -m pytest tests/test_admin_phase4_1_audit.py tests/test_phase7_predictive_intelligence.py tests/test_phase8_qa_suite.py -v`
   *(Plus safeguarded/restored run of `tests/test_backend_phase1.py` and `scripts/empirical_phase1_verification.py` against a backed-up or `tmp_path`-isolated copy so live `complaints.json` and `uploads/` are never polluted.)*
2. **Legacy Streamlit Rollback Suite:**
   `python -m unittest discover -s smart-campus-facility-prediction/tests -p "test_*.py"`
3. **Frontend Vitest & Production Build:**
   `Set-Location frontend; npm test; npm run build`
4. **Live Browser E2E Verification & Performance Benchmark:**
   `.\venv_backend\Scripts\python.exe scripts/benchmark_phase8_performance.py`
   `node scripts/verify_phase8_e2e.js`

---

## 6. Release-Blocking Criteria

A **READY FOR CONTROLLED PILOT** or **CONDITIONALLY READY** decision in Stage B requires:
1. **Zero Critical defects** in student isolation, admin RBAC, upload security, complaint lifecycle persistence, or MCPI/analytics accuracy.
2. **All verified functional & security defects** found in Stage A (e.g., student photo attachment `401`, student modal `resolved_at`, terminal `Withdrawn` guard, silent JSON write failure, CORS wildcard + credentials, DPDP overclaim in Footer, security headers) resolved and regression-tested—or explicitly documented with mitigations if architectural/env-level (e.g., `--workers 1`, env secrets, disabling demo login buttons in pilot).
3. **100% pass rate** across Backend QA/Regression suites, Legacy Streamlit suite (`233/233`), Frontend Vitest + `tsc -b && vite build`, and Live Browser E2E across Desktop, Tablet, and Mobile.
4. **Live operational data (`complaints.json`) preserved intact** after all test runs.

---

**Stage A Complete — Ready for Review.** Awaiting approval to proceed with **Phase 8 Stage B (Verification Execution, Defect Fixes, Performance Benchmarks & Final Release Readiness Report)**.
