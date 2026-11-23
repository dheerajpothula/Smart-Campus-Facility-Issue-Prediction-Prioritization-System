"""
FIPP 2.0 — Machine Learning & Intelligence Telemetry API Routes.
Provides NLP classification, severity prediction, Shapley feature attributions (SHAP),
predictive maintenance forecasts, and MCPI priority weight tuning.
All machine learning calculations execute 100% inside Python.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import require_admin
from app.models.data_models import (
    PriorityWeights,
    ShapExplanationResponse,
)
from app.services.complaint_service import complaint_service
from app.services.ml_service import ml_service

router = APIRouter(prefix="/api/ml", tags=["Machine Learning & Analytics"])


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Complaint text or problem description")
    location: Optional[str] = Field("Campus Main Complex", description="Campus building or facility name")
    facility_type: Optional[str] = Field(None, description="Known facility type if pre-selected")


class CustomShapRequest(BaseModel):
    severity_score: float = Field(60.0, ge=0.0, le=100.0)
    recurrence_score: float = Field(30.0, ge=0.0, le=100.0)
    footfall_score: float = Field(65.0, ge=0.0, le=100.0)
    location_risk_score: float = Field(50.0, ge=0.0, le=100.0)
    impact_score: float = Field(55.0, ge=0.0, le=100.0)
    priority_score: float = Field(50.0, ge=0.0, le=100.0)


@router.post("/analyze")
def analyze_issue(payload: AnalyzeTextRequest):
    """
    Executes the multi-stage machine learning inference pipeline on free-form text:
    - Scikit-Learn TF-IDF NLP classification
    - Severity risk scoring
    - Location footfall calculation
    - Multi-criteria priority indexing (MCPI)
    """
    analysis = ml_service.analyze_text(
        text=payload.text,
        location=payload.location or "Campus Main Complex",
        facility_type=payload.facility_type,
    )
    return {"success": True, "analysis": analysis}


@router.get("/shap/{complaint_id}", response_model=ShapExplanationResponse)
def get_shap_explanation_for_complaint(complaint_id: str):
    """
    Computes exact Shapley feature attributions (phi_i) for a specific complaint,
    satisfying efficiency, symmetry, dummy player, and additivity axioms.
    """
    record = complaint_service.get_by_id(complaint_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' was not found.",
        )

    # Map complaint metrics to feature inputs
    sev = record.get("severity", "Medium")
    sev_map = {"Critical": 90.0, "High": 70.0, "Medium": 45.0, "Low": 20.0}
    sev_score = sev_map.get(sev, 50.0)

    rec_risk = float(record.get("recurrence_risk", 0.35)) * 100.0
    impact = float(record.get("impact_scale", 0.50)) * 100.0
    prio_score = float(record.get("priority_score", 50.0))

    shap_data = ml_service.explain_shap(
        severity_score=sev_score,
        recurrence_score=rec_risk,
        footfall_score=impact,
        location_risk_score=50.0,
        impact_score=impact,
        priority_score=prio_score,
    )
    return ShapExplanationResponse(**shap_data)


@router.post("/shap/custom", response_model=ShapExplanationResponse)
def compute_custom_shap(payload: CustomShapRequest):
    """Computes Shapley feature attributions for arbitrary feature inputs."""
    shap_data = ml_service.explain_shap(
        severity_score=payload.severity_score,
        recurrence_score=payload.recurrence_score,
        footfall_score=payload.footfall_score,
        location_risk_score=payload.location_risk_score,
        impact_score=payload.impact_score,
        priority_score=payload.priority_score,
    )
    return ShapExplanationResponse(**shap_data)


@router.get("/predictive")
def get_predictive_maintenance_forecasts():
    """
    Returns campus-wide Poisson failure forecasts based on historical MTBF
    and footfall cyclical stress modeling.
    """
    return ml_service.get_predictive_forecasts()


@router.get("/metrics")
def get_ml_metrics():
    """Returns genuine Scikit-Learn evaluation metrics computed on test datasets."""
    return ml_service.get_model_metrics()


# Weight tuning router (can also be mounted under /api/settings)
weights_router = APIRouter(prefix="/api/settings", tags=["Settings"])


@weights_router.get("/weights", response_model=PriorityWeights)
def get_priority_weights():
    """Returns the active MCPI priority weighting configuration."""
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
