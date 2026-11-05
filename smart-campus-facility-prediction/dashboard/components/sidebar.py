"""
Admin Right-Side Sidebar Navigation Component.
Renders the Administrator identity, navigation menu, live repository status,
demo data controls, and logout button on the right side of the dashboard.
Adheres strictly to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2).
"""
import streamlit as st
from src.data.complaints_store import get_complaints_df, clear_all_complaints, reset_to_default_dataset

# Task 1 baseline navigation options (preserved for test compatibility)
NAVIGATION_OPTIONS = [
    "📊 Overview",
    "📋 Complaint Management",
    "📈 Predictive Analytics",
    "🚨 Maintenance Priorities",
    "🧠 Model Insights",
]

# Full Admin navigation menu (8 logical sections)
ADMIN_NAVIGATION_OPTIONS = [
    "📊 Overview",
    "📋 Complaint Management",
    "⚡ AI Analysis",
    "🚨 Priority Queue",
    "🔮 Predictive Maintenance",
    "🔁 Recurring Issues",
    "🔬 Explainable AI",
    "⚙️ Settings",
]


def render_admin_sidebar(admin_name: str | None = None, admin_id: str | None = None) -> str:
    """
    Renders the Administrator right-side sidebar panel.

    Args:
        admin_name: Logged-in administrator name.
        admin_id: Logged-in administrator ID.

    Returns:
        The selected page title string.
    """
    if not admin_name or not admin_id:
        auth = st.session_state.get("auth_user") or {}
        admin_name = auth.get("name") or "Administrator"
        admin_id = auth.get("id") or "ADM-2026-001"

    # Container with soft tan border and warm styling
    st.markdown(
        f"""
        <div class="admin-sidebar-box">
            <div style="display: flex; align-items: center; gap: 0.6rem; padding-bottom: 0.75rem; border-bottom: 1px solid #EAE3D2; margin-bottom: 0.75rem;">
                <div style="
                    width: 38px;
                    height: 38px;
                    border-radius: 8px;
                    background-color: #EAE3D2;
                    border: 1px solid #D8CFBD;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.25rem;
                ">
                    🏫
                </div>
                <div>
                    <h3 style="margin: 0; font-size: 1.05rem; color: #1A1A1A; font-weight: 700;">
                        Smart Campus AI
                    </h3>
                    <p style="margin: 0; font-size: 0.76rem; color: #555555;">
                        Facility Management Intelligence
                    </p>
                </div>
            </div>
            <div style="
                background-color: #FDFBF7;
                border: 1px solid #EAE3D2;
                border-radius: 8px;
                padding: 0.65rem 0.8rem;
                margin-bottom: 0.85rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                    <span style="
                        font-size: 0.68rem;
                        font-weight: 700;
                        color: #1A1A1A;
                        background-color: #EAE3D2;
                        padding: 0.12rem 0.45rem;
                        border-radius: 4px;
                        text-transform: uppercase;
                        letter-spacing: 0.04em;
                        border: 1px solid #D8CFBD;
                    ">Administrator</span>
                </div>
                <div style="font-size: 0.88rem; font-weight: 600; color: #1A1A1A; margin-top: 0.2rem;">
                    {admin_name}
                </div>
                <div style="font-size: 0.75rem; color: #555555; font-family: monospace;">
                    ID: {admin_id}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Menu Header
    st.markdown(
        "<span style='font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #767676;'>Navigation</span>",
        unsafe_allow_html=True,
    )

    # Determine current index
    current_page = st.session_state.get("admin_active_page", ADMIN_NAVIGATION_OPTIONS[0])
    default_idx = 0
    for i, opt in enumerate(ADMIN_NAVIGATION_OPTIONS):
        if current_page in opt or opt in current_page:
            default_idx = i
            break

    selected_page = st.radio(
        "Admin Navigation",
        options=ADMIN_NAVIGATION_OPTIONS,
        index=default_idx,
        label_visibility="collapsed",
        key="radio_admin_right_nav",
    )
    st.session_state["admin_active_page"] = selected_page

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Logout Button
    if st.button("Logout", key="btn_admin_sidebar_logout", type="secondary", use_container_width=True):
        st.session_state["auth_user"] = None
        st.session_state["selected_role"] = None
        st.session_state["user_role"] = None
        st.rerun()

    st.markdown("---")

    # Live Repository Status
    df = get_complaints_df()
    total_tickets = len(df)
    open_backlog = len(df[df["status"] != "Resolved"]) if not df.empty else 0
    high_prio = len(df[df["priority_tier"].isin(["Critical", "High"])]) if not df.empty else 0

    st.markdown(
        f"""
        <div style="
            background-color: #FFFFFF;
            border: 1px solid #EAE3D2;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            margin-bottom: 0.75rem;
            font-size: 0.78rem;
            color: #1A1A1A;
            line-height: 1.6;
        ">
            <span style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #767676;">Repository Status</span><br>
            • Total Tickets: <strong>{total_tickets}</strong><br>
            • Open Backlog: <strong>{open_backlog}</strong><br>
            • High Priority: <strong>{high_prio}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Demo Data Controls
    with st.expander("🛠️ Demo Controls", expanded=False):
        st.caption("Reset or empty dataset state:")
        c_res, c_clr = st.columns(2)
        with c_res:
            if st.button("Reset", use_container_width=True, key="btn_reset_demo", type="secondary"):
                reset_to_default_dataset()
                st.rerun()
        with c_clr:
            if st.button("Empty", use_container_width=True, key="btn_empty_demo", type="secondary"):
                clear_all_complaints()
                st.rerun()

    # Footer note
    st.markdown(
        """
        <div style="font-size: 0.72rem; color: #767676; text-align: center; margin-top: 1rem;">
            Smart Campus v0.4.0 • Light Theme
        </div>
        """,
        unsafe_allow_html=True,
    )

    return selected_page


def render_sidebar() -> str:
    """Backward-compatible wrapper for render_admin_sidebar."""
    return render_admin_sidebar()
