"""
FIPP 2.0 — Student Facility Dashboard.
Implements the notebook sketch layout:
1. Clean horizontal header with FIPP logo/title on left, Home option on right.
2. Main Dashboard with two prominent, equal-sized options: 'Raise a Query' and 'History'.
3. Student Declaration section with two mandatory checkboxes and dynamically enabled 'Agree & Proceed' button.
4. Access to Complaint Portal (Raise a Query with 7 fields + optional photo upload, unique token generation CMP-2026-XXX)
   and History page with strict student data isolation.
5. Modern Sage & Forest Theme:
   - Soft Ivory: #F5F7F2
   - Forest Green: #203A32
   - Sage: #A8B9A3
   - Pale Sage: #DCE5D8
   - White: #FFFFFF
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
    """
    Renders the dedicated Student Facility Interface based on the hand-drawn design:
    - Horizontal Header: FIPP logo & full title on left, Home option on right.
    - Main Dashboard Hub: Two prominent equal-sized cards for 'Raise a Query' and 'History'.
    - Mandatory Student Declaration with two checkboxes; 'Agree & Proceed' enabled only when both are checked.
    - Portal Views: Raise a Query (with 7 validated fields + optional photo upload) & History (isolated to current student).
    """
    # Hide sidebar when in student mode for a clean, distraction-free widescreen view
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        .block-container {
            max-width: 1200px !important;
            margin: 0 auto !important;
            padding-top: 1.25rem !important;
            padding-bottom: 3.5rem !important;
        }
        .stCheckbox label p {
            color: #203A32 !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    # Initialize Student session state attributes
    if "student_agreed" not in st.session_state:
        st.session_state["student_agreed"] = False
    if "student_selected_option" not in st.session_state:
        st.session_state["student_selected_option"] = "raise"
    if "student_active_view" not in st.session_state:
        st.session_state["student_active_view"] = None
    if "chk_declaration_responsible" not in st.session_state:
        st.session_state["chk_declaration_responsible"] = False
    if "chk_declaration_truthful" not in st.session_state:
        st.session_state["chk_declaration_truthful"] = False

    # Count existing complaints for this student
    student_complaints_all = get_student_complaints(active_student_id)
    complaint_count = len(student_complaints_all)

    # =========================================================================
    # 1. CLEAN HORIZONTAL HEADER
    # - FIPP logo & full title on left.
    # - Home option on right.
    # =========================================================================
    col_hdr_left, col_hdr_right = st.columns([3.2, 1.3])

    with col_hdr_left:
        st.markdown(
            _clean_html(
                """
                <div style="display: flex; align-items: center; gap: 0.95rem; padding: 0.25rem 0;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background-color: #DCE5D8; border: 1.5px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 1.65rem; box-shadow: 0 2px 6px rgba(32, 58, 50, 0.05);">
                        🏫
                    </div>
                    <div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #203A32; letter-spacing: -0.025em; line-height: 1.2;">
                            FIPP
                        </div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #4A6357;">
                            Facility Issue Prediction &amp; Prioritisation System
                        </div>
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with col_hdr_right:
        st.markdown("<div style='text-align: right; padding-top: 0.25rem;'>", unsafe_allow_html=True)
        col_btn_home, col_btn_logout = st.columns([1, 1])
        with col_btn_home:
            if st.button("Home", key="btn_student_hdr_home", type="secondary", use_container_width=True):
                st.session_state["selected_role"] = None
                st.session_state["auth_user"] = None
                st.session_state["user_role"] = None
                st.session_state["student_agreed"] = False
                st.session_state["student_active_view"] = None
                st.rerun()
        with col_btn_logout:
            if st.button("Logout", key="btn_student_hdr_logout", type="secondary", use_container_width=True):
                st.session_state["selected_role"] = None
                st.session_state["auth_user"] = None
                st.session_state["user_role"] = None
                st.session_state["student_agreed"] = False
                st.session_state["student_active_view"] = None
                st.rerun()

        st.markdown(
            f"""<div style='font-size: 0.8rem; color: #6D8276; margin-top: 0.35rem; text-align: right;'>
                Student: <strong>{active_student_name}</strong> (<code style='background: #DCE5D8; color: #203A32; padding: 0.1rem 0.35rem; border-radius: 4px;'>{active_student_id}</code>)
            </div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 0.75rem 0 1.75rem 0; border: none; border-top: 1px solid #DCE5D8;'/>", unsafe_allow_html=True)

    # =========================================================================
    # 2. SUBMISSION SUCCESS CONFIRMATION VIEW (If a ticket was just submitted)
    # =========================================================================
    if "submission_confirmation" in st.session_state:
        conf = st.session_state["submission_confirmation"]
        conf_token = conf.get("token", "CMP-2026-001")
        conf_status = conf.get("status", "Submitted")
        conf_status_badge = get_status_badge(conf_status)

        st.markdown(
            _clean_html(
                f"""
                <div class="dashboard-card" style="text-align: center; padding: 2.75rem 2rem; max-width: 680px; margin: 1.5rem auto; border-top: 4px solid #203A32; border-radius: 14px; background: #FFFFFF; box-shadow: 0 4px 16px rgba(32, 58, 50, 0.06);">
                    <div style="width: 64px; height: 64px; line-height: 64px; border-radius: 50%; background-color: #DCE5D8; border: 2px solid #A8B9A3; font-size: 2rem; color: #203A32; margin: 0 auto 1.25rem auto;">
                        ✓
                    </div>
                    <h2 style="color: #203A32; font-size: 1.6rem; font-weight: 800; margin-bottom: 0.35rem; letter-spacing: -0.02em;">
                        Issue submitted successfully
                    </h2>
                    <p style="color: #4A6357; font-size: 1rem; margin-bottom: 1.5rem;">
                        Your complaint has been registered.
                    </p>
                    <div style="background-color: #F5F7F2; border: 1px solid #DCE5D8; border-radius: 12px; padding: 1.35rem 1.6rem; margin: 0 auto 1.5rem auto; text-align: left; max-width: 440px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem;">
                            <span style="font-size: 0.95rem; color: #4A6357; font-weight: 600;">Complaint Token:</span>
                            <span style="font-family: monospace; font-size: 1.1rem; font-weight: 800; color: #203A32; background-color: #DCE5D8; padding: 0.25rem 0.65rem; border-radius: 6px; border: 1px solid #A8B9A3;">
                                {conf_token}
                            </span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.95rem; color: #4A6357; font-weight: 600;">Status:</span>
                            {conf_status_badge}
                        </div>
                    </div>
                    <p style="color: #6D8276; font-size: 0.9rem; margin-bottom: 1.75rem;">
                        You can track the progress of your complaint in My Complaints.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        col_c1, col_c2, col_c3 = st.columns([1, 1.4, 1])
        with col_c2:
            c_ret_hist, c_ret_raise = st.columns(2)
            with c_ret_hist:
                if st.button("Return to My Complaints", key="btn_conf_view_history", type="primary", use_container_width=True):
                    del st.session_state["submission_confirmation"]
                    st.session_state["student_active_view"] = "history"
                    st.rerun()
            with c_ret_raise:
                if st.button("Raise Another Query", key="btn_conf_raise_another", type="secondary", use_container_width=True):
                    del st.session_state["submission_confirmation"]
                    st.session_state["student_active_view"] = "raise"
                    st.rerun()
        return

    # =========================================================================
    # 3. MAIN DASHBOARD HUB & DECLARATION VIEW (Initial state before Proceed)
    # =========================================================================
    if not st.session_state.get("student_agreed") or not st.session_state.get("student_active_view"):
        current_sel = st.session_state.get("student_selected_option", "raise")

        st.markdown(
            _clean_html(
                """
                <div style="text-align: center; max-width: 820px; margin: 0 auto 2.25rem auto;">
                    <h2 style="font-size: 1.85rem; color: #203A32; font-weight: 800; margin: 0 0 0.45rem 0; letter-spacing: -0.025em;">
                        Student Facility Dashboard
                    </h2>
                    <p style="color: #4A6357; font-size: 0.96rem; margin: 0;">
                        Select an option below to submit a new campus facility query or review your complaint tracking history.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        # Two prominent equal-sized options in the centre
        col_card_raise, col_card_hist = st.columns(2, gap="large")

        # Visual highlights based on selected option
        border_raise = "border: 2px solid #203A32; box-shadow: 0 8px 24px rgba(32, 58, 50, 0.08);" if current_sel == "raise" else "border: 1px solid #DCE5D8;"
        border_hist = "border: 2px solid #203A32; box-shadow: 0 8px 24px rgba(32, 58, 50, 0.08);" if current_sel == "history" else "border: 1px solid #DCE5D8;"

        with col_card_raise:
            st.markdown(
                _clean_html(
                    f"""
                    <div class="dashboard-card" style="padding: 2.5rem 2.2rem 1.8rem 2.2rem; {border_raise} border-top: 4px solid #203A32; border-radius: 16px; background: #FFFFFF; min-height: 230px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0.75rem;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
                                <div style="width: 58px; height: 58px; border-radius: 14px; background-color: #DCE5D8; border: 1.5px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 2rem; box-shadow: 0 2px 6px rgba(32, 58, 50, 0.05);">
                                    💬
                                </div>
                                {'<span style="font-size: 0.74rem; font-weight: 700; color: #203A32; background: #DCE5D8; padding: 0.2rem 0.55rem; border-radius: 9999px; text-transform: uppercase; border: 1px solid #A8B9A3;">Selected</span>' if current_sel == 'raise' else ''}
                            </div>
                            <h3 style="font-size: 1.4rem; font-weight: 750; color: #203A32; margin: 0 0 0.55rem 0;">
                                Raise a Query
                            </h3>
                            <p style="color: #4A6357; font-size: 0.94rem; line-height: 1.55; margin: 0;">
                                Report a campus facility problem, equipment breakdown, hygiene issue, or maintenance request.
                            </p>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            btn_raise_type = "primary" if current_sel == "raise" else "secondary"
            btn_raise_label = "✓ Selected: Raise a Query" if current_sel == "raise" else "Select: Raise a Query"
            if st.button(btn_raise_label, key="btn_sel_raise_opt", type=btn_raise_type, use_container_width=True):
                st.session_state["student_selected_option"] = "raise"
                st.rerun()

        with col_card_hist:
            st.markdown(
                _clean_html(
                    f"""
                    <div class="dashboard-card" style="padding: 2.5rem 2.2rem 1.8rem 2.2rem; {border_hist} border-top: 4px solid #A8B9A3; border-radius: 16px; background: #FFFFFF; min-height: 230px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0.75rem;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
                                <div style="width: 58px; height: 58px; border-radius: 14px; background-color: #DCE5D8; border: 1.5px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 2rem; box-shadow: 0 2px 6px rgba(32, 58, 50, 0.05);">
                                    🕒
                                </div>
                                {'<span style="font-size: 0.74rem; font-weight: 700; color: #203A32; background: #DCE5D8; padding: 0.2rem 0.55rem; border-radius: 9999px; text-transform: uppercase; border: 1px solid #A8B9A3;">Selected</span>' if current_sel == 'history' else ''}
                            </div>
                            <h3 style="font-size: 1.4rem; font-weight: 750; color: #203A32; margin: 0 0 0.55rem 0;">
                                History
                            </h3>
                            <p style="color: #4A6357; font-size: 0.94rem; line-height: 1.55; margin: 0;">
                                Track and view your previous complaints ({complaint_count} registered), status updates, and progress timelines.
                            </p>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            btn_hist_type = "primary" if current_sel == "history" else "secondary"
            btn_hist_label = "✓ Selected: History" if current_sel == "history" else "Select: History"
            if st.button(btn_hist_label, key="btn_sel_hist_opt", type=btn_hist_type, use_container_width=True):
                st.session_state["student_selected_option"] = "history"
                st.rerun()

        # =====================================================================
        # STUDENT DECLARATION SECTION
        # - Two mandatory checkboxes (initially unchecked)
        # - 'Agree & Proceed' button disabled initially; enabled only when both are checked
        # =====================================================================
        st.markdown(
            _clean_html(
                """
                <div class="dashboard-card" style="padding: 2.2rem 2.4rem 1.6rem 2.4rem; border-top: 4px solid #203A32; border-radius: 16px; background: #FFFFFF; box-shadow: 0 4px 16px rgba(32, 58, 50, 0.05); margin-top: 2.25rem; margin-bottom: 1.25rem;">
                    <div style="display: flex; align-items: center; gap: 0.85rem; margin-bottom: 0.75rem;">
                        <div style="width: 42px; height: 42px; border-radius: 12px; background-color: #DCE5D8; border: 1px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 1.45rem;">
                            📋
                        </div>
                        <div>
                            <h3 style="margin: 0; font-size: 1.3rem; color: #203A32; font-weight: 750;">
                                Student Declaration
                            </h3>
                            <p style="margin: 0; color: #4A6357; font-size: 0.88rem;">
                                Please review and accept the official student undertaking before proceeding to the portal.
                            </p>
                        </div>
                    </div>
                    <div style="height: 1px; background-color: #DCE5D8; margin: 1rem 0 1.25rem 0;"></div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        _, col_decl_inner, _ = st.columns([0.2, 5.6, 0.2])
        with col_decl_inner:
            # Checkbox 1
            cb_responsible = st.checkbox(
                "I am responsible for the content typed in my query.",
                value=st.session_state.get("chk_declaration_responsible", False),
                key="chk_declaration_responsible",
                help="Mandatory student confirmation of content accountability.",
            )

            # Checkbox 2
            cb_truthful = st.checkbox(
                "The information given by me regarding the complaint/request is true to the best of my knowledge.",
                value=st.session_state.get("chk_declaration_truthful", False),
                key="chk_declaration_truthful",
                help="Mandatory student affirmation of accurate and factual problem reporting.",
            )

            both_checked = bool(cb_responsible and cb_truthful)

            st.markdown("<div style='height: 0.85rem;'></div>", unsafe_allow_html=True)

            col_btn_agree, col_btn_help = st.columns([2, 3])
            with col_btn_agree:
                # Agree & Proceed button disabled unless both checkboxes are selected
                btn_proceed = st.button(
                    "Agree & Proceed",
                    key="btn_agree_and_proceed",
                    type="primary",
                    disabled=not both_checked,
                    use_container_width=True,
                )

            with col_btn_help:
                if not both_checked:
                    st.markdown(
                        """<div style='padding-top: 0.55rem; color: #6D8276; font-size: 0.84rem;'>
                            ⚠️ <em>Please check both declarations above to enable the Agree &amp; Proceed button.</em>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    target_label = "Raise a Query" if current_sel == "raise" else "Complaint History"
                    st.markdown(
                        f"""<div style='padding-top: 0.55rem; color: #203A32; font-size: 0.86rem; font-weight: 600;'>
                            ✓ Declarations accepted. Ready to proceed to <strong>{target_label}</strong>.
                        </div>""",
                        unsafe_allow_html=True,
                    )

            if btn_proceed:
                if not both_checked:
                    st.error("Access Denied: You must check both declaration checkboxes before proceeding.")
                else:
                    st.session_state["student_agreed"] = True
                    st.session_state["student_active_view"] = st.session_state.get("student_selected_option", "raise")
                    st.rerun()

        # Footer note
        st.markdown(
            """
            <div style="text-align: center; margin-top: 3.5rem; color: #6D8276; font-size: 0.82rem;">
                FIPP 2.0 • University Facility Management Portal • Modern Sage &amp; Forest Architecture
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # =========================================================================
    # 4. AUTHORIZED STUDENT PORTAL (After Agree & Proceed)
    # Allows switching between 'Raise a Query' and 'History'
    # =========================================================================
    active_view = st.session_state.get("student_active_view", "raise")

    # Portal Section Sub-Navigation
    col_nav1, col_nav2, col_nav3 = st.columns([1.6, 1.6, 1.4])

    with col_nav1:
        btn_view_raise_type = "primary" if active_view == "raise" else "secondary"
        if st.button("💬 Raise a Query", key="btn_nav_to_raise", type=btn_view_raise_type, use_container_width=True):
            st.session_state["student_active_view"] = "raise"
            st.rerun()

    with col_nav2:
        btn_view_hist_type = "primary" if active_view == "history" else "secondary"
        if st.button(f"🕒 History ({complaint_count})", key="btn_nav_to_history", type=btn_view_hist_type, use_container_width=True):
            st.session_state["student_active_view"] = "history"
            st.rerun()

    with col_nav3:
        if st.button("← Main Dashboard", key="btn_nav_back_hub", type="secondary", use_container_width=True):
            st.session_state["student_active_view"] = None
            st.rerun()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # VIEW A: RAISE A QUERY FORM
    # Contains: Student Name, Student ID, Issue Title, Facility Category,
    # Building or Block, Floor or Specific Location, Detailed Issue Description,
    # and Optional photo upload.
    # -------------------------------------------------------------------------
    if active_view == "raise":
        st.markdown(
            _clean_html(
                """
                <div style="background-color: #FFFFFF; border: 1px solid #DCE5D8; border-top: 4px solid #203A32; border-radius: 14px; padding: 1.6rem 2rem; box-shadow: 0 4px 16px rgba(32, 58, 50, 0.05); margin-bottom: 1.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <span style="background-color: #DCE5D8; color: #203A32; border: 1px solid #A8B9A3; font-size: 0.74rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em;">
                                New Query
                            </span>
                            <h2 style="margin: 0.4rem 0 0 0; font-size: 1.45rem; color: #203A32; font-weight: 750;">
                                Submit a Campus Facility Query
                            </h2>
                            <p style="color: #4A6357; font-size: 0.9rem; margin: 0.25rem 0 0 0;">
                                Provide accurate details regarding the facility breakdown. Required fields are validated upon submission.
                            </p>
                        </div>
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        with st.form("form_student_raise_issue", clear_on_submit=False):
            # Row 1: Student Name & Student ID (Non-editable, bound to authenticated session)
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

            # Row 2: Issue Title & Facility Category
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
                    help="Select the campus facility domain matching the issue.",
                )

            # Row 3: Building or Block & Floor or Specific Location
            c_f5, c_f6 = st.columns(2)
            with c_f5:
                building_block = st.selectbox(
                    "Building or Block",
                    options=CAMPUS_BUILDINGS,
                    index=0,
                    help="Select the campus building, block, or facility zone.",
                )
            with c_f6:
                specific_location = st.text_input(
                    "Floor or Specific Location",
                    placeholder="e.g., Room 302, 2nd Floor Corridor, Block A Washroom",
                    help="Provide room number, corridor, or wing details so maintenance technicians can locate it.",
                )

            # Row 4: Detailed Issue Description
            issue_description = st.text_area(
                "Detailed Issue Description",
                placeholder="Explain the problem clearly: when it started, observed symptoms, physical hazards, and impact on students...",
                help="Include physical symptoms, hazard risks, or affected fixtures.",
                height=110,
            )

            # Row 5: Optional Photo Upload
            photo_file = st.file_uploader(
                "Upload Issue Photo (Optional)",
                type=["png", "jpg", "jpeg"],
                help="Attach a photograph of the maintenance problem (optional).",
            )

            st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

            # Form Action Buttons: Submit Issue & Cancel
            sub_col1, sub_col2, _ = st.columns([1.4, 1.2, 3])
            with sub_col1:
                submit_button = st.form_submit_button("Submit Issue", type="primary", use_container_width=True)
            with sub_col2:
                cancel_button = st.form_submit_button("Cancel", type="secondary", use_container_width=True)

            if cancel_button:
                st.session_state["student_active_view"] = None
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
                    with st.spinner("Submitting complaint and generating token..."):
                        time.sleep(0.2)

                    # Build complaint payload strictly bound to authenticated student
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

                    if photo_file is not None:
                        new_ticket["has_photo"] = True
                        new_ticket["photo_name"] = photo_file.name

                    try:
                        # Add to store (generates unique CMP-2026-XXX token and persists)
                        created_token = add_complaint(new_ticket)

                        if created_token and created_token.startswith("CMP-2026-"):
                            st.session_state["submission_confirmation"] = {
                                "token": created_token,
                                "status": "Submitted",
                            }
                            st.rerun()
                        else:
                            st.error("Failed to generate a valid complaint token. Please retry.")
                    except Exception as exc:
                        st.error(f"Complaint registration failed: {exc}. Please retry.")

    # -------------------------------------------------------------------------
    # VIEW B: HISTORY VIEW
    # Strictly retrieves and displays complaints for currently authenticated student ID.
    # -------------------------------------------------------------------------
    elif active_view == "history":
        c_hdr, c_srch = st.columns([2.2, 1.5])
        with c_hdr:
            st.markdown(
                _clean_html(
                    f"""
                    <div style="margin-bottom: 0.5rem;">
                        <h2 style="margin: 0; font-size: 1.4rem; color: #203A32; font-weight: 750;">
                            Complaint History &amp; Status Tracking
                        </h2>
                        <p style="margin: 0.2rem 0 0 0; color: #4A6357; font-size: 0.88rem;">
                            Showing complaints submitted by <strong>{active_student_name}</strong> ({active_student_id}).
                        </p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        # Scoped retrieval strictly by authenticated student ID
        student_complaints_list = get_student_complaints(active_student_id)

        with c_srch:
            search_token = st.text_input(
                "Track Complaint by Token",
                placeholder="Search token (e.g. CMP-2026-001)...",
                label_visibility="collapsed",
                key="search_student_complaints",
            )

        # Filter by search token if entered
        if search_token.strip():
            term = search_token.strip().lower()
            student_complaints_list = [
                c for c in student_complaints_list
                if term in str(c.get("complaint_id", "")).lower()
                or term in str(c.get("title", "")).lower()
                or term in str(c.get("facility_type", "")).lower()
            ]

        # Clean empty state when no complaints exist for this student
        if not student_complaints_list:
            if search_token.strip():
                msg_title = "No matching complaints found."
                msg_desc = f"No complaints found matching '{search_token}'. Check the token ID."
            else:
                msg_title = "No complaints submitted yet."
                msg_desc = "You have not registered any facility queries yet. Click below to raise your first issue."

            st.markdown(
                _clean_html(
                    f"""
                    <div class="dashboard-card" style="text-align: center; padding: 3rem 2rem; margin: 1.5rem 0; border: 1px solid #DCE5D8; border-radius: 14px; background: #FFFFFF;">
                        <div style="width: 58px; height: 58px; line-height: 58px; border-radius: 16px; background-color: #DCE5D8; border: 1px solid #A8B9A3; font-size: 1.9rem; margin: 0 auto 1.25rem auto;">
                            📋
                        </div>
                        <h3 style="color: #203A32; font-size: 1.3rem; font-weight: 750; margin-bottom: 0.5rem;">
                            {msg_title}
                        </h3>
                        <p style="color: #4A6357; font-size: 0.95rem; max-width: 480px; margin: 0 auto 1.5rem auto; line-height: 1.55;">
                            {msg_desc}
                        </p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            if not search_token.strip():
                col_empty_btn, _ = st.columns([1.5, 4])
                with col_empty_btn:
                    if st.button("➕ Raise a Query", key="btn_empty_raise_query", type="primary", use_container_width=True):
                        st.session_state["student_active_view"] = "raise"
                        st.rerun()
            return

        # Render each student complaint card
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
            est_res_text = f"<span>⏱️ <strong>Est. Turnaround:</strong> <span style='color: #203A32; font-weight: 600;'>{est_res}</span></span>" if est_res else ""

            # 5-stage progress indicator
            progress_indicator_html = render_student_progress_timeline(status)

            card_html = _clean_html(
                f"""
                <div class="dashboard-card" style="margin-bottom: 1.35rem; padding: 1.5rem 1.8rem; border: 1px solid #DCE5D8; border-radius: 14px; background: #FFFFFF; box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
                        <div>
                            <span style="font-family: monospace; font-size: 0.85rem; font-weight: 800; color: #203A32; background-color: #DCE5D8; padding: 0.2rem 0.6rem; border-radius: 6px; border: 1px solid #A8B9A3;">
                                {cid}
                            </span>
                            <span style="font-size: 0.78rem; font-weight: 600; color: #203A32; background-color: #F0F4ED; padding: 0.2rem 0.6rem; border-radius: 6px; margin-left: 0.4rem; border: 1px solid #DCE5D8;">
                                {fac}
                            </span>
                            <h3 style="margin: 0.55rem 0 0 0; color: #203A32; font-size: 1.2rem; font-weight: 750;">
                                {title}
                            </h3>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 0.82rem; color: #4A6357; font-weight: 500;">Status:</span>
                            {s_badge}
                        </div>
                    </div>
                    {progress_indicator_html}
                    <p style="color: #203A32; font-size: 0.94rem; margin: 0.95rem 0 0.95rem 0; line-height: 1.55;">
                        {desc}
                    </p>
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #DCE5D8; padding-top: 0.85rem; font-size: 0.84rem; color: #4A6357; flex-wrap: wrap; gap: 0.75rem;">
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
            <div style="background-color: #FFFFFF; border: 1px dashed #A8B9A3; border-radius: 10px; padding: 0.95rem 1.25rem; margin-top: 2rem; text-align: center; font-size: 0.84rem; color: #4A6357;">
                💡 Need immediate assistance for an emergency? Contact your hostel warden or campus security desk.
                Campus facility updates and maintenance dispatches are tracked directly in this portal.
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
