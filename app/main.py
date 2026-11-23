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

from app.core.config import PRIMARY_JSON_DATA_FILE
from app.api.routes_auth import router as auth_router
from app.api.routes_taxonomy import router as taxonomy_router
from app.api.routes_student import router as student_router
from app.api.routes_admin import router as admin_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_ml import router as ml_router, weights_router
from app.api.deps import require_admin
from app.services.complaint_service import complaint_service
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

# Enable CORS for future React + TypeScript dev server and enterprise clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {
        "status": "healthy",
        "service": "fipp-backend-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "datastore": {
            "type": "json",
            "path": str(PRIMARY_JSON_DATA_FILE),
            "status": "connected" if PRIMARY_JSON_DATA_FILE.is_file() else "missing",
            "record_count": len(records),
        },
        "ml_services": {
            "nlp_classifier": "active",
            "severity_model": "active",
            "shap_explainer": "active",
            "priority_engine": "active",
        },
    }


# ============================================================================
# TOP-LEVEL COMPATIBILITY & CONVENIENCE ENDPOINTS
# ============================================================================

@app.get("/api/kpi", response_model=DashboardKPIs, tags=["Overview"])
def get_dashboard_kpis():
    """Top-level convenience endpoint returning real-time operational KPIs."""
    return DashboardKPIs(**complaint_service.get_kpis())


@app.get("/api/campus-locations", tags=["Taxonomy"])
def get_campus_locations():
    """Returns campus map coordinates and footfall ratings."""
    return DEMO_LOCATIONS


@app.get("/api/model-metrics", tags=["Machine Learning & Analytics"])
def get_model_metrics():
    """Returns genuine evaluation metrics from holdout test partitions."""
    return ml_service.get_model_metrics()


@app.get("/api/predictive-maintenance", tags=["Machine Learning & Analytics"])
def get_predictive_maintenance():
    """Returns predictive maintenance issue-risk forecasts."""
    return ml_service.get_predictive_forecasts()


@app.get("/api/recurring-issues", tags=["Machine Learning & Analytics"])
def get_recurring_issues():
    """Returns chronic recurring issue profile and pattern timeline from active dataset."""
    records = campus_db._records
    recurring_records = [r for r in records if r.get("recurrence_detected", False)]

    grouped: Dict[str, Dict[str, Any]] = {}
    for r in recurring_records:
        key = f"{r.get('facility_type')} - {r.get('location')}"
        if key not in grouped:
            grouped[key] = {
                "facility": r.get("facility_type"),
                "location": r.get("location"),
                "count": 0,
                "latest_ticket": r.get("complaint_id"),
                "latest_severity": r.get("severity"),
                "highest_priority": 0.0,
                "status": r.get("status"),
            }
        grouped[key]["count"] += 1
        grouped[key]["highest_priority"] = max(grouped[key]["highest_priority"], float(r.get("priority_score", 0.0)))

    return {
        "chronic_highlight": CHRONIC_RECURRENCE_DATA,
        "recurring_clusters": sorted(grouped.values(), key=lambda x: x["count"], reverse=True)[:25],
        "total_recurring_tickets": len(recurring_records),
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
    try:
        csv_text = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded text.")

    res = campus_db.import_custom_csv(csv_text)
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
