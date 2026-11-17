"""
Dedicated Login Interface for Administrator and Student Roles.
Implements simulated authentication with Name and ID inputs,
clear role headers, input validation, and back navigation.
Modern Sage & Forest Theme:
- Soft Ivory: #F5F7F2
- Forest Green: #203A32
- Sage: #A8B9A3
- Pale Sage: #DCE5D8
- White: #FFFFFF
"""
import streamlit as st


def render_login_screen(role: str) -> None:
    """
    Renders the dedicated login portal for the selected role in Modern Sage & Forest style.

    Args:
        role: Either 'admin' or 'student'.
    """
    is_admin = (role == "admin")
    role_display = "Administrator" if is_admin else "Student"
    role_icon = "🛠️" if is_admin else "🎓"
    role_title = f"{role_display} Login"

    name_label = "Administrator Name" if is_admin else "Student Name"
    name_placeholder = "e.g. Dr. Robert Davies" if is_admin else "e.g. Alex Chen"

    id_label = "Administrator ID" if is_admin else "Student ID"
    id_placeholder = "e.g. ADM-2026-001" if is_admin else "e.g. STU-2026-101"

    # Hide sidebar when on login screen
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Project Branding Header
    st.markdown(
        """
        <div style="text-align: center; max-width: 780px; margin: 0 auto 1.8rem auto;">
            <div style="
                display: inline-flex;
                width: 58px;
                height: 58px;
                border-radius: 14px;
                background-color: #DCE5D8;
                border: 1px solid #A8B9A3;
                align-items: center;
                justify-content: center;
                font-size: 1.85rem;
                margin-bottom: 0.75rem;
                box-shadow: 0 4px 6px -1px rgba(32, 58, 50, 0.05);
            ">
                🏫
            </div>
            <h1 style="font-size: 1.85rem; color: #203A32; margin-bottom: 0.25rem; font-weight: 800; letter-spacing: -0.025em;">
                FIPP — Facility Issue Prediction &amp; Prioritization
            </h1>
            <p style="color: #4A6357; font-size: 0.92rem; margin: 0;">
                Smart Campus Facility Intelligence &amp; Autonomous Triage System
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered Login Card
    _, col_form, _ = st.columns([1, 1.8, 1])

    with col_form:
        st.markdown(
            f"""
            <div class="dashboard-card" style="padding: 2.2rem 2.2rem; margin-bottom: 1.25rem; border-top: 4px solid {'#203A32' if is_admin else '#A8B9A3'};">
                <div style="display: flex; align-items: center; gap: 0.85rem; margin-bottom: 0.5rem;">
                    <div style="
                        width: 48px;
                        height: 48px;
                        text-align: center;
                        border-radius: 12px;
                        background-color: #DCE5D8;
                        border: 1px solid #A8B9A3;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.6rem;
                    ">
                        {role_icon}
                    </div>
                    <div>
                        <h2 style="margin: 0; font-size: 1.45rem; color: #203A32; font-weight: 700;">
                            {role_title}
                        </h2>
                        <span style="
                            font-size: 0.72rem;
                            font-weight: 700;
                            color: #203A32;
                            background-color: #DCE5D8;
                            padding: 0.18rem 0.55rem;
                            border-radius: 9999px;
                            text-transform: uppercase;
                            letter-spacing: 0.04em;
                            border: 1px solid #A8B9A3;
                            display: inline-block;
                            margin-top: 0.2rem;
                        ">Simulated Authentication</span>
                    </div>
                </div>
                <p style="color: #4A6357; font-size: 0.88rem; line-height: 1.5; margin: 0.8rem 0 1.25rem 0;">
                    This prototype uses simulated authentication for demonstration purposes without requiring external server credentials. Please enter your name and ID to proceed.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_role_login", clear_on_submit=False):
            entered_name = st.text_input(
                name_label,
                placeholder=name_placeholder,
                help=f"Enter the full name for the {role_display.lower()} session.",
            )

            entered_id = st.text_input(
                id_label,
                placeholder=id_placeholder,
                help=f"Enter a unique identification code (e.g. {id_placeholder}).",
            )

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            c_login, c_back = st.columns([1.4, 1.2])
            with c_login:
                login_submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            with c_back:
                back_submitted = st.form_submit_button("Back to Role Selection", type="secondary", use_container_width=True)

            if back_submitted:
                st.session_state["selected_role"] = None
                st.session_state["auth_user"] = None
                st.session_state["user_role"] = None
                st.rerun()

            if login_submitted:
                clean_name = entered_name.strip()
                clean_id = entered_id.strip()

                if not clean_name or not clean_id:
                    st.error("Please enter both your name and ID to log in.")
                else:
                    st.session_state["auth_user"] = {
                        "role": role,
                        "name": clean_name,
                        "id": clean_id,
                    }
                    st.session_state["user_role"] = role
                    if is_admin:
                        st.session_state["admin_active_page"] = "Overview"
                    st.rerun()

    # Footer note
    st.markdown(
        """
        <div style="text-align: center; margin-top: 3rem; color: #6D8276; font-size: 0.82rem;">
            Academic Capstone Prototype • CSE AIML 3rd-Year Project • Built with Python &amp; Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )
