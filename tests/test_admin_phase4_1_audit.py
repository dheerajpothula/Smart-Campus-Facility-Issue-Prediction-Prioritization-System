"""
FIPP 2.0 — Phase 4.1 Verification Audit Test Suite (Backend API & Unit Tests).
Uses an isolated temporary JSON datastore so live data is never mutated.
"""
import csv
import importlib.util
import io
import json
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.core.config import UPLOAD_DIR
from app.models.data_models import PriorityWeights
from app.services.complaint_service import (
    LOCATION_CRITICALITY_MAP,
    SEVERITY_SCORE_MAP,
    complaint_service,
)

from tests.helpers import admin_headers, setup_isolated_environment, student_headers

client = TestClient(app)
_CTX: dict = {}


@pytest.fixture
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Provides an isolated temporary complaints JSON store and ephemeral accounts for deterministic testing."""
    now = datetime.now()
    seed = [
        {
            "complaint_id": "CMP-2026-001",
            "student_id": "00123456",
            "student_name": "Aarav Sharma",
            "contact_number": "9123456789",
            "category": "Electricity",
            "facility_type": "Electricity",
            "building": "Academic Block 1",
            "location": "Academic Block 1 - Room 302",
            "title": "Sparking switchboard in Room 302",
            "description": "Main switchboard sparking on projector line.",
            "severity": "Critical",
            "location_type": "Server Room",
            "recurrence_risk": 0.8,
            "impact_scale": 0.9,
            "status": "Submitted",
            "date_reported": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "remarks_history": [],
        },
        {
            "complaint_id": "CMP-2026-002",
            "student_id": "00123457",
            "student_name": "Priya Nair",
            "contact_number": "9876543210",
            "category": "Plumbing",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "location": "Hostel Block B - 2nd Floor",
            "title": "Pipe leak in corridor",
            "description": "Continuous pipe leakage in 2nd floor washroom.",
            "severity": "High",
            "location_type": "Hostel Washroom",
            "recurrence_risk": 0.5,
            "impact_scale": 0.6,
            "status": "In Progress",
            "allotted_person": "Ramesh Kumar",
            "department": "Plumbing Squad",
            "date_reported": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "remarks_history": [],
        },
        {
            "complaint_id": "CMP-2026-003",
            "student_id": "00123456",
            "student_name": "Aarav Sharma",
            "contact_number": "9123456789",
            "category": "Air Conditioner",
            "facility_type": "Air Conditioner",
            "building": "Central Library",
            "location": "Central Library - 1st Floor",
            "title": "AC compressor failure",
            "description": "Library reading hall AC not cooling.",
            "severity": "Medium",
            "location_type": "Central Library",
            "recurrence_risk": 0.3,
            "impact_scale": 0.5,
            "priority_tier": "Medium",
            "priority_score": 45.0,
            "status": "Resolved",
            "date_reported": (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"),
            "resolved_at": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "resolved_by": "fipp.admin",
            "closing_remarks": "Replaced capacitor and tested.",
            "estimated_resolution": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "remarks_history": [],
        },
        {
            "complaint_id": "CMP-2026-004",
            "student_id": "00123457",
            "student_name": "Priya Nair",
            "contact_number": "9876543210",
            "category": "Carpentry",
            "facility_type": "Carpentry",
            "building": "GH-1 Girls Hostel",
            "location": "GH-1 Girls Hostel - Room 302",
            "title": "Loose cupboard hinge",
            "description": "Cupboard door hinge loose.",
            "severity": "Low",
            "location_type": "Hostel Room",
            "recurrence_risk": 0.1,
            "impact_scale": 0.2,
            "priority_tier": "Low",
            "priority_score": 25.0,
            "status": "Withdrawn",
            "date_reported": (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M"),
            "estimated_resolution": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "remarks_history": [],
        },
    ]
    env = setup_isolated_environment(tmp_path, monkeypatch, seed_complaints=seed)
    _CTX.clear()
    _CTX.update(env)
    return env["data_file"]


def _adm_headers() -> dict:
    return admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])


def _stu_headers(sid: str) -> dict:
    name = "Aarav Sharma" if sid == "00123456" else "Priya Nair"
    return student_headers(client, name, sid)


def test_admin_rbac_and_unauthorized_actions(isolated_store):
    stu_headers = _stu_headers("00123456")

    admin_gets = [
        "/api/admin/kpis",
        "/api/admin/complaints",
        "/api/admin/complaints/unassigned",
        "/api/admin/complaints/in-progress",
        "/api/admin/complaints/resolved",
        "/api/admin/complaints/CMP-2026-001",
        "/api/admin/reports/analytics",
        "/api/admin/reports/export",
    ]
    for endpoint in admin_gets:
        assert client.get(endpoint).status_code == 401
        assert client.get(endpoint, headers=stu_headers).status_code == 403

    # Unauthenticated and student blocked from admin mutations
    assert client.patch("/api/admin/complaints/CMP-2026-001", json={"status": "Assigned"}).status_code == 401
    assert client.patch("/api/admin/complaints/CMP-2026-001", json={"status": "Assigned"}, headers=stu_headers).status_code == 403
    assert client.post("/api/admin/complaints/CMP-2026-003/reopen", json={"remarks": "Still broken"}).status_code == 401
    assert client.post("/api/admin/complaints/CMP-2026-003/reopen", json={"remarks": "Still broken"}, headers=stu_headers).status_code == 403


def test_assignment_persistence_and_clearing(isolated_store):
    adm_headers = _adm_headers()

    res = client.patch(
        "/api/admin/complaints/CMP-2026-001",
        json={
            "status": "Assigned",
            "remarks": "Dispatched electrical lead.",
            "allotted_person": "Vikram Mehta",
            "squad_assigned": "Electrical Squad A",
        },
        headers=adm_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["allotted_person"] == "Vikram Mehta"
    assert body["department"] == "Electrical Squad A"
    assert body["remarks_history"][0]["new_status"] == "Assigned"
    assert "fipp.admin" in body["remarks_history"][0]["name"]

    # Clearing technician and squad persists null
    clear_res = client.patch(
        "/api/admin/complaints/CMP-2026-001",
        json={
            "status": "Under Review",
            "remarks": "Reassigning technician.",
            "allotted_person": "",
            "squad_assigned": "",
        },
        headers=adm_headers,
    )
    assert clear_res.status_code == 200
    assert clear_res.json()["allotted_person"] is None
    assert clear_res.json()["department"] is None


def test_resolution_remarks_and_reopening_history(isolated_store):
    adm_headers = _adm_headers()

    # 1. Resolving without remarks is rejected at API boundary
    bad_resolve = client.patch(
        "/api/admin/complaints/CMP-2026-002",
        json={"status": "Resolved", "remarks": "   "},
        headers=adm_headers,
    )
    assert bad_resolve.status_code == 422

    # 2. Resolving with valid remarks persists timestamp, admin ID, and audit entry
    ok_resolve = client.patch(
        "/api/admin/complaints/CMP-2026-002",
        json={"status": "Resolved", "remarks": "Replaced leaking elbow joint and pressure tested."},
        headers=adm_headers,
    )
    assert ok_resolve.status_code == 200
    resolved = ok_resolve.json()
    assert resolved["status"] == "Resolved"
    assert resolved["resolved_by"] == "fipp.admin"
    assert resolved["closing_remarks"] == "Replaced leaking elbow joint and pressure tested."
    assert resolved["resolved_at"] is not None

    # 3. Reopening a non-Resolved ticket fails
    bad_reopen = client.post(
        "/api/admin/complaints/CMP-2026-001/reopen",
        json={"remarks": "Cannot reopen submitted ticket"},
        headers=adm_headers,
    )
    assert bad_reopen.status_code == 400

    # 4. Reopening requires >=3 chars
    short_reopen = client.post(
        "/api/admin/complaints/CMP-2026-002/reopen",
        json={"remarks": "no"},
        headers=adm_headers,
    )
    assert short_reopen.status_code == 422

    # 5. Valid reopen transitions to Under Review and preserves prior resolution history
    reopen_res = client.post(
        "/api/admin/complaints/CMP-2026-002/reopen",
        json={"remarks": "Minor seepage observed again after 2 hours."},
        headers=adm_headers,
    )
    assert reopen_res.status_code == 200
    reopened = reopen_res.json()
    assert reopened["status"] == "Under Review"
    assert reopened["is_reopened"] is True
    assert reopened["original_resolved_at"] == resolved["resolved_at"]
    assert reopened["original_resolved_by"] == "fipp.admin"
    assert reopened["previous_closing_remarks"] == "Replaced leaking elbow joint and pressure tested."
    assert len(reopened["remarks_history"]) == 2
    assert "Ticket Reopened" in reopened["remarks_history"][0]["remarks"]


def test_student_satisfaction_rating_authorization(isolated_store):
    adm_headers = _adm_headers()
    stu1_headers = _stu_headers("00123456")
    stu2_headers = _stu_headers("00123457")

    # Admin cannot submit student feedback
    assert client.post(
        "/api/student/complaints/CMP-2026-003/feedback",
        json={"rating": 5, "comments": "Admin attempt"},
        headers=adm_headers,
    ).status_code == 403

    # Student 2 cannot rate Student 1's resolved complaint
    assert client.post(
        "/api/student/complaints/CMP-2026-003/feedback",
        json={"rating": 1, "comments": "Wrong student"},
        headers=stu2_headers,
    ).status_code == 400

    # Student 1 cannot rate their own non-resolved complaint
    assert client.post(
        "/api/student/complaints/CMP-2026-001/feedback",
        json={"rating": 4, "comments": "Not resolved yet"},
        headers=stu1_headers,
    ).status_code == 400

    # Student 1 CAN rate their own resolved complaint
    ok_fb = client.post(
        "/api/student/complaints/CMP-2026-003/feedback",
        json={"rating": 5, "comments": "AC cooling restored."},
        headers=stu1_headers,
    )
    assert ok_fb.status_code == 200
    detail = client.get("/api/student/complaints/CMP-2026-003", headers=stu1_headers).json()
    assert detail["feedback"]["rating"] == 5
    assert detail["feedback"]["student_id"] == "00123456"


def test_attachment_ownership_isolation(isolated_store):
    stu1_headers = _stu_headers("00123456")
    stu2_headers = _stu_headers("00123457")
    adm_headers = _adm_headers()

    img_bytes = io.BytesIO()
    Image.new("RGB", (20, 20), color="red").save(img_bytes, format="PNG")
    up_res = client.post(
        "/api/uploads/photo",
        files={"file": ("leak.png", img_bytes.getvalue(), "image/png")},
        headers=stu1_headers,
    )
    assert up_res.status_code == 200
    stored_name = up_res.json()["stored_filename"]

    try:
        # Attach stored_name to STU101's complaint CMP-2026-001
        records = json.loads(isolated_store.read_text(encoding="utf-8"))
        records[0]["photo_stored_filename"] = stored_name
        isolated_store.write_text(json.dumps(records, indent=2), encoding="utf-8")

        # Owner STU101 and Admin can retrieve; STU102 is forbidden
        assert client.get(f"/api/uploads/{stored_name}", headers=stu1_headers).status_code == 200
        assert client.get(f"/api/uploads/{stored_name}", headers=adm_headers).status_code == 200
        assert client.get(f"/api/uploads/{stored_name}", headers=stu2_headers).status_code == 403
        assert client.get(f"/api/uploads/{stored_name}").status_code == 401
    finally:
        uploaded_path = UPLOAD_DIR / stored_name
        if uploaded_path.is_file():
            uploaded_path.unlink()


def test_report_metric_calculations_and_trends(isolated_store):
    adm_headers = _adm_headers()

    # Daily analytics
    daily = client.get("/api/admin/reports/analytics?trend_agg=Daily", headers=adm_headers).json()
    kpis = daily["kpis"]
    assert kpis["total"] == 4
    assert kpis["new"] == 1
    assert kpis["in_progress"] == 1
    assert kpis["resolved"] == 1
    assert kpis["withdrawn"] == 1
    # Resolution rate excludes Withdrawn: 1 / (4 - 1) = 33.3%
    assert kpis["resolution_rate_percent"] == 33.3
    # Turnaround from CMP-2026-003 (4 days ago -> 1 day ago = 3.0 days)
    assert kpis["average_turnaround_days"] == 3.0

    # Priority distribution uses genuine MCPI tiers, not all Medium
    assert daily["priority_distribution"]["Critical"] == 1
    assert daily["priority_distribution"]["High"] == 1
    assert daily["priority_distribution"]["Medium"] == 1
    assert daily["priority_distribution"]["Low"] == 1

    # Aging brackets exclude Resolved and Withdrawn -> only 001 (<24h) and 002 (1-3d)
    assert daily["aging_brackets"]["<24h"] == 1
    assert daily["aging_brackets"]["1–3d"] == 1
    assert daily["aging_brackets"]["3–7d"] == 0
    assert daily["aging_brackets"][">7d"] == 0

    # Weekly & Monthly grouping produce distinct period formats
    weekly = client.get("/api/admin/reports/analytics?trend_agg=Weekly", headers=adm_headers).json()
    assert any("-W" in pt["period"] for pt in weekly["trends"])

    monthly = client.get("/api/admin/reports/analytics?trend_agg=Monthly", headers=adm_headers).json()
    assert all(len(pt["period"]) == 7 for pt in monthly["trends"])

    # When no resolved tickets exist in filter, turnaround is None (never fabricated)
    open_only = client.get("/api/admin/reports/analytics?status=Submitted", headers=adm_headers).json()
    assert open_only["kpis"]["average_turnaround_days"] is None


def test_csv_privacy_and_filter_behavior(isolated_store):
    adm_headers = _adm_headers()

    # Filtered CSV export respects status & category filters and masks PII
    res = client.get(
        "/api/admin/reports/export?redact_pii=true&status=Resolved&category=Air%20Conditioner",
        headers=adm_headers,
    )
    assert res.status_code == 200
    rows = list(csv.DictReader(io.StringIO(res.text)))
    assert len(rows) == 1
    row = rows[0]
    assert row["complaint_id"] == "CMP-2026-003"
    assert row["student_id"] == "[REDACTED]"
    assert row["student_name"] == "[REDACTED]"
    assert row["contact_number"] == "[REDACTED]"
    # Sensitive/internal fields never exported
    for forbidden_col in ("password", "password_hash", "token", "email", "photo_sha256", "remarks_history"):
        assert forbidden_col not in row
    assert "9123456789" not in res.text
    assert "Rahul Sharma" not in res.text

    # Default export (without explicit redact_pii query param) still masks student PII
    # while retaining operational room/location and technician fields
    default_res = client.get("/api/admin/reports/export", headers=adm_headers)
    assert default_res.status_code == 200
    default_rows = {r["complaint_id"]: r for r in csv.DictReader(io.StringIO(default_res.text))}
    assert default_rows["CMP-2026-002"]["student_id"] == "[REDACTED]"
    assert default_rows["CMP-2026-002"]["student_name"] == "[REDACTED]"
    assert default_rows["CMP-2026-002"]["contact_number"] == "[REDACTED]"
    assert default_rows["CMP-2026-002"]["location"] == "Hostel Block B - 2nd Floor"
    assert default_rows["CMP-2026-002"]["allotted_person"] == "Ramesh Kumar"


def test_mcpi_parity_with_original_priority_scoring():
    """Verifies bit-for-bit parity between pure-Python compute_mcpi and original priority_scoring."""
    sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))
    orig_path = Path("smart-campus-facility-prediction/src/prediction/priority_scoring.py")
    spec = importlib.util.spec_from_file_location("orig_priority_scoring_parity", orig_path)
    orig_mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(orig_mod)

    assert orig_mod.LOCATION_CRITICALITY_MAP == LOCATION_CRITICALITY_MAP
    assert orig_mod.SEVERITY_SCORE_MAP == SEVERITY_SCORE_MAP

    for sev in ["Critical", "High", "Medium", "Low", "Unknown"]:
        for loc in list(LOCATION_CRITICALITY_MAP.keys()) + ["Unknown Zone"]:
            for rec in [-0.2, 0.0, 0.25, 0.65, 1.0, 1.3]:
                for imp in [-0.1, 0.0, 0.45, 0.80, 1.0, 1.2]:
                    expected = orig_mod.calculate_priority_score(
                        severity=sev,
                        location_type=loc,
                        recurrence_risk=rec,
                        impact_scale=imp,
                        weights=orig_mod.PriorityWeights(),
                    )
                    actual = complaint_service.compute_mcpi(
                        severity=sev,
                        location_type=loc,
                        recurrence_risk=rec,
                        impact_scale=imp,
                        weights=PriorityWeights(),
                    )
                    assert actual == expected

    # Verify weight normalization for unnormalized weights
    unnorm = PriorityWeights(
        severity=0.70,
        location_criticality=0.50,
        recurrence_probability=0.50,
        impact_population=0.30,
    )
    norm_res = complaint_service.compute_mcpi("Critical", "Server Room", 0.80, 0.90, weights=unnorm)
    default_res = complaint_service.compute_mcpi("Critical", "Server Room", 0.80, 0.90, weights=PriorityWeights())
    assert norm_res == default_res

    # Verify exact tier thresholds: >=75 Critical, >=50 High, >=28 Medium, <28 Low
    assert complaint_service.compute_mcpi("Critical", "Server Room", 1.0, 1.0)[1] == "Critical"
    assert complaint_service.compute_mcpi("High", "Hostel Room", 0.5, 0.5)[1] == "High"
    assert complaint_service.compute_mcpi("Medium", "Corridor / Common Area", 0.25, 0.45)[1] == "Medium"
    assert complaint_service.compute_mcpi("Low", "Campus Grounds", 0.0, 0.0)[1] == "Low"


def test_in_progress_kpi_and_queue_status_definitions(isolated_store):
    """Verifies Overview KPI counts Under Review + Assigned + In Progress while /in-progress stays Assigned + In Progress."""
    adm_headers = _adm_headers()

    # Reopen CMP-2026-003 -> transitions to Under Review while preserving resolution history
    reopen_res = client.post(
        "/api/admin/complaints/CMP-2026-003/reopen",
        json={"remarks": "Compressor noise returned after restart."},
        headers=adm_headers,
    )
    assert reopen_res.status_code == 200
    reopened = reopen_res.json()
    assert reopened["status"] == "Under Review"
    assert reopened["original_resolved_by"] == "fipp.admin"
    assert reopened["previous_closing_remarks"] == "Replaced capacitor and tested."

    kpis = client.get("/api/admin/kpis", headers=adm_headers).json()
    # CMP-2026-002 (In Progress) + CMP-2026-003 (Under Review) = 2
    assert kpis["in_progress"] == 2
    assert kpis["new"] == 1
    assert kpis["resolved"] == 0
    assert kpis["withdrawn"] == 1
    assert kpis["new"] + kpis["in_progress"] + kpis["resolved"] + kpis["withdrawn"] == kpis["total"]

    queue = client.get("/api/admin/complaints/in-progress", headers=adm_headers).json()
    assert queue["total_count"] == 1
    assert [r["complaint_id"] for r in queue["records"]] == ["CMP-2026-002"]

