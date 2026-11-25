"""
FIPP 2.0 — Phase 7 Predictive Intelligence & Model Registry Service.
Provides:
- Authoritative 4-factor MCPI score explanation (rule-based, non-ML).
- Honest availability verification for trained ML model artifacts and SHAP explainers.
- Genuine model registry diagnostics without fabricating SHAP values or forecasts.
"""
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import SMART_CAMPUS_DIR
from app.ml.nlp_classifier import nlp_model
from app.ml.severity_model import severity_model
from app.services.complaint_service import (
    LOCATION_CRITICALITY_MAP,
    SEVERITY_SCORE_MAP,
    complaint_service,
)

MODELS_ARTIFACT_DIR = SMART_CAMPUS_DIR / "models"
SUPPORTED_ARTIFACT_EXTENSIONS = (".joblib", ".pkl", ".onnx", ".pt", ".h5")

MCPI_THRESHOLDS = [
    {"tier": "Critical", "rule": ">= 75.0", "min_score": 75.0},
    {"tier": "High", "rule": "50.0 – 74.9", "min_score": 50.0},
    {"tier": "Medium", "rule": "28.0 – 49.9", "min_score": 28.0},
    {"tier": "Low", "rule": "< 28.0", "min_score": 0.0},
]


class IntelligenceService:
    """Coordinates authoritative MCPI explanations and honest ML/SHAP status checks."""

    def __init__(self, models_dir: Path = MODELS_ARTIFACT_DIR):
        self.models_dir = Path(models_dir)

    def inspect_ml_capabilities(self) -> Dict[str, Any]:
        """Inspects actual disk model artifacts and installed SHAP dependencies."""
        artifact_files: List[str] = []
        if self.models_dir.is_dir():
            artifact_files = sorted(
                p.name
                for p in self.models_dir.iterdir()
                if p.is_file() and p.suffix.lower() in SUPPORTED_ARTIFACT_EXTENSIONS
            )

        shap_installed = importlib.util.find_spec("shap") is not None
        has_artifacts = len(artifact_files) > 0
        shap_available = has_artifacts and shap_installed

        if not has_artifacts and not shap_installed:
            shap_reason = (
                "No serialized trained ML model artifacts exist in the model registry and "
                "the 'shap' explainability library is not installed."
            )
        elif not has_artifacts:
            shap_reason = (
                "No serialized trained ML model artifacts exist in the model registry "
                "to attach a SHAP explainer."
            )
        elif not shap_installed:
            shap_reason = (
                "The 'shap' explainability library is not installed in the backend environment."
            )
        else:
            shap_reason = "Trained model artifact and SHAP explainer available."

        return {
            "mcpi_engine": {
                "available": True,
                "scoring_type": "Rule-Based Multi-Criteria Priority Index (MCPI)",
                "is_ml_prediction": False,
                "weights": {
                    "severity": 0.35,
                    "location_criticality": 0.25,
                    "recurrence_probability": 0.25,
                    "impact_population": 0.15,
                },
                "thresholds": MCPI_THRESHOLDS,
            },
            "shap_explainability": {
                "available": shap_available,
                "status": "available" if shap_available else "unavailable",
                "reason": shap_reason,
                "model_artifact_present": has_artifacts,
                "artifact_filenames": artifact_files,
                "shap_library_installed": shap_installed,
            },
            "auxiliary_models": {
                "nlp_classifier": {
                    "available_in_memory": nlp_model.pipeline is not None,
                    "model_name": nlp_model.metrics.get("model_name"),
                    "train_samples": nlp_model.metrics.get("train_samples_count"),
                    "test_samples": nlp_model.metrics.get("test_samples_count"),
                    "holdout_accuracy": nlp_model.metrics.get("accuracy"),
                    "weighted_f1": nlp_model.metrics.get("weighted_f1_score"),
                    "classes_count": len(nlp_model.classes_),
                    "is_demo_evaluation": True,
                    "has_persisted_artifact": False,
                    "has_shap_explainer": False,
                    "limitation": (
                        "In-memory 7-class legacy baseline trained on 70 sample phrases; "
                        "not aligned with the 19-category LPU RMS taxonomy."
                    ),
                },
                "severity_model": {
                    "available_in_memory": severity_model.pipeline is not None,
                    "model_name": severity_model.metrics.get("model_name"),
                    "train_samples": severity_model.metrics.get("train_samples"),
                    "test_samples": severity_model.metrics.get("test_samples"),
                    "holdout_accuracy": severity_model.metrics.get("accuracy"),
                    "weighted_f1": severity_model.metrics.get("weighted_f1_score"),
                    "is_demo_evaluation": True,
                    "has_persisted_artifact": False,
                    "has_shap_explainer": False,
                    "limitation": (
                        "In-memory 4-class baseline trained on 32 sample phrases with keyword overrides; "
                        "no persisted artifact or SHAP explainer."
                    ),
                },
            },
            "predictive_forecasting": {
                "available": False,
                "status": "unavailable",
                "reason": (
                    "Live failure-window forecasting is unavailable: the legacy predictive module "
                    "serves static sample records rather than longitudinal asset telemetry from persisted complaints."
                ),
            },
        }

    def build_mcpi_explanation(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds an authoritative, rule-based MCPI breakdown strictly from the backend
        ComplaintService calculation and normalized complaint record.
        """
        norm = complaint_service.normalize_record(record)
        sev = str(norm.get("severity") or "Medium")
        loc_type = str(norm.get("location_type") or "Corridor / Common Area")
        rec_raw = norm.get("recurrence_risk", 0.35)
        imp_raw = norm.get("impact_scale", 0.50)

        try:
            r_val = max(0.0, min(1.0, float(rec_raw)))
        except (TypeError, ValueError):
            r_val = 0.35
        try:
            i_val = max(0.0, min(1.0, float(imp_raw)))
        except (TypeError, ValueError):
            i_val = 0.50

        s_val = SEVERITY_SCORE_MAP.get(sev, 0.4)
        c_val = LOCATION_CRITICALITY_MAP.get(loc_type, 0.5)

        bdown = norm.get("score_breakdown") or {}
        score = float(norm.get("priority_score", 0.0))
        tier = str(norm.get("priority_tier") or "Medium")

        # Resolve matching threshold rule text
        if score >= 75.0:
            threshold_rule = ">= 75.0 (Critical)"
        elif score >= 50.0:
            threshold_rule = "50.0 – 74.9 (High)"
        elif score >= 28.0:
            threshold_rule = "28.0 – 49.9 (Medium)"
        else:
            threshold_rule = "< 28.0 (Low)"

        components = [
            {
                "key": "severity",
                "label": "Severity",
                "weight": 0.35,
                "raw_label": sev,
                "normalized_input": round(s_val, 3),
                "points": round(float(bdown.get("Severity Contribution", round(0.35 * s_val * 100.0, 1))), 1),
                "max_points": 35.0,
            },
            {
                "key": "location_criticality",
                "label": "Location Criticality",
                "weight": 0.25,
                "raw_label": loc_type,
                "normalized_input": round(c_val, 3),
                "points": round(float(bdown.get("Location Criticality Contribution", round(0.25 * c_val * 100.0, 1))), 1),
                "max_points": 25.0,
            },
            {
                "key": "recurrence_probability",
                "label": "Recurrence Risk",
                "weight": 0.25,
                "raw_label": f"{round(r_val * 100)}% risk factor",
                "normalized_input": round(r_val, 3),
                "points": round(float(bdown.get("Recurrence Risk Contribution", round(0.25 * r_val * 100.0, 1))), 1),
                "max_points": 25.0,
            },
            {
                "key": "impact_population",
                "label": "Population Impact",
                "weight": 0.15,
                "raw_label": f"{round(i_val * 100)}% impact scale",
                "normalized_input": round(i_val, 3),
                "points": round(float(bdown.get("Impact Population Contribution", round(0.15 * i_val * 100.0, 1))), 1),
                "max_points": 15.0,
            },
        ]

        return {
            "scoring_type": "Rule-Based Multi-Criteria Priority Index (MCPI)",
            "is_ml_prediction": False,
            "priority_score": round(score, 1),
            "priority_tier": tier,
            "weights": {
                "severity": 0.35,
                "location_criticality": 0.25,
                "recurrence_probability": 0.25,
                "impact_population": 0.15,
            },
            "thresholds": MCPI_THRESHOLDS,
            "components": components,
            "classification_rationale": (
                f"Composite MCPI score of {score:.1f} / 100 maps to '{tier}' under threshold {threshold_rule}. "
                "MCPI is a deterministic rule-based weighted score, not a machine learning prediction."
            ),
        }

    def load_supported_shap_bundle(self) -> Optional[Dict[str, Any]]:
        """
        Loads a serialized ML model artifact and compatible SHAP explainer only when
        both a supported artifact on disk and the 'shap' package are present.
        Returns None when either is missing.
        """
        caps = self.inspect_ml_capabilities()
        shap_cap = caps["shap_explainability"]
        if not shap_cap["available"]:
            return None
        # No serialized LPU RMS model artifacts currently ship in models/
        return None

    def get_shap_status_for_complaint(self, record_or_id: Any) -> Dict[str, Any]:
        """
        Returns SHAP explainability results when a compatible trained model artifact
        and SHAP explainer exist; otherwise returns an honest unavailable state.
        Never fabricates SHAP values or runs mismatched prototype linear formulas.
        """
        if isinstance(record_or_id, dict):
            complaint_id = str(record_or_id.get("complaint_id") or "")
            record = record_or_id
        else:
            complaint_id = str(record_or_id or "")
            record = None

        caps = self.inspect_ml_capabilities()
        shap_cap = caps["shap_explainability"]
        bundle = self.load_supported_shap_bundle()

        if bundle and record is not None and callable(bundle.get("explain_fn")):
            explained = bundle["explain_fn"](record)
            return {
                "complaint_id": complaint_id,
                "available": True,
                "status": "available",
                "reason": "Compatible trained model artifact and SHAP explainer active.",
                "model_artifact_present": True,
                "shap_library_installed": True,
                "explanation_method": explained.get("explanation_method"),
                "model_version": explained.get("model_version"),
                "prediction_timestamp": explained.get("prediction_timestamp"),
                "prediction": explained.get("prediction"),
                "base_value": explained.get("base_value"),
                "output_value": explained.get("output_value"),
                "features": explained.get("features", []),
                "summary": explained.get("summary", ""),
            }

        return {
            "complaint_id": complaint_id,
            "available": False,
            "status": "unavailable",
            "reason": shap_cap["reason"],
            "model_artifact_present": shap_cap["model_artifact_present"],
            "shap_library_installed": shap_cap["shap_library_installed"],
            "explanation_method": None,
            "model_version": None,
            "prediction_timestamp": None,
            "prediction": None,
            "base_value": None,
            "output_value": None,
            "features": [],
            "summary": (
                "SHAP feature attribution is unavailable because no compatible trained ML model "
                "artifact and SHAP explainer exist for persisted LPU RMS complaints."
            ),
        }

    def get_complaint_intelligence(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Combines authoritative MCPI breakdown with honest SHAP capability status."""
        cid = str(record.get("complaint_id") or "")
        return {
            "complaint_id": cid,
            "mcpi": self.build_mcpi_explanation(record),
            "shap": self.get_shap_status_for_complaint(record),
        }


intelligence_service = IntelligenceService()
