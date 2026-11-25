"""
FIPP 2.0 — Phase 8 Stage B Isolated Backend QA & Security Suite.

Strictly uses pytest `tmp_path` isolation for complaints storage, uploaded media,
and revoked token lists so live operational records are never mutated.
"""
from __future__ import annotations

import copy
import io
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY, PRIMARY_JSON_DATA_FILE
from app.core.security import SYSTEM_USER_STORE, create_access_token
from app.main import app
from app.services.complaint_service import ComplaintService, complaint_service


def _make_png_bytes(width: int = 8, height: int = 8) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(37, 99, 235))
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Isolate complaints JSON, upload directory, and revoked token store per test."""
    data_file = tmp_path / "complaints.json"
    if PRIMARY_JSON_DATA_FILE.exists():
        shutil.copy2(PRIMARY_JSON_DATA_FILE, data_file)
    else:
        data_file.write_text("[]", encoding="utf-8")

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    revoked_file = tmp_path / "revoked_tokens.json"
    revoked_file.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(complaint_service, "data_file", data_file)
    monkeypatch.setattr("app.services.upload_service.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("app.api.routes_uploads.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("app.core.security._REVOKED_TOKENS_FILE", revoked_file)
    monkeypatch.setattr("app.core.security._REVOKED_TOKENS", set())

    return {
        "client": TestClient(app),
        "data_file": data_file,
        "upload_dir": upload_dir,
        "revoked_file": revoked_file,
    }


def _login(client: TestClient, username: str, password: str) -> dict:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _valid_submission(**overrides) -> dict:
    payload = {
        "category_type": "Maintenance / Electrical Complaints",
        "message_type": "Grievance",
        "title": "QA Isolated Electrical Test",
        "category": "Electrical",
        "sub_category": "Power Supply / Socket",
        "specific_categories": ["Sparking socket"],
        "building": "Academic Block 34",
        "sub_block": "Wing A",
        "room_type": "Room No",
        "room_number": "304",
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


# ---------------------------------------------------------------------------
# 1. Authentication, Token Revocation & Role Authorization Security
# ---------------------------------------------------------------------------

def test_auth_rejects_expired_malformed_and_revoked_tokens(isolated_env, monkeypatch):
    client = isolated_env["client"]

    # Expired token -> 401
    expired_payload = {
        "sub": "STU-2026-001",
        "id": "STU-2026-001",
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
    auth_data = _login(client, "STU-2026-001", "student123")
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

    # Inactive user rejection -> 403
    inactive_user = copy.deepcopy(SYSTEM_USER_STORE["STU-2026-001"])
    inactive_user["is_active"] = False
    monkeypatch.setitem(SYSTEM_USER_STORE, "STU-INACTIVE", inactive_user)
    tok = create_access_token({**inactive_user, "id": "STU-INACTIVE"})
    res_inactive = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert res_inactive.status_code == 403


def test_role_isolation_blocks_student_admin_crossover(isolated_env):
    client = isolated_env["client"]
    stu_token = _login(client, "STU-2026-001", "student123")["access_token"]
    adm_token = _login(client, "ADM-2026-001", "Admin@001")["access_token"]

    # Student blocked from admin endpoints
    for endpoint in [
        "/api/admin/kpis",
        "/api/admin/complaints",
        "/api/admin/intelligence/overview",
        "/api/admin/intelligence/complaint/CMP-2026-001",
        "/api/admin/reports/analytics",
        "/api/admin/reports/export",
    ]:
        r = client.get(endpoint, headers={"Authorization": f"Bearer {stu_token}"})
        assert r.status_code == 403, f"Expected 403 for student on {endpoint}, got {r.status_code}"

    # Admin blocked from student endpoints
    r_adm = client.get("/api/student/complaints", headers={"Authorization": f"Bearer {adm_token}"})
    assert r_adm.status_code == 403


# ---------------------------------------------------------------------------
# 2. Fail-Fast Pilot/Production Secrets & CORS / Security Headers
# ---------------------------------------------------------------------------

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

    # Allowed trusted origin
    r_allowed = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert r_allowed.status_code == 200
    assert r_allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert r_allowed.headers.get("x-content-type-options") == "nosniff"
    assert r_allowed.headers.get("x-frame-options") == "DENY"
    assert r_allowed.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "no-store" in (r_allowed.headers.get("cache-control") or "")

    # Untrusted wildcard/external origin rejected
    r_evil = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert r_evil.headers.get("access-control-allow-origin") is None


# ---------------------------------------------------------------------------
# 3. Upload Security, Attachment Ownership & Dataset Upload Fix
# ---------------------------------------------------------------------------

def test_upload_validation_idor_and_path_traversal(isolated_env):
    client = isolated_env["client"]
    stu1_token = _login(client, "STU-2026-001", "student123")["access_token"]
    stu2_token = _login(client, "STU102", "student123")["access_token"]
    adm_token = _login(client, "ADM-2026-001", "Admin@001")["access_token"]

    # 0-byte file -> 400
    r_empty = client.post(
        "/api/uploads/photo",
        headers={"Authorization": f"Bearer {stu1_token}"},
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert r_empty.status_code == 400

    # Oversized >10MB -> 400
    r_big = client.post(
        "/api/uploads/photo",
        headers={"Authorization": f"Bearer {stu1_token}"},
        files={"file": ("huge.png", b"A" * (10 * 1024 * 1024 + 5), "image/png")},
    )
    assert r_big.status_code == 400

    # Spoofed/WebP MIME or magic bytes -> 400
    r_spoof = client.post(
        "/api/uploads/photo",
        headers={"Authorization": f"Bearer {stu1_token}"},
        files={"file": ("fake.png", b"not-a-real-png-image", "image/png")},
    )
    assert r_spoof.status_code == 400

    # Valid PNG upload + complaint link
    png_bytes = _make_png_bytes()
    r_ok = client.post(
        "/api/uploads/photo",
        headers={"Authorization": f"Bearer {stu1_token}"},
        files={"file": ("evidence.png", png_bytes, "image/png")},
    )
    assert r_ok.status_code == 200, r_ok.text
    up_json = r_ok.json()
    stored_name = up_json["stored_filename"]

    create_res = client.post(
        "/api/student/complaints/submit",
        headers={"Authorization": f"Bearer {stu1_token}"},
        json=_valid_submission(photo_stored_filename=stored_name, photo_sha256=up_json["sha256"]),
    )
    assert create_res.status_code in {200, 201}, create_res.text

    # Unauthenticated GET attachment -> 401
    assert client.get(f"/api/uploads/{stored_name}").status_code == 401

    # Different student IDOR attempt -> 403
    assert client.get(
        f"/api/uploads/{stored_name}",
        headers={"Authorization": f"Bearer {stu2_token}"},
    ).status_code == 403

    # Owner and Admin allowed -> 200
    assert client.get(
        f"/api/uploads/{stored_name}",
        headers={"Authorization": f"Bearer {stu1_token}"},
    ).status_code == 200
    assert client.get(
        f"/api/uploads/{stored_name}",
        headers={"Authorization": f"Bearer {adm_token}"},
    ).status_code == 200

    # Path traversal blocked (400 or 404)
    r_trav = client.get(
        "/api/uploads/..%2F..%2Fapp%2Fcore%2Fconfig.py",
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert r_trav.status_code in {400, 404}


def test_admin_dataset_upload_invalid_csv_returns_clean_400_instead_of_500(isolated_env):
    client = isolated_env["client"]
    adm_token = _login(client, "ADM-2026-001", "Admin@001")["access_token"]

    r = client.post(
        "/api/admin/dataset/upload",
        headers={"Authorization": f"Bearer {adm_token}"},
        files={"file": ("bad.csv", b"col1,col2\n1,2\n", "text/csv")},
    )
    assert r.status_code == 400
    assert "validation failed" in r.json().get("detail", "").lower()


# ---------------------------------------------------------------------------
# 4. Lifecycle Integrity, Failed-Write Handling, Persistence & Concurrency
# ---------------------------------------------------------------------------

def test_lifecycle_transitions_atomic_persistence_and_failed_write_handling(isolated_env, monkeypatch):
    client = isolated_env["client"]
    stu_token = _login(client, "STU-2026-001", "student123")["access_token"]
    adm_token = _login(client, "ADM-2026-001", "Admin@001")["access_token"]

    # Create Ticket A -> full valid lifecycle + reopen
    r_a = client.post(
        "/api/student/complaints/submit",
        headers={"Authorization": f"Bearer {stu_token}"},
        json=_valid_submission(title="Lifecycle Test Ticket"),
    )
    assert r_a.status_code in {200, 201}, r_a.text
    cid_a = _extract_id(r_a.json())

    # Feedback before Resolved blocked -> 400
    r_fb_early = client.post(
        f"/api/student/complaints/{cid_a}/feedback",
        headers={"Authorization": f"Bearer {stu_token}"},
        json={"rating": 5, "comments": "Too early"},
    )
    assert r_fb_early.status_code == 400

    # Valid admin progression -> Under Review -> Assigned -> In Progress -> Resolved
    for st, extra in [
        ("Under Review", {"remarks": "Reviewed by supervisor."}),
        ("Assigned", {"remarks": "Assigned to Electrical Wing.", "allotted_person": "R. Sharma"}),
        ("In Progress", {"remarks": "Work underway."}),
        ("Resolved", {"remarks": "Faulty breaker replaced and tested."}),
    ]:
        r_up = client.patch(
            f"/api/admin/complaints/{cid_a}",
            headers={"Authorization": f"Bearer {adm_token}"},
            json={"status": st, **extra},
        )
        assert r_up.status_code == 200, r_up.text
        updated = r_up.json().get("complaint", r_up.json())
        assert updated["status"] == st

    # Invalid direct downgrade out of Resolved via PATCH -> 400 (must use /reopen)
    r_bad_downgrade = client.patch(
        f"/api/admin/complaints/{cid_a}",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"status": "Submitted", "remarks": "Invalid rollback attempt."},
    )
    assert r_bad_downgrade.status_code == 400

    # Student feedback on Resolved ticket -> 200
    r_fb = client.post(
        f"/api/student/complaints/{cid_a}/feedback",
        headers={"Authorization": f"Bearer {stu_token}"},
        json={"rating": 5, "comments": "Fast resolution!"},
    )
    assert r_fb.status_code == 200

    # Admin reopen -> Under Review
    r_reopen = client.post(
        f"/api/admin/complaints/{cid_a}/reopen",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"remarks": "Voltage fluctuates again."},
    )
    assert r_reopen.status_code == 200
    reopened = r_reopen.json().get("complaint", r_reopen.json())
    assert reopened["status"] == "Under Review"
    assert reopened["is_reopened"] is True

    # Verify persistence across a brand new ComplaintService instance
    fresh_service = ComplaintService(data_file=isolated_env["data_file"])
    persisted = fresh_service.get_by_id(cid_a)
    assert persisted is not None
    assert persisted["status"] == "Under Review"
    assert persisted["is_reopened"] is True

    # Create Ticket B -> withdraw -> verify Withdrawn terminal rule
    r_b = client.post(
        "/api/student/complaints/submit",
        headers={"Authorization": f"Bearer {stu_token}"},
        json=_valid_submission(title="Withdraw Terminal Ticket"),
    )
    assert r_b.status_code in {200, 201}, r_b.text
    cid_b = _extract_id(r_b.json())
    r_wd = client.post(
        f"/api/student/complaints/{cid_b}/withdraw",
        headers={"Authorization": f"Bearer {stu_token}"},
        json={"reason": "Issue resolved on its own."},
    )
    assert r_wd.status_code == 200

    r_after_wd = client.patch(
        f"/api/admin/complaints/{cid_b}",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"status": "In Progress", "remarks": "Should not transition from Withdrawn."},
    )
    assert r_after_wd.status_code == 400

    # Simulate disk write failure -> RuntimeError -> 500 without leaking raw path
    def _boom(*_args, **_kwargs):
        raise OSError("Simulated disk full at /var/secret/complaints.json")

    monkeypatch.setattr("os.replace", _boom)
    r_fail_save = client.post(
        "/api/student/complaints/submit",
        headers={"Authorization": f"Bearer {stu_token}"},
        json=_valid_submission(title="Disk Failure Test"),
    )
    assert r_fail_save.status_code == 500
    detail = r_fail_save.json().get("detail", "")
    assert "/var/secret" not in detail
    assert "persist" in detail.lower()


def test_concurrent_submissions_generate_unique_tokens_with_zero_loss(isolated_env):
    client = isolated_env["client"]
    stu_token = _login(client, "STU-2026-001", "student123")["access_token"]
    initial_count = len(json.loads(isolated_env["data_file"].read_text(encoding="utf-8")))

    def _submit(idx: int):
        r = client.post(
            "/api/student/complaints/submit",
            headers={"Authorization": f"Bearer {stu_token}"},
            json=_valid_submission(title=f"Concurrent Ticket {idx}"),
        )
        assert r.status_code in {200, 201}, r.text
        return _extract_id(r.json())

    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(_submit, range(8)))

    assert len(set(tokens)) == 8
    stored = json.loads(isolated_env["data_file"].read_text(encoding="utf-8"))
    assert len(stored) == initial_count + 8


# ---------------------------------------------------------------------------
# 5. Data Privacy, CSV Redaction & Phase 7 MCPI Regression
# ---------------------------------------------------------------------------

def test_privacy_csv_redaction_and_mcpi_parity(isolated_env):
    client = isolated_env["client"]
    adm_token = _login(client, "ADM-2026-001", "Admin@001")["access_token"]
    stu_token = _login(client, "STU-2026-001", "student123")["access_token"]

    # Export CSV masks PII
    r_csv = client.get("/api/admin/reports/export", headers={"Authorization": f"Bearer {adm_token}"})
    assert r_csv.status_code == 200
    csv_body = r_csv.text
    assert "[REDACTED]" in csv_body
    assert "STU-2026-001" not in csv_body
    assert "9876543210" not in csv_body

    # Auth response and intelligence endpoint never leak password hashes
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {stu_token}"}).json()
    assert "password_hash" not in json.dumps(me_res)

    intel_res = client.get(
        "/api/admin/intelligence/complaint/CMP-2026-001",
        headers={"Authorization": f"Bearer {adm_token}"},
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
