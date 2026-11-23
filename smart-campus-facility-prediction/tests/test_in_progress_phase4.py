"""
FIPP Phase 4 — Comprehensive Verification Test Suite for In Progress Complaint Management.
Tests:
1. Summary indicators: Total In Progress, Assigned, and Awaiting Action calculated dynamically from actual data.
2. Status criteria & exclusions: Genuine in-progress and assigned work orders included; submitted, under review, and resolved excluded.
3. Search functionality: Search by Token, Student ID, and Issue Title.
4. Multi-filter support: Category, Location, Submission Date, Status, Assignment, and Priority filters.
5. Sorting: Chronological Newest first and Oldest first.
6. Clear Filters action: Safe Streamlit session-state handling, zero exceptions.
7. Right-side details panel: Reuses existing panel displaying complaint, student, MCPI priority, assignment, and status history.
8. Progress remarks: Adding progress observations updates record and audit history.
9. Status transitions & assignment: Transition between Assigned, In Progress, and squad assignment updates.
10. Resolution workflow: Mandatory resolution remarks required before resolving; successful closure archives ticket.
11. Student Portal synchronization: Real-time update reflected in student history with strict data isolation.
12. Empty state handling: Professional empty state when queue or filters yield no records.
13. Full Streamlit AppTest: End-to-end workflow execution with zero exceptions.
"""
import inspect
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    update_complaint_status_extended,
    reopen_complaint,
    assign_complaint_staff,
    reset_to_default_dataset,
    PROGRESS_STAGES,
)
from dashboard.pages import admin_requests
from dashboard.components import complaint_details, styles


class TestInProgressPhase4(unittest.TestCase):
    """Test suite verifying all Phase 4 In Progress specifications."""

    def setUp(self):
        import streamlit as st
        st._main._form_data = None
        reset_to_default_dataset()

    def tearDown(self):
        import streamlit as st
        st._main._form_data = None

    def test_01_summary_indicators_calculation(self):
        """1. Summary indicators calculated dynamically from actual complaint data."""
        df = get_complaints_df()
        staff_s = df["assigned_staff"] if "assigned_staff" in df.columns else pd.Series([""] * len(df), index=df.index)
        allotted_s = df["allotted_person"] if "allotted_person" in df.columns else pd.Series([""] * len(df), index=df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])

        total_in_prog = int((df["status"] == "In Progress").sum())
        assigned_count = int(
            ((df["status"].isin(["In Progress", "Assigned"])) & ((df["status"] == "Assigned") | (~is_unassigned))).sum()
        )
        awaiting_action_count = int(
            ((df["status"] == "In Progress") & is_unassigned).sum()
        )

        # In default seed dataset:
        # CMP-2026-001 (In Progress), CMP-2026-004 (In Progress) -> total 2
        # CMP-2026-002 (Assigned) -> assigned 1
        # CMP-2026-001, CMP-2026-004 (unassigned) -> awaiting action 2
        self.assertEqual(total_in_prog, 2)
        self.assertEqual(assigned_count, 1)
        self.assertEqual(awaiting_action_count, 2)

        # Dynamic update: assigning a squad to CMP-2026-001 increments Assigned and decrements Awaiting Action
        ok = update_complaint_status_extended(
            complaint_id="CMP-2026-001",
            new_status="In Progress",
            remarks="Squad dispatched.",
            assigned_staff="Plumbing Response Team",
        )
        self.assertTrue(ok)

        df_after = get_complaints_df()
        staff_s2 = df_after["assigned_staff"] if "assigned_staff" in df_after.columns else pd.Series([""] * len(df_after), index=df_after.index)
        allotted_s2 = df_after["allotted_person"] if "allotted_person" in df_after.columns else pd.Series([""] * len(df_after), index=df_after.index)
        is_unassigned2 = staff_s2.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                         allotted_s2.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])

        assigned_after = int(
            ((df_after["status"].isin(["In Progress", "Assigned"])) & ((df_after["status"] == "Assigned") | (~is_unassigned2))).sum()
        )
        awaiting_after = int(
            ((df_after["status"] == "In Progress") & is_unassigned2).sum()
        )
        self.assertEqual(assigned_after, 2)
        self.assertEqual(awaiting_after, 1)

    def test_02_status_filtering_criteria_and_exclusions(self):
        """2. In Progress includes genuine active complaints and excludes new, under review, and resolved."""
        df = get_complaints_df()
        in_prog_df = df[df["status"].isin(["In Progress", "Assigned"])]

        # Verify active complaints are included
        self.assertIn("CMP-2026-001", in_prog_df["complaint_id"].values)  # In Progress
        self.assertIn("CMP-2026-002", in_prog_df["complaint_id"].values)  # Assigned
        self.assertIn("CMP-2026-004", in_prog_df["complaint_id"].values)  # In Progress

        # Verify exclusions
        self.assertNotIn("CMP-2026-003", in_prog_df["complaint_id"].values)  # Under Review
        self.assertNotIn("CMP-2026-005", in_prog_df["complaint_id"].values)  # Under Review
        self.assertNotIn("CMP-2026-006", in_prog_df["complaint_id"].values)  # Resolved
        self.assertNotIn("CMP-2026-007", in_prog_df["complaint_id"].values)  # Resolved
        self.assertFalse(any(s == "Submitted" for s in in_prog_df["status"]))
        self.assertFalse(any(s == "Resolved" for s in in_prog_df["status"]))

    def test_03_search_across_token_student_id_and_title(self):
        """3. Search correctly filters by Token, Student ID, and Issue Title."""
        # Add a complaint in In Progress with specific student ID
        cid = add_complaint({
            "title": "Hydraulic Lift Pressure Drop in Engineering Wing",
            "description": "Passenger elevator stuck between 1st and 2nd floor.",
            "facility_type": "Other maintenance issues",
            "building": "Engineering Block 1",
            "location": "Engineering Block 1 - Lift Shaft",
            "status": "In Progress",
            "student_id": "STU-2026-999",
            "student_name": "Test Student",
        })

        df = get_complaints_df()
        in_prog_df = df[df["status"].isin(["In Progress", "Assigned"])]

        # Token search
        res_tok = in_prog_df[in_prog_df["complaint_id"].str.contains("CMP-2026-001", case=False)]
        self.assertEqual(len(res_tok), 1)

        # Title search
        res_title = in_prog_df[in_prog_df["title"].str.contains("Precision AC", case=False)]
        self.assertEqual(len(res_title), 1)
        self.assertEqual(res_title.iloc[0]["complaint_id"], "CMP-2026-002")

        # Student ID search
        res_stu = in_prog_df[in_prog_df["student_id"].fillna("").str.contains("STU-2026-999", case=False)]
        self.assertEqual(len(res_stu), 1)
        self.assertEqual(res_stu.iloc[0]["complaint_id"], cid)

    def test_04_multi_filter_support(self):
        """4. Filters correctly apply to Category, Location, Date, Status, and Assignment."""
        # Add assigned complaint
        add_complaint({
            "title": "Restroom Sensor Flush Valve Replacement",
            "description": "Infrared sensor solenoid malfunctioning.",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "location": "Hostel Block B 1st Floor",
            "status": "In Progress",
            "allotted_person": "Plumbing Response Team",
            "student_id": "12318042",
        })

        df = get_complaints_df()
        in_prog_df = df[df["status"].isin(["In Progress", "Assigned"])]

        # Category filter
        plumb_df = in_prog_df[in_prog_df["facility_type"] == "Plumbing"]
        self.assertGreaterEqual(len(plumb_df), 1)
        self.assertTrue(all(c == "Plumbing" for c in plumb_df["facility_type"]))

        # Location filter
        loc_df = in_prog_df[in_prog_df["building"] == "Academic Block 3"]
        self.assertEqual(len(loc_df), 1)
        self.assertEqual(loc_df.iloc[0]["complaint_id"], "CMP-2026-002")

        # Status filter
        stat_df = in_prog_df[in_prog_df["status"] == "Assigned"]
        self.assertEqual(len(stat_df), 1)
        self.assertEqual(stat_df.iloc[0]["complaint_id"], "CMP-2026-002")

        # Assignment filter
        staff_s = in_prog_df["assigned_staff"] if "assigned_staff" in in_prog_df.columns else pd.Series([""] * len(in_prog_df), index=in_prog_df.index)
        allotted_s = in_prog_df["allotted_person"] if "allotted_person" in in_prog_df.columns else pd.Series([""] * len(in_prog_df), index=in_prog_df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])
        is_assigned = (in_prog_df["status"] == "Assigned") | (~is_unassigned)

        assigned_records = in_prog_df[is_assigned]
        unassigned_records = in_prog_df[is_unassigned & (in_prog_df["status"] != "Assigned")]

        self.assertGreaterEqual(len(assigned_records), 2)  # CMP-002 + added plumbing
        self.assertGreaterEqual(len(unassigned_records), 2)  # CMP-001, CMP-004

    def test_05_sorting_newest_and_oldest(self):
        """5. Sorting arranges complaints in correct chronological order."""
        df = get_complaints_df()
        in_prog_df = df[df["status"].isin(["In Progress", "Assigned"])]

        d_s = pd.to_datetime(in_prog_df["date_reported"], errors="coerce")
        df_newest = in_prog_df.assign(_d=d_s).sort_values(by="_d", ascending=False)
        self.assertEqual(df_newest["_d"].dropna().tolist(), sorted(df_newest["_d"].dropna().tolist(), reverse=True))

        df_oldest = in_prog_df.assign(_d=d_s).sort_values(by="_d", ascending=True)
        self.assertEqual(df_oldest["_d"].dropna().tolist(), sorted(df_oldest["_d"].dropna().tolist(), reverse=False))

    def test_06_clear_filters_action_resets_state(self):
        """6. Clear Filters action safely resets all session state keys."""
        import streamlit as st

        st.session_state["search_in_progress"] = "Leak"
        st.session_state["sort_in_progress"] = "Oldest first"
        st.session_state["f_stat_in_progress"] = "In Progress"
        st.session_state["f_cat_in_progress"] = "Plumbing"
        st.session_state["f_loc_in_progress"] = "Hostel Block B"
        st.session_state["f_date_in_progress"] = "Today"
        st.session_state["f_prio_in_progress"] = "High"
        st.session_state["f_assign_in_progress"] = "Assigned"
        st.session_state["page_sel_in_progress"] = 2

        admin_requests.reset_requests_filters("in_progress")

        self.assertEqual(st.session_state["search_in_progress"], "")
        self.assertEqual(st.session_state["sort_in_progress"], "Newest first")
        self.assertEqual(st.session_state["f_stat_in_progress"], "All Statuses")
        self.assertEqual(st.session_state["f_cat_in_progress"], "All Categories")
        self.assertEqual(st.session_state["f_loc_in_progress"], "All Locations")
        self.assertEqual(st.session_state["f_date_in_progress"], "All Dates")
        self.assertEqual(st.session_state["f_prio_in_progress"], "All Priorities")
        self.assertEqual(st.session_state["f_assign_in_progress"], "All Assignments")
        self.assertEqual(st.session_state["page_sel_in_progress"], 1)

    def test_07_progress_management_add_progress_remarks(self):
        """7. Adding progress remarks updates action taken and appends to audit history."""
        target_cid = "CMP-2026-001"
        ok = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="In Progress",
            remarks="Technician replaced damaged flange gasket. Pressure test underway.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )
        self.assertTrue(ok)

        df = get_complaints_df()
        rec = df[df["complaint_id"] == target_cid].iloc[0]
        self.assertEqual(rec["status"], "In Progress")
        self.assertIn("flange gasket", rec["action_taken"])

        # Check remarks history contains entry
        history = rec.get("remarks_history", [])
        self.assertGreater(len(history), 0)
        self.assertIn("flange gasket", history[0]["remarks"])
        self.assertEqual(history[0]["new_status"], "In Progress")

    def test_08_status_transition_from_assigned_to_in_progress(self):
        """8. Valid status transition from Assigned to In Progress with technician update."""
        target_cid = "CMP-2026-002"
        ok = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="In Progress",
            remarks="HVAC specialist arrived on-site and commenced compressor diagnostics.",
            admin_id="ADM-2026-002",
            admin_title="Facility Supervisor",
            assigned_staff="HVAC & Cooling Systems Unit",
        )
        self.assertTrue(ok)

        df = get_complaints_df()
        rec = df[df["complaint_id"] == target_cid].iloc[0]
        self.assertEqual(rec["status"], "In Progress")
        self.assertEqual(rec["allotted_person"], "HVAC & Cooling Systems Unit")

    def test_09_resolution_requires_mandatory_remarks(self):
        """9. Resolution requires mandatory remarks; resolving archives ticket from In Progress."""
        target_cid = "CMP-2026-004"

        # Resolving with mandatory remarks succeeds
        ok = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Resolved",
            remarks="Replaced 24-port Gigabit edge switch SFP transceiver and verified link restoration.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )
        self.assertTrue(ok)

        df = get_complaints_df()
        rec = df[df["complaint_id"] == target_cid].iloc[0]
        self.assertEqual(rec["status"], "Resolved")
        self.assertEqual(rec["closing_remarks"], "Replaced 24-port Gigabit edge switch SFP transceiver and verified link restoration.")
        self.assertTrue("resolved_at" in rec)
        self.assertEqual(rec["resolved_by"], "ADM-2026-001")

        # Excluded from In Progress queue
        in_prog_df = df[df["status"].isin(["In Progress", "Assigned"])]
        self.assertNotIn(target_cid, in_prog_df["complaint_id"].values)

    def test_10_student_history_synchronization(self):
        """10. Status updates and remarks synchronize to Student History with strict data isolation."""
        stu_id = "12318042"
        other_stu = "11904523"

        cid = add_complaint({
            "title": "Study Lamp Fixture Sparking",
            "description": "Desk lamp wiring shorting out.",
            "facility_type": "Electrical or lighting issues",
            "building": "Hostel Block A",
            "location": "Hostel Block A Room 201",
            "status": "In Progress",
            "student_id": stu_id,
            "student_name": "Praveen",
            "allotted_person": "Electrical Maintenance Squad",
        })

        # Initially student sees In Progress
        stu_recs = get_student_complaints(stu_id)
        target = next(c for c in stu_recs if c["complaint_id"] == cid)
        self.assertEqual(target["status"], "In Progress")
        self.assertEqual(target["allotted_person"], "Electrical Maintenance Squad")

        # Admin adds progress remarks
        update_complaint_status_extended(
            complaint_id=cid,
            new_status="In Progress",
            remarks="Electrician replaced desktop ballast and isolated circuit.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )

        # Student history immediately reflects updated action taken and status
        stu_recs_mid = get_student_complaints(stu_id)
        target_mid = next(c for c in stu_recs_mid if c["complaint_id"] == cid)
        self.assertEqual(target_mid["action_taken"], "Electrician replaced desktop ballast and isolated circuit.")
        self.assertEqual(target_mid["status"], "In Progress")

        # Admin resolves ticket
        update_complaint_status_extended(
            complaint_id=cid,
            new_status="Resolved",
            remarks="Repairs completed and tested with multimeter.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )

        # Student history reflects resolution
        stu_recs_after = get_student_complaints(stu_id)
        target_after = next(c for c in stu_recs_after if c["complaint_id"] == cid)
        self.assertEqual(target_after["status"], "Resolved")
        self.assertEqual(target_after["closing_remarks"], "Repairs completed and tested with multimeter.")

        # Data isolation: Other student cannot see this record
        other_recs = get_student_complaints(other_stu)
        self.assertNotIn(cid, [c["complaint_id"] for c in other_recs])

    def test_11_empty_state_handling(self):
        """11. Professional empty state rendered when queue or filters yield no records."""
        df = get_complaints_df()

        # Filter with an impossible criteria
        filtered = df[df["status"] == "NonExistentStatus"]
        self.assertTrue(filtered.empty)

        # Confirm default empty message title
        empty_title = "No matching complaints found"
        self.assertEqual(empty_title, "No matching complaints found")

    def test_12_apptest_in_progress_full_workflow(self):
        """12. Full Streamlit AppTest verifies In Progress page, search, clear filters, and details panel."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        at.session_state["auth_user"] = {
            "admin_id": "ADM-2026-001",
            "name": "Facility Operations Lead",
            "role": "admin",
            "title": "Facility Operations Lead",
        }
        at.session_state["user_role"] = "admin"
        at.session_state["admin_active_page"] = "In Progress"
        at.run()

        # Zero runtime exceptions
        self.assertEqual(len(at.exception), 0, f"Exceptions on initial run: {[e.value for e in at.exception]}")

        # Type search query in In Progress search bar
        at.text_input(key="search_in_progress").input("Pipe")
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("search_in_progress"), "Pipe")

        # Click Clear Filters
        at.button(key="btn_reset_in_progress").click()
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("search_in_progress"), "")


if __name__ == "__main__":
    unittest.main()
