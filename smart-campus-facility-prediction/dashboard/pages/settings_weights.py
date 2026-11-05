"""
Settings & Priority Weights Configuration Page.
Allows campus administrators to configure the multi-criteria priority scoring weights with validation and live updates.
"""
import streamlit as st

from src.prediction.priority_scoring import (
    PriorityWeights,
    get_current_weights,
    update_weights,
    reset_weights_to_default,
)


def render_page() -> None:
    """Renders the Configurable Priority Weights & System Settings view."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h1 style="margin: 0; font-size: 1.75rem; color: #0f172a; font-weight: 700;">
                ⚙️ Configurable Priority Weights & Scoring Settings
            </h1>
            <p style="margin: 0.2rem 0 0 0; color: #64748b; font-size: 0.92rem;">
                Adjust the sensitivity coefficients of the Multi-Criteria Priority Index (MCPI) algorithm.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current = get_current_weights()

    st.markdown(
        """
        <div class="dashboard-card">
            <h3 style="margin-top: 0; color: #0f172a; font-size: 1.1rem;">
                📐 Mathematical Foundation: Multi-Criteria Priority Index
            </h3>
            <p style="color: #475569; font-size: 0.88rem; margin-bottom: 0.5rem;">
                Every active work order is ranked by calculating an objective composite score (0–100):
            </p>
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem 1rem; font-family: monospace; font-size: 0.95rem; color: #1e40af; margin-bottom: 0.5rem;">
                Priority Score = 100 × [ (w₁ × Severity) + (w₂ × Criticality) + (w₃ × Recurrence) + (w₄ × Impact) ]
            </div>
            <p style="color: #64748b; font-size: 0.82rem; margin: 0;">
                <strong>Constraint:</strong> The sum of all four coefficients must equal 1.0 (100%) to maintain calibrated 0–100 score distribution.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sliders for each of the 4 weights
    col_w1, col_w2 = st.columns(2)

    with col_w1:
        new_severity = st.slider(
            "w₁: Severity Weight (Physical Hazard & Urgency)",
            min_value=0.05,
            max_value=0.70,
            value=float(current.severity),
            step=0.05,
            help="Weight assigned to immediate physical safety risks (electrical sparks, severe water flooding, structural collapse).",
        )
        st.caption("Controls how aggressively life-safety and emergency hazards overtake other tickets.")

        new_criticality = st.slider(
            "w₂: Location Criticality Weight (Asset Importance)",
            min_value=0.05,
            max_value=0.70,
            value=float(current.location_criticality),
            step=0.05,
            help="Multiplier assigned to high-impact spaces (Server Rooms, Exam Halls, Chemistry Labs vs Corridors).",
        )
        st.caption("Prioritizes mission-critical university facilities over general circulation spaces.")

    with col_w2:
        new_recurrence = st.slider(
            "w₃: Recurrence Probability Weight (Chronic Failure History)",
            min_value=0.05,
            max_value=0.70,
            value=float(current.recurrence_probability),
            step=0.05,
            help="Weight assigned to components with historical repetition patterns and chronic fatigue.",
        )
        st.caption("Ensures chronic repeat failures receive immediate escalation for root-cause overhaul.")

        new_impact = st.slider(
            "w₄: Impact Population Weight (Student / Faculty Reach)",
            min_value=0.05,
            max_value=0.70,
            value=float(current.impact_population),
            step=0.05,
            help="Weight reflecting estimated population affected (Lecture Hall with 200 students vs Single Cabin).",
        )
        st.caption("Favors issues that cause broad academic disruption to large groups of students.")

    # Calculate total
    candidate = PriorityWeights(
        severity=round(new_severity, 2),
        location_criticality=round(new_criticality, 2),
        recurrence_probability=round(new_recurrence, 2),
        impact_population=round(new_impact, 2),
    )
    total_val = candidate.total
    is_valid = candidate.is_valid()

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Validation banner
    c_tot, c_act1, c_act2, c_act3 = st.columns([1.5, 1, 1, 1])
    with c_tot:
        if is_valid:
            st.success(f"✓ Total Weight: **{round(total_val*100, 1)}% (Valid = 1.0)**")
        else:
            st.error(f"⚠️ Total Weight: **{round(total_val*100, 1)}%** (Must sum to 100%)")

    with c_act1:
        if st.button("Apply & Save Weights", disabled=not is_valid, type="primary", use_container_width=True):
            update_weights(candidate)
            st.success("Priority weights updated successfully!")
            st.rerun()

    with c_act2:
        if st.button("Auto-Normalize to 1.0", type="secondary", use_container_width=True):
            norm = candidate.normalize()
            update_weights(norm)
            st.info("Normalized weights to sum exactly to 1.0.")
            st.rerun()

    with c_act3:
        if st.button("Reset to Defaults", type="secondary", use_container_width=True):
            reset_weights_to_default()
            st.info("Reset weights to baseline defaults: 35%, 25%, 25%, 15%.")
            st.rerun()

    st.markdown("---")

    # Impact of Current Configuration on Queue
    st.subheader("💡 Impact of Configuration on Maintenance Dispatch")
    st.markdown(
        """
        - **Higher Severity ($w_1 > 0.40$)**: Emergency response model. Prioritizes electrical sparking and flooding regardless of where they occur.
        - **Higher Criticality ($w_2 > 0.35$)**: Research and core infrastructure protection model. Protects Data Centers and Labs over hostels.
        - **Higher Recurrence ($w_3 > 0.35$)**: Preventative maintenance overhaul model. Emphasizes fixing repeat offenders permanently.
        - **Higher Impact ($w_4 > 0.25$)**: Academic continuity model. Pushes lecture hall and exam hall fixes to the top of the queue.
        """
    )
