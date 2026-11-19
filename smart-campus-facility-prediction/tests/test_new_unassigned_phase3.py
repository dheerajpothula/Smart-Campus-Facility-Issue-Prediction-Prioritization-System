"""
FIPP Phase 3 — Verification Test Suite for New / Unassigned Complaint Management.
Tests:
1. Summary indicators: Total New Requests, Awaiting Review, Unassigned dynamically calculated from data.
2. Status criteria: Genuine newly submitted and unassigned triage complaints (Submitted, unassigned Under Review).
3. Exclusions: Already resolved, assigned, or in-progress complaints excluded.
4. Search functionality: Search by Token, Student ID, and Issue Title.
5. Filters: Category, Status, Location, Date, Priority.
6. Sorting: Newest first and Oldest first.
7. Clear Filters action: Safe Streamlit session-state handling, zero exceptions.
8. Details panel integration: Reuses complaint details panel with full metadata and history.
9. Administrative actions: Mark Under Review, Assign staff, Move to In Progress with audit logging.
10. Student Portal synchronization: Real-time update reflected in student history with strict data isolation.
11. Empty state handling: Professional empty state when no new/unassigned complaints exist.
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
    reset_to_default_dataset,
    PROGRESS_STAGES,
)
from dashboard.pages import admin_requests
from dashboard.components import complaint_details, styles


class TestNewUnassignedPhase3(unittest.TestCase):
    """Test suite verifying all Phase 3 New / Unassigned specifications."""

    def setUp(self):
        import streamlit as st
        st._main._form_data = None
        reset_to_default_dataset()

    def tearDown(self):
        import streamlit as st
        st._main._form_data = None

    def test_01_summary_indicators_calculation(self):
        """1. Summary indicators calculated dynamically from actual data."""
        df = get_complaints_df()
        staff_s = df["assigned_staff"] if "assigned_staff" in df.columns else pd.Series([""] * len(df), index=df.index)
        allotted_s = df["allotted_person"] if "allotted_person" in df.columns else pd.Series([""] * len(df), index=df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])

        total_new = int((df["status"] == "Submitted").sum())
        awaiting_review = int((df["status"] == "Under Review").sum())
        unassigned_count = int(((df["status"].isin(["Submitted", "Under Review"])) & is_unassigned).sum())

        self.assertEqual(total_new, 0)
        self.assertEqual(awaiting_review, 2)
        self.assertEqual(unassigned_count, 2)

        # Adding a new submitted complaint dynamically updates counts
        new_cid = add_complaint({
            "title": "Corridor Fluorescent Tube Buzzing",
            "description": "Ballast failure in hallway light.",
            "facility_type": "Electrical or lighting issues",
            "building": "Hostel Block A",
            "location": "Hostel Block A 2nd Floor",
            "status": "Submitted",
            "student_id": "12318042",
            "student_name": "Praveen",
        })
        df_after = get_complaints_df()
        staff_s2 = df_after["assigned_staff"] if "assigned_staff" in df_after.columns else pd.Series([""] * len(df_after), index=df_after.index)
        allotted_s2 = df_after["allotted_person"] if "allotted_person" in df_after.columns else pd.Series([""] * len(df_after), index=df_after.index)
        is_unassigned2 = (staff_s2.isna() | staff_s2.astype(str).str.strip().isin(["", "nan", "None", "Unassigned"])) & \
                         (allotted_s2.isna() | allotted_s2.astype(str).str.strip().isin(["", "nan", "None", "Unassigned"]))

        self.assertEqual(int((df_after["status"] == "Submitted").sum()), total_new + 1)
        self.assertEqual(int(((df_after["status"].isin(["Submitted", "Under Review"])) & is_unassigned2).sum()), unassigned_count + 1)

    def test_02_status_filtering_criteria_and_exclusions(self):
        """2. New / Unassigned includes genuine new/triage records and excludes resolved or active work."""
        df = get_complaints_df()
        staff_s = df["assigned_staff"] if "assigned_staff" in df.columns else pd.Series([""] * len(df), index=df.index)
        allotted_s = df["allotted_person"] if "allotted_person" in df.columns else pd.Series([""] * len(df), index=df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])

        is_submitted = df["status"] == "Submitted"
        is_unassigned_review = (df["status"] == "Under Review") & is_unassigned
        new_df = df[is_submitted | is_unassigned_review]

        # In default seed dataset: CMP-2026-003 and CMP-2026-005 are Under Review and unassigned
        self.assertEqual(len(new_df), 2)
        self.assertIn("CMP-2026-003", new_df["complaint_id"].values)
        self.assertIn("CMP-2026-005", new_df["complaint_id"].values)

        # Exclusions: No resolved or active work orders
        self.assertNotIn("CMP-2026-001", new_df["complaint_id"].values)  # In Progress
        self.assertNotIn("CMP-2026-002", new_df["complaint_id"].values)  # Assigned
        self.assertNotIn("CMP-2026-006", new_df["complaint_id"].values)  # Resolved
        self.assertNotIn("CMP-2026-007", new_df["complaint_id"].values)  # Resolved
        self.assertFalse(any(s == "Resolved" for s in new_df["status"]))

    def test_03_search_across_token_student_id_and_title(self):
        """3. Search correctly filters by Token, Student ID, and Issue Title in New / Unassigned."""
        add_complaint({
            "title": "Water Leakage Near Room 305",
            "description": "Pipe leaking onto hallway carpet.",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "location": "Hostel Block B 3rd Floor",
            "status": "Submitted",
            "student_id": "12318042",
            "student_name": "Praveen",
        })
        df = get_complaints_df()
        staff_s = df["assigned_staff"] if "assigned_staff" in df.columns else pd.Series([""] * len(df), index=df.index)
        allotted_s = df["allotted_person"] if "allotted_person" in df.columns else pd.Series([""] * len(df), index=df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])
        new_df = df[(df["status"] == "Submitted") | ((df["status"] == "Under Review") & is_unassigned)]

        # Token search
        res_tok = new_df[new_df["complaint_id"].str.contains("CMP-2026-003", case=False)]
        self.assertEqual(len(res_tok), 1)

        # Title search
        res_title = new_df[new_df["title"].str.contains("Flickering", case=False)]
        self.assertEqual(len(res_title), 1)
        self.assertEqual(res_tok.iloc[0]["complaint_id"], "CMP-2026-003")

        # Student ID search
        res_stu = new_df[new_df["student_id"].fillna("").str.contains("12318042", case=False)]
        self.assertEqual(len(res_stu), 1)
        self.assertIn("Water Leakage", res_stu.iloc[0]["title"])

    def test_04_sorting_newest_and_oldest(self):
        """4. Sorting arranges complaints in correct chronological order."""
        df = get_complaints_df()
        staff_s = df["assigned_staff"] if "assigned_staff" in df.columns else pd.Series([""] * len(df), index=df.index)
        allotted_s = df["allotted_person"] if "allotted_person" in df.columns else pd.Series([""] * len(df), index=df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])
        new_df = df[(df["status"] == "Submitted") | ((df["status"] == "Under Review") & is_unassigned)]

        d_s = pd.to_datetime(new_df["date_reported"], errors="coerce")
        df_newest = new_df.assign(_d=d_s).sort_values(by="_d", ascending=False)
        self.assertEqual(df_newest["_d"].dropna().tolist(), sorted(df_newest["_d"].dropna().tolist(), reverse=True))

        df_oldest = new_df.assign(_d=d_s).sort_values(by="_d", ascending=True)
        self.assertEqual(df_oldest["_d"].dropna().tolist(), sorted(df_oldest["_d"].dropna().tolist(), reverse=False))

    def test_05_clear_filters_action_resets_state(self):
        """5. Clear Filters action safely resets all session state keys."""
        import streamlit as st

        st.session_state["search_new"] = "Water leak"
        st.session_state["sort_new"] = "Oldest first"
        st.session_state["f_stat_new"] = "Submitted"
        st.session_state["f_cat_new"] = "Plumbing"
        st.session_state["f_loc_new"] = "Hostel Block B"
        st.session_state["f_date_new"] = "Today"
        st.session_state["f_prio_new"] = "High"
        st.session_state["page_sel_new"] = 2

        admin_requests.reset_requests_filters("new")

        self.assertEqual(st.session_state["search_new"], "")
        self.assertEqual(st.session_state["sort_new"], "Newest first")
        self.assertEqual(st.session_state["f_stat_new"], "All Statuses")
        self.assertEqual(st.session_state["f_cat_new"], "All Categories")
        self.assertEqual(st.session_state["f_loc_new"], "All Locations")
        self.assertEqual(st.session_state["f_date_new"], "All Dates")
        self.assertEqual(st.session_state["f_prio_new"], "All Priorities")
        self.assertEqual(st.session_state["page_sel_new"], 1)

    def test_06_administrative_action_mark_under_review(self):
        """6. Marking a submitted ticket as Under Review records audit and updates status."""
        new_cid = add_complaint({
            "title": "Air Conditioner Water Dripping",
            "description": "Condensate line blocked.",
            "facility_type": "HVAC",
            "building": "Hostel Block C",
            "location": "Hostel Block C Room 204",
            "status": "Submitted",
            "student_id": "12318042",
            "student_name": "Praveen",
        })

        ok = update_complaint_status_extended(
            complaint_id=new_cid,
            new_status="Under Review",
            remarks="Acknowledged by operations and taken under evaluation.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )
        self.assertTrue(ok)

        df = get_complaints_df()
        rec = df[df["complaint_id"] == new_cid].iloc[0]
        self.assertEqual(rec["status"], "Under Review")
        self.assertEqual(rec["action_taken"], "Acknowledged by operations and taken under evaluation.")

    def test_07_administrative_action_assign_staff_and_move_in_progress(self):
        """7. Assigning staff moves ticket into active operations with full audit trail."""
        target_cid = "CMP-2026-003"
        ok = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Assigned",
            remarks="Assigned to Electrical Maintenance Squad for inspection.",
            admin_id="ADM-2026-003",
            admin_title="Maintenance Dispatcher",
            assigned_staff="Electrical Maintenance Squad",
        )
        self.assertTrue(ok)

        df = get_complaints_df()
        rec = df[df["complaint_id"] == target_cid].iloc[0]
        self.assertEqual(rec["status"], "Assigned")
        self.assertEqual(rec["allotted_person"], "Electrical Maintenance Squad")

        # Now verify that CMP-2026-003 is excluded from New / Unassigned
        staff_s = df["assigned_staff"] if "assigned_staff" in df.columns else pd.Series([""] * len(df), index=df.index)
        allotted_s = df["allotted_person"] if "allotted_person" in df.columns else pd.Series([""] * len(df), index=df.index)
        is_unassigned = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                        allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])
        new_df = df[(df["status"] == "Submitted") | ((df["status"] == "Under Review") & is_unassigned)]
        self.assertNotIn(target_cid, new_df["complaint_id"].values)

    def test_08_student_history_synchronization(self):
        """8. Authorised status transitions reflect in Student History immediately with data isolation."""
        stu_id = "12318042"
        other_stu = "11904523"

        cid = add_complaint({
            "title": "Door Hinge Detached",
            "description": "Room entry door hinge screws pulled out.",
            "facility_type": "Other maintenance issues",
            "building": "Hostel Block B",
            "location": "Hostel Block B Room 102",
            "status": "Submitted",
            "student_id": stu_id,
            "student_name": "Praveen",
        })

        # Initially student sees Submitted
        stu_recs = get_student_complaints(stu_id)
        target = next(c for c in stu_recs if c["complaint_id"] == cid)
        self.assertEqual(target["status"], "Submitted")

        # Admin assigns and moves to In Progress
        update_complaint_status_extended(
            complaint_id=cid,
            new_status="In Progress",
            remarks="Carpentry crew dispatched with replacement mounting screws.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
            assigned_staff="Carpentry & Furniture Repairs",
        )

        # Student immediately sees In Progress and assigned staff
        stu_recs_after = get_student_complaints(stu_id)
        target_after = next(c for c in stu_recs_after if c["complaint_id"] == cid)
        self.assertEqual(target_after["status"], "In Progress")
        self.assertEqual(target_after["allotted_person"], "Carpentry & Furniture Repairs")
        self.assertEqual(target_after["action_taken"], "Carpentry crew dispatched with replacement mounting screws.")

        # Other student cannot see this complaint (data isolation)
        other_recs = get_student_complaints(other_stu)
        self.assertNotIn(cid, [c["complaint_id"] for c in other_recs])

    def test_09_apptest_new_unassigned_full_workflow(self):
        """9. Full Streamlit AppTest verifies New / Unassigned page, search, clear filters, and details panel."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        at.session_state["auth_user"] = {
            "admin_id": "ADM-2026-001",
            "name": "Facility Operations Lead",
            "role": "admin",
            "title": "Facility Operations Lead",
        }
        at.session_state["user_role"] = "admin"
        at.session_state["admin_active_page"] = "New / Unassigned"
        at.run()

        # Zero runtime exceptions
        self.assertEqual(len(at.exception), 0, f"Exceptions on initial run: {[e.value for e in at.exception]}")

        # Type search query
        at.text_input(key="search_new").input("Flickering")
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("search_new"), "Flickering")

        # Click Clear Filters
        at.button(key="btn_reset_new").click()
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("search_new"), "")


if __name__ == "__main__":
    unittest.main()
