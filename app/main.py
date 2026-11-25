"""
FastAPI Application for FIPP 2.0 — Facility Issue Prediction & Prioritization.
Provides RESTful APIs with strict Role-Based Access Control (RBAC):
- Secure Authentication with OWASP PBKDF2-HMAC-SHA256 & signed JWTs
- 19-Category LPU RMS Taxonomy Hierarchy API
- Student Portal APIs (strictly isolated to authenticated student identity)
- Administrator Control Centre APIs (All 6 approved sections, remarks audit trail, reopening)
- Secure File Upload validation (magic bytes, 10MB limit, raster check)
- Real Scikit-Learn NLP, Severity, SHAP, and Predictive Maintenance APIs
- Preserves backward compatibility for existing prototypes and Streamlit integration.
"""
import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import CORS_ORIGINS, PRIMARY_JSON_DATA_FILE
from app.api.routes_auth import router as auth_router
from app.api.routes_taxonomy import router as taxonomy_router
from app.api.routes_student import router as student_router
from app.api.routes_admin import router as admin_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_ml import router as ml_router, weights_router
from app.api.deps import require_admin
from app.services.complaint_service import complaint_service
from app.services.intelligence_service import intelligence_service
from app.services.taxonomy_service import taxonomy_service
from app.services.ml_service import ml_service
from app.data.database import campus_db
from app.data.sample_data import DEMO_LOCATIONS, CHRONIC_RECURRENCE_DATA
from app.models.data_models import DashboardKPIs

app = FastAPI(
    title="FIPP 2.0 — Facility Issue Prediction & Prioritization API",
    description="Unified Enterprise Backend for FIPP 2.0 with strict RBAC, 19-category taxonomy, and ML services.",
    version="2.0.0",
)

# Enable explicit trusted CORS for React + TypeScript frontend and enterprise clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Attaches defensive HTTP security headers to all responses."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response

# Register Core API Routers
app.include_router(auth_router)
app.include_router(taxonomy_router)
app.include_router(student_router)
app.include_router(admin_router)
app.include_router(uploads_router)
app.include_router(ml_router)
app.include_router(weights_router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ============================================================================
# HEALTH CHECK & SYSTEM DIAGNOSTICS
# ============================================================================

@app.get("/api/health", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint providing service status, version, and datastore integrity."""
    records = complaint_service._load_records()
    caps = intelligence_service.inspect_ml_capabilities()
    return {
        "status": "healthy",
        "service": "fipp-backend-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "datastore": {
            "type": "json",
            "status": "connected" if PRIMARY_JSON_DATA_FILE.is_file() else "missing",
            "record_count": len(records),
        },
        "ml_services": {
            "mcpi_engine": "active",
            "nlp_classifier": "auxiliary_baseline",
            "severity_model": "auxiliary_baseline",
            "shap_explainer": caps["shap_explainability"]["status"],
            "model_artifacts": "present" if caps["shap_explainability"]["model_artifact_present"] else "missing",
        },
    }


# ============================================================================
# TOP-LEVEL COMPATIBILITY & CONVENIENCE ENDPOINTS
# ============================================================================

@app.get("/api/kpi", response_model=DashboardKPIs, tags=["Overview"])
def get_dashboard_kpis(current_user: Dict[str, Any] = Depends(require_admin)):
    """Top-level convenience endpoint returning real-time operational KPIs (admin-only)."""
    return DashboardKPIs(**complaint_service.get_kpis())


@app.get("/api/campus-locations", tags=["Taxonomy"])
def get_campus_locations():
    """Returns campus map coordinates and footfall ratings."""
    return DEMO_LOCATIONS


@app.get("/api/model-metrics", tags=["Machine Learning & Analytics"])
def get_model_metrics(current_user: Dict[str, Any] = Depends(require_admin)):
    """Returns genuine evaluation metrics from demo holdout test partitions (admin-only)."""
    return ml_service.get_model_metrics()


@app.get("/api/predictive-maintenance", tags=["Machine Learning & Analytics"])
def get_predictive_maintenance(current_user: Dict[str, Any] = Depends(require_admin)):
    """Returns predictive maintenance availability status (admin-only)."""
    caps = intelligence_service.inspect_ml_capabilities()
    return {
        "available": False,
        "status": "unavailable",
        "forecasts": [],
        "reason": caps["predictive_forecasting"]["reason"],
        "disclaimer": "Prediction ≠ Confirmed Physical Breakdown. Live failure forecasting requires longitudinal asset telemetry not present in current operational records.",
    }


@app.get("/api/recurring-issues", tags=["Machine Learning & Analytics"])
def get_recurring_issues(current_user: Dict[str, Any] = Depends(require_admin)):
    """Returns recurring issue clusters from live operational records (admin-only)."""
    records = complaint_service._load_records()
    grouped: Dict[str, Dict[str, Any]] = {}
    for r in records:
        norm = complaint_service.normalize_record(r)
        is_rec = bool(norm.get("is_recurring", False)) or float(norm.get("recurrence_risk", 0.0)) >= 0.5
        if not is_rec:
            continue
        key = f"{norm.get('category')} - {norm.get('building')}"
        if key not in grouped:
            grouped[key] = {
                "facility": norm.get("category"),
                "location": norm.get("building"),
                "count": 0,
                "latest_ticket": norm.get("complaint_id"),
                "highest_priority": 0.0,
                "status": norm.get("status"),
            }
        grouped[key]["count"] += 1
        grouped[key]["highest_priority"] = max(grouped[key]["highest_priority"], float(norm.get("priority_score", 0.0)))

    clusters = sorted(grouped.values(), key=lambda x: x["count"], reverse=True)[:25]
    return {
        "source": "live_operational_records",
        "recurring_clusters": clusters,
        "total_recurring_tickets": sum(c["count"] for c in clusters),
    }


# ============================================================================
# HISTORICAL DATASET MANAGEMENT (ADMINISTRATOR UTILITIES)
# ============================================================================

@app.get("/api/admin/dataset/summary", tags=["Dataset Management"])
def get_dataset_summary(admin: Dict[str, Any] = Depends(require_admin)):
    """Provides metadata and statistics for the historical CSV dataset."""
    return campus_db.get_dataset_summary()


@app.post("/api/admin/dataset/upload", tags=["Dataset Management"])
async def upload_dataset_csv(
    file: UploadFile = File(...),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """Admin CSV dataset upload and schema validation."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only standard CSV files are accepted.")

    contents = await file.read()
    res = campus_db.validate_and_replace_csv(contents)
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("error", "CSV validation failed."))
    return res


@app.get("/api/admin/dataset/export", tags=["Dataset Management"])
def export_dataset_csv(admin: Dict[str, Any] = Depends(require_admin)):
    """Admin endpoint to export the active CSV dataset."""
    csv_str = campus_db.export_dataset_csv()
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campus_complaints_export.csv"},
    )


@app.post("/api/admin/dataset/reset", tags=["Dataset Management"])
def reset_dataset_default(admin: Dict[str, Any] = Depends(require_admin)):
    """Resets dataset to canonical default."""
    campus_db.reset_to_default_dataset()
    return {"success": True, "message": "Database reset to initial historical dataset."}


# ============================================================================
# STATIC FILES AND ROOT MOUNT
# ============================================================================

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    """Serves the main application or status response."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FIPP 2.0 — Facility Issue Prediction & Prioritization API is running."}
