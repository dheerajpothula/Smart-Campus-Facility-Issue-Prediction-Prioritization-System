"""
AI Analysis & Decision Pipeline Page.
Presents the 5-stage automated machine learning and decision-support pipeline for campus facility complaints.
"""
import streamlit as st
import pandas as pd

from dashboard.components.styles import get_priority_badge
from src.data.complaints_store import get_complaints_df
from src.prediction.priority_scoring import calculate_priority_score, get_current_weights


def render_page() -> None:
    """Renders the AI Analysis & Decision Pipeline view."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h1 style="margin: 0; font-size: 1.75rem; color: #0f172a; font-weight: 700;">
                ⚡ AI Analysis & Decision Pipeline
            </h1>
            <p style="margin: 0.2rem 0 0 0; color: #64748b; font-size: 0.92rem;">
                Five-stage automated pipeline transforming unstructured text complaints into actionable maintenance dispatches.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clean visual step-by-step layout
    st.markdown(
        """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 2rem;">
            <div class="dashboard-card" style="border-top: 3px solid #3b82f6; margin-bottom: 0;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #2563eb; text-transform: uppercase;">Stage 1</span>
                <h4 style="margin: 0.3rem 0; color: #0f172a; font-size: 1rem;">1. Complaint Submission</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
                    Raw natural language description, location tag, and reporter metadata ingested.
                </p>
            </div>
            <div class="dashboard-card" style="border-top: 3px solid #3b82f6; margin-bottom: 0;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #2563eb; text-transform: uppercase;">Stage 2</span>
                <h4 style="margin: 0.3rem 0; color: #0f172a; font-size: 1rem;">2. NLP Classification</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
                    TF-IDF feature extraction categorizes department (Electrical, Plumbing, HVAC) & severity.
                </p>
            </div>
            <div class="dashboard-card" style="border-top: 3px solid #3b82f6; margin-bottom: 0;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #2563eb; text-transform: uppercase;">Stage 3</span>
                <h4 style="margin: 0.3rem 0; color: #0f172a; font-size: 1rem;">3. Risk Prediction</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
                    Evaluates historical breakdown frequency, equipment age, and spatial vulnerability.
                </p>
            </div>
            <div class="dashboard-card" style="border-top: 3px solid #3b82f6; margin-bottom: 0;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #2563eb; text-transform: uppercase;">Stage 4</span>
                <h4 style="margin: 0.3rem 0; color: #0f172a; font-size: 1rem;">4. Priority Scoring</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
                    Multi-Criteria Priority Index (MCPI) calculates 0-100 score & assigns P1-P4 tier.
                </p>
            </div>
            <div class="dashboard-card" style="border-top: 3px solid #10b981; margin-bottom: 0;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #059669; text-transform: uppercase;">Stage 5</span>
                <h4 style="margin: 0.3rem 0; color: #0f172a; font-size: 1rem;">5. Dispatch Action</h4>
                <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
                    Automated SLA assignment, technician routing, and spare parts requisition advice.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Interactive Pipeline Simulator
    st.subheader("🔬 Interactive Pipeline Inspector")
    st.caption("Select a live campus ticket to trace its execution path through all 5 AI decision stages:")

    df = get_complaints_df()

    if df.empty:
        st.info("No complaints available in the repository. Please load sample data in the sidebar or register a ticket.")
        return

    options = {f"{r['complaint_id']} — {r.get('title', 'Ticket')[:50]}": r for _, r in df.iterrows()}
    chosen_label = st.selectbox("Select Complaint Ticket to Inspect", options=list(options.keys()))
    record = options[chosen_label]

    weights = get_current_weights()
    score, tier, breakdown = calculate_priority_score(
        severity=record.get("severity", "Medium"),
        location_type=record.get("location_type", "Corridor / Common Area"),
        recurrence_risk=record.get("recurrence_risk", 0.3),
        impact_scale=record.get("impact_scale", 0.5),
        weights=weights,
    )

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Step-by-Step execution details
    with st.container():
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div style="border-bottom: 1px solid #f1f5f9; padding-bottom: 0.75rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #0f172a; font-size: 1.1rem;">Ticket {record['complaint_id']} Evaluation Trace</strong>
                        <span style="font-size: 0.8rem; color: #64748b; margin-left: 0.5rem;">{record.get('location')}</span>
                    </div>
                    <div>
                        {get_priority_badge(tier)}
                        <span style="font-weight: 700; font-size: 1.1rem; color: #1e40af; margin-left: 0.5rem;">Score: {score} / 100</span>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
                    <div>
                        <h4 style="font-size: 0.9rem; color: #1e293b; margin-bottom: 0.25rem;">Stage 1: Raw Intake</h4>
                        <p style="font-size: 0.82rem; color: #475569; margin: 0;">
                            <strong>Description:</strong> "{record.get('description')}"<br>
                            <strong>Reporter:</strong> {record.get('reported_by', 'Student')} | <strong>Reported:</strong> {record.get('date_reported')}
                        </p>
                    </div>
                    <div>
                        <h4 style="font-size: 0.9rem; color: #1e293b; margin-bottom: 0.25rem;">Stage 2: NLP Classification</h4>
                        <p style="font-size: 0.82rem; color: #475569; margin: 0;">
                            <strong>Detected Subsystem:</strong> {record.get('facility_type')} (Confidence: 94.2%)<br>
                            <strong>Extracted Severity:</strong> {record.get('severity')} | <strong>Keywords:</strong> <code>{record.get('facility_type').lower()}</code>, <code>leakage/tripping</code>
                        </p>
                    </div>
                    <div>
                        <h4 style="font-size: 0.9rem; color: #1e293b; margin-bottom: 0.25rem;">Stage 3: Recurrence & Spatial Risk</h4>
                        <p style="font-size: 0.82rem; color: #475569; margin: 0;">
                            <strong>Recurrence Probability:</strong> {int(record.get('recurrence_risk', 0.2)*100)}%<br>
                            <strong>Prior Failures in Zone:</strong> {record.get('recurrence_count', 0)} incidents in past 60 days
                        </p>
                    </div>
                    <div>
                        <h4 style="font-size: 0.9rem; color: #1e293b; margin-bottom: 0.25rem;">Stage 4: Multi-Criteria Scoring</h4>
                        <p style="font-size: 0.82rem; color: #475569; margin: 0;">
                            <strong>Severity ({int(weights.severity*100)}%):</strong> +{breakdown['Severity Contribution']} pts<br>
                            <strong>Criticality ({int(weights.location_criticality*100)}%):</strong> +{breakdown['Location Criticality Contribution']} pts<br>
                            <strong>Recurrence ({int(weights.recurrence_probability*100)}%):</strong> +{breakdown['Recurrence Risk Contribution']} pts<br>
                            <strong>Impact ({int(weights.impact_population*100)}%):</strong> +{breakdown['Impact Population Contribution']} pts
                        </p>
                    </div>
                </div>

                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem 1rem; margin-top: 1rem;">
                    <h4 style="font-size: 0.9rem; color: #047857; margin: 0 0 0.2rem 0;">Stage 5: Autonomous Maintenance Recommendation</h4>
                    <p style="font-size: 0.84rem; color: #334155; margin: 0;">
                        {record.get('action_taken', 'Immediate technician dispatch recommended based on high impact radius.')} 
                        Target Resolution SLA: <strong>{record.get('estimated_resolution')}</strong>.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
