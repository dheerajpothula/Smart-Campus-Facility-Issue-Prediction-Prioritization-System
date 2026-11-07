"""
FastAPI Application for FIPP — Facility Issue Prediction & Prioritization.
Provides RESTful APIs with strict Role-Based Access Control (RBAC):
- Authentication (Student / Admin login, session validation)
- Student Portal APIs (isolated to authenticated student's tickets, ticket submission)
- Admin Portal APIs (all complaints management, dataset upload/export/reset, analytics, SHAP, weights)
- Serves the modern web frontend.
"""

import os
import io
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models.data_models import (
    LoginRequest,
    AuthResponse,
    ComplaintSubmission,
    StatusUpdateRequest,
    AdminComplaintUpdate,
    PriorityWeights,
    DashboardKPIs
)
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin,
    require_student,
    REGISTERED_USERS
)
from app.data.database import campus_db
from app.ml.pipeline import pipeline_coordinator
from app.ml.nlp_classifier import nlp_model
from app.ml.severity_model import severity_model
from app.ml.risk_model import risk_model
from app.ml.predictive_engine import predictive_engine
from app.ml.shap_explainer import shap_explainer
from app.ml.priority_engine import active_priority_weights, priority_engine
from app.data.sample_data import DEMO_LOCATIONS, CHRONIC_RECURRENCE_DATA

app = FastAPI(
    title="FIPP — Facility Issue Prediction & Prioritization API",
    description="AI/ML-powered predictive maintenance and intelligent complaint prioritization system with RBAC.",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/login", response_model=AuthResponse)
def login(creds: LoginRequest):
    """Authenticates credentials against registered users and returns signed JWT-like token."""
    user = authenticate_user(creds.username, creds.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your ID/email and password."
        )
    token = create_access_token(user)
    user_sanitized = {k: v for k, v in user.items() if k != "password"}
    return {
        "success": True,
        "token": token,
        "user": user_sanitized,
        "message": f"Welcome back, {user['name']} ({user['role'].capitalize()})"
    }

@app.get("/api/auth/me")
def get_current_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Validates session token and returns active user profile."""
    return {"success": True, "user": current_user}

@app.post("/api/auth/logout")
def logout():
    """Client-side token invalidate response."""
    return {"success": True, "message": "Signed out successfully."}


# ============================================================================
# STUDENT PORTAL ENDPOINTS (STRICTLY ISOLATED TO LOGGED-IN STUDENT)
# ============================================================================

@app.get("/api/student/complaints")
def get_student_complaints(student: Dict[str, Any] = Depends(require_student)):
    """
    Returns only the authenticated student's complaints.
    Prevents access to other students' or campus-wide complaints.
    """
    records = campus_db.get_student_complaints(student["id"])
    return {
        "student_id": student["id"],
        "student_name": student["name"],
        "total_complaints": len(records),
        "complaints": records
    }

@app.get("/api/student/complaints/{complaint_id}")
def get_student_complaint_detail(
    complaint_id: str,
    student: Dict[str, Any] = Depends(require_student)
):
    """Retrieves single complaint detail ONLY if it belongs to the authenticated student."""
    # Admins can inspect any complaint; students only their own
    if student.get("role") == "admin":
        rec = campus_db.get_by_id(complaint_id)
    else:
        rec = campus_db.get_student_complaint_by_id(student["id"], complaint_id)

    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint ticket not found or access unauthorized."
        )
    return rec

@app.post("/api/student/complaints/submit")
def submit_student_complaint(
    submission: ComplaintSubmission,
    student: Dict[str, Any] = Depends(require_student)
):
    """
    Student complaint submission endpoint.
    Automatically assigns student identity, runs AI pipeline, calculates priority,
    and returns ticket confirmation with tracking metadata.
    """
    analysis = pipeline_coordinator.analyze_complaint(submission, active_priority_weights)

    new_record = {
        "reporter_name": student["name"],
        "reporter_role": "Student",
        "student_id": student["id"],
        "facility_type": submission.facility_type or analysis["predicted_category"],
        "facility_category": submission.facility_type or analysis["predicted_category"],
        "building_name": submission.location,
        "location": submission.location,
        "complaint_text": submission.description,
        "description": submission.description,
        "image_url": submission.image_url,
        "predicted_category": analysis["predicted_category"],
        "category_confidence": analysis["category_confidence"],
        "predicted_severity": analysis["predicted_severity"],
        "severity": analysis["predicted_severity"],
        "severity_confidence": analysis["severity_confidence"],
        "recurrence_detected": analysis["recurrence_detected"],
        "recurring_count_30d": analysis["recurrence_count"],
        "recurrence_count": analysis["recurrence_count"],
        "location_risk": analysis["location_risk"],
        "footfall_level": analysis["footfall_level"],
        "footfall_score": analysis["footfall_score"],
        "footfall_index": analysis["footfall_score"],
        "severity_score": analysis["severity_score"],
        "recurrence_score": analysis["recurrence_score"],
        "location_risk_score": analysis["location_risk_score"],
        "impact_score": analysis["impact_score"],
        "expected_impact": analysis["expected_impact"],
        "priority_score": analysis["priority_score"],
        "priority": "Critical" if analysis["priority_score"] >= 80 else ("High" if analysis["priority_score"] >= 65 else ("Medium" if analysis["priority_score"] >= 45 else "Low")),
        "recommended_action": analysis["recommended_action"],
        "points_breakdown": analysis["points_breakdown"],
        "shap_explanation": analysis["shap_explanation"],
        "status": "Open",
        "technician_assigned": "Pending Dispatch",
        "department": analysis["predicted_category"],
        "is_demo": False
    }

    saved = campus_db.add_student_complaint(student["id"], student["name"], new_record)

    return {
        "success": True,
        "message": "Complaint successfully filed and analyzed by AI.",
        "record": saved,
        "ticket_number": saved["complaint_id"],
        "pipeline_analysis": {
            "predicted_category": analysis["predicted_category"],
            "predicted_severity": analysis["predicted_severity"],
            "priority_score": analysis["priority_score"],
            "recommended_action": analysis["recommended_action"]
        }
    }


# ============================================================================
# ADMINISTRATOR PORTAL ENDPOINTS (RESTRICTED TO ADMIN ONLY)
# ============================================================================

@app.get("/api/admin/complaints")
def get_admin_complaints(
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    facility_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    department: Optional[str] = Query(None),
    recurring: Optional[bool] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Returns full dataset complaints with advanced filtering for Administrator."""
    return campus_db.get_admin_complaints(
        search=search,
        location=location,
        facility_type=facility_type,
        severity=severity,
        priority=priority,
        status=status_filter,
        department=department,
        recurring=recurring,
        limit=limit,
        offset=offset
    )

@app.patch("/api/admin/complaints/{complaint_id}")
def update_complaint_admin(
    complaint_id: str,
    payload: AdminComplaintUpdate,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Admin endpoint to update status, department, and assigned technician."""
    updated = campus_db.admin_update_complaint(
        complaint_id=complaint_id,
        status=payload.status,
        department=payload.department,
        technician=payload.technician_assigned
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Complaint record not found.")
    return {"success": True, "message": "Complaint updated successfully.", "record": updated}

@app.delete("/api/admin/complaints/{complaint_id}")
def delete_complaint_admin(
    complaint_id: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Admin endpoint to delete a complaint record."""
    deleted = campus_db.admin_delete_complaint(complaint_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Complaint record not found.")
    return {"success": True, "message": f"Complaint {complaint_id} permanently deleted."}

@app.get("/api/admin/dataset/summary")
def get_dataset_summary(admin: Dict[str, Any] = Depends(require_admin)):
    """Provides dataset statistics, distributions, missing values, duplicates, and preview."""
    return campus_db.get_dataset_summary()

@app.post("/api/admin/dataset/upload")
async def upload_dataset(
    request: Request,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Uploads, validates, and ingests a replacement CSV dataset via raw bytes, text/csv, or JSON."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        csv_str = body.get("csv_content", "")
        content = csv_str.encode("utf-8")
    else:
        content = await request.body()

    if not content or len(content) < 10:
        raise HTTPException(status_code=400, detail="CSV file content is empty.")

    result = campus_db.validate_and_replace_csv(content)
    if not result.get("success"):
        raise HTTPException(
            status_code=422,
            detail={
                "error": result.get("error"),
                "missing_columns": result.get("missing_columns", [])
            }
        )
    return result

@app.get("/api/admin/dataset/export")
def export_dataset(admin: Dict[str, Any] = Depends(require_admin)):
    """Exports current active platform dataset as a CSV file download."""
    csv_str = campus_db.export_dataset_csv()
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campus_complaints_export.csv"}
    )

@app.post("/api/admin/dataset/reset")
def reset_dataset_to_default(admin: Dict[str, Any] = Depends(require_admin)):
    """Resets dataset back to the default 5,500 historical complaint records."""
    return campus_db.reset_to_default_dataset()

@app.get("/api/admin/users")
def get_system_users(admin: Dict[str, Any] = Depends(require_admin)):
    """Lists registered users and roles for User Directory management."""
    sanitized = [
        {k: v for k, v in u.items() if k != "password"}
        for u in REGISTERED_USERS.values()
    ]
    return {"total_users": len(sanitized), "users": sanitized}


# ============================================================================
# SHARED / ANALYTICS ENDPOINTS (CALCULATED FROM ACTIVE 5,500+ DATASET)
# ============================================================================

@app.get("/api/kpi", response_model=DashboardKPIs)
def get_kpi():
    """Returns aggregated campus KPI statistics calculated from the active dataset."""
    return campus_db.get_kpis()

@app.get("/api/complaints")
def get_complaints(
    data_source: str = Query("all", description="Filter source: all, demo_only, live_only"),
    status: Optional[str] = Query(None, description="Status filter: Open, In Progress, Resolved"),
    severity: Optional[str] = Query(None, description="Severity: Low, Medium, High, Critical"),
    facility_type: Optional[str] = Query(None, description="Facility type filter"),
    location: Optional[str] = Query(None, description="Location search query"),
    limit: int = Query(300, ge=1, le=1000)
):
    """Fetches complaints matching filters from active dataset."""
    res = campus_db.get_admin_complaints(
        location=location,
        facility_type=facility_type,
        severity=severity,
        status=status,
        limit=limit
    )
    return res["records"]

@app.get("/api/complaints/{complaint_id}")
def get_complaint_detail(complaint_id: str):
    """Retrieves single complaint with full SHAP explainability breakdown."""
    rec = campus_db.get_by_id(complaint_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Complaint record not found")

    if not rec.get("shap_explanation"):
        explanation = shap_explainer.explain(
            severity_score=float(rec.get("severity_score", 60.0)),
            recurrence_score=float(rec.get("recurrence_score", 30.0)),
            footfall_score=float(rec.get("footfall_score", 65.0)),
            location_risk_score=float(rec.get("location_risk_score", 50.0)),
            impact_score=float(rec.get("impact_score", 55.0)),
            priority_score=float(rec.get("priority_score", 50.0)),
            weights=active_priority_weights
        )
        rec["shap_explanation"] = explanation.model_dump()

    return rec

@app.post("/api/complaints/submit")
def submit_complaint(submission: ComplaintSubmission):
    """
    Direct submission endpoint (for API backwards compatibility).
    """
    analysis = pipeline_coordinator.analyze_complaint(submission, active_priority_weights)
    new_record = {
        "reporter_name": submission.reporter_name or "Campus Complainant",
        "reporter_role": submission.reporter_role or "Student",
        "student_id": submission.student_id or "STU101",
        "facility_type": submission.facility_type or analysis["predicted_category"],
        "facility_category": submission.facility_type or analysis["predicted_category"],
        "location": submission.location,
        "building_name": submission.location,
        "description": submission.description,
        "complaint_text": submission.description,
        "image_url": submission.image_url,
        "predicted_category": analysis["predicted_category"],
        "category_confidence": analysis["category_confidence"],
        "predicted_severity": analysis["predicted_severity"],
        "severity": analysis["predicted_severity"],
        "severity_confidence": analysis["severity_confidence"],
        "recurrence_detected": analysis["recurrence_detected"],
        "recurring_count_30d": analysis["recurrence_count"],
        "location_risk": analysis["location_risk"],
        "footfall_level": analysis["footfall_level"],
        "footfall_score": analysis["footfall_score"],
        "footfall_index": analysis["footfall_score"],
        "severity_score": analysis["severity_score"],
        "recurrence_score": analysis["recurrence_score"],
        "location_risk_score": analysis["location_risk_score"],
        "impact_score": analysis["impact_score"],
        "expected_impact": analysis["expected_impact"],
        "priority_score": analysis["priority_score"],
        "priority": "Critical" if analysis["priority_score"] >= 80 else ("High" if analysis["priority_score"] >= 65 else ("Medium" if analysis["priority_score"] >= 45 else "Low")),
        "recommended_action": analysis["recommended_action"],
        "points_breakdown": analysis["points_breakdown"],
        "shap_explanation": analysis["shap_explanation"],
        "status": "Open",
        "department": analysis["predicted_category"],
        "technician_assigned": "Pending Dispatch",
        "is_demo": False
    }

    saved = campus_db.add_student_complaint(new_record["student_id"], new_record["reporter_name"], new_record)
    return {
        "success": True,
        "message": "Complaint processed and prioritized by AI pipeline.",
        "record": saved,
        "pipeline_analysis": analysis
    }

@app.post("/api/analyze-preview")
def analyze_preview(submission: ComplaintSubmission):
    """Real-time pipeline sandbox for evaluating any text without saving to the database."""
    analysis = pipeline_coordinator.analyze_complaint(submission, active_priority_weights)
    return {
        "success": True,
        "analysis": analysis
    }

@app.patch("/api/complaints/{complaint_id}/status")
def update_complaint_status(complaint_id: str, request: StatusUpdateRequest):
    """Updates ticket status between 'Open', 'In Progress', and 'Resolved'."""
    updated = campus_db.admin_update_complaint(complaint_id, status=request.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Complaint record not found")
    return {"success": True, "record": updated}

@app.get("/api/priority-queue")
def get_priority_queue(limit: int = Query(50, ge=1, le=500)):
    """Returns complaints sorted strictly descending by computed priority score."""
    records = campus_db._records
    sorted_q = sorted(
        records,
        key=lambda x: (x.get("status") != "Resolved", float(x.get("priority_score", 0))),
        reverse=True
    )
    return sorted_q[:limit]

@app.get("/api/risk-intelligence")
def get_risk_intelligence():
    """Returns location risk rankings and vulnerability metrics across campus zones."""
    return risk_model.get_campus_risk_matrix(campus_db._records)

@app.get("/api/recurring-issues")
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
                "status": r.get("status")
            }
        grouped[key]["count"] += 1
        grouped[key]["highest_priority"] = max(grouped[key]["highest_priority"], float(r.get("priority_score", 0.0)))

    return {
        "chronic_highlight": CHRONIC_RECURRENCE_DATA,
        "recurring_clusters": sorted(grouped.values(), key=lambda x: x["count"], reverse=True)[:25],
        "total_recurring_tickets": len(recurring_records)
    }

@app.get("/api/predictive-maintenance")
def get_predictive_maintenance():
    """Returns forward-looking predictive issue-risk forecasts with explicit disclaimers."""
    return {
        "forecasts": predictive_engine.get_forecasts(),
        "methodology": "Historical MTBF Poisson regression & footfall cyclical stress modeling.",
        "disclaimer": "Prediction ≠ Confirmed Physical Breakdown. Algorithmic issue-risk forecast based on historical recurrence cycles & footfall telemetry."
    }

@app.get("/api/campus-locations")
def get_campus_locations():
    """Returns campus map coordinates and footfall ratings."""
    return DEMO_LOCATIONS

@app.get("/api/model-metrics")
def get_model_metrics():
    """Returns genuine evaluation metrics computed on holdout test partitions."""
    return {
        "nlp_classifier": nlp_model.metrics,
        "severity_model": severity_model.metrics,
        "priority_formula": {
            "formula": "Priority = w_sev*Severity + w_rec*Recurrence + w_foot*Footfall + w_loc*LocationRisk + w_imp*Impact",
            "active_weights": active_priority_weights.model_dump(),
            "configurable": True
        }
    }

@app.get("/api/settings/weights")
def get_priority_weights():
    """Returns current active prototype priority weights."""
    return active_priority_weights

@app.post("/api/settings/weights")
def update_priority_weights(weights: PriorityWeights):
    """Updates configurable prototype priority weights and recalculates open ticket priorities."""
    global active_priority_weights
    active_priority_weights = weights

    for r in campus_db._records:
        res = priority_engine.calculate_priority(
            severity_score=float(r.get("severity_score", 50.0)),
            recurrence_score=float(r.get("recurrence_score", 20.0)),
            footfall_score=float(r.get("footfall_score", 60.0)),
            location_risk_score=float(r.get("location_risk_score", 50.0)),
            impact_score=float(r.get("impact_score", 50.0)),
            facility_type=r.get("facility_type", "Water Cooler"),
            predicted_severity=r.get("severity", "Medium"),
            weights=active_priority_weights
        )
        r["priority_score"] = res["priority_score"]
        r["priority"] = "Critical" if res["priority_score"] >= 80 else ("High" if res["priority_score"] >= 65 else ("Medium" if res["priority_score"] >= 45 else "Low"))
        r["expected_impact"] = res["expected_impact"]
        r["recommended_action"] = res["recommended_action"]
        r["points_breakdown"] = res["breakdown"]

    return {
        "success": True,
        "message": "Priority weights updated and all complaint priority scores recalculated.",
        "active_weights": active_priority_weights
    }

@app.post("/api/reset-demo-data")
def reset_demo_data():
    """Resets complaint store back to the pristine historical dataset."""
    campus_db.reset_to_default_dataset()
    return {"success": True, "message": "Database reset to initial 5,500 record dataset."}


# ============================================================================
# STATIC FILES AND ROOT MOUNT
# ============================================================================

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    """Serves the main application."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FIPP — Facility Issue Prediction & Prioritization API is running."}
