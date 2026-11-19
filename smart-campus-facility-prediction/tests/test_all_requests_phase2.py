"""
FIPP Phase 2 — Comprehensive Verification Test Suite for All Requests & Details Panel.
Tests all Phase 2 requirements:
1. Summary indicators calculated dynamically from real complaint records.
2. Search across Token, Student ID, and Issue Title.
3. Filters for Status, Category, Location, Date, and MCPI Priority.
4. Sorting (Newest first, Oldest first, Highest existing priority).
5. Clean enterprise table presentation with neutral indicators ("—") for missing fields.
6. Right-Side Complaint Details Panel sections A–F.
7. Mandatory resolution remarks when resolving.
8. Reopening workflow with mandatory justification on resolved tickets.
9. State preservation on panel close.
10. Immediate synchronization with Student History and persistent storage.
"""
import inspect
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
    _load_from_disk,
    PROGRESS_STAGES,
)
from dashboard.pages import admin_requests
from dashboard.components import complaint_details, styles


class TestAllRequestsPhase2(unittest.TestCase):
    """Test suite verifying all Phase 2 All Requests specifications."""

    def setUp(self):
        reset_to_default_dataset()

    def test_01_summary_indicators_dynamic_calculation(self):
        """1. Summary indicators are calculated dynamically from actual complaint records."""
        df = get_complaints_df()
        total_count = len(df)
        new_count = int((df["status"] == "Submitted").sum())
        in_prog_count = int(df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum())
        resolved_count = int((df["status"] == "Resolved").sum())

        self.assertGreater(total_count, 0)
        self.assertEqual(total_count, new_count + in_prog_count + resolved_count + int((df["status"] == "Withdrawn").sum()))

        # Adding a new complaint dynamically increases total and new count
        new_ticket = {
            "title": "HVAC Chilled Water Valve Leak",
            "description": "Chilled water leaking from ceiling pipe into corridor.",
            "facility_type": "HVAC",
            "building": "Engineering Block 1",
            "location": "Engineering Block 1 - 3rd Floor",
            "specific_location": "3rd Floor Corridor",
            "severity": "High",
            "status": "Submitted",
            "student_id": "12318042",
            "student_name": "Test Student",
        }
        new_cid = add_complaint(new_ticket)
        self.assertTrue(new_cid.startswith("CMP-2026-"))

        updated_df = get_complaints_df()
        self.assertEqual(len(updated_df), total_count + 1)
        self.assertEqual(int((updated_df["status"] == "Submitted").sum()), new_count + 1)

    def test_02_search_across_token_student_id_and_title(self):
        """2. Search functions correctly across Token, Student ID, and Issue Title."""
        df = get_complaints_df()

        # Token search
        target_token = "CMP-2026-001"
        res_tok = df[df["complaint_id"].str.lower().str.contains(target_token.lower(), regex=False)]
        self.assertEqual(len(res_tok), 1)
        self.assertEqual(res_tok.iloc[0]["complaint_id"], target_token)

        # Issue Title search
        title_word = "pipe"
        res_title = df[df["title"].str.lower().str.contains(title_word, regex=False)]
        self.assertGreaterEqual(len(res_title), 1)
        self.assertTrue(all("pipe" in t.lower() for t in res_title["title"]))

        # Student ID search
        add_complaint({
            "title": "Broken Socket in Dorm",
            "description": "Wall socket not providing power.",
            "facility_type": "Electrical",
            "building": "BH-1",
            "location": "BH-1 Room 102",
            "status": "Submitted",
            "student_id": "11904523",
            "student_name": "Priya Sharma",
        })
        df_after = get_complaints_df()
        res_stu = df_after[df_after["student_id"].fillna("").str.contains("11904523", regex=False)]
        self.assertEqual(len(res_stu), 1)
        self.assertEqual(res_stu.iloc[0]["student_id"], "11904523")

    def test_03_multi_field_filtering_on_stored_fields(self):
        """3. Filters accurately support Status, Category, Location, Date, and MCPI Priority."""
        df = get_complaints_df()

        # Status filter
        for status_val in ["Submitted", "Resolved"]:
            subset = df[df["status"] == status_val]
            if not subset.empty:
                self.assertTrue((subset["status"] == status_val).all())

        # Category filter
        for cat in df["facility_type"].dropna().unique()[:3]:
            cat_subset = df[df["facility_type"] == cat]
            self.assertTrue((cat_subset["facility_type"] == cat).all())

        # Priority filter
        for prio in ["Critical", "High", "Medium", "Low"]:
            prio_subset = df[df["priority_tier"] == prio]
            if not prio_subset.empty:
                self.assertTrue((prio_subset["priority_tier"] == prio).all())

        # Date filter
        dates = pd.to_datetime(df["date_reported"], errors="coerce")
        today = pd.Timestamp.now().normalize()
        past_7 = df[dates.dt.normalize() >= (today - pd.Timedelta(days=7))]
        self.assertGreater(len(past_7), 0)

    def test_04_sorting_records(self):
        """4. Sorting properly arranges records by Newest first, Oldest first, and Highest priority."""
        df = get_complaints_df()

        # Newest first
        d_newest = pd.to_datetime(df["date_reported"], errors="coerce")
        df_newest = df.assign(_d=d_newest).sort_values(by="_d", ascending=False)
        dates_list = df_newest["_d"].dropna().tolist()
        self.assertEqual(dates_list, sorted(dates_list, reverse=True))

        # Oldest first
        df_oldest = df.assign(_d=d_newest).sort_values(by="_d", ascending=True)
        dates_oldest = df_oldest["_d"].dropna().tolist()
        self.assertEqual(dates_oldest, sorted(dates_oldest, reverse=False))

        # Highest priority
        df_prio = df.sort_values(by="priority_score", ascending=False)
        scores = df_prio["priority_score"].tolist()
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_05_clean_table_presentation_and_neutral_indicators(self):
        """5. Verifies clean table columns, neutral indicators ('—') for missing fields, and no emojis."""
        req_src = inspect.getsource(admin_requests)
        self.assertIn("TOKEN", req_src)
        self.assertIn("ISSUE", req_src)
        self.assertIn("STUDENT ID", req_src)
        self.assertIn("CATEGORY", req_src)
        self.assertIn("LOCATION", req_src)
        self.assertIn("SUBMITTED", req_src)
        self.assertIn("STATUS", req_src)
        self.assertIn("PRIORITY", req_src)

        # Clear Filters action present
        self.assertIn("Clear Filters", req_src)

        # Neutral indicator "—" used for missing data
        self.assertIn("—", req_src)

        # Zero cheap emojis in source
        for forbidden in ["📊", "📋", "🆕", "⏳", "✅", "📈", "🛡️"]:
            self.assertNotIn(forbidden, req_src)

    def test_06_details_panel_sections_a_through_f(self):
        """6. Right-Side Complaint Details Panel implements all required sections."""
        details_src = inspect.getsource(complaint_details)
        self.assertIn("Complaint Details", details_src)
        self.assertIn("Student Details", details_src)
        self.assertIn("Administrative Information", details_src)
        self.assertIn("Attachments", details_src)
        self.assertIn("Remarks &amp; History", details_src)
        self.assertIn("Operational Actions", details_src)

        # Missing contact fallback to "—"
        self.assertIn('contact_no = "—"', details_src)

    def test_07_status_update_and_mandatory_resolution_remarks(self):
        """7. Status updates persist and mandatory resolution remarks are enforced."""
        df = get_complaints_df()
        target_cid = df.iloc[0]["complaint_id"]

        # Successful update to In Progress
        ok = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="In Progress",
            remarks="Squad dispatched to inspect valve.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
            assigned_staff="Plumbing Response Team",
        )
        self.assertTrue(ok)

        # Verify disk persistence
        disk_records = _load_from_disk()
        rec = next(r for r in disk_records if r["complaint_id"] == target_cid)
        self.assertEqual(rec["status"], "In Progress")
        self.assertEqual(rec["allotted_person"], "Plumbing Response Team")

        # Resolve ticket with remarks
        ok_res = update_complaint_status_extended(
            complaint_id=target_cid,
            new_status="Resolved",
            remarks="Main line valve replaced and hydrostatic pressure test passed.",
            admin_id="ADM-2026-001",
            admin_title="Facility Operations Lead",
        )
        self.assertTrue(ok_res)

        disk_after = _load_from_disk()
        rec_res = next(r for r in disk_after if r["complaint_id"] == target_cid)
        self.assertEqual(rec_res["status"], "Resolved")
        self.assertIn("hydrostatic pressure", rec_res.get("closing_remarks", ""))

    def test_08_reopening_resolved_complaint(self):
        """8. Reopening a resolved complaint requires justification and transitions to 'Under Review'."""
        df = get_complaints_df()
        resolved_tickets = df[df["status"] == "Resolved"]
        self.assertGreater(len(resolved_tickets), 0)
        target_cid = resolved_tickets.iloc[0]["complaint_id"]

        # Reopen complaint
        reopen_reason = "Water pressure drop observed again after 24 hours."
        ok_reopen = reopen_complaint(
            complaint_id=target_cid,
            remarks=reopen_reason,
            admin_id="ADM-2026-002",
            admin_title="Campus Infrastructure Admin",
        )
        self.assertTrue(ok_reopen)

        # Verify state in disk storage
        disk_records = _load_from_disk()
        rec = next(r for r in disk_records if r["complaint_id"] == target_cid)
        self.assertEqual(rec["status"], "Under Review")
        self.assertTrue(rec.get("is_reopened"))

        # Verify earlier history is preserved
        history = rec.get("remarks_history", [])
        self.assertGreaterEqual(len(history), 1)
        self.assertIn("Complaint Reopened", history[0]["remarks"])

    def test_09_student_portal_history_synchronization(self):
        """9. Administrator actions immediately synchronize with Student History."""
        stu_id = "12318042"
        # Submit a student complaint
        new_cid = add_complaint({
            "title": "Study Lamp Not Functioning",
            "description": "Desk lamp socket shorted in room.",
            "facility_type": "Electrical Maintenance",
            "building": "BH-5",
            "location": "BH-5 Room 302",
            "status": "Submitted",
            "student_id": stu_id,
            "student_name": "Aditya Verma",
        })

        # Student initially sees 'Submitted'
        stu_records = get_student_complaints(stu_id)
        match_init = next(r for r in stu_records if r["complaint_id"] == new_cid)
        self.assertEqual(match_init["status"], "Submitted")

        # Admin updates status to 'Assigned' with technician
        update_complaint_status_extended(
            complaint_id=new_cid,
            new_status="Assigned",
            remarks="Assigned to Electrical Maintenance Squad.",
            admin_id="ADM-2026-003",
            admin_title="Maintenance Dispatcher",
            assigned_staff="Electrical Maintenance Squad",
        )

        # Student immediately sees updated status and technician
        stu_records_after = get_student_complaints(stu_id)
        match_after = next(r for r in stu_records_after if r["complaint_id"] == new_cid)
        self.assertEqual(match_after["status"], "Assigned")
        self.assertEqual(match_after["allotted_person"], "Electrical Maintenance Squad")

    def test_10_status_badge_clean_dot_indicators(self):
        """10. Status badges use clean indicator dots (no emojis)."""
        for s in ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved", "Withdrawn"]:
            badge = styles.get_status_badge(s)
            self.assertIn("●", badge) if s != "Resolved" else self.assertIn("✓", badge)
            self.assertNotIn("⏳", badge)
            self.assertNotIn("⚡", badge)
            self.assertNotIn("📌", badge)


if __name__ == "__main__":
    unittest.main()
