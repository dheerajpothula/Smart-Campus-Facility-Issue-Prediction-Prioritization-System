"""
Intelligent Maintenance Priority Engine with Configurable Prototype Weights.
Calculates transparent, multi-factor priority scores (0 - 100) and prescribes
actionable maintenance interventions.
"""

from typing import Dict, Any
from app.models.data_models import PriorityWeights

# Global active weights instance (configurable via API and UI sliders)
active_priority_weights = PriorityWeights(
    weight_severity=0.35,
    weight_recurrence=0.25,
    weight_footfall=0.20,
    weight_location_risk=0.10,
    weight_impact=0.10
)

ACTION_CATALOG = {
    "Water Cooler": {
        "Critical": "Immediate isolation: shut off electrical power & inlet valve, dispatch refrigeration specialist.",
        "High": "Inspect and repair immediately: test compressor pressure, check drainage pipe, service filter tap.",
        "Medium": "Schedule inspection within 24 hours: replace sediment filter cartridge and calibrate thermostat.",
        "Low": "Queue for routine weekly maintenance: clean drip tray and sanitize exterior nozzle."
    },
    "Washroom & Plumbing": {
        "Critical": "Emergency plumbing team dispatch: shut main risers to stop flooding and clear blocked sewage line.",
        "High": "Urgent maintenance: fix tap leakage, clear floor drain blockage, and place wet-floor hazard signs.",
        "Medium": "Standard plumbing service: replace worn washers and flush siphon diaphragms within 48 hours.",
        "Low": "Routine upkeep: replenish soap/towel supplies and clear minor drain lint."
    },
    "Lighting & Electrical": {
        "Critical": "Immediate electrical safety isolation: trip affected circuit breaker, tag out panel, inspect wiring.",
        "High": "Urgent electrician dispatch: replace burnt socket/switch and verify ground fault interrupter.",
        "Medium": "Replace faulty ballasts and swap flickering fluorescent tubes with LED panels within 3 days.",
        "Low": "Schedule routine replacement during next scheduled building lighting sweep."
    },
    "HVAC & Air Conditioning": {
        "Critical": "Critical climate dispatch: service primary cooling loop to avoid hardware thermal shutdown.",
        "High": "Urgent HVAC service: wash air handling unit filters and recharge refrigerant loop.",
        "Medium": "Inspect duct damper actuators and lubricate blower fan bearings within 72 hours.",
        "Low": "Calibrate room thermostat and schedule quarterly filter replacement."
    },
    "Waste Management & Sanitation": {
        "Critical": "Hazmat / bio-waste protocol: isolate area and conduct professional sanitation clearing.",
        "High": "Urgent sanitation: clear overflowing waste dumpster, sanitize perimeter, and spray pest deterrent.",
        "Medium": "Dispatch cleaning staff with auxiliary bins and clear scattered litter.",
        "Low": "Empty recycling bins on regular evening collection route."
    },
    "Elevator & Mobility": {
        "Critical": "Emergency lift lockout: disable elevator car, verify cabin occupancy, dispatch certified lift engineer.",
        "High": "Urgent technical inspection: clean and realign optical door safety sensors and guide rails.",
        "Medium": "Inspect landing floor leveling accuracy and service hydraulic fluid levels.",
        "Low": "Replace indicator lamps and clean car threshold grooves."
    },
    "Classroom AV & Furniture": {
        "Critical": "Remove hazardous equipment immediately to avoid student injury or class disruption.",
        "High": "Urgent classroom repair: swap failed projector lamp before next scheduled lecture.",
        "Medium": "Replace damaged student seating from backup buffer stock within 48 hours.",
        "Low": "Refit whiteboard marker tray and tighten podium fasteners."
    }
}

class PriorityEngine:
    """Calculates explainable priority score based on configurable prototype weights."""

    def calculate_priority(
        self,
        severity_score: float,
        recurrence_score: float,
        footfall_score: float,
        location_risk_score: float,
        impact_score: float,
        facility_type: str,
        predicted_severity: str,
        weights: PriorityWeights = None
    ) -> Dict[str, Any]:
        w = weights or active_priority_weights

        # Normalize weights if sum != 1.0
        total_w = w.weight_severity + w.weight_recurrence + w.weight_footfall + w.weight_location_risk + w.weight_impact
        norm_sev = w.weight_severity / total_w
        norm_rec = w.weight_recurrence / total_w
        norm_foot = w.weight_footfall / total_w
        norm_loc = w.weight_location_risk / total_w
        norm_imp = w.weight_impact / total_w

        # Individual factor points
        pts_sev = norm_sev * severity_score
        pts_rec = norm_rec * recurrence_score
        pts_foot = norm_foot * footfall_score
        pts_loc = norm_loc * location_risk_score
        pts_imp = norm_imp * impact_score

        composite_score = pts_sev + pts_rec + pts_foot + pts_loc + pts_imp
        final_priority = round(min(100.0, max(10.0, composite_score)), 1)

        # Expected Impact Level derivation
        if composite_score >= 80.0:
            expected_impact = "Critical"
        elif composite_score >= 68.0:
            expected_impact = "High"
        elif composite_score >= 45.0:
            expected_impact = "Medium"
        else:
            expected_impact = "Low"

        # Action lookup with fallback
        cat_actions = ACTION_CATALOG.get(facility_type, ACTION_CATALOG["Water Cooler"])
        recommended_action = cat_actions.get(
            predicted_severity,
            f"Inspect and address {facility_type} issue according to standard maintenance SOP."
        )

        return {
            "priority_score": final_priority,
            "expected_impact": expected_impact,
            "recommended_action": recommended_action,
            "breakdown": {
                "severity_points": round(pts_sev, 2),
                "recurrence_points": round(pts_rec, 2),
                "footfall_points": round(pts_foot, 2),
                "location_risk_points": round(pts_loc, 2),
                "impact_points": round(pts_imp, 2),
                "raw_inputs": {
                    "severity_score": severity_score,
                    "recurrence_score": recurrence_score,
                    "footfall_score": footfall_score,
                    "location_risk_score": location_risk_score,
                    "impact_score": impact_score
                },
                "normalized_weights_used": {
                    "severity": round(norm_sev, 3),
                    "recurrence": round(norm_rec, 3),
                    "footfall": round(norm_foot, 3),
                    "location_risk": round(norm_loc, 3),
                    "impact": round(norm_imp, 3)
                }
            }
        }

priority_engine = PriorityEngine()
