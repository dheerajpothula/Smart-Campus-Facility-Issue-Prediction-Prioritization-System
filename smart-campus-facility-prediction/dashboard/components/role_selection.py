"""
FIPP — Facility Issue Prediction & Prioritisation
Role Selection Gateway Screen with Hero Banner Collage and Pixel-Accurate Reference Styling.
Adheres strictly to the 60/30/10 palette: Warm Chalk (#FDFBF7), Deep Charcoal (#1A1A1A), and Soft Tan (#EAE3D2).
"""
import base64
from pathlib import Path
import streamlit as st

# Valid candidate paths for the campus panoramic hero banner asset (1024x341, ~3.0 ratio)
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
    """
    b64_banner = get_hero_banner_base64()

    # Scoped styles for the pixel-perfect landing page
    st.markdown(
        """
        <style>
        /* Scoped Container Styling */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1040px !important;
        }

        .fipp-hero-banner-wrapper {
            width: 100%;
            border-radius: 20px 20px 0 0;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            position: relative;
        }

        .fipp-hero-banner-img {
            width: 100%;
            height: auto;
            max-height: 340px;
            object-fit: cover;
            display: block;
        }

        .fipp-overlay-card {
            position: relative;
            margin-top: -65px;
            background-color: #FDFBF7;
            border-radius: 40px 40px 24px 24px;
            padding: 2.2rem 2.4rem 2.4rem 2.4rem;
            box-shadow: 0 10px 30px rgba(26, 26, 26, 0.06);
            border: 1px solid #EAE3D2;
            z-index: 10;
        }

        .fipp-title-heading {
            text-align: center;
            font-size: 2.15rem;
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
            width: 68px;
            height: 3.5px;
            background-color: #756044;
            border-radius: 9999px;
            margin: 0.65rem auto 2.2rem auto;
        }

        .fipp-role-card {
            background-color: #FFFFFF;
            border: 1px solid #EAE3D2;
            border-radius: 16px;
            padding: 1.5rem 1.6rem 1.2rem 1.6rem;
            box-shadow: 0 4px 14px rgba(26, 26, 26, 0.04);
            display: flex;
            gap: 1.1rem;
            align-items: flex-start;
            min-height: 135px;
            margin-bottom: 0.75rem;
        }

        .fipp-icon-badge {
            width: 52px;
            height: 52px;
            min-width: 52px;
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
            font-size: 1.35rem;
            font-weight: 700;
            color: #1A1A1A;
            margin: 0 0 0.35rem 0;
            line-height: 1.2;
        }

        .fipp-card-desc {
            font-size: 0.90rem;
            color: #4A4A4A;
            line-height: 1.5;
            margin: 0;
        }

        /* Specific Button Override for Landing Page to match reference #5F2A0A */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #5F2A0A !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 0.72rem 1.2rem !important;
            box-shadow: 0 2px 8px rgba(95, 42, 10, 0.25) !important;
            transition: all 0.2s ease-in-out !important;
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

    # 2. Main Floating Overlay Card with exact FIPP Title & Underline
    st.markdown(
        """
        <div class="fipp-overlay-card">
            <h1 class="fipp-title-heading">
                <span class="fipp-title-dark" style="color: #1A1A1A;">FIPP - </span><span class="fipp-title-brown" style="color: #756044;">Facility Issue Prediction &amp; Prioritisation</span>
            </h1>
            <div class="fipp-title-underline" style="background-color: #756044;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Two Role Cards Side-by-Side
    col_admin, col_student = st.columns(2, gap="large")

    with col_admin:
        st.markdown(
            """
            <div class="fipp-role-card">
                <div class="fipp-icon-badge">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="#5F2A0A" xmlns="http://www.w3.org/2000/svg">
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
        st.markdown(
            """
            <div class="fipp-role-card">
                <div class="fipp-icon-badge">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="#5F2A0A" xmlns="http://www.w3.org/2000/svg">
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
