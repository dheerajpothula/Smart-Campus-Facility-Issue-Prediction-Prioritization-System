import os
import sys
import tempfile
import secrets
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.core import security
from app.main import app
from app.services.complaint_service import complaint_service
from app.data.database import campus_db


def test_system_rbac_and_isolated_auth(tmp_path: Path, monkeypatch):
    data_file = tmp_path / "complaints.json"
    data_file.write_text("[]", encoding="utf-8")
    admin_store = tmp_path / "admin_accounts.json"
    stu_reg = tmp_path / "student_registry.json"
    stu_reg.write_text("[]", encoding="utf-8")

    monkeypatch.setenv("FIPP_ADMIN_STORE_FILE", str(admin_store))
    monkeypatch.setenv("FIPP_STUDENT_REGISTRY_FILE", str(stu_reg))
    monkeypatch.setattr(complaint_service, "data_file", data_file)

    boot = security.bootstrap_initial_admin()
    pwd = f"SysTest!{secrets.token_hex(5)}A1"
    security.change_admin_password(boot["username"], boot["temporary_password"], pwd)
    security.provision_student("00123456", "System Test Student", block="Block 57")

    client = TestClient(app)

    r_stu = client.post(
        "/api/auth/student/login",
        json={"student_name": "System Test Student", "student_id": "00123456"},
    )
    assert r_stu.status_code == 200
    stu_token = r_stu.json()["access_token"]

    r_adm = client.post(
        "/api/auth/login",
        json={"username": boot["username"], "password": pwd},
    )
    assert r_adm.status_code == 200
    adm_token = r_adm.json()["access_token"]

    assert client.get("/api/admin/complaints", headers={"Authorization": f"Bearer {stu_token}"}).status_code == 403
    assert client.get("/api/admin/complaints", headers={"Authorization": f"Bearer {adm_token}"}).status_code == 200
    assert client.get("/api/admin/dataset/summary", headers={"Authorization": f"Bearer {adm_token}"}).status_code == 200
