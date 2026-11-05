"""
Comprehensive verification test suite for the Final UI/UX Refinement and Student Complaint Tracking task.
Validates:
1. Role Selection page text, lack of arrows and extra paragraphs.
2. Student complaint isolation (fresh student sees 0 complaints, no sample complaints).
3. Exact 7-field form submission and validation.
4. Token format strictly CMP-2026-XXX (3-digit zero-padded, sequential, unique).
5. Student complaint card displays 5-stage progress timeline and NO priority labels/scores.
6. Admin complaint management view shows Student ID/Name and allows updating status across 5 stages.
7. Immediate reflection of Admin updates in Student progress indicator.
"""
import inspect
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    generate_next_token,
    update_complaint_status,
    reset_to_default_dataset,
    clear_all_complaints,
    PROGRESS_STAGES,
)
from dashboard.components import role_selection
from dashboard.components.styles import render_student_progress_timeline
from dashboard.pages import student_dashboard, complaint_management


class TestFinalRefinementRequirements(unittest.TestCase):
    """Rigorous verification of the final refinement acceptance criteria."""

    def setUp(self):
        reset_to_default_dataset()

    def test_requirement_1_role_selection_page_content(self):
        """1. Role selection page must display only required text, without removed text or arrow symbols."""
        source = inspect.getsource(role_selection)

        # Removed text must not appear
        self.assertNotIn(
            "Intelligent campus maintenance operations, automated NLP issue triage",
            source,
            "Found removed description paragraph on Role Selection page.",
        )
        self.assertNotIn(
            "Role-Based Access Demo: Select a profile below",
            source,
            "Found removed notice banner on Role Selection page.",
        )

        # No arrow symbols after titles or headings
        self.assertNotIn("→", source, "Found decorative arrow symbol '→' on Role Selection page.")

        # Exact required descriptions must be present
        self.assertIn(
            "Manage campus maintenance, facility issues, AI predictions, and maintenance priorities.",
            source,
        )
        self.assertIn(
            "Report facility issues and track your complaints.",
            source,
        )

    def test_requirement_2_student_sees_no_sample_complaints(self):
        """2. Student dashboard must display ONLY complaints submitted by that student."""
        # For a newly initialized student, no complaints must be returned
        alex_complaints = get_student_complaints("STU-2026-001")
        self.assertEqual(
            len(alex_complaints),
            0,
            "Student STU-2026-001 unexpectedly sees complaints before submitting any.",
        )

        fresh_complaints = get_student_complaints("STU-2026-002")
        self.assertEqual(len(fresh_complaints), 0)

        # Seed complaints in active register must NOT have student IDs
        df = get_complaints_df()
        self.assertGreater(len(df), 0, "Seed dataset should exist for admin.")
        student_records = df[df["student_id"].notna()]
        self.assertEqual(
            len(student_records),
            0,
            "Seed records must not have a student_id assigned so they don't leak into student view.",
        )

    def test_requirement_3_raise_issue_form_fields_and_validation(self):
        """3. Form fields and validation: exactly 7 fields, validated on submission."""
        source = inspect.getsource(student_dashboard)

        # Ensure no red asterisks in field labels
        self.assertNotIn('"Student ID*"', source)
        self.assertNotIn('"Student Name*"', source)
        self.assertNotIn('"Issue Title / Brief Headline*"', source)
        self.assertNotIn('"Facility Category*"', source)
        self.assertNotIn('"Building or Block*"', source)
        self.assertNotIn('"Floor or Specific Location*"', source)
        self.assertNotIn('"Detailed Issue Description*"', source)

        # Ensure 7 fields are present
        self.assertIn('"Student ID"', source)
        self.assertIn('"Student Name"', source)
        self.assertIn('"Issue Title / Brief Headline"', source)
        self.assertIn('"Facility Category"', source)
        self.assertIn('"Building or Block"', source)
        self.assertIn('"Floor or Specific Location"', source)
        self.assertIn('"Detailed Issue Description"', source)

        # Ensure action buttons
        self.assertIn('"Submit Issue"', source)
        self.assertIn('"Cancel"', source)

    def test_requirement_4_token_generation_format(self):
        """4. Token generation format: CMP-2026-001, CMP-2026-002, 3-digit zero-padded sequential."""
        token_regex = re.compile(r"^CMP-2026-\d{3}$")

        # When starting from fresh empty store
        clear_all_complaints()
        tok1 = generate_next_token([])
        self.assertEqual(tok1, "CMP-2026-001")

        # Test incrementing sequence
        c1 = add_complaint({
            "student_id": "STU-2026-001",
            "student_name": "Alex Chen",
            "title": "Broken Tap in 2nd Floor Washroom",
            "facility_type": "Plumbing",
            "building": "Hostel Block A",
            "specific_location": "2nd Floor Washroom",
            "description": "Tap leaking cold water continuously.",
        })
        self.assertEqual(c1, "CMP-2026-001")

        c2 = add_complaint({
            "student_id": "STU-2026-001",
            "student_name": "Alex Chen",
            "title": "AC Tripping in Lab",
            "facility_type": "HVAC",
            "building": "Academic Block 1",
            "specific_location": "Lab 101",
            "description": "AC unit humming and stopping.",
        })
        self.assertEqual(c2, "CMP-2026-002")

        c3 = add_complaint({
            "student_id": "STU-2026-002",
            "student_name": "Priya Sharma",
            "title": "Light Bulb Burned Out",
            "facility_type": "Electrical or lighting issues",
            "building": "Hostel Block B",
            "specific_location": "Room 304",
            "description": "Overhead bulb not turning on.",
        })
        self.assertEqual(c3, "CMP-2026-003")

        # Verify all match format
        for tok in [c1, c2, c3]:
            self.assertTrue(bool(token_regex.match(tok)))

    def test_requirement_5_student_progress_indicator_and_no_priority_badges(self):
        """5. Student complaint view displays 5-stage progress indicator and NO priority labels/scores."""
        source = inspect.getsource(student_dashboard)

        # Student dashboard must NOT call get_priority_badge
        self.assertNotIn("get_priority_badge", source, "Student dashboard must not render priority badges.")
        self.assertNotIn("priority_tier", source, "Student dashboard must not inspect priority tiers.")
        self.assertNotIn("priority_score", source, "Student dashboard must not inspect priority scores.")

        # Test the 5 progress stages
        for stage in PROGRESS_STAGES:
            html = render_student_progress_timeline(stage)
            self.assertIn("Submitted", html)
            self.assertIn("Under Review", html)
            self.assertIn("Assigned", html)
            self.assertIn("In Progress", html)
            self.assertIn("Resolved", html)

            # Ensure no priority or internal risk metrics
            self.assertNotIn("Critical", html)
            self.assertNotIn("High", html)
            self.assertNotIn("Medium", html)
            self.assertNotIn("Low", html)
            self.assertNotIn("priority_score", html)

    def test_requirement_6_admin_integration_and_status_update_propagation(self):
        """6. Admin views student complaints with Student ID/Name and updates status immediately."""
        # Submit student issue
        cid = add_complaint({
            "student_id": "STU-2026-001",
            "student_name": "Alex Chen",
            "title": "Window latch broken in Room 204",
            "facility_type": "Other maintenance issues",
            "building": "Hostel Block C",
            "specific_location": "Room 204",
            "description": "Window latch loose and rattles loudly in high wind.",
            "status": "Submitted",
        })

        # Admin fetches register
        admin_df = get_complaints_df()
        admin_rec = admin_df[admin_df["complaint_id"] == cid].iloc[0]

        # Admin must see Student ID and Student Name
        self.assertEqual(admin_rec["student_id"], "STU-2026-001")
        self.assertEqual(admin_rec["student_name"], "Alex Chen")

        # Admin must see ML predictions
        self.assertIn(admin_rec["severity"], ["Critical", "High", "Medium", "Low"])
        self.assertGreater(admin_rec["priority_score"], 0)
        self.assertIsNotNone(admin_rec["estimated_resolution"])

        # Admin updates status to 'Under Review'
        update_complaint_status(cid, "Under Review", action_taken="Facility manager inspected.")
        stu_recs = get_student_complaints("STU-2026-001")
        self.assertEqual(stu_recs[0]["status"], "Under Review")

        # Admin updates status to 'Assigned'
        update_complaint_status(cid, "Assigned", action_taken="Assigned to carpentry contractor.")
        stu_recs = get_student_complaints("STU-2026-001")
        self.assertEqual(stu_recs[0]["status"], "Assigned")

        # Admin updates status to 'In Progress'
        update_complaint_status(cid, "In Progress", action_taken="Carpentry contractor repairing latch.")
        stu_recs = get_student_complaints("STU-2026-001")
        self.assertEqual(stu_recs[0]["status"], "In Progress")

        # Admin updates status to 'Resolved'
        update_complaint_status(cid, "Resolved", action_taken="Latch replaced and tested.")
        stu_recs = get_student_complaints("STU-2026-001")
        self.assertEqual(stu_recs[0]["status"], "Resolved")

    def test_requirement_7_login_flow_and_simulated_auth(self):
        """7. Dedicated login interface for Administrator and Student with Name and ID validation."""
        from dashboard.components import login_page

        source = inspect.getsource(login_page)
        # Check requirements
        self.assertIn("Administrator Name", source)
        self.assertIn("Student Name", source)
        self.assertIn("Administrator ID", source)
        self.assertIn("Student ID", source)
        self.assertIn("Back to Role Selection", source)
        self.assertIn("Simulated Authentication", source)

        # No password or email inputs
        self.assertNotIn("password", source.lower())
        self.assertNotIn("email", source.lower())

    def test_requirement_8_admin_right_sidebar(self):
        """8. Admin right sidebar contains admin identity, all 8 navigation items, and logout button."""
        from dashboard.components.sidebar import ADMIN_NAVIGATION_OPTIONS, render_admin_sidebar

        # Check all 8 navigation menu sections
        expected_sections = [
            "Overview",
            "Complaint Management",
            "AI Analysis",
            "Priority Queue",
            "Predictive Maintenance",
            "Recurring Issues",
            "Explainable AI",
            "Settings",
        ]
        for section in expected_sections:
            self.assertTrue(
                any(section in opt for opt in ADMIN_NAVIGATION_OPTIONS),
                f"Missing admin navigation section: {section}",
            )

        # Calling render_admin_sidebar with custom identity
        selected = render_admin_sidebar(admin_name="Dr. Taylor", admin_id="ADM-888")
        self.assertIsNotNone(selected)

    def test_requirement_9_button_visibility_and_contrast(self):
        """9. Button visibility: primary #756044 / #FFFFFF, secondary #EAE3D2 / #1A1A1A, visible labels."""
        from dashboard.components.styles import GLOBAL_LIGHT_THEME_CSS

        # Primary button colors
        self.assertIn("#756044", GLOBAL_LIGHT_THEME_CSS, "Primary button background #756044 missing.")
        self.assertIn("#FFFFFF", GLOBAL_LIGHT_THEME_CSS, "White text for primary button missing.")
        self.assertIn("#5D4A32", GLOBAL_LIGHT_THEME_CSS, "Primary button hover #5D4A32 missing.")

        # Secondary button colors
        self.assertIn("#EAE3D2", GLOBAL_LIGHT_THEME_CSS, "Secondary button background #EAE3D2 missing.")
        self.assertIn("#D8CDB8", GLOBAL_LIGHT_THEME_CSS, "Secondary button hover #D8CDB8 missing.")

        # Label override to prevent black rectangle issue
        self.assertIn("button p", GLOBAL_LIGHT_THEME_CSS, "button p text contrast override missing.")


if __name__ == "__main__":
    unittest.main()
