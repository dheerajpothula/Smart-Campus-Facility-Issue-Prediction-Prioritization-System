"""
FIPP 2.0 — Phase 9 Correction / Hotfix Focused Regression Suite.

Validates all 16 hotfix requirements directly against genuine backend security,
bootstrap, auth, student portal, upload, taxonomy, and persistence modules in
completely isolated `tmp_path` storage without mutating live operational data.
"""
from __future__ import annotations

import io
import json
import secrets
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import require_admin, reset_rate_limiter
from app.api.routes_auth import router as auth_router
from app.api.routes_student import router as student_router
from app.api.routes_taxonomy import router as taxonomy_router
from app.api.routes_uploads import router as uploads_router
from app.bootstrap_admin import main as bootstrap_cli_main
from app.core.config import CAMPUS_BLOCKS_SEED_FILE, PRIMARY_JSON_DATA_FILE
from app.core.security import (
    bootstrap_initial_admin,
    get_student_record,
    list_students,
    rotate_admin_temporary_password,
    update_student_enrollment,
    validate_strong_password,
)
from app.services.complaint_service import ComplaintService, complaint_service


def _build_hotfix_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(auth_router)
    test_app.include_router(taxonomy_router)
    test_app.include_router(student_router)
    test_app.include_router(uploads_router)

    @test_app.get("/api/admin/kpis")
    def _admin_kpis_gate(current_user: dict = pytest.importorskip("fastapi").Depends(require_admin)):
        return complaint_service.get_kpis()

    return test_app


@pytest.fixture
def hotfix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_file = tmp_path / "complaints.json"
    shutil.copy2(PRIMARY_JSON_DATA_FILE, data_file)

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    revoked_file = tmp_path / "revoked_tokens.json"
    revoked_file.write_text("[]", encoding="utf-8")
    admin_store = tmp_path / "admin_accounts.json"
    student_registry = tmp_path / "student_registry.json"
    student_registry.write_text("[]", encoding="utf-8")
    blocks_file = tmp_path / "campus_blocks_override.json"
    if CAMPUS_BLOCKS_SEED_FILE.is_file():
        shutil.copy2(CAMPUS_BLOCKS_SEED_FILE, blocks_file)

    monkeypatch.setenv("FIPP_DATA_FILE", str(data_file))
    monkeypatch.setenv("FIPP_UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("FIPP_ADMIN_STORE_FILE", str(admin_store))
    monkeypatch.setenv("FIPP_STUDENT_REGISTRY_FILE", str(student_registry))
    monkeypatch.setenv("FIPP_CAMPUS_BLOCKS_FILE", str(blocks_file))

    monkeypatch.setattr(complaint_service, "data_file", data_file)
    monkeypatch.setattr("app.services.upload_service.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("app.api.routes_uploads.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("app.core.security._REVOKED_TOKENS_FILE", revoked_file)
    monkeypatch.setattr("app.core.security._REVOKED_TOKENS", set())
    reset_rate_limiter()

    return {
        "client": TestClient(_build_hotfix_test_app()),
        "data_file": data_file,
        "upload_dir": upload_dir,
        "admin_store": admin_store,
        "student_registry": student_registry,
    }


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (6, 6), color=(32, 58, 50)).save(buf, format="PNG")
    return buf.getvalue()


def test_01_02_03_04_05_06_07_student_self_registration_and_persistence(hotfix_env):
    client = hotfix_env["client"]
    reg_file = hotfix_env["student_registry"]

    # 15. Clean deployment starts with zero pre-created student records
    assert json.loads(reg_file.read_text(encoding="utf-8")) == []

    # 3. Reject invalid 8-digit formats and invalid/empty names
    for bad_id in ["1234567", "123456789", "1234ABCD", "0012 345", 12345678]:
        r = client.post(
            "/api/auth/student/login",
            json={"student_name": "Ananya Iyer", "student_id": bad_id},
        )
        assert r.status_code == 422

    for bad_name in ["", "   ", "12345", "A"]:
        r = client.post(
            "/api/auth/student/login",
            json={"student_name": bad_name, "student_id": "00123456"},
        )
        assert r.status_code == 422

    # 1 & 4. New leading-zero student self-registers without prior admin provisioning
    res_new = client.post(
        "/api/auth/student/login",
        json={"student_name": "  Ananya   Iyer  ", "student_id": "00123456"},
    )
    assert res_new.status_code == 200, res_new.text
    body = res_new.json()
    assert body["is_new_registration"] is True
    assert body["user"]["id"] == "00123456"
    assert body["user"]["name"] == "Ananya Iyer"
    assert body["user"]["identity_verification"] == "self_declared_unverified"

    # 7. Persisted cleanly to JSON store on disk
    disk_records = json.loads(reg_file.read_text(encoding="utf-8"))
    assert len(disk_records) == 1
    assert disk_records[0]["student_id"] == "00123456"
    assert disk_records[0]["name"] == "Ananya Iyer"
    assert disk_records[0]["registration_source"] == "self_registered"

    # 2 & 5. Existing student login with normalized whitespace/case does NOT duplicate
    res_relogin = client.post(
        "/api/auth/student/login",
        json={"student_name": "ananya iyer", "student_id": "00123456"},
    )
    assert res_relogin.status_code == 200
    assert res_relogin.json()["is_new_registration"] is False
    assert len(list_students()) == 1

    # 6. Mismatched name is rejected with 409, does NOT overwrite, and does NOT leak stored name
    res_mismatch = client.post(
        "/api/auth/student/login",
        json={"student_name": "Imposter User", "student_id": "00123456"},
    )
    assert res_mismatch.status_code == 409
    assert "ananya" not in res_mismatch.text.lower()
    assert get_student_record("00123456")["name"] == "Ananya Iyer"

    # Admin-controlled name correction allows re-login with corrected name
    update_student_enrollment("00123456", name="Ananya R. Iyer")
    res_fixed = client.post(
        "/api/auth/student/login",
        json={"student_name": "Ananya R. Iyer", "student_id": "00123456"},
    )
    assert res_fixed.status_code == 200
    assert res_fixed.json()["user"]["name"] == "Ananya R. Iyer"


def test_08_09_10_11_12_13_16_student_activities_ownership_and_rate_limit(hotfix_env):
    client = hotfix_env["client"]

    # Two self-registered students with leading-zero 8-digit string IDs
    a_login = client.post(
        "/api/auth/student/login",
        json={"student_name": "Kavita Rao", "student_id": "00001122"},
    ).json()
    b_login = client.post(
        "/api/auth/student/login",
        json={"student_name": "Vikram Gill", "student_id": "00003344"},
    ).json()
    hdr_a = {"Authorization": f"Bearer {a_login['access_token']}"}
    hdr_b = {"Authorization": f"Bearer {b_login['access_token']}"}

    # Unauthenticated student endpoint rejected
    assert client.get("/api/student/complaints").status_code == 401

    # Student A uploads PNG photo
    up_res = client.post(
        "/api/uploads/photo",
        headers=hdr_a,
        files={"file": ("leak.png", _png_bytes(), "image/png")},
    )
    assert up_res.status_code == 200
    stored_photo = up_res.json()["stored_filename"]

    base = {
        "student_id": "99999999",  # spoofed field in payload must never override verified identity
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "title": "Block 57 Electrical Fault",
        "category": "Electricity",
        "sub_category": "Power Supply / Socket",
        "specific_categories": ["Sparking socket"],
        "building": "Block 57",
        "block_id": "BLK-57",
        "floor_id": "BLK-57-F2",
        "floor_label": "Second Floor",
        "room_type": "Room No",
        "room_number": "204",
        "contact_number": "9876543210",
        "availability_date": "2026-12-15",
        "time_slot": "10:00 AM - 12:00 PM",
        "description": "Electrical outlet sparking on Second Floor laboratory.",
        "declarations_accepted": True,
        "photo_stored_filename": stored_photo,
        "photo_sha256": up_res.json()["sha256"],
    }

    # 8. Complaint creation linked to student_id
    r_cmp = client.post("/api/student/complaints/submit", headers=hdr_a, json=base)
    assert r_cmp.status_code == 200, r_cmp.text
    cmp_id = r_cmp.json()["token"]
    assert r_cmp.json()["complaint"]["student_id"] == "00001122"
    assert r_cmp.json()["complaint"]["availability_date"] == "2026-12-15"

    # 9. Query creation ("Enquiry") linked to student_id
    r_qry = client.post(
        "/api/student/complaints/submit",
        headers=hdr_a,
        json={
            **base,
            "message_type": "Enquiry",
            "title": "Inspection Time Slot Query",
            "photo_stored_filename": None,
            "photo_sha256": None,
            "description": "Confirming inspection schedule window for Second Floor room 204.",
        },
    )
    assert r_qry.status_code == 200, r_qry.text
    qry_id = r_qry.json()["token"]

    # 11, 12, 13. Cross-student isolation across complaints, details, withdrawal, feedback, attachments
    assert client.get("/api/student/complaints", headers=hdr_b).json()["total_complaints"] == 0
    assert client.get(f"/api/student/complaints/{cmp_id}", headers=hdr_b).status_code == 403
    assert client.get(f"/api/uploads/{stored_photo}", headers=hdr_a).status_code == 200
    assert client.get(f"/api/uploads/{stored_photo}", headers=hdr_b).status_code == 403
    assert client.get(f"/api/uploads/{stored_photo}").status_code == 401
    assert (
        client.post(
            "/api/student/complaints/submit",
            headers=hdr_b,
            json={**base, "photo_stored_filename": stored_photo},
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/api/student/complaints/{cmp_id}/withdraw",
            headers=hdr_b,
            json={"reason": "Cross-student attempt"},
        ).status_code
        == 400
    )

    # Admin updates & resolves ticket -> visible to Student A with resolution remarks + feedback
    resolved = complaint_service.update_complaint_status(
        complaint_id=cmp_id,
        new_status="Resolved",
        remarks="Replaced damaged wall socket on Second Floor.",
        admin_id="fipp.admin",
        admin_title="System Administrator",
    )
    assert resolved is not None and resolved["student_id"] == "00001122"
    assert (
        client.post(
            f"/api/student/complaints/{cmp_id}/feedback",
            headers=hdr_b,
            json={"rating": 1, "comments": "Wrong user"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/api/student/complaints/{cmp_id}/feedback",
            headers=hdr_a,
            json={"rating": 5, "comments": "Resolved cleanly."},
        ).status_code
        == 200
    )

    # 10 & 7. Simulated restart: re-login & fresh ComplaintService instance retrieve all history
    fresh_svc = ComplaintService(data_file=hotfix_env["data_file"])
    reloaded = fresh_svc.get_student_complaints("00001122")
    assert {r["complaint_id"] for r in reloaded} == {cmp_id, qry_id}
    r_cmp_reloaded = next(r for r in reloaded if r["complaint_id"] == cmp_id)
    assert r_cmp_reloaded["closing_remarks"] == "Replaced damaged wall socket on Second Floor."
    assert r_cmp_reloaded["feedback"]["rating"] == 5

    # 16. Pre-existing CMP-2026-001..010 records remain untouched inside the store
    all_ids = {r["complaint_id"] for r in fresh_svc._load_records()}
    for i in range(1, 11):
        assert f"CMP-2026-{i:03d}" in all_ids

    # 13. Auth rate limiter enforces HTTP 429 on rapid burst
    reset_rate_limiter()
    codes = [
        client.post(
            "/api/auth/student/login",
            json={"student_name": "Burst Student", "student_id": f"880000{i:02d}"},
        ).status_code
        for i in range(28)
    ]
    assert 429 in codes
    reset_rate_limiter()


def test_14_15_admin_bootstrap_rotation_first_login_gate_and_no_default_creds(hotfix_env):
    client = hotfix_env["client"]

    # 15. Legacy default student & admin credentials fail
    for u, p in [
        ("STU-2026-001", "student123"),
        ("STU101", "student123"),
        ("STU-TEST-001", "student123"),
        ("ADMIN01", "admin123"),
        ("fipp.admin", "rU82^Y9A#yYtL8bC4zpP"),
    ]:
        assert client.post("/api/auth/login", json={"username": u, "password": p}).status_code == 401

    # 14. Idempotent bootstrap + rotation + first-login gate
    assert bootstrap_cli_main([]) == 0
    boot = bootstrap_initial_admin()
    assert boot["created"] is False  # idempotent second call

    rot1 = rotate_admin_temporary_password()
    assert rot1["rotated"] is True
    assert rot1["username"] == "fipp.admin"
    assert rot1["display_name"] == "FIPP System Administrator"
    temp1 = rot1["temporary_password"]
    validate_strong_password(temp1, "fipp.admin")

    # Ensure plaintext password is never saved in admin store
    assert temp1 not in hotfix_env["admin_store"].read_text(encoding="utf-8")

    res_login = client.post("/api/auth/login", json={"username": "fipp.admin", "password": temp1})
    assert res_login.status_code == 200
    assert res_login.json()["user"]["must_change_password"] is True
    temp_hdr = {"Authorization": f"Bearer {res_login.json()['access_token']}"}

    # Blocked before password change
    assert client.get("/api/admin/kpis", headers=temp_hdr).status_code == 403

    # Rotate again -> temp1 & old token become invalid
    rot2 = rotate_admin_temporary_password()
    temp2 = rot2["temporary_password"]
    assert temp2 != temp1
    assert client.get("/api/admin/kpis", headers=temp_hdr).status_code == 401
    assert client.post("/api/auth/login", json={"username": "fipp.admin", "password": temp1}).status_code == 401

    # Login with temp2, rotate to final strong password -> unlocks admin access
    t2_token = client.post("/api/auth/login", json={"username": "fipp.admin", "password": temp2}).json()["access_token"]
    new_strong = f"PilotAdmin#{secrets.token_hex(6)}Q7"
    chg = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {t2_token}"},
        json={"current_password": temp2, "new_password": new_strong},
    )
    assert chg.status_code == 200
    assert chg.json()["user"]["must_change_password"] is False
    fresh_hdr = {"Authorization": f"Bearer {chg.json()['access_token']}"}
    assert client.get("/api/admin/kpis", headers=fresh_hdr).status_code == 200
