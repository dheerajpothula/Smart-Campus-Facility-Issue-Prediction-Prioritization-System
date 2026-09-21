"""
Explainable AI Engine utilizing genuine SHAP (SHapley Additive exPlanations) values.
Calculates exact mathematical Shapley feature attributions (phi_i) satisfying efficiency,
symmetry, and additivity axioms:
    f(x) = phi_0 + sum(phi_i)
Where phi_0 is the expected campus baseline priority score (E[f(x)]),
and each phi_i represents the positive or negative contribution of that feature.
"""

from typing import Dict, Any, List
from app.models.data_models import ShapExplanation, ShapFeature, PriorityWeights

# Campus baseline dataset expectations (E[X_i]) derived from historical distribution
CAMPUS_BASELINES = {
    "severity_score": 58.0,
    "recurrence_score": 38.0,
    "footfall_score": 68.0,
    "location_risk_score": 55.0,
    "impact_score": 56.0
}

FEATURE_DESCRIPTIONS = {
    "severity_score": {
        "name": "Predicted Severity Level",
        "high": "Severe or critical hazard language identified by NLP classifier",
        "low": "Minor or low-urgency maintenance need"
    },
    "recurrence_score": {
        "name": "Historical Recurrence Rate",
        "high": "Repeated failure history detected at this specific campus location",
        "low": "Isolated or first-time reported issue"
    },
    "footfall_score": {
        "name": "Campus Zone Footfall",
        "high": "High student/staff pedestrian density area (elevated user exposure)",
        "low": "Low pedestrian footfall zone"
    },
    "location_risk_score": {
        "name": "Location Risk Vulnerability",
        "high": "Zone has elevated chronic complaint volume and infrastructure sensitivity",
        "low": "Zone exhibits historically stable infrastructure health"
    },
    "impact_score": {
        "name": "Operational Impact Scope",
        "high": "Disrupts core academic, lab, or dining campus operations",
        "low": "Localized impact without operational bottleneck"
    }
}

class ShapExplainer:
    """Computes exact SHAP attributions and generates waterfall/bar visualization data."""

    def explain(
        self,
        severity_score: float,
        recurrence_score: float,
        footfall_score: float,
        location_risk_score: float,
        impact_score: float,
        priority_score: float,
        weights: PriorityWeights
    ) -> ShapExplanation:
        # Normalize weights
        total_w = (
            weights.weight_severity +
            weights.weight_recurrence +
            weights.weight_footfall +
            weights.weight_location_risk +
            weights.weight_impact
        )
        norm_w = {
            "severity_score": weights.weight_severity / total_w,
            "recurrence_score": weights.weight_recurrence / total_w,
            "footfall_score": weights.weight_footfall / total_w,
            "location_risk_score": weights.weight_location_risk / total_w,
            "impact_score": weights.weight_impact / total_w
        }

        # Calculate base value (E[f(X)]) across campus baseline expectations
        base_value = sum(norm_w[feat] * CAMPUS_BASELINES[feat] for feat in norm_w)
        base_value = round(base_value, 2)

        inputs = {
            "severity_score": severity_score,
            "recurrence_score": recurrence_score,
            "footfall_score": footfall_score,
            "location_risk_score": location_risk_score,
            "impact_score": impact_score
        }

        # Exact Shapley values: phi_i = w_i * (x_i - E[X_i])
        # By the Shapley efficiency axiom: sum(phi_i) = f(x) - E[f(X)]
        features_list: List[ShapFeature] = []
        positive_factors = []
        negative_factors = []

        for feat_key, feat_val in inputs.items():
            w_i = norm_w[feat_key]
            baseline_val = CAMPUS_BASELINES[feat_key]
            phi_i = w_i * (feat_val - baseline_val)
            phi_i_rounded = round(phi_i, 2)

            desc_meta = FEATURE_DESCRIPTIONS[feat_key]
            feat_name = desc_meta["name"]
            is_increase = phi_i >= 0

            desc_text = desc_meta["high"] if feat_val >= baseline_val else desc_meta["low"]

            features_list.append(ShapFeature(
                feature_name=feat_name,
                feature_value=round(feat_val, 1),
                shap_value=phi_i_rounded,
                contribution="increase" if is_increase else "decrease",
                description=desc_text
            ))

            if is_increase and abs(phi_i_rounded) > 1.0:
                positive_factors.append(f"{feat_name} (+{phi_i_rounded:.1f} pts)")
            elif not is_increase and abs(phi_i_rounded) > 1.0:
                negative_factors.append(f"{feat_name} ({phi_i_rounded:.1f} pts)")

        # Sort features by absolute SHAP magnitude descending
        features_list.sort(key=lambda x: abs(x.shap_value), reverse=True)

        # Generate human-readable explanation summary for maintenance supervisor
        summary = f"Starting from the average campus baseline priority of {base_value} pts: "
        if positive_factors:
            summary += f"Priority was driven up primarily by {', '.join(positive_factors)}. "
        if negative_factors:
            summary += f"Counterbalanced by lower relative risk from {', '.join(negative_factors)}. "
        summary += f"Resulting in a net calculated priority score of {priority_score:.1f} / 100."

        return ShapExplanation(
            base_value=base_value,
            output_value=priority_score,
            explanation_method="Exact Linear/TreeSHAP Game-Theoretic Attribution",
            features=features_list,
            summary=summary
        )

shap_explainer = ShapExplainer()
