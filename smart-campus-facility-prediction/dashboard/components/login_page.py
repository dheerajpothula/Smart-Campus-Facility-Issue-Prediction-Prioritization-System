"""
Dedicated Login Interface for Administrator and Student Roles.
Implements simulated authentication with Name and ID inputs,
clear role headers, input validation, and back navigation.
Strict 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2).
"""
import streamlit as st


def render_login_screen(role: str) -> None:
    """
    Renders the dedicated login portal for the selected role.

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

    # Top spacing
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Project Branding Header
    st.markdown(
        """
        <div style="text-align: center; max-width: 780px; margin: 0 auto 2rem auto;">
            <div style="
                display: inline-block;
                width: 60px;
                height: 60px;
                line-height: 60px;
                border-radius: 16px;
                background-color: #EAE3D2;
                border: 1px solid #D8CFBD;
                font-size: 2rem;
                margin-bottom: 0.8rem;
                box-shadow: 0 4px 6px -1px rgba(26, 26, 26, 0.05);
            ">
                🏫
            </div>
            <h1 style="font-size: 1.95rem; color: #1A1A1A; margin-bottom: 0.25rem; font-weight: 700; letter-spacing: -0.02em;">
                Smart Campus Facility Issue Prediction & Prioritization System
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered Login Card
    _, col_form, _ = st.columns([1, 1.8, 1])

    with col_form:
        st.markdown(
            f"""
            <div class="dashboard-card" style="padding: 2rem 2.2rem; margin-bottom: 1.25rem;">
                <div style="display: flex; align-items: center; gap: 0.85rem; margin-bottom: 0.5rem;">
                    <div style="
                        width: 44px;
                        height: 44px;
                        line-height: 44px;
                        text-align: center;
                        border-radius: 10px;
                        background-color: #EAE3D2;
                        border: 1px solid #D8CFBD;
                        font-size: 1.45rem;
                    ">
                        {role_icon}
                    </div>
                    <div>
                        <h2 style="margin: 0; font-size: 1.4rem; color: #1A1A1A; font-weight: 700;">
                            {role_title}
                        </h2>
                        <span style="
                            font-size: 0.72rem;
                            font-weight: 600;
                            color: #1A1A1A;
                            background-color: #EAE3D2;
                            padding: 0.15rem 0.5rem;
                            border-radius: 4px;
                            text-transform: uppercase;
                            letter-spacing: 0.04em;
                            border: 1px solid #D8CFBD;
                        ">Simulated Authentication</span>
                    </div>
                </div>
                <p style="color: #555555; font-size: 0.88rem; line-height: 1.5; margin: 0.8rem 0 1.25rem 0;">
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
        <div style="text-align: center; margin-top: 3rem; color: #767676; font-size: 0.82rem;">
            Academic Capstone Prototype • CSE AIML 3rd-Year Project • Built with Python & Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )
