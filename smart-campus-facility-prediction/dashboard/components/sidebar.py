"""
Admin Left-Side Sidebar Navigation Component.
Renders the Administrator identity, navigation menu, live repository status,
demo data controls, and logout button on the left sidebar of the dashboard.
Palette: Soft Ivory (#F5F7F2), Forest Green (#203A32), Deep Forest (#172D28),
Sage (#A8B9A3), Pale Sage (#DCE5D8), White (#FFFFFF).
Uses Lucide outline vector icons for navigation and branding; zero emoji symbols.
Subtle, slightly lighter forest-green hover state (#24453A) with no white boxes.
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
    admin_id = admin_id or auth.get("id") or "fipp.admin"
    admin_title = admin_title or auth.get("title") or auth.get("role_title") or "System Administrator"

    # Dark forest-green sidebar styling with pale sage highlights and clean text navigation
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background-color: #172D28 !important;
            border-right: 1px solid rgba(220, 229, 216, 0.18) !important;
            min-width: 290px !important;
            width: 290px !important;
            z-index: 100 !important;
        }
        [data-testid="stSidebarContent"] {
            padding: 1.25rem 1rem !important;
            overflow-x: hidden !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(220, 229, 216, 0.2) !important;
        }

        /* Sidebar Radio Container */
        [data-testid="stSidebar"] [data-testid="stRadio"] {
            background-color: transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] {
            display: none !important;
        }

        /* Hide native circular radio dot for clean navigation list */
        [data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child,
        [data-testid="stSidebar"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] ~ div,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div > div:first-child,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {
            display: none !important;
        }

        /* Navigation Item Base Layout - Clean Professional Text Labels */
        [data-testid="stSidebar"] [data-testid="stRadioOption"],
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label,
        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            display: flex !important;
            align-items: center !important;
            padding: 0.65rem 0.95rem !important;
            margin-bottom: 0.25rem !important;
            border-radius: 8px !important;
            white-space: nowrap !important;
            cursor: pointer !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
            transition: all 0.15s ease-in-out !important;
            box-sizing: border-box !important;
        }

        /* Ensure inner containers and paragraphs stay transparent */
        [data-testid="stSidebar"] [data-testid="stRadioOption"] div,
        [data-testid="stSidebar"] [data-testid="stRadioOption"] span,
        [data-testid="stSidebar"] [data-testid="stRadioOption"] p {
            background-color: transparent !important;
        }

        /* Inactive Navigation Item Typography */
        [data-testid="stSidebar"] [data-testid="stRadioOption"] p,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label p,
        [data-testid="stSidebar"] .stRadio label p {
            color: #DCE5D8 !important;
            font-size: 0.92rem !important;
            font-weight: 550 !important;
            margin: 0 !important;
            white-space: nowrap !important;
            line-height: 1.2 !important;
        }

        /* =========================================================================
           HOVER STATE: Subtle, slightly lighter forest-green (#24453A)
           Eliminates any pure-white or pale background; keeps text crisp white (#FFFFFF).
           ========================================================================= */
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked)):hover,
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked))[data-hovered="true"],
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:not([data-selected="true"]):not(:has(input:checked)):hover,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:not([data-checked="true"]):not(:has(input:checked)):hover {
            background-color: #24453A !important;
            border-color: rgba(168, 185, 163, 0.25) !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked)):hover p,
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked))[data-hovered="true"] p,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:not([data-selected="true"]):not(:has(input:checked)):hover p,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:not([data-checked="true"]):not(:has(input:checked)):hover p {
            color: #FFFFFF !important;
        }

        /* =========================================================================
           ACTIVE / SELECTED STATE: Distinct Forest Green (#203A32) with Sage Accent
           Hovering over another item NEVER overrides this active styling.
           ========================================================================= */
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"],
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked),
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label[data-selected="true"],
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:has(input:checked),
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"],
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
            background-color: #203A32 !important;
            border-left: 4px solid #A8B9A3 !important;
            padding-left: 0.85rem !important;
            border-top: 1px solid transparent !important;
            border-right: 1px solid transparent !important;
            border-bottom: 1px solid transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p,
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) p,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label[data-selected="true"] p,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:has(input:checked) p,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] p,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) p {
            color: #FFFFFF !important;
            font-weight: 750 !important;
        }

        /* Active item hover: maintain distinct active background and left border */
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"]:hover,
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked):hover,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label[data-selected="true"]:hover,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:has(input:checked):hover,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"]:hover,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked):hover {
            background-color: #203A32 !important;
            border-left: 4px solid #A8B9A3 !important;
        }

        /* =========================================================================
           KEYBOARD FOCUS STATE: Accessible, subtle focus outline without white box
           ========================================================================= */
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-visible,
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-focus-visible="true"],
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:focus-visible,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:focus-visible {
            background-color: #24453A !important;
            outline: 2px solid #A8B9A3 !important;
            outline-offset: -2px !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-visible p,
        [data-testid="stSidebar"] [data-testid="stRadioOption"][data-focus-visible="true"] p,
        [data-testid="stSidebar"] [data-testid="stRadioGroup"] label:focus-visible p,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:focus-visible p {
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Branding header with restored campus facility icon
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
                    font-size: 1.35rem;
                    flex-shrink: 0;
                ">
                    🏫
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
