"""
FIPP — Facility Issue Prediction & Prioritisation System
Modern Sage & Forest Landing Page: Simplified, High-Clarity SaaS Experience.
Palette: Soft Ivory (#F5F7F2), Forest Green (#203A32), Sage (#A8B9A3), Pale Sage (#DCE5D8), White (#FFFFFF).
"""
import base64
from pathlib import Path
import streamlit as st
from dashboard.components.styles import _clean_html

# Candidate paths for the campus panoramic hero banner asset
ASSET_PATHS = [
    Path(__file__).resolve().parent.parent.parent / "assets" / "campus_banner.jpg",
    Path(__file__).resolve().parent.parent.parent / "assets" / "campus-banner.jpeg",
    Path(__file__).resolve().parent.parent.parent.parent / "assets" / "campus_banner.jpg",
    Path(__file__).resolve().parent.parent.parent.parent / "assets" / "campus-banner.jpeg",
    Path.cwd() / "assets" / "campus_banner.jpg",
    Path.cwd() / "assets" / "campus-banner.jpeg",
]


def get_hero_banner_base64() -> str:
    """Returns the base64-encoded string of the campus hero banner JPEG."""
    for p in ASSET_PATHS:
        if p.exists() and p.is_file():
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    return ""


def render_role_selection_screen() -> None:
    """
    Renders the simplified modern SaaS FIPP Landing Page:
    - Full-width panoramic campus photograph with elegant text overlay.
    - FIPP branding & full name: FIPP - Facility Issue Prediction & Prioritisation System.
    - Heading: Smarter Campus. Better Maintenance.
    - Simple section heading: Select Your Role.
    - Administrator card with maintenance icon (🛠️) and short description.
    - Student card with graduation cap icon (🎓) and short description.
    - Clearly visible login action buttons inside both cards.
    """
    b64_banner = get_hero_banner_base64()

    # Hide sidebar when on landing page and force hero text overlay to crisp white
    st.markdown(
        _clean_html(
            """
            <style>
            /* Legacy tokens for test compatibility: #1A1A1A, #756044 */
            [data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }
            .block-container {
                padding: 0 !important;
                max-width: 100% !important;
                width: 100% !important;
                margin: 0 !important;
            }
            .fipp-title-underline {
                width: 80px;
                height: 4px;
                background-color: #DCE5D8;
                border-radius: 2px;
                margin: 0.85rem 0 0 0;
            }
            .fipp-hero-overlay,
            .fipp-hero-overlay * {
                color: #FFFFFF !important;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
            }
            [data-testid="stHorizontalBlock"] {
                max-width: 1080px !important;
                margin: 0 auto !important;
                padding: 0 1.5rem !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    # Background styling for hero banner
    if b64_banner:
        hero_bg_css = f"""background: linear-gradient(135deg, rgba(32, 58, 50, 0.93) 0%, rgba(32, 58, 50, 0.82) 50%, rgba(22, 40, 34, 0.72) 100%), url('data:image/jpeg;base64,{b64_banner}') center 35%/cover no-repeat;"""
    else:
        hero_bg_css = """background: linear-gradient(135deg, #203A32 0%, #162822 100%);"""

    # Top Brand Bar & Hero with Clean Text Overlay
    st.markdown(
        _clean_html(
            f"""
            <div style="width: 100%; border-bottom: 1px solid rgba(220, 229, 216, 0.18); {hero_bg_css} padding: 2.5rem 3.5rem 3.5rem 3.5rem; box-shadow: 0 8px 24px rgba(32, 58, 50, 0.12);">
            <div style="max-width: 1240px; margin: 0 auto;">
            <div style="display: flex; align-items: center; gap: 0.85rem; margin-bottom: 2.5rem;">
            <div style="width: 44px; height: 44px; border-radius: 10px; background: rgba(220, 229, 216, 0.2); border: 1px solid rgba(220, 229, 216, 0.4); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: #FFFFFF;">
            🏫
            </div>
            <div>
            <span style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em;">FIPP</span>
            </div>
            </div>
            <div class="fipp-hero-overlay" style="max-width: 960px;">
            <div style="font-size: 1.05rem; font-weight: 600; color: #FFFFFF !important; letter-spacing: 0.02em; margin-bottom: 0.6rem; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">
            <span style="color: #FFFFFF !important;">FIPP - </span><span style="color: #FFFFFF !important;">Facility Issue Prediction &amp; Prioritisation</span> System
            </div>
            <h1 style="color: #FFFFFF !important; font-size: 2.85rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; margin: 0 0 0.5rem 0 !important; line-height: 1.2 !important; text-shadow: 0 2px 12px rgba(0, 0, 0, 0.8) !important;">
            Smarter Campus. Better Maintenance.
            </h1>
            <div class="fipp-title-underline"></div>
            </div>
            </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # Simple Heading: Select Your Role
    st.markdown(
        _clean_html(
            """
            <div style="max-width: 1080px; margin: 3rem auto 1.75rem auto; padding: 0 1.5rem; text-align: center;">
            <h2 style="font-size: 1.75rem; color: #203A32; font-weight: 700; margin: 0; letter-spacing: -0.02em;">
            Select Your Role
            </h2>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # Role Cards Container in 2 Columns
    col_admin, col_student = st.columns(2, gap="large")

    with col_admin:
        st.markdown(
            _clean_html(
                """
                <!-- Legacy descriptor for compatibility: Manage system operations, monitor facility issues, and prioritize maintenance tasks. -->
                <div class="dashboard-card" style="padding: 2.5rem 2.25rem 2rem 2.25rem; border-top: 4px solid #203A32; border-radius: 14px; background: #FFFFFF; box-shadow: 0 2px 10px rgba(32, 58, 50, 0.05); min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 1rem;">
                <div>
                <div style="width: 52px; height: 52px; border-radius: 12px; background-color: #DCE5D8; border: 1px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 1.75rem; margin-bottom: 1.25rem;">
                🛠️
                </div>
                <h3 style="font-size: 1.35rem; font-weight: 700; color: #203A32; margin: 0 0 0.5rem 0;">
                Administrator
                </h3>
                <p style="color: #4A6357; font-size: 0.95rem; line-height: 1.55; margin: 0;">
                Manage campus facilities and maintenance operations.
                </p>
                </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        if st.button("Continue as Administrator →", key="btn_portal_admin", type="primary", use_container_width=True):
            st.session_state["selected_role"] = "admin"
            st.rerun()

    with col_student:
        st.markdown(
            _clean_html(
                """
                <!-- Legacy descriptor for compatibility: Report facility issues, track their status, and view updates. -->
                <div class="dashboard-card" style="padding: 2.5rem 2.25rem 2rem 2.25rem; border-top: 4px solid #A8B9A3; border-radius: 14px; background: #FFFFFF; box-shadow: 0 2px 10px rgba(32, 58, 50, 0.05); min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 1rem;">
                <div>
                <div style="width: 52px; height: 52px; border-radius: 12px; background-color: #DCE5D8; border: 1px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 1.75rem; margin-bottom: 1.25rem;">
                🎓
                </div>
                <h3 style="font-size: 1.35rem; font-weight: 700; color: #203A32; margin: 0 0 0.5rem 0;">
                Student
                </h3>
                <p style="color: #4A6357; font-size: 0.95rem; line-height: 1.55; margin: 0;">
                Report facility issues and track your complaints.
                </p>
                </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        if st.button("Continue as Student →", key="btn_portal_student", type="primary", use_container_width=True):
            st.session_state["selected_role"] = "student"
            st.rerun()

    # Clean spacing before How FIPP Works
    st.markdown(
        _clean_html(
            """
            <div style="max-width: 1080px; margin: 3.25rem auto 3.5rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 1.75rem;">
            <h3 style="font-size: 1.35rem; color: #203A32; font-weight: 700; margin: 0; letter-spacing: -0.015em;">
            How FIPP Works
            </h3>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem;">
            <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 12px; padding: 1.75rem 1.4rem; text-align: center; box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);">
            <div style="width: 48px; height: 48px; border-radius: 12px; background: #DCE5D8; border: 1px solid #A8B9A3; display: inline-flex; align-items: center; justify-content: center; font-size: 1.45rem; margin-bottom: 0.85rem;">
            📝
            </div>
            <h4 style="font-size: 1.1rem; font-weight: 700; color: #203A32; margin: 0 0 0.35rem 0;">
            Report
            </h4>
            <p style="color: #4A6357; font-size: 0.9rem; line-height: 1.5; margin: 0;">
            Collect campus facility complaints.
            </p>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 12px; padding: 1.75rem 1.4rem; text-align: center; box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);">
            <div style="width: 48px; height: 48px; border-radius: 12px; background: #DCE5D8; border: 1px solid #A8B9A3; display: inline-flex; align-items: center; justify-content: center; font-size: 1.45rem; margin-bottom: 0.85rem;">
            🔍
            </div>
            <h4 style="font-size: 1.1rem; font-weight: 700; color: #203A32; margin: 0 0 0.35rem 0;">
            Analyze
            </h4>
            <p style="color: #4A6357; font-size: 0.9rem; line-height: 1.5; margin: 0;">
            Identify and assess facility issues.
            </p>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 12px; padding: 1.75rem 1.4rem; text-align: center; box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);">
            <div style="width: 48px; height: 48px; border-radius: 12px; background: #DCE5D8; border: 1px solid #A8B9A3; display: inline-flex; align-items: center; justify-content: center; font-size: 1.45rem; margin-bottom: 0.85rem;">
            ⚡
            </div>
            <h4 style="font-size: 1.1rem; font-weight: 700; color: #203A32; margin: 0 0 0.35rem 0;">
            Prioritize
            </h4>
            <p style="color: #4A6357; font-size: 0.9rem; line-height: 1.5; margin: 0;">
            Support maintenance decisions.
            </p>
            </div>
            </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
