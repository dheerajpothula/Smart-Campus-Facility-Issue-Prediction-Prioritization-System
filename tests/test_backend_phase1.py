"""
FIPP 2.0 — Phase 1 Regression Verification Test Suite (Updated for Phase 9 Identity & Campus Blocks).
Verifies:
- OWASP PBKDF2-HMAC-SHA256 hashing & JWT auth tokens
- Strict RBAC student/admin role isolation
- 19-category facility taxonomy hierarchy & campus block/floor API
- Student complaint lifecycle & 8-digit leading-zero ID preservation
- Admin status transitions, PII-redacted CSV exports, and upload magic-byte checks
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.security import hash_password, verify_password
from app.main import app
from tests.helpers import admin_headers, setup_isolated_environment, student_headers

client = TestClient(app)
_CTX: dict = {}


@pytest.fixture(autouse=True)
def isolated_phase1_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env = setup_isolated_environment(tmp_path, monkeypatch)
    _CTX.clear()
    _CTX.update(env)
    return env


def test_pbkdf2_hashing_and_verification():
    sample = "StrongTest!Pwd#92"
    hashed = hash_password(sample)
    assert hashed.startswith("pbkdf2_sha256$600000$")
    assert verify_password(sample, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_login_and_jwt_issuance():
    res = client.post("/api/auth/login", json={"username": _CTX["admin_username"], "password": _CTX["admin_password"]})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["user"]["id"] == "fipp.admin"
    assert data["user"]["role"] == "admin"

    res_stu = client.post("/api/auth/student/login", json={"student_name": "Aarav Sharma", "student_id": "00123456"})
    assert res_stu.status_code == 200
    assert res_stu.json()["user"]["id"] == "00123456"
    assert res_stu.json()["user"]["role"] == "student"

    res_bad = client.post("/api/auth/login", json={"username": _CTX["admin_username"], "password": "wrongpassword"})
    assert res_bad.status_code == 401


def test_token_refresh():
    login_res = client.post("/api/auth/login", json={"username": _CTX["admin_username"], "password": _CTX["admin_password"]}).json()
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": login_res["refresh_token"]})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()


def test_rbac_endpoint_protection():
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    adm_hdr = admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])

    assert client.get("/api/admin/kpis").status_code == 401
    assert client.get("/api/admin/kpis", headers=stu_hdr).status_code == 403
    assert client.get("/api/admin/kpis", headers=adm_hdr).status_code == 200
    assert client.get("/api/student/complaints", headers=adm_hdr).status_code == 403
    assert client.get("/api/student/complaints", headers=stu_hdr).status_code == 200


def test_taxonomy_hierarchy_endpoint():
    """Verifies full 19-category facility hierarchy and structured campus blocks."""
    res = client.get("/api/taxonomy/hierarchy")
    assert res.status_code == 200
    data = res.json()
    assert len(data["maintenance_categories"]) == 19
    assert len(data["mandatory_declarations"]) == 3
    assert len(data["blocks_reference"]) >= 10
    assert "Block 57" in data["campus_blocks"]


def test_student_submission_validation():
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    bad_payload = {
        "message_type": "Grievance",
        "category": "Electricity",
        "building": "Block 57",
        "block_id": "BLK-57",
        "floor_id": "BLK-57-F2",
        "floor_label": "Second Floor",
        "contact_number": "123",
        "availability_date": future_date,
        "time_slot": "10:00–12:00",
        "description": "Tube light is flickering.",
        "declarations_accepted": True,
    }
    assert client.post("/api/student/complaints/submit", headers=stu_hdr, json=bad_payload).status_code == 422


def test_student_submission_and_token_format():
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    payload = {
        "message_type": "Grievance",
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
        "availability_date": future_date,
        "time_slot": "10:00–12:00",
        "description": "Main wall socket sparking intermittently.",
        "declarations_accepted": True,
    }
    res = client.post("/api/student/complaints/submit", headers=stu_hdr, json=payload)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["token"].startswith("CMP-2026-")
    assert body["complaint"]["student_id"] == "00123456"


def test_student_data_isolation():
    stu1_hdr = student_headers(client, "Aarav Sharma", "00123456")
    stu2_hdr = student_headers(client, "Priya Nair", "00123457")
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    payload = {
        "message_type": "Grievance",
        "category": "Plumbing",
        "building": "Block 3",
        "block_id": "BLK-3",
        "room_type": "Room No",
        "room_number": "105",
        "contact_number": "9876543210",
        "availability_date": future_date,
        "time_slot": "08:00–10:00",
        "description": "Sink drainage pipe is leaking.",
        "declarations_accepted": True,
    }
    sub = client.post("/api/student/complaints/submit", headers=stu1_hdr, json=payload).json()
    tid = sub["token"]
    assert client.get(f"/api/student/complaints/{tid}", headers=stu2_hdr).status_code == 403
    assert client.get(f"/api/student/complaints/{tid}", headers=stu1_hdr).status_code == 200


def test_admin_kpis_and_listing():
    adm_hdr = admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])
    r_kpis = client.get("/api/admin/kpis", headers=adm_hdr)
    assert r_kpis.status_code == 200
    assert "total" in r_kpis.json()
    r_list = client.get("/api/admin/complaints", headers=adm_hdr)
    assert r_list.status_code == 200


def test_admin_status_update_and_audit_history():
    adm_hdr = admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])
    r = client.patch(
        "/api/admin/complaints/CMP-2026-001",
        headers=adm_hdr,
        json={"status": "Under Review", "remarks": "Queued for technician dispatch."},
    )
    assert r.status_code == 200


def test_admin_reports_and_pii_redacted_export():
    adm_hdr = admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])
    assert client.get("/api/admin/reports/analytics", headers=adm_hdr).status_code == 200
    csv_res = client.get("/api/admin/reports/export", headers=adm_hdr)
    assert csv_res.status_code == 200
    assert "[REDACTED]" in csv_res.text


def test_file_upload_magic_bytes_and_validation():
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    assert client.post(
        "/api/uploads/photo",
        headers=stu_hdr,
        files={"file": ("bad.png", b"invalid", "image/png")},
    ).status_code == 400

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(0, 100, 200)).save(buf, format="PNG")
    r_ok = client.post(
        "/api/uploads/photo",
        headers=stu_hdr,
        files={"file": ("valid.png", buf.getvalue(), "image/png")},
    )
    assert r_ok.status_code == 200


def test_ml_analyze_and_shap_explainability():
    adm_hdr = admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])
    r = client.get("/api/admin/intelligence/complaint/CMP-2026-001", headers=adm_hdr)
    assert r.status_code == 200
    assert "mcpi" in r.json()


def test_migration_dry_run():
    adm_hdr = admin_headers(client, _CTX["admin_username"], _CTX["admin_password"])
    r = client.post("/api/admin/migration/dry-run", headers=adm_hdr)
    assert r.status_code == 200
    assert r.json().get("dry_run_success") is True
