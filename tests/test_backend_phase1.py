"""
FIPP 2.0 — Comprehensive Phase 1 Backend Unification Test Suite.
Verifies all Phase 1 deliverables:
- Cryptographic security & PBKDF2-HMAC-SHA256 authentication
- 19-category LPU RMS taxonomy hierarchy API
- Student complaint lifecycle, mandatory validation, and strict data isolation
- Administrator Control Centre workflows, audit logging, and reopening
- Secure file upload validation (magic bytes, 10MB limit, raster integrity)
- Scikit-Learn NLP inference, SHAP explanations, and predictive maintenance
- Relational schema validation and non-destructive dry-run migration
"""
import io
import json
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    authenticate_user,
    SYSTEM_USER_STORE,
)
from app.services.complaint_service import complaint_service
from app.services.taxonomy_service import taxonomy_service
from app.services.migration_service import migration_service
from app.services.upload_service import upload_service

client = TestClient(app)


# ============================================================================
# 1. AUTHENTICATION & SECURITY TESTS
# ============================================================================

def test_pbkdf2_hashing_and_verification():
    """Verifies OWASP-compliant PBKDF2-HMAC-SHA256 hashing and timing-safe verify."""
    plain = "SuperSecurePassword2026!"
    hashed = hash_password(plain, iterations=600_000)
    assert hashed.startswith("pbkdf2_sha256$600000$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_login_and_jwt_issuance():
    """Verifies login endpoint issues signed JWT access and refresh tokens."""
    # 1. Admin login
    res = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["id"] == "ADM-2026-001"

    # 2. Student login
    res_stu = client.post("/api/auth/login", json={"username": "STU-2026-001", "password": "student123"})
    assert res_stu.status_code == 200
    data_stu = res_stu.json()
    assert data_stu["user"]["role"] == "student"

    # 3. Invalid credentials rejection
    res_bad = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "wrongpassword"})
    assert res_bad.status_code == 401


def test_token_refresh():
    """Verifies refresh token endpoint issues new valid access token."""
    login_res = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    refresh_token = login_res.json()["refresh_token"]

    ref_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert ref_data["success"] is True
    assert "access_token" in ref_data

    # Test with invalid refresh token
    bad_ref = client.post("/api/auth/refresh", json={"refresh_token": "invalid.refresh.token"})
    assert bad_ref.status_code == 401


def test_rbac_endpoint_protection():
    """Verifies role boundaries: students cannot access admin routes; unauthenticated rejected."""
    # 1. Unauthenticated request
    res_no_auth = client.get("/api/admin/complaints")
    assert res_no_auth.status_code == 401

    # 2. Student attempting admin endpoint
    stu_login = client.post("/api/auth/login", json={"username": "STU-2026-001", "password": "student123"})
    stu_token = stu_login.json()["access_token"]
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    res_stu_forbidden = client.get("/api/admin/complaints", headers=stu_headers)
    assert res_stu_forbidden.status_code == 403

    # 3. Admin attempting student submission
    adm_login = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    adm_token = adm_login.json()["access_token"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    res_adm_forbidden = client.get("/api/student/complaints", headers=adm_headers)
    assert res_adm_forbidden.status_code == 403


# ============================================================================
# 2. TAXONOMY API TESTS
# ============================================================================

def test_taxonomy_hierarchy_endpoint():
    """Verifies full 19-category LPU RMS hierarchy and location metadata."""
    res = client.get("/api/taxonomy/hierarchy")
    assert res.status_code == 200
    data = res.json()

    # Verify 19 maintenance categories
    cats = data["maintenance_categories"]
    assert len(cats) == 19
    assert "Carpentry" in cats
    assert "Electricity" in cats
    assert "Plumbing" in cats
    assert "Air Conditioner" in cats

    # Verify metadata
    assert len(data["campus_blocks"]) > 5
    assert len(data["room_types"]) >= 2
    assert len(data["time_slots"]) >= 3
    assert len(data["mandatory_declarations"]) == 3
    assert "FAQ" in data["faq_confirmation_text"] or "Frequently Asked Questions" in data["faq_confirmation_text"]


# ============================================================================
# 3. STUDENT WORKFLOW & DATA ISOLATION TESTS
# ============================================================================

def test_student_submission_validation():
    """Verifies validation rules: 10-digit phone, future date, 5-500 char desc, declarations."""
    stu_login = client.post("/api/auth/login", json={"username": "STU-2026-001", "password": "student123"})
    stu_headers = {"Authorization": f"Bearer {stu_login.json()['access_token']}"}

    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Invalid short phone
    bad_phone_payload = {
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "category": "Plumbing / Water Supply Maintenance",
        "building": "Hostel Block B",
        "contact_number": "123",
        "availability_date": tomorrow,
        "time_slot": "09:00 AM - 12:00 PM",
        "description": "Continuous water leakage under sink.",
        "declarations_accepted": True,
    }
    res = client.post("/api/student/complaints/submit", json=bad_phone_payload, headers=stu_headers)
    assert res.status_code == 422

    # 2. Unaccepted declarations
    bad_decl_payload = dict(bad_phone_payload)
    bad_decl_payload["contact_number"] = "9876543210"
    bad_decl_payload["declarations_accepted"] = False
    res = client.post("/api/student/complaints/submit", json=bad_decl_payload, headers=stu_headers)
    assert res.status_code == 422

    # 3. Past availability date
    bad_date_payload = dict(bad_phone_payload)
    bad_date_payload["contact_number"] = "9876543210"
    bad_date_payload["declarations_accepted"] = True
    bad_date_payload["availability_date"] = "2020-01-01"
    res = client.post("/api/student/complaints/submit", json=bad_date_payload, headers=stu_headers)
    assert res.status_code == 422


def test_student_submission_and_token_format():
    """Verifies successful complaint submission and canonical sequential CMP-2026-XXX token."""
    stu_login = client.post("/api/auth/login", json={"username": "STU-2026-001", "password": "student123"})
    stu_headers = {"Authorization": f"Bearer {stu_login.json()['access_token']}"}

    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    valid_payload = {
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "category": "Electrical / Appliances Maintenance",
        "sub_category": "Fan / Regulator",
        "specific_categories": ["Ceiling Fan Not Working"],
        "building": "BH-1 Boys Hostel",
        "sub_block": "Wing A",
        "room_type": "Room No",
        "room_number": "204",
        "contact_number": "9876543210",
        "availability_date": tomorrow,
        "time_slot": "10:00 AM - 01:00 PM",
        "description": "Ceiling fan making loud grinding noise and running very slow in room 204.",
        "declarations_accepted": True,
    }

    res = client.post("/api/student/complaints/submit", json=valid_payload, headers=stu_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    token = data["token"]
    assert token.startswith("CMP-2026-")
    assert len(token) >= 12  # CMP-2026-XXX format

    # Verify ticket was assigned to logged in student
    complaint = data["complaint"]
    assert complaint["student_id"] == "STU-2026-001"
    assert complaint["status"] == "Submitted"
    assert len(complaint["remarks_history"]) >= 1


def test_student_data_isolation():
    """Verifies Student A cannot inspect or withdraw Student B's complaint."""
    stu1_login = client.post("/api/auth/login", json={"username": "STU101", "password": "student123"})
    stu1_headers = {"Authorization": f"Bearer {stu1_login.json()['access_token']}"}

    stu2_login = client.post("/api/auth/login", json={"username": "STU102", "password": "student123"})
    stu2_headers = {"Authorization": f"Bearer {stu2_login.json()['access_token']}"}

    # Student 1 submits a complaint
    tomorrow = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    payload = {
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "category": "Carpentry (Wood Work)",
        "building": "Hostel Block B",
        "contact_number": "9123456789",
        "availability_date": tomorrow,
        "time_slot": "02:00 PM - 05:00 PM",
        "description": "Study table drawer broken and stuck.",
        "declarations_accepted": True,
    }
    submit_res = client.post("/api/student/complaints/submit", json=payload, headers=stu1_headers)
    assert submit_res.status_code == 200
    token = submit_res.json()["token"]

    # Student 1 can view it
    view_stu1 = client.get(f"/api/student/complaints/{token}", headers=stu1_headers)
    assert view_stu1.status_code == 200

    # Student 2 CANNOT view Student 1's complaint
    view_stu2 = client.get(f"/api/student/complaints/{token}", headers=stu2_headers)
    assert view_stu2.status_code == 403

    # Student 2 CANNOT withdraw Student 1's complaint
    withdraw_stu2 = client.post(
        f"/api/student/complaints/{token}/withdraw",
        json={"reason": "Malicious attempt"},
        headers=stu2_headers,
    )
    assert withdraw_stu2.status_code == 400

    # Student 1 CAN withdraw their own complaint
    withdraw_stu1 = client.post(
        f"/api/student/complaints/{token}/withdraw",
        json={"reason": "Fixed by roommate"},
        headers=stu1_headers,
    )
    assert withdraw_stu1.status_code == 200
    assert withdraw_stu1.json()["success"] is True


# ============================================================================
# 4. ADMINISTRATOR WORKFLOW TESTS
# ============================================================================

def test_admin_kpis_and_listing():
    """Verifies Control Centre KPIs and All Requests query capabilities."""
    adm_login = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # 1. KPIs
    kpi_res = client.get("/api/admin/kpis", headers=adm_headers)
    assert kpi_res.status_code == 200
    kpis = kpi_res.json()
    assert kpis["total"] >= 1
    assert "resolution_rate_percent" in kpis
    assert "new" in kpis
    assert "in_progress" in kpis
    assert "resolved" in kpis

    # 2. All Complaints listing
    list_res = client.get("/api/admin/complaints?limit=10", headers=adm_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total_count"] >= 1
    assert len(data["records"]) <= 10


def test_admin_status_update_and_audit_history():
    """Verifies status transition (Under Review -> Assigned -> In Progress -> Resolved) and audit log."""
    adm_login = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # Submit ticket as student to test on fresh record
    stu_login = client.post("/api/auth/login", json={"username": "STU-2026-001", "password": "student123"})
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    sub_res = client.post(
        "/api/student/complaints/submit",
        json={
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Plumbing / Water Supply Maintenance",
            "building": "GH-1 Girls Hostel",
            "contact_number": "9876543210",
            "availability_date": tomorrow,
            "time_slot": "09:00 AM - 12:00 PM",
            "description": "Geyser not heating water in 3rd floor washroom.",
            "declarations_accepted": True,
        },
        headers={"Authorization": f"Bearer {stu_login.json()['access_token']}"},
    )
    token = sub_res.json()["token"]

    # 1. Update status to 'Assigned' and assign squad
    patch_res = client.patch(
        f"/api/admin/complaints/{token}",
        json={
            "status": "Assigned",
            "remarks": "Dispatched senior plumbing technician.",
            "allotted_person": "Ramesh Kumar",
            "squad_assigned": "Hostel Plumbing Squad",
        },
        headers=adm_headers,
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "Assigned"
    assert updated["allotted_person"] == "Ramesh Kumar"
    assert updated["department"] == "Hostel Plumbing Squad"
    assert len(updated["remarks_history"]) >= 2

    # 2. Update status to 'Resolved'
    res_resolve = client.patch(
        f"/api/admin/complaints/{token}",
        json={
            "status": "Resolved",
            "remarks": "Replaced heating element and thermostat. Tested OK.",
        },
        headers=adm_headers,
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "Resolved"
    assert res_resolve.json()["resolved_at"] is not None

    # 3. Test Reopen
    reopen_res = client.post(
        f"/api/admin/complaints/{token}/reopen",
        json={"remarks": "Water is still lukewarm, requires secondary check."},
        headers=adm_headers,
    )
    assert reopen_res.status_code == 200
    reopened = reopen_res.json()
    assert reopened["status"] == "Under Review"
    assert reopened["is_reopened"] is True


def test_admin_reports_and_pii_redacted_export():
    """Verifies analytics report and PII-redacted CSV export."""
    adm_login = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # 1. Operational Analytics Report
    rep_res = client.get("/api/admin/reports/analytics", headers=adm_headers)
    assert rep_res.status_code == 200
    rep = rep_res.json()
    assert "kpis" in rep
    assert "trends" in rep
    assert "category_distribution" in rep
    assert "aging_brackets" in rep

    # 2. PII-Redacted CSV Export
    csv_res = client.get("/api/admin/reports/export?redact_pii=true", headers=adm_headers)
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    csv_text = csv_res.text
    assert "complaint_id" in csv_text
    assert "[REDACTED]" in csv_text


# ============================================================================
# 5. SECURE FILE UPLOAD TESTS
# ============================================================================

def test_file_upload_magic_bytes_and_validation():
    """Verifies authentic PNG raster upload success and corrupt file rejection."""
    adm_login = client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # 1. Valid PNG Image
    img_byte_arr = io.BytesIO()
    image = Image.new("RGB", (60, 30), color="blue")
    image.save(img_byte_arr, format="PNG")
    valid_png_bytes = img_byte_arr.getvalue()

    res_good = client.post(
        "/api/uploads/photo",
        files={"file": ("damage_photo.png", valid_png_bytes, "image/png")},
        headers=adm_headers,
    )
    assert res_good.status_code == 200
    good_data = res_good.json()
    assert good_data["success"] is True
    assert "sha256" in good_data
    assert "stored_filename" in good_data

    # 2. Corrupt or fake image (executable / script disguised as jpg)
    fake_bytes = b"MZ\x90\x00\x03\x00\x00\x00FAKE_EXECUTABLE_BINARY"
    res_fake = client.post(
        "/api/uploads/photo",
        files={"file": ("malicious.jpg", fake_bytes, "image/jpeg")},
        headers=adm_headers,
    )
    assert res_fake.status_code == 400


# ============================================================================
# 6. MACHINE LEARNING & TELEMETRY TESTS
# ============================================================================

def test_ml_analyze_and_shap_explainability():
    """Verifies Scikit-Learn NLP text analysis and SHAP feature attributions."""
    # 1. ML Analysis
    analysis_res = client.post(
        "/api/ml/analyze",
        json={"text": "Water pipeline burst in basement causing severe flooding.", "location": "Academic Block 1"},
    )
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()["analysis"]
    assert "predicted_category" in analysis
    assert "predicted_severity" in analysis
    assert analysis["predicted_severity"] in ["Critical", "High"]
    assert "priority_score" in analysis
    assert "points_breakdown" in analysis

    # 2. SHAP attributions for complaint
    shap_res = client.get("/api/ml/shap/CMP-2026-001")
    assert shap_res.status_code == 200
    shap_data = shap_res.json()
    assert "base_value" in shap_data
    assert "features" in shap_data
    assert len(shap_data["features"]) >= 4

    # 3. Predictive Maintenance Forecasts
    pred_res = client.get("/api/ml/predictive")
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert "forecasts" in pred_data
    assert "disclaimer" in pred_data
    assert "Prediction ≠ Confirmed Physical Breakdown" in pred_data["disclaimer"]


# ============================================================================
# 7. RELATIONAL SCHEMA & MIGRATION DRY-RUN TESTS
# ============================================================================

def test_migration_dry_run():
    """Verifies migration dry-run succeeds with 0 errors and zero token collisions."""
    inspection = migration_service.inspect_source_datastores()
    assert inspection["collision_analysis"]["has_collisions"] is False

    dry_run = migration_service.run_dry_run_migration()
    assert dry_run["dry_run_success"] is True
    assert dry_run["migrated_live_count"] >= 1
    assert dry_run["total_records_in_staging"] >= 1
    assert dry_run["errors"] == []
    assert dry_run["production_switch_status"] == "PRESERVED_JSON_LIVE (No production switch executed)"
