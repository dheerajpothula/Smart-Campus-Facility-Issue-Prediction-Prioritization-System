"""
Facility Operations Control Centre — Reports & Operational Analytics.
Implements Phase 12:
- Real-data analytics only: no fabricated metrics or fake statistics.
- Complaint trends by date.
- Category-wise distribution.
- Building / location-wise distribution.
- Status distribution.
- Actual resolution turnaround analysis for resolved tickets.
- MCPI priority tier distribution.
- Honest empty/unavailable states.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from dashboard.components.admin_header import render_admin_header
from dashboard.components.styles import render_kpi, _clean_html
from src.data.complaints_store import get_complaints_df


def render_reports_page() -> None:
    """Renders the Facility Operations Reports and Analytics page."""
    render_admin_header(
        page_title="Operational Reports & Analytics",
        subtitle="Empirical performance analytics, incident distributions, and facility vulnerability metrics.",
        kicker="FACILITY OPERATIONS · REPORTS",
    )

    df = get_complaints_df()

    if df.empty:
        st.info("No complaint data currently available to generate operational reports.")
        return

    # Top KPI Metrics from Actual Data
    total_tickets = len(df)
    resolved_tickets = int((df["status"] == "Resolved").sum()) if "status" in df.columns else 0
    in_prog_tickets = int(df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum()) if "status" in df.columns else 0
    high_prio_tickets = int(df["priority_tier"].isin(["Critical", "High"]).sum()) if "priority_tier" in df.columns else 0
    resolution_rate = f"{round((resolved_tickets / total_tickets * 100), 1)}%" if total_tickets > 0 else "0.0%"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi("Total Volume", total_tickets, caption="Lifetime records", icon="📋")
    with k2:
        render_kpi("Resolved Tickets", resolved_tickets, caption="Closed maintenance", icon="✅")
    with k3:
        render_kpi("Active Backlog", in_prog_tickets, caption="Ongoing repairs", icon="⏳")
    with k4:
        render_kpi("High/Critical Priority", high_prio_tickets, caption="P1 & P2 hazards", icon="🚨")
    with k5:
        render_kpi("Resolution Rate", resolution_rate, caption="Completed ratio", icon="📈")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 1. COMPLAINT TRENDS BY DATE
    st.markdown(
        """
        <div class="dashboard-card" style="margin-bottom: 0.75rem;">
            <h3 style="margin-top: 0; font-size: 1.1rem; color: #203A32; font-weight: 750;">
                📅 Incident Ingestion Trends by Date
            </h3>
            <p style="color: #4A6357; font-size: 0.84rem; margin-bottom: 0.8rem;">
                Empirical count of facility complaints registered across campus by submission date.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "date_reported" in df.columns and not df["date_reported"].dropna().empty:
        # Extract date component (YYYY-MM-DD)
        dates = pd.to_datetime(df["date_reported"], errors="coerce").dt.date
        date_counts = dates.value_counts().sort_index()

        if not date_counts.empty:
            c_trend1, c_trend2 = st.columns([2.2, 1])
            with c_trend1:
                st.bar_chart(date_counts, color="#203A32")
            with c_trend2:
                trend_table = pd.DataFrame({
                    "Date": [str(d) for d in date_counts.index],
                    "Complaints Logged": date_counts.values,
                })
                st.dataframe(trend_table, use_container_width=True, hide_index=True)
        else:
            st.info("No valid timestamp data available for date trend analysis.")
    else:
        st.info("Date reported data unavailable.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 2. CATEGORY-WISE & STATUS DISTRIBUTIONS
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.75rem;">
                <h3 style="margin-top: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    🏢 Complaints by Facility Subsystem
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin-bottom: 0.6rem;">
                    Distribution across campus engineering departments.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cat_col = "facility_type" if "facility_type" in df.columns else "category"
        if cat_col in df.columns and not df[cat_col].dropna().empty:
            cat_counts = df[cat_col].value_counts()
            st.bar_chart(cat_counts, color="#203A32")
        else:
            st.info("Category breakdown data unavailable.")

    with col_c2:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.75rem;">
                <h3 style="margin-top: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    🔄 Maintenance Status Distribution
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin-bottom: 0.6rem;">
                    Proportion of tickets across lifecycle stages.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if "status" in df.columns and not df["status"].dropna().empty:
            stat_counts = df["status"].value_counts()
            st.bar_chart(stat_counts, color="#A8B9A3")
        else:
            st.info("Status distribution data unavailable.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 3. BUILDING / LOCATION ANALYSIS & MCPI PRIORITY TIERS
    col_l1, col_l2 = st.columns(2)

    with col_l1:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.75rem;">
                <h3 style="margin-top: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    📍 Building &amp; Location Density
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin-bottom: 0.6rem;">
                    Registered complaints clustered by campus facility buildings.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        loc_col = "building" if "building" in df.columns and not df["building"].dropna().empty else "location"
        if loc_col in df.columns and not df[loc_col].dropna().empty:
            loc_counts = df[loc_col].value_counts().head(8)
            st.bar_chart(loc_counts, color="#203A32")
        else:
            st.info("Location distribution data unavailable.")

    with col_l2:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.75rem;">
                <h3 style="margin-top: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    🚨 MCPI Priority Distribution
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin-bottom: 0.6rem;">
                    Risk triage breakdown computed via multi-criteria facility scoring.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if "priority_tier" in df.columns and not df["priority_tier"].dropna().empty:
            prio_order = ["Critical", "High", "Medium", "Low"]
            prio_counts = df["priority_tier"].value_counts().reindex(prio_order).fillna(0)
            st.bar_chart(prio_counts, color="#D97706")
        else:
            st.info("Priority distribution data unavailable.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 4. RESOLUTION TURNAROUND ANALYSIS (for Resolved tickets)
    st.markdown(
        """
        <div class="dashboard-card" style="margin-bottom: 0.75rem;">
            <h3 style="margin-top: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                ⏱️ Resolution Turnaround Analysis
            </h3>
            <p style="color: #4A6357; font-size: 0.82rem; margin-bottom: 0.6rem;">
                Empirical audit of closed requests showing reported dates, resolution remarks, and dispatch tracking.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    resolved_df = df[df["status"] == "Resolved"] if "status" in df.columns else pd.DataFrame()
    if not resolved_df.empty:
        summary_cols = ["complaint_id", "title", "facility_type", "location", "date_reported"]
        if "action_taken" in resolved_df.columns:
            summary_cols.append("action_taken")
        available_cols = [c for c in summary_cols if c in resolved_df.columns]
        st.dataframe(resolved_df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No resolved tickets currently in repository to compute turnaround metrics.")
