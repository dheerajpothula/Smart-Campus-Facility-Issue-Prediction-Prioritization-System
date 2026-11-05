"""
Overview Page — Maintenance Operations Dashboard.
Presents campus-wide operational KPIs, facility distributions, and interactive filtering with modern SaaS styling.
"""
import streamlit as st
import pandas as pd

from dashboard.components.styles import render_kpi, get_priority_badge, get_status_badge
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import get_complaints_df, get_kpi_summary


def render_page() -> None:
    """Renders the Maintenance Operations Dashboard view."""
    # Header
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h1 style="margin: 0; font-size: 1.75rem; color: #0f172a; font-weight: 700;">
                📊 Maintenance Operations Dashboard
            </h1>
            <p style="margin: 0.2rem 0 0 0; color: #64748b; font-size: 0.92rem;">
                Campus-wide infrastructure surveillance, workload KPIs, and maintenance dispatch telemetry.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch live data
    raw_df = get_complaints_df()

    if raw_df.empty:
        render_empty_state(
            title="Maintenance Operations Repository Unpopulated",
            subtitle="No complaint data or operational records currently loaded.",
            description="Upload university records via Complaint Management or click 'Reset Default' in the sidebar demo controls to view operational metrics.",
            icon="📭",
            badge_label="Status: No Data",
        )
        return

    # Filter Bar
    with st.expander("🔎 Interactive Operational Filters", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            facility_list = ["All Facilities"] + sorted(list(raw_df["facility_type"].dropna().unique()))
            selected_facility = st.selectbox("Facility Category", options=facility_list)
        with f_col2:
            location_list = ["All Locations"] + sorted(list(raw_df["location"].dropna().unique()))
            selected_location = st.selectbox("Location / Building", options=location_list)
        with f_col3:
            severity_list = ["All Severities", "Critical", "High", "Medium", "Low"]
            selected_severity = st.selectbox("Severity Level", options=severity_list)
        with f_col4:
            status_list = ["All Statuses", "Submitted", "Under Review", "Assigned", "In Progress", "Resolved"]
            selected_status = st.selectbox("Maintenance Status", options=status_list)

    # Apply filters
    filtered_df = raw_df.copy()
    if selected_facility != "All Facilities":
        filtered_df = filtered_df[filtered_df["facility_type"] == selected_facility]
    if selected_location != "All Locations":
        filtered_df = filtered_df[filtered_df["location"] == selected_location]
    if selected_severity != "All Severities":
        filtered_df = filtered_df[filtered_df["severity"] == selected_severity]
    if selected_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]

    # Calculate KPIs from filtered data
    kpis = get_kpi_summary(filtered_df)

    # Render KPI Cards in a clean 6-column grid
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_kpi("Total Issues", kpis["total"], caption="Active campus scope", icon="📋")
    with k2:
        render_kpi("Open Backlog", kpis["open"], caption="Awaiting completion", icon="⏳")
    with k3:
        render_kpi("High Priority", kpis["high_priority"], caption="P1 & P2 Critical/High", icon="🚨")
    with k4:
        render_kpi("Recurring", kpis["recurring"], caption="Multi-incident repeat", icon="🔁")
    with k5:
        render_kpi("Avg Resolution", kpis["avg_resolution_time"], caption="Rolling turnaround", icon="⏱️")
    with k6:
        render_kpi("Risk Index", kpis["facility_risk_overview"], caption="Campus vulnerability", icon="🛡️")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("No complaint records match the active filter criteria. Clear filters to resume view.")
        return

    # Visual Distribution Charts in Deep Charcoal and Soft Tan
    c_dist1, c_dist2 = st.columns(2)

    with c_dist1:
        st.markdown(
            """
            <div class="dashboard-card">
                <h3 style="margin-top: 0; font-size: 1.05rem; color: #1A1A1A;">
                    🏢 Complaints by Facility Subsystem
                </h3>
                <p style="color: #555555; font-size: 0.8rem; margin-bottom: 0.8rem;">
                    Proportion of issues across campus engineering departments.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        facility_counts = filtered_df["facility_type"].value_counts()
        st.bar_chart(facility_counts, color="#1A1A1A")

    with c_dist2:
        st.markdown(
            """
            <div class="dashboard-card">
                <h3 style="margin-top: 0; font-size: 1.05rem; color: #1A1A1A;">
                    ⚠️ Severity & Risk Tier Distribution
                </h3>
                <p style="color: #555555; font-size: 0.8rem; margin-bottom: 0.8rem;">
                    Breakdown of urgent safety hazards vs routine maintenance.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sev_counts = filtered_df["severity"].value_counts()
        st.bar_chart(sev_counts, color="#D8CFBD")

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # Location-wise breakdown table
    st.markdown(
        """
        <div class="dashboard-card">
            <h3 style="margin-top: 0; font-size: 1.05rem; color: #0f172a;">
                📍 Campus Location Vulnerability & Density Analysis
            </h3>
            <p style="color: #64748b; font-size: 0.82rem; margin-bottom: 0.5rem;">
                Cluster distribution of registered incidents across campus buildings and facility zones.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    loc_summary = (
        filtered_df.groupby("location")
        .agg(
            Total_Complaints=("complaint_id", "count"),
            Open_Complaints=("status", lambda s: (s != "Resolved").sum()),
            Critical_Complaints=("severity", lambda sev: (sev.isin(["Critical", "High"])).sum()),
            Recurring_Incidents=("is_recurring", lambda r: r.sum()),
        )
        .reset_index()
        .sort_values(by="Total_Complaints", ascending=False)
    )

    st.dataframe(
        loc_summary,
        column_config={
            "location": st.column_config.TextColumn("Campus Location / Facility Area"),
            "Total_Complaints": st.column_config.NumberColumn("Total Issues"),
            "Open_Complaints": st.column_config.NumberColumn("Pending"),
            "Critical_Complaints": st.column_config.NumberColumn("P1/P2 Critical"),
            "Recurring_Incidents": st.column_config.NumberColumn("Recurring"),
        },
        use_container_width=True,
        hide_index=True,
    )
