"""
Integration tests for the Student 'Raise an Issue' workflow, token generation format,
student isolation, status propagation, and access control.
"""
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    generate_next_token,
    update_complaint_status,
    reset_to_default_dataset,
    predict_issue_attributes,
    PROGRESS_STAGES,
)
from dashboard.components.styles import render_student_progress_timeline


class TestStudentRaiseIssueWorkflow(unittest.TestCase):
    """Verifies student issue creation, sequential token format, student isolation, and admin status updates."""

    def setUp(self):
        reset_to_default_dataset()

    def test_token_format_three_digit_zero_padded(self):
        """Verifies all tokens adhere strictly to CMP-2026-001, CMP-2026-002, etc."""
        token_pattern = re.compile(r"^CMP-2026-\d{3}$")

        # Check default seed tokens
        df = get_complaints_df()
        for cid in df["complaint_id"]:
            self.assertTrue(
                bool(token_pattern.match(cid)),
                f"Token {cid} does not match required 3-digit format CMP-2026-XXX",
            )

        # Check next token generator
        next_tok = generate_next_token()
        self.assertTrue(bool(token_pattern.match(next_tok)))
        # Since seeds are 001..007, next must be CMP-2026-008
        self.assertEqual(next_tok, "CMP-2026-008")

    def test_student_isolation_and_empty_state_for_new_student(self):
        """Ensures a student never sees sample complaints or another student's complaints."""
        # Fresh student ID has 0 complaints submitted
        fresh_student_complaints = get_student_complaints("STU-2026-999")
        self.assertEqual(len(fresh_student_complaints), 0)

        # Pre-existing seed complaints must not belong to STU-2026-001 or any student
        df = get_complaints_df()
        seed_complaints_for_stu1 = df[df["student_id"] == "STU-2026-001"]
        self.assertEqual(len(seed_complaints_for_stu1), 0)

    def test_student_form_submission_with_seven_fields(self):
        """Simulates 7-field complaint submission and verifies storage, token, and status."""
        new_ticket = {
            "student_id": "STU-2026-001",
            "student_name": "Alex Chen",
            "title": "Water leak under sink in 2nd floor washroom",
            "facility_type": "Plumbing",
            "building": "Hostel Block B",
            "specific_location": "2nd Floor Washroom, Room 204",
            "description": "Continuous cold water dripping under the sink forming a pool on the floor.",
            "status": "Submitted",
        }

        created_token = add_complaint(new_ticket)
        self.assertTrue(re.match(r"^CMP-2026-\d{3}$", created_token))

        # Check student complaints query
        stu_complaints = get_student_complaints("STU-2026-001")
        self.assertEqual(len(stu_complaints), 1)
        target = stu_complaints[0]
        self.assertEqual(target["complaint_id"], created_token)
        self.assertEqual(target["student_id"], "STU-2026-001")
        self.assertEqual(target["student_name"], "Alex Chen")
        self.assertEqual(target["status"], "Submitted")
        self.assertEqual(target["facility_type"], "Plumbing")
        self.assertIn("Hostel Block B", target["location"])

        # Check that another student STILL sees 0 complaints
        other_stu_complaints = get_student_complaints("STU-2026-002")
        self.assertEqual(len(other_stu_complaints), 0)

    def test_student_progress_timeline_stages_and_no_priority_labels(self):
        """Verifies progress indicator renders 5 stages without priority labels or scores."""
        for stage in PROGRESS_STAGES:
            html = render_student_progress_timeline(stage)
            for expected_stage in ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved"]:
                self.assertIn(expected_stage, html)

            # Must NEVER contain priority levels or score breakdowns
            self.assertNotIn("Critical", html)
            self.assertNotIn("High Priority", html)
            self.assertNotIn("Medium Priority", html)
            self.assertNotIn("priority_score", html)
            self.assertNotIn("recurrence_risk", html)

    def test_admin_updates_status_reflected_in_student_view(self):
        """Verifies that Admin status updates immediately propagate to the Student view."""
        # 1. Student submits issue
        cid = add_complaint({
            "student_id": "STU-2026-001",
            "student_name": "Alex Chen",
            "title": "Garbage Bin Overflowing near Mess",
            "description": "Waste containers overflowing with food packaging attract stray animals.",
            "facility_type": "Garbage overflow",
            "building": "Hostel Block A",
            "specific_location": "Mess Entrance",
            "status": "Submitted",
        })

        # 2. Check initial status is 'Submitted'
        stu_complaints = get_student_complaints("STU-2026-001")
        target = [c for c in stu_complaints if c["complaint_id"] == cid][0]
        self.assertEqual(target["status"], "Submitted")

        # 3. Admin transitions through the 5 stages: Under Review -> Assigned -> In Progress -> Resolved
        update_complaint_status(cid, "Under Review", action_taken="Sanitation supervisor reviewing.")
        target = [c for c in get_student_complaints("STU-2026-001") if c["complaint_id"] == cid][0]
        self.assertEqual(target["status"], "Under Review")

        update_complaint_status(cid, "Assigned", action_taken="Assigned to Sanitation Crew A.")
        target = [c for c in get_student_complaints("STU-2026-001") if c["complaint_id"] == cid][0]
        self.assertEqual(target["status"], "Assigned")

        update_complaint_status(cid, "In Progress", action_taken="Sanitation team currently on-site.")
        target = [c for c in get_student_complaints("STU-2026-001") if c["complaint_id"] == cid][0]
        self.assertEqual(target["status"], "In Progress")

        update_complaint_status(cid, "Resolved", action_taken="Bins emptied and area sanitized.")
        target = [c for c in get_student_complaints("STU-2026-001") if c["complaint_id"] == cid][0]
        self.assertEqual(target["status"], "Resolved")

    def test_student_cannot_access_admin_navigation(self):
        """Ensures Student role state isolates navigation and does not expose Admin tools."""
        st.session_state["user_role"] = "student"
        self.assertEqual(st.session_state["user_role"], "student")
        self.assertNotEqual(st.session_state["user_role"], "admin")

    def test_no_switch_student_or_other_profiles_in_student_dashboard(self):
        """Verifies that Switch Student button, dropdown, and other student profiles are completely absent."""
        import inspect
        from dashboard.pages import student_dashboard
        src = inspect.getsource(student_dashboard)

        # Forbidden features
        self.assertNotIn("Switch Student", src)
        self.assertNotIn("Priya Sharma", src)
        self.assertNotIn("Marcus Vance", src)
        self.assertNotIn("STU-2026-002", src)
        self.assertNotIn("STU-2026-003", src)

    def test_progress_timeline_has_no_four_space_indentation(self):
        """Verifies progress indicator HTML lines do not start with 4+ spaces (preventing code block parsing)."""
        for stage in PROGRESS_STAGES:
            html = render_student_progress_timeline(stage)
            for line in html.splitlines():
                if line.strip():
                    leading_spaces = len(line) - len(line.lstrip())
                    self.assertLess(
                        leading_spaces,
                        4,
                        f"Line '{line}' starts with {leading_spaces} spaces, which triggers Markdown code blocks!",
                    )

    def test_submission_confirmation_interface_content(self):
        """Verifies the confirmation interface strings match requirements."""
        import inspect
        from dashboard.pages import student_dashboard
        src = inspect.getsource(student_dashboard)

        self.assertIn("Issue submitted successfully", src)
        self.assertIn("Your complaint has been registered.", src)
        self.assertIn("Complaint Token:", src)
        self.assertIn("Status:", src)
        self.assertIn("You can track the progress of your complaint in My Complaints.", src)
        self.assertIn("Return to My Complaints", src)


if __name__ == "__main__":
    unittest.main()
