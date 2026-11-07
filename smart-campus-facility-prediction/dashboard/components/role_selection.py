"""
FIPP — Facility Issue Prediction & Prioritisation
Role Selection Gateway Screen with Hero Banner Collage and Pixel-Accurate Reference Styling.
Adheres strictly to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), and Soft Tan (#EAE3D2).
Engineered to fit completely within the viewport without vertical scrolling.
"""
import base64
from pathlib import Path
import streamlit as st

# Candidate paths for the campus panoramic hero banner asset (1024x341, ~3.0 ratio)
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
    Renders the exact FIPP Landing Page matching the user's reference mockup:
    - Panoramic university campus hero banner
    - Rounded card overlay container with arch top
    - Centered title: 'FIPP - Facility Issue Prediction & Prioritisation' with dual-tone color
    - Subtle horizontal underline pill (#756044)
    - Side-by-side Administrator and Student cards with exact copy, custom badge icons,
      and warm brown 'Continue as [Role] →' action buttons.
    - Fits the full screen comfortably without vertical scrolling.
    """
    b64_banner = get_hero_banner_base64()

    # Scoped styles for the pixel-perfect compact landing page
    st.markdown(
        """
        <style>
        /* Hide Streamlit default header on landing page for full-screen fit */
        header[data-testid="stHeader"] {
            display: none !important;
        }

        /* Scoped Container Styling - Fits page without scrolling */
        .block-container {
            padding-top: 0.75rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 1040px !important;
            margin: 0 auto !important;
        }

        .fipp-hero-banner-wrapper {
            width: 100%;
            border-radius: 18px 18px 0 0;
            overflow: hidden;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
            position: relative;
            max-height: 250px;
        }

        .fipp-hero-banner-img {
            width: 100%;
            height: 250px;
            object-fit: cover;
            object-position: center 28%;
            display: block;
        }

        .fipp-curved-top-bar {
            background-color: #FDFBF7;
            border-radius: 36px 36px 0 0;
            margin-top: -55px;
            padding: 1.4rem 2rem 0.4rem 2rem;
            text-align: center;
            position: relative;
            z-index: 10;
            box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.03);
            border-top: 1px solid #EAE3D2;
            border-left: 1px solid #EAE3D2;
            border-right: 1px solid #EAE3D2;
        }

        .fipp-title-heading {
            text-align: center;
            font-size: 1.95rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.025em;
            line-height: 1.2;
        }

        .fipp-title-dark {
            color: #1A1A1A;
        }

        .fipp-title-brown {
            color: #756044;
        }

        .fipp-title-underline {
            width: 64px;
            height: 3.5px;
            background-color: #756044;
            border-radius: 9999px;
            margin: 0.5rem auto 1.2rem auto;
        }

        /* Style the st.container(border=True) to match reference card */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF !important;
            border: 1px solid #EAE3D2 !important;
            border-radius: 16px !important;
            padding: 1.2rem 1.4rem 1.1rem 1.4rem !important;
            box-shadow: 0 4px 14px rgba(26, 26, 26, 0.04) !important;
        }

        .fipp-card-header {
            display: flex;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 0.85rem;
            min-height: 80px;
        }

        .fipp-icon-badge {
            width: 48px;
            height: 48px;
            min-width: 48px;
            border-radius: 12px;
            background-color: #EAE3D2;
            border: 1px solid #D8CFBD;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .fipp-card-body {
            flex: 1;
        }

        .fipp-card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1A1A1A;
            margin: 0 0 0.25rem 0;
            line-height: 1.2;
        }

        .fipp-card-desc {
            font-size: 0.88rem;
            color: #4A4A4A;
            line-height: 1.45;
            margin: 0;
        }

        /* Full width button matching reference #5F2A0A */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #5F2A0A !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            padding: 0.65rem 1.2rem !important;
            box-shadow: 0 2px 8px rgba(95, 42, 10, 0.25) !important;
            transition: all 0.2s ease-in-out !important;
            margin-top: 0.2rem !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #4A1E06 !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 12px rgba(95, 42, 10, 0.35) !important;
            transform: translateY(-1px) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. Panoramic Campus Hero Banner
    if b64_banner:
        st.markdown(
            f"""
            <div class="fipp-hero-banner-wrapper">
                <img src="data:image/jpeg;base64,{b64_banner}" class="fipp-hero-banner-img" alt="Campus Panoramic Hero Banner" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Arched Cutout Header with FIPP Title & Underline
    st.markdown(
        """
        <div class="fipp-curved-top-bar">
            <h1 class="fipp-title-heading">
                <span class="fipp-title-dark" style="color: #1A1A1A;">FIPP - </span><span class="fipp-title-brown" style="color: #756044;">Facility Issue Prediction &amp; Prioritisation</span>
            </h1>
            <div class="fipp-title-underline" style="background-color: #756044;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Two Role Cards Side-by-Side (Buttons integrated directly inside the cards)
    col_admin, col_student = st.columns(2, gap="medium")

    with col_admin:
        with st.container(border=True):
            st.markdown(
                """
                <div class="fipp-card-header">
                    <div class="fipp-icon-badge">
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="#5F2A0A" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h9.2c-.13-.64-.2-1.31-.2-2 0-1.85.73-3.52 1.93-4.76C13.9 14.47 12.92 14 12 14zm7.25 1.5v1.08c-.3.12-.57.28-.82.47l-.95-.55-.75 1.3.95.55c-.06.32-.08.64-.08.95s.02.63.08.95l-.95.55.75 1.3.95-.55c.25.19.52.35.82.47V23h1.5v-1.08c.3-.12.57-.28.82-.47l.95.55.75-1.3-.95-.55c.06-.32.08-.64.08-.95s-.02-.63-.08-.95l.95-.55-.75-1.3-.95.55c-.25-.19-.52-.35-.82-.47V15.5h-1.5zm.75 4.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                        </svg>
                    </div>
                    <div class="fipp-card-body">
                        <h2 class="fipp-card-title">Administrator</h2>
                        <p class="fipp-card-desc">
                            Manage system operations, monitor facility issues, and prioritize maintenance tasks.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Continue as Administrator →", key="btn_role_admin", type="primary", use_container_width=True):
                st.session_state["selected_role"] = "admin"
                st.session_state["user_role"] = None
                st.rerun()

    with col_student:
        with st.container(border=True):
            st.markdown(
                """
                <div class="fipp-card-header">
                    <div class="fipp-icon-badge">
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="#5F2A0A" xmlns="http://www.w3.org/2000/svg">
                            <path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/>
                        </svg>
                    </div>
                    <div class="fipp-card-body">
                        <h2 class="fipp-card-title">Student</h2>
                        <p class="fipp-card-desc">
                            Report facility issues, track their status, and view updates.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Continue as Student →", key="btn_role_student", type="primary", use_container_width=True):
                st.session_state["selected_role"] = "student"
                st.session_state["user_role"] = None
                st.rerun()
