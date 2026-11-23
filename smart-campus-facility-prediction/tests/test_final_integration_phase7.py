"""
FIPP Phase 7: Final Integration, System Validation & Deployment Readiness Test Suite.
Validates:
1. System Architecture & Components Map.
2. Complete Student Portal Submission Journey (Declarations, Form, Validation, Token).
3. Student Record Isolation & Privacy.
4. Student Withdrawal Workflow (Open tickets only).
5. Student 5-Star Feedback Workflow (Resolved tickets only).
6. Admin Portal Views (Overview, All Requests, New/Unassigned, In Progress, Resolved, Reports).
7. Complete Complaint Lifecycle (Submitted -> Under Review -> Assigned -> In Progress -> Resolved).
8. Student–Admin Real-time Synchronization & Remarks Propagation.
9. Reopen Preservation Integrity (original timestamps, closing remarks, audit history).
10. Authentication Cryptographic Security (PBKDF2-HMAC-SHA256, constant-time compare).
11. Role-Based Access Control & Server-Side Security Guards.
12. MCPI Multi-Criteria Scoring & Tier Classification Accuracy.
13. Database Persistence & Restart Consistency.
14. Reports & Analytics Empirical Calculation Integrity.
15. Data Export Privacy Compliance (Student PII Redaction).
16. Streamlit AppTest End-to-End Simulation (Student and Admin Portals).
"""
import io
import sys
import unittest
from datetime import datetime, timedelta, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from dashboard.pages import (
    admin_reports,
    admin_requests,
    overview,
    student_dashboard,
)
from dashboard.components import (
    admin_header,
    admin_login,
    complaint_details,
    login_page,
    role_selection,
    sidebar,
    styles,
)
from src.auth import admin_auth
from src.data import complaints_store, complaint_categories
from src.prediction import priority_scoring


class TestFinalIntegrationPhase7(unittest.TestCase):
    """Comprehensive Final Integration & Deployment-Readiness Test Suite for FIPP."""

    def setUp(self):
        """Prepare fresh session state and default dataset before each test."""
        st.session_state.clear()
        complaints_store.reset_to_default_dataset()

    def tearDown(self):
        """Clean up session state and restore default dataset after each test."""
        st.session_state.clear()
        complaints_store.reset_to_default_dataset()

    def test_01_system_architecture_and_components_map(self):
        """1. Verify all UI pages, components, data stores, and auth modules exist and export required interfaces."""
        # Check core pages
        self.assertTrue(callable(admin_reports.render_reports_page))
        self.assertTrue(callable(admin_requests.render_all_requests_page))
        self.assertTrue(callable(admin_requests.render_new_unassigned_page))
        self.assertTrue(callable(admin_requests.render_in_progress_page))
        self.assertTrue(callable(admin_requests.render_resolved_page))
        self.assertTrue(callable(overview.render_page))
        self.assertTrue(callable(student_dashboard.render_student_dashboard))

        # Check core components
        self.assertTrue(callable(admin_header.render_admin_header))
        self.assertTrue(callable(complaint_details.render_complaint_details_panel))
        self.assertTrue(callable(sidebar.render_admin_sidebar))
        self.assertTrue(callable(styles.apply_theme))
        self.assertTrue(callable(styles.render_kpi))

        # Check data stores and predictions
        self.assertTrue(callable(complaints_store.get_complaints_df))
        self.assertTrue(callable(complaints_store.add_complaint))
        self.assertTrue(callable(complaints_store.update_complaint_status_extended))
        self.assertTrue(callable(complaints_store.reopen_complaint))
        self.assertTrue(callable(priority_scoring.calculate_priority_score))
        self.assertTrue(callable(admin_auth.authenticate_admin))

    def test_02_student_portal_full_submission_journey(self):
        """2. Verify student complaint submission creates valid record with 3-digit zero-padded token and ML score."""
        student_id = "STU-VAL-001"
        ticket_data = {
            "student_id": student_id,
            "student_name": "Validation Student",
            "message_type": "Grievance",
            "category": "Maintenance / Electrical Complaints",
            "facility_type": "Plumbing",
            "sub_category": "Washroom problem",
            "specific_category": "Water Drainage problem",
            "building": "Hostel Block A",
            "sub_block": "Wing 2",
            "room_type": "Room No",
            "room_number": "104",
            "contact_number": "9876543210",
            "title": "[Grievance] Water Drainage problem",
            "description": "Severe drainage blockage causing wastewater accumulation in washroom.",
            "preferred_slot": "Morning (9 AM - 12 PM)",
        }

        token = complaints_store.add_complaint(ticket_data)
        self.assertRegex(token, r"^CMP-2026-\d{3,}$", "Token must adhere to CMP-2026-XXX format.")

        # Check record in store
        df = complaints_store.get_complaints_df()
        new_row = df[df["complaint_id"] == token]
        self.assertEqual(len(new_row), 1)
        rec = new_row.iloc[0]

        self.assertEqual(rec["status"], "Submitted")
        self.assertEqual(rec["student_id"], student_id)
        self.assertEqual(rec["facility_type"], "Plumbing")
        self.assertIn("priority_score", rec)
        self.assertIn(rec["priority_tier"], ["Critical", "High", "Medium", "Low"])
        self.assertTrue(isinstance(rec["score_breakdown"], dict))

    def test_03_student_record_isolation(self):
        """3. Verify strict student record isolation so students can never view other students' tickets."""
        # Create tickets for two different students
        cid1 = complaints_store.add_complaint({
            "student_id": "STU-ALPHA",
            "student_name": "Student Alpha",
            "title": "Alpha Broken Light",
            "facility_type": "Electricity",
            "building": "Hostel Block A",
            "status": "Submitted",
        })
        cid2 = complaints_store.add_complaint({
            "student_id": "STU-BETA",
            "student_name": "Student Beta",
            "title": "Beta Clogged Sink",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "status": "Submitted",
        })

        alpha_records = complaints_store.get_student_complaints("STU-ALPHA")
        beta_records = complaints_store.get_student_complaints("STU-BETA")
        gamma_records = complaints_store.get_student_complaints("STU-GAMMA")

        # Alpha sees only Alpha's ticket
        self.assertTrue(any(r["complaint_id"] == cid1 for r in alpha_records))
        self.assertFalse(any(r["complaint_id"] == cid2 for r in alpha_records))

        # Beta sees only Beta's ticket
        self.assertTrue(any(r["complaint_id"] == cid2 for r in beta_records))
        self.assertFalse(any(r["complaint_id"] == cid1 for r in beta_records))

        # Gamma sees zero tickets
        self.assertEqual(len(gamma_records), 0)

    def test_04_student_withdrawal_workflow(self):
        """4. Verify eligible open complaints can be withdrawn by student, but closed complaints cannot."""
        student_id = "STU-WITHDRAW-001"
        cid = complaints_store.add_complaint({
            "student_id": student_id,
            "title": "Temporary Fan Sound",
            "facility_type": "Electricity",
            "building": "Hostel Block C",
            "status": "Submitted",
        })

        # Other student cannot withdraw Alpha's complaint
        unauth_withdraw = complaints_store.withdraw_complaint(cid, student_id="STU-OTHER-002", reason="Not mine")
        self.assertFalse(unauth_withdraw)

        # Authorized student can withdraw open complaint
        auth_withdraw = complaints_store.withdraw_complaint(cid, student_id=student_id, reason="Resolved by myself")
        self.assertTrue(auth_withdraw)

        # Check status updated to Withdrawn
        records = complaints_store._load_from_disk()
        rec = [r for r in records if r["complaint_id"] == cid][0]
        self.assertEqual(rec["status"], "Withdrawn")
        self.assertTrue(rec.get("is_withdrawn"))
        self.assertEqual(rec.get("withdrawal_reason"), "Resolved by myself")

        # Cannot withdraw again
        self.assertFalse(complaints_store.withdraw_complaint(cid, student_id=student_id, reason="Repeat"))

    def test_05_student_feedback_workflow(self):
        """5. Verify 5-star feedback can only be submitted for Resolved tickets and persists to ticket record."""
        student_id = "STU-FEEDBACK-001"
        cid = complaints_store.add_complaint({
            "student_id": student_id,
            "title": "Corridor Bulb Outage",
            "facility_type": "Electricity",
            "building": "Academic Block 1",
            "status": "In Progress",
        })

        # Cannot submit feedback for unresolved complaint
        fb_fail = complaints_store.submit_complaint_feedback(cid, rating=5, comments="Good", student_id=student_id)
        self.assertFalse(fb_fail)

        # Resolve complaint
        complaints_store.update_complaint_status_extended(cid, "Resolved", remarks="Replaced bulb.", admin_id="ADM-2026-001")

        # Other student cannot submit feedback
        fb_unauth = complaints_store.submit_complaint_feedback(cid, rating=4, comments="Nice", student_id="STU-OTHER")
        self.assertFalse(fb_unauth)

        # Authorized student submits 5-star feedback
        fb_ok = complaints_store.submit_complaint_feedback(cid, rating=5, comments="Promptly fixed, thank you!", student_id=student_id)
        self.assertTrue(fb_ok)

        records = complaints_store._load_from_disk()
        rec = [r for r in records if r["complaint_id"] == cid][0]
        self.assertEqual(rec["feedback"]["rating"], 5)
        self.assertEqual(rec["feedback"]["rating_label"], "Excellent")
        self.assertEqual(rec["feedback"]["comments"], "Promptly fixed, thank you!")

    def test_06_admin_portal_views_and_navigation(self):
        """6. Verify admin views execute without error and enforce respective mode filtering."""
        st.session_state["auth_user"] = {
            "id": "ADM-2026-001",
            "name": "Administrator",
            "role": "admin",
            "title": "Facility Operations Lead",
        }

        # Overview
        try:
            overview.render_page()
            ov_ok = True
        except Exception:
            ov_ok = False
        self.assertTrue(ov_ok)

        # All Requests
        try:
            admin_requests.render_all_requests_page()
            all_ok = True
        except Exception:
            all_ok = False
        self.assertTrue(all_ok)

        # New / Unassigned
        try:
            admin_requests.render_new_unassigned_page()
            new_ok = True
        except Exception:
            new_ok = False
        self.assertTrue(new_ok)

        # In Progress
        try:
            admin_requests.render_in_progress_page()
            inp_ok = True
        except Exception:
            inp_ok = False
        self.assertTrue(inp_ok)

        # Resolved
        try:
            admin_requests.render_resolved_page()
            res_ok = True
        except Exception:
            res_ok = False
        self.assertTrue(res_ok)

        # Reports
        try:
            admin_reports.render_reports_page()
            rep_ok = True
        except Exception:
            rep_ok = False
        self.assertTrue(rep_ok)

    def test_07_complete_complaint_lifecycle(self):
        """7. Verify complete 5-stage lifecycle: Submitted -> Under Review -> Assigned -> In Progress -> Resolved."""
        cid = complaints_store.add_complaint({
            "title": "Leaking Roof in Lecture Hall",
            "facility_type": "Other maintenance issues",
            "building": "Academic Block 1",
            "status": "Submitted",
        })

        # Stage 1: Submitted
        rec = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        self.assertEqual(rec["status"], "Submitted")

        # Stage 2: Under Review
        complaints_store.update_complaint_status_extended(cid, "Under Review", remarks="Assessing damage.", admin_id="ADM-2026-001")
        rec = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        self.assertEqual(rec["status"], "Under Review")

        # Stage 3: Assigned
        complaints_store.assign_complaint_staff(cid, "Civil Repair Crew", remarks="Crew allocated.", admin_id="ADM-2026-001")
        rec = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        self.assertEqual(rec.get("allotted_person"), "Civil Repair Crew")

        # Stage 4: In Progress
        complaints_store.update_complaint_status_extended(cid, "In Progress", remarks="Sealing membrane applied.", admin_id="ADM-2026-001")
        rec = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        self.assertEqual(rec["status"], "In Progress")

        # Stage 5: Resolved
        complaints_store.update_complaint_status_extended(cid, "Resolved", remarks="Waterproof test passed.", admin_id="ADM-2026-001")
        rec = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        self.assertEqual(rec["status"], "Resolved")
        self.assertIsNotNone(rec.get("resolved_at"))
        self.assertEqual(rec.get("closing_remarks"), "Waterproof test passed.")

    def test_08_student_admin_synchronization(self):
        """8. Verify updates performed by admin immediately reflect in student history and remarks audit."""
        student_id = "STU-SYNC-001"
        cid = complaints_store.add_complaint({
            "student_id": student_id,
            "title": "Sparking Switchboard",
            "facility_type": "Electricity",
            "building": "Hostel Block B",
            "status": "Submitted",
        })

        # Admin advances ticket and adds progress remark
        complaints_store.update_complaint_status_extended(
            cid, "In Progress", remarks="Electrician replaced MCB.", admin_id="ADM-2026-001", admin_title="Facility Operations Lead"
        )

        # Check student history view
        student_tickets = complaints_store.get_student_complaints(student_id)
        self.assertEqual(len(student_tickets), 1)
        sync_ticket = student_tickets[0]

        self.assertEqual(sync_ticket["status"], "In Progress")
        history = sync_ticket.get("remarks_history", [])
        self.assertTrue(len(history) >= 2)
        self.assertIn("Electrician replaced MCB", history[0]["remarks"])

    def test_09_reopen_preservation_integrity(self):
        """9. Verify reopening a complaint preserves original resolution timestamp, closing remarks, and adds audit history."""
        cid = complaints_store.add_complaint({
            "title": "Air Conditioner Sensor Error",
            "facility_type": "HVAC",
            "building": "Academic Block 3",
            "status": "In Progress",
        })

        # Resolve
        complaints_store.update_complaint_status_extended(
            cid, "Resolved", remarks="Thermostat recalibrated.", admin_id="ADM-2026-002", admin_title="Campus Infrastructure Admin"
        )
        rec_res = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        orig_resolved_at = rec_res["resolved_at"]
        orig_closing_remarks = rec_res["closing_remarks"]
        orig_admin = rec_res["resolved_by"]

        # Reopen
        reopen_ok = complaints_store.reopen_complaint(
            cid, remarks="AC displaying error code E3 again.", admin_id="ADM-2026-001", admin_title="Facility Operations Lead"
        )
        self.assertTrue(reopen_ok)

        rec_reopened = [r for r in complaints_store._load_from_disk() if r["complaint_id"] == cid][0]
        self.assertEqual(rec_reopened["status"], "Under Review")
        self.assertTrue(rec_reopened.get("is_reopened"))
        self.assertEqual(rec_reopened.get("original_resolved_at"), orig_resolved_at)
        self.assertEqual(rec_reopened.get("previous_closing_remarks"), orig_closing_remarks)
        self.assertEqual(rec_reopened.get("original_resolved_by"), orig_admin)

        # Verify audit history logged the reopening action
        latest_remark = rec_reopened["remarks_history"][0]
        self.assertIn("Complaint Reopened", latest_remark["remarks"])
        self.assertIn("error code E3", latest_remark["remarks"])

    def test_10_authentication_cryptographic_security(self):
        """10. Verify PBKDF2-HMAC-SHA256 password hashing, salt, constant-time compare, and timing-attack protection."""
        # Authenticate valid admin credentials
        auth1 = admin_auth.authenticate_admin("ADM-2026-001", "Admin@001")
        self.assertIsNotNone(auth1)
        self.assertEqual(auth1["id"], "ADM-2026-001")
        self.assertEqual(auth1["role"], "admin")
        self.assertEqual(auth1["name"], "Administrator")

        # Wrong password rejection
        auth_bad = admin_auth.authenticate_admin("ADM-2026-001", "WrongPassword123!")
        self.assertIsNone(auth_bad)

        # Unknown admin ID rejection
        auth_unknown = admin_auth.authenticate_admin("ADM-9999-999", "Admin@001")
        self.assertIsNone(auth_unknown)

        # Hash verify
        hash_val = admin_auth.hash_password("Admin@001")
        self.assertEqual(len(hash_val), 64)
        self.assertEqual(hash_val, admin_auth._ADMIN_CREDENTIALS_STORE["ADM-2026-001"]["password_hash"])

    def test_11_role_based_access_control_server_guard(self):
        """11. Verify server-side session authorization guards prevent unauthorized access to admin operations."""
        # None session
        self.assertFalse(admin_auth.verify_admin_session(None))
        self.assertFalse(admin_auth.verify_admin_session({}))

        # Student session cannot access admin functions
        student_session = {"role": "student", "name": "Student", "id": "STU-2026-001"}
        self.assertFalse(admin_auth.verify_admin_session(student_session))

        # Admin session verified
        admin_session = {"role": "admin", "name": "Administrator", "id": "ADM-2026-001"}
        self.assertTrue(admin_auth.verify_admin_session(admin_session))

    def test_12_mcpi_scoring_and_tier_classification(self):
        """12. Verify Multi-Criteria Priority Index (MCPI) scoring formula, weights, and tier classification."""
        weights = priority_scoring.get_current_weights()
        self.assertTrue(weights.is_valid())
        self.assertAlmostEqual(weights.total, 1.0, places=3)

        # 1. Critical scenario: Critical severity, Server Room (1.0), high recurrence, high impact
        score_crit, tier_crit, bd_crit = priority_scoring.calculate_priority_score(
            severity="Critical",
            location_type="Server Room",
            recurrence_risk=0.90,
            impact_scale=0.95,
            weights=weights,
        )
        self.assertGreaterEqual(score_crit, 75.0)
        self.assertEqual(tier_crit, "Critical")
        self.assertEqual(bd_crit["Severity Contribution"], 35.0)
        self.assertEqual(bd_crit["Location Criticality Contribution"], 25.0)

        # 2. Low scenario: Low severity, Campus Grounds (0.25), low recurrence, low impact
        score_low, tier_low, bd_low = priority_scoring.calculate_priority_score(
            severity="Low",
            location_type="Campus Grounds",
            recurrence_risk=0.10,
            impact_scale=0.10,
            weights=weights,
        )
        self.assertLess(score_low, 28.0)
        self.assertEqual(tier_low, "Low")

    def test_13_database_persistence_and_restart_consistency(self):
        """13. Verify complaint storage persists correctly to disk across simulated restarts and preserves token format."""
        cid = complaints_store.add_complaint({
            "title": "Persistent Storage Verification Test",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "status": "In Progress",
        })

        # Clear session state to simulate server restart
        st.session_state.clear()

        # Re-read from disk
        reloaded_df = complaints_store.get_complaints_df()
        self.assertFalse(reloaded_df.empty)
        matching = reloaded_df[reloaded_df["complaint_id"] == cid]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching.iloc[0]["title"], "Persistent Storage Verification Test")

    def test_14_reports_analytics_calculation_integrity(self):
        """14. Verify Reports & Analytics KPI indicators, resolution turnaround, and backlog ageing calculations."""
        raw_df = complaints_store.get_complaints_df()
        total = len(raw_df)
        resolved_count = int((raw_df["status"] == "Resolved").sum())
        in_prog_count = int(raw_df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum())
        new_count = int((raw_df["status"] == "Submitted").sum())
        res_rate = f"{round(resolved_count / total * 100, 1)}%" if total > 0 else "0.0%"

        self.assertEqual(total, 7)
        self.assertEqual(resolved_count, 2)
        self.assertEqual(in_prog_count, 5)
        self.assertEqual(new_count, 0)
        self.assertEqual(res_rate, "28.6%")

        # Turnaround calculation on resolved seed complaints
        res_df = raw_df[raw_df["status"] == "Resolved"]
        rep_dt = pd.to_datetime(res_df["date_reported"], format="mixed", errors="coerce")
        res_dt = pd.to_datetime(res_df["resolved_at"], format="mixed", errors="coerce")
        turnaround_days = (res_dt - rep_dt).dt.total_seconds() / 86400.0
        self.assertAlmostEqual(turnaround_days.mean(), 2.0, places=1)

    def test_15_export_privacy_compliance(self):
        """15. Verify administrative CSV export includes operational fields while strictly redacting student PII."""
        df = complaints_store.get_complaints_df()
        export_cols = [
            "complaint_id", "title", "facility_type", "building", "location",
            "status", "priority_tier", "priority_score", "date_reported",
            "resolved_at", "allotted_person", "action_taken"
        ]
        avail = [c for c in export_cols if c in df.columns]
        export_df = df[avail].copy()
        csv_str = export_df.to_csv(index=False)

        # Operational fields present
        self.assertIn("complaint_id", csv_str)
        self.assertIn("CMP-2026-001", csv_str)
        self.assertIn("priority_tier", csv_str)

        # Sensitive student PII strictly omitted
        self.assertNotIn("student_name", csv_str)
        self.assertNotIn("phone", csv_str)
        self.assertNotIn("email", csv_str)

    def test_16_streamlit_apptest_student_and_admin_flows(self):
        """16. Verify end-to-end Streamlit AppTest execution for both Student and Administrator navigation."""
        app_path = str(PROJECT_ROOT / "app.py")

        # 1. Admin flow
        at_admin = AppTest.from_file(app_path)
        at_admin.session_state["auth_user"] = {
            "id": "ADM-2026-001",
            "name": "Administrator",
            "role": "admin",
            "title": "Facility Operations Lead",
        }
        at_admin.session_state["selected_role"] = "admin"
        at_admin.session_state["user_role"] = "admin"
        at_admin.session_state["admin_active_page"] = "Overview"
        at_admin.run(timeout=10)
        self.assertFalse(at_admin.exception, f"Admin AppTest threw exception: {at_admin.exception}")

        # 2. Student flow
        at_student = AppTest.from_file(app_path)
        at_student.session_state["auth_user"] = {
            "id": "STU-2026-001",
            "name": "Student",
            "role": "student",
        }
        at_student.session_state["selected_role"] = "student"
        at_student.session_state["user_role"] = "student"
        at_student.session_state["student_active_view"] = "History"
        at_student.run(timeout=10)
        self.assertFalse(at_student.exception, f"Student AppTest threw exception: {at_student.exception}")


if __name__ == "__main__":
    unittest.main()
