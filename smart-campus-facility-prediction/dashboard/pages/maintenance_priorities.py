"""
Intelligent Maintenance Priority Queue Page.
Displays real-time algorithmic ranking of active campus work orders with sorting, filtering, and dispatch actions.
"""
import pandas as pd
import streamlit as st

from dashboard.components.styles import get_priority_badge, get_status_badge
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import get_complaints_df, update_complaint_status
from src.prediction.priority_scoring import get_current_weights


def render_page() -> None:
    """Renders the Intelligent Maintenance Priority Queue view."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h1 style="margin: 0; font-size: 1.75rem; color: #0f172a; font-weight: 700;">
                🚨 Intelligent Maintenance Priority Queue
            </h1>
            <p style="margin: 0.2rem 0 0 0; color: #64748b; font-size: 0.92rem;">
                Dynamic multi-factor ranking dispatch queue ordering campus tickets by urgency, recurrence, and impact.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
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
    with st.expander("⚙️ Queue Sorting & Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sort_by = st.selectbox(
                "Sort Work Orders By",
                ["Priority Score (Highest First)", "Recurrence Risk (Highest First)", "Date Reported (Newest First)"],
            )
        with c2:
            tier_filter = st.selectbox("Priority Tier Filter", ["All Tiers", "Critical", "High", "Medium", "Low"])
        with c3:
            fac_filter = st.selectbox("Facility Filter", ["All Facilities"] + sorted(list(df["facility_type"].dropna().unique())))
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
        f"<div style='margin: 0.5rem 0; font-size: 0.85rem; color: #475569;'>"
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

    for _, row in q_df.iterrows():
        cid = row["complaint_id"]
        tier = row.get("priority_tier", "Low")
        score = row.get("priority_score", 0.0)
        p_badge = get_priority_badge(tier)
        s_badge = get_status_badge(row.get("status", "Under Review"))
        title = row.get("title", "Issue")
        desc = row.get("description", "")
        fac = row.get("facility_type", "General")
        loc = row.get("location", "Campus")
        rec_risk = int(row.get("recurrence_risk", 0.0) * 100)
        action = row.get("action_taken", "Assign maintenance squad.")

        st.markdown(
            f"""
            <div class="dashboard-card" style="margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.4rem;">
                    <div>
                        <span style="font-family: monospace; font-size: 0.8rem; font-weight: 700; color: #1e40af;">{cid}</span>
                        <span style="font-size: 0.75rem; font-weight: 600; color: #2563eb; background-color: #eff6ff; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.35rem;">{fac}</span>
                        <strong style="font-size: 1rem; color: #0f172a; margin-left: 0.4rem;">{title}</strong>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span style="font-size: 0.8rem; color: #64748b;">Recurrence Risk: <strong>{rec_risk}%</strong></span>
                        <span style="font-size: 0.85rem; font-weight: 700; color: #1e40af; background-color: #f1f5f9; padding: 0.15rem 0.5rem; border-radius: 4px;">Score: {score}</span>
                        {p_badge}
                        {s_badge}
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-bottom: 0.5rem;">
                    {desc}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 0.5rem; font-size: 0.8rem; color: #64748b; flex-wrap: wrap; gap: 0.5rem;">
                    <span>📍 <strong>Location:</strong> {loc} (Reported: {row.get('date_reported', 'Recent')})</span>
                    <span>🛠️ <strong>Recommended Action:</strong> <span style="color: #0f172a;">{action}</span></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_act1, col_act2, _ = st.columns([1, 1, 4])
        with col_act1:
            if row["status"] != "Dispatched":
                if st.button("Dispatch Crew", key=f"q_disp_{cid}", type="primary"):
                    update_complaint_status(cid, "Dispatched")
                    st.rerun()
        with col_act2:
            if row["status"] != "Resolved":
                if st.button("Mark Resolved", key=f"q_res_{cid}", type="secondary"):
                    update_complaint_status(cid, "Resolved")
                    st.rerun()
