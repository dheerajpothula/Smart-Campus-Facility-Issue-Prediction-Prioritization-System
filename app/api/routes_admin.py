"""
FIPP 2.0 — Administrator Control Centre API Routes.
Provides full operational management across all six sections:
1. Overview & KPIs
2. All Requests (search, filtering, pagination, sorting)
3. New / Unassigned Queue
4. In Progress Queue
5. Resolved Archive
6. Operational Analytics & PII-Redacted CSV Export
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import rate_limit_admin_intelligence, require_admin
from app.models.data_models import (
    AdminComplaintListResponse,
    AdminReopenRequest,
    AdminStatusUpdateRequest,
    AnalyticsReportResponse,
    ComplaintDetail,
    ComplaintIntelligenceResponse,
    DashboardKPIs,
)
from app.services.analytics_service import analytics_service
from app.services.complaint_service import complaint_service
from app.services.intelligence_service import intelligence_service
from app.services.migration_service import migration_service

router = APIRouter(prefix="/api/admin", tags=["Administrator Operations"])
_admin_intel_rate_limit = rate_limit_admin_intelligence(max_requests=60, window_seconds=60)


def _to_admin_detail(record: Dict[str, Any]) -> ComplaintDetail:
    """Normalizes a complaint record and attaches authoritative MCPI details for admins only."""
    norm = complaint_service.normalize_record(record)
    norm["mcpi_details"] = intelligence_service.build_mcpi_explanation(norm)
    return ComplaintDetail(**norm)


# ============================================================================
# 1. OVERVIEW & OPERATIONAL KPIS
# ============================================================================

@router.get("/kpis", response_model=DashboardKPIs)
def get_admin_kpis(current_user: Dict[str, Any] = Depends(require_admin)):
    """Calculates real-time KPI metrics for the Control Centre overview dashboard."""
    kpis = complaint_service.get_kpis()
    return DashboardKPIs(**kpis)


# ============================================================================
# 2. REQUEST MANAGEMENT TABLES (ALL, NEW, IN PROGRESS, RESOLVED)
# ============================================================================

@router.get("/complaints", response_model=AdminComplaintListResponse)
def get_all_complaints(
    search: Optional[str] = Query(None, description="Search across ID, title, description, location"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by building or location"),
    priority: Optional[str] = Query(None, description="Filter by priority tier"),
    squad: Optional[str] = Query(None, description="Filter by assigned department/squad"),
    sort_by: str = Query("Newest first", description="Sorting criteria"),
    limit: int = Query(50, ge=1, le=500, description="Page size limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Retrieves the complete campus complaint ledger with multi-parameter filtering,
    full-text searching, pagination, and sorting.
    """
    records, total_count = complaint_service.get_all_complaints(
        search=search,
        status=status_filter,
        category=category,
        location=location,
        priority=priority,
        squad=squad,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )
    normalized = [_to_admin_detail(r) for r in records]

    return AdminComplaintListResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        records=normalized,
    )


@router.get("/complaints/unassigned", response_model=AdminComplaintListResponse)
def get_unassigned_complaints(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Convenience endpoint: Retrieves New / Unassigned requests requiring initial triage."""
    records, total = complaint_service.get_all_complaints(status="Submitted", limit=limit, offset=offset)
    normalized = [_to_admin_detail(r) for r in records]
    return AdminComplaintListResponse(total_count=total, limit=limit, offset=offset, records=normalized)


@router.get("/complaints/in-progress", response_model=AdminComplaintListResponse)
def get_in_progress_complaints(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Convenience endpoint: Retrieves active work orders in progress or assigned."""
    records, total = complaint_service.get_all_complaints(status=["In Progress", "Assigned"], limit=limit, offset=offset)
    normalized = [_to_admin_detail(r) for r in records]
    return AdminComplaintListResponse(total_count=total, limit=limit, offset=offset, records=normalized)


@router.get("/complaints/resolved", response_model=AdminComplaintListResponse)
def get_resolved_complaints(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Convenience endpoint: Retrieves resolved complaint archives."""
    records, total = complaint_service.get_all_complaints(status="Resolved", limit=limit, offset=offset)
    normalized = [_to_admin_detail(r) for r in records]
    return AdminComplaintListResponse(total_count=total, limit=limit, offset=offset, records=normalized)


# ============================================================================
# 3. COMPLAINT DETAILS, TRIAGE & AUDIT LOGGING
# ============================================================================

@router.get("/complaints/{complaint_id}", response_model=ComplaintDetail)
def get_complaint_by_id(
    complaint_id: str,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """Retrieves full complaint record including complete administrative remarks history."""
    record = complaint_service.get_by_id(complaint_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' was not found.",
        )
    return _to_admin_detail(record)


@router.patch("/complaints/{complaint_id}", response_model=ComplaintDetail)
def update_complaint_status(
    complaint_id: str,
    payload: AdminStatusUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Updates complaint status, technician assignment, and squad allotment.
    Appends an immutable audit entry to the complaint remarks history.
    """
    try:
        updated = complaint_service.update_complaint_status(
            complaint_id=complaint_id,
            new_status=payload.status,
            remarks=payload.remarks,
            admin_id=current_user["id"],
            admin_title=current_user.get("title") or current_user.get("name"),
            allotted_person=payload.allotted_person,
            squad_assigned=payload.squad_assigned,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist reopened complaint safely.",
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist complaint update safely.",
        )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to update: Complaint '{complaint_id}' does not exist.",
        )
    return _to_admin_detail(updated)


@router.post("/complaints/{complaint_id}/reopen", response_model=ComplaintDetail)
def reopen_complaint(
    complaint_id: str,
    payload: AdminReopenRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Reopens a resolved complaint, transitioning status back to 'Under Review'.
    Preserves original resolution date and remarks in audit trail.
    """
    try:
        reopened = complaint_service.reopen_complaint(
            complaint_id=complaint_id,
            remarks=payload.remarks,
            admin_id=current_user["id"],
            admin_title=current_user.get("title") or current_user.get("name"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist reopened complaint safely.",
        )
    if not reopened:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to reopen: Complaint '{complaint_id}' was not found.",
        )
    return _to_admin_detail(reopened)


# ============================================================================
# 4. OPERATIONAL REPORTS & PII-REDACTED EXPORT
# ============================================================================

@router.get("/reports/analytics", response_model=AnalyticsReportResponse)
def get_analytics_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Category filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter"),
    trend_agg: str = Query("Daily", description="Aggregation bucket: Daily, Weekly, Monthly"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Aggregates multi-dimensional operational analytics for executive review.
    Provides time-series incident trends, category Pareto distributions, and aging brackets.
    """
    report = analytics_service.get_analytics_report(
        start_date=start_date,
        end_date=end_date,
        category=category,
        location=location,
        status=status_filter,
        trend_agg=trend_agg,
    )
    return AnalyticsReportResponse(**report)


@router.get("/reports/export")
def export_complaints_csv(
    redact_pii: bool = Query(
        True,
        description="Mask direct student identifiers (student_id, student_name, contact_number); room/location and technician fields remain in operational exports",
    ),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Category filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter"),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Exports filtered complaint ledger records as a standard CSV download (admin-only).
    Masks direct student identifiers (student_id, student_name, contact_number) by default;
    room/location details and technician names remain in operational exports.
    """
    csv_data = analytics_service.export_complaints_csv(
        redact_pii=redact_pii,
        start_date=start_date,
        end_date=end_date,
        category=category,
        location=location,
        status=status_filter,
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fipp_operational_complaints_ledger.csv"},
    )


# ============================================================================
# 7. RELATIONAL MIGRATION DRY-RUN & SAFETY INSPECTION
# ============================================================================

@router.post("/migration/dry-run")
def run_migration_dry_run(current_user: Dict[str, Any] = Depends(require_admin)):
    """
    Executes a non-destructive dry-run migration against an isolated in-memory staging SQLite database.
    Verifies target schema compatibility, relations, foreign keys, and zero token collisions
    without modifying the live primary JSON datastore.
    """
    return migration_service.run_dry_run_migration()


@router.get("/migration/inspect")
def inspect_migration_datastores(current_user: Dict[str, Any] = Depends(require_admin)):
    """
    Audits live primary JSON datastore vs historical CSV dataset,
    detecting token namespaces and collision risks.
    """
    return migration_service.inspect_source_datastores()


# ============================================================================
# 8. PREDICTIVE INTELLIGENCE & MODEL DIAGNOSTICS (ADMIN ONLY)
# ============================================================================

@router.get("/intelligence/overview")
def get_admin_intelligence_overview(current_user: Dict[str, Any] = Depends(require_admin)):
    """
    Returns genuine operational intelligence summary from persisted records along with
    honest ML model registry and SHAP/forecasting availability disclosures.
    """
    return {
        "capabilities": intelligence_service.inspect_ml_capabilities(),
        "operational_analytics": analytics_service.get_analytics_report(),
    }


@router.get("/intelligence/complaint/{complaint_id}", response_model=ComplaintIntelligenceResponse)
def get_complaint_intelligence(
    complaint_id: str,
    current_user: Dict[str, Any] = Depends(_admin_intel_rate_limit),
):
    """
    Returns authoritative rule-based MCPI breakdown and honest SHAP explainability
    status for a single complaint (admin-only, rate-limited).
    """
    record = complaint_service.get_by_id(complaint_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' was not found.",
        )
    return ComplaintIntelligenceResponse(**intelligence_service.get_complaint_intelligence(record))

