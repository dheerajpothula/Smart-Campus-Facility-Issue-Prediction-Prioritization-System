"""
Shared isolated test helpers for FIPP 2.0 backend pytest suites.
Isolates all mutable stores (`complaints.json`, `uploads`, `admin_accounts.json`,
`student_registry.json`, `revoked_tokens.json`, `campus_blocks_override.json`) inside `tmp_path`.
"""
from __future__ import annotations

import secrets
import shutil
from pathlib import Path
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.core.config import CAMPUS_BLOCKS_SEED_FILE, PRIMARY_JSON_DATA_FILE
from app.core.security import (
    bootstrap_initial_admin,
    change_admin_password,
    provision_student,
)
from app.services.complaint_service import complaint_service


def setup_isolated_environment(tmp_path: Path, monkeypatch, seed_complaints: Any = None) -> Dict[str, Any]:
    """Configures complete `tmp_path` isolation for stores and provisions ephemeral test accounts."""
    data_file = tmp_path / "complaints.json"
    if seed_complaints is not None:
        import json
        data_file.write_text(json.dumps(seed_complaints, indent=2), encoding="utf-8")
    elif PRIMARY_JSON_DATA_FILE.exists():
        shutil.copy2(PRIMARY_JSON_DATA_FILE, data_file)
    else:
        data_file.write_text("[]", encoding="utf-8")

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

    boot = bootstrap_initial_admin()
    active_admin_pwd = f"QaPilot!{secrets.token_hex(6)}A1"
    change_admin_password(boot["username"], boot["temporary_password"], active_admin_pwd)

    stu1 = provision_student("00123456", "Aarav Sharma", block="Block 57", room_number="204", provisioned_by="fipp.admin")
    stu2 = provision_student("00123457", "Priya Nair", block="Block 3", room_number="102", provisioned_by="fipp.admin")

    return {
        "data_file": data_file,
        "upload_dir": upload_dir,
        "revoked_file": revoked_file,
        "admin_store": admin_store,
        "student_registry": student_registry,
        "blocks_file": blocks_file,
        "admin_username": boot["username"],
        "admin_password": active_admin_pwd,
        "student1": stu1,
        "student2": stu2,
    }


def admin_headers(client: TestClient, username: str, password: str) -> Dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def student_headers(client: TestClient, student_name: str, student_id: str) -> Dict[str, str]:
    res = client.post(
        "/api/auth/student/login",
        json={"student_name": student_name, "student_id": student_id},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
