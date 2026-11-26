"""
FIPP 2.0 — Phase 9 Final Redesign Approval Acceptance Suite.

Validates:
- Zero old/sample credentials can authenticate
- Idempotent `fipp.admin` bootstrap + mandatory first-login password change
- Strong password policy enforcement
- 8-digit string Student ID validation preserving leading zeroes + authorized registry gating
- Structured Campus Block & Floor reference dataset + server-side validation
- Neutral institutional naming across API contracts
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import reset_rate_limiter
from app.core.security import (
    bootstrap_initial_admin,
    hash_password,
    rotate_admin_temporary_password,
    validate_strong_password,
)
from app.main import app
from app.services.complaint_service import ComplaintService
from tests.helpers import admin_headers, setup_isolated_environment, student_headers


@pytest.fixture
def phase9_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    return {
        "client": TestClient(app),
        **setup_isolated_environment(tmp_path, monkeypatch),
    }


def test_old_sample_credentials_permanently_rejected(phase9_env):
    client = phase9_env["client"]
    legacy_attempts = [
        ("ADM-2026-001", "Admin@001"),
        ("ADM-2026-002", "Admin@002"),
        ("ADMIN01", "admin123"),
        ("STU-2026-001", "student123"),
        ("STU101", "student123"),
        ("STU102", "student123"),
        ("STU-TEST-001", "student123"),
        ("fipp.admin", "admin123"),
        ("fipp.admin", "password"),
        ("fipp.admin", "rU82^Y9A#yYtL8bC4zpP"),
    ]
    for username, password in legacy_attempts:
        r = client.post("/api/auth/login", json={"username": username, "password": password})
        assert r.status_code == 401, f"Legacy sample credential {username} unexpectedly succeeded!"

    # Fresh unpopulated student registry on clean deployment has zero pre-created demo students
    empty_reg = json.loads(phase9_env["student_registry"].read_text(encoding="utf-8"))
    assert all(r.get("student_id") not in {"STU-2026-001", "STU101", "STU102", "STU-TEST-001"} for r in empty_reg)


def test_admin_bootstrap_idempotency_and_mandatory_first_login_password_change(tmp_path: Path, monkeypatch):
    admin_store = tmp_path / "admin_accounts.json"
    revoked_file = tmp_path / "revoked_tokens.json"
    revoked_file.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("FIPP_ADMIN_STORE_FILE", str(admin_store))
    monkeypatch.setattr("app.core.security._REVOKED_TOKENS_FILE", revoked_file)
    monkeypatch.setattr("app.core.security._REVOKED_TOKENS", set())

    # 1. First-run bootstrap creates `fipp.admin` securely
    first = bootstrap_initial_admin()
    assert first["created"] is True
    assert first["username"] == "fipp.admin"
    assert first["display_name"] == "FIPP System Administrator"
    temp_pwd = first["temporary_password"]
    assert len(temp_pwd) >= 16
    validate_strong_password(temp_pwd, "fipp.admin")

    # Verify disk contains PBKDF2-600k hash only — never plaintext password
    disk_raw = admin_store.read_text(encoding="utf-8")
    assert temp_pwd not in disk_raw
    assert "pbkdf2_sha256$600000$" in disk_raw

    # 2. Second bootstrap attempt is strictly idempotent (never resets/overwrites)
    second = bootstrap_initial_admin()
    assert second["created"] is False
    assert second["already_initialized"] is True
    assert "temporary_password" not in second

    # 3. First login enforces password change before accessing admin operations
    client = TestClient(app)
    login_res = client.post("/api/auth/login", json={"username": "fipp.admin", "password": temp_pwd})
    assert login_res.status_code == 200, login_res.text
    login_json = login_res.json()
    assert login_json["user"]["must_change_password"] is True
    temp_token = login_json["access_token"]

    blocked = client.get("/api/admin/kpis", headers={"Authorization": f"Bearer {temp_token}"})
    assert blocked.status_code == 403
    assert "password change required" in blocked.json()["detail"].lower()

    # Weak new password rejected
    weak_res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {temp_token}"},
        json={"current_password": temp_pwd, "new_password": "short"},
    )
    assert weak_res.status_code in {400, 422}

    # Strong new password unlocks admin controls & revokes prior temp token
    strong_new = f"CampusAdmin#{secrets.token_hex(6)}Z9"
    chg_res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {temp_token}"},
        json={"current_password": temp_pwd, "new_password": strong_new},
    )
    assert chg_res.status_code == 200, chg_res.text
    assert chg_res.json()["user"]["must_change_password"] is False
    fresh_token = chg_res.json()["access_token"]

    # Old token revoked
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {temp_token}"}).status_code == 401
    # New token unlocks admin endpoint
    assert client.get("/api/admin/kpis", headers={"Authorization": f"Bearer {fresh_token}"}).status_code == 200


def test_eight_digit_student_self_registration_persistence_and_mismatch_protection(phase9_env):
    client = phase9_env["client"]
    adm_hdr = admin_headers(client, phase9_env["admin_username"], phase9_env["admin_password"])
    reg_file = phase9_env["student_registry"]

    # Case A: Brand-new 8-digit leading-zero student self-registers WITHOUT prior admin creation
    r_new = client.post(
        "/api/auth/student/login",
        json={"student_name": "  Rohan   Verma  ", "student_id": "00009876"},
    )
    assert r_new.status_code == 200, r_new.text
    new_json = r_new.json()
    assert new_json["is_new_registration"] is True
    assert new_json["user"]["id"] == "00009876"  # leading zeroes preserved as string
    assert new_json["user"]["name"] == "Rohan Verma"
    assert new_json["user"]["identity_verification"] == "self_declared_unverified"

    # Verify student profile persisted to disk
    persisted_students = json.loads(reg_file.read_text(encoding="utf-8"))
    matching_9876 = [s for s in persisted_students if s["student_id"] == "00009876"]
    assert len(matching_9876) == 1
    assert matching_9876[0]["registration_source"] == "self_registered"

    # Case B (matching name with normalized whitespace/case) -> logs in WITHOUT creating duplicate
    r_again = client.post(
        "/api/auth/student/login",
        json={"student_name": "rohan verma", "student_id": "00009876"},
    )
    assert r_again.status_code == 200, r_again.text
    assert r_again.json()["is_new_registration"] is False
    persisted_after = json.loads(reg_file.read_text(encoding="utf-8"))
    assert len([s for s in persisted_after if s["student_id"] == "00009876"]) == 1

    # Case B (name mismatch) -> rejected (409 Conflict), stored name NOT overwritten, no name leaked in message
    wrong_name = client.post(
        "/api/auth/student/login",
        json={"student_name": "Imposter Name", "student_id": "00009876"},
    )
    assert wrong_name.status_code == 409
    assert "rohan" not in wrong_name.text.lower()
    persisted_still = json.loads(reg_file.read_text(encoding="utf-8"))
    assert [s for s in persisted_still if s["student_id"] == "00009876"][0]["name"] == "Rohan Verma"

    # Empty / malformed names & invalid 8-digit formats rejected cleanly
    for bad_name in ["", "   ", "12345", "A"]:
        r_bad_n = client.post(
            "/api/auth/student/login",
            json={"student_name": bad_name, "student_id": "00009876"},
        )
        assert r_bad_n.status_code == 422

    for bad_id in ["1234567", "123456789", "1234ABCD", "0012 345", 12345678]:
        r_bad = client.post(
            "/api/auth/student/login",
            json={"student_name": "Rohan Verma", "student_id": bad_id},
        )
        assert r_bad.status_code == 422, f"Expected 422 for student_id={bad_id!r}, got {r_bad.status_code}"

    # Admin-controlled identity name correction -> student can then sign in under corrected name
    r_fix = client.patch(
        "/api/admin/students/00009876",
        headers=adm_hdr,
        json={"name": "Rohan K. Verma"},
    )
    assert r_fix.status_code == 200, r_fix.text
    r_fixed_login = client.post(
        "/api/auth/student/login",
        json={"student_name": "Rohan K. Verma", "student_id": "00009876"},
    )
    assert r_fixed_login.status_code == 200
    rohan_hdr = {"Authorization": f"Bearer {r_fixed_login.json()['access_token']}"}
    assert client.get("/api/student/complaints", headers=rohan_hdr).status_code == 200

    # Deactivate student -> active session blocked (403) and re-login blocked (403)
    r_deact = client.patch(
        "/api/admin/students/00009876",
        headers=adm_hdr,
        json={"is_active": False},
    )
    assert r_deact.status_code == 200
    assert client.get("/api/student/complaints", headers=rohan_hdr).status_code == 403
    assert (
        client.post(
            "/api/auth/student/login",
            json={"student_name": "Rohan K. Verma", "student_id": "00009876"},
        ).status_code
        == 403
    )


def test_campus_block_floor_reference_and_server_side_validation(phase9_env):
    client = phase9_env["client"]
    adm_hdr = admin_headers(client, phase9_env["admin_username"], phase9_env["admin_password"])
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")

    tax = client.get("/api/taxonomy/hierarchy").json()
    tax_str = json.dumps(tax)
    assert "lpu" not in tax_str.lower()
    blocks = {b["block_id"]: b for b in tax["blocks_reference"]}

    # Verify required reference blocks and unverified status
    for required_bid in ["BLK-3", "BLK-8B", "BLK-27", "BLK-55", "BLK-56", "BLK-57", "BLK-UC", "BLK-LIB", "BLK-HOSP", "BLK-BH1"]:
        assert required_bid in blocks
        assert blocks[required_bid]["verification_status"] == "unverified_external_reference"

    assert blocks["BLK-57"]["floor_count"] == 8
    assert len(blocks["BLK-57"]["floors"]) == 8
    assert blocks["BLK-UC"]["floor_count"] == 8
    assert blocks["BLK-3"]["floor_count"] is None
    assert blocks["BLK-3"]["floors"] == []

    base_payload = {
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "title": "Block Floor Validation Check",
        "category": "Electricity",
        "sub_category": "Power Supply / Socket",
        "specific_categories": ["Sparking socket"],
        "room_type": "Room No",
        "room_number": "204",
        "contact_number": "9876543210",
        "availability_date": "2026-12-10",
        "time_slot": "10:00 AM - 12:00 PM",
        "description": "Sparking electrical socket near seminar table.",
        "declarations_accepted": True,
    }

    # Block 57 missing floor -> 400
    r_no_floor = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json={**base_payload, "building": "Block 57", "block_id": "BLK-57"},
    )
    assert r_no_floor.status_code == 400

    # Block 57 with fabricated 9th floor or University Centre floor -> 400
    r_bad_floor = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json={**base_payload, "building": "Block 57", "block_id": "BLK-57", "floor_id": "BLK-UC-F2", "floor_label": "Second Floor"},
    )
    assert r_bad_floor.status_code == 400

    # Block 57 with valid floor BLK-57-F2 -> 200
    r_ok_57 = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json={**base_payload, "building": "Block 57", "block_id": "BLK-57", "floor_id": "BLK-57-F2", "floor_label": "Second Floor"},
    )
    assert r_ok_57.status_code == 200, r_ok_57.text
    created = r_ok_57.json()["complaint"]
    assert created["block_id"] == "BLK-57"
    assert created["floor_id"] == "BLK-57-F2"
    assert "Second Floor" in created["location"]

    # Unknown floor block (Block 3) rejects fabricated floor string -> 400, accepts unspecified floor -> 200
    r_fab_blk3 = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json={**base_payload, "building": "Block 3", "block_id": "BLK-3", "floor_label": "Fourth Floor"},
    )
    assert r_fab_blk3.status_code == 400

    r_ok_blk3 = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json={**base_payload, "building": "Block 3", "block_id": "BLK-3"},
    )
    assert r_ok_blk3.status_code == 200, r_ok_blk3.text

    # Admin configures and verifies Block 3 floors dynamically
    r_cfg = client.put(
        "/api/admin/locations/blocks/BLK-3",
        headers=adm_hdr,
        json={
            "display_name": "Block 3",
            "block_category": "Academic",
            "floor_labels": ["Ground Floor", "First Floor", "Second Floor"],
            "verification_status": "verified",
            "notes": "Verified by campus estate audit.",
        },
    )
    assert r_cfg.status_code == 200
    assert r_cfg.json()["block"]["floor_count"] == 3

    # Existing legacy complaint records remain readable cleanly
    all_admin = client.get("/api/admin/complaints", headers=adm_hdr)
    assert all_admin.status_code == 200
    assert any(r.get("complaint_id") == "CMP-2026-001" for r in all_admin.json()["records"])


def test_self_registered_student_complaints_queries_attachments_isolation_and_restart(phase9_env):
    client = phase9_env["client"]
    adm_hdr = admin_headers(client, phase9_env["admin_username"], phase9_env["admin_password"])

    # Student A (leading-zero self-registered without prior admin provisioning)
    r_a = client.post(
        "/api/auth/student/login",
        json={"student_name": "Kavita Rao", "student_id": "00001122"},
    )
    assert r_a.status_code == 200
    hdr_a = {"Authorization": f"Bearer {r_a.json()['access_token']}"}

    # Student B self-registers independently
    r_b = client.post(
        "/api/auth/student/login",
        json={"student_name": "Vikram Gill", "student_id": "00003344"},
    )
    assert r_b.status_code == 200
    hdr_b = {"Authorization": f"Bearer {r_b.json()['access_token']}"}

    # Student A uploads PNG photo
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(15, 95, 70)).save(buf, format="PNG")
    up_res = client.post(
        "/api/uploads/photo",
        headers=hdr_a,
        files={"file": ("defect.png", buf.getvalue(), "image/png")},
    )
    assert up_res.status_code == 200, up_res.text
    stored_photo = up_res.json()["stored_filename"]

    # Raise Complaint ("Grievance") even if spoofed student_id passed in payload body
    c_payload = {
        "student_id": "99999999",
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "title": "Blocked Lab Corridor Drain",
        "category": "Electricity",
        "sub_category": "Power Supply / Socket",
        "specific_categories": ["Sparking socket"],
        "building": "Block 57",
        "block_id": "BLK-57",
        "floor_id": "BLK-57-F2",
        "floor_label": "Second Floor",
        "room_type": "Room No",
        "room_number": "209",
        "contact_number": "9876543210",
        "availability_date": "2026-12-12",
        "time_slot": "10:00 AM - 12:00 PM",
        "description": "Power strip overheating near Block 57 laboratory room 209.",
        "declarations_accepted": True,
        "photo_stored_filename": stored_photo,
        "photo_sha256": up_res.json()["sha256"],
    }
    sub_complaint = client.post("/api/student/complaints/submit", headers=hdr_a, json=c_payload)
    assert sub_complaint.status_code == 200, sub_complaint.text
    cmp_id = sub_complaint.json()["token"]
    assert sub_complaint.json()["complaint"]["student_id"] == "00001122"

    # Raise Query ("Enquiry") under same self-registered student ID
    q_payload = {
        **c_payload,
        "message_type": "Enquiry",
        "title": "Inspection Schedule Enquiry",
        "photo_stored_filename": None,
        "photo_sha256": None,
        "description": "Requesting technician inspection slot confirmation for room 209.",
    }
    sub_query = client.post("/api/student/complaints/submit", headers=hdr_a, json=q_payload)
    assert sub_query.status_code == 200, sub_query.text
    qry_id = sub_query.json()["token"]

    # Student B CANNOT view Student A's complaint, attachment, steal attachment ref, withdraw, or rate
    assert client.get("/api/student/complaints", headers=hdr_b).json()["total_complaints"] == 0
    assert client.get(f"/api/student/complaints/{cmp_id}", headers=hdr_b).status_code == 403
    assert client.get(f"/api/uploads/{stored_photo}", headers=hdr_b).status_code == 403
    assert (
        client.post(
            f"/api/student/complaints/{cmp_id}/withdraw",
            headers=hdr_b,
            json={"reason": "Unauthorized attempt"},
        ).status_code
        == 400
    )
    steal_photo = client.post(
        "/api/student/complaints/submit",
        headers=hdr_b,
        json={**q_payload, "photo_stored_filename": stored_photo},
    )
    assert steal_photo.status_code == 400

    # Admin resolves complaint -> Student A sees updated status, closing remarks & submits feedback
    assert (
        client.patch(
            f"/api/admin/complaints/{cmp_id}",
            headers=adm_hdr,
            json={"status": "Resolved", "remarks": "Replaced faulty power strip in room 209."},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/student/complaints/{cmp_id}/feedback",
            headers=hdr_a,
            json={"rating": 5, "comments": "Prompt repair."},
        ).status_code
        == 200
    )

    # Admin view displays associated self-registered student identity
    adm_view = client.get(f"/api/admin/complaints/{cmp_id}", headers=adm_hdr)
    assert adm_view.status_code == 200
    assert adm_view.json()["student_id"] == "00001122"
    assert adm_view.json()["student_name"] == "Kavita Rao"

    # Simulated application restart / fresh service & fresh re-login retrieves both records
    fresh_service = ComplaintService(data_file=phase9_env["data_file"])
    reloaded = fresh_service.get_student_complaints("00001122")
    assert {r["complaint_id"] for r in reloaded} == {cmp_id, qry_id}

    r_relogin = client.post(
        "/api/auth/student/login",
        json={"student_name": "  kavita   rao ", "student_id": "00001122"},
    )
    assert r_relogin.status_code == 200
    assert r_relogin.json()["is_new_registration"] is False
    hdr_a2 = {"Authorization": f"Bearer {r_relogin.json()['access_token']}"}
    hist = client.get("/api/student/complaints", headers=hdr_a2).json()
    assert hist["total_complaints"] == 2
    assert {r["complaint_id"] for r in hist["records"]} == {cmp_id, qry_id}


def test_admin_credential_rotation_and_auth_rate_limiting(phase9_env):
    client = phase9_env["client"]
    old_admin_hdr = admin_headers(client, phase9_env["admin_username"], phase9_env["admin_password"])
    assert client.get("/api/admin/kpis", headers=old_admin_hdr).status_code == 200

    # Rotate temporary admin password -> old password & old JWT both rejected
    rot = rotate_admin_temporary_password()
    assert rot["rotated"] is True
    assert rot["must_change_password"] is True
    new_temp = rot["temporary_password"]
    assert new_temp != phase9_env["admin_password"]

    assert client.get("/api/admin/kpis", headers=old_admin_hdr).status_code == 401
    assert (
        client.post(
            "/api/auth/login",
            json={"username": "fipp.admin", "password": phase9_env["admin_password"]},
        ).status_code
        == 401
    )

    # New temporary password logs in with must_change_password=True blocking admin endpoints
    temp_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": new_temp})
    assert temp_login.status_code == 200
    assert temp_login.json()["user"]["must_change_password"] is True
    temp_hdr = {"Authorization": f"Bearer {temp_login.json()['access_token']}"}
    assert client.get("/api/admin/kpis", headers=temp_hdr).status_code == 403

    # Verify auth rate limiter triggers HTTP 429 cleanly after burst on student registration/login
    reset_rate_limiter()
    statuses = []
    for idx in range(28):
        r = client.post(
            "/api/auth/student/login",
            json={"student_name": "Rate Test Student", "student_id": f"880000{idx:02d}"},
        )
        statuses.append(r.status_code)
    assert 429 in statuses
    reset_rate_limiter()
