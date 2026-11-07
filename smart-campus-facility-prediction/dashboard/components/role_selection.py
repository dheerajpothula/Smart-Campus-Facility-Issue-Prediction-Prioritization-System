"""
Role Selection Gateway Screen.
Features a clean, minimal, and professional presentation with 60/30/10 palette:
Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), and Soft Tan (#EAE3D2).
"""
import streamlit as st


def render_role_selection_screen() -> None:
    """Renders the clean, minimal university role selection portal."""
    # Top spacing
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Main Gateway Header Container
    st.markdown(
        """
        <div style="text-align: center; max-width: 780px; margin: 0 auto 3rem auto;">
            <div style="
                display: inline-block;
                width: 72px;
                height: 72px;
                line-height: 72px;
                border-radius: 18px;
                background-color: #EAE3D2;
                border: 1px solid #D8CFBD;
                font-size: 2.3rem;
                margin-bottom: 1.1rem;
                box-shadow: 0 4px 6px -1px rgba(26, 26, 26, 0.05);
            ">
                🏫
            </div>
            <h1 style="font-size: 2.15rem; color: #1A1A1A; margin-bottom: 0; font-weight: 700; letter-spacing: -0.025em;">
                FIPP — Facility Issue Prediction &amp; Prioritization
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Two Role Cards Side-by-Side
    _, col_admin, col_student, _ = st.columns([0.1, 1, 1, 0.1])

    with col_admin:
        st.markdown(
            """
            <div class="dashboard-card" style="
                min-height: 260px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                text-align: left;
                padding: 2rem 1.8rem;
                border: 1px solid #EAE3D2;
                background-color: #FFFFFF;
            ">
                <div>
                    <div style="
                        width: 48px;
                        height: 48px;
                        line-height: 48px;
                        text-align: center;
                        border-radius: 12px;
                        background-color: #EAE3D2;
                        border: 1px solid #D8CFBD;
                        font-size: 1.6rem;
                        margin-bottom: 1.2rem;
                    ">
                        🛠️
                    </div>
                    <h2 style="font-size: 1.45rem; color: #1A1A1A; margin: 0 0 0.75rem 0; font-weight: 700;">
                        Administrator
                    </h2>
                    <p style="color: #4A4A4A; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;">
                        Manage campus maintenance, facility issues, AI predictions, and maintenance priorities.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Continue as Administrator", key="btn_role_admin", type="primary", use_container_width=True):
            st.session_state["selected_role"] = "admin"
            st.session_state["user_role"] = None
            st.rerun()

    with col_student:
        st.markdown(
            """
            <div class="dashboard-card" style="
                min-height: 260px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                text-align: left;
                padding: 2rem 1.8rem;
                border: 1px solid #EAE3D2;
                background-color: #FFFFFF;
            ">
                <div>
                    <div style="
                        width: 48px;
                        height: 48px;
                        line-height: 48px;
                        text-align: center;
                        border-radius: 12px;
                        background-color: #EAE3D2;
                        border: 1px solid #D8CFBD;
                        font-size: 1.6rem;
                        margin-bottom: 1.2rem;
                    ">
                        🎓
                    </div>
                    <h2 style="font-size: 1.45rem; color: #1A1A1A; margin: 0 0 0.75rem 0; font-weight: 700;">
                        Student
                    </h2>
                    <p style="color: #4A4A4A; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;">
                        Report facility issues and track your complaints.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Continue as Student", key="btn_role_student", type="primary", use_container_width=True):
            st.session_state["selected_role"] = "student"
            st.session_state["user_role"] = None
            st.rerun()

    # Footer note
    st.markdown(
        """
        <div style="text-align: center; margin-top: 4rem; color: #767676; font-size: 0.82rem;">
            Academic Capstone Prototype • CSE AIML 3rd-Year Project • Built with Python & Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )
