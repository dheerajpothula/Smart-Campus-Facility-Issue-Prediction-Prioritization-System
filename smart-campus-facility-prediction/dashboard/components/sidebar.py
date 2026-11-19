"""
Admin Left-Side Sidebar Navigation Component.
Renders the Administrator identity, navigation menu, live repository status,
demo data controls, and logout button on the left sidebar of the dashboard.
Palette: Soft Ivory (#F5F7F2), Forest Green (#203A32), Deep Forest (#172D28),
Sage (#A8B9A3), Pale Sage (#DCE5D8), White (#FFFFFF).
Uses Lucide outline vector icons for navigation and branding; zero emoji symbols.
"""
import streamlit as st
from src.data.complaints_store import get_complaints_df, clear_all_complaints, reset_to_default_dataset
from dashboard.components.icons import render_lucide_icon, get_lucide_icon_data_uri

# Task 1 baseline navigation options (preserved for test compatibility)
NAVIGATION_OPTIONS = [
    "📊 Overview",
    "📋 Complaint Management",
    "📈 Predictive Analytics",
    "🚨 Maintenance Priorities",
    "🧠 Model Insights",
]

# FIPP 2.0 Control Centre Navigation (Phase 4 & UI Refinement: Clean professional labels)
ADMIN_NAVIGATION_OPTIONS = [
    "Overview",
    "All Requests",
    "New / Unassigned",
    "In Progress",
    "Resolved",
    "Reports",
]


def render_admin_sidebar(
    admin_name: str | None = None,
    admin_id: str | None = None,
    admin_title: str | None = None,
) -> str:
    """
    Renders the Administrator left-side sidebar panel in Modern Sage & Forest styling.

    Args:
        admin_name: Logged-in administrator name (unused in UI to preserve neutrality).
        admin_id: Logged-in administrator ID.
        admin_title: Logged-in administrator title / role.

    Returns:
        The selected page title string.
    """
    auth = st.session_state.get("auth_user") or {}
    admin_id = admin_id or auth.get("id") or "ADM-2026-001"
    admin_title = admin_title or auth.get("title") or auth.get("role_title") or "Facility Operations Lead"

    # Navigation icon data URIs for CSS pseudo-element injection
    uri_overview = get_lucide_icon_data_uri("layout-dashboard", color="%23DCE5D8", size=18)
    uri_overview_act = get_lucide_icon_data_uri("layout-dashboard", color="%23FFFFFF", size=18)

    uri_requests = get_lucide_icon_data_uri("clipboard-list", color="%23DCE5D8", size=18)
    uri_requests_act = get_lucide_icon_data_uri("clipboard-list", color="%23FFFFFF", size=18)

    uri_unassigned = get_lucide_icon_data_uri("inbox", color="%23DCE5D8", size=18)
    uri_unassigned_act = get_lucide_icon_data_uri("inbox", color="%23FFFFFF", size=18)

    uri_inprogress = get_lucide_icon_data_uri("wrench", color="%23DCE5D8", size=18)
    uri_inprogress_act = get_lucide_icon_data_uri("wrench", color="%23FFFFFF", size=18)

    uri_resolved = get_lucide_icon_data_uri("check-circle", color="%23DCE5D8", size=18)
    uri_resolved_act = get_lucide_icon_data_uri("check-circle", color="%23FFFFFF", size=18)

    uri_reports = get_lucide_icon_data_uri("chart-no-axes-combined", color="%23DCE5D8", size=18)
    uri_reports_act = get_lucide_icon_data_uri("chart-no-axes-combined", color="%23FFFFFF", size=18)

    building_svg = render_lucide_icon("building", size=22, color="#FFFFFF", stroke_width=2.0)

    # Dark forest-green sidebar styling with pale sage highlights and Lucide outline icons
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{
            background-color: #172D28 !important;
            border-right: 1px solid rgba(220, 229, 216, 0.18) !important;
            min-width: 290px !important;
            width: 290px !important;
            z-index: 100 !important;
        }}
        [data-testid="stSidebarContent"] {{
            padding: 1.25rem 1rem !important;
            overflow-x: hidden !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: rgba(220, 229, 216, 0.2) !important;
        }}
        /* Hide native circular radio dot for clean navigation list */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {{
            display: none !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {{
            display: flex !important;
            align-items: center !important;
            gap: 0.75rem !important;
            padding: 0.6rem 0.85rem !important;
            margin-bottom: 0.25rem !important;
            border-radius: 8px !important;
            white-space: nowrap !important;
            cursor: pointer !important;
            transition: all 0.15s ease-in-out !important;
        }}
        [data-testid="stSidebar"] .stRadio label p {{
            color: #DCE5D8 !important;
            font-size: 0.92rem !important;
            font-weight: 550 !important;
            margin: 0 !important;
            white-space: nowrap !important;
            line-height: 1.2 !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label::before {{
            content: "";
            display: inline-block !important;
            width: 18px !important;
            height: 18px !important;
            min-width: 18px !important;
            background-size: contain !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            opacity: 0.85;
            transition: opacity 0.15s ease-in-out;
            flex-shrink: 0 !important;
        }}
        /* 1. Overview: layout-dashboard */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(1)::before {{
            background-image: url('{uri_overview}');
        }}
        /* 2. All Requests: clipboard-list */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(2)::before {{
            background-image: url('{uri_requests}');
        }}
        /* 3. New / Unassigned: inbox */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(3)::before {{
            background-image: url('{uri_unassigned}');
        }}
        /* 4. In Progress: wrench */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(4)::before {{
            background-image: url('{uri_inprogress}');
        }}
        /* 5. Resolved: check-circle */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(5)::before {{
            background-image: url('{uri_resolved}');
        }}
        /* 6. Reports: chart-no-axes-combined */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(6)::before {{
            background-image: url('{uri_reports}');
        }}
        /* Hover State */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {{
            background-color: rgba(32, 58, 50, 0.75) !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover p {{
            color: #FFFFFF !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover::before {{
            opacity: 1 !important;
        }}
        /* Active State */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {{
            background-color: #203A32 !important;
            border-left: 4px solid #A8B9A3 !important;
            padding-left: 0.7rem !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] p,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) p {{
            color: #FFFFFF !important;
            font-weight: 750 !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked)::before {{
            opacity: 1 !important;
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(1)[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(1):has(input:checked)::before {{
            background-image: url('{uri_overview_act}');
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(2)[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(2):has(input:checked)::before {{
            background-image: url('{uri_requests_act}');
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(3)[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(3):has(input:checked)::before {{
            background-image: url('{uri_unassigned_act}');
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(4)[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(4):has(input:checked)::before {{
            background-image: url('{uri_inprogress_act}');
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(5)[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(5):has(input:checked)::before {{
            background-image: url('{uri_resolved_act}');
        }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(6)[data-checked="true"]::before,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-of-type(6):has(input:checked)::before {{
            background-image: url('{uri_reports_act}');
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Branding header with Lucide building vector icon
    st.markdown(
        f"""
        <div class="admin-sidebar-box">
            <div style="display: flex; align-items: center; gap: 0.65rem; padding-bottom: 0.75rem; border-bottom: 1px solid rgba(220, 229, 216, 0.2); margin-bottom: 0.75rem;">
                <div style="
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                    background-color: #203A32;
                    border: 1.5px solid #A8B9A3;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                ">
                    {building_svg}
                </div>
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem; color: #FFFFFF; font-weight: 800; letter-spacing: -0.01em; line-height: 1.2;">
                        FIPP Operations
                    </h3>
                    <p style="margin: 0; font-size: 0.76rem; color: #DCE5D8; font-weight: 500; line-height: 1.2;">
                        Control Centre &bull; Admin
                    </p>
                </div>
            </div>
            <div style="
                background-color: #203A32;
                border: 1px solid rgba(220, 229, 216, 0.25);
                border-radius: 8px;
                padding: 0.75rem 0.85rem;
                margin-bottom: 0.85rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                    <span style="
                        font-size: 0.68rem;
                        font-weight: 750;
                        color: #FFFFFF;
                        background-color: #172D28;
                        padding: 0.15rem 0.55rem;
                        border-radius: 4px;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        border: 1px solid #A8B9A3;
                    ">Control Centre</span>
                </div>
                <div style="font-size: 0.92rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem; line-height: 1.3;">
                    Administrator
                </div>
                <div style="font-size: 0.78rem; font-weight: 500; color: #DCE5D8; margin-top: 0.1rem; margin-bottom: 0.2rem; line-height: 1.3;">
                    {admin_title}
                </div>
                <div style="font-size: 0.75rem; color: #A8B9A3; font-family: monospace;">
                    ID: {admin_id}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Menu Header
    st.markdown(
        "<span style='font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #DCE5D8;'>Control Centre Menu</span>",
        unsafe_allow_html=True,
    )

    # Determine current index
    current_page = st.session_state.get("admin_active_page", ADMIN_NAVIGATION_OPTIONS[0])
    default_idx = 0
    for i, opt in enumerate(ADMIN_NAVIGATION_OPTIONS):
        if current_page == opt or current_page in opt or opt in current_page:
            default_idx = i
            break

    selected_page = st.radio(
        "Admin Navigation",
        options=ADMIN_NAVIGATION_OPTIONS,
        index=default_idx,
        label_visibility="collapsed",
        key="radio_admin_left_nav",
    )
    st.session_state["admin_active_page"] = selected_page

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Logout Button (Item 9 from User Requirements: clean label, zero emoji)
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
            background-color: #203A32;
            border: 1px solid rgba(220, 229, 216, 0.22);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            margin-bottom: 0.75rem;
            font-size: 0.78rem;
            color: #DCE5D8;
            line-height: 1.6;
        ">
            <span style="font-size: 0.7rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.06em; color: #A8B9A3;">Telemetry Status</span><br>
            • Total Tickets: <strong style="color: #FFFFFF;">{total_tickets}</strong><br>
            • Open Backlog: <strong style="color: #FFFFFF;">{open_backlog}</strong><br>
            • High Priority: <strong style="color: #FFFFFF;">{high_prio}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Demo Data Controls
    with st.expander("Demo Controls", expanded=False):
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
        <div style="font-size: 0.72rem; color: #6D8276; text-align: center; margin-top: 1rem;">
            FIPP 2.0 • Modern Sage &amp; Forest
        </div>
        """,
        unsafe_allow_html=True,
    )

    return selected_page


def render_sidebar() -> str:
    """Backward-compatible wrapper for render_admin_sidebar."""
    return render_admin_sidebar()
