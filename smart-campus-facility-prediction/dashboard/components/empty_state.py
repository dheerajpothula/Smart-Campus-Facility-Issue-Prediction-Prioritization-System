"""
Empty state component for Smart Campus Facility Issue Prediction & Prioritization System.
Provides a clean, uniform, and professional empty-state visual with context and roadmap notes.
"""
import streamlit as st


def render_empty_state(
    title: str,
    subtitle: str,
    description: str,
    action_notes: list[str] | None = None,
    icon: str = "ℹ️",
    badge_label: str = "Awaiting Data / Model",
) -> None:
    """
    Renders an elegant empty state container.

    Args:
        title: Main heading for the empty state.
        subtitle: Brief explanatory subtitle.
        description: Paragraph explaining why the data/model is not yet present.
        action_notes: List of upcoming roadmap milestones to activate this view.
        icon: Display icon.
        badge_label: Status pill text.
    """
    st.markdown(
        f"""
        <div style="
            border: 1px dashed #D8CFBD;
            border-radius: 12px;
            padding: 2.2rem;
            background-color: #FFFFFF;
            text-align: center;
            margin: 1.5rem 0;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <span style="
                background-color: #EAE3D2;
                color: #1A1A1A;
                font-size: 0.75rem;
                font-weight: 600;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                letter-spacing: 0.05em;
                text-transform: uppercase;
                border: 1px solid #D8CFBD;
            ">{badge_label}</span>
            <h3 style="color: #1A1A1A; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600;">{title}</h3>
            <p style="color: #555555; font-size: 0.95rem; max-width: 620px; margin: 0 auto 1.2rem auto; line-height: 1.5;">
                <strong>{subtitle}</strong><br>{description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if action_notes:
        with st.expander("🛠️ Planned Implementation Roadmap for this Module", expanded=True):
            st.markdown("**Scheduled capabilities in upcoming project phases:**")
            for note in action_notes:
                st.markdown(f"- {note}")
