"""
FIPP 2.0 — Phase 8 Stage B Isolated Backend QA & Security Suite.

Uses `tmp_path` isolation for complaints storage, uploaded media, revoked tokens,
admin credentials, and authorized student registry so live data is never mutated.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import io
import jwt
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.core.security import create_access_token
from app.main import app
from app.services.complaint_service import ComplaintService
from tests.helpers import admin_headers, setup_isolated_environment, student_headers


def _make_png_bytes(width: int = 8, height: int = 8) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(37, 99, 235))
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Isolate complaints JSON, uploads, revoked tokens, and auth stores per test."""
    env = setup_isolated_environment(tmp_path, monkeypatch)
    return {
        "client": TestClient(app),
        **env,
    }


def _valid_submission(**overrides) -> dict:
    payload = {
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "title": "QA Isolated Electrical Test",
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
        "availability_date": "2026-12-01",
        "time_slot": "10:00 AM - 12:00 PM",
        "description": "Electrical outlet near podium emits sparks when load is connected.",
        "declarations_accepted": True,
    }
    payload.update(overrides)
    return payload


def _extract_id(resp_json: dict) -> str:
    if "token" in resp_json:
        return resp_json["token"]
    if "complaint_id" in resp_json:
        return resp_json["complaint_id"]
    return resp_json["complaint"]["complaint_id"]


def test_auth_rejects_expired_malformed_and_revoked_tokens(isolated_env):
    client = isolated_env["client"]

    # Expired token -> 401
    expired_payload = {
        "sub": "00123456",
        "id": "00123456",
        "role": "student",
        "token_type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    res_exp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_exp.status_code == 401

    # Tampered/malformed token -> 401
    res_bad = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert res_bad.status_code == 401

    # Logout revokes BOTH access token and refresh token
    auth_res = client.post(
        "/api/auth/student/login",
        json={"student_name": "Aarav Sharma", "student_id": "00123456"},
    )
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    access_token = auth_data["access_token"]
    refresh_token = auth_data["refresh_token"]

    logout_res = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 200

    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}).status_code == 401
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 401

    # Deactivated user rejection -> 403
    adm_hdr = admin_headers(client, isolated_env["admin_username"], isolated_env["admin_password"])
    stu_hdr = student_headers(client, "Priya Nair", "00123457")
    assert client.patch("/api/admin/students/00123457", headers=adm_hdr, json={"is_active": False}).status_code == 200
    assert client.get("/api/auth/me", headers=stu_hdr).status_code == 403


def test_role_isolation_blocks_student_admin_crossover(isolated_env):
    client = isolated_env["client"]
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    adm_hdr = admin_headers(client, isolated_env["admin_username"], isolated_env["admin_password"])

    for endpoint in [
        "/api/admin/kpis",
        "/api/admin/complaints",
        "/api/admin/intelligence/overview",
        "/api/admin/intelligence/complaint/CMP-2026-001",
        "/api/admin/reports/analytics",
        "/api/admin/reports/export",
        "/api/admin/students",
        "/api/admin/locations/blocks",
    ]:
        r = client.get(endpoint, headers=stu_hdr)
        assert r.status_code == 403, f"Expected 403 for student on {endpoint}, got {r.status_code}"

    r_adm = client.get("/api/student/complaints", headers=adm_hdr)
    assert r_adm.status_code == 403


def test_strict_pilot_env_fails_without_secrets_and_boots_with_strong_secrets():
    root = str(Path(__file__).resolve().parent.parent)
    py = sys.executable

    env_fail = os.environ.copy()
    env_fail["FIPP_ENV"] = "pilot"
    env_fail.pop("FIPP_JWT_SECRET", None)
    env_fail.pop("FIPP_AUTH_SALT", None)

    fail_proc = subprocess.run(
        [py, "-c", "import app.core.config"],
        cwd=root,
        env=env_fail,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert fail_proc.returncode != 0
    assert "FIPP_JWT_SECRET" in (fail_proc.stderr + fail_proc.stdout)

    env_ok = os.environ.copy()
    env_ok["FIPP_ENV"] = "pilot"
    env_ok["FIPP_JWT_SECRET"] = "pilot_strong_random_jwt_secret_key_9f8e7d6c5b4a"
    env_ok["FIPP_AUTH_SALT"] = "pilot_strong_auth_salt_123456"

    ok_proc = subprocess.run(
        [py, "-c", "import app.core.config; print(app.core.config.IS_STRICT_DEPLOY)"],
        cwd=root,
        env=env_ok,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert ok_proc.returncode == 0, ok_proc.stderr
    assert "True" in ok_proc.stdout


def test_cors_and_security_headers(isolated_env):
    client = isolated_env["client"]

    r_allowed = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert r_allowed.status_code == 200
    assert r_allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert r_allowed.headers.get("x-content-type-options") == "nosniff"
    assert r_allowed.headers.get("x-frame-options") == "DENY"
    assert r_allowed.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "no-store" in (r_allowed.headers.get("cache-control") or "")

    r_evil = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert r_evil.headers.get("access-control-allow-origin") is None


def test_upload_validation_idor_and_path_traversal(isolated_env):
    client = isolated_env["client"]
    stu1_hdr = student_headers(client, "Aarav Sharma", "00123456")
    stu2_hdr = student_headers(client, "Priya Nair", "00123457")
    adm_hdr = admin_headers(client, isolated_env["admin_username"], isolated_env["admin_password"])

    assert client.post(
        "/api/uploads/photo",
        headers=stu1_hdr,
        files={"file": ("empty.png", b"", "image/png")},
    ).status_code == 400

    assert client.post(
        "/api/uploads/photo",
        headers=stu1_hdr,
        files={"file": ("huge.png", b"A" * (10 * 1024 * 1024 + 5), "image/png")},
    ).status_code == 400

    assert client.post(
        "/api/uploads/photo",
        headers=stu1_hdr,
        files={"file": ("fake.png", b"not-a-real-png-image", "image/png")},
    ).status_code == 400

    png_bytes = _make_png_bytes()
    r_ok = client.post(
        "/api/uploads/photo",
        headers=stu1_hdr,
        files={"file": ("evidence.png", png_bytes, "image/png")},
    )
    assert r_ok.status_code == 200, r_ok.text
    up_json = r_ok.json()
    stored_name = up_json["stored_filename"]

    create_res = client.post(
        "/api/student/complaints/submit",
        headers=stu1_hdr,
        json=_valid_submission(photo_stored_filename=stored_name, photo_sha256=up_json["sha256"]),
    )
    assert create_res.status_code in {200, 201}, create_res.text

    assert client.get(f"/api/uploads/{stored_name}").status_code == 401
    assert client.get(f"/api/uploads/{stored_name}", headers=stu2_hdr).status_code == 403
    assert client.get(f"/api/uploads/{stored_name}", headers=stu1_hdr).status_code == 200
    assert client.get(f"/api/uploads/{stored_name}", headers=adm_hdr).status_code == 200

    r_trav = client.get(
        "/api/uploads/..%2F..%2Fapp%2Fcore%2Fconfig.py",
        headers=adm_hdr,
    )
    assert r_trav.status_code in {400, 404}


def test_admin_dataset_upload_invalid_csv_returns_clean_400_instead_of_500(isolated_env):
    client = isolated_env["client"]
    adm_hdr = admin_headers(client, isolated_env["admin_username"], isolated_env["admin_password"])

    r = client.post(
        "/api/admin/dataset/upload",
        headers=adm_hdr,
        files={"file": ("bad.csv", b"col1,col2\n1,2\n", "text/csv")},
    )
    assert r.status_code == 400
    assert "validation failed" in r.json().get("detail", "").lower()


def test_lifecycle_transitions_atomic_persistence_and_failed_write_handling(isolated_env, monkeypatch):
    client = isolated_env["client"]
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    adm_hdr = admin_headers(client, isolated_env["admin_username"], isolated_env["admin_password"])

    r_a = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json=_valid_submission(title="Lifecycle Test Ticket"),
    )
    assert r_a.status_code in {200, 201}, r_a.text
    cid_a = _extract_id(r_a.json())

    assert client.post(
        f"/api/student/complaints/{cid_a}/feedback",
        headers=stu_hdr,
        json={"rating": 5, "comments": "Too early"},
    ).status_code == 400

    for st, extra in [
        ("Under Review", {"remarks": "Reviewed by supervisor."}),
        ("Assigned", {"remarks": "Assigned to Electrical Wing.", "allotted_person": "R. Sharma"}),
        ("In Progress", {"remarks": "Work underway."}),
        ("Resolved", {"remarks": "Faulty breaker replaced and tested."}),
    ]:
        r_up = client.patch(
            f"/api/admin/complaints/{cid_a}",
            headers=adm_hdr,
            json={"status": st, **extra},
        )
        assert r_up.status_code == 200, r_up.text
        updated = r_up.json().get("complaint", r_up.json())
        assert updated["status"] == st

    assert client.patch(
        f"/api/admin/complaints/{cid_a}",
        headers=adm_hdr,
        json={"status": "Submitted", "remarks": "Invalid rollback attempt."},
    ).status_code == 400

    assert client.post(
        f"/api/student/complaints/{cid_a}/feedback",
        headers=stu_hdr,
        json={"rating": 5, "comments": "Fast resolution!"},
    ).status_code == 200

    r_reopen = client.post(
        f"/api/admin/complaints/{cid_a}/reopen",
        headers=adm_hdr,
        json={"remarks": "Voltage fluctuates again."},
    )
    assert r_reopen.status_code == 200
    reopened = r_reopen.json().get("complaint", r_reopen.json())
    assert reopened["status"] == "Under Review"
    assert reopened["is_reopened"] is True

    fresh_service = ComplaintService(data_file=isolated_env["data_file"])
    persisted = fresh_service.get_by_id(cid_a)
    assert persisted is not None
    assert persisted["status"] == "Under Review"
    assert persisted["is_reopened"] is True

    r_b = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json=_valid_submission(title="Withdraw Terminal Ticket"),
    )
    cid_b = _extract_id(r_b.json())
    assert client.post(
        f"/api/student/complaints/{cid_b}/withdraw",
        headers=stu_hdr,
        json={"reason": "Issue resolved on its own."},
    ).status_code == 200

    assert client.patch(
        f"/api/admin/complaints/{cid_b}",
        headers=adm_hdr,
        json={"status": "In Progress", "remarks": "Should not transition from Withdrawn."},
    ).status_code == 400

    def _boom(*_args, **_kwargs):
        raise OSError("Simulated disk full at /var/secret/complaints.json")

    monkeypatch.setattr("os.replace", _boom)
    r_fail_save = client.post(
        "/api/student/complaints/submit",
        headers=stu_hdr,
        json=_valid_submission(title="Disk Failure Test"),
    )
    assert r_fail_save.status_code == 500
    detail = r_fail_save.json().get("detail", "")
    assert "/var/secret" not in detail
    assert "persist" in detail.lower()


def test_concurrent_submissions_generate_unique_tokens_with_zero_loss(isolated_env):
    client = isolated_env["client"]
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")
    initial_count = len(json.loads(isolated_env["data_file"].read_text(encoding="utf-8")))

    def _submit(idx: int):
        r = client.post(
            "/api/student/complaints/submit",
            headers=stu_hdr,
            json=_valid_submission(title=f"Concurrent Ticket {idx}"),
        )
        assert r.status_code in {200, 201}, r.text
        return _extract_id(r.json())

    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(_submit, range(8)))

    assert len(set(tokens)) == 8
    stored = json.loads(isolated_env["data_file"].read_text(encoding="utf-8"))
    assert len(stored) == initial_count + 8


def test_privacy_csv_redaction_and_mcpi_parity(isolated_env):
    client = isolated_env["client"]
    adm_hdr = admin_headers(client, isolated_env["admin_username"], isolated_env["admin_password"])
    stu_hdr = student_headers(client, "Aarav Sharma", "00123456")

    r_csv = client.get("/api/admin/reports/export", headers=adm_hdr)
    assert r_csv.status_code == 200
    csv_body = r_csv.text
    assert "[REDACTED]" in csv_body

    me_res = client.get("/api/auth/me", headers=stu_hdr).json()
    assert "password_hash" not in json.dumps(me_res)

    intel_res = client.get(
        "/api/admin/intelligence/complaint/CMP-2026-001",
        headers=adm_hdr,
    )
    assert intel_res.status_code == 200
    intel = intel_res.json()
    mcpi = intel["mcpi"]
    assert mcpi["is_ml_prediction"] is False
    assert mcpi["weights"]["severity"] == pytest.approx(0.35)
    assert mcpi["weights"]["location_criticality"] == pytest.approx(0.25)
    assert mcpi["weights"]["recurrence_probability"] == pytest.approx(0.25)
    assert mcpi["weights"]["impact_population"] == pytest.approx(0.15)
    component_sum = sum(c["points"] for c in mcpi["components"])
    assert component_sum == pytest.approx(mcpi["priority_score"], abs=0.25)
