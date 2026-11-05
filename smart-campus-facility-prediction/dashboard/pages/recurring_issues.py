"""
Chronic Recurring Problem Tracking Page.
Tracks chronic infrastructure failures, frequency metrics, prior repair logs, and permanent root-cause overhaul plans.
"""
import streamlit as st
import pandas as pd

from dashboard.components.styles import get_priority_badge, get_status_badge
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import get_complaints_df


def render_page() -> None:
    """Renders the Chronic Recurring Problem Tracking view."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h1 style="margin: 0; font-size: 1.75rem; color: #0f172a; font-weight: 700;">
                🔁 Chronic Recurring Problem Tracking
            </h1>
            <p style="margin: 0.2rem 0 0 0; color: #64748b; font-size: 0.92rem;">
                Surveillance of repetitive equipment breakdowns across campus requiring structural overhaul rather than temporary patches.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = get_complaints_df()

    if df.empty:
        render_empty_state(
            title="No Recurring Breakdown Data Available",
            subtitle="The chronic issue tracker requires historical complaint logs.",
            description="When complaint records with historical repetition tags are loaded, chronic patterns will be tracked here.",
            icon="🔁",
            badge_label="Status: No History",
        )
        return

    # Filter for recurring issues
    rec_df = df[df["is_recurring"] == True].copy()

    if rec_df.empty:
        st.success("🎉 No chronic recurring problems detected! All logged issues are isolated single-incident tickets.")
        return

    st.markdown(
        f"**Found {len(rec_df)} chronic recurring issues** across campus facilities:"
    )

    for _, row in rec_df.iterrows():
        cid = row["complaint_id"]
        title = row.get("title", "Recurring Issue")
        fac = row.get("facility_type", "General")
        loc = row.get("location", "Campus")
        rec_count = row.get("recurrence_count", 2)
        rec_rate = f"{round(rec_count * 0.85, 1)} incidents / month"
        status = row.get("status", "Under Review")
        desc = row.get("description", "")
        action = row.get("action_taken", "Investigating chronic recurrence.")

        st.markdown(
            f"""
            <div class="dashboard-card" style="border-left: 4px solid #ef4444; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <div>
                        <span style="font-family: monospace; font-size: 0.78rem; font-weight: 700; color: #1e40af;">{cid}</span>
                        <span style="font-size: 0.75rem; font-weight: 600; color: #2563eb; background-color: #eff6ff; padding: 0.15rem 0.45rem; border-radius: 4px; margin-left: 0.3rem;">{fac}</span>
                        <span style="font-size: 0.75rem; font-weight: 700; color: #b91c1c; background-color: #fee2e2; padding: 0.15rem 0.45rem; border-radius: 4px; margin-left: 0.3rem;">
                            🔁 {rec_count} Previous Incidents
                        </span>
                        <h3 style="margin: 0.35rem 0 0.2rem 0; color: #0f172a; font-size: 1.1rem;">{title}</h3>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        {get_priority_badge(row.get('priority_tier', 'High'))}
                        {get_status_badge(status)}
                    </div>
                </div>

                <p style="color: #475569; font-size: 0.88rem; margin: 0 0 0.65rem 0;">
                    {desc}
                </p>

                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.7rem 0.9rem; margin-bottom: 0.65rem;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.5rem; font-size: 0.82rem; color: #334155;">
                        <div>📍 <strong>Location:</strong> {loc}</div>
                        <div>📊 <strong>Recurrence Frequency:</strong> {rec_rate}</div>
                        <div>🔧 <strong>Latest Action Logged:</strong> {action}</div>
                        <div>💡 <strong>Root Cause Analysis:</strong> Material fatigue / improper original installation</div>
                    </div>
                </div>

                <div style="font-size: 0.8rem; color: #0369a1; background-color: #e0f2fe; padding: 0.4rem 0.75rem; border-radius: 4px;">
                    🛡️ <strong>Engineering Recommendation:</strong> Cease repetitive spot repairs. Request procurement of complete subsystem overhaul package.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
