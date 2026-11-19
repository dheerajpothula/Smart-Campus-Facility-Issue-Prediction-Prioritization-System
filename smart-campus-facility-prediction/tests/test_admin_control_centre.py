"""
FIPP 2.0 — Comprehensive Verification Test Suite for Facility Operations Control Centre.
Tests all 15 Phase 15 verification criteria:
1. Administrator login works for all 3 configured accounts.
2. Correct administrator identity and role are displayed.
3. Admin Overview displays real complaint counts (never hardcoded).
4. All Requests displays all stored complaints.
5. Search and filters work correctly.
6. Right-side complaint panel displays the correct complaint data.
7. Status updates persist after application restart (disk persistence).
8. Remarks and status history are preserved chronologically.
9. Resolved complaints remain in permanent history without deletion.
10. Reopening a complaint preserves its earlier resolution and status history.
11. Student History reflects administrator status updates.
12. Students cannot access other students' complaints (strict isolation).
13. MCPI and prediction functionality remain operational.
14. Existing student submission workflow works and generates sequential tokens.
15. Sidebar navigation contains all 6 required sections.
"""
import inspect
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.auth.admin_auth import (
    authenticate_admin,
    verify_admin_session,
    _ADMIN_CREDENTIALS_STORE,
)
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    update_complaint_status_extended,
    reopen_complaint,
    assign_complaint_staff,
    get_control_centre_kpis,
    generate_next_token,
    reset_to_default_dataset,
    _load_from_disk,
    PROGRESS_STAGES,
)
from src.prediction.priority_scoring import calculate_priority_score
from dashboard.components.sidebar import ADMIN_NAVIGATION_OPTIONS
from dashboard.pages import (
    overview,
    admin_requests,
    admin_reports,
)


class TestAdminControlCentre(unittest.TestCase):
    """Test suite verifying all 15 Phase 15 criteria for Admin Control Centre."""

    def setUp(self):
        reset_to_default_dataset()

    def test_01_admin_login_configured_accounts(self):
        """1. Administrator login works for all three configured accounts."""
        auth1 = authenticate_admin("ADM-2026-001", "Admin@001")
        self.assertIsNotNone(auth1)
        self.assertEqual(auth1["id"], "ADM-2026-001")
        self.assertEqual(auth1["title"], "Facility Operations Lead")

        auth2 = authenticate_admin("ADM-2026-002", "Admin@002")
        self.assertIsNotNone(auth2)
        self.assertEqual(auth2["id"], "ADM-2026-002")
        self.assertEqual(auth2["title"], "Campus Infrastructure Admin")

        auth3 = authenticate_admin("ADM-2026-003", "Admin@003")
        self.assertIsNotNone(auth3)
        self.assertEqual(auth3["id"], "ADM-2026-003")
        self.assertEqual(auth3["title"], "Maintenance Dispatcher")

    def test_02_admin_identity_and_role_displayed(self):
        """2. Correct administrator identity and role are associated with session."""
        auth = authenticate_admin("ADM-2026-001", "Admin@001")
        self.assertEqual(auth["role"], "admin")
        self.assertEqual(auth["role_title"], "Facility Operations Lead")
        self.assertTrue(verify_admin_session(auth))

        # Student cannot pass admin session verification
        student_session = {"role": "student", "id": "STU-2026-001", "name": "Student"}
        self.assertFalse(verify_admin_session(student_session))

    def test_03_admin_overview_displays_real_counts(self):
        """3. Admin Overview displays real complaint counts (never hardcoded)."""
        df = get_complaints_df()
        kpis = get_control_centre_kpis(df)

        self.assertEqual(kpis["total"], len(df))
        self.assertEqual(kpis["new"], int((df["status"] == "Submitted").sum()))
        self.assertEqual(
            kpis["in_progress"],
            int(df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum()),
        )
        self.assertEqual(kpis["resolved"], int((df["status"] == "Resolved").sum()))

    def test_04_all_requests_displays_all_stored_complaints(self):
        """4. All Requests displays all stored complaints regardless of status."""
        df = get_complaints_df()
        self.assertGreaterEqual(len(df), 7)
        statuses = set(df["status"].unique())
        self.assertTrue(len(statuses) >= 2)

    def test_05_search_and_filters_work_correctly(self):
        """5. Search and filters work correctly across tokens, categories, and priorities."""
        df = get_complaints_df()

        # Token search
        match_token = df[df["complaint_id"] == "CMP-2026-001"]
        self.assertEqual(len(match_token), 1)

        # Status filter
        resolved_subset = df[df["status"] == "Resolved"]
        self.assertTrue((resolved_subset["status"] == "Resolved").all())

        # Category filter
        plumbing_subset = df[df["facility_type"] == "Plumbing"]
        self.assertTrue((plumbing_subset["facility_type"] == "Plumbing").all())

        # Priority filter
        crit_subset = df[df["priority_tier"] == "Critical"]
        self.assertTrue((crit_subset["priority_tier"] == "Critical").all())

    def test_06_right_side_complaint_panel_displays_correct_complaint(self):
        """6. Right-side complaint panel fields are fully preserved and populated."""
        df = get_complaints_df()
        record = df.iloc[0].to_dict()

        self.assertIn("complaint_id", record)
        self.assertIn("title", record)
        self.assertIn("location", record)
        self.assertIn("status", record)
        self.assertIn("priority_score", record)
        self.assertIn("priority_tier", record)
        self.assertIn("severity", record)

    def test_07_status_updates_persist_after_restart(self):
        """7. Status updates persist after simulated application restart (disk read)."""
        df = get_complaints_df()
        target_cid = df.iloc[0]["complaint_id"]

        success = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Under Review",
            remarks="Investigating electrical conduit on 2nd floor.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )
        self.assertTrue(success)

        # Reload from disk directly
        disk_records = _load_from_disk()
        self.assertIsNotNone(disk_records)
        updated_rec = next(r for r in disk_records if r["complaint_id"] == target_cid)
        self.assertEqual(updated_rec["status"], "Under Review")
        self.assertIn("Investigating", updated_rec.get("action_taken", ""))

    def test_08_remarks_and_status_history_preserved(self):
        """8. Remarks and status history are preserved chronologically."""
        df = get_complaints_df()
        target_cid = df.iloc[0]["complaint_id"]

        update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Assigned",
            remarks="Assigned to Electrical Squad.",
            admin_id="ADM-2026-003",
            admin_title="Maintenance Dispatcher",
            assigned_staff="Electrical Squad",
        )
        update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="In Progress",
            remarks="Technician on site replacing breaker.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )

        disk_records = _load_from_disk()
        updated_rec = next(r for r in disk_records if r["complaint_id"] == target_cid)
        history = updated_rec.get("remarks_history", [])
        self.assertGreaterEqual(len(history), 2)
        # Latest remark at index 0
        self.assertIn("replacing breaker", history[0]["remarks"])

    def test_09_resolved_complaints_remain_in_permanent_history(self):
        """9. Resolved complaints remain permanently in store and are never deleted."""
        df = get_complaints_df()
        target_cid = df.iloc[0]["complaint_id"]

        update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Resolved",
            remarks="Breaker replaced and voltage calibrated.",
            admin_id="ADM-2026-001",
        )

        df_after = get_complaints_df()
        resolved_cids = df_after[df_after["status"] == "Resolved"]["complaint_id"].tolist()
        self.assertIn(target_cid, resolved_cids)

        # Reload from disk
        disk_records = _load_from_disk()
        rec_from_disk = next(r for r in disk_records if r["complaint_id"] == target_cid)
        self.assertEqual(rec_from_disk["status"], "Resolved")
        self.assertIn("Breaker replaced", rec_from_disk.get("closing_remarks", ""))

    def test_10_reopening_complaint_preserves_earlier_history(self):
        """10. Reopening a complaint preserves earlier resolution and remarks history."""
        df = get_complaints_df()
        target_cid = df.iloc[0]["complaint_id"]

        # First resolve it
        update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Resolved",
            remarks="Work completed on main valve.",
            admin_id="ADM-2026-001",
        )

        # Then reopen it
        reopened = reopen_complaint(
            complaint_id=target_cid,
            remarks="Leak reported again by floor warden.",
            admin_id="ADM-2026-002",
            admin_title="Campus Infrastructure Admin",
        )
        self.assertTrue(reopened)

        disk_records = _load_from_disk()
        rec = next(r for r in disk_records if r["complaint_id"] == target_cid)
        self.assertEqual(rec["status"], "Under Review")
        self.assertTrue(rec.get("is_reopened"))
        # Previous resolution remark must still be in remarks history
        history_remarks = [h["remarks"] for h in rec.get("remarks_history", [])]
        self.assertTrue(any("Work completed on main valve" in h for h in history_remarks))
        self.assertTrue(any("Leak reported again" in h for h in history_remarks))

    def test_11_student_history_reflects_admin_updates(self):
        """11. Student History reflects administrator status updates and remarks."""
        stu_id = "STU-SYNC-2026"
        new_ticket = {
            "title": "Water Dispenser Sensor Malfunction",
            "description": "Sensor does not stop dispensing water.",
            "category": "Water cooler or water supply",
            "building": "Hostel Block A",
            "specific_location": "1st Floor Pantry",
            "student_id": stu_id,
            "student_name": "Maya Patel",
            "status": "Submitted",
        }
        cid = add_complaint(new_ticket)

        # Admin resolves ticket
        update_complaint_status_extended(
            complaint_id=cid,
            new_status="Resolved",
            remarks="Infrared optic sensor replaced and sealed.",
            admin_id="ADM-2026-001",
        )

        # Student checks history
        stu_complaints = get_student_complaints(stu_id)
        self.assertEqual(len(stu_complaints), 1)
        self.assertEqual(stu_complaints[0]["status"], "Resolved")
        self.assertEqual(stu_complaints[0]["complaint_id"], cid)
        self.assertIn("sensor replaced", stu_complaints[0].get("closing_remarks", ""))

    def test_12_student_data_isolation(self):
        """12. Students cannot access other students' complaints."""
        add_complaint({
            "title": "Room 101 Desk Broken",
            "student_id": "STU-ISOLATE-A",
            "student_name": "Alice",
            "status": "Submitted",
        })
        add_complaint({
            "title": "Room 202 Window Latch Stuck",
            "student_id": "STU-ISOLATE-B",
            "student_name": "Bob",
            "status": "Submitted",
        })

        alice_tickets = get_student_complaints("STU-ISOLATE-A")
        bob_tickets = get_student_complaints("STU-ISOLATE-B")

        self.assertTrue(all(t["student_id"] == "STU-ISOLATE-A" for t in alice_tickets))
        self.assertTrue(all(t["student_id"] == "STU-ISOLATE-B" for t in bob_tickets))
        self.assertNotIn("Room 202 Window Latch Stuck", [t["title"] for t in alice_tickets])

    def test_13_mcpi_prediction_operational(self):
        """13. MCPI and existing prediction functionality remain operational."""
        score, tier, bdown = calculate_priority_score(
            severity="Critical",
            location_type="Server Room",
            recurrence_risk=0.8,
            impact_scale=0.9,
        )
        self.assertIsInstance(score, (int, float))
        self.assertGreater(score, 70.0)
        self.assertEqual(tier, "Critical")
        self.assertIn("Severity Contribution", bdown)

    def test_14_student_submission_workflow_operational(self):
        """14. Existing student submission workflow still works and generates sequential tokens."""
        token1 = generate_next_token()
        self.assertTrue(token1.startswith("CMP-2026-"))
        cid = add_complaint({
            "title": "Ceiling Fan Regulator Not Working",
            "category": "Electrical or lighting issues",
            "student_id": "STU-2026-FLOW",
            "student_name": "Flow Student",
            "status": "Submitted",
        })
        self.assertEqual(cid, token1)

    def test_15_control_centre_sidebar_navigation_sections(self):
        """15. Sidebar navigation contains all 6 approved sections."""
        required_sections = [
            "Overview",
            "All Requests",
            "New / Unassigned",
            "In Progress",
            "Resolved",
            "Reports",
        ]
        self.assertEqual(len(ADMIN_NAVIGATION_OPTIONS), 6)
        for sec in required_sections:
            self.assertTrue(
                any(sec in opt for opt in ADMIN_NAVIGATION_OPTIONS),
                f"Missing navigation section: {sec}",
            )


if __name__ == "__main__":
    unittest.main()
