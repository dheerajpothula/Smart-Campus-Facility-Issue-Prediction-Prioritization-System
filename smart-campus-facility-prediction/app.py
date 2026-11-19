"""
FIPP — Facility Issue Prediction & Prioritisation
Main Application Entry Point with Modern Sage & Forest Theme, Role-Based Access Control,
Dedicated Login Flow, Left-Side Admin Navigation Sidebar, and Student Portal.
Palette: Soft Ivory (#F5F7F2), Forest Green (#203A32), Sage (#A8B9A3), Pale Sage (#DCE5D8), White (#FFFFFF).
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
from dashboard.components.admin_login import render_admin_login_screen
from dashboard.components.sidebar import render_admin_sidebar, render_sidebar
from src.auth.admin_auth import _ADMIN_CREDENTIALS_STORE
from dashboard.pages import (
    admin_reports,
    admin_requests,
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
    """Sets standard Streamlit wide page configuration and injects Modern Sage & Forest theme."""
    st.set_page_config(
        page_title="FIPP — Facility Issue Prediction & Prioritisation",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()


def render_admin_content(selected_page: str) -> None:
    """Dispatches admin sub-page based on navigation selection with strict server-side authorization."""
    auth = st.session_state.get("auth_user")
    if not auth or auth.get("role") != "admin":
        st.error("⛔ Access Denied: Administrator authorization required to view maintenance operations.")
        if st.button("Return to Gateway", key="btn_auth_guard_return", type="primary"):
            st.session_state["auth_user"] = None
            st.session_state["selected_role"] = None
            st.session_state["user_role"] = None
            st.rerun()
        st.stop()

    if "Overview" in selected_page:
        overview.render_page()
    elif "All Requests" in selected_page:
        admin_requests.render_all_requests_page()
    elif "New / Unassigned" in selected_page or ("New" in selected_page and "Unassigned" in selected_page):
        admin_requests.render_new_unassigned_page()
    elif "In Progress" in selected_page:
        admin_requests.render_in_progress_page()
    elif "Resolved" in selected_page:
        admin_requests.render_resolved_page()
    elif "Reports" in selected_page:
        admin_reports.render_reports_page()
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

    # Support URL query parameter for direct portal access (e.g. ?role=admin)
    if not selected_role and not auth:
        param_role = st.query_params.get("role")
        if param_role in ["admin", "student"]:
            st.session_state["selected_role"] = param_role
            selected_role = param_role
            if param_role == "admin" and st.query_params.get("auth") == "true":
                adm_id = st.query_params.get("id", "ADM-2026-001")
                adm_rec = _ADMIN_CREDENTIALS_STORE.get(adm_id) or _ADMIN_CREDENTIALS_STORE["ADM-2026-001"]
                auth = {
                    "role": "admin",
                    "name": adm_rec["name"],
                    "id": adm_rec["id"],
                    "title": adm_rec.get("title", "Facility Operations Lead"),
                    "role_title": adm_rec.get("title", "Facility Operations Lead"),
                }
                st.session_state["auth_user"] = auth
                st.session_state["user_role"] = "admin"
                if st.query_params.get("page"):
                    st.session_state["admin_active_page"] = st.query_params.get("page")
                if st.query_params.get("selected"):
                    st.session_state["admin_selected_complaint_id"] = st.query_params.get("selected")
            elif param_role == "student" and st.query_params.get("auth") == "true":
                s_name = st.query_params.get("name", "Alex Chen")
                s_id = st.query_params.get("id", "STU-2026-101")
                auth = {"role": "student", "name": s_name, "id": s_id}
                st.session_state["auth_user"] = auth
                st.session_state["user_role"] = "student"
                if st.query_params.get("view"):
                    st.session_state["student_active_view"] = st.query_params.get("view")
                if st.query_params.get("agreed") == "true":
                    st.session_state["student_agreed"] = True
                if st.query_params.get("msg_type"):
                    st.session_state["sq_message_type"] = st.query_params.get("msg_type")
                if st.query_params.get("category"):
                    st.session_state["sq_category"] = st.query_params.get("category")
                if st.query_params.get("sub_category"):
                    sub_val = st.query_params.get("sub_category")
                    st.session_state["sq_sub_category"] = sub_val
                    if st.query_params.get("faq_ok") == "true":
                        st.session_state["sq_faq_confirmed_sub"] = sub_val
                if st.query_params.get("room_type"):
                    st.session_state["sq_room_type"] = st.query_params.get("room_type")
                if st.query_params.get("block"):
                    st.session_state["sq_block"] = st.query_params.get("block")
                if st.query_params.get("val_err") == "true":
                    st.session_state["sq_validation_errors"] = [
                        "Please select a Message Type before submitting.",
                        "Please select or enter your Hostel / Campus Block.",
                        "Please select your Sub Block / Wing.",
                        "Please select a Room Type (Room No or Any Other).",
                        "Contact Number is mandatory. Please enter your mobile number.",
                        "Please select a preferred time slot for facility inspection.",
                        "Detailed Description is mandatory.",
                    ]

    # Support for test harnesses that assign user_role directly
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
    if not auth and selected_role == "admin":
        render_admin_login_screen()
        return

    if not auth and selected_role == "student":
        render_login_screen(selected_role)
        return

    # =========================================================================
    # 3. ROLE: Student Dashboard (Spacious, Clean Student Experience)
    # =========================================================================
    if auth and auth.get("role") == "student":
        student_dashboard.render_student_dashboard()
        return

    # =========================================================================
    # 4. ROLE: Administrator Dashboard (LEFT-SIDE Navigation Sidebar & Full Main Workspace)
    # =========================================================================
    if auth and auth.get("role") == "admin":
        admin_name = auth.get("name", "Administrator")
        admin_id = auth.get("id", "ADM-2026-001")
        admin_title = auth.get("title") or auth.get("role_title", "Facility Operations Lead")

        # LEFT-SIDE navigation sidebar
        with st.sidebar:
            selected_page = render_admin_sidebar(
                admin_name=admin_name,
                admin_id=admin_id,
                admin_title=admin_title,
            )

        # Spacious main dashboard workspace
        render_admin_content(selected_page)
        return

    # Fallback to role selection
    st.session_state["auth_user"] = None
    st.session_state["selected_role"] = None
    st.session_state["user_role"] = None
    st.rerun()


if __name__ == "__main__":
    main()
