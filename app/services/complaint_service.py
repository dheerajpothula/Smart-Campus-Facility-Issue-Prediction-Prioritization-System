"""
FIPP 2.0 — Unified Complaint Service.
Encapsulates all complaint lifecycle management, sequential token generation,
thread-safe atomic JSON datastore persistence, student data isolation,
remarks audit logging, maintenance squad assignment, withdrawal, and feedback.
"""
import json
import os
import re
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Set

from app.core.config import PRIMARY_JSON_DATA_FILE
from app.models.data_models import StudentComplaintCreate, PriorityWeights
from app.services.location_service import location_service

# Ensure smart-campus-facility-prediction is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SMART_CAMPUS_DIR = PROJECT_ROOT / "smart-campus-facility-prediction"
if str(SMART_CAMPUS_DIR) not in sys.path:
    sys.path.insert(0, str(SMART_CAMPUS_DIR))

try:
    from src.prediction.priority_scoring import calculate_priority_score, PriorityWeights as SrcPriorityWeights
except ImportError:
    from app.ml.priority_engine import priority_engine

# Re-entrant lock for thread safety during atomic file I/O
_SERVICE_LOCK = threading.RLock()

CANONICAL_PROGRESS_STAGES = [
    "Submitted",
    "Under Review",
    "Assigned",
    "In Progress",
    "Resolved",
    "Withdrawn",
]

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

SEVERITY_SCORE_MAP = {
    "Critical": 1.0,
    "High": 0.75,
    "Medium": 0.45,
    "Low": 0.20,
}


def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parses canonical and legacy complaint timestamps without inventing values."""
    if not ts_str or not isinstance(ts_str, str):
        return None
    cleaned = ts_str.strip()
    if not cleaned:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %I:%M:%S %p",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


class ComplaintService:
    """Core domain service for managing campus facility complaints."""

    def __init__(self, data_file: Path = PRIMARY_JSON_DATA_FILE):
        self.data_file = Path(data_file).resolve()
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_records(self) -> List[Dict[str, Any]]:
        """Loads records from the atomic JSON store safely under lock."""
        with _SERVICE_LOCK:
            if self.data_file.is_file():
                try:
                    with open(self.data_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data
                except Exception:
                    pass
            return []

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        """Persists records atomically using temporary file replacement under lock; fails loudly on write error."""
        with _SERVICE_LOCK:
            temp_path = self.data_file.with_suffix(".tmp")
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                os.replace(temp_path, self.data_file)
            except Exception as exc:
                raise RuntimeError("Failed to persist complaint records safely.") from exc
            finally:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

    def generate_next_token(self, records: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generates a unique, permanent, sequential complaint token strictly formatted as:
        CMP-2026-001, CMP-2026-002, CMP-2026-003, ...
        """
        if records is None:
            records = self._load_records()

        highest = 0
        pattern = re.compile(r"^CMP-2026-(\d+)$")
        for r in records:
            cid = str(r.get("complaint_id", "")).strip()
            match = pattern.match(cid)
            if match:
                num = int(match.group(1))
                if num > highest:
                    highest = num

        next_num = highest + 1
        return f"CMP-2026-{next_num:03d}"

    def compute_mcpi(
        self,
        severity: str,
        location_type: str,
        recurrence_risk: float = 0.35,
        impact_scale: float = 0.50,
        weights: Optional[PriorityWeights] = None
    ) -> Tuple[float, str, Dict[str, float]]:
        """Computes multi-criteria priority score (0-100), tier, and breakdown."""
        w = weights or PriorityWeights()
        if abs(w.total - 1.0) > 0.005:
            w = w.normalize()
        s_val = SEVERITY_SCORE_MAP.get(severity, 0.4)
        c_val = LOCATION_CRITICALITY_MAP.get(location_type, 0.5)
        r_val = max(0.0, min(1.0, float(recurrence_risk)))
        i_val = max(0.0, min(1.0, float(impact_scale)))

        contrib_s = w.severity * s_val * 100.0
        contrib_c = w.location_criticality * c_val * 100.0
        contrib_r = w.recurrence_probability * r_val * 100.0
        contrib_i = w.impact_population * i_val * 100.0

        score = round(max(0.0, min(100.0, contrib_s + contrib_c + contrib_r + contrib_i)), 1)
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

    def predict_issue_attributes(self, category: str, title: str, description: str, building: str) -> Dict[str, Any]:
        """Heuristic attribute inference matching existing Streamlit logic."""
        text = f"{title} {description} {building}".lower()

        if any(k in text for k in ["spark", "fire", "smoke", "shock", "burst", "flood", "gush", "burn", "collapse"]):
            severity = "Critical"
        elif "electrical" in category.lower() or any(k in text for k in ["trip", "outage", "blackout", "overflow", "no water", "short"]):
            severity = "High"
        elif "plumbing" in category.lower() or "water" in category.lower() or any(k in text for k in ["leak", "choke", "sensor", "tap", "drain"]):
            severity = "Medium"
        elif "washroom" in category.lower() or "garbage" in category.lower():
            severity = "Medium" if "overflow" in text else "Low"
        else:
            severity = "Low"

        # Location Type
        if "server" in text or "data center" in text:
            location_type = "Server Room"
        elif "chem" in text:
            location_type = "Chemistry Lab"
        elif "lab" in text or "computer" in text:
            location_type = "Computer Lab"
        elif "library" in text:
            location_type = "Central Library"
        elif "washroom" in text or "toilet" in text or "restroom" in text:
            location_type = "Hostel Washroom" if "hostel" in text else "Corridor / Common Area"
        elif "hostel" in text or "room" in text:
            location_type = "Hostel Room"
        elif "class" in text or "hall" in text or "lecture" in text:
            location_type = "Lecture Hall"
        else:
            location_type = "Corridor / Common Area"

        now = datetime.now()
        if severity == "Critical":
            est_res = (now + timedelta(hours=6)).strftime("%Y-%m-%d")
        elif severity == "High":
            est_res = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif severity == "Medium":
            est_res = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        else:
            est_res = (now + timedelta(days=3)).strftime("%Y-%m-%d")

        return {
            "severity": severity,
            "location_type": location_type,
            "recurrence_risk": 0.65 if severity in ["Critical", "High"] else 0.25,
            "impact_scale": 0.80 if location_type in ["Server Room", "Computer Lab", "Lecture Hall"] else 0.45,
            "estimated_resolution": est_res,
        }

    def create_complaint(
        self,
        student_id: str,
        student_name: str,
        data: StudentComplaintCreate,
        weights: Optional[PriorityWeights] = None
    ) -> Dict[str, Any]:
        """Creates and persists a new complaint ticket from an authenticated student."""
        validated_block, validated_floor = location_service.validate_block_floor_combination(
            building=data.building,
            block_id=data.block_id,
            floor_id=data.floor_id,
            floor_label=data.floor_label,
        )
        resolved_building = str(validated_block["display_name"])
        resolved_block_id = str(validated_block["block_id"])
        resolved_floor_id = str(validated_floor["floor_id"]) if validated_floor else None
        resolved_floor_label = str(validated_floor["floor_label"]) if validated_floor else None

        with _SERVICE_LOCK:
            records = self._load_records()
            token = self.generate_next_token(records)

            # Location formatting
            if data.room_type == "Room No" and data.room_number:
                spec_loc = f"Room {data.room_number.strip()}"
            elif data.specified_location:
                spec_loc = data.specified_location.strip()
            else:
                spec_loc = "Campus Facility Area"

            loc_parts = [resolved_building]
            if resolved_floor_label:
                loc_parts.append(resolved_floor_label)
            elif data.sub_block:
                loc_parts.append(f"Sub Block {data.sub_block}")
            loc_parts.append(spec_loc)
            full_location = " - ".join(loc_parts[:2])
            if len(loc_parts) > 2:
                full_location += f", {loc_parts[2]}"

            # Specific Category formatting
            spec_cat_str = ", ".join(data.specific_categories) if data.specific_categories else (data.sub_category or data.category)
            title = (data.title or "").strip() if getattr(data, "title", None) else f"[{data.message_type}] {spec_cat_str}"
            if not title:
                title = f"[{data.message_type}] {spec_cat_str}"

            # Predict domain attributes and priority score
            pred = self.predict_issue_attributes(
                category=data.category,
                title=title,
                description=data.description,
                building=resolved_building,
            )
            score, tier, bdown = self.compute_mcpi(
                severity=pred["severity"],
                location_type=pred["location_type"],
                recurrence_risk=pred["recurrence_risk"],
                impact_scale=pred["impact_scale"],
                weights=weights,
            )

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            audit_str = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

            new_ticket: Dict[str, Any] = {
                "complaint_id": token,
                "student_id": student_id,
                "student_name": student_name,
                "category_type": data.category_type,
                "message_type": data.message_type,
                "category": data.category,
                "sub_category": data.sub_category or "General",
                "specific_categories": data.specific_categories,
                "specific_category": spec_cat_str,
                "facility_type": data.category,
                "building": resolved_building,
                "block_id": resolved_block_id,
                "floor_id": resolved_floor_id,
                "floor_label": resolved_floor_label,
                "sub_block": data.sub_block,
                "room_type": data.room_type,
                "room_number": data.room_number,
                "specified_location": data.specified_location,
                "specific_location": spec_loc,
                "location": full_location,
                "contact_number": data.contact_number,
                "availability_date": data.availability_date,
                "time_slot": data.time_slot,
                "time_slots": [data.time_slot],
                "title": title,
                "subject": title,
                "description": data.description.strip(),
                "reported_by": student_name,
                "status": "Submitted",
                "priority_tier": tier,
                "priority_score": score,
                "severity": pred["severity"],
                "location_type": pred["location_type"],
                "recurrence_risk": pred["recurrence_risk"],
                "impact_scale": pred["impact_scale"],
                "score_breakdown": bdown,
                "allotted_person": None,
                "department": None,
                "designation": None,
                "date_reported": now_str,
                "estimated_resolution": pred["estimated_resolution"],
                "action_taken": "Your request has been registered and queued for triage.",
                "has_photo": bool(data.photo_stored_filename),
                "photo_stored_filename": data.photo_stored_filename,
                "photo_sha256": data.photo_sha256,
                "remarks_history": [
                    {
                        "remarks": "Your request has been forwarded to the concerned Department for necessary action.",
                        "update_date": audit_str,
                        "name": "System Triage",
                        "supporting_document": "None",
                    }
                ],
                "feedback": None,
            }

            records.insert(0, new_ticket)
            self._save_records(records)
            return new_ticket

    def get_all_complaints(
        self,
        search: Optional[str] = None,
        status: Optional[Union[str, List[str], Set[str], Tuple[str, ...]]] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        priority: Optional[str] = None,
        squad: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "Newest first"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieves complaints with filtering, searching, and pagination."""
        records = self._load_records()

        # Filtering
        filtered = []
        search_lower = search.strip().lower() if search else None

        for r in records:
            if status and status != "All Statuses":
                if isinstance(status, (list, tuple, set)):
                    if r.get("status") not in status:
                        continue
                elif r.get("status") != status:
                    continue
            if category and category != "All Categories" and r.get("category") != category and r.get("facility_type") != category:
                continue
            if location and location != "All Locations":
                bld = r.get("building") or r.get("location", "")
                if location.lower() not in str(bld).lower():
                    continue
            if priority and priority != "All Priorities" and r.get("priority_tier") != priority:
                continue
            if squad and squad != "All Squads" and r.get("department") != squad:
                continue

            if search_lower:
                match = (
                    search_lower in str(r.get("complaint_id", "")).lower() or
                    search_lower in str(r.get("title", "")).lower() or
                    search_lower in str(r.get("description", "")).lower() or
                    search_lower in str(r.get("student_id", "")).lower() or
                    search_lower in str(r.get("location", "")).lower()
                )
                if not match:
                    continue

            filtered.append(r)

        total_count = len(filtered)

        # Sorting
        if sort_by == "Oldest first":
            filtered.sort(key=lambda x: x.get("date_reported", ""))
        elif "highest" in sort_by.lower() or "priority" in sort_by.lower():
            filtered.sort(key=lambda x: float(x.get("priority_score", 0)), reverse=True)
        else:  # Newest first default
            filtered.sort(key=lambda x: x.get("date_reported", ""), reverse=True)

        return filtered[offset:offset + limit], total_count

    def get_student_complaints(self, student_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves only complaints belonging to the specified student."""
        records = self._load_records()
        owned = [r for r in records if r.get("student_id") == student_id]

        if search and search.strip():
            term = search.strip().lower()
            owned = [
                r for r in owned
                if term in str(r.get("complaint_id", "")).lower()
                or term in str(r.get("title", "")).lower()
                or term in str(r.get("description", "")).lower()
            ]

        owned.sort(key=lambda x: x.get("date_reported", ""), reverse=True)
        return owned

    def get_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single complaint by token."""
        records = self._load_records()
        for r in records:
            if r.get("complaint_id") == complaint_id:
                return r
        return None

    def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
        remarks: Optional[str] = None,
        admin_id: Optional[str] = None,
        admin_title: Optional[str] = None,
        allotted_person: Optional[str] = None,
        squad_assigned: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates status, assignment, remarks, and appends to audit history."""
        with _SERVICE_LOCK:
            records = self._load_records()
            for r in records:
                if r.get("complaint_id") == complaint_id:
                    old_status = r.get("status", "Submitted")
                    if old_status == "Withdrawn":
                        raise ValueError("Cannot update status of a terminal 'Withdrawn' complaint.")
                    if old_status == "Resolved" and new_status != "Resolved":
                        raise ValueError("Resolved complaints must be reopened via the reopen workflow.")
                    r["status"] = new_status
                    if remarks:
                        r["action_taken"] = remarks
                        if new_status == "Resolved":
                            r["closing_remarks"] = remarks
                    if allotted_person is not None:
                        r["allotted_person"] = None if allotted_person in ["Unassigned", "None", ""] else allotted_person
                    if squad_assigned is not None:
                        r["department"] = None if squad_assigned in ["Unassigned", "None", ""] else squad_assigned

                    now_str = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                    admin_label = f"{admin_title or 'Administrator'} ({admin_id or 'Admin Desk'})"
                    remarks_list = r.setdefault("remarks_history", [])
                    remarks_list.insert(0, {
                        "remarks": f"Status updated to '{new_status}'. {remarks or ''}".strip(),
                        "update_date": now_str,
                        "name": admin_label,
                        "previous_status": old_status,
                        "new_status": new_status,
                        "supporting_document": "None",
                    })

                    if new_status == "Resolved":
                        r["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        r["resolved_by"] = admin_id or "Administrator"

                    self._save_records(records)
                    return r
            return None

    def reopen_complaint(
        self,
        complaint_id: str,
        remarks: str,
        admin_id: Optional[str] = None,
        admin_title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Reopens a resolved complaint, transitioning to 'Under Review' and preserving history."""
        with _SERVICE_LOCK:
            records = self._load_records()
            for r in records:
                if r.get("complaint_id") == complaint_id:
                    old_status = r.get("status")
                    if old_status != "Resolved":
                        raise ValueError(f"Only complaints with 'Resolved' status can be reopened (current status: '{old_status}').")
                    r["status"] = "Under Review"
                    r["is_reopened"] = True
                    r["reopened_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if "resolved_at" in r and "original_resolved_at" not in r:
                        r["original_resolved_at"] = r["resolved_at"]
                    if "resolved_by" in r and "original_resolved_by" not in r:
                        r["original_resolved_by"] = r["resolved_by"]
                    if "closing_remarks" in r and "previous_closing_remarks" not in r:
                        r["previous_closing_remarks"] = r["closing_remarks"]

                    now_str = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                    admin_label = f"{admin_title or 'Administrator'} ({admin_id or 'Admin Desk'})"
                    remarks_list = r.setdefault("remarks_history", [])
                    remarks_list.insert(0, {
                        "remarks": f"Ticket Reopened: {remarks.strip()}",
                        "update_date": now_str,
                        "name": admin_label,
                        "previous_status": old_status,
                        "new_status": "Under Review",
                        "supporting_document": "None",
                    })

                    self._save_records(records)
                    return r
            return None

    def withdraw_complaint(self, complaint_id: str, student_id: str, reason: Optional[str] = None) -> bool:
        """Allows a student to withdraw an open query."""
        with _SERVICE_LOCK:
            records = self._load_records()
            for r in records:
                if r.get("complaint_id") == complaint_id:
                    if r.get("student_id") != student_id:
                        return False
                    if r.get("status") in ["Resolved", "Withdrawn"]:
                        return False

                    old_status = r.get("status")
                    r["status"] = "Withdrawn"
                    r["withdrawn_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    r["withdrawal_reason"] = reason or "Withdrawn by student."

                    now_str = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                    remarks_list = r.setdefault("remarks_history", [])
                    remarks_list.insert(0, {
                        "remarks": f"Query Withdrawn by Student: {reason or 'No reason provided'}",
                        "update_date": now_str,
                        "name": f"Student ({student_id})",
                        "previous_status": old_status,
                        "new_status": "Withdrawn",
                        "supporting_document": "None",
                    })

                    self._save_records(records)
                    return True
            return False

    def submit_feedback(self, complaint_id: str, student_id: str, rating: int, comments: Optional[str] = None) -> bool:
        """Stores student 5-star resolution feedback."""
        with _SERVICE_LOCK:
            records = self._load_records()
            for r in records:
                if r.get("complaint_id") == complaint_id:
                    if r.get("student_id") != student_id:
                        return False
                    if r.get("status") != "Resolved":
                        return False

                    star_labels = {5: "Excellent", 4: "Good", 3: "Average", 2: "Below Average", 1: "Poor"}
                    r["feedback"] = {
                        "rating": rating,
                        "rating_label": star_labels.get(rating, "Average"),
                        "comments": comments or "",
                        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "student_id": student_id,
                    }

                    self._save_records(records)
                    return True
            return False

    def get_kpis(self) -> Dict[str, Any]:
        """Calculates real-time Control Centre KPI metrics from genuine persisted records."""
        records = self._load_records()
        total = len(records)
        new_count = sum(1 for r in records if r.get("status") == "Submitted")
        in_prog_count = sum(1 for r in records if r.get("status") in ["Under Review", "Assigned", "In Progress"])
        resolved_count = sum(1 for r in records if r.get("status") == "Resolved")
        withdrawn_count = sum(1 for r in records if r.get("status") == "Withdrawn")
        eligible_total = total - withdrawn_count
        rate = round((resolved_count / eligible_total * 100), 1) if eligible_total > 0 else 0.0

        # Calculate average turnaround time strictly from genuine submission and resolution timestamps
        turnaround_days = []
        for r in records:
            if r.get("status") == "Resolved":
                t_res = parse_timestamp(r.get("resolved_at"))
                t_rep = parse_timestamp(r.get("date_reported"))
                if t_res and t_rep:
                    diff = (t_res - t_rep).total_seconds() / 86400.0
                    if diff >= 0:
                        turnaround_days.append(diff)

        avg_turnaround = round(sum(turnaround_days) / len(turnaround_days), 1) if turnaround_days else None

        return {
            "total": total,
            "new": new_count,
            "in_progress": in_prog_count,
            "resolved": resolved_count,
            "withdrawn": withdrawn_count,
            "resolution_rate_percent": rate,
            "average_turnaround_days": avg_turnaround,
        }

    @classmethod
    def normalize_record(cls, r: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures a complaint record adheres strictly to the target API contract."""
        rec = dict(r)
        cat = rec.get("category") or rec.get("facility_type") or "General"
        fac = rec.get("facility_type") or rec.get("category") or "General"
        loc = rec.get("location") or "Campus Main Complex"
        bld = rec.get("building") or (loc.split(" - ")[0] if " - " in loc else "Campus Main Complex")
        title = rec.get("title") or rec.get("subject") or f"Facility Issue: {cat}"
        sev = rec.get("severity", "Medium")

        if rec.get("priority_tier") and rec.get("priority_score") is not None and rec.get("score_breakdown"):
            tier = rec["priority_tier"]
            score = float(rec["priority_score"])
            bdown = rec["score_breakdown"]
        else:
            calc_score, calc_tier, calc_bdown = complaint_service.compute_mcpi(
                severity=sev,
                location_type=rec.get("location_type", "Corridor / Common Area"),
                recurrence_risk=float(rec.get("recurrence_risk", 0.35)),
                impact_scale=float(rec.get("impact_scale", 0.50)),
            )
            tier = rec.get("priority_tier") or calc_tier
            score = float(rec["priority_score"]) if rec.get("priority_score") is not None else calc_score
            bdown = rec.get("score_breakdown") or calc_bdown

        rec["category"] = cat
        rec["facility_type"] = fac
        rec["building"] = bld
        rec["location"] = loc
        rec["title"] = title
        rec["priority_tier"] = tier
        rec["priority_score"] = score
        rec["score_breakdown"] = bdown
        rec["category_type"] = rec.get("category_type", "Maintenance / Electrical Complaints")
        rec["message_type"] = rec.get("message_type", "Grievance")
        rec["specific_categories"] = rec.get("specific_categories") or []
        rec["remarks_history"] = rec.get("remarks_history") or []
        rec["has_photo"] = rec.get("has_photo", bool(rec.get("photo_stored_filename")))
        return rec


complaint_service = ComplaintService()
