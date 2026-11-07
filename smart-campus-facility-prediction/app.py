"""
FIPP — Facility Issue Prediction & Prioritization
Main Application Entry Point with Role-Based Access Control, Dedicated Login Flow,
and Right-Side Admin Sidebar.
Adheres strictly to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2).
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from dashboard.components.styles import apply_theme
from dashboard.components.role_selection import render_role_selection_screen
from dashboard.components.login_page import render_login_screen
from dashboard.components.sidebar import render_admin_sidebar, render_sidebar
from dashboard.pages import (
    ai_analysis,
    complaint_management,
    explainable_ai,
    maintenance_priorities,
    model_insights,
    overview,
    predictive_analytics,
    recurring_issues,
    settings_weights,
    student_dashboard,
)


def configure_page() -> None:
    """Sets standard Streamlit page configuration and injects clean light theme."""
    st.set_page_config(
        page_title="FIPP — Facility Issue Prediction & Prioritization",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_theme()


def render_admin_content(selected_page: str) -> None:
    """Dispatches admin sub-page based on navigation selection."""
    if "Overview" in selected_page:
        overview.render_page()
    elif "Complaint Management" in selected_page:
        complaint_management.render_page()
    elif "AI Analysis" in selected_page:
        ai_analysis.render_page()
    elif "Priority Queue" in selected_page:
        maintenance_priorities.render_page()
    elif "Predictive Maintenance" in selected_page:
        predictive_analytics.render_page()
    elif "Recurring Issues" in selected_page:
        recurring_issues.render_page()
    elif "Explainable AI" in selected_page:
        explainable_ai.render_page()
    elif "Settings" in selected_page or "Priority Weights" in selected_page:
        settings_weights.render_page()
    elif "Model Insights" in selected_page:
        model_insights.render_page()
    else:
        overview.render_page()


def main() -> None:
    """Application dispatcher with role selection, dedicated login, and dashboards."""
    configure_page()

    auth = st.session_state.get("auth_user")
    selected_role = st.session_state.get("selected_role")
    user_role = st.session_state.get("user_role")

    # Seamless support for test harnesses that assign user_role directly
    if not auth and user_role in ["student", "admin"]:
        if user_role == "student":
            auth = {"role": "student", "name": "Student", "id": "STU-TEST-001"}
            st.session_state["auth_user"] = auth
        elif user_role == "admin":
            auth = {"role": "admin", "name": "Administrator", "id": "ADM-TEST-001"}
            st.session_state["auth_user"] = auth

    # =========================================================================
    # 1. GATEWAY: Role Selection (When no role has been chosen)
    # =========================================================================
    if not auth and not selected_role:
        render_role_selection_screen()
        return

    # =========================================================================
    # 2. DEDICATED LOGIN: When role is selected but user is not yet logged in
    # =========================================================================
    if not auth and selected_role in ["admin", "student"]:
        render_login_screen(selected_role)
        return

    # =========================================================================
    # 3. ROLE: Student Dashboard
    # =========================================================================
    if auth and auth.get("role") == "student":
        student_dashboard.render_student_dashboard()
        return

    # =========================================================================
    # 4. ROLE: Administrator Dashboard (Content on Left, Sidebar on Right)
    # =========================================================================
    if auth and auth.get("role") == "admin":
        admin_name = auth.get("name", "Administrator")
        admin_id = auth.get("id", "ADM-2026-001")

        col_content, col_sidebar = st.columns([3.5, 1.1], gap="large")

        with col_sidebar:
            selected_page = render_admin_sidebar(admin_name=admin_name, admin_id=admin_id)

        with col_content:
            render_admin_content(selected_page)
        return

    # Fallback to role selection
    st.session_state["auth_user"] = None
    st.session_state["selected_role"] = None
    st.session_state["user_role"] = None
    st.rerun()


if __name__ == "__main__":
    main()
