"""
Campus Location & Facility Risk Intelligence Model.
Calculates continuous location risk index (0 - 100) and risk tiers (Low, Medium, High)
incorporating footfall density, complaint density, and recurrence patterns.
"""

from typing import Dict, Any, List
from app.data.sample_data import DEMO_LOCATIONS

class RiskModel:
    """Evaluates location sensitivity and footfall risk scores."""

    def __init__(self):
        self.locations_map = {loc["name"]: loc for loc in DEMO_LOCATIONS}

    def get_location_metadata(self, location_name: str) -> Dict[str, Any]:
        # Fuzzy match if exact match not found
        for name, meta in self.locations_map.items():
            if location_name.lower() in name.lower() or name.lower() in location_name.lower():
                return meta
        # Default fallback
        return {
            "id": "LOC-CUSTOM",
            "name": location_name,
            "zone": "General Academic",
            "footfall": "Moderate",
            "footfall_score": 65.0,
            "x": 50,
            "y": 50
        }

    def calculate_location_risk(self, location_name: str, historical_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        loc_meta = self.get_location_metadata(location_name)
        footfall_score = float(loc_meta["footfall_score"])
        footfall_tier = loc_meta["footfall"]

        # Number of historical complaints at this location
        matching = [r for r in historical_records if location_name.lower() in r.get("location", "").lower()]
        complaints_count = len(matching)
        recurring_count = sum(1 for r in matching if r.get("recurrence_detected", False))

        # Composite risk formula: 55% Footfall exposure + 30% complaint density + 15% recurrence concentration
        complaint_density_score = min(100.0, complaints_count * 8.0)
        recurrence_density_score = min(100.0, recurring_count * 12.0)

        risk_score = (0.55 * footfall_score) + (0.30 * complaint_density_score) + (0.15 * recurrence_density_score)
        risk_score = round(min(100.0, max(20.0, risk_score)), 1)

        if risk_score >= 75.0:
            risk_tier = "High"
        elif risk_score >= 50.0:
            risk_tier = "Medium"
        else:
            risk_tier = "Low"

        return {
            "location_name": loc_meta["name"],
            "zone": loc_meta["zone"],
            "footfall_level": footfall_tier,
            "footfall_score": footfall_score,
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "historical_complaints_count": complaints_count,
            "historical_recurring_count": recurring_count,
            "coordinates": {"x": loc_meta["x"], "y": loc_meta["y"]}
        }

    def get_campus_risk_matrix(self, historical_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matrix = []
        for loc in DEMO_LOCATIONS:
            risk_info = self.calculate_location_risk(loc["name"], historical_records)
            matrix.append({
                "location_id": loc["id"],
                "location_name": loc["name"],
                "zone": loc["zone"],
                "risk_tier": risk_info["risk_tier"],
                "risk_score": risk_info["risk_score"],
                "footfall_tier": risk_info["footfall_level"],
                "footfall_score": risk_info["footfall_score"],
                "active_complaints": sum(1 for r in historical_records if loc["name"].lower() in r.get("location", "").lower() and r.get("status") == "Open"),
                "recurring_complaints": risk_info["historical_recurring_count"],
                "coordinates": risk_info["coordinates"]
            })
        # Sort descending by risk score
        return sorted(matrix, key=lambda x: x["risk_score"], reverse=True)

risk_model = RiskModel()
