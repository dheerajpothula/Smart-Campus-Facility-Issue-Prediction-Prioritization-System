import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.ml.nlp_classifier import nlp_model
from app.ml.severity_model import severity_model
from app.ml.recurrence_detector import recurrence_detector
from app.ml.risk_model import risk_model
from app.ml.priority_engine import priority_engine, active_priority_weights
from app.ml.shap_explainer import shap_explainer
from app.ml.predictive_engine import predictive_engine
from app.models.data_models import PriorityWeights, ComplaintSubmission
from app.data.database import campus_db

client = TestClient(app)

def test_nlp_classifier():
    print("[TEST 1/8] Testing NLP Classifier...")
    cat, conf, probs = nlp_model.predict("The water cooler on 2nd floor is not dispensing cold water.")
    assert cat == "Water Cooler", f"Expected 'Water Cooler', got {cat}"
    assert conf > 0.3, "Confidence should be significant"
    assert "Water Cooler" in probs
    print(f" -> NLP Success: Predicted '{cat}' with confidence {conf:.2f}")

def test_severity_model():
    print("[TEST 2/8] Testing Severity Model...")
    sev, conf, score, signals = severity_model.predict("Sparks flying from main distribution switchboard in lab.")
    assert sev in ["Critical", "High"], f"Expected Critical or High for sparks, got {sev}"
    assert score >= 75.0, f"Expected severity score >= 75, got {score}"
    assert signals["has_hazard_keywords"] is True
    print(f" -> Severity Success: '{sev}' with score {score}")

def test_priority_engine_math():
    print("[TEST 3/8] Testing Priority Engine and Configurable Weights...")
    weights = PriorityWeights(
        weight_severity=0.40,
        weight_recurrence=0.30,
        weight_footfall=0.10,
        weight_location_risk=0.10,
        weight_impact=0.10
    )
    res = priority_engine.calculate_priority(
        severity_score=90.0,
        recurrence_score=80.0,
        footfall_score=70.0,
        location_risk_score=60.0,
        impact_score=80.0,
        facility_type="Water Cooler",
        predicted_severity="High",
        weights=weights
    )
    expected = (0.40*90.0) + (0.30*80.0) + (0.10*70.0) + (0.10*60.0) + (0.10*80.0)
    assert abs(res["priority_score"] - round(expected, 1)) < 0.2, f"Priority math mismatch: {res['priority_score']} vs {expected}"
    assert "recommended_action" in res
    print(f" -> Priority Math Success: {res['priority_score']} / 100")

def test_shap_game_theoretic_efficiency():
    print("[TEST 4/8] Testing SHAP Efficiency Axiom...")
    weights = PriorityWeights(
        weight_severity=0.35,
        weight_recurrence=0.25,
        weight_footfall=0.20,
        weight_location_risk=0.10,
        weight_impact=0.10
    )
    norm_w = [0.35, 0.25, 0.20, 0.10, 0.10]
    inputs = [85.0, 90.0, 88.0, 75.0, 80.0]
    priority_val = round(sum(w * x for w, x in zip(norm_w, inputs)), 1)

    expl = shap_explainer.explain(
        severity_score=inputs[0],
        recurrence_score=inputs[1],
        footfall_score=inputs[2],
        location_risk_score=inputs[3],
        impact_score=inputs[4],
        priority_score=priority_val,
        weights=weights
    )
    shap_sum = sum(f.shap_value for f in expl.features)
    reconstructed = expl.base_value + shap_sum
    assert abs(reconstructed - priority_val) < 0.5, f"SHAP efficiency failed: base({expl.base_value}) + sum({shap_sum}) = {reconstructed} != {priority_val}"
    print(f" -> SHAP Efficiency Verified: base {expl.base_value} + sum {shap_sum:.2f} = {reconstructed:.2f} (Target: {priority_val})")

def test_predictive_disclaimer():
    print("[TEST 5/8] Testing Predictive Maintenance Integrity & Disclaimers...")
    forecasts = predictive_engine.get_forecasts()
    assert len(forecasts) >= 4
    for f in forecasts:
        assert "Prediction ≠ Confirmed Physical Breakdown" in f.disclaimer
    print(" -> Predictive Disclaimers Verified!")

def test_authentication_rbac():
    print("[TEST 6/8] Testing Role-Based Authentication & JWT-like Tokens...")
    # 1. Student Login
    r = client.post("/api/auth/login", json={"username": "STU101", "password": "student123"})
    assert r.status_code == 200
    stu_auth = r.json()
    assert stu_auth["success"] is True
    assert stu_auth["user"]["role"] == "student"
    stu_token = stu_auth["token"]

    # 2. Admin Login
    r = client.post("/api/auth/login", json={"username": "ADMIN01", "password": "admin123"})
    assert r.status_code == 200
    adm_auth = r.json()
    assert adm_auth["success"] is True
    assert adm_auth["user"]["role"] == "admin"
    adm_token = adm_auth["token"]

    # 3. Invalid credentials
    r = client.post("/api/auth/login", json={"username": "STU101", "password": "wrongpassword"})
    assert r.status_code == 401

    # 4. Token validation
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {stu_token}"})
    assert r.status_code == 200
    assert r.json()["user"]["id"] == "STU101"
    print(" -> Authentication & Session Tokens Verified!")
    return stu_token, adm_token

def test_student_isolation_and_workflow(stu_token):
    print("[TEST 7/8] Testing Student Privacy Isolation & Complaint Filing...")
    # 1. Student can fetch own complaints
    r = client.get("/api/student/complaints", headers={"Authorization": f"Bearer {stu_token}"})
    assert r.status_code == 200
    stu_data = r.json()
    assert stu_data["student_id"] == "STU101"
    for c in stu_data["complaints"]:
        assert c["student_id"] == "STU101"

    # 2. Student is FORBIDDEN from accessing Admin endpoints (403 Forbidden)
    r = client.get("/api/admin/complaints", headers={"Authorization": f"Bearer {stu_token}"})
    assert r.status_code == 403, f"Expected 403 Forbidden for student on admin endpoint, got {r.status_code}"

    r = client.get("/api/admin/dataset/summary", headers={"Authorization": f"Bearer {stu_token}"})
    assert r.status_code == 403

    r = client.post("/api/admin/dataset/reset", headers={"Authorization": f"Bearer {stu_token}"})
    assert r.status_code == 403

    # 3. Student files a new complaint
    sub_payload = {
        "facility_type": "Water Cooler",
        "location": "Block C (Science & Labs)",
        "description": "Student reported water cooler is leaking continuously on corridor tile floor."
    }
    r = client.post("/api/student/complaints/submit", headers={"Authorization": f"Bearer {stu_token}"}, json=sub_payload)
    assert r.status_code == 200
    sub_res = r.json()
    assert sub_res["success"] is True
    assert "ticket_number" in sub_res
    new_ticket_id = sub_res["ticket_number"]

    # 4. Student can view the details of their own ticket
    r = client.get(f"/api/student/complaints/{new_ticket_id}", headers={"Authorization": f"Bearer {stu_token}"})
    assert r.status_code == 200
    assert r.json()["complaint_id"] == new_ticket_id
    print(f" -> Student Privacy Isolation & Filing Verified! (Filed: {new_ticket_id})")

def test_admin_portal_dataset_and_operations(adm_token):
    print("[TEST 8/8] Testing Admin Master Complaints & Dataset Management...")
    # 1. Admin accesses all 5,500 complaints
    r = client.get("/api/admin/complaints?limit=10", headers={"Authorization": f"Bearer {adm_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 5500, f"Expected >= 5500 complaints, got {data['total']}"
    assert len(data["records"]) == 10

    # 2. Admin inspects Dataset Summary
    r = client.get("/api/admin/dataset/summary", headers={"Authorization": f"Bearer {adm_token}"})
    assert r.status_code == 200
    summary = r.json()
    assert summary["total_records"] >= 5500
    assert summary["total_columns"] >= 20
    assert "preview_rows" in summary
    assert len(summary["preview_rows"]) >= 10

    # 3. Admin updates a complaint
    first_ticket_id = data["records"][0]["complaint_id"]
    r = client.patch(
        f"/api/admin/complaints/{first_ticket_id}",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"status": "In Progress", "department": "Plumbing", "technician_assigned": "Ramesh (Plumbing)"}
    )
    assert r.status_code == 200
    assert r.json()["record"]["status"] == "In Progress"

    # 4. Admin schema validation rejects invalid CSV
    bad_csv = "random_col1,random_col2\n1,2\n3,4"
    r = client.post(
        "/api/admin/dataset/upload",
        headers={"Authorization": f"Bearer {adm_token}", "Content-Type": "application/json"},
        json={"csv_content": bad_csv}
    )
    assert r.status_code == 422, f"Expected 422 for missing required columns, got {r.status_code}"
    assert "missing_columns" in r.json()["detail"]

    # 5. Admin exports CSV
    r = client.get("/api/admin/dataset/export", headers={"Authorization": f"Bearer {adm_token}"})
    assert r.status_code == 200
    assert "complaint_id" in r.text

    # 6. Admin user directory
    r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {adm_token}"})
    assert r.status_code == 200
    users = r.json()["users"]
    assert len(users) >= 3
    print(" -> Admin Operations & Dataset Management Fully Verified!")

if __name__ == "__main__":
    test_nlp_classifier()
    test_severity_model()
    test_priority_engine_math()
    test_shap_game_theoretic_efficiency()
    test_predictive_disclaimer()
    stu_token, adm_token = test_authentication_rbac()
    test_student_isolation_and_workflow(stu_token)
    test_admin_portal_dataset_and_operations(adm_token)

    print("\n============================================================")
    print(" ALL 8 RBAC & PLATFORM TEST SUITES PASSED FLAWLESSLY (100%)!")
    print("============================================================\n")
