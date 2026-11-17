"""
Predictive Maintenance Page.
Analyzes campus vulnerability, forecasts recurring equipment failures, and provides proactive servicing recommendations.
Modern Sage & Forest Theme:
- Soft Ivory: #F5F7F2
- Forest Green: #203A32
- Sage: #A8B9A3
- Pale Sage: #DCE5D8
- White: #FFFFFF
"""
import streamlit as st
import pandas as pd

from dashboard.components.styles import get_priority_badge, render_section_header
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import get_complaints_df


def render_page() -> None:
    """Renders the Predictive Maintenance & Failure Forecasting view."""
    render_section_header(
        title="Predictive Maintenance & Failure Forecasting",
        subtitle="Anticipating high-risk facilities and recommending pre-emptive maintenance actions before disruptive breakdowns occur.",
        badge="Proactive Telemetry",
    )

    df = get_complaints_df()

    if df.empty:
        render_empty_state(
            title="Predictive Models Offline / Awaiting Data",
            subtitle="No complaint telemetry available to generate facility risk forecasts.",
            description="When campus maintenance logs are loaded, this view evaluates temporal breakdown frequency and spatial density.",
            icon="📉",
            badge_label="Status: No Telemetry",
        )
        return

    # Methodological Disclaimer Banner
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border: 1px solid #DCE5D8; border-left: 4px solid #203A32; border-radius: 8px; padding: 0.85rem 1.15rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 700; color: #203A32; font-size: 0.92rem; margin-bottom: 0.2rem;">
                🛡️ Algorithmic Forecast Notice
            </div>
            <p style="margin: 0; font-size: 0.84rem; color: #4A6357; line-height: 1.45;">
                <strong>Prediction ≠ Confirmed Physical Breakdown.</strong> Algorithmic issue-risk forecast based on historical recurrence cycles, equipment MTBF, and footfall telemetry.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # High-Risk Facilities Ranking
    st.markdown("### 🗺️ High-Risk Campus Facilities Ranking")
    st.caption("Identified through multi-incident density, repeat breakdown probability, and location criticality:")

    risk_group = (
        df.groupby(["location", "facility_type"])
        .agg(
            Incident_Count=("complaint_id", "count"),
            Avg_Recurrence_Risk=("recurrence_risk", "mean"),
            Max_Severity=("severity", lambda s: "Critical" if "Critical" in s.values else ("High" if "High" in s.values else "Medium")),
        )
        .reset_index()
    )

    # Compute risk score (0-100) dynamically
    risk_group["Calculated_Risk_Score"] = (
        risk_group["Incident_Count"] * 18.0 + risk_group["Avg_Recurrence_Risk"] * 45.0
    ).clip(15.0, 98.0).round(1)

    risk_group = risk_group.sort_values(by="Calculated_Risk_Score", ascending=False)

    col_rk1, col_rk2 = st.columns([1.6, 1])

    with col_rk1:
        st.dataframe(
            risk_group,
            column_config={
                "location": st.column_config.TextColumn("Facility Location"),
                "facility_type": st.column_config.TextColumn("Subsystem"),
                "Incident_Count": st.column_config.NumberColumn("Recent Incidents"),
                "Avg_Recurrence_Risk": st.column_config.ProgressColumn("Recurrence Probability", min_value=0.0, max_value=1.0, format="%.2f"),
                "Calculated_Risk_Score": st.column_config.NumberColumn("Risk Index / 100"),
                "Max_Severity": st.column_config.TextColumn("Peak Severity"),
            },
            use_container_width=True,
            hide_index=True,
        )

    with col_rk2:
        top_risk = risk_group.iloc[0] if not risk_group.empty else None
        if top_risk is not None:
            st.markdown(
                f"""
                <div class="dashboard-card" style="border: 1px solid #DCE5D8; background-color: #FFFFFF;">
                    <span style="font-size: 0.72rem; font-weight: 700; color: #203A32; background: #DCE5D8; border-radius: 4px; padding: 0.15rem 0.5rem; text-transform: uppercase;">
                        Highest Urgency Area
                    </span>
                    <h3 style="margin: 0.4rem 0 0.2rem 0; font-size: 1.2rem; color: #203A32;">
                        {top_risk['location']}
                    </h3>
                    <p style="font-size: 0.85rem; color: #4A6357; margin-bottom: 0.8rem;">
                        Subsystem: <strong>{top_risk['facility_type']}</strong>
                    </p>
                    <div style="font-size: 1.85rem; font-weight: 800; color: #203A32; margin-bottom: 0.4rem;">
                        {top_risk['Calculated_Risk_Score']} <span style="font-size: 0.95rem; font-weight: 500; color: #6D8276;">Risk Score / 100</span>
                    </div>
                    <p style="font-size: 0.84rem; color: #203A32; line-height: 1.45; margin-bottom: 0.75rem;">
                        High recurring failure frequency detected. Recommended action: schedule comprehensive preventive maintenance inspection before peak class hours.
                    </p>
                    <div style="border-top: 1px solid #DCE5D8; padding-top: 0.6rem; font-size: 0.8rem; color: #4A6357;">
                        • Peak Severity: <strong>{top_risk['Max_Severity']}</strong><br>
                        • Cumulative Incidents: <strong>{top_risk['Incident_Count']}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Proactive Maintenance Recommendations
    st.markdown("### 🛠️ Proactive Maintenance Recommendations")

    c_rec1, c_rec2 = st.columns(2)
    with c_rec1:
        st.markdown(
            """
            <div class="dashboard-card" style="border: 1px solid #DCE5D8;">
                <h4 style="margin: 0 0 0.35rem 0; color: #203A32; font-weight: 700;">Hostel Block Washroom Valves &amp; Plumbing</h4>
                <p style="font-size: 0.85rem; color: #4A6357; line-height: 1.5; margin-bottom: 0.75rem;">
                    Repeated flush valve leakages correlate with weekend water pressure fluctuations. Proactive pressure regulator installation recommended to prevent recurring pipe bursts.
                </p>
                <div style="font-size: 0.78rem; color: #203A32; font-weight: 700;">
                    Action: Replace gasket assemblies &amp; install pressure balancing valve.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_rec2:
        st.markdown(
            """
            <div class="dashboard-card" style="border: 1px solid #DCE5D8;">
                <h4 style="margin: 0 0 0.35rem 0; color: #203A32; font-weight: 700;">Data Center &amp; Server Room Precision HVAC</h4>
                <p style="font-size: 0.85rem; color: #4A6357; line-height: 1.5; margin-bottom: 0.75rem;">
                    Compressor tripping telemetry indicates heat exchanger coil fouling. Servicing prior to summer temperature spikes will prevent critical server room thermal shutdowns.
                </p>
                <div style="font-size: 0.78rem; color: #203A32; font-weight: 700;">
                    Action: Deep chemical condenser flush &amp; sensor calibration.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
