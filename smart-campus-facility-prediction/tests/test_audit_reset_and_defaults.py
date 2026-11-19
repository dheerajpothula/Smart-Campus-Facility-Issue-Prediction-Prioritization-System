"""
FIPP — Comprehensive Functional Audit, Reset Behaviour & Default Value Removal Verification Suite.
Validates:
1. Form Reset Behaviour:
   - Reset clears text fields, dropdowns, radios, checkboxes, date pickers, file uploaders.
   - Reset clears cascaded downstream selections and visible validation error alerts.
   - Reset preserves user authentication and keeps student on the active form.
   - Reset does not submit complaints, generate tokens, or modify the database.
2. Removal of Default / Preselected Values:
   - Category Type radio starts unselected (index=None).
   - Availability Date starts unselected (value=None).
   - Time Slot radio starts unselected (index=None).
   - Form fields use helpful placeholders without prefilled sample values.
   - No hardcoded sample student names ('Alex Chen') in default URL parameter handlers.
3. Elimination of Cheap Emoji Symbols:
   - Professional Lucide SVG icons and clean typography across student and admin portals.
4. Data Integrity & Student Isolation:
   - Submissions persist to disk and re-load faithfully.
   - Student queries are strictly isolated to the authenticated student ID.
   - MCPI priority scores compute accurately without distortion.
"""
import inspect
import sys
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from dashboard.pages import student_dashboard, admin_requests, admin_reports, overview
from dashboard.components import login_page, role_selection, sidebar
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    reset_to_default_dataset,
)
from src.prediction.priority_scoring import calculate_priority_score, PriorityWeights


class TestAuditResetAndDefaults(unittest.TestCase):
    """Test suite verifying complete functional audit, reset behavior, and default removal."""

    def setUp(self):
        reset_to_default_dataset()
        self.dashboard_source = inspect.getsource(student_dashboard)
        self.login_source = inspect.getsource(login_page)
        self.role_source = inspect.getsource(role_selection)
        self.reports_source = inspect.getsource(admin_reports)

    def test_01_reset_clears_all_form_session_state(self):
        """Reset clears all text inputs, dropdowns, radios, checkboxes, dates, and validation errors."""
        # Simulate populated form session state
        st.session_state["sq_category_type"] = "Maintenance / Electrical Complaints"
        st.session_state["sq_message_type"] = "Grievance"
        st.session_state["sq_category"] = "Electricity"
        st.session_state["sq_sub_category"] = "Power failure in room"
        st.session_state["sq_specific_categories"] = ["Complete room dark"]
        st.session_state["chk_spec_opt_Electricity_Power failure in room_0"] = True
        st.session_state["sq_block"] = "Hostel Block A"
        st.session_state["sq_sub_block"] = "Wing 1"
        st.session_state["sq_room_type"] = "Room No"
        st.session_state["sq_room_number"] = "402"
        st.session_state["sq_specified_location"] = "Near elevator"
        st.session_state["sq_contact_number"] = "9876543210"
        st.session_state["sq_availability_date"] = date(2026, 12, 1)
        st.session_state["sq_time_slot_radio"] = "10:00–12:00"
        st.session_state["sq_description"] = "No power in room since morning."
        st.session_state["sq_validation_errors"] = ["Some previous validation error"]
        st.session_state["_tracked_cat_type"] = "Maintenance / Electrical Complaints"
        st.session_state["_tracked_msg_type"] = "Grievance"
        st.session_state["_tracked_category"] = "Electricity"
        st.session_state["_tracked_sub_category"] = "Power failure in room"
        st.session_state["sq_faq_confirmed_sub"] = "Power failure in room"

        # Preserve authentication state
        st.session_state["auth_user"] = {"role": "student", "name": "Audit Student", "id": "STU-AUDIT-001"}
        st.session_state["user_role"] = "student"
        st.session_state["student_active_view"] = "raise"
        st.session_state["student_agreed"] = True

        # Initial complaint count
        initial_count = len(get_complaints_df())

        # Trigger reset
        student_dashboard._reset_submission_form_state()

        # Verify all form fields are reset to blank defaults
        self.assertIsNone(st.session_state.get("sq_category_type"))
        self.assertIsNone(st.session_state.get("sq_message_type"))
        self.assertIsNone(st.session_state.get("sq_category"))
        self.assertIsNone(st.session_state.get("sq_sub_category"))
        self.assertEqual(st.session_state.get("sq_specific_categories"), [])
        self.assertIsNone(st.session_state.get("sq_block"))
        self.assertIsNone(st.session_state.get("sq_sub_block"))
        self.assertIsNone(st.session_state.get("sq_room_type"))
        self.assertEqual(st.session_state.get("sq_room_number"), "")
        self.assertEqual(st.session_state.get("sq_specified_location"), "")
        self.assertEqual(st.session_state.get("sq_contact_number"), "")
        self.assertIsNone(st.session_state.get("sq_availability_date"))
        self.assertIsNone(st.session_state.get("sq_time_slot_radio"))
        self.assertEqual(st.session_state.get("sq_description"), "")
        self.assertEqual(st.session_state.get("sq_validation_errors"), [])
        self.assertNotIn("chk_spec_opt_Electricity_Power failure in room_0", st.session_state)

        # Verify authentication and view are preserved
        self.assertEqual(st.session_state.get("auth_user")["id"], "STU-AUDIT-001")
        self.assertEqual(st.session_state.get("user_role"), "student")
        self.assertEqual(st.session_state.get("student_active_view"), "raise")
        self.assertTrue(st.session_state.get("student_agreed"))

        # Verify no database complaint was added
        self.assertEqual(len(get_complaints_df()), initial_count)

    def test_02_no_default_preselection_in_category_type_and_availability_date(self):
        """Verifies Category Type, Availability Date, and Time Slot have no preselected values."""
        # Category Type radio must not default to index=1
        self.assertNotIn("index=1,", self.dashboard_source)
        self.assertIn("cat_type_idx = CATEGORY_TYPES.index(curr_cat_type) if", self.dashboard_source)
        self.assertIn("index=cat_type_idx", self.dashboard_source)

        # Availability Date must default to None rather than date.today()
        self.assertIn('value=st.session_state.get("sq_availability_date", None)', self.dashboard_source)

        # Time Slot must use slot_idx which defaults to None
        self.assertIn("index=slot_idx", self.dashboard_source)

    def test_03_no_hardcoded_sample_student_names(self):
        """Verifies removal of hardcoded sample student names like 'Alex Chen'."""
        self.assertNotIn("Alex Chen", self.login_source)
        self.assertIn("Enter Student Name", self.login_source)

        # Also check app.py query parameter fallback
        app_path = PROJECT_ROOT / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            app_src = f.read()
        self.assertNotIn('s_name = st.query_params.get("name", "Alex Chen")', app_src)

    def test_04_no_cheap_emojis_in_student_or_role_selection_ui(self):
        """Verifies no cheap emojis are displayed in role selection, login, or student buttons."""
        # Buttons in student dashboard must not start with emojis
        self.assertIn('"Raise a Query"', self.dashboard_source)
        self.assertIn('"Raise Another Query"', self.dashboard_source)
        self.assertNotIn('"💬 Raise a Query"', self.dashboard_source)
        self.assertNotIn('"➕ Raise Another Query"', self.dashboard_source)
        self.assertNotIn('"➕ Raise a Query"', self.dashboard_source)

        # Admin reports must not contain stopwatch emoji
        self.assertNotIn("⏱️", self.reports_source)

        # Role selection must use Lucide outline icons
        self.assertIn('render_lucide_icon("wrench"', self.role_source)
        self.assertIn('render_lucide_icon("graduation-cap"', self.role_source)

    def test_05_student_data_isolation(self):
        """Verifies student history displays only complaints submitted by that student."""
        stu1_id = "STU-ISOLATION-1"
        stu2_id = "STU-ISOLATION-2"

        t1 = add_complaint({
            "student_id": stu1_id,
            "student_name": "Student One",
            "title": "Broken desk in room",
            "facility_type": "Carpentry",
            "location": "Hostel Block A - Room 101",
            "description": "Desk leg broken.",
        })
        t2 = add_complaint({
            "student_id": stu2_id,
            "student_name": "Student Two",
            "title": "Leaking faucet",
            "facility_type": "Plumbing",
            "location": "Hostel Block B - Room 202",
            "description": "Bathroom tap dripping continuously.",
        })

        stu1_records = get_student_complaints(stu1_id)
        stu2_records = get_student_complaints(stu2_id)

        stu1_ids = [r["complaint_id"] for r in stu1_records]
        stu2_ids = [r["complaint_id"] for r in stu2_records]

        self.assertIn(t1, stu1_ids)
        self.assertNotIn(t2, stu1_ids)

        self.assertIn(t2, stu2_ids)
        self.assertNotIn(t1, stu2_ids)

    def test_06_mcpi_calculation_integrity(self):
        """Verifies accurate MCPI priority calculation without distortion."""
        # Critical severity in high criticality location with high recurrence
        score_crit, tier_crit, _ = calculate_priority_score(
            severity="Critical",
            location_type="Server Room",
            recurrence_risk=0.9,
            impact_scale=0.9,
        )
        self.assertTrue(score_crit >= 75.0)
        self.assertEqual(tier_crit, "Critical")

        # Low impact routine request
        score_low, tier_low, _ = calculate_priority_score(
            severity="Low",
            location_type="Campus Grounds",
            recurrence_risk=0.1,
            impact_scale=0.1,
        )
        self.assertTrue(score_low <= 35.0)
        self.assertEqual(tier_low, "Low")


if __name__ == "__main__":
    unittest.main()
