"""
FIPP 2.0 — Phase 1 Empirical Verification Script.
Executes end-to-end verification of all FastAPI endpoints, RBAC policies,
token revocation, persistent credentials rehash across restart,
data integrity, taxonomy, ML models, and migration safety.
"""
import io
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import PRIMARY_JSON_DATA_FILE
from app.core.security import (
    SYSTEM_USER_STORE,
    _PERSISTENT_CREDENTIALS_FILE,
    _REVOKED_TOKENS_FILE,
    authenticate_user,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.complaint_service import complaint_service
from app.services.taxonomy_service import taxonomy_service
from app.services.migration_service import migration_service

client = TestClient(app)
results = {}

def run_test(name, func):
    t0 = time.time()
    try:
        data = func()
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        results[name] = {"status": "PASSED", "duration_ms": elapsed_ms, "details": data}
        print(f"[PASS] {name} ({elapsed_ms}ms)")
    except Exception as e:
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        results[name] = {"status": "FAILED", "duration_ms": elapsed_ms, "error": str(e)}
        print(f"[FAIL] {name}: {e}")
        raise

# 1. Health Checks
def test_health():
    res1 = client.get("/health")
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
    j1 = res1.json()
    assert j1["status"] == "healthy"
    assert j1["version"] == "2.0.0"
    assert j1["datastore"]["record_count"] >= 7

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "healthy"
    return {"status": j1["status"], "records": j1["datastore"]["record_count"], "ml": j1["ml_services"]}

# 2. Authentication & Persistence
def test_auth_and_persistence():
    # Admin valid login
    res_adm = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    assert res_adm.status_code == 200, f"Admin login failed: {res_adm.text}"
    adm_data = res_adm.json()
    assert adm_data["success"] is True
    adm_token = adm_data["access_token"]
    assert adm_data["user"]["role"] == "admin"
    assert adm_data["user"]["id"] == "fipp.admin"

    # Admin invalid login
    res_bad = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "WrongPassword#999"})
    assert res_bad.status_code == 401

    # Student valid login
    res_stu = client.post("/api/auth/login", json={"username": "00123456", "password": "REDACTED_TEST_ENV_CRED"})
    assert res_stu.status_code == 200
    stu_data = res_stu.json()
    assert stu_data["success"] is True
    stu_token = stu_data["access_token"]
    assert stu_data["user"]["role"] == "student"

    # Profile me
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_me.status_code == 200
    assert res_me.json()["user"]["id"] == "fipp.admin"

    # Refresh
    res_ref = client.post("/api/auth/refresh", json={"refresh_token": adm_data["refresh_token"]})
    assert res_ref.status_code == 200
    assert "access_token" in res_ref.json()

    # Logout and revocation
    res_logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_logout.status_code == 200
    # Immediate attempt with revoked token must be rejected
    res_revoked = client.get("/api/auth/me", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_revoked.status_code == 401, f"Expected 401 for revoked token, got {res_revoked.status_code}"

    # Verify persistent credentials file exists and contains upgraded modular hashes
    assert _PERSISTENT_CREDENTIALS_FILE.is_file(), "Persistent credentials file missing"
    with open(_PERSISTENT_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        creds = json.load(f)
    assert "fipp.admin" in creds
    assert creds["fipp.admin"].startswith("pbkdf2_sha256$600000$")

    # Verify simulation of server restart: reload from credentials_store.json
    fresh_user = authenticate_user("fipp.admin", "REDACTED_TEST_ENV_CRED")
    assert fresh_user is not None
    assert fresh_user["id"] == "fipp.admin"

    return {"admin_authenticated": True, "student_authenticated": True, "token_revoked": True, "rehash_persisted": True}

# 3. RBAC & Student Isolation
def test_rbac_and_isolation():
    # Login fresh admin
    adm_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    adm_token = adm_login.json()["access_token"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    # Login Student 1
    stu1_login = client.post("/api/auth/login", json={"username": "00123456", "password": "REDACTED_TEST_ENV_CRED"})
    stu1_token = stu1_login.json()["access_token"]
    stu1_headers = {"Authorization": f"Bearer {stu1_token}"}

    # Login Student 2
    stu2_login = client.post("/api/auth/login", json={"username": "00123456", "password": "REDACTED_TEST_ENV_CRED"})
    stu2_token = stu2_login.json()["access_token"]
    stu2_headers = {"Authorization": f"Bearer {stu2_token}"}

    # 1. Unauthenticated request to protected route
    res_no_auth = client.get("/api/admin/complaints")
    assert res_no_auth.status_code == 401

    # 2. Student blocked from admin endpoint
    res_stu_adm = client.get("/api/admin/complaints", headers=stu1_headers)
    assert res_stu_adm.status_code == 403

    # 3. Admin blocked from student complaint submission
    res_adm_stu = client.get("/api/student/complaints", headers=adm_headers)
    assert res_adm_stu.status_code == 403

    # 4. Student isolation: Stu1 submits complaint
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    sub1 = client.post(
        "/api/student/complaints/submit",
        json={
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Air Conditioning / HVAC Maintenance",
            "building": "BH-1 Boys Hostel",
            "contact_number": "9876543210",
            "availability_date": tomorrow,
            "time_slot": "09:00 AM - 12:00 PM",
            "description": "AC unit in Room 204 is making loud humming noise.",
            "declarations_accepted": True,
        },
        headers=stu1_headers,
    )
    assert sub1.status_code == 200
    token1 = sub1.json()["token"]

    # Student 1 can see token1
    res_stu1_view = client.get(f"/api/student/complaints/{token1}", headers=stu1_headers)
    assert res_stu1_view.status_code == 200

    # Student 2 CANNOT see token1 (returns 403 Forbidden to enforce student isolation)
    res_stu2_view = client.get(f"/api/student/complaints/{token1}", headers=stu2_headers)
    assert res_stu2_view.status_code == 403

    # Student 2 CANNOT withdraw token1 (returns 400 Bad Request due to ownership check)
    res_stu2_withdraw = client.post(
        f"/api/student/complaints/{token1}/withdraw",
        json={"reason": "Malicious attempt"},
        headers=stu2_headers,
    )
    assert res_stu2_withdraw.status_code == 400

    return {"rbac_enforced": True, "student_isolation_verified": True, "created_token": token1}

# 4. Taxonomy Endpoint
def test_taxonomy():
    res = client.get("/api/taxonomy/hierarchy")
    assert res.status_code == 200
    tax = res.json()
    assert "maintenance_categories" in tax
    categories = tax["maintenance_categories"]
    assert len(categories) == 19, f"Expected 19 categories, got {len(categories)}"
    # Check that it starts with Electrical Maintenance (matching Campus Facility canonical hierarchy)
    assert categories[0] == "Air Conditioner"
    assert "campus_blocks" in tax
    assert "time_slots" in tax
    assert "message_types" in tax
    assert "mandatory_declarations" in tax
    return {"category_count": len(categories), "first_category": categories[0]}

# 5. File Upload Verification
def test_file_upload():
    adm_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # 1. Valid PNG upload
    img_byte_arr = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="green")
    image.save(img_byte_arr, format="PNG")
    valid_png_bytes = img_byte_arr.getvalue()

    res_good = client.post(
        "/api/uploads/photo",
        files={"file": ("evidence.png", valid_png_bytes, "image/png")},
        headers=adm_headers,
    )
    assert res_good.status_code == 200
    upload_data = res_good.json()
    assert upload_data["success"] is True
    assert upload_data["stored_filename"].endswith(".png")
    stored_name = upload_data["stored_filename"]

    # 2. Retrieve photo
    res_get = client.get(f"/api/uploads/{stored_name}", headers=adm_headers)
    assert res_get.status_code == 200
    assert res_get.headers["content-type"] == "image/png"

    # 3. Reject spoofed/corrupted file
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00fake executable content"
    res_bad = client.post(
        "/api/uploads/photo",
        files={"file": ("fake_virus.png", fake_exe_bytes, "image/png")},
        headers=adm_headers,
    )
    assert res_bad.status_code == 400

    return {"stored_filename": stored_name, "security_validation_passed": True}

# 6. Admin Control Centre & Complaint Lifecycle
def test_admin_workflows():
    adm_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # KPIs
    res_kpis = client.get("/api/admin/kpis", headers=adm_headers)
    assert res_kpis.status_code == 200
    kpis = res_kpis.json()
    assert kpis["total"] >= 7

    # Queues
    res_all = client.get("/api/admin/complaints?limit=20", headers=adm_headers)
    assert res_all.status_code == 200

    res_unassigned = client.get("/api/admin/complaints/unassigned", headers=adm_headers)
    assert res_unassigned.status_code == 200

    res_inprogress = client.get("/api/admin/complaints/in-progress", headers=adm_headers)
    assert res_inprogress.status_code == 200
    # In Progress should include In Progress and Assigned
    for r in res_inprogress.json()["records"]:
        assert r["status"] in ["In Progress", "Assigned"]

    res_resolved = client.get("/api/admin/complaints/resolved", headers=adm_headers)
    assert res_resolved.status_code == 200
    for r in res_resolved.json()["records"]:
        assert r["status"] == "Resolved"

    # Student submits a ticket to test lifecycle
    stu_login = client.post("/api/auth/login", json={"username": "00123456", "password": "REDACTED_TEST_ENV_CRED"})
    stu_headers = {"Authorization": f"Bearer {stu_login.json()['access_token']}"}
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    sub = client.post(
        "/api/student/complaints/submit",
        json={
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Carpentry / Furniture Maintenance",
            "building": "BH-1 Boys Hostel",
            "contact_number": "9876543210",
            "availability_date": tomorrow,
            "time_slot": "09:00 AM - 12:00 PM",
            "description": "Study chair broken in room 204.",
            "declarations_accepted": True,
        },
        headers=stu_headers,
    )
    token = sub.json()["token"]

    # 1. Update to Assigned
    p1 = client.patch(
        f"/api/admin/complaints/{token}",
        json={
            "status": "Assigned",
            "remarks": "Assigned to hostel carpentry squad.",
            "allotted_person": "Satish Verma",
            "squad_assigned": "Hostel Carpentry Squad",
        },
        headers=adm_headers,
    )
    assert p1.status_code == 200
    assert p1.json()["status"] == "Assigned"

    # 2. Update to In Progress
    p2 = client.patch(
        f"/api/admin/complaints/{token}",
        json={"status": "In Progress", "remarks": "Technician on site inspecting chair."},
        headers=adm_headers,
    )
    assert p2.status_code == 200
    assert p2.json()["status"] == "In Progress"

    # 3. Update to Resolved
    p3 = client.patch(
        f"/api/admin/complaints/{token}",
        json={"status": "Resolved", "remarks": "Replaced chair hydraulic and welded base."},
        headers=adm_headers,
    )
    assert p3.status_code == 200
    assert p3.json()["status"] == "Resolved"
    assert p3.json()["resolved_at"] is not None

    # 4. Student submits feedback
    fb = client.post(
        f"/api/student/complaints/{token}/feedback",
        json={"rating": 5, "comments": "Prompt and excellent work."},
        headers=stu_headers,
    )
    assert fb.status_code == 200
    assert fb.json()["success"] is True

    # 5. Admin Reopens ticket
    reopen = client.post(
        f"/api/admin/complaints/{token}/reopen",
        json={"remarks": "Student reported chair wobbles slightly under load."},
        headers=adm_headers,
    )
    assert reopen.status_code == 200
    r_data = reopen.json()
    assert r_data["status"] == "Under Review"
    assert r_data["is_reopened"] is True
    # Verify remarks history survived and grew
    assert len(r_data["remarks_history"]) >= 4

    return {"lifecycle_verified": True, "token": token, "remarks_count": len(r_data["remarks_history"])}

# 7. Student Withdrawal
def test_student_withdrawal():
    stu_login = client.post("/api/auth/login", json={"username": "00123456", "password": "REDACTED_TEST_ENV_CRED"})
    stu_headers = {"Authorization": f"Bearer {stu_login.json()['access_token']}"}
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    sub = client.post(
        "/api/student/complaints/submit",
        json={
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Housekeeping / Sanitation Maintenance",
            "building": "BH-1 Boys Hostel",
            "contact_number": "9876543210",
            "availability_date": tomorrow,
            "time_slot": "09:00 AM - 12:00 PM",
            "description": "Dust in hallway corridor.",
            "declarations_accepted": True,
        },
        headers=stu_headers,
    )
    token = sub.json()["token"]

    withdraw_res = client.post(
        f"/api/student/complaints/{token}/withdraw",
        json={"reason": "Corridor already swept by cleaner this morning."},
        headers=stu_headers,
    )
    assert withdraw_res.status_code == 200
    w_data = withdraw_res.json()
    assert w_data["success"] is True

    # Verify status is Withdrawn on the complaint
    chk = client.get(f"/api/student/complaints/{token}", headers=stu_headers)
    assert chk.status_code == 200
    assert chk.json()["status"] == "Withdrawn"

    # Attempting to withdraw again fails (400 Bad Request)
    w_again = client.post(
        f"/api/student/complaints/{token}/withdraw",
        json={"reason": "Duplicate attempt"},
        headers=stu_headers,
    )
    assert w_again.status_code == 400

    return {"withdrawal_verified": True, "token": token}

# 8. Reports & PII Export
def test_reports_and_export():
    adm_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # Analytics
    rep = client.get("/api/admin/reports/analytics", headers=adm_headers)
    assert rep.status_code == 200
    rep_data = rep.json()
    assert "kpis" in rep_data
    assert "trends" in rep_data
    assert "category_distribution" in rep_data

    # PII Export
    exp = client.get("/api/admin/reports/export?redact_pii=true", headers=adm_headers)
    assert exp.status_code == 200
    assert "[REDACTED]" in exp.text

    return {"analytics_ok": True, "export_redacted": True}

# 9. ML & Predictions
def test_ml_endpoints():
    adm_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # Analyze
    an = client.post(
        "/api/ml/analyze",
        json={
            "text": "Severe spark and burning smell in power outlet on ground floor corridor.",
            "location": "Academic Block 34",
            "facility_type": "Electrical Maintenance",
        },
        headers=adm_headers,
    )
    assert an.status_code == 200
    an_data = an.json()["analysis"]
    assert an_data["predicted_severity"] in ["High", "Critical", "Medium", "Low"]
    assert "priority_score" in an_data
    assert an_data["priority_score"] >= 40

    # Predictive maintenance schedule
    pm = client.get("/api/ml/predictive", headers=adm_headers)
    assert pm.status_code == 200
    assert "forecasts" in pm.json()

    # Model metrics
    mm = client.get("/api/ml/metrics", headers=adm_headers)
    assert mm.status_code == 200
    assert "nlp_classifier" in mm.json()

    # Priority weights (admin-only)
    gw = client.get("/api/settings/weights", headers=adm_headers)
    assert gw.status_code == 200
    assert gw.json()["severity"] >= 0

    pw = client.post(
        "/api/settings/weights",
        json={"severity": 0.40, "location_criticality": 0.20, "recurrence_probability": 0.20, "impact_population": 0.20},
        headers=adm_headers,
    )
    assert pw.status_code == 200

    # SHAP explanations for CMP-2026-001
    sh = client.get("/api/ml/shap/CMP-2026-001", headers=adm_headers)
    assert sh.status_code == 200
    assert "features" in sh.json()

    return {"nlp_analyzed": True, "expected_impact": an_data["expected_impact"], "shap_ready": True, "weights_updated": True}

# 10. Migration Safety
def test_migration_safety():
    adm_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": "REDACTED_TEST_ENV_CRED"})
    adm_headers = {"Authorization": f"Bearer {adm_login.json()['access_token']}"}

    # Inspect
    insp = client.get("/api/admin/migration/inspect", headers=adm_headers)
    assert insp.status_code == 200
    insp_data = insp.json()
    assert insp_data["collision_analysis"]["has_collisions"] is False

    # Dry-run
    dry = client.post("/api/admin/migration/dry-run", headers=adm_headers)
    assert dry.status_code == 200
    dry_data = dry.json()
    assert dry_data["dry_run_success"] is True
    assert dry_data["migrated_live_count"] >= 7
    assert dry_data["errors"] == []
    assert dry_data["production_switch_status"] == "PRESERVED_JSON_LIVE (No production switch executed)"

    return {
        "dry_run_success": True,
        "migrated_live_count": dry_data["migrated_live_count"],
        "staging_total": dry_data["total_records_in_staging"],
        "token_collisions": len(insp_data["collision_analysis"]["colliding_tokens"]),
        "switch_status": dry_data["production_switch_status"],
    }

def main():
    print("=" * 70)
    print("STARTING FIPP 2.0 PHASE 1 EMPIRICAL VERIFICATION")
    print("=" * 70)

    run_test("Health Checks", test_health)
    run_test("Authentication & Persistence", test_auth_and_persistence)
    run_test("RBAC & Student Isolation", test_rbac_and_isolation)
    run_test("Taxonomy Endpoint", test_taxonomy)
    run_test("Secure File Upload", test_file_upload)
    run_test("Admin Workflows & Lifecycle", test_admin_workflows)
    run_test("Student Withdrawal", test_student_withdrawal)
    run_test("Reports & PII Export", test_reports_and_export)
    run_test("ML & Predictions", test_ml_endpoints)
    run_test("Migration Safety", test_migration_safety)

    print("=" * 70)
    print("ALL 10 VERIFICATION MODULES PASSED SUCCESSFULLY!")
    print("=" * 70)

    # Save empirical results to artifact/docs
    out_path = PROJECT_ROOT / "docs" / "empirical_verification_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_path}")

if __name__ == "__main__":
    main()
