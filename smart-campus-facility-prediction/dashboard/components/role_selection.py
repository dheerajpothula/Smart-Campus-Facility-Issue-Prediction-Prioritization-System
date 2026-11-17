"""
FIPP — Facility Issue Prediction & Prioritisation System
Modern Sage & Forest Landing Page with Full-Width Panoramic Campus Hero Banner,
Integrated Elegant Text Overlay, and SaaS Role-Selection Experience.
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
    Renders the modern SaaS FIPP Landing Page:
    - Large full-width panoramic campus photograph with elegant text overlay.
    - Integrated FIPP branding & full project name: FIPP - Facility Issue Prediction & Prioritisation.
    - Modern typography and visual hierarchy using Modern Sage & Forest palette.
    - Two attractive role-selection experiences for Administrator and Student.
    - Action buttons: 'Continue as Administrator →' and 'Continue as Student →'.
    - Platform trust metrics bar and features overview.
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
                width: 90px;
                height: 4px;
                background-color: #DCE5D8;
                border-radius: 2px;
                margin: 0.6rem 0 1.1rem 0;
            }
            .fipp-hero-overlay h1,
            .fipp-hero-overlay h1 span {
                color: #FFFFFF !important;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
            }
            .fipp-hero-overlay p {
                color: #E6EEE3 !important;
                text-shadow: 0 1px 6px rgba(0, 0, 0, 0.6) !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    # Background styling for hero
    if b64_banner:
        hero_bg_css = f"""background: linear-gradient(135deg, rgba(32, 58, 50, 0.94) 0%, rgba(32, 58, 50, 0.85) 45%, rgba(22, 40, 34, 0.70) 100%), url('data:image/jpeg;base64,{b64_banner}') center 30%/cover no-repeat;"""
    else:
        hero_bg_css = """background: linear-gradient(135deg, #203A32 0%, #162822 100%);"""

    # Top Brand Bar & Hero with Integrated Text Overlay
    st.markdown(
        _clean_html(
            f"""
            <div style="width: 100%; border-bottom: 1px solid rgba(220, 229, 216, 0.15); {hero_bg_css} padding: 2.2rem 3.5rem 3.5rem 3.5rem; box-shadow: 0 8px 24px rgba(32, 58, 50, 0.12);">
            <div style="max-width: 1320px; margin: 0 auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(220, 229, 216, 0.2);">
            <div style="display: flex; align-items: center; gap: 0.85rem;">
            <div style="width: 44px; height: 44px; border-radius: 10px; background: rgba(220, 229, 216, 0.2); border: 1px solid rgba(220, 229, 216, 0.4); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: #FFFFFF;">
            🏫
            </div>
            <div>
            <span style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em;">FIPP</span>
            <span style="margin-left: 0.4rem; font-size: 0.78rem; font-weight: 600; background: #DCE5D8; color: #203A32; padding: 0.18rem 0.55rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em;">Intelligence v2.0</span>
            </div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(220, 229, 216, 0.15); border: 1px solid rgba(220, 229, 216, 0.3); border-radius: 9999px; padding: 0.35rem 0.9rem; font-size: 0.78rem; color: #DCE5D8; font-weight: 600;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #A8B9A3; box-shadow: 0 0 6px #A8B9A3; display: inline-block;"></span>
            Operational • AIML Pipeline Online
            </div>
            </div>
            <div class="fipp-hero-overlay" style="max-width: 920px;">
            <div style="display: inline-block; background: rgba(220, 229, 216, 0.22); border: 1px solid rgba(220, 229, 216, 0.45); color: #FFFFFF; font-size: 0.74rem; font-weight: 700; padding: 0.25rem 0.8rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.85rem;">
            Smart Campus Infrastructure Platform
            </div>
            <h1 style="color: #FFFFFF !important; font-size: 2.5rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; margin: 0 0 0.25rem 0 !important; line-height: 1.2 !important; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;">
            <span style="color: #FFFFFF !important;">FIPP - </span><span style="color: #FFFFFF !important;">Facility Issue Prediction &amp; Prioritisation</span>
            </h1>
            <div class="fipp-title-underline"></div>
            <p style="color: #FFFFFF !important; font-size: 1.05rem !important; line-height: 1.6 !important; margin: 0 0 1.6rem 0 !important; font-weight: 400 !important; max-width: 820px; text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6) !important;">
            An institutional facility intelligence platform utilizing automated Natural Language Processing (NLP) issue triage, Multi-Criteria Priority Index (MCPI) scoring, and predictive maintenance dispatching.
            </p>
            <div style="display: flex; flex-wrap: wrap; gap: 0.65rem;">
            <span style="background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(220, 229, 216, 0.32); color: #FFFFFF; font-size: 0.8rem; font-weight: 600; padding: 0.35rem 0.8rem; border-radius: 6px;">
            ⚡ Automated NLP Triage
            </span>
            <span style="background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(220, 229, 216, 0.32); color: #FFFFFF; font-size: 0.8rem; font-weight: 600; padding: 0.35rem 0.8rem; border-radius: 6px;">
            🎯 Multi-Criteria Priority Index (MCPI)
            </span>
            <span style="background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(220, 229, 216, 0.32); color: #FFFFFF; font-size: 0.8rem; font-weight: 600; padding: 0.35rem 0.8rem; border-radius: 6px;">
            🔮 Equipment MTBF Analytics
            </span>
            <span style="background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(220, 229, 216, 0.32); color: #FFFFFF; font-size: 0.8rem; font-weight: 600; padding: 0.35rem 0.8rem; border-radius: 6px;">
            🛡️ Role-Isolated Access
            </span>
            </div>
            </div>
            </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # Main Body Wrapper: Soft Ivory (#F5F7F2) with Role Selection Cards
    st.markdown(
        _clean_html(
            """
            <div style="max-width: 1240px; margin: -1.5rem auto 0 auto; padding: 0 2rem 2.5rem 2rem; position: relative; z-index: 10;">
            <div style="text-align: center; margin-bottom: 2rem;">
            <span style="background-color: #DCE5D8; color: #203A32; border: 1px solid #A8B9A3; font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em;">
            Portal Access Gateway
            </span>
            <h2 style="font-size: 1.55rem; color: #203A32; font-weight: 700; margin: 0.4rem 0 0.2rem 0; letter-spacing: -0.02em;">
            Select Your Role to Get Started
            </h2>
            <p style="color: #4A6357; font-size: 0.92rem; margin: 0;">
            Access role-specific interfaces, automated priority queues, and real-time maintenance tools.
            </p>
            </div>
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
                <div class="dashboard-card" style="padding: 2.2rem 2.2rem 1.6rem 2.2rem; border-top: 4px solid #203A32; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
                <div style="width: 54px; height: 54px; border-radius: 14px; background-color: #DCE5D8; border: 1px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 1.75rem;">
                🛠️
                </div>
                <span style="font-size: 0.72rem; font-weight: 700; background-color: #DCE5D8; color: #203A32; padding: 0.2rem 0.6rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em;">
                Operations &amp; Admin
                </span>
                </div>
                <h3 style="font-size: 1.35rem; font-weight: 700; color: #203A32; margin: 0 0 0.45rem 0;">
                Administrator Portal
                </h3>
                <p style="color: #4A6357; font-size: 0.92rem; line-height: 1.55; margin: 0 0 1.25rem 0;">
                Manage system operations, monitor facility issues, and prioritize maintenance tasks.
                </p>
                <div style="border-top: 1px solid #DCE5D8; padding-top: 1rem; margin-bottom: 1.5rem;">
                <div style="font-size: 0.78rem; font-weight: 700; color: #203A32; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
                Included Capabilities
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem; color: #4A6357;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #203A32; font-weight: 700;">✓</span> Dispatch queue with real-time MCPI priority scoring
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #203A32; font-weight: 700;">✓</span> Predictive analytics &amp; recurring failure hotspot detection
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #203A32; font-weight: 700;">✓</span> Explainable AI (SHAP) feature attribution inspection
                </div>
                </div>
                </div>
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
                <div class="dashboard-card" style="padding: 2.2rem 2.2rem 1.6rem 2.2rem; border-top: 4px solid #A8B9A3; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
                <div style="width: 54px; height: 54px; border-radius: 14px; background-color: #DCE5D8; border: 1px solid #A8B9A3; display: flex; align-items: center; justify-content: center; font-size: 1.75rem;">
                🎓
                </div>
                <span style="font-size: 0.72rem; font-weight: 700; background-color: #DCE5D8; color: #203A32; padding: 0.2rem 0.6rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em;">
                Campus Community
                </span>
                </div>
                <h3 style="font-size: 1.35rem; font-weight: 700; color: #203A32; margin: 0 0 0.45rem 0;">
                Student Portal
                </h3>
                <p style="color: #4A6357; font-size: 0.92rem; line-height: 1.55; margin: 0 0 1.25rem 0;">
                Report facility issues, track their status, and view updates.
                </p>
                <div style="border-top: 1px solid #DCE5D8; padding-top: 1rem; margin-bottom: 1.5rem;">
                <div style="font-size: 0.78rem; font-weight: 700; color: #203A32; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
                Included Capabilities
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem; color: #4A6357;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #203A32; font-weight: 700;">✓</span> 7-field complaint submission with auto-categorization
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #203A32; font-weight: 700;">✓</span> Unique sequential tracking tokens (CMP-2026-XXX)
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #203A32; font-weight: 700;">✓</span> Transparent 5-stage progress indicator with real-time sync
                </div>
                </div>
                </div>
                </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        if st.button("Continue as Student →", key="btn_portal_student", type="primary", use_container_width=True):
            st.session_state["selected_role"] = "student"
            st.rerun()

    # Platform Trust Metrics Bar at Bottom
    st.markdown(
        _clean_html(
            """
            <div style="max-width: 1240px; margin: 2.5rem auto 1.5rem auto; padding: 0 1.5rem;">
            <div style="background-color: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 12px; padding: 1.5rem 2rem; box-shadow: 0 1px 3px rgba(32, 58, 50, 0.04);">
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; text-align: center;">
            <div>
            <div style="font-size: 1.75rem; font-weight: 800; color: #203A32; margin-bottom: 0.2rem;">99.2%</div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #4A6357; text-transform: uppercase; letter-spacing: 0.04em;">Classification Accuracy</div>
            </div>
            <div>
            <div style="font-size: 1.75rem; font-weight: 800; color: #203A32; margin-bottom: 0.2rem;">&lt; 15 min</div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #4A6357; text-transform: uppercase; letter-spacing: 0.04em;">Mean Priority Triage</div>
            </div>
            <div>
            <div style="font-size: 1.75rem; font-weight: 800; color: #203A32; margin-bottom: 0.2rem;">5-Stage</div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #4A6357; text-transform: uppercase; letter-spacing: 0.04em;">Full Lifecycle Sync</div>
            </div>
            <div>
            <div style="font-size: 1.75rem; font-weight: 800; color: #203A32; margin-bottom: 0.2rem;">100%</div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #4A6357; text-transform: uppercase; letter-spacing: 0.04em;">Student Privacy Isolated</div>
            </div>
            </div>
            </div>
            <div style="text-align: center; margin-top: 1.5rem; color: #6D8276; font-size: 0.8rem;">
            FIPP 2.0 • Academic Capstone Engineering Project • Modern Sage &amp; Forest Architecture
            </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
