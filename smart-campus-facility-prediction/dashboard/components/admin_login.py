"""
Professional Administrator Authentication Screen for FIPP.
Provides secure credential verification, password hashing, show/hide password toggle,
clear feedback for invalid credentials, and navigation back to the landing page.
Palette: Soft Ivory (#F5F7F2), Forest Green (#203A32), Sage (#A8B9A3), Pale Sage (#DCE5D8), White (#FFFFFF).
"""
import streamlit as st
from src.auth.admin_auth import authenticate_admin


def render_admin_login_screen() -> None:
    """
    Renders the dedicated, secure Administrator Login portal in Modern Sage & Forest style.
    Contains:
    - Administrator ID input.
    - Password input with dynamic Show/Hide password toggle.
    - Prominent Primary Login button.
    - Clear invalid credentials error handling.
    - Back to landing page navigation.
    """
    # Hide sidebar on login screen and apply wide container spacing
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .block-container {
            padding-top: 2.5rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Project Branding Header
    st.markdown(
        """
        <div style="text-align: center; max-width: 780px; margin: 0 auto 2rem auto;">
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
                FIPP — Facility Issue Prediction &amp; Prioritisation
            </h1>
            <p style="color: #4A6357; font-size: 0.92rem; margin: 0;">
                Administrator Security Gateway • Operations &amp; Facility Intelligence
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered Login Card
    _, col_form, _ = st.columns([1, 1.4, 1])

    with col_form:
        st.markdown(
            """
            <div class="dashboard-card" style="padding: 2.2rem 2.2rem 1.6rem 2.2rem; margin-bottom: 1.25rem; border-top: 4px solid #203A32; border-radius: 14px; background: #FFFFFF; box-shadow: 0 4px 16px rgba(32, 58, 50, 0.06);">
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
                        🛠️
                    </div>
                    <div>
                        <h2 style="margin: 0; font-size: 1.4rem; color: #203A32; font-weight: 700;">
                            Administrator Login
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
                        ">Secured Authentication</span>
                    </div>
                </div>
                <p style="color: #4A6357; font-size: 0.88rem; line-height: 1.5; margin: 0.8rem 0 0.5rem 0;">
                    Please enter your verified Administrator ID and password to access facility triage operations and predictive analytics.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        admin_id_input = st.text_input(
            "Administrator ID",
            placeholder="e.g. ADM-2026-001 or admin",
            help="Enter your assigned Administrator identification code.",
            key="input_admin_id",
        )

        # Show/Hide password toggle checkbox
        show_password = st.checkbox("Show password", key="chk_admin_show_password")
        password_input_type = "default" if show_password else "password"

        password_input = st.text_input(
            "Password",
            type=password_input_type,
            placeholder="Enter administrator password",
            help="Enter your confidential administrator password.",
            key="input_admin_pwd",
        )

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        col_submit, col_back = st.columns([1.3, 1.2])
        with col_submit:
            login_clicked = st.button("Login", type="primary", use_container_width=True, key="btn_admin_submit_login")
        with col_back:
            back_clicked = st.button("Back to Landing Page", type="secondary", use_container_width=True, key="btn_admin_back_portal")

        if back_clicked:
            st.session_state["selected_role"] = None
            st.session_state["auth_user"] = None
            st.session_state["user_role"] = None
            st.rerun()

        if login_clicked:
            clean_id = admin_id_input.strip()
            clean_pwd = password_input.strip()

            if not clean_id or not clean_pwd:
                st.error("Please enter both your Administrator ID and password to proceed.")
            else:
                auth_result = authenticate_admin(clean_id, clean_pwd)
                if auth_result:
                    st.session_state["auth_user"] = auth_result
                    st.session_state["user_role"] = "admin"
                    st.session_state["admin_active_page"] = "Overview"
                    st.rerun()
                else:
                    st.error("Invalid Administrator ID or password. Please verify your credentials and try again.")

        # Tasteful demo credential note for authorized operators
        st.markdown(
            """
            <div style="background-color: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 8px; padding: 0.85rem 1.1rem; margin-top: 1.25rem; font-size: 0.82rem; color: #4A6357;">
                <div style="font-weight: 700; color: #203A32; margin-bottom: 0.2rem;">🔐 Default Administrator Credentials</div>
                <div>ID: <code style="background: #F5F7F2; padding: 0.1rem 0.35rem; border-radius: 4px; color: #203A32;">ADM-2026-001</code> or <code style="background: #F5F7F2; padding: 0.1rem 0.35rem; border-radius: 4px; color: #203A32;">admin</code></div>
                <div>Password: <code style="background: #F5F7F2; padding: 0.1rem 0.35rem; border-radius: 4px; color: #203A32;">Admin@2026</code></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Footer note
    st.markdown(
        """
        <div style="text-align: center; margin-top: 3.5rem; color: #6D8276; font-size: 0.8rem;">
            FIPP 2.0 • Secured Campus Maintenance Intelligence • Modern Sage &amp; Forest Architecture
        </div>
        """,
        unsafe_allow_html=True,
    )
