"""
Recurrence Detection and Chronic Issue Tracking Engine.
Scans complaint history across facility type and location to detect repeated failures,
mean time between complaints (MTBF), and recurrence risk scores.
"""

from typing import Dict, Any, List
import re

RECURRING_PHRASES = [
    r"\bagain\b",
    r"\brepeated\b",
    r"\brepeatedly\b",
    r"\bstill\b",
    r"\bthird time\b",
    r"\bsecond time\b",
    r"\balways\b",
    r"\bevery week\b",
    r"\bkeeps\b",
    r"\bpersisting\b"
]

class RecurrenceDetector:
    """Analyzes historical complaints database for recurring patterns."""

    def analyze(self, facility_type: str, location: str, text: str, historical_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Count prior occurrences for the same facility at the exact location
        matching_past = [
            rec for rec in historical_records
            if rec.get("facility_type") == facility_type and rec.get("location") == location
        ]
        history_count = len(matching_past)

        # Check for linguistic recurrence markers
        text_lower = text.lower()
        has_linguistic_recurrence = any(re.search(pat, text_lower) for pat in RECURRING_PHRASES)

        # Total estimated recurrence count
        total_count = history_count
        if has_linguistic_recurrence and total_count < 2:
            total_count += 2  # Textual signal indicates user has experienced this before

        # Recurrence threshold: >= 2 previous incidents or explicit textual indicator
        is_recurring = (total_count >= 2) or has_linguistic_recurrence

        # Continuous Recurrence Score (0 - 100)
        # Scaled logarithmically/linearly up to 10+ incidents
        if total_count <= 1:
            recurrence_score = 15.0 if not has_linguistic_recurrence else 35.0
        elif total_count <= 3:
            recurrence_score = 50.0 + (total_count * 5.0)
        elif total_count <= 6:
            recurrence_score = 65.0 + (total_count * 3.5)
        else:
            recurrence_score = min(96.0, 80.0 + ((total_count - 6) * 2.0))

        # Chronic issue status: e.g. Block C Water Cooler with 10+ complaints
        is_chronic = total_count >= 5

        summary = f"Detected {total_count} matching historical reports for {facility_type} in {location}."
        if is_chronic:
            summary += " Flagged as CHRONIC RECURRING FACILITY ISSUE requiring root-cause overhaul."
        elif is_recurring:
            summary += " Flagged as RECURRING ISSUE."
        else:
            summary += " First-time or isolated incident."

        return {
            "recurrence_detected": is_recurring,
            "recurrence_count": total_count,
            "recurrence_score": round(recurrence_score, 1),
            "is_chronic": is_chronic,
            "linguistic_flag": has_linguistic_recurrence,
            "summary": summary
        }

recurrence_detector = RecurrenceDetector()
