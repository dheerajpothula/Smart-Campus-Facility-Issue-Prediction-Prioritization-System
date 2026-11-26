# FIPP 2.0 — Phase 9: Final Release Approval, Credential Cleanup & Campus Data Finalisation Report

**Document ID:** FIPP-PHASE9-FINAL-APPROVAL-2026  
**Baseline Tag:** `checkpoint-phase9-start` (`4f0cad01b5bc3bc6f49a523454eee4d891dd3f70`)  
**Final Approval Decision:** **`CONDITIONALLY APPROVED — PREREQUISITES REMAIN`**

---

## 1. Executive Summary

Phase 9 completes the final closeout, security hardening, identity governance, and campus infrastructure data integration for the **FIPP 2.0 (Facility Issue Prediction & Prioritisation)** platform prior to a controlled campus pilot:

1. **Complete Sample Credential Elimination:** All hardcoded demo accounts, sample passwords, default cryptographic salt/JWT fallback literals, frontend autofill shortcuts, and legacy URL auth-bypass hooks have been removed across backend, frontend, legacy rollback modules, scripts, tests, and historical documentation.
2. **Idempotent First-Run Administrator Bootstrap (`fipp.admin`):** Implemented a cryptographically random 20-character temporary password generator, strong password policy (`>= 12` chars with mixed classes), and idempotent bootstrap CLI (`python -m app.bootstrap_admin`) requiring immediate password replacement upon first login.
3. **Authorized Student Identity & Eight-Digit String Validation:** Student authentication now strictly validates trimmed student names and exact eight-digit numeric string IDs (`^\d{8}$`, preserving leading zeroes) against an administrator-provisioned student enrollment registry.
4. **Neutral Structured Campus Block & Floor Reference (`unverified_external_reference`):** Integrated structured block and floor metadata (`Block 3`, `Block 8B`, `Block 27`, `Block 55`, `Block 56`, `Block 57` [8 referenced floors], `University Centre` [8 referenced storeys], `Administrative Block`, `Library`, `Campus Hospital`, and Hostels) with strict server-side cascading validation, zero fabricated floors on unverified blocks, and zero institutional branding or naming anywhere in the codebase.

---

## 2. Repository and Git State

- **Branch:** `main`
- **Safe Checkpoint Tag Created:** `checkpoint-phase9-start` at `4f0cad01b5bc3bc6f49a523454eee4d891dd3f70`
- **Unrelated User Change Preserved:** `docs/empirical_verification_results.json` left strictly untouched.
- **Live Operational Datastore (`smart-campus-facility-prediction/data/processed/complaints.json`):** Verified intact with **10** records (`CMP-2026-010`, `CMP-2026-009`, `CMP-2026-008`, `CMP-2026-001`–`CMP-2026-007`) and exact pre-Phase 9 SHA-256 `99f8d9725ccf5427a2f4286cd848797bdd61a624237ef18b24dcf15669566832`.
- **Phase 9 Final Commit Hash:** Recorded upon commit & remote verification (`git ls-remote origin refs/heads/main`).

---

## 3. Credential Cleanup Results

A full-repository scan inspected Python backend modules, React/TypeScript UI files, legacy Streamlit rollback files, HTML/JS static assets, test suites, helper scripts, JSON stores, and markdown documentation.

| Component / File Group | Audit Findings Removed / Remediated |
|---|---|
| `app/core/config.py` | Removed hardcoded JWT secret and salt fallback constants; non-strict dev/test falls back to ephemeral per-process `secrets` randomness while `pilot`/`production` strictly fails fast unless `FIPP_JWT_SECRET` (>= 32 chars) and `FIPP_AUTH_SALT` (>= 16 chars) are set. |
| `app/core/security.py` | Removed hardcoded sample user store and legacy precomputed hashes; replaced with file-backed `admin_accounts.json` (`FIPP_ADMIN_STORE_FILE`), PBKDF2-HMAC-SHA256 (600,000 iterations, random 16-byte salt), strong password policy, idempotent bootstrap, and `student_registry.json`. |
| `app/auth.py` | Removed legacy in-memory sample user dictionary (`REGISTERED_USERS`) and static `SECRET_KEY`; delegated cleanly to `app.core.security`. |
| `app/static/index.html` & `app/static/js/app.js` | Removed automatic demo `quickLogin(...)`, sample credential buttons, and seeded user table rows. |
| `smart-campus-facility-prediction/app.py`, `src/auth/admin_auth.py`, `dashboard/components/*.py`, `data/processed/credentials_store.json` | Removed URL `?auth=true` login bypass, `_DEFAULT_SALT`, hardcoded administrator hashes, and cleared `credentials_store.json` (`{}`). Legacy Streamlit rollback now authenticates via `admin_accounts.json`. |
| `frontend/src/pages/auth/LoginPage.tsx` | Removed all demo login buttons, demo flags, and sample ID placeholders; implemented Student Portal (Name + 8-digit ID) and Administrator login tabs. |
| `frontend/src/pages/landing/LandingPage.tsx`, `RaiseQueryPage.tsx`, `Footer.tsx`, `app/main.py`, `routes_taxonomy.py`, `taxonomy_service.py`, `intelligence_service.py`, `data_models.py`, `db_models.py`, `complaint_categories.py`, `student_dashboard.py`, `docs/*.md`, `stage2_prompt.txt` | Removed all external institution naming/URLs and redacted legacy sample credentials across documentation and scripts. |
| `tests/*.py`, `smart-campus-facility-prediction/tests/*.py`, `frontend/src/test/*.tsx`, `scripts/*` | Replaced sample account logins with isolated `tmp_path` test fixtures bootstrapping ephemeral accounts dynamically per test run (`tests/helpers.py`). |

---

## 4. Initial Administrator Bootstrap Procedure

1. Run the idempotent setup CLI in the backend virtual environment:
   ```powershell
   .\venv_backend\Scripts\python.exe -m app.bootstrap_admin
   ```
2. On first execution (when `admin_accounts.json` does not exist or `bootstrapped` is `false`), `bootstrap_initial_admin()` generates a cryptographically random 20-character mixed-class password via `secrets.choice` + `secrets.SystemRandom().shuffle`, stores only its 600,000-iteration PBKDF2-HMAC-SHA256 hash (`pbkdf2_sha256$600000$...`), sets `must_change_password: true`, and outputs the one-time temporary password to standard output **once**.
3. Subsequent runs of `python -m app.bootstrap_admin` detect initialization and exit cleanly with `[OK] Administrator bootstrap already initialized for 'fipp.admin'. Existing account was preserved unchanged.` — never regenerating or resetting credentials.
4. Upon first sign-in on `/login` (`POST /api/auth/login`), `fipp.admin` receives `must_change_password: true`: all operational `/api/admin/*` endpoints reject access with HTTP `403`, and `AdminPortalLayout.tsx` locks the UI on a **First-Login Password Update Required** screen calling `POST /api/auth/change-password` until a compliant strong password replaces the temporary credential.

---

## 5. Initial Administrator Identity

- **Username:** `fipp.admin`
- **Display Name:** `FIPP System Administrator`
- **Role:** `admin`
- **First-Login Enforcement:** Mandatory password replacement enforced both server-side (`app/api/deps.py#require_admin`) and client-side (`AdminPortalLayout.tsx`).

---

## 6. One-Time Password Security Confirmation

Confirmed: During Phase 9 execution, `.\venv_backend\Scripts\python.exe -m app.bootstrap_admin` initialized the local `fipp.admin` account (gitignored under `smart-campus-facility-prediction/data/processed/admin_accounts.json`) and displayed the temporary credential **exclusively in Antigravity execution stdout**. No plaintext password was written to source files, JSON stores, documentation, application logs, or Git commits, and an immediate second CLI run confirmed idempotent preservation (`already_initialized`).

---

## 7. Student Identity & Enrollment Design

- **Login Requirements:** Student authentication (`POST /api/auth/student/login`) requires **Student Name** (trimmed text, 2–100 chars with alphabetic content) and **Student ID** (exact eight-digit numeric string, leading zeroes preserved).
- **Authorized Registry Gate:** Credentials are checked strictly against the administrator-provisioned student registry (`smart-campus-facility-prediction/data/processed/student_registry.json`, overridable via `FIPP_STUDENT_REGISTRY_FILE`), initialized empty (`[]`) with zero pre-seeded fake users. Arbitrary format-valid combinations are rejected (`401`).
- **Administrator Provisioning Workflow:** Preserving the exact 6 primary administrator navigation sections (`Overview`, `All Requests`, `New / Unassigned`, `In Progress`, `Resolved`, `Reports`), an authorized administrator can enroll, activate, or deactivate 8-digit students via `GET/POST/PATCH /api/admin/students` and the `Student Registry` modal in `AdminOverviewPage`.

---

## 8. Eight-Digit Student ID Validation Evidence

Verified on both client (`LoginPage.tsx`, `AdminDirectoryModal.tsx`) and server (`StudentLoginRequest`, `StudentProvisionRequest`, `app/core/security.py#validate_student_id`):

- Accepts exact 8-digit strings preserving leading zeroes (e.g., `"00123456"`, `"00009876"` verified in `test_eight_digit_student_id_validation_and_registry_enforcement`, `frontend_phase8.test.tsx`, and `verify_phase9_e2e.mjs`).
- Rejects non-string integer JSON payloads (`12345678`), alphabetic characters (`"1234ABCD"`), spaces (`"0012 345"`), shorter IDs (`"1234567"`), and longer IDs (`"123456789"`) with HTTP `422`.
- Rejects valid-format unprovisioned IDs (`"99887766"`) and name mismatches with HTTP `401`; rejects deactivated student enrollments (`is_active=false`) immediately on both login (`401`) and active sessions (`403`).

---

## 9. Campus Block / Floor Reference Dataset Summary

Stored neutrally in [campus_blocks_reference.json](file:///c:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/data/campus_blocks_reference.json) and managed via [location_service.py](file:///c:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/location_service.py), exposed at `GET /api/taxonomy/hierarchy` and editable by administrators via `GET/PUT /api/admin/locations/blocks*` and the `Blocks & Floors` modal:

| Block ID | Display Name | Category | Floor Count | Floor Status | Verification Status |
|---|---|---|---|---|---|
| `BLK-3` | Block 3 | Academic | `null` | `unknown` | `unverified_external_reference` |
| `BLK-8B` | Block 8B | Academic | `null` | `unknown` | `unverified_external_reference` |
| `BLK-27` | Block 27 | Academic | `null` | `unknown` | `unverified_external_reference` |
| `BLK-55` | Block 55 | Academic | `null` | `unknown` | `unverified_external_reference` |
| `BLK-56` | Block 56 | Academic | `null` | `unknown` | `unverified_external_reference` |
| `BLK-57` | Block 57 | Academic | `8` | `external_reference_8_floors` | `unverified_external_reference` |
| `BLK-UC` | University Centre | Administrative | `8` | `external_reference_8_storeys` | `unverified_external_reference` |
| `BLK-ADM` | Administrative Block | Administrative | `null` | `unknown` | `unverified_external_reference` |
| `BLK-LIB` | Library | Library | `null` | `unknown` | `unverified_external_reference` |
| `BLK-HOSP` | Campus Hospital | Hospital | `null` | `unknown` | `unverified_external_reference` |
| `BLK-BH1` | Boys Hostel 1 | Hostel | `null` | `unknown` | `unverified_external_reference` |
| `BLK-GH1` | Girls Hostel 1 | Hostel | `null` | `unknown` | `unverified_external_reference` |

- **Cascading & Server Validation:** Changing Block in `RaiseQueryPage.tsx` immediately resets Floor and dependent room/location fields; changing Floor resets dependent room/location fields. Server-side validation rejects mismatched block/floor pairs, cross-block floors, missing floors on multi-floor blocks (`Block 57`), and fabricated floors on unknown-floor blocks (`Block 3`), while preserving full readability and analytics compatibility for all 10 existing historical complaint records.

---

## 10. Data Verification Limitations

- All imported block and floor entries remain flagged `unverified_external_reference` pending physical campus estate confirmation.
- Blocks without supported floor counts (`Block 3`, `Block 8B`, `Block 27`, `Block 55`, `Block 56`, `Administrative Block`, `Library`, `Campus Hospital`, `Boys Hostel 1`, `Girls Hostel 1`) intentionally preserve `floor_count: null` and `floors: []` rather than fabricating storeys or basements.
- For `Block 57` and `University Centre`, 8 above-ground floor labels (`Ground Floor` through `Seventh Floor`) reflect the external eight-floor/eight-storey references without inventing unverified basements.
- **Zero institutional names or branding** remain anywhere in application code, JSON datasets, UI text, tests, scripts, or documentation.

---

## 11. Security Review Summary (Part D Verification)

| Control | Verification Result |
|---|---|
| Old sample credentials rejected | Confirmed (`401 Unauthorized` across all legacy IDs/passwords). |
| Admin bootstrap non-repeatable | Confirmed idempotent (`already_initialized: true` preserves existing hash/account). |
| Student registry authorization required | Confirmed (`401` if unprovisioned or name mismatched; `403` if deactivated). |
| 8-digit string Student ID validation | Confirmed frontend + Pydantic `^\d{8}$` string check preserving leading zeroes. |
| RBAC isolation | Confirmed students blocked from `/api/admin/*` (`403`); admins blocked from `/api/student/*` (`403`). |
| Authenticated attachment access | Confirmed Bearer JWT + owner/admin check (`401`/`403` enforced). |
| Logout & refresh revocation | Confirmed both access & refresh tokens revoked atomically on `/api/auth/logout`. |
| Explicit CORS & security headers | Confirmed `CORS_ORIGINS` (no wildcard `*`) + `nosniff`, `DENY`, `strict-origin-when-cross-origin`, `no-store`. |
| Pilot/prod secret fail-fast | Confirmed `FIPP_ENV=pilot` aborts startup when `FIPP_JWT_SECRET` / `FIPP_AUTH_SALT` missing. |
| Server-side Block/Floor validation | Confirmed in `complaint_service.create_complaint()` via `location_service.validate_block_floor_combination()`. |

---

## 12. Automated Regression & Performance Test Results

| Suite | Command | Environment | Result | Timing |
|---|---|---|---|---|
| **Backend Pytest Suites (Phases 1, 4.1, 7, 8, 9, System)** | `.\venv_backend\Scripts\python.exe -m pytest tests/test_backend_phase1.py tests/test_admin_phase4_1_audit.py tests/test_phase7_predictive_intelligence.py tests/test_phase8_qa_suite.py tests/test_phase9_release_gate.py tests/test_system.py -v` | Python 3.13.15, isolated `tmp_path` stores | **43 / 43 PASSED** (0 failed) | `83.58s` |
| **Legacy Streamlit Rollback Suite** | `python -m unittest discover -s smart-campus-facility-prediction/tests -p "test_*.py"` | Python 3.13 + Streamlit 1.66.1 (temp backup/restore of `complaints.json`) | **233 / 233 PASSED** (`OK`) | `21.116s` |
| **Frontend Vitest Suite** | `Set-Location frontend; npm test` | Node + Vitest v5.1.1 + jsdom | **6 files, 43 / 43 PASSED** | `12.58s` |
| **Phase 9 Isolated Benchmarks** | `.\venv_backend\Scripts\python.exe scripts/benchmark_phase8_performance.py` | Isolated temp stores, 500 synthetic scaled records | `GET /api/admin/kpis` (500): **36.05 ms** mean; filtered list (500): **43.62 ms** mean; analytics (500): **81.81 ms** mean; PBKDF2-600k login: **494.19 ms** mean | `100% pass` |

---

## 13. Build and Browser E2E Verification Results

- **TypeScript & Vite Production Build:** `tsc -b && vite build` succeeded cleanly in `1.22s` (`dist/index.html` 0.45 kB, `dist/assets/index-5JC7sFmQ.css` 44.49 kB, `dist/assets/index-BXe3CMMp.js` 476.19 kB).
- **Phase 9 Browser E2E Suite (`scripts/verify_phase9_e2e.mjs` against `vite preview` + `--workers 1` Uvicorn):**
  - **Checks Passed:** Landing compliance & route guards (`PASSED`), initial `fipp.admin` mandatory password change gate (`PASSED`), admin provisioning `00123456` / `Aarav Sharma` (`PASSED`), Block & Floor reference inspection (`PASSED`), student 8-digit leading-zero login & dynamic Block 3 / Block 57 cascade + PNG upload + attachment `200 OK` + logout `200 OK` (`PASSED`), all 6 admin sections + MCPI drawer + status `Resolved` (`PASSED`).
  - **Responsive Layout & Runtime Telemetry:** **10 / 10 zero-overflow checks** across Desktop (`1440×900`), Tablet (`768×1024`), and Mobile (`390×844`); **0 console errors**, **0 uncaught `pageerror`s**, **0 unexpected HTTP `>= 400` responses**.

---

## 14. Final Release Risk Register

| Risk Area | Current Posture & Limitation | Pilot Mitigation / Control |
|---|---|---|
| **JSON Storage & Single-Process Constraint** | File-backed JSON datastore uses in-process `threading.RLock()`. | Enforce Uvicorn `--workers 1`; defer PostgreSQL migration until approved post-pilot. |
| **One-Worker Uvicorn Requirement** | Running `>1` worker risks lock races and lost writes across processes. | Explicitly mandate `--workers 1` in deployment scripts and service unit files. |
| **Backup & Restore Readiness** | No automated cloud backup daemon is bundled inside the repo. | Pilot operations must schedule daily snapshot copies of `complaints.json`, `admin_accounts.json`, `student_registry.json`, `campus_blocks_override.json`, and `uploads/`, verified via test restore. |
| **Secret Management** | Pilot requires externalized `FIPP_JWT_SECRET` and `FIPP_AUTH_SALT`. | `FIPP_ENV=pilot` enforces fail-fast startup rejection if strong secrets are absent. |
| **CORS & HTTPS / Reverse Proxy** | Uvicorn serves plain HTTP locally; trusted browser origin depends on deployment host. | Terminate TLS at Nginx/reverse proxy and set exact `FIPP_CORS_ORIGINS`. |
| **Administrator Provisioning** | Single initial bootstrap account (`fipp.admin`) with mandatory first-login password change. | Operator runs `bootstrap_admin`, stores temp password securely, and rotates immediately on first login. |
| **Student Identity Without Campus SSO** | Validates against admin-provisioned `student_registry.json` (`name` + 8-digit ID) without password/SSO. | Controlled pilot only; restrict cohort enrollment to verified active students; institution SSO deferred to approved post-pilot roadmap. |
| **Data Retention & Privacy Notice** | Operational JSON/uploads persist indefinitely until archive/purge; do **not** claim ISO 27001 or DPDP Act 2023 compliance without formal legal/security audit. | Display accurate campus facility notice; define pilot retention window before launch. |
| **CSV Export & PII** | `/api/admin/reports/export` redacts `student_id`, `student_name`, `contact_number` by default (`redact_pii=true`). | Keep `redact_pii=true` standard for operational sharing; restrict `redact_pii=false` downloads. |
| **Logging & Monitoring** | Standard Uvicorn stdout/stderr logs; no external SIEM/APM bundled. | Route server logs to host log rotation without logging request auth tokens or credentials. |
| **Incident Response & Support** | Pilot support ownership rests with designated Campus Facility Operations & IT leads. | Assign named on-call contact and support escalation channel before onboarding users. |
| **Block / Floor Accuracy** | External reference blocks marked `unverified_external_reference` (`floor_count: null` on 10 blocks). | Campus estate admin verifies/configures blocks via `Blocks & Floors` modal or import API before full rollout. |
| **Capacity Extrapolation Caveat** | Local 500-record `TestClient` benchmarks (<90 ms) **do not prove campus-scale multi-user production capacity**. | Monitor pilot concurrency under `--workers 1` and re-evaluate relational storage before scaling campus-wide. |
| **Rollback Readiness** | Streamlit legacy app remains verified (`233/233`); Phase 9 start checkpoint tagged `checkpoint-phase9-start`. | Switch traffic/process to `start_fipp_streamlit.bat` or revert to `checkpoint-phase9-start` after backing up `data/processed/`. |

---

## 15. Controlled Pilot Deployment Checklist (Preparation Plan Only)

- [ ] **1. Pilot Environment Mode:** Set `FIPP_ENV=pilot`.
- [ ] **2. Secure Secrets:** Provision cryptographically random `FIPP_JWT_SECRET` (>= 32 chars) and `FIPP_AUTH_SALT` (>= 16 chars).
- [ ] **3. HTTPS & Reverse Proxy:** Terminate TLS at reverse proxy forwarding `/api` and `/health` to `127.0.0.1:8000` and serving `frontend/dist/`.
- [ ] **4. Explicit CORS Origins:** Set `FIPP_CORS_ORIGINS` strictly to the HTTPS pilot hostname(s).
- [ ] **5. Single Uvicorn Worker:** Configure process manager with `--workers 1`.
- [ ] **6. Isolated Storage Paths:** Verify persistent write permissions for `complaints.json`, `admin_accounts.json`, `student_registry.json`, `campus_blocks_override.json`, and `uploads/`.
- [ ] **7. Backup & Restore Drill:** Perform and verify a full copy-and-restore drill of JSON stores + `uploads/` prior to pilot opening.
- [ ] **8. Initial Administrator Setup:** Confirm `fipp.admin` initial login + immediate mandatory password rotation completed.
- [ ] **9. Authorized Student Enrollment:** Provision pilot cohort 8-digit student IDs and names via Admin Student Registry.
- [ ] **10. Block & Floor Verification:** Have campus estate admin verify floor counts for pilot buildings.
- [ ] **11. Support Ownership & Escalation:** Document named pilot owner and technical support contact.
- [ ] **12. Incident Response & Rollback Runbook:** Confirm team sign-off on backup-first rollback procedure.
- [ ] **13. Data Retention & User Notice:** Publish pilot data retention duration and facility-operations privacy notice.
- [ ] **14. Pilot Exit Criteria:** Zero Sev-1 data integrity defects, verified backup/restore reliability, admin sign-off on triage usability, and formal decision on relational DB / campus SSO prior to general availability.

---

## 16. Rollback Plan

1. **Snapshot Live Data First:** Copy `smart-campus-facility-prediction/data/processed/` (`complaints.json`, `admin_accounts.json`, `student_registry.json`, `campus_blocks_override.json`) and `uploads/` before any rollback action.
2. **Legacy UI Rollback:** Stop FastAPI/frontend servers and launch legacy Streamlit via `start_fipp_streamlit.bat` (verified `233/233` tests passing, compatible with `complaints.json` and `admin_accounts.json`).
3. **Code Checkpoint Rollback:** Restore working tree from Git tag `checkpoint-phase9-start` (`4f0cad01b5bc3bc6f49a523454eee4d891dd3f70`).

---

## 17. Final Approval Decision

**Decision: `CONDITIONALLY APPROVED — PREREQUISITES REMAIN`**

FIPP 2.0 satisfies all Phase 9 software security, credential hygiene, administrator bootstrap, eight-digit student identity validation, structured neutral campus block/floor integration, automated testing, and responsive browser E2E criteria for a **controlled campus pilot**, conditional on completing the operational prerequisites listed in Section 14 and Section 15 (secrets, HTTPS proxy, `--workers 1`, verified backups, block/floor verification by campus estates, and pilot cohort configuration). Public campus-wide production launch remains contingent on future approved relational database and institutional SSO/directory phases.

---

## 18. Phase 9 Correction / Hotfix: Student Self-Registration & Admin Credential Handover

Following initial Phase 9 review, a targeted hotfix was applied to replace mandatory administrator pre-provisioning for students with **self-declared Student Name + 8-digit Student ID self-registration**, remove any remaining fallback student test identities, and rotate the initial administrator temporary password.

### 18.1 Removal of Default & Fallback Student Credentials

- **Mandatory Pre-Creation Gate Removed:** `POST /api/auth/student/login` no longer requires an administrator to enroll a student beforehand.
- **Hidden Fallbacks Removed:** Removed the residual `"STU-TEST-001"` / `"ADM-TEST-001"` fallbacks in `smart-campus-facility-prediction/src/data/complaints_store.py` (`get_current_student_identity()`) and `smart-campus-facility-prediction/app.py`, cleared residual quick-login helpers/placeholders in `app/static/index.html` and `app/static/js/app.js`, and updated legacy `smart-campus-facility-prediction/dashboard/components/login_page.py` to use the exact 8-digit string ID and self-registration validation rules.
- **Legacy Credential Rejection:** Verified old demo accounts (`STU-2026-001`, `STU101`, `STU-TEST-001`, `ADMIN01`, `student123`) and empty/invalid student strings cannot authenticate.

### 18.2 Student Self-Registration & Eight-Digit ID Validation

- **Strict Server & Client Validation (`app/core/security.py`, `app/models/data_models.py`, `frontend/src/pages/auth/LoginPage.tsx`):**
  - `student_id` must be submitted as a string matching `^\d{8}$` (exact 8 numeric digits `0-9`); leading zeroes (e.g., `00123456`, `00001122`) are preserved end-to-end and integer/alphanumeric/wrong-length values fail with HTTP `422`.
  - `student_name` is trimmed and whitespace-collapsed (`" ".join(name.strip().split())`), rejecting empty strings or strings without alphabetic characters.
- **Case A — New Student ID:** When an unused valid 8-digit `student_id` is submitted, `authenticate_or_register_student()` atomically creates and persists a profile in `student_registry.json` (`registration_source: "self_registered"`, `identity_verification: "self_declared_unverified"`, `registered_at`, `last_login_at`), sets `is_new_registration: true`, and issues signed JWT access/refresh tokens immediately.
- **Case B — Existing Student ID:** Retrieves the stored record, normalizes submitted vs. stored names (`casefold()` + collapsed whitespace), and authenticates without creating duplicate entries when matching (`is_new_registration: false`).
- **Name Mismatch Handling:** If an existing 8-digit `student_id` is submitted with a non-matching name, login fails with HTTP `409 Conflict` and a generic safe message (without leaking the stored student name or silently overwriting the stored record). Administrators can perform identity name corrections via **Student Profiles → Edit Name** (`PATCH /api/admin/students/{student_id}`) in `AdminDirectoryModal.tsx`.

### 18.3 Student Record Persistence, Ownership & Retrieval

- **JSON-Backed Persistence:** Profiles persist atomically (`tempfile` + `os.replace` under `threading.RLock`) in `student_registry.json`; complaints and queries persist atomically in `complaints.json`. *(FIPP continues using JSON-backed storage rather than claiming relational PostgreSQL persistence.)*
- **Stable `student_id` Linkage & Ownership Isolation:** Every complaint, query (`message_type` in `Grievance`, `Enquiry`, `Assistance`, `Feedback`), location/block/floor selection, inspection availability (`availability_date`, `time_slot`), photo attachment reference, withdrawal, status history entry, resolution closing summary, and 5-star feedback links strictly to JWT-authenticated `student_id` (payload `student_id` overrides are not accepted).
- **Cross-Student Protections:** Students retrieve only their own records via `GET /api/student/complaints`; cross-student ticket retrieval returns `403 Forbidden`, cross-student attachment downloads return `403 Forbidden`, attachment reuse/theft across different `student_id`s is rejected (`400 Bad Request`), and administrators see associated `student_id` and `student_name` in `ComplaintDetailsDrawer.tsx`.
- **Rate Limiting & Enumeration Prevention:** Added sliding-window IP rate limiting (`rate_limit_auth_requests`, 25 requests / 60s) on `/api/auth/login` and `/api/auth/student/login` returning `429 Too Many Requests` on bursts; no public student lookup or enumeration endpoint exists.

### 18.4 Security Limitations of Self-Declared Student Identity

> **IMPORTANT SECURITY DISCLOSURE:** Student self-registration using a self-declared Student Name and 8-digit Student ID is **NOT** independent or university-verified authentication.
> - **Impersonation Risk:** Any individual who knows another student's 8-digit Student ID before first registration—or knows both the Student Name and 8-digit ID after registration—can register or sign in as that student without a password or institutional Single Sign-On (SSO).
> - **Mitigation & Governance:** Both the React login portal (`LoginPage.tsx`) and this approval report explicitly disclose that student identities are self-declared and unverified. Administrator oversight (name correction, account deactivation via `/api/admin/students/{id}`), ownership isolation, rate limiting, and non-enumerating errors reduce automated abuse, but campus SSO / verified student password authentication remains mandatory prior to unmonitored campus-wide production deployment. *(Supersedes Section 15 Item 9 mandatory pre-enrollment note for pilot self-service access.)*

### 18.5 Administrator Credential Rotation & Bootstrap Verification

- Updated `app/core/security.py` and `app/bootstrap_admin.py` to support explicit credential rotation (`--rotate` / `rotate_admin_temporary_password()`) alongside strict idempotency for default `python -m app.bootstrap_admin`.
- Added per-account `token_version` verification in `app/api/deps.py` and `app/api/routes_auth.py` so rotating or updating an administrator password immediately invalidates prior JWT access and refresh tokens.
- Executed `python -m app.bootstrap_admin` (confirmed idempotent preservation) followed by `python -m app.bootstrap_admin --rotate` for `fipp.admin` (`FIPP System Administrator`, role `admin`), invalidating the previously exposed temporary credential, hashing only the new PBKDF2-HMAC-SHA256 digest in gitignored `admin_accounts.json`, enforcing `must_change_password: true`, and delivering the new temporary one-time password solely in execution output (never committed or written into files).

### 18.6 Hotfix Regression Verification Results

- **Focused Backend Hotfix Pytest (`.\venv_backend\Scripts\python.exe -m pytest tests/test_phase9_hotfix_self_registration.py -v`):** **3 / 3 PASSED (`4.96s`)** covering all 16 hotfix acceptance scenarios (new self-registration, normalized existing login, 8-digit & leading-zero validation, duplicate prevention, `409` mismatch & admin name correction, simulated restart persistence, complaints/queries/inspection/remarks/feedback/attachment ownership, `429` auth rate limiting, admin credential rotation + `must_change_password` gate, default credential rejection, and preservation of `CMP-2026-001..010`). Scope: isolated `tmp_path` FastAPI `TestClient` mounting genuine `auth_router`, `taxonomy_router`, `student_router`, `uploads_router`, and `require_admin` gate.
- **Legacy Streamlit Regression (`python -m unittest discover -s smart-campus-facility-prediction/tests -p "test_*.py"`):** **233 / 233 PASSED (`16.056s`, `OK`)** executed with backup/restore preserving live `complaints.json` intact.
- **Frontend Vitest & Production Build (`cd frontend && npm test -- --run && npm run build`):** **43 / 43 PASSED (`6.46s`, 6 files)** and `tsc -b && vite build` **PASSED (`1.01s`)**.
- **Environment Limitation Observed (Host Windows Application Control):** Running the full-app suites importing `app.main` / `routes_admin` (`test_phase9_release_gate.py`, `test_phase8_qa_suite.py`, etc.) or starting full `uvicorn app.main:app` for live browser E2E post-hotfix encountered an OS-level Windows Application Control policy DLL load block on compiled C-extensions inside the virtualenv (`ImportError: DLL load failed while importing _stats_pythran / conversion / interval: An Application Control policy has blocked this file` for `scipy`/`pandas` in `venv_backend` and `C:\Users\pothu\venv`). No attempt was made to bypass host Application Control; non-`scipy`/`pandas` backend modules (`security`, `bootstrap_admin`, `deps`, `routes_auth`, `routes_student`, `routes_uploads`, `routes_taxonomy`, `complaint_service`, `location_service`, `analytics_service`), all 43 frontend unit tests, production Vite build, and all 233 legacy Streamlit tests ran cleanly and passed after the hotfix edits. Re-running the full `app.main` pytest and live browser E2E suite in an Application-Control-cleared environment remains required prior to pilot launch.
