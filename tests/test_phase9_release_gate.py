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

from app.core.security import (
    bootstrap_initial_admin,
    hash_password,
    provision_student,
    validate_strong_password,
)
from app.main import app
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
        ("fipp.admin", "admin123"),
        ("fipp.admin", "password"),
    ]
    for username, password in legacy_attempts:
        r = client.post("/api/auth/login", json={"username": username, "password": password})
        assert r.status_code == 401, f"Legacy sample credential {username} unexpectedly succeeded!"


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


def test_eight_digit_student_id_validation_and_registry_enforcement(phase9_env):
    client = phase9_env["client"]
    adm_hdr = admin_headers(client, phase9_env["admin_username"], phase9_env["admin_password"])

    # Valid leading-zero 8-digit student provisioned
    s_hdr = student_headers(client, "Aarav Sharma", "00123456")
    me_res = client.get("/api/auth/me", headers=s_hdr)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["id"] == "00123456"  # leading zeroes preserved

    # Unprovisioned valid 8-digit identity cannot sign in
    unprov = client.post(
        "/api/auth/student/login",
        json={"student_name": "Unauthorized Student", "student_id": "99887766"},
    )
    assert unprov.status_code == 401

    # Provisioned ID with wrong name cannot sign in
    wrong_name = client.post(
        "/api/auth/student/login",
        json={"student_name": "Wrong Person", "student_id": "00123456"},
    )
    assert wrong_name.status_code == 401

    # Invalid ID formats rejected (alphabetic, too short, too long, integer non-string)
    for bad_id in ["1234567", "123456789", "1234ABCD", "0012 345", 12345678]:
        r_bad = client.post(
            "/api/auth/student/login",
            json={"student_name": "Aarav Sharma", "student_id": bad_id},
        )
        assert r_bad.status_code == 422, f"Expected 422 for student_id={bad_id!r}, got {r_bad.status_code}"

    # Admin provisions a new leading-zero student via API, then deactivates them
    r_prov = client.post(
        "/api/admin/students",
        headers=adm_hdr,
        json={"student_id": "00009876", "name": "Neha Verma", "block": "Block 57"},
    )
    assert r_prov.status_code == 201, r_prov.text
    assert r_prov.json()["student"]["student_id"] == "00009876"

    neha_hdr = student_headers(client, "Neha Verma", "00009876")
    assert client.get("/api/student/complaints", headers=neha_hdr).status_code == 200

    # Deactivate student -> active session blocked (403) and re-login rejected (401)
    r_deact = client.patch(
        "/api/admin/students/00009876",
        headers=adm_hdr,
        json={"is_active": False},
    )
    assert r_deact.status_code == 200
    assert client.get("/api/student/complaints", headers=neha_hdr).status_code == 403
    assert (
        client.post(
            "/api/auth/student/login",
            json={"student_name": "Neha Verma", "student_id": "00009876"},
        ).status_code
        == 401
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
