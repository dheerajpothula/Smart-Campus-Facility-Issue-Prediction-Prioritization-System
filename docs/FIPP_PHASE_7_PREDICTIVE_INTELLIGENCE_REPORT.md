# FIPP 2.0 — Phase 7: Predictive Intelligence Integration Report

**Date:** November 25, 2026  
**Branch:** `main`  
**Checkpoint Tag:** `checkpoint-phase7-start` (`057f0962d5ce0c4dd92624ae0f47a6f62f8874cc`)  
**Status:** Implemented, Verified & Documented (Stopped before Phase 8)

---

## 1. Initial Architecture Audit

Before modifying any code, a full read-only audit of the backend ML modules, FastAPI endpoints, persisted datastores, React Administrator Control Centre, and Student Portal was performed:

- **Live Operational Datastore:** [complaints.json](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/smart-campus-facility-prediction/data/processed/complaints.json) managed by `ComplaintService` ([complaint_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/complaint_service.py)) with 10 persisted operational tickets (`CMP-2026-001`–`CMP-2026-010`).
- **Separate Historical / Demo Datasets (Excluded from Live Operational Views):** [campus_complaints_dataset.csv](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/data/campus_complaints_dataset.csv) (5,500 synthetic historical records loaded in memory by `CampusDatabase` in [database.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/data/database.py)) and [sample_data.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/data/sample_data.py) (`RAW_DEMO_COMPLAINTS`, `PREDICTIVE_RISK_FORECASTS`, `CHRONIC_RECURRENCE_DATA`).
- **Security Findings Identified & Fixed:** Existing ML and convenience routes (`/api/ml/*`, `GET /api/settings/weights`, `/api/kpi`, `/api/model-metrics`, `/api/predictive-maintenance`, `/api/recurring-issues`) lacked `Depends(require_admin)`, `/api/health` leaked `str(PRIMARY_JSON_DATA_FILE)`, and `/api/ml/*` lacked rate limiting.
- **Student Portal Isolation Verified:** [RaiseQueryPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/RaiseQueryPage.tsx) and [StudentHistoryPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/student/StudentHistoryPage.tsx) expose zero MCPI, SHAP, or administrator analytics.

---

## 2. Existing ML Components Discovered

| Component | Location | Actual State | Disposition in Phase 7 |
|---|---|---|---|
| **Model Artifact Directory** | `smart-campus-facility-prediction/models/` | Contains only `.gitkeep`; zero `.joblib` / `.pkl` / `.onnx` artifacts on disk | **Unavailable** — honestly disclosed |
| **NLP Classifier** | [nlp_classifier.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/ml/nlp_classifier.py) | In-memory `TfidfVectorizer` + `MultinomialNB` trained on 70 hardcoded phrases across 7 legacy categories (`0.4286` holdout accuracy on 14 test samples, `is_demo_evaluation: true`); no saved artifact or SHAP explainer | **Existing & Reused** as locked auxiliary baseline telemetry only (not applied to 19-category LPU RMS tickets) |
| **Severity Model** | [severity_model.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/ml/severity_model.py) | In-memory `TfidfVectorizer` + `MultinomialNB` trained on 32 hardcoded phrases (`0.375` holdout accuracy on 8 test samples, `is_demo_evaluation: true`) + keyword heuristic overrides | **Existing & Reused** as locked auxiliary baseline telemetry only |
| **Prototype Priority Engine** | [priority_engine.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/ml/priority_engine.py) | 5-weight prototype (`0.35 / 0.25 / 0.20 / 0.10 / 0.10`, thresholds `80 / 68 / 45`) divergent from authoritative 4-factor MCPI | **Preserved untouched** for legacy compatibility; NOT used for Control Centre priority |
| **Legacy SHAP Calculator** | [shap_explainer.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/ml/shap_explainer.py) | Pure-Python linear delta calculator (`w_i * (x_i - CAMPUS_BASELINES[feat])`) for the 5-weight prototype; `shap` package is not installed (`find_spec('shap') is None`) | **Not surfaced as ML SHAP** — replaced at API boundary by honest unavailable check |
| **Predictive Engine** | [predictive_engine.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/ml/predictive_engine.py) | Returns static hardcoded `PREDICTIVE_RISK_FORECASTS` from `sample_data.py` | **Not supported by live data** — static forecasts excluded; endpoint reports unavailable |
| **Authoritative MCPI** | [complaint_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/complaint_service.py) | Pure-Python 4-factor rule-based MCPI (`0.35 / 0.25 / 0.25 / 0.15`; `>=75 / >=50 / >=28 / <28`), parity-verified against [priority_scoring.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/smart-campus-facility-prediction/src/prediction/priority_scoring.py) | **Existing & Reused** as primary Control Centre priority intelligence |

---

## 3. Existing MCPI Implementation and Verification

- **Preserved Weights:** `severity = 0.35`, `location_criticality = 0.25`, `recurrence_probability = 0.25`, `impact_population = 0.15`.
- **Preserved Thresholds:** `>= 75.0` Critical, `>= 50.0` High, `>= 28.0` Medium, `< 28.0` Low.
- **Backend Explanation Builder:** Added `IntelligenceService.build_mcpi_explanation()` ([intelligence_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/intelligence_service.py)) reading directly from `ComplaintService.normalize_record()` so component contributions are reported strictly in points (`pts`), accompanied by raw input labels (`severity`, `location_type`, `recurrence_risk`, `impact_scale`), weights, threshold rules, and explicit non-ML labeling (`is_ml_prediction: false`).
- **Verification:** `test_mcpi_calculation_consistency_and_thresholds` and `test_mcpi_parity_with_original_priority_scoring` verify exact scores, point contributions, and parity across all 3,150 combinations.

---

## 4. Existing SHAP Implementation and Verification

- Inspection confirmed that neither the `shap` Python library nor serialized trained ML model artifacts exist in the repository (`smart-campus-facility-prediction/models/` contains only `.gitkeep`).
- Previously, `GET /api/ml/shap/{complaint_id}` called the 5-weight linear delta calculator in `shap_explainer.py` with mismatched inputs (`location_risk_score=50.0` hardcoded, `footfall_score=impact`, and a different severity map), producing values inconsistent with the 4-factor MCPI score.
- **Implemented & Verified:** `IntelligenceService.get_shap_status_for_complaint()` checks disk model artifacts and `importlib.util.find_spec("shap")`. When either is absent, `/api/ml/shap/{complaint_id}`, `/api/ml/shap/custom`, and `/api/admin/intelligence/complaint/{complaint_id}` return `available: false` with empty `features` and the explicit diagnostic reason. When a compatible bundle is supplied (verified via `test_shap_supported_model_and_explainer_bundle`), the endpoint cleanly passes genuine `prediction`, `features`, `base_value`, `output_value`, `model_version`, and `prediction_timestamp`.

---

## 5. Backend API Changes

- **[app/services/intelligence_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/intelligence_service.py):** New service for authoritative MCPI explanation assembly, model artifact/SHAP inspection, and honest capability reporting.
- **[app/api/deps.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/api/deps.py):** Added sliding-window `rate_limit_admin_intelligence(max_requests=60, window_seconds=60)` and `reset_rate_limiter()`.
- **[app/api/routes_ml.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/api/routes_ml.py):** Enforced `Depends(require_admin)` on all routes (`/api/ml/analyze`, `/api/ml/shap/{complaint_id}`, `/api/ml/shap/custom`, `/api/ml/predictive`, `/api/ml/metrics`, `GET /api/settings/weights`, `POST /api/settings/weights`), added rate limiting and text length/whitespace validation (`max_length=2000`), and replaced pseudo-SHAP / static forecasts with honest availability responses.
- **[app/main.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/main.py):** Enforced `Depends(require_admin)` on `/api/kpi`, `/api/model-metrics`, `/api/predictive-maintenance`, and `/api/recurring-issues`; updated `/api/recurring-issues` to inspect live persisted records rather than the 5,500 historical CSV dataset; removed internal filesystem path `PRIMARY_JSON_DATA_FILE` from `/api/health`.
- **[app/models/data_models.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/models/data_models.py):** Added `McpiComponentItem`, `McpiThresholdItem`, `McpiExplanation`, `ShapAvailabilityResponse`, `ComplaintIntelligenceResponse`, `WorkloadSummary`, `AssignmentDistributionItem`, and optional `mcpi_details` on `ComplaintDetail` (populated only in admin routes).
- **[app/services/analytics_service.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/services/analytics_service.py):** Extended `get_analytics_report()` with genuine `workload_summary`, `assignment_distribution`, and `status_distribution` computed strictly from filtered operational records.
- **[app/api/routes_admin.py](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/app/api/routes_admin.py):** Added `_to_admin_detail()` to populate `mcpi_details` exclusively on admin complaint responses, plus `GET /api/admin/intelligence/overview` and `GET /api/admin/intelligence/complaint/{complaint_id}` (`require_admin`, rate-limited).

---

## 6. Frontend Components Implemented

- **[frontend/src/types/index.ts](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/types/index.ts) & [intelligenceService.ts](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/services/intelligenceService.ts):** TypeScript interfaces and API client methods for `/api/admin/intelligence/overview` and `/api/admin/intelligence/complaint/{id}`.
- **[McpiBreakdownCard.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/components/admin/intelligence/McpiBreakdownCard.tsx):** Displays `Rule-Based Scoring (Non-ML)` badge, total MCPI score (`/ 100`), priority badge, weighted component contributions in `pts`, raw inputs, active threshold highlight, and rationale.
- **[ShapExplainabilityCard.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/components/admin/intelligence/ShapExplainabilityCard.tsx):** Renders loading, error, active SHAP attribution, or honest `SHAP Feature Attribution Unavailable` state.
- **[WorkloadIntelligenceStrip.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/components/admin/intelligence/WorkloadIntelligenceStrip.tsx):** Reusable 3-card strip for `MCPI Priority Distribution`, `Operational Workload Balance`, and `Open Queue Aging`.
- **Control Centre Views Updated (6-section navigation preserved untouched):**
  - [AdminOverviewPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminOverviewPage.tsx): Added `WorkloadIntelligenceStrip` and numeric MCPI score alongside priority badges in Recent Requests.
  - [AdminAllRequestsPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminAllRequestsPage.tsx): Displays numeric MCPI score (`priority_score`) alongside priority badges with accessible ARIA label and tooltip.
  - [ComplaintDetailsDrawer.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/components/admin/ComplaintDetailsDrawer.tsx): Integrated `McpiBreakdownCard` and `ShapExplainabilityCard` fetching `/api/admin/intelligence/complaint/{id}`.
  - [AdminReportsPage.tsx](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/frontend/src/pages/admin/AdminReportsPage.tsx): Added `Assignment & Workload Distribution` and `Predictive Intelligence & Model Status` cards.

---

## 7. Operational Analytics Implemented

All analytics are computed server-side in `AnalyticsService.get_analytics_report()` from genuine persisted records in `complaints.json` (never mixing historical CSV or static demo forecasts):

- **MCPI Priority Distribution & Average MCPI Score:** Counts across `Critical`, `High`, `Medium`, `Low`, plus `average_mcpi_score` (`None` / `"Unavailable"` on empty datasets).
- **Operational Workload Balance:** `active_total`, `unassigned_active` (no `allotted_person` and no `department`), `assigned_active`, `high_critical_active`, and `reopened_count`.
- **Assignment Distribution:** Per-assignee/squad `active_count`, `resolved_count`, and `total_count` across filtered records.
- **Open Queue Aging, Trends, Category Pareto, Location Hotspots:** Preserved and filter-aligned (`start_date`, `end_date`, `category`, `location`, `status`, `trend_agg`).

---

## 8. Security and Authorization Verification

- Verified `401 Unauthorized` (unauthenticated) and `403 Forbidden` (student token) across all `/api/admin/intelligence/*`, `/api/ml/*`, `/api/settings/weights`, `/api/kpi`, `/api/model-metrics`, `/api/predictive-maintenance`, and `/api/recurring-issues` endpoints.
- Verified `429 Too Many Requests` rate-limiting behavior on `/api/admin/intelligence/complaint/{id}`.
- Verified `422 Unprocessable Entity` on invalid/whitespace-only prediction text inputs and `404 Not Found` on missing complaint tokens.
- Verified Student Portal (`/api/student/complaints` and `StudentHistoryPage.tsx`) does not expose `mcpi_details`, SHAP, or administrator analytics.
- Verified `/api/health` does not expose internal filesystem paths.

---

## 9. Test Commands and Actual Results

| Suite | Command | Outcome | Notes |
|---|---|---|---|
| **Backend Pytest (Phase 1 + 4.1 + 7)** | `.\venv_backend\Scripts\python.exe -m pytest tests/test_backend_phase1.py tests/test_admin_phase4_1_audit.py tests/test_phase7_predictive_intelligence.py -v` | **29 / 29 Passed** (27.73s) | 14 Phase 1 + 9 Phase 4.1 + 6 Phase 7 tests (`tmp_path` isolated). |
| **Legacy Streamlit Suite** | `python -m unittest discover -s smart-campus-facility-prediction/tests -p "test_*.py"` | **233 / 233 Passed** (25.66s) | Legacy rollback suite intact. |
| **Frontend Vitest Suite** | `cd frontend; npm test` | **37 / 37 Passed** (5/5 files, 3.56s) | Includes 5 new Phase 7 integration tests (`frontend_phase7.test.tsx`). |
| **Frontend Production Build** | `cd frontend; npm run build` | **Passed** (0 errors, 540ms) | `tsc -b && vite build` clean output. |
| **Live Browser E2E Verification** | `node scripts/verify_phase7_browser.js` | **Passed** (15 checks, 0 errors) | Headless Chrome across Desktop, Tablet, and Mobile against live Uvicorn + Vite Preview. |

---

## 10. Browser Verification Results

Executed [verify_phase7_browser.js](file:///C:/Users/pothu/OneDrive/Desktop/ROD(SUPER)/scripts/verify_phase7_browser.js) against live Uvicorn (`127.0.0.1:8000`) and Vite Preview (`127.0.0.1:5173`) at:
- **Desktop:** `1440 × 900`
- **Tablet:** `768 × 1024`
- **Mobile:** `390 × 844`

**Verified:**
- `0` browser console errors, `0` uncaught `pageerror` exceptions, `0` HTTP `>= 400` responses, `0` horizontal layout overflow (`scrollWidth <= innerWidth + 2`) across all 15 viewport/route checks.
- Verified MCPI points breakdown, rule-based labels, and honest SHAP unavailable state in `ComplaintDetailsDrawer`; workload & priority strip in `Overview`; numeric MCPI scores in `All Requests`; assignment workload & model diagnostics in `Reports`; and Student Portal isolation after sign-out and student re-login.

---

## 11. Git Commit and Push Details

- **Pre-Phase 7 Checkpoint Tag:** `checkpoint-phase7-start` (`057f0962d5ce0c4dd92624ae0f47a6f62f8874cc`)
- **Branch:** `main` → `origin/main`
- **Implementation Commit & Remote Hash:** Recorded in the follow-up documentation update commit immediately after pushing `main`.

---

## 12. Capability Classification & Remaining Limitations

- **Implemented and Verified:**
  - Authoritative 4-factor MCPI score, tier, point breakdown (`pts`), weights, and threshold rationale in backend and Admin UI.
  - Genuine operational workload analytics (`MCPI Priority Distribution`, `Operational Workload Balance`, `Open Queue Aging`, `Assignment & Workload Distribution`).
  - Admin-only RBAC, rate limiting, input validation, and filesystem-path sanitization across all ML/intelligence endpoints.
  - Honest `SHAP Feature Attribution Unavailable` and `Live Failure Forecasting Unavailable` UI & API states.
- **Existing and Reused:**
  - `ComplaintService.compute_mcpi()`, `AnalyticsService`, `AdminPortalLayout` 6-section navigation, `ComplaintDetailsDrawer`, and in-memory baseline NLP/Severity holdout metrics.
- **Not Supported by Available Data:**
  - Live failure-window forecasting (`PREDICTIVE_RISK_FORECASTS` in `sample_data.py` is static demo data; live `complaints.json` lacks longitudinal asset failure-cycle telemetry).
  - SLA deadline / estimated-resolution-time predictions (not invented).
- **Not Implemented (With Reasons):**
  - Training/rebuilding ML models or installing `shap` (Phase 7 is strictly an integration phase, not an ML redevelopment phase; no serialized model artifacts or `shap` explainer exist for the 19-category LPU RMS taxonomy).
  - Surfacing `app/ml/shap_explainer.py` as ML SHAP (it is a 5-weight prototype linear delta calculator incompatible with the 4-factor MCPI and not backed by an ML model).
