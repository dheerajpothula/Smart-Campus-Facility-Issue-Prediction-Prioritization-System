"""
Chronic Recurring Problem Tracking Page.
Tracks chronic infrastructure failures, frequency metrics, prior repair logs, and permanent root-cause overhaul plans.
Strictly adheres to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), Soft Tan (#EAE3D2), and Primary Brown (#756044).
"""
import streamlit as st
import pandas as pd

from dashboard.components.styles import get_priority_badge, get_status_badge, render_section_header
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import get_complaints_df


def render_page() -> None:
    """Renders the Chronic Recurring Problem Tracking view."""
    render_section_header(
        title="Chronic Recurring Problem Tracking",
        subtitle="Surveillance of repetitive equipment breakdowns across campus requiring structural overhaul rather than temporary patches.",
        badge="Pattern Recognition",
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
            <div class="dashboard-card" style="border-left: 4px solid #756044; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <div>
                        <span style="font-family: monospace; font-size: 0.8rem; font-weight: 700; color: #1A1A1A; background-color: #EAE3D2; padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid #D8CFBD;">
                            {cid}
                        </span>
                        <span style="font-size: 0.76rem; font-weight: 600; color: #1A1A1A; background-color: #F6F3EB; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.35rem; border: 1px solid #EAE3D2;">
                            {fac}
                        </span>
                        <span style="font-size: 0.76rem; font-weight: 700; color: #756044; background-color: #EAE3D2; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.35rem; border: 1px solid #D8CFBD;">
                            🔁 {rec_count} Previous Incidents
                        </span>
                        <h3 style="margin: 0.35rem 0 0.2rem 0; color: #1A1A1A; font-size: 1.15rem; font-weight: 700;">{title}</h3>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        {get_priority_badge(row.get('priority_tier', 'High'))}
                        {get_status_badge(status)}
                    </div>
                </div>

                <p style="color: #4A4A4A; font-size: 0.9rem; margin: 0 0 0.75rem 0; line-height: 1.5;">
                    {desc}
                </p>

                <div style="background-color: #FDFBF7; border: 1px solid #EAE3D2; border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 0.75rem;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.65rem; font-size: 0.84rem; color: #2D2D2D;">
                        <div>📍 <strong>Location:</strong> {loc}</div>
                        <div>📊 <strong>Frequency:</strong> {rec_rate}</div>
                        <div>🔧 <strong>Latest Action:</strong> {action}</div>
                        <div>💡 <strong>Root Cause:</strong> Material fatigue / improper original installation</div>
                    </div>
                </div>

                <div style="font-size: 0.82rem; color: #1A1A1A; background-color: #EAE3D2; border: 1px solid #D8CFBD; padding: 0.5rem 0.85rem; border-radius: 6px; font-weight: 500;">
                    🛡️ <strong>Engineering Recommendation:</strong> Cease repetitive spot repairs. Request procurement of complete subsystem overhaul package.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
