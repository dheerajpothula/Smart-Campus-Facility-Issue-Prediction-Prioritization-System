"""
Student Dashboard View.
Provides a clean, modern SaaS interface for students to view their submitted complaints
and raise new facility tickets with automated sequential token generation, strict data isolation,
and 5-stage progress tracking.
Adheres strictly to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2).
"""
import time
from datetime import datetime
import streamlit as st
import pandas as pd

from dashboard.components.styles import get_status_badge, render_student_progress_timeline, _clean_html
from src.data.complaints_store import (
    get_complaints_df,
    get_student_complaints,
    add_complaint,
    get_current_student_identity,
)

FACILITY_CATEGORIES = [
    "Washroom cleanliness",
    "Garbage overflow",
    "Water cooler or water supply",
    "Electrical or lighting issues",
    "Plumbing",
    "Other maintenance issues",
]

CAMPUS_BUILDINGS = [
    "Hostel Block A",
    "Hostel Block B",
    "Hostel Block C",
    "Academic Block 1",
    "Academic Block 2",
    "Academic Block 3 (Data Science)",
    "Central Library",
    "Science Complex & Labs",
    "Student Cafeteria",
    "Sports Complex & Gym",
    "Administrative Block",
    "Campus Grounds / Parking",
]


def render_student_dashboard() -> None:
    """Renders the dedicated, student-friendly facility status and issue submission portal."""
    # 1. Identity & Session Setup (Dynamic session-authenticated identity)
    trusted_student = get_current_student_identity()
    active_student_id = trusted_student.get("student_id")
    active_student_name = trusted_student.get("student_name")

    # Guard against unauthenticated direct access
    if not active_student_id:
        st.warning("No authenticated student session found. Please log in through the role selection portal.")
        if st.button("Return to Login", key="btn_no_auth_login", type="secondary"):
            st.session_state["user_role"] = None
            st.session_state["selected_role"] = "student"
            st.session_state["auth_user"] = None
            st.rerun()
        return

    if "show_raise_issue_form" not in st.session_state:
        st.session_state["show_raise_issue_form"] = False

    # Top Header & Primary Action Bar
    header_col1, header_col2 = st.columns([3, 1.2])

    with header_col1:
        st.markdown(
            _clean_html(
                f"""
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background-color: #EAE3D2; border: 1px solid #D8CFBD; display: flex; align-items: center; justify-content: center; font-size: 1.45rem;">
                🎓
                </div>
                <div>
                <h1 style="margin: 0; font-size: 1.65rem; color: #1A1A1A; font-weight: 700;">
                Student Facility Portal
                </h1>
                <p style="margin: 0; color: #555555; font-size: 0.88rem;">
                Logged in as: <strong>{active_student_name}</strong> (ID: <code>{active_student_id}</code>)
                </p>
                </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with header_col2:
        st.markdown("<div style='text-align: right; padding-top: 0.2rem;'>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns([1.6, 1])
        with btn_c1:
            btn_label = "Close Form" if st.session_state["show_raise_issue_form"] else "Raise an Issue"
            btn_type = "secondary" if st.session_state["show_raise_issue_form"] else "primary"
            if st.button(btn_label, key="btn_toggle_raise_issue", type=btn_type, use_container_width=True):
                st.session_state["show_raise_issue_form"] = not st.session_state["show_raise_issue_form"]
                # Close confirmation if opening form
                if "submission_confirmation" in st.session_state:
                    del st.session_state["submission_confirmation"]
                st.rerun()
        with btn_c2:
            if st.button("Logout", key="btn_student_logout", type="secondary", use_container_width=True):
                st.session_state["auth_user"] = None
                st.session_state["selected_role"] = None
                st.session_state["user_role"] = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # 2. SUBMISSION SUCCESS CONFIRMATION INTERFACE (Dedicated View)
    # =========================================================================
    if "submission_confirmation" in st.session_state:
        conf = st.session_state["submission_confirmation"]
        conf_token = conf.get("token", "CMP-2026-001")
        conf_status = conf.get("status", "Submitted")
        conf_status_badge = get_status_badge(conf_status)

        st.markdown(
            _clean_html(
                f"""
                <div class="dashboard-card" style="text-align: center; padding: 2.5rem 2rem; max-width: 650px; margin: 1.5rem auto; border: 1px solid #EAE3D2;">
                <div style="width: 64px; height: 64px; line-height: 64px; border-radius: 50%; background-color: #EAE3D2; border: 2px solid #D8CFBD; font-size: 2rem; color: #1A1A1A; margin: 0 auto 1.25rem auto;">
                ✓
                </div>
                <h2 style="color: #1A1A1A; font-size: 1.55rem; font-weight: 700; margin-bottom: 0.35rem;">
                Issue submitted successfully
                </h2>
                <p style="color: #4A4A4A; font-size: 1.05rem; margin-bottom: 1.5rem;">
                Your complaint has been registered.
                </p>
                <div style="background-color: #FDFBF7; border: 1px solid #EAE3D2; border-radius: 10px; padding: 1.25rem 1.5rem; margin: 0 auto 1.5rem auto; text-align: left; max-width: 420px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 0.92rem; color: #555555; font-weight: 500;">Complaint Token:</span>
                <span style="font-family: monospace; font-size: 1.05rem; font-weight: 700; color: #1A1A1A; background-color: #EAE3D2; padding: 0.2rem 0.6rem; border-radius: 6px; border: 1px solid #D8CFBD;">
                {conf_token}
                </span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.92rem; color: #555555; font-weight: 500;">Status:</span>
                {conf_status_badge}
                </div>
                </div>
                <p style="color: #555555; font-size: 0.95rem; margin-bottom: 1.75rem;">
                You can track the progress of your complaint in My Complaints.
                </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        _, col_ret, _ = st.columns([1, 1.4, 1])
        with col_ret:
            if st.button("Return to My Complaints", key="btn_return_from_confirmation", type="primary", use_container_width=True):
                del st.session_state["submission_confirmation"]
                st.rerun()
        return

    # =========================================================================
    # 3. RAISE AN ISSUE FORM (EXACTLY 7 FIELDS, NO RED ASTERISKS)
    # =========================================================================
    if st.session_state["show_raise_issue_form"]:
        st.markdown(
            _clean_html(
                """
                <div style="background-color: #FFFFFF; border: 1px solid #EAE3D2; border-radius: 12px; padding: 1.5rem 1.6rem; box-shadow: 0 4px 6px -1px rgba(26, 26, 26, 0.04); margin-bottom: 2rem;">
                <div style="margin-bottom: 1rem;">
                <span style="background-color: #EAE3D2; color: #1A1A1A; border: 1px solid #D8CFBD; font-size: 0.74rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em;">
                New Complaint
                </span>
                <h2 style="margin: 0.35rem 0 0 0; font-size: 1.35rem; color: #1A1A1A; font-weight: 700;">
                Submit a Campus Facility Issue
                </h2>
                <p style="color: #555555; font-size: 0.88rem; margin: 0.3rem 0 0 0;">
                Fill in the details below. Required fields are validated upon submission.
                </p>
                </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        with st.form("form_student_raise_issue", clear_on_submit=False):
            # Row 1: Student Name & Student ID (Fields 1 & 2 - Bound to authenticated session, non-editable)
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.text_input(
                    "Student Name",
                    value=active_student_name,
                    disabled=True,
                    help="Auto-filled from your authenticated student session.",
                )
            with c_f2:
                st.text_input(
                    "Student ID",
                    value=active_student_id,
                    disabled=True,
                    help="Auto-filled from your authenticated student session.",
                )

            # Row 2: Issue Title & Facility Category (Fields 3 & 4)
            c_f3, c_f4 = st.columns(2)
            with c_f3:
                issue_title = st.text_input(
                    "Issue Title / Brief Headline",
                    placeholder="e.g., Water leak under sink in 2nd floor washroom",
                    help="Summarize the core problem concisely.",
                )
            with c_f4:
                facility_category = st.selectbox(
                    "Facility Category",
                    options=FACILITY_CATEGORIES,
                    index=0,
                    help="Select the infrastructure domain that matches the breakdown.",
                )

            # Row 3: Building or Block & Floor or Specific Location (Fields 5 & 6)
            c_f5, c_f6 = st.columns(2)
            with c_f5:
                building_block = st.selectbox(
                    "Building or Block",
                    options=CAMPUS_BUILDINGS,
                    index=0,
                    help="Select campus facility or hostel building.",
                )
            with c_f6:
                specific_location = st.text_input(
                    "Floor or Specific Location",
                    placeholder="e.g., Room 302, 2nd Floor Corridor, Block A Washroom",
                    help="Provide room number, corridor, or wing details so technicians can locate it.",
                )

            # Row 4: Detailed Issue Description (Field 7)
            issue_description = st.text_area(
                "Detailed Issue Description",
                placeholder="Explain the problem clearly: when it started, symptoms observed, and how it impacts residents...",
                help="Include physical symptoms, hazard risks, or affected fixtures.",
                height=110,
            )

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            # Action Buttons: Submit Issue & Cancel
            sub_col1, sub_col2, _ = st.columns([1.4, 1.2, 3])
            with sub_col1:
                submit_button = st.form_submit_button("Submit Issue", type="primary", use_container_width=True)
            with sub_col2:
                cancel_button = st.form_submit_button("Cancel", type="secondary", use_container_width=True)

            if cancel_button:
                st.session_state["show_raise_issue_form"] = False
                st.rerun()

            if submit_button:
                # Validation of required fields
                validation_errors = []
                if not issue_title.strip():
                    validation_errors.append("Please enter an issue title or brief headline.")
                if not specific_location.strip():
                    validation_errors.append("Please specify the floor or specific location.")
                if not issue_description.strip() or len(issue_description.strip()) < 5:
                    validation_errors.append("Please provide a detailed issue description.")

                if validation_errors:
                    for err in validation_errors:
                        st.error(f"⚠️ {err}")
                else:
                    # Subtle loading state during submission
                    with st.spinner("Submitting complaint and generating token..."):
                        time.sleep(0.2)

                    # Bind directly to server-side authenticated identity
                    new_ticket = {
                        "student_id": active_student_id,
                        "student_name": active_student_name,
                        "title": issue_title.strip(),
                        "description": issue_description.strip(),
                        "facility_type": facility_category,
                        "building": building_block,
                        "specific_location": specific_location.strip(),
                        "reported_by": active_student_name,
                        "status": "Submitted",
                    }

                    try:
                        # Add to store (assigns sequential CMP-2026-XXX token and saves to disk)
                        created_token = add_complaint(new_ticket)

                        if created_token and created_token.startswith("CMP-2026-"):
                            st.session_state["show_raise_issue_form"] = False
                            st.session_state["submission_confirmation"] = {
                                "token": created_token,
                                "status": "Submitted",
                            }
                            st.rerun()
                        else:
                            st.error("Failed to generate a valid complaint token. Please retry.")
                    except Exception as exc:
                        st.error(f"Complaint registration failed: {exc}. Please retry.")

    # =========================================================================
    # 4. MY COMPLAINTS — STRICTLY RETRIEVED BY AUTHENTICATED STUDENT ID
    # =========================================================================
    st.markdown(
        _clean_html(
            """
            <div style="margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 1.35rem; color: #1A1A1A; font-weight: 700;">
            My Complaints
            </h2>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # Backend retrieval strictly scoped to authenticated student ID
    student_complaints_list = get_student_complaints(active_student_id)

    # Clean empty state when no complaints exist for this student
    if not student_complaints_list:
        st.markdown(
            _clean_html(
                """
                <div class="dashboard-card" style="text-align: center; padding: 3rem 2rem; margin: 1.5rem 0;">
                <div style="width: 56px; height: 56px; line-height: 56px; border-radius: 16px; background-color: #EAE3D2; border: 1px solid #D8CFBD; font-size: 1.8rem; margin: 0 auto 1.25rem auto;">
                📋
                </div>
                <h3 style="color: #1A1A1A; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem;">
                No complaints submitted yet.
                </h3>
                <p style="color: #555555; font-size: 0.95rem; max-width: 450px; margin: 0 auto 1.5rem auto; line-height: 1.5;">
                Raise an issue to report a facility problem on campus.
                </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        col_empty_btn, _ = st.columns([1.5, 4])
        with col_empty_btn:
            if st.button("➕ Raise an Issue", key="btn_empty_raise_issue", type="primary", use_container_width=True):
                st.session_state["show_raise_issue_form"] = True
                st.rerun()
        return

    # Render each student complaint card (clean, spacious, NO priority labels/ML scores, 5-stage progress indicator)
    for item in student_complaints_list:
        cid = item.get("complaint_id", "CMP-2026-000")
        fac = item.get("facility_type", "General")
        title = item.get("title", "Facility Issue")
        desc = item.get("description", "")
        status = item.get("status", "Submitted")
        s_badge = get_status_badge(status)
        loc = item.get("location", "Campus")
        date_rep = item.get("date_reported", "Recently")
        est_res = item.get("estimated_resolution")
        est_res_text = f"<span>⏱️ <strong>Est. Resolution:</strong> <span style='color: #1A1A1A; font-weight: 600;'>{est_res}</span></span>" if est_res else ""

        progress_indicator_html = render_student_progress_timeline(status)

        # Card rendered with zero-indented HTML to prevent Markdown parser from converting HTML into code blocks
        card_html = _clean_html(
            f"""
            <div class="dashboard-card" style="margin-bottom: 1.25rem; padding: 1.4rem 1.6rem; border: 1px solid #EAE3D2;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
            <div>
            <span style="font-family: monospace; font-size: 0.82rem; font-weight: 700; color: #1A1A1A; background-color: #EAE3D2; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #D8CFBD;">
            {cid}
            </span>
            <span style="font-size: 0.76rem; font-weight: 600; color: #1A1A1A; background-color: #F6F3EB; padding: 0.2rem 0.55rem; border-radius: 6px; margin-left: 0.4rem; border: 1px solid #EAE3D2;">
            {fac}
            </span>
            <h3 style="margin: 0.5rem 0 0 0; color: #1A1A1A; font-size: 1.15rem; font-weight: 700;">
            {title}
            </h3>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 0.8rem; color: #555555; font-weight: 500;">Status:</span>
            {s_badge}
            </div>
            </div>
            {progress_indicator_html}
            <p style="color: #2D2D2D; font-size: 0.92rem; margin: 0.85rem 0 0.85rem 0; line-height: 1.55;">
            {desc}
            </p>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #EAE3D2; padding-top: 0.75rem; font-size: 0.82rem; color: #555555; flex-wrap: wrap; gap: 0.75rem;">
            <div>
            📍 <strong>Location:</strong> {loc}
            </div>
            <div style="display: flex; gap: 1.5rem; align-items: center;">
            <span>📅 <strong>Reported:</strong> {date_rep}</span>
            {est_res_text}
            </div>
            </div>
            </div>
            """
        )

        st.markdown(card_html, unsafe_allow_html=True)

    # Campus resident notice footer
    st.markdown(
        _clean_html(
            """
            <div style="background-color: #FFFFFF; border: 1px dashed #D8CFBD; border-radius: 8px; padding: 0.85rem 1.1rem; margin-top: 1.5rem; text-align: center; font-size: 0.82rem; color: #555555;">
            💡 Need immediate assistance for an emergency? Contact your hostel warden or campus security desk.
            Campus facility updates and maintenance dispatches are tracked directly in this portal.
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
