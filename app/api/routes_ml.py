"""
FIPP 2.0 — Machine Learning & Intelligence Telemetry API Routes.
All intelligence endpoints enforce strict administrator authorization (require_admin)
and input validation. SHAP endpoints return an honest unavailable state when no
compatible trained model artifact or SHAP explainer exists.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import rate_limit_admin_intelligence, require_admin
from app.models.data_models import (
    PriorityWeights,
    ShapAvailabilityResponse,
)
from app.services.complaint_service import complaint_service
from app.services.intelligence_service import intelligence_service
from app.services.ml_service import ml_service

router = APIRouter(prefix="/api/ml", tags=["Machine Learning & Analytics"])

_ml_rate_limit = rate_limit_admin_intelligence(max_requests=60, window_seconds=60)


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000, description="Complaint text or problem description")
    location: Optional[str] = Field("Campus Main Complex", max_length=200, description="Campus building or facility name")
    facility_type: Optional[str] = Field(None, max_length=120, description="Known facility type if pre-selected")


class CustomShapRequest(BaseModel):
    severity_score: float = Field(60.0, ge=0.0, le=100.0)
    recurrence_score: float = Field(30.0, ge=0.0, le=100.0)
    footfall_score: float = Field(65.0, ge=0.0, le=100.0)
    location_risk_score: float = Field(50.0, ge=0.0, le=100.0)
    impact_score: float = Field(55.0, ge=0.0, le=100.0)
    priority_score: float = Field(50.0, ge=0.0, le=100.0)


@router.post("/analyze")
def analyze_issue(
    payload: AnalyzeTextRequest,
    current_user: Dict[str, Any] = Depends(_ml_rate_limit),
):
    """
    Executes the auxiliary baseline NLP & severity pipeline on free-form text (admin-only).
    Clearly tagged as auxiliary 7-class baseline telemetry, distinct from authoritative MCPI.
    """
    cleaned_text = payload.text.strip()
    if len(cleaned_text) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text input must contain at least 3 non-whitespace characters.",
        )
    analysis = ml_service.analyze_text(
        text=cleaned_text,
        location=(payload.location or "Campus Main Complex").strip(),
        facility_type=payload.facility_type,
    )
    analysis["is_auxiliary_baseline"] = True
    return {"success": True, "analysis": analysis}


@router.get("/shap/{complaint_id}", response_model=ShapAvailabilityResponse)
def get_shap_explanation_for_complaint(
    complaint_id: str,
    current_user: Dict[str, Any] = Depends(_ml_rate_limit),
):
    """
    Checks SHAP explainability availability for a specific complaint (admin-only).
    Returns an honest unavailable response when no compatible trained ML model artifact
    or SHAP explainer is present rather than fabricating attributions.
    """
    record = complaint_service.get_by_id(complaint_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' was not found.",
        )

    shap_status = intelligence_service.get_shap_status_for_complaint(record)
    return ShapAvailabilityResponse(**shap_status)


@router.post("/shap/custom", response_model=ShapAvailabilityResponse)
def compute_custom_shap(
    payload: CustomShapRequest,
    current_user: Dict[str, Any] = Depends(_ml_rate_limit),
):
    """Checks custom SHAP explainability availability (admin-only)."""
    shap_status = intelligence_service.get_shap_status_for_complaint("CUSTOM")
    return ShapAvailabilityResponse(**shap_status)


@router.get("/predictive")
def get_predictive_maintenance_forecasts(
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Returns predictive maintenance availability status (admin-only).
    Does not serve static sample forecasts as live operational predictions.
    """
    caps = intelligence_service.inspect_ml_capabilities()
    return {
        "available": False,
        "status": "unavailable",
        "forecasts": [],
        "methodology": None,
        "reason": caps["predictive_forecasting"]["reason"],
        "disclaimer": "Prediction ≠ Confirmed Physical Breakdown. Live failure forecasting requires longitudinal asset telemetry not present in current operational records.",
    }


@router.get("/metrics")
def get_ml_metrics(current_user: Dict[str, Any] = Depends(require_admin)):
    """Returns genuine Scikit-Learn baseline evaluation metrics computed on demo holdout partitions (admin-only)."""
    return ml_service.get_model_metrics()


# Weight tuning router (mounted under /api/settings)
weights_router = APIRouter(prefix="/api/settings", tags=["Settings"])


@weights_router.get("/weights", response_model=PriorityWeights)
def get_priority_weights(current_user: Dict[str, Any] = Depends(require_admin)):
    """Returns the active MCPI priority weighting configuration (admin-only)."""
    return ml_service.get_priority_weights()


@weights_router.post("/weights", response_model=PriorityWeights)
def update_priority_weights(
    weights: PriorityWeights,
    current_user: Dict[str, Any] = Depends(require_admin),
):
    """
    Updates the multi-criteria priority engine weights.
    Requires administrator authorization.
    """
    normalized = ml_service.update_priority_weights(weights)
    return normalized
