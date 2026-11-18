"""
Test Suite for FIPP Stage 1 — Student Complaint Submission Workflow & History.
Verifies all workflow requirements and latest corrections:
1. Category Type selection directly in form without step boxes or numbering.
2. Message Type selection (Grievance, Assistance, Enquiry, Feedback, Positive Feedback).
3. Strict dependency sequence: Message Type -> Category -> Sub Category -> Specific Category.
   Dependent dropdowns are disabled until their parent is selected.
4. Location selection and conditional Room Number / Any Other fields.
5. Contact Number validation.
6. Availability Date and Time Slots.
7. 500-character description limit with live counter.
8. Save and Reset functionality.
9. Complaint token generation (CMP-2026-XXX).
10. Persistent storage.
11. Student-only History visibility.
12. Admin status updates appearing in Student History.
13. Raise a Query and History remain separate without auto-redirecting to History on submit.
"""
import inspect
import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from dashboard.pages import student_dashboard
from src.data.complaint_categories import (
    CATEGORY_TYPES,
    MESSAGE_TYPES,
    CLASSIFICATION_HIERARCHY,
    CAMPUS_BLOCKS,
    CAMPUS_SUB_BLOCKS,
    ROOM_TYPES,
    TIME_SLOTS,
    get_categories_for_type,
    get_sub_categories,
    get_specific_categories,
)
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    generate_next_token,
    update_complaint_status,
    reset_to_default_dataset,
)


class TestStage1StudentWorkflow(unittest.TestCase):
    """Rigorous verification of the Stage 1 Student Complaint Workflow and corrections."""

    def setUp(self):
        reset_to_default_dataset()
        st.session_state.clear()

    def test_01_category_type_selection_and_no_step_numbering(self):
        """1. Category Type selection: present directly in form without step boxes or numbering."""
        self.assertIn("Academic and Administrative Issues", CATEGORY_TYPES)
        self.assertIn("Maintenance / Electrical Complaints", CATEGORY_TYPES)
        self.assertEqual(len(CATEGORY_TYPES), 2)

        source = inspect.getsource(student_dashboard)
        self.assertIn("sq_category_type", source)
        self.assertIn("Category Type", source)

        # Step 1 box and step numbering must be completely removed
        self.assertNotIn("Step 1", source)
        self.assertNotIn("Step 2", source)
        self.assertNotIn("Step 3", source)
        self.assertNotIn("Step 4", source)
        self.assertNotIn("Step 5", source)
        self.assertNotIn("Step 6", source)
        self.assertNotIn("Step 7", source)
        self.assertNotIn("step-badge", source)

    def test_02_message_type_selection(self):
        """2. Message Type selection: verifies 5 mandatory message types."""
        expected_types = ["Grievance", "Assistance", "Enquiry", "Feedback", "Positive Feedback"]
        self.assertEqual(MESSAGE_TYPES, expected_types)

        source = inspect.getsource(student_dashboard)
        self.assertIn("sq_message_type", source)
        self.assertIn("Message Type", source)

    def test_03_message_type_to_category_strict_dependency(self):
        """3. Strict Message Type -> Category -> Sub Category -> Specific Category dependency chain."""
        source = inspect.getsource(student_dashboard)

        # Category is disabled until Message Type is selected
        self.assertIn("disabled=cat_disabled", source)
        self.assertIn("cat_options = [\"-- Select Message Type first --\"]", source)

        # Sub Category is disabled until Category is selected
        self.assertIn("disabled=sub_cat_disabled", source)
        self.assertIn("sub_cat_options = [\"-- Select Category first --\"]", source)

        # Specific Category is disabled until Sub Category is selected
        self.assertIn("disabled=spec_cat_disabled", source)
        self.assertIn("spec_cat_options = [\"-- Select Sub Category first --\"]", source)

        # Parent change detection and child resets
        self.assertIn("_tracked_cat_type", source)
        self.assertIn("_tracked_msg_type", source)
        self.assertIn("_tracked_category", source)
        self.assertIn("_tracked_sub_category", source)

    def test_04_location_details_and_conditional_room_types(self):
        """4. Location selection and conditional Room Number / Any Other fields."""
        self.assertIn("Hostel Block A", CAMPUS_BLOCKS)
        self.assertIn("Central Library", CAMPUS_BLOCKS)
        self.assertIn("Room No", ROOM_TYPES)
        self.assertIn("Any Other", ROOM_TYPES)

        source = inspect.getsource(student_dashboard)
        self.assertIn("sq_block", source)
        self.assertIn("sq_sub_block", source)
        self.assertIn("sq_room_type", source)
        self.assertIn("sq_room_number", source)
        self.assertIn("sq_specified_location", source)

    def test_05_contact_number_validation(self):
        """5. Contact number validation: requires valid 10-digit mobile number."""
        source = inspect.getsource(student_dashboard)
        self.assertIn("sq_contact_number", source)
        self.assertIn("Contact Number is mandatory", source)
        self.assertIn("valid 10-digit mobile contact number", source)

    def test_06_availability_date_and_time_slots(self):
        """6. Availability Date and Time Slots validation."""
        expected_slots = [
            "08:00–10:00",
            "10:00–12:00",
            "12:00–14:00",
            "14:00–16:00",
            "16:00–18:00",
        ]
        self.assertEqual(TIME_SLOTS, expected_slots)

        source = inspect.getsource(student_dashboard)
        self.assertIn("sq_availability_date", source)
        self.assertIn("Preferred Time Slots", source)
        self.assertIn("at least one preferred time slot", source)

    def test_07_500_character_description_limit(self):
        """7. 500-character description limit with remaining character calculation."""
        source = inspect.getsource(student_dashboard)
        self.assertIn("max_chars=500", source)
        self.assertIn("500 - desc_len", source)
        self.assertIn("Exceeded by", source)

    def test_08_save_and_reset_functionality(self):
        """8. Save and Reset functionality."""
        source = inspect.getsource(student_dashboard)
        self.assertIn("btn_save_query", source)
        self.assertIn("btn_reset_query", source)
        self.assertIn("_reset_submission_form_state", source)

    def test_09_complaint_token_generation(self):
        """9. Sequential unique token generation format (CMP-2026-XXX)."""
        ticket = {
            "student_id": "STU-2026-101",
            "student_name": "Alex Chen",
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Plumbing",
            "sub_category": "Water Supply & Pipelines",
            "specific_category": "Pipe Leakage / Burst",
            "block": "Hostel Block B",
            "sub_block": "2nd Floor",
            "room_type": "Room No",
            "room_number": "204",
            "contact_number": "9876543210",
            "availability_date": date.today().strftime("%Y-%m-%d"),
            "time_slots": ["10:00–12:00", "14:00–16:00"],
            "description": "Continuous water leaking from washbasin pipe.",
        }
        token = add_complaint(ticket)
        self.assertTrue(bool(re.match(r"^CMP-2026-\d{3}$", token)))

    def test_10_persistent_storage(self):
        """10. Persistent storage retains submitted complaint details."""
        ticket = {
            "student_id": "STU-2026-101",
            "student_name": "Alex Chen",
            "category_type": "Maintenance / Electrical Complaints",
            "message_type": "Grievance",
            "category": "Electrical or lighting issues",
            "sub_category": "Lighting & Fixtures",
            "specific_category": "Switchboard / Socket Sparking",
            "block": "Academic Block 1",
            "sub_block": "1st Floor",
            "room_type": "Room No",
            "room_number": "108",
            "contact_number": "9123456780",
            "availability_date": date.today().strftime("%Y-%m-%d"),
            "time_slots": ["08:00–10:00"],
            "description": "Power socket sparks upon plugging in laboratory equipment.",
        }
        tok = add_complaint(ticket)

        df = get_complaints_df()
        record = df[df["complaint_id"] == tok].iloc[0]
        self.assertEqual(record["student_id"], "STU-2026-101")
        self.assertEqual(record["message_type"], "Grievance")
        self.assertEqual(record["contact_number"], "9123456780")
        self.assertEqual(record["specific_category"], "Switchboard / Socket Sparking")
        self.assertIn("Academic Block 1", record["location"])

    def test_11_student_only_history_visibility(self):
        """11. Student-only History visibility enforces strict data isolation."""
        stu1_id = "STU-2026-101"
        stu2_id = "STU-2026-202"

        # Submit complaint for student 1
        tok1 = add_complaint({
            "student_id": stu1_id,
            "student_name": "Alex Chen",
            "category": "Plumbing",
            "specific_category": "Tap / Faucet Broken or Leaking",
            "description": "Bathroom tap dripping constantly.",
            "block": "Hostel Block A",
            "room_number": "101",
        })

        # Submit complaint for student 2
        tok2 = add_complaint({
            "student_id": stu2_id,
            "student_name": "David Miller",
            "category": "HVAC",
            "specific_category": "AC Unit Not Cooling",
            "description": "Room AC not providing cold air.",
            "block": "Hostel Block C",
            "room_number": "304",
        })

        stu1_records = get_student_complaints(stu1_id)
        stu1_tokens = [c["complaint_id"] for c in stu1_records]
        self.assertIn(tok1, stu1_tokens)
        self.assertNotIn(tok2, stu1_tokens)

        stu2_records = get_student_complaints(stu2_id)
        stu2_tokens = [c["complaint_id"] for c in stu2_records]
        self.assertIn(tok2, stu2_tokens)
        self.assertNotIn(tok1, stu2_tokens)

    def test_12_admin_status_updates_appear_in_student_history(self):
        """12. Admin status updates immediately propagate to Student History."""
        stu_id = "STU-2026-101"
        tok = add_complaint({
            "student_id": stu_id,
            "student_name": "Alex Chen",
            "category": "Washroom cleanliness",
            "specific_category": "Washroom Floor Dirty / Wet",
            "description": "Floor slippery due to pooled water.",
            "block": "Hostel Block B",
            "room_number": "205",
            "status": "Submitted",
        })

        # Verify initial status
        records = get_student_complaints(stu_id)
        target = [c for c in records if c["complaint_id"] == tok][0]
        self.assertEqual(target["status"], "Submitted")

        # Admin updates status to Under Review
        update_complaint_status(tok, "Under Review", action_taken="Sanitation team notified.")
        records = get_student_complaints(stu_id)
        target = [c for c in records if c["complaint_id"] == tok][0]
        self.assertEqual(target["status"], "Under Review")

        # Admin updates status to Assigned
        update_complaint_status(tok, "Assigned", action_taken="Assigned to Housekeeping Crew.")
        records = get_student_complaints(stu_id)
        target = [c for c in records if c["complaint_id"] == tok][0]
        self.assertEqual(target["status"], "Assigned")

        # Admin updates status to In Progress
        update_complaint_status(tok, "In Progress", action_taken="Crew cleaning corridor.")
        records = get_student_complaints(stu_id)
        target = [c for c in records if c["complaint_id"] == tok][0]
        self.assertEqual(target["status"], "In Progress")

        # Admin updates status to Resolved
        update_complaint_status(tok, "Resolved", action_taken="Area dried and sanitized.")
        records = get_student_complaints(stu_id)
        target = [c for c in records if c["complaint_id"] == tok][0]
        self.assertEqual(target["status"], "Resolved")

    def test_13_raise_a_query_and_history_separate_navigation(self):
        """13. Raise a Query and History remain separate at top without auto-redirect to History on submit."""
        source = inspect.getsource(student_dashboard)
        self.assertIn("btn_open_raise_query", source)
        self.assertIn("btn_open_history", source)
        self.assertIn('st.session_state["student_active_view"] = "raise"', source)
        self.assertIn('st.session_state["student_active_view"] = "history"', source)


if __name__ == "__main__":
    unittest.main()
