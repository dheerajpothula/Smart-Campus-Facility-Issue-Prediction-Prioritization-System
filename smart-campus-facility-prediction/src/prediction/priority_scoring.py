"""
Priority Scoring and Multi-Criteria Ranking Engine.
Computes objective priority scores and SHAP-style feature attributions for campus facility issues.
"""
from dataclasses import dataclass
from typing import Any
import streamlit as st


@dataclass
class PriorityWeights:
    """Configurable priority weights that sum to 1.0."""
    severity: float = 0.35
    location_criticality: float = 0.25
    recurrence_probability: float = 0.25
    impact_population: float = 0.15

    def is_valid(self, tolerance: float = 0.005) -> bool:
        """Checks if weights sum to 1.0 within tolerance."""
        return abs(self.total - 1.0) <= tolerance

    @property
    def total(self) -> float:
        return round(
            self.severity + self.location_criticality + self.recurrence_probability + self.impact_population,
            4,
        )

    def normalize(self) -> "PriorityWeights":
        """Returns normalized weights that sum exactly to 1.0."""
        s = self.severity + self.location_criticality + self.recurrence_probability + self.impact_population
        if s <= 0:
            return PriorityWeights(0.35, 0.25, 0.25, 0.15)
        return PriorityWeights(
            severity=round(self.severity / s, 3),
            location_criticality=round(self.location_criticality / s, 3),
            recurrence_probability=round(self.recurrence_probability / s, 3),
            impact_population=round(self.impact_population / s, 3),
        )


def get_current_weights() -> PriorityWeights:
    """Retrieves the active priority weights from session state or initializes default."""
    if "priority_weights" not in st.session_state:
        st.session_state["priority_weights"] = PriorityWeights()
    return st.session_state["priority_weights"]


def update_weights(weights: PriorityWeights) -> None:
    """Saves updated priority weights to session state."""
    st.session_state["priority_weights"] = weights


def reset_weights_to_default() -> PriorityWeights:
    """Resets weights to standard defaults."""
    default_w = PriorityWeights(0.35, 0.25, 0.25, 0.15)
    st.session_state["priority_weights"] = default_w
    return default_w


# Location Criticality lookup (0.0 to 1.0 scale)
LOCATION_CRITICALITY_MAP = {
    "Server Room": 1.0,
    "Data Center": 1.0,
    "Exam Hall": 0.95,
    "Chemistry Lab": 0.90,
    "Computer Lab": 0.85,
    "Lecture Hall": 0.80,
    "Hostel Mess / Kitchen": 0.80,
    "Hostel Washroom": 0.75,
    "Central Library": 0.70,
    "Hostel Room": 0.60,
    "Faculty Office": 0.55,
    "Administrative Office": 0.50,
    "Corridor / Common Area": 0.35,
    "Campus Grounds": 0.25,
}

# Severity Numeric Mapping (0.0 to 1.0)
SEVERITY_SCORE_MAP = {
    "Critical": 1.0,
    "High": 0.75,
    "Medium": 0.45,
    "Low": 0.20,
}


def calculate_priority_score(
    severity: str,
    location_type: str,
    recurrence_risk: float,
    impact_scale: float,
    weights: PriorityWeights | None = None,
) -> tuple[float, str, dict[str, float]]:
    """
    Computes the composite priority score (0-100), priority tier, and component breakdown.

    Returns:
        (score, tier, breakdown_dict)
    """
    if weights is None:
        weights = get_current_weights()

    s_val = SEVERITY_SCORE_MAP.get(severity, 0.4)
    c_val = LOCATION_CRITICALITY_MAP.get(location_type, 0.5)
    r_val = max(0.0, min(1.0, float(recurrence_risk)))
    i_val = max(0.0, min(1.0, float(impact_scale)))

    contrib_s = weights.severity * s_val * 100.0
    contrib_c = weights.location_criticality * c_val * 100.0
    contrib_r = weights.recurrence_probability * r_val * 100.0
    contrib_i = weights.impact_population * i_val * 100.0

    raw_score = contrib_s + contrib_c + contrib_r + contrib_i
    score = round(max(0.0, min(100.0, raw_score)), 1)

    if score >= 75.0:
        tier = "Critical"
    elif score >= 50.0:
        tier = "High"
    elif score >= 28.0:
        tier = "Medium"
    else:
        tier = "Low"

    breakdown = {
        "Severity Contribution": round(contrib_s, 1),
        "Location Criticality Contribution": round(contrib_c, 1),
        "Recurrence Risk Contribution": round(contrib_r, 1),
        "Impact Population Contribution": round(contrib_i, 1),
    }

    return score, tier, breakdown
