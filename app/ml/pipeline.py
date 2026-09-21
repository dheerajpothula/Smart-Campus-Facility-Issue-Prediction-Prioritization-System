"""
End-to-End Machine Learning Pipeline Coordinator.
Orchestrates:
  Complaint Text → NLP Tokenization → Issue Classification → Severity Prediction →
  Recurrence Analysis → Campus Risk Mapping → Priority Scoring → SHAP Attribution → Maintenance Action
"""

from typing import Dict, Any, Optional
from app.ml.nlp_classifier import nlp_model
from app.ml.severity_model import severity_model
from app.ml.recurrence_detector import recurrence_detector
from app.ml.risk_model import risk_model
from app.ml.priority_engine import priority_engine, active_priority_weights
from app.ml.shap_explainer import shap_explainer
from app.data.database import campus_db
from app.models.data_models import ComplaintSubmission, PriorityWeights

class MLPipelineCoordinator:
    """Executes full predictive pipeline for incoming complaints."""

    def analyze_complaint(
        self,
        submission: ComplaintSubmission,
        weights: Optional[PriorityWeights] = None
    ) -> Dict[str, Any]:
        used_weights = weights or active_priority_weights
        text = submission.description

        # Stage 1: NLP Processing & Issue Classification
        pred_cat, cat_conf, cat_probs = nlp_model.predict(text)
        keywords = nlp_model.extract_keywords(text)

        # Stage 2: Location Risk & Footfall Mapping
        loc_meta = risk_model.get_location_metadata(submission.location)
        footfall_score = float(loc_meta["footfall_score"])
        footfall_level = loc_meta["footfall"]

        loc_risk_data = risk_model.calculate_location_risk(submission.location, campus_db.get_all_records())
        location_risk_tier = loc_risk_data["risk_tier"]
        location_risk_score = loc_risk_data["risk_score"]

        # Stage 3: Severity Prediction Model
        pred_sev, sev_conf, sev_score, sev_signals = severity_model.predict(text, footfall_score=footfall_score)

        # Stage 4: Recurrence Detection Engine
        recurrence_data = recurrence_detector.analyze(
            facility_type=submission.facility_type or pred_cat,
            location=submission.location,
            text=text,
            historical_records=campus_db.get_all_records()
        )
        is_recurring = recurrence_data["recurrence_detected"]
        rec_count = recurrence_data["recurrence_count"]
        rec_score = recurrence_data["recurrence_score"]

        # Stage 5: Operational Impact Calculation
        impact_score = round(0.40 * sev_score + 0.35 * footfall_score + 0.25 * rec_score, 1)

        # Stage 6: Intelligent Priority Scoring Engine
        priority_res = priority_engine.calculate_priority(
            severity_score=sev_score,
            recurrence_score=rec_score,
            footfall_score=footfall_score,
            location_risk_score=location_risk_score,
            impact_score=impact_score,
            facility_type=submission.facility_type or pred_cat,
            predicted_severity=pred_sev,
            weights=used_weights
        )
        priority_score = priority_res["priority_score"]
        expected_impact = priority_res["expected_impact"]
        recommended_action = priority_res["recommended_action"]
        points_breakdown = priority_res["breakdown"]

        # Stage 7: SHAP Explainability Engine
        shap_result = shap_explainer.explain(
            severity_score=sev_score,
            recurrence_score=rec_score,
            footfall_score=footfall_score,
            location_risk_score=location_risk_score,
            impact_score=impact_score,
            priority_score=priority_score,
            weights=used_weights
        )

        return {
            "predicted_category": pred_cat,
            "category_confidence": cat_conf,
            "category_probabilities": cat_probs,
            "extracted_keywords": keywords,
            "predicted_severity": pred_sev,
            "severity_confidence": sev_conf,
            "severity_score": sev_score,
            "severity_signals": sev_signals,
            "location_risk": location_risk_tier,
            "location_risk_score": location_risk_score,
            "footfall_level": footfall_level,
            "footfall_score": footfall_score,
            "recurrence_detected": is_recurring,
            "recurrence_count": rec_count,
            "recurrence_score": rec_score,
            "recurrence_summary": recurrence_data["summary"],
            "impact_score": impact_score,
            "expected_impact": expected_impact,
            "priority_score": priority_score,
            "recommended_action": recommended_action,
            "points_breakdown": points_breakdown,
            "shap_explanation": shap_result.model_dump()
        }

pipeline_coordinator = MLPipelineCoordinator()
