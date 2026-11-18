"""
Test Suite for FIPP 2.0 Student Dashboard Redesign.
Verifies:
1. Clean horizontal header containing FIPP logo, Facility Issue Prediction & Prioritisation System title, and Home option.
2. Main dashboard with two prominent options: 'Raise a Query' and 'History'.
3. Student declaration with two mandatory checkboxes:
   - 'I am responsible for the content typed in my query.'
   - 'The information given by me regarding the complaint/request is true to the best of my knowledge.'
   and dynamic 'Agree & Proceed' button disabled initially and enabled only when both checkboxes are checked.
4. Form fields for Raise a Query: Student Name, Student ID, Issue Title, Facility Category, Building or Block,
   Floor or Specific Location, Detailed Issue Description, and optional photo upload.
5. Strict student data isolation and complaint token generation (CMP-2026-XXX).
"""
import inspect
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from dashboard.pages import student_dashboard
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    reset_to_default_dataset,
)


class TestStudentDashboardRedesign(unittest.TestCase):
    """Verifies all requirements for the redesigned Student Dashboard notebook sketch."""

    def setUp(self):
        reset_to_default_dataset()
        st.session_state.clear()

    def test_header_components(self):
        """Header must contain FIPP logo, full project title, and Home option."""
        source = inspect.getsource(student_dashboard)

        self.assertIn("🏫", source)
        self.assertIn("Facility Issue Prediction &amp; Prioritisation System", source)
        self.assertIn('"Home"', source)
        self.assertIn("btn_student_hdr_home", source)

    def test_main_dashboard_two_options(self):
        """Main dashboard must feature two equal-sized prominent options: 'Raise a Query' and 'History'."""
        source = inspect.getsource(student_dashboard)

        # Raise a Query option
        self.assertIn("Raise a Query", source)
        self.assertIn("💬", source)

        # History option
        self.assertIn("History", source)
        self.assertIn("🕒", source)

    def test_student_declaration_removed(self):
        """Student declaration section, checkboxes, and Agree & Proceed button must be completely removed."""
        source = inspect.getsource(student_dashboard)

        # Declaration heading and descriptions removed
        self.assertNotIn("Student Declaration", source)
        self.assertNotIn("Please review and accept the official student undertaking", source)

        # Both checkboxes removed
        self.assertNotIn("I am responsible for the content typed in my query.", source)
        self.assertNotIn(
            "The information given by me regarding the complaint/request is true to the best of my knowledge.",
            source,
        )

        # Agree & Proceed button removed
        self.assertNotIn('"Agree & Proceed"', source)
        self.assertNotIn("btn_agree_and_proceed", source)

        # Direct card navigation buttons present
        self.assertIn("btn_open_raise_query", source)
        self.assertIn("btn_open_history", source)

    def test_complaint_form_fields_including_photo_upload(self):
        """Form must contain Student Name, ID, Title, Category, Building, Floor/Location, Description, and photo upload."""
        source = inspect.getsource(student_dashboard)

        self.assertIn('"Student Name"', source)
        self.assertIn('"Student ID"', source)
        self.assertIn('"Issue Title / Brief Headline"', source)
        self.assertIn('"Facility Category"', source)
        self.assertIn('"Building or Block"', source)
        self.assertIn('"Floor or Specific Location"', source)
        self.assertIn('"Detailed Issue Description"', source)
        self.assertIn('"Upload Issue Photo (Optional)"', source)

        # Form action buttons
        self.assertIn('"Submit Issue"', source)
        self.assertIn('"Cancel"', source)

    def test_student_data_isolation(self):
        """History must strictly isolate complaints to currently authenticated student."""
        # Fresh student ID has zero complaints
        fresh_id = "STU-2026-555"
        self.assertEqual(len(get_student_complaints(fresh_id)), 0)

        # Submit complaint for STU-2026-555
        tok = add_complaint({
            "student_id": fresh_id,
            "student_name": "Test Student",
            "title": "Broken study light in library reading room",
            "facility_type": "Electrical or lighting issues",
            "building": "Central Library",
            "specific_location": "2nd Floor Desk 14",
            "description": "Flickering lamp creates eye strain.",
            "status": "Submitted",
        })

        self.assertTrue(re.match(r"^CMP-2026-\d{3}$", tok))

        # Check that fresh student sees exactly 1 complaint
        stu_complaints = get_student_complaints(fresh_id)
        self.assertEqual(len(stu_complaints), 1)
        self.assertEqual(stu_complaints[0]["complaint_id"], tok)
        self.assertEqual(stu_complaints[0]["student_id"], fresh_id)

        # Check that another student STILL sees 0 complaints
        other_complaints = get_student_complaints("STU-2026-777")
        self.assertEqual(len(other_complaints), 0)


if __name__ == "__main__":
    unittest.main()
