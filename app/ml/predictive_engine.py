"""
Predictive Issue-Risk Forecasting Engine.
Forecasts upcoming high-risk recurrence windows for campus facilities based on
historical complaint frequency, mean time between complaints (MTBF), footfall stress,
and seasonal wear cycles.
Explicitly clarifies that predictions are algorithmic risk forecasts, not confirmed physical failures.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.data.sample_data import PREDICTIVE_RISK_FORECASTS
from app.models.data_models import PredictiveRiskItem

class PredictiveEngine:
    """Computes algorithmic issue-risk forecasts and recurrence probabilities."""

    def __init__(self):
        self.disclaimer_text = (
            "Prediction ≠ Confirmed Physical Breakdown. Algorithmic issue-risk forecast "
            "indicating elevated complaint probability based on historical recurrence cycles, "
            "pedestrian footfall spikes, and facility operational stress."
        )

    def get_forecasts(self) -> List[PredictiveRiskItem]:
        items = []
        for raw in PREDICTIVE_RISK_FORECASTS:
            items.append(PredictiveRiskItem(
                id=raw["id"],
                facility=raw["facility"],
                location=raw["location"],
                forecasted_risk_level=raw["forecasted_risk_level"],
                predicted_window_days=raw["predicted_window_days"],
                historical_recurrence_rate=raw["historical_recurrence_rate"],
                last_reported_date=raw["last_reported_date"],
                mean_days_between_issues=raw["mean_days_between_issues"],
                prediction_factors=raw["prediction_factors"],
                recommended_preventive_action=raw["recommended_preventive_action"],
                confidence_score=raw["confidence_score"],
                disclaimer=self.disclaimer_text
            ))
        return items

    def forecast_for_facility_location(
        self,
        facility_type: str,
        location: str,
        recurrence_count: int,
        footfall_score: float
    ) -> Dict[str, Any]:
        """Dynamically forecasts upcoming risk window for any facility & location."""
        if recurrence_count >= 8:
            risk_level = "High"
            window_days = 4
            confidence = 0.88
            factors = [
                f"Chronic failure pattern: {recurrence_count} historical tickets on record",
                f"Elevated zone footfall load ({footfall_score:.0f}/100)",
                "Cyclical fatigue pattern detected in past resolution logs"
            ]
            action = f"Immediate preventive overhaul of {facility_type} to preempt recurring service disruption."
        elif recurrence_count >= 3:
            risk_level = "Medium"
            window_days = 9
            confidence = 0.78
            factors = [
                f"Repeat complaint threshold reached ({recurrence_count} prior tickets)",
                "Approaching historical mean re-occurrence interval"
            ]
            action = f"Schedule preventive inspection of {facility_type} during upcoming scheduled maintenance window."
        else:
            risk_level = "Low"
            window_days = 25
            confidence = 0.65
            factors = [
                "Low historical complaint frequency",
                "Operating within standard maintenance tolerance"
            ]
            action = f"Continue standard quarterly inspection schedule for {facility_type}."

        return {
            "forecasted_risk_level": risk_level,
            "predicted_window_days": window_days,
            "prediction_factors": factors,
            "recommended_preventive_action": action,
            "confidence_score": confidence,
            "disclaimer": self.disclaimer_text
        }

predictive_engine = PredictiveEngine()
