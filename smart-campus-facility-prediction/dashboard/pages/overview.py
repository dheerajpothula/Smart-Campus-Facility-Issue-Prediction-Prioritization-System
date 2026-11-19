"""
FIPP 2.0 — Facility Operations Control Centre: Overview Page.
Implements Phase 3 approved structure:
- FIPP ADMINISTRATION / Control Centre / FACILITY OPERATIONS · OVERVIEW
- Four Dynamic KPI Cards: Total, New, In Progress, Resolved (Clicking navigates to corresponding sections)
- Recent Facility Requests table displaying actual records
- Right-side complaint details panel integration
"""
import streamlit as st
import pandas as pd

from dashboard.components.admin_header import render_admin_header
from dashboard.components.complaint_details import render_complaint_details_panel
from dashboard.components.styles import get_priority_badge, get_status_badge, _clean_html
from src.data.complaints_store import get_complaints_df, get_control_centre_kpis


def render_page() -> None:
    """Renders the Administrator Control Centre Overview page."""
    # Top Header
    render_admin_header(
        page_title="Control Centre",
        subtitle="Operational telemetry, campus-wide facility health, and real-time maintenance dispatch.",
        kicker="FACILITY OPERATIONS · OVERVIEW",
    )

    df = get_complaints_df()
    kpis = get_control_centre_kpis(df)

    # =========================================================================
    # FOUR DYNAMIC KPI CARDS (Phase 3)
    # Total, New, In Progress, Resolved
    # =========================================================================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="dashboard-card" style="
                border-top: 4px solid #203A32;
                padding: 1.25rem 1.4rem 1rem 1.4rem;
                background: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);
                margin-bottom: 0.6rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.76rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.06em; color: #4A6357;">
                        Total Requests
                    </span>
                    <span style="font-size: 1.25rem;">📋</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #203A32; margin: 0.2rem 0; line-height: 1.1;">
                    {kpis["total"]}
                </div>
                <p style="margin: 0; font-size: 0.78rem; color: #6D8276;">
                    All campus registered issues
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View All Requests →", key="btn_kpi_nav_all", type="secondary", use_container_width=True):
            st.session_state["admin_active_page"] = "All Requests"
            st.rerun()

    with col2:
        st.markdown(
            f"""
            <div class="dashboard-card" style="
                border-top: 4px solid #D97706;
                padding: 1.25rem 1.4rem 1rem 1.4rem;
                background: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);
                margin-bottom: 0.6rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.76rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.06em; color: #92400E;">
                        New / Unassigned
                    </span>
                    <span style="font-size: 1.25rem;">🆕</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #D97706; margin: 0.2rem 0; line-height: 1.1;">
                    {kpis["new"]}
                </div>
                <p style="margin: 0; font-size: 0.78rem; color: #6D8276;">
                    Awaiting administrator triage
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View New Requests →", key="btn_kpi_nav_new", type="secondary", use_container_width=True):
            st.session_state["admin_active_page"] = "New / Unassigned"
            st.rerun()

    with col3:
        st.markdown(
            f"""
            <div class="dashboard-card" style="
                border-top: 4px solid #2563EB;
                padding: 1.25rem 1.4rem 1rem 1.4rem;
                background: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);
                margin-bottom: 0.6rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.76rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.06em; color: #1E40AF;">
                        In Progress
                    </span>
                    <span style="font-size: 1.25rem;">⏳</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #2563EB; margin: 0.2rem 0; line-height: 1.1;">
                    {kpis["in_progress"]}
                </div>
                <p style="margin: 0; font-size: 0.78rem; color: #6D8276;">
                    Dispatched &amp; active repairs
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View In Progress →", key="btn_kpi_nav_prog", type="secondary", use_container_width=True):
            st.session_state["admin_active_page"] = "In Progress"
            st.rerun()

    with col4:
        st.markdown(
            f"""
            <div class="dashboard-card" style="
                border-top: 4px solid #059669;
                padding: 1.25rem 1.4rem 1rem 1.4rem;
                background: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);
                margin-bottom: 0.6rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.76rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.06em; color: #065F46;">
                        Resolved
                    </span>
                    <span style="font-size: 1.25rem;">✅</span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #059669; margin: 0.2rem 0; line-height: 1.1;">
                    {kpis["resolved"]}
                </div>
                <p style="margin: 0; font-size: 0.78rem; color: #6D8276;">
                    Completed maintenance work
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View Resolved Archive →", key="btn_kpi_nav_resolved", type="secondary", use_container_width=True):
            st.session_state["admin_active_page"] = "Resolved"
            st.rerun()

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # RECENT FACILITY REQUESTS & RIGHT-SIDE DETAILS PANEL (Phase 3 & Phase 6)
    # =========================================================================
    selected_cid = st.session_state.get("admin_selected_complaint_id")
    selected_record = None
    if selected_cid and not df.empty:
        matching = df[df["complaint_id"] == selected_cid]
        if not matching.empty:
            selected_record = matching.iloc[0].to_dict()
        else:
            st.session_state["admin_selected_complaint_id"] = None

    if selected_record:
        col_list, col_panel = st.columns([1.35, 1.0], gap="large")
    else:
        col_list = st.container()
        col_panel = None

    with col_list:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.2rem; font-weight: 800; color: #203A32;">
                        Recent Facility Requests
                    </h3>
                    <p style="margin: 0.15rem 0 0 0; font-size: 0.82rem; color: #4A6357;">
                        Latest campus complaints awaiting or undergoing facility operations triage.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No facility complaints currently registered in the database.")
            return

        # Display latest submissions (top 6)
        recent_df = df.head(6)

        for _, row in recent_df.iterrows():
            cid = row["complaint_id"]
            title = row.get("title", "Issue")
            cat = row.get("facility_type") or row.get("category", "General")
            loc = row.get("location", "Campus")
            status = row.get("status", "Submitted")
            s_badge = get_status_badge(status)
            p_badge = get_priority_badge(row.get("priority_tier", "Medium"))
            dt = row.get("date_reported", "")

            # Highlight selected row
            is_active = (cid == selected_cid)
            card_border = "border: 2px solid #203A32; background: #FAFBF9;" if is_active else "border: 1px solid #DCE5D8; background: #FFFFFF;"

            st.markdown(
                _clean_html(
                    f"""
                    <div class="dashboard-card" style="
                        {card_border}
                        border-radius: 10px;
                        padding: 0.85rem 1.1rem;
                        margin-bottom: 0.6rem;
                        box-shadow: 0 1px 4px rgba(32, 58, 50, 0.03);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; flex-wrap: wrap;">
                            <div>
                                <span style="font-family: monospace; font-size: 0.78rem; font-weight: 800; color: #203A32; background: #DCE5D8; padding: 0.15rem 0.45rem; border-radius: 4px;">
                                    {cid}
                                </span>
                                <span style="font-size: 0.74rem; font-weight: 600; color: #4A6357; background: #F0F4ED; padding: 0.15rem 0.45rem; border-radius: 4px; margin-left: 0.3rem;">
                                    {cat}
                                </span>
                                <h4 style="margin: 0.25rem 0 0.15rem 0; font-size: 0.96rem; font-weight: 700; color: #203A32;">
                                    {title}
                                </h4>
                                <div style="font-size: 0.78rem; color: #6D8276;">
                                    📍 {loc} &bull; 📅 {dt}
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 0.4rem;">
                                {p_badge}
                                {s_badge}
                            </div>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            c_btn1, _ = st.columns([1.2, 3])
            with c_btn1:
                btn_label = "Viewing Details 🔍" if is_active else "Inspect Ticket →"
                if st.button(btn_label, key=f"btn_overview_inspect_{cid}", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state["admin_selected_complaint_id"] = cid
                    st.rerun()

    # Right-side complaint details panel
    if col_panel is not None and selected_record is not None:
        with col_panel:
            render_complaint_details_panel(selected_record)
