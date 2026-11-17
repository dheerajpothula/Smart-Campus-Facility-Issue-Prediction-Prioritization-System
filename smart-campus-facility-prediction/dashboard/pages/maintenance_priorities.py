"""
Intelligent Maintenance Priority Queue Page.
Displays real-time algorithmic ranking of active campus work orders with sorting, filtering, and dispatch actions.
Strictly adheres to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2), and Primary Brown (#756044).
"""
import pandas as pd
import streamlit as st

from dashboard.components.styles import get_priority_badge, get_status_badge, render_section_header
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import get_complaints_df, update_complaint_status
from src.prediction.priority_scoring import get_current_weights


def render_page() -> None:
    """Renders the Intelligent Maintenance Priority Queue view."""
    render_section_header(
        title="Intelligent Maintenance Priority Queue",
        subtitle="Dynamic multi-factor ranking dispatch queue ordering campus tickets by urgency, recurrence, and impact.",
        badge="MCPI Prioritization Engine",
    )

    df = get_complaints_df()

    if df.empty:
        render_empty_state(
            title="Priority Dispatch Queue Empty",
            subtitle="There are currently no active tickets to prioritize.",
            description="Register new complaints or load the demo dataset to view the prioritized work orders.",
            icon="⚖️",
            badge_label="Status: Queue Idle",
        )
        return

    # Filter & Sort Controls Bar
    with st.expander("⚙️ Queue Sorting & Multi-Factor Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sort_by = st.selectbox(
                "Sort Work Orders By",
                ["Priority Score (Highest First)", "Recurrence Risk (Highest First)", "Date Reported (Newest First)"],
            )
        with c2:
            tier_filter = st.selectbox("Priority Tier Filter", ["All Tiers", "Critical", "High", "Medium", "Low"])
        with c3:
            fac_filter = st.selectbox("Facility Category", ["All Facilities"] + sorted(list(df["facility_type"].dropna().unique())))
        with c4:
            status_filter = st.selectbox("Status Filter", ["All Active", "Submitted", "Under Review", "Assigned", "In Progress", "Resolved"])

    # Apply Filters
    q_df = df.copy()
    if tier_filter != "All Tiers":
        q_df = q_df[q_df["priority_tier"] == tier_filter]
    if fac_filter != "All Facilities":
        q_df = q_df[q_df["facility_type"] == fac_filter]
    if status_filter == "All Active":
        q_df = q_df[q_df["status"] != "Resolved"]
    elif status_filter != "All":
        q_df = q_df[q_df["status"] == status_filter]

    # Apply Sorting
    if "Priority Score" in sort_by:
        q_df = q_df.sort_values(by="priority_score", ascending=False)
    elif "Recurrence Risk" in sort_by:
        q_df = q_df.sort_values(by="recurrence_risk", ascending=False)
    elif "Date Reported" in sort_by:
        if "date_reported" in q_df.columns:
            q_df = q_df.sort_values(by="date_reported", ascending=False)

    weights = get_current_weights()
    st.markdown(
        f"<div style='margin: 0.5rem 0 1rem 0; font-size: 0.88rem; color: #555555; background: #FFFFFF; border: 1px solid #EAE3D2; border-radius: 8px; padding: 0.6rem 0.9rem;'>"
        f"Active Weights: <strong>Severity ({int(weights.severity*100)}%)</strong> • "
        f"<strong>Criticality ({int(weights.location_criticality*100)}%)</strong> • "
        f"<strong>Recurrence ({int(weights.recurrence_probability*100)}%)</strong> • "
        f"<strong>Impact ({int(weights.impact_population*100)}%)</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if q_df.empty:
        st.info("No work orders match the current filter selection.")
        return

    # Render Clean Table / Card Rows
    st.markdown(f"**Showing {len(q_df)} prioritized work orders:**")

    for rank, (_, row) in enumerate(q_df.iterrows(), start=1):
        cid = row["complaint_id"]
        tier = row.get("priority_tier", "Low")
        score = row.get("priority_score", 0.0)
        p_badge = get_priority_badge(tier)
        s_badge = get_status_badge(row.get("status", "Under Review"))
        title = row.get("title", "Work Order")
        desc = row.get("description", "")
        loc = row.get("location", "Campus")
        rec_count = row.get("recurrence_count", 0)
        is_rec = row.get("is_recurring", False)
        rec_pill = f"<span style='background-color: #EBDCDA; color: #1A1A1A; border: 1px solid #D3BCB9; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.72rem; font-weight: 700;'>🔁 Repeat ({rec_count}x)</span>" if is_rec else ""

        st.markdown(
            f"""
            <div class="dashboard-card" style="margin-bottom: 0.85rem; border-left: 4px solid #756044;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <span style="font-size: 0.78rem; font-weight: 700; color: #756044; background-color: #EAE3D2; padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid #D8CFBD;">
                            Rank #{rank}
                        </span>
                        <span style="font-family: monospace; font-size: 0.8rem; font-weight: 700; color: #1A1A1A; margin-left: 0.35rem;">
                            {cid}
                        </span>
                        <span style="font-size: 0.76rem; color: #555555; background-color: #F6F3EB; padding: 0.15rem 0.45rem; border-radius: 4px; margin-left: 0.35rem; border: 1px solid #EAE3D2;">
                            {row.get('facility_type')}
                        </span>
                        {rec_pill}
                        <h4 style="margin: 0.35rem 0 0.2rem 0; color: #1A1A1A; font-size: 1.08rem; font-weight: 700;">{title}</h4>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        <span style="font-size: 1.15rem; font-weight: 800; color: #756044;">{score} pts</span>
                        {p_badge}
                        {s_badge}
                    </div>
                </div>

                <p style="color: #2D2D2D; font-size: 0.88rem; margin: 0.4rem 0 0.6rem 0; line-height: 1.5;">{desc}</p>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #EAE3D2; padding-top: 0.5rem; font-size: 0.8rem; color: #555555; flex-wrap: wrap; gap: 0.5rem;">
                    <div>📍 <strong>Location:</strong> {loc} • Reported: {row.get('date_reported')}</div>
                    <div>⚡ <strong>Action:</strong> {row.get('action_taken', 'Pending dispatch review')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
