"""
FIPP 2.0 — Phase 7: Predictive Intelligence Integration Test Suite (Backend).
Verifies MCPI consistency, SHAP unavailable & supported paths, RBAC, rate limiting,
invalid inputs, workload analytics accuracy, empty datasets, and zero data leakage.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import reset_rate_limiter
from app.main import app
from app.services.complaint_service import complaint_service
from app.services.intelligence_service import IntelligenceService, intelligence_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    reset_rate_limiter()
    yield
    reset_rate_limiter()


@pytest.fixture
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Provides an isolated temporary complaints JSON store for deterministic Phase 7 tests."""
    temp_file = tmp_path / "complaints_phase7.json"
    now = datetime.now()
    seed = [
        {
            "complaint_id": "CMP-2026-901",
            "student_id": "STU101",
            "student_name": "Rahul Sharma",
            "category": "Electricity",
            "facility_type": "Electricity",
            "building": "Academic Block 1",
            "location": "Academic Block 1 - Room 101",
            "title": "Server Room breaker sparking",
            "description": "Main server room distribution breaker sparking repeatedly.",
            "severity": "Critical",
            "location_type": "Server Room",
            "recurrence_risk": 0.85,
            "impact_scale": 0.90,
            "status": "Submitted",
            "date_reported": (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
            "remarks_history": [],
        },
        {
            "complaint_id": "CMP-2026-902",
            "student_id": "STU102",
            "student_name": "Priya Patel",
            "category": "Plumbing",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "location": "Hostel Block B - 2nd Floor",
            "title": "Washroom tap leakage",
            "description": "Continuous leakage in hostel washroom.",
            "severity": "High",
            "location_type": "Hostel Washroom",
            "recurrence_risk": 0.50,
            "impact_scale": 0.60,
            "status": "In Progress",
            "allotted_person": "Ramesh Kumar",
            "department": "Plumbing Squad",
            "date_reported": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "remarks_history": [],
        },
        {
            "complaint_id": "CMP-2026-903",
            "student_id": "STU101",
            "student_name": "Rahul Sharma",
            "category": "Carpentry",
            "facility_type": "Carpentry",
            "building": "BH-1 Boys Hostel",
            "location": "BH-1 Boys Hostel - Room 204",
            "title": "Loose cupboard door",
            "description": "Cupboard hinge slightly loose.",
            "severity": "Low",
            "location_type": "Campus Grounds",
            "recurrence_risk": 0.10,
            "impact_scale": 0.10,
            "status": "Resolved",
            "allotted_person": "Satish Verma",
            "department": "Carpentry Squad",
            "resolved_by": "ADM-2026-001",
            "closing_remarks": "Tightened hinge screws.",
            "is_reopened": True,
            "date_reported": (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
            "resolved_at": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "remarks_history": [],
        },
    ]
    temp_file.write_text(json.dumps(seed, indent=2), encoding="utf-8")
    monkeypatch.setattr(complaint_service, "data_file", temp_file)
    return temp_file


def _auth_headers(username: str, password: str) -> dict:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_mcpi_calculation_consistency_and_thresholds(isolated_store):
    adm_headers = _auth_headers("ADM-2026-001", "Admin@001")

    # Fetch intelligence for Critical Server Room complaint (0.35*100 + 0.25*100 + 0.25*85 + 0.15*90 = 94.8)
    res = client.get("/api/admin/intelligence/complaint/CMP-2026-901", headers=adm_headers)
    assert res.status_code == 200
    body = res.json()
    mcpi = body["mcpi"]
    assert mcpi["is_ml_prediction"] is False
    assert mcpi["weights"] == {
        "severity": 0.35,
        "location_criticality": 0.25,
        "recurrence_probability": 0.25,
        "impact_population": 0.15,
    }
    assert mcpi["priority_score"] == 94.8
    assert mcpi["priority_tier"] == "Critical"
    pts_sum = round(sum(c["points"] for c in mcpi["components"]), 1)
    assert abs(pts_sum - mcpi["priority_score"]) <= 0.2

    # Low threshold (<28): 0.35*20 + 0.25*25 + 0.25*10 + 0.15*10 = 7.0 + 6.25 + 2.5 + 1.5 = 17.25 -> 17.2
    res_low = client.get("/api/admin/intelligence/complaint/CMP-2026-903", headers=adm_headers)
    assert res_low.status_code == 200
    mcpi_low = res_low.json()["mcpi"]
    assert mcpi_low["priority_score"] == 17.2
    assert mcpi_low["priority_tier"] == "Low"


def test_shap_missing_artifact_and_missing_explainer_handling(isolated_store, tmp_path: Path):
    adm_headers = _auth_headers("ADM-2026-001", "Admin@001")

    # Live environment: no model artifacts and no shap installed -> honest unavailable state
    res = client.get("/api/admin/intelligence/complaint/CMP-2026-901", headers=adm_headers)
    assert res.status_code == 200
    shap = res.json()["shap"]
    assert shap["available"] is False
    assert shap["status"] == "unavailable"
    assert shap["model_artifact_present"] is False
    assert shap["shap_library_installed"] is False
    assert shap["features"] == []

    # Direct /api/ml/shap/{id} must also report honest unavailable state
    ml_shap = client.get("/api/ml/shap/CMP-2026-901", headers=adm_headers)
    assert ml_shap.status_code == 200
    assert ml_shap.json()["available"] is False
    assert ml_shap.json()["features"] == []

    # Missing explainer when an artifact file exists on disk
    models_dir = tmp_path / "models_with_artifact"
    models_dir.mkdir()
    (models_dir / "dummy_model.joblib").write_bytes(b"placeholder")
    svc = IntelligenceService(models_dir=models_dir)
    caps = svc.inspect_ml_capabilities()
    assert caps["shap_explainability"]["model_artifact_present"] is True
    assert caps["shap_explainability"]["shap_library_installed"] is False
    assert caps["shap_explainability"]["available"] is False
    shap_res = svc.get_shap_status_for_complaint({"complaint_id": "CMP-2026-901"})
    assert shap_res["available"] is False
    assert shap_res["features"] == []


def test_shap_supported_model_and_explainer_bundle(isolated_store, monkeypatch: pytest.MonkeyPatch):
    adm_headers = _auth_headers("ADM-2026-001", "Admin@001")

    def fake_bundle():
        return {
            "explain_fn": lambda rec: {
                "explanation_method": "TreeSHAP",
                "model_version": "v1.0-test",
                "prediction_timestamp": "2026-11-25T14:30:00Z",
                "prediction": "Critical",
                "base_value": 52.0,
                "output_value": 89.5,
                "features": [
                    {
                        "feature_name": "Severity Signal",
                        "feature_value": rec.get("severity"),
                        "shap_value": 24.5,
                        "contribution": "increase",
                        "description": "High hazard language contribution in model output.",
                    }
                ],
                "summary": "Model output driven upward by Severity Signal.",
            }
        }

    monkeypatch.setattr(intelligence_service, "load_supported_shap_bundle", fake_bundle)
    res = client.get("/api/admin/intelligence/complaint/CMP-2026-901", headers=adm_headers)
    assert res.status_code == 200
    shap = res.json()["shap"]
    assert shap["available"] is True
    assert shap["model_version"] == "v1.0-test"
    assert shap["prediction"] == "Critical"
    assert len(shap["features"]) == 1
    assert shap["features"][0]["shap_value"] == 24.5


def test_admin_only_intelligence_rbac_and_student_isolation(isolated_store):
    stu_headers = _auth_headers("STU101", "student123")
    adm_headers = _auth_headers("ADM-2026-001", "Admin@001")

    admin_only_gets = [
        "/api/admin/intelligence/overview",
        "/api/admin/intelligence/complaint/CMP-2026-901",
        "/api/ml/shap/CMP-2026-901",
        "/api/ml/predictive",
        "/api/ml/metrics",
        "/api/settings/weights",
        "/api/kpi",
        "/api/model-metrics",
        "/api/predictive-maintenance",
        "/api/recurring-issues",
    ]
    for path in admin_only_gets:
        assert client.get(path).status_code == 401, f"Expected 401 on {path}"
        assert client.get(path, headers=stu_headers).status_code == 403, f"Expected 403 on {path}"
        assert client.get(path, headers=adm_headers).status_code == 200, f"Expected 200 on {path}"

    # POST ML endpoints also enforce admin-only RBAC
    assert client.post("/api/ml/analyze", json={"text": "Sparking socket in lab"}).status_code == 401
    assert client.post("/api/ml/analyze", json={"text": "Sparking socket in lab"}, headers=stu_headers).status_code == 403
    assert client.post("/api/ml/shap/custom", json={}, headers=stu_headers).status_code == 403

    # Student portal does NOT expose mcpi_details
    stu_list = client.get("/api/student/complaints", headers=stu_headers)
    assert stu_list.status_code == 200
    for rec in stu_list.json()["records"]:
        assert rec["student_id"] == "STU101"
        assert rec.get("mcpi_details") is None

    # Health check must not leak internal filesystem paths
    health = client.get("/api/health").json()
    assert "path" not in health["datastore"]


def test_invalid_inputs_and_rate_limiting(isolated_store):
    adm_headers = _auth_headers("ADM-2026-001", "Admin@001")

    # Whitespace-only or too-short text rejected
    assert client.post("/api/ml/analyze", json={"text": "   "}, headers=adm_headers).status_code == 422
    assert client.post("/api/ml/analyze", json={"text": "ab"}, headers=adm_headers).status_code == 422
    # Missing complaint returns 404
    assert client.get("/api/admin/intelligence/complaint/CMP-DOES-NOT-EXIST", headers=adm_headers).status_code == 404
    assert client.get("/api/ml/shap/CMP-DOES-NOT-EXIST", headers=adm_headers).status_code == 404

    # Rate limit enforcement (> 60 requests in window returns 429)
    for _ in range(60):
        r = client.get("/api/admin/intelligence/complaint/CMP-2026-901", headers=adm_headers)
        assert r.status_code == 200
    over = client.get("/api/admin/intelligence/complaint/CMP-2026-901", headers=adm_headers)
    assert over.status_code == 429


def test_workload_analytics_and_empty_dataset_handling(isolated_store):
    adm_headers = _auth_headers("ADM-2026-001", "Admin@001")

    rep = client.get("/api/admin/reports/analytics", headers=adm_headers).json()
    workload = rep["workload_summary"]
    assert workload["active_total"] == 2
    assert workload["unassigned_active"] == 1
    assert workload["assigned_active"] == 1
    assert workload["reopened_count"] == 1
    assert workload["high_critical_active"] == 2
    assert workload["average_mcpi_score"] is not None

    assignees = {item["assignee"]: item for item in rep["assignment_distribution"]}
    assert assignees["Unassigned"]["active_count"] == 1
    assert assignees["Ramesh Kumar"]["active_count"] == 1
    assert assignees["Satish Verma"]["resolved_count"] == 1

    # Recurring issues must only inspect live operational records, not 5,500 historical CSV rows
    rec_res = client.get("/api/recurring-issues", headers=adm_headers).json()
    assert rec_res["source"] == "live_operational_records"
    assert rec_res["total_recurring_tickets"] <= 3

    # Empty dataset must be handled safely without fabricated metrics
    isolated_store.write_text("[]", encoding="utf-8")
    empty_rep = client.get("/api/admin/reports/analytics", headers=adm_headers).json()
    assert empty_rep["kpis"]["total"] == 0
    assert empty_rep["kpis"]["average_turnaround_days"] is None
    assert empty_rep["workload_summary"]["active_total"] == 0
    assert empty_rep["workload_summary"]["average_mcpi_score"] is None
    assert empty_rep["assignment_distribution"] == []
