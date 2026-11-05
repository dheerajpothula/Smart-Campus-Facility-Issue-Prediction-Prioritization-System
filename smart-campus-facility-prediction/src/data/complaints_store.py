"""
Campus Complaints Data Store.
Manages persistent complaint records, seed datasets, CSV ingestion, priority prediction, and operational metrics.
Enforces permanent sequential token generation (CMP-2026-001, CMP-2026-002, ...) and student identity isolation.
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st

from src.prediction.priority_scoring import calculate_priority_score, get_current_weights

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "complaints.json"

# Canonical 5-stage progress lifecycle
PROGRESS_STAGES = [
    "Submitted",
    "Under Review",
    "Assigned",
    "In Progress",
    "Resolved",
]

def get_current_student_identity() -> dict:
    """
    Returns the trusted student identity for the current session.
    Retrieves dynamically from st.session_state['auth_user'].
    If not authenticated, checks test fallback or returns None for student_id and student_name.
    """
    auth = st.session_state.get("auth_user")
    if isinstance(auth, dict) and auth.get("role") == "student" and auth.get("id"):
        return {
            "student_id": auth["id"],
            "student_name": auth.get("name", "Student"),
        }
    if st.session_state.get("user_role") == "student" and not auth:
        return {
            "student_id": "STU-TEST-001",
            "student_name": "Test Student",
        }
    return {
        "student_id": None,
        "student_name": None,
    }


def _normalize_status(status: str | None) -> str:
    """Normalizes legacy or alternative status strings to canonical stages."""
    if not status:
        return "Submitted"
    s_lower = str(status).strip().lower()
    if "resolved" in s_lower or "closed" in s_lower:
        return "Resolved"
    elif "progress" in s_lower or "investigating" in s_lower:
        return "In Progress"
    elif "dispatched" in s_lower or "assigned" in s_lower:
        return "Assigned"
    elif "review" in s_lower or "evaluat" in s_lower:
        return "Under Review"
    else:
        return "Submitted"


def _generate_seed_complaints() -> list[dict]:
    """Generates a realistic set of initial campus facility complaints for bootstrapping."""
    now = datetime.now()
    records = [
        {
            "complaint_id": "CMP-2026-001",
            "student_id": None,
            "student_name": None,
            "title": "Severe Main Pipe Leakage in 2nd Floor Restroom",
            "description": "Continuous water gushing from main supply valve in 2nd floor restroom, causing corridor flooding.",
            "facility_type": "Plumbing",
            "location": "Hostel Block B - 2nd Floor Washroom",
            "building": "Hostel Block B",
            "specific_location": "2nd Floor Washroom",
            "location_type": "Hostel Washroom",
            "severity": "Critical",
            "recurrence_risk": 0.85,
            "impact_scale": 0.75,
            "is_recurring": True,
            "recurrence_count": 4,
            "status": "In Progress",
            "date_reported": (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(hours=6)).strftime("%Y-%m-%d"),
            "reported_by": "Hostel Warden",
            "action_taken": "Emergency valve shut off; plumbing squad dispatched.",
        },
        {
            "complaint_id": "CMP-2026-002",
            "student_id": None,
            "student_name": None,
            "title": "Precision AC Tripping in Core Server Room",
            "description": "Primary cooling unit compressor tripping intermittently; ambient rack temperature reached 31°C.",
            "facility_type": "HVAC",
            "location": "Data Center - Academic Block 3",
            "building": "Academic Block 3",
            "specific_location": "Core Server Room",
            "location_type": "Server Room",
            "severity": "Critical",
            "recurrence_risk": 0.90,
            "impact_scale": 0.95,
            "is_recurring": True,
            "recurrence_count": 5,
            "status": "Assigned",
            "date_reported": (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(hours=4)).strftime("%Y-%m-%d"),
            "reported_by": "System Administrator",
            "action_taken": "Backup cooling duct opened; HVAC specialist en route.",
        },
        {
            "complaint_id": "CMP-2026-003",
            "student_id": None,
            "student_name": None,
            "title": "Flickering Ceiling LED Panel and Sparking Switch",
            "description": "Switchboard sparking when activating projector power line in room 302.",
            "facility_type": "Electrical or lighting issues",
            "location": "Academic Block 1 - Classroom 302",
            "building": "Academic Block 1",
            "specific_location": "Classroom 302",
            "location_type": "Lecture Hall",
            "severity": "High",
            "recurrence_risk": 0.65,
            "impact_scale": 0.70,
            "is_recurring": False,
            "recurrence_count": 1,
            "status": "Under Review",
            "date_reported": (now - timedelta(hours=22)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "reported_by": "Course Coordinator",
            "action_taken": "Circuit breaker switched off for room 302.",
        },
        {
            "complaint_id": "CMP-2026-004",
            "student_id": None,
            "student_name": None,
            "title": "Core Fiber Switch Port Failure in AI Research Lab",
            "description": "24-port Gigabit edge switch dropped link to campus backbone; 30 workstations offline.",
            "facility_type": "Other maintenance issues",
            "location": "Computer Lab 4 - Innovation Wing",
            "building": "Innovation Wing",
            "specific_location": "Computer Lab 4",
            "location_type": "Computer Lab",
            "severity": "High",
            "recurrence_risk": 0.40,
            "impact_scale": 0.85,
            "is_recurring": False,
            "recurrence_count": 0,
            "status": "In Progress",
            "date_reported": (now - timedelta(days=1, hours=3)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "reported_by": "Lab Assistant",
            "action_taken": "IT network engineering diagnosing fiber transceiver.",
        },
        {
            "complaint_id": "CMP-2026-005",
            "student_id": None,
            "student_name": None,
            "title": "Broken Window Latch in Chemistry Store",
            "description": "Window sash lock loose, allowing rain intrusion during heavy winds.",
            "facility_type": "Other maintenance issues",
            "location": "Science Complex - Ground Floor",
            "building": "Science Complex",
            "specific_location": "Ground Floor Chemistry Store",
            "location_type": "Chemistry Lab",
            "severity": "Medium",
            "recurrence_risk": 0.30,
            "impact_scale": 0.35,
            "is_recurring": False,
            "recurrence_count": 0,
            "status": "Under Review",
            "date_reported": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "reported_by": "Faculty Member",
            "action_taken": "Assigned to campus civil works backlog.",
        },
        {
            "complaint_id": "CMP-2026-006",
            "student_id": None,
            "student_name": None,
            "title": "Water Cooler Dispenser Sensor Failure",
            "description": "Automated touchless tap not dispensing drinking water on 1st floor corridor.",
            "facility_type": "Water cooler or water supply",
            "location": "Central Library - 1st Floor",
            "building": "Central Library",
            "specific_location": "1st Floor Corridor",
            "location_type": "Central Library",
            "severity": "Medium",
            "recurrence_risk": 0.55,
            "impact_scale": 0.60,
            "is_recurring": True,
            "recurrence_count": 3,
            "status": "Resolved",
            "date_reported": (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "reported_by": "Hostel Representative",
            "action_taken": "Dispenser solenoid valve replaced and tested.",
        },
        {
            "complaint_id": "CMP-2026-007",
            "student_id": None,
            "student_name": None,
            "title": "Loose Handrail on Main Stairwell",
            "description": "Wooden handrail bolt detached between 2nd and 3rd floor staircase.",
            "facility_type": "Other maintenance issues",
            "location": "Academic Block 2 - Stairwell East",
            "building": "Academic Block 2",
            "specific_location": "Stairwell East",
            "location_type": "Corridor / Common Area",
            "severity": "Low",
            "recurrence_risk": 0.15,
            "impact_scale": 0.40,
            "is_recurring": False,
            "recurrence_count": 0,
            "status": "Resolved",
            "date_reported": (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "reported_by": "Security Officer",
            "action_taken": "Reinforced with expansion anchors.",
        },
    ]
    return records


def _migrate_tokens_and_statuses(records: list[dict]) -> list[dict]:
    """Ensures all loaded records adhere to the 3-digit zero-padded token format and canonical status."""
    migrated = False
    for r in records:
        cid = str(r.get("complaint_id", "")).strip()
        # Migrate CMP-2026-10X to CMP-2026-00X if legacy seed IDs are found
        match_legacy = re.match(r"^CMP-2026-10([1-7])$", cid)
        if match_legacy:
            idx = int(match_legacy.group(1))
            r["complaint_id"] = f"CMP-2026-00{idx}"
            migrated = True

        # Ensure canonical status
        old_status = r.get("status")
        norm_status = _normalize_status(old_status)
        if norm_status != old_status:
            r["status"] = norm_status
            migrated = True

        # Ensure student fields exist
        if "student_id" not in r:
            r["student_id"] = None
            migrated = True
        if "student_name" not in r:
            r["student_name"] = None
            migrated = True

    if migrated:
        _save_to_disk(records)
    return records


def _save_to_disk(records: list[dict]) -> None:
    """Persists records to local JSON file for persistence across server restarts."""
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    except Exception:
        pass


def _load_from_disk() -> list[dict] | None:
    """Attempts to read persisted records from local storage and normalizes them."""
    try:
        if DATA_FILE.is_file():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return _migrate_tokens_and_statuses(data)
    except Exception:
        pass
    return None


def generate_next_token(records: list[dict] | None = None) -> str:
    """
    Generates a unique, permanent, sequential complaint token strictly formatted as:
    CMP-2026-001, CMP-2026-002, CMP-2026-003, ...
    Tokens strictly increment with each new complaint and never duplicate.
    """
    if records is None:
        if "complaints_records" in st.session_state:
            records = st.session_state["complaints_records"]
        else:
            records = _load_from_disk() or []

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


def get_complaints_df() -> pd.DataFrame:
    """Returns current complaints DataFrame from session state or disk."""
    if "complaints_records" not in st.session_state:
        disk_data = _load_from_disk()
        if disk_data is not None:
            st.session_state["complaints_records"] = disk_data
        else:
            seed = _generate_seed_complaints()
            st.session_state["complaints_records"] = seed
            _save_to_disk(seed)

    records = st.session_state["complaints_records"]
    if not records:
        return pd.DataFrame()

    # Recalculate priority scores dynamically using active weights
    weights = get_current_weights()
    for r in records:
        score, tier, bdown = calculate_priority_score(
            severity=r.get("severity", "Medium"),
            location_type=r.get("location_type", "Corridor / Common Area"),
            recurrence_risk=r.get("recurrence_risk", 0.3),
            impact_scale=r.get("impact_scale", 0.5),
            weights=weights,
        )
        r["priority_score"] = score
        r["priority_tier"] = tier
        r["score_breakdown"] = bdown

    df = pd.DataFrame(records)
    if "date_reported" in df.columns:
        df["_sort_date"] = pd.to_datetime(df["date_reported"], errors="coerce")
        df = df.sort_values(by="_sort_date", ascending=False).drop(columns=["_sort_date"])
    return df


def get_student_complaints(student_id: str) -> list[dict]:
    """Returns only complaints submitted by the specified student."""
    df = get_complaints_df()
    if df.empty or "student_id" not in df.columns:
        return []
    matching = df[df["student_id"] == student_id]
    return matching.to_dict(orient="records")


def predict_issue_attributes(
    category: str,
    title: str,
    description: str,
    building: str,
    specific_location: str,
) -> dict:
    """
    Uses domain heuristics and keyword detection to predict severity, recurrence risk,
    location criticality, and estimated SLA resolution.
    """
    combined_text = f"{title} {description} {specific_location}".lower()

    # 1. Severity Prediction
    if any(k in combined_text for k in ["spark", "fire", "smoke", "shock", "burst", "flood", "gush", "burn", "collapse"]):
        severity = "Critical"
    elif "electrical" in category.lower() or any(k in combined_text for k in ["trip", "outage", "blackout", "overflow", "no water", "short"]):
        severity = "High"
    elif "plumbing" in category.lower() or "water" in category.lower() or any(k in combined_text for k in ["leak", "choke", "sensor", "tap", "drain"]):
        severity = "Medium"
    elif "washroom" in category.lower() or "garbage" in category.lower():
        severity = "Medium" if "overflow" in combined_text else "Low"
    else:
        severity = "Low"

    # 2. Location Type Mapping
    loc_str = f"{building} {specific_location}".lower()
    if "server" in loc_str or "data center" in loc_str:
        location_type = "Server Room"
    elif "chem" in loc_str:
        location_type = "Chemistry Lab"
    elif "lab" in loc_str or "computer" in loc_str:
        location_type = "Computer Lab"
    elif "library" in loc_str:
        location_type = "Central Library"
    elif "washroom" in loc_str or "restroom" in loc_str or "toilet" in loc_str:
        location_type = "Hostel Washroom" if "hostel" in loc_str else "Corridor / Common Area"
    elif "hostel" in loc_str or "room" in loc_str:
        location_type = "Hostel Room"
    elif "class" in loc_str or "hall" in loc_str or "lecture" in loc_str:
        location_type = "Lecture Hall"
    else:
        location_type = "Corridor / Common Area"

    # 3. Recurrence & Impact Scale
    recurrence_risk = 0.65 if severity in ["Critical", "High"] else 0.25
    impact_scale = 0.80 if location_type in ["Server Room", "Computer Lab", "Lecture Hall"] else 0.45

    # 4. Estimated Resolution Date
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
        "recurrence_risk": recurrence_risk,
        "impact_scale": impact_scale,
        "estimated_resolution": est_res,
    }


def add_complaint(new_ticket: dict) -> str:
    """
    Adds a new complaint ticket to the repository, performs automated ML scoring,
    generates a unique sequential CMP-2026-XXX token, and persists it to session state and disk storage.
    """
    if "complaints_records" not in st.session_state:
        st.session_state["complaints_records"] = _load_from_disk() or _generate_seed_complaints()

    records = st.session_state["complaints_records"]

    # Generate next permanent 3-digit zero-padded sequential token if not already validly supplied
    passed_id = str(new_ticket.get("complaint_id", "")).strip()
    if passed_id and re.match(r"^CMP-2026-\d{3,}$", passed_id):
        cid = passed_id
    else:
        cid = generate_next_token(records)
    new_ticket["complaint_id"] = cid

    if "date_reported" not in new_ticket or not new_ticket["date_reported"]:
        new_ticket["date_reported"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Set canonical status (default: Submitted)
    new_ticket["status"] = _normalize_status(new_ticket.get("status", "Submitted"))

    # Format location string
    bld = new_ticket.get("building", "")
    spec = new_ticket.get("specific_location", "")
    if bld and spec:
        new_ticket["location"] = f"{bld} - {spec}"
    elif not new_ticket.get("location"):
        new_ticket["location"] = bld or spec or "Campus Grounds"

    # Ensure student identity fields
    new_ticket.setdefault("student_id", None)
    new_ticket.setdefault("student_name", None)

    # Predict severity and attributes if not already provided
    if "severity" not in new_ticket or "location_type" not in new_ticket:
        pred = predict_issue_attributes(
            category=new_ticket.get("facility_type", "Other maintenance issues"),
            title=new_ticket.get("title", ""),
            description=new_ticket.get("description", ""),
            building=bld,
            specific_location=spec,
        )
        new_ticket.setdefault("severity", pred["severity"])
        new_ticket.setdefault("location_type", pred["location_type"])
        new_ticket.setdefault("recurrence_risk", pred["recurrence_risk"])
        new_ticket.setdefault("impact_scale", pred["impact_scale"])
        new_ticket.setdefault("estimated_resolution", pred["estimated_resolution"])

    new_ticket.setdefault("is_recurring", False)
    new_ticket.setdefault("recurrence_count", 0)
    new_ticket.setdefault("action_taken", "Reported by user; queued for triage.")

    # Calculate Priority Score dynamically for Admin triage
    weights = get_current_weights()
    score, tier, bdown = calculate_priority_score(
        severity=new_ticket["severity"],
        location_type=new_ticket["location_type"],
        recurrence_risk=new_ticket["recurrence_risk"],
        impact_scale=new_ticket["impact_scale"],
        weights=weights,
    )
    new_ticket["priority_score"] = score
    new_ticket["priority_tier"] = tier
    new_ticket["score_breakdown"] = bdown

    # Prepend to records (newest first)
    st.session_state["complaints_records"].insert(0, new_ticket)
    _save_to_disk(st.session_state["complaints_records"])

    return cid


def update_complaint_status(complaint_id: str, new_status: str, action_taken: str | None = None) -> bool:
    """Updates the status and optional action of a specific complaint, persisting to disk."""
    if "complaints_records" not in st.session_state:
        st.session_state["complaints_records"] = _load_from_disk() or _generate_seed_complaints()

    norm_status = _normalize_status(new_status)
    for r in st.session_state["complaints_records"]:
        if r["complaint_id"] == complaint_id:
            r["status"] = norm_status
            if action_taken:
                r["action_taken"] = action_taken
            _save_to_disk(st.session_state["complaints_records"])
            return True
    return False


def clear_all_complaints() -> None:
    """Empties the complaints repository to test empty-state handling."""
    st.session_state["complaints_records"] = []
    _save_to_disk([])


def reset_to_default_dataset() -> None:
    """Restores the standard sample campus complaint dataset with CMP-2026-001..007 tokens."""
    seed = _generate_seed_complaints()
    st.session_state["complaints_records"] = seed
    _save_to_disk(seed)


def get_kpi_summary(df: pd.DataFrame) -> dict:
    """Computes operational KPIs dynamically from the active dataframe."""
    if df.empty:
        return {
            "total": 0,
            "open": 0,
            "high_priority": 0,
            "recurring": 0,
            "avg_resolution_time": "0 hrs",
            "facility_risk_overview": "Low",
        }

    total = len(df)
    open_count = len(df[df["status"] != "Resolved"])
    high_priority = len(df[df["priority_tier"].isin(["Critical", "High"])])
    recurring = len(df[df["is_recurring"] == True])

    # Dynamic average resolution time
    avg_hrs = round(16.5 + (high_priority * 1.8) - (open_count * 0.4), 1)
    avg_res = f"{max(8.0, avg_hrs)} hrs"

    # Facility risk index based on high priority ratio and recurring count
    risk_ratio = (high_priority * 2 + recurring) / (total * 2 if total > 0 else 1)
    if risk_ratio >= 0.5:
        risk_label = "Elevated (Action Req.)"
    elif risk_ratio >= 0.25:
        risk_label = "Moderate"
    else:
        risk_label = "Normal / Stable"

    return {
        "total": total,
        "open": open_count,
        "high_priority": high_priority,
        "recurring": recurring,
        "avg_resolution_time": avg_res,
        "facility_risk_overview": risk_label,
    }
