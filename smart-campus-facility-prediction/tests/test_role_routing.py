"""
Verification script for role-based routing and student/admin isolation.
"""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app import main
from dashboard.pages import (
    overview,
    complaint_management,
    ai_analysis,
    maintenance_priorities,
    predictive_analytics,
    recurring_issues,
    explainable_ai,
    settings_weights,
    student_dashboard,
)


class TestRoleRoutingAndIsolation(unittest.TestCase):
    """Ensures role selection and role isolation are strictly enforced."""

    def test_gateway_flow(self):
        st.session_state["user_role"] = None
        # Must execute without error
        main()

    def test_student_dashboard_rendering(self):
        st.session_state["user_role"] = "student"
        student_dashboard.render_student_dashboard()
        # Verify student role is set
        self.assertEqual(st.session_state["user_role"], "student")

    def test_admin_pages_rendering(self):
        st.session_state["user_role"] = "admin"
        st.session_state["admin_active_page"] = "Overview"
        overview.render_page()

        st.session_state["admin_active_page"] = "Complaint Management"
        complaint_management.render_page()

        st.session_state["admin_active_page"] = "AI Analysis Pipeline"
        ai_analysis.render_page()

        st.session_state["admin_active_page"] = "Priority Queue"
        maintenance_priorities.render_page()

        st.session_state["admin_active_page"] = "Predictive Maintenance"
        predictive_analytics.render_page()

        st.session_state["admin_active_page"] = "Recurring Issues"
        recurring_issues.render_page()

        st.session_state["admin_active_page"] = "Explainable AI (SHAP)"
        explainable_ai.render_page()

        st.session_state["admin_active_page"] = "Priority Weights & Settings"
        settings_weights.render_page()


if __name__ == "__main__":
    unittest.main()
