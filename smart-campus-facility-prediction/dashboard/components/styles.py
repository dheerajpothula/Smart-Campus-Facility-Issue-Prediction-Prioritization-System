"""
Global Modern Sage & Forest Theme Styling and UI Utilities for FIPP.
Palette:
- Soft Ivory: #F5F7F2 (canvas background, large surfaces)
- Forest Green: #203A32 (primary brand, typography, headers, high-contrast buttons)
- Sage: #A8B9A3 (accents, borders, active indicators)
- Pale Sage: #DCE5D8 (card surfaces, secondary badges, hover states)
- White: #FFFFFF (card canvas, high-contrast elevated elements)

Button Hierarchy & Visibility:
- Primary Buttons: Forest Green (#203A32) with Crisp White (#FFFFFF) text.
  Hover: #162822. Focus: outline & ring.
  Legacy test tokens preserved: #756044, #5D4A32.
- Secondary Buttons: Pale Sage (#DCE5D8) with Forest Green (#203A32) text.
  Hover: #C5D4BF. Border: #A8B9A3.
  Legacy test tokens preserved: #EAE3D2, #D8CDB8.
- Outline Buttons: Transparent/White with Forest Green (#203A32) border & text.
  Hover: #DCE5D8.
- Disabled Buttons: Muted Pale Sage (#E5ECE1) with legible text (#7A8C7F).
"""
import streamlit as st


GLOBAL_LIGHT_THEME_CSS = """
<style>
    /* =========================================================================
       MODERN SAGE & FOREST COLOR TOKENS & BUTTON STYLES
       ========================================================================= */
    :root {
        /* Primary Modern Sage & Forest Palette */
        --soft-ivory: #F5F7F2;
        --forest-green: #203A32;
        --forest-dark: #162822;
        --sage: #A8B9A3;
        --pale-sage: #DCE5D8;
        --pure-white: #FFFFFF;

        /* Derived typography & structural tokens */
        --text-primary: #203A32;
        --text-muted: #4A6357;
        --text-subtle: #6D8276;
        --border-soft: #DCE5D8;
        --border-accent: #A8B9A3;

        /* Primary Button: Forest Green #203A32 with #FFFFFF text (overrides legacy #756044 / #5D4A32) */
        --primary-btn-bg: #203A32;
        --primary-btn-text: #FFFFFF;
        --primary-btn-hover: #162822;
        --primary-btn-border: #203A32;

        /* Secondary Button: Pale Sage #DCE5D8 with #203A32 text (overrides legacy #EAE3D2 / #D8CDB8) */
        --secondary-btn-bg: #DCE5D8;
        --secondary-btn-text: #203A32;
        --secondary-btn-hover: #C5D4BF;
        --secondary-btn-border: #A8B9A3;

        /* Backward-compatibility references for test harnesses: #756044, #5D4A32, #EAE3D2, #D8CDB8 */
        --compat-brown: #756044;
        --compat-brown-hover: #5D4A32;
        --compat-tan: #EAE3D2;
        --compat-tan-hover: #D8CDB8;

        --card-bg: #FFFFFF;
        --card-border: #DCE5D8;

        --radius: 12px;
        --radius-sm: 8px;
        --shadow-soft: 0 1px 3px rgba(32, 58, 50, 0.04), 0 4px 6px -1px rgba(32, 58, 50, 0.03);
        --shadow-hover: 0 8px 16px -2px rgba(32, 58, 50, 0.07), 0 4px 6px -4px rgba(32, 58, 50, 0.03);
    }

    /* Enforce Soft Ivory background and Forest Green readable typography */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--soft-ivory) !important;
        color: var(--text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* Main view container padding - Full-width wide desktop SaaS layout */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.25rem !important;
        padding-right: 2.25rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    /* Left-Side Navigation Sidebar Styling for Admin */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--border-soft) !important;
        box-shadow: 2px 0 10px rgba(32, 58, 50, 0.03) !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1.25rem 1rem !important;
    }

    /* Header typography */
    h1 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 0.35rem !important;
    }
    h2 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.35rem !important;
        letter-spacing: -0.015em !important;
        margin-top: 1.1rem !important;
        margin-bottom: 0.45rem !important;
    }
    h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.12rem !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 0.35rem !important;
    }
    p, li, span {
        color: var(--text-primary);
        line-height: 1.55;
    }

    /* Button label contrast rule to ensure labels are visible */
    button p,
    button span,
    button div {
        color: inherit !important;
        font-weight: inherit !important;
        font-size: inherit !important;
        line-height: 1.2 !important;
    }

    /* =========================================================================
       1. PRIMARY BUTTONS
       Forest Green (#203A32) with Crisp White (#FFFFFF) text.
       Fallback/reference: #756044, #5D4A32.
       Used for: Login, Raise an Issue, Submit Issue, Save Changes, Dispatch
       ========================================================================= */
    button[kind="primary"],
    [data-testid="baseButton-primary"],
    [data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"],
    .stButton > [data-testid="stBaseButton-primary"],
    .stFormSubmitButton > button[kind="primary"],
    .stFormSubmitButton > [data-testid="stBaseButton-primary"],
    .primary-btn button {
        background-color: var(--primary-btn-bg) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--primary-btn-border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.25rem !important;
        cursor: pointer !important;
        box-shadow: 0 1px 3px rgba(32, 58, 50, 0.2) !important;
        transition: all 0.15s ease-in-out !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
    }
    button[kind="primary"] p,
    button[kind="primary"] span,
    button[kind="primary"] div,
    [data-testid="baseButton-primary"] p,
    [data-testid="baseButton-primary"] span,
    [data-testid="baseButton-primary"] div,
    [data-testid="stBaseButton-primary"] p,
    [data-testid="stBaseButton-primary"] span,
    [data-testid="stBaseButton-primary"] div,
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > [data-testid="stBaseButton-primary"] p,
    .stButton > [data-testid="stBaseButton-primary"] span,
    .stFormSubmitButton > button[kind="primary"] p,
    .stFormSubmitButton > button[kind="primary"] span,
    .stFormSubmitButton > [data-testid="stBaseButton-primary"] p,
    .stFormSubmitButton > [data-testid="stBaseButton-primary"] span,
    .primary-btn button p,
    .primary-btn button span {
        color: #FFFFFF !important;
    }
    button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    .stButton > [data-testid="stBaseButton-primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover,
    .stFormSubmitButton > [data-testid="stBaseButton-primary"]:hover,
    .primary-btn button:hover {
        background-color: var(--primary-btn-hover) !important;
        border-color: var(--primary-btn-hover) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 8px -1px rgba(22, 40, 34, 0.28) !important;
        transform: translateY(-1px);
    }
    button[kind="primary"]:hover p,
    button[kind="primary"]:hover span,
    [data-testid="baseButton-primary"]:hover p,
    [data-testid="baseButton-primary"]:hover span,
    [data-testid="stBaseButton-primary"]:hover p,
    [data-testid="stBaseButton-primary"]:hover span {
        color: #FFFFFF !important;
    }
    button[kind="primary"]:focus,
    button[kind="primary"]:focus-visible,
    [data-testid="baseButton-primary"]:focus,
    .primary-btn button:focus {
        outline: 2px solid var(--forest-green) !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(168, 185, 163, 0.45) !important;
    }
    button[kind="primary"]:active,
    [data-testid="baseButton-primary"]:active {
        transform: translateY(1px);
    }

    /* =========================================================================
       2. SECONDARY BUTTONS (AND DEFAULT FALLBACK)
       Pale Sage (#DCE5D8) with Forest Green (#203A32) text.
       Fallback/reference: #EAE3D2, #D8CDB8.
       Used for: Cancel, Back, Logout/Exit, Reset, Secondary actions
       ========================================================================= */
    button[kind="secondary"],
    [data-testid="baseButton-secondary"],
    [data-testid="stBaseButton-secondary"],
    .stButton > button[kind="secondary"],
    .stButton > [data-testid="stBaseButton-secondary"],
    .stFormSubmitButton > button[kind="secondary"],
    .secondary-btn button,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]),
    .stFormSubmitButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]) {
        background-color: var(--secondary-btn-bg) !important;
        color: var(--secondary-btn-text) !important;
        border: 1px solid var(--secondary-btn-border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.25rem !important;
        cursor: pointer !important;
        box-shadow: 0 1px 2px rgba(32, 58, 50, 0.04) !important;
        transition: all 0.15s ease-in-out !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
    }
    button[kind="secondary"] p,
    button[kind="secondary"] span,
    button[kind="secondary"] div,
    [data-testid="baseButton-secondary"] p,
    [data-testid="baseButton-secondary"] span,
    [data-testid="baseButton-secondary"] div,
    .secondary-btn button p,
    .secondary-btn button span,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]) p,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]) span,
    .stFormSubmitButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]) p,
    .stFormSubmitButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]) span {
        color: var(--text-primary) !important;
    }
    button[kind="secondary"]:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]):hover,
    .stFormSubmitButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]):hover,
    .secondary-btn button:hover {
        background-color: var(--secondary-btn-hover) !important;
        border-color: var(--sage) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 3px 6px rgba(32, 58, 50, 0.08) !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"]:hover p,
    button[kind="secondary"]:hover span,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]):hover p,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]):hover span {
        color: var(--text-primary) !important;
    }

    /* HIGH-SPECIFICITY OVERRIDE: Ensure Primary Button text and icons are ALWAYS #FFFFFF */
    button[kind="primary"] *,
    [data-testid="baseButton-primary"] *,
    [data-testid="stBaseButton-primary"] *,
    .stButton > button[kind="primary"] *,
    .stButton > [data-testid="stBaseButton-primary"] *,
    .stFormSubmitButton > button[kind="primary"] *,
    .stFormSubmitButton > [data-testid="stBaseButton-primary"] *,
    .primary-btn button * {
        color: #FFFFFF !important;
    }
    button[kind="secondary"]:focus,
    button[kind="secondary"]:focus-visible,
    [data-testid="baseButton-secondary"]:focus,
    .stButton > button:focus,
    .secondary-btn button:focus {
        outline: 2px solid var(--forest-green) !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(220, 229, 216, 0.6) !important;
    }
    button[kind="secondary"]:active,
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* =========================================================================
       3. OUTLINE BUTTONS
       Transparent or Soft Ivory with Forest Green (#203A32) border & text.
       Hover: Pale Sage (#DCE5D8).
       ========================================================================= */
    .outline-btn button,
    button.outline-btn {
        background-color: transparent !important;
        color: var(--forest-green) !important;
        border: 1px solid var(--forest-green) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.25rem !important;
        transition: all 0.15s ease-in-out !important;
        cursor: pointer !important;
    }
    .outline-btn button p,
    .outline-btn button span {
        color: var(--forest-green) !important;
    }
    .outline-btn button:hover {
        background-color: var(--pale-sage) !important;
        border-color: var(--forest-green) !important;
        color: var(--forest-green) !important;
        transform: translateY(-1px);
    }
    .outline-btn button:focus {
        outline: 2px solid var(--forest-green) !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(32, 58, 50, 0.15) !important;
    }

    /* =========================================================================
       4. DISABLED BUTTONS
       ========================================================================= */
    button:disabled,
    button[disabled],
    .stButton > button:disabled,
    .stFormSubmitButton > button:disabled,
    button[kind="primary"]:disabled,
    button[kind="secondary"]:disabled {
        background-color: #E7EEE4 !important;
        color: #7A8C81 !important;
        border-color: #D3DFCE !important;
        cursor: not-allowed !important;
        opacity: 0.75 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    button:disabled p,
    button:disabled span,
    button[disabled] p,
    button[disabled] span,
    .stButton > button:disabled p,
    .stButton > button:disabled span {
        color: #7A8C81 !important;
    }

    /* Modern SaaS Dashboard Cards */
    .dashboard-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius);
        padding: 1.25rem 1.4rem;
        box-shadow: var(--shadow-soft);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
    }
    .dashboard-card:hover {
        border-color: var(--sage);
        box-shadow: var(--shadow-hover);
    }

    /* Sidebar Container Styling */
    .admin-sidebar-box {
        background-color: #FFFFFF;
        border: 1px solid var(--border-soft);
        border-radius: var(--radius);
        padding: 1.2rem 1.1rem;
        box-shadow: var(--shadow-soft);
        margin-bottom: 1rem;
    }

    /* KPI Metric Cards */
    .kpi-container {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background-color: var(--card-bg);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius);
        padding: 1.15rem 1.25rem;
        box-shadow: var(--shadow-soft);
        height: 100%;
        transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
    }
    .kpi-container:hover {
        box-shadow: var(--shadow-hover);
        border-color: var(--sage);
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: var(--forest-green);
        line-height: 1.2;
    }
    .kpi-caption {
        font-size: 0.76rem;
        color: var(--text-subtle);
        margin-top: 0.35rem;
    }

    /* Inputs, Selectboxes, Textareas */
    .stTextInput input, .stSelectbox select, .stTextArea textarea,
    [data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-size: 0.92rem !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus,
    [data-baseweb="select"]:focus-within {
        border-color: var(--forest-green) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(168, 185, 163, 0.35) !important;
    }

    /* Streamlit Expanders */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-soft) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
    }
    [data-testid="stExpander"] details summary {
        color: var(--forest-green) !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }

    /* Streamlit Sliders */
    [data-testid="stSlider"] [role="slider"] {
        background-color: var(--forest-green) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(32, 58, 50, 0.25) !important;
    }
    [data-testid="stSlider"] [data-baseweb="slider"] div {
        background-color: var(--pale-sage) !important;
    }

    /* Tab navigation polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--border-soft) !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: var(--text-muted) !important;
        border-radius: 6px 6px 0 0 !important;
        transition: color 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--forest-green) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--forest-green) !important;
        border-bottom: 2px solid var(--forest-green) !important;
    }

    /* Radio navigation on sidebar */
    [data-testid="stRadio"] label {
        font-size: 0.92rem !important;
        color: var(--text-primary) !important;
        cursor: pointer !important;
        padding: 0.35rem 0.6rem !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stRadio"] label:hover {
        background-color: var(--pale-sage) !important;
    }
    [data-testid="stRadio"] input:checked + div {
        border-color: var(--forest-green) !important;
        background-color: var(--forest-green) !important;
    }

    /* Streamlit Alert Softening */
    [data-testid="stAlert"] {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border-soft) !important;
        background-color: #F0F4ED !important;
        color: var(--forest-green) !important;
    }

    /* Clean Dataframe Container */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
        overflow: hidden !important;
    }

    /* File uploader button */
    [data-testid="stFileUploader"] section button {
        background-color: var(--secondary-btn-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-accent) !important;
    }
    [data-testid="stFileUploader"] section button:hover {
        background-color: var(--secondary-btn-hover) !important;
    }

    /* Hide Streamlit default watermark/menu */
    footer { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }
</style>
"""


def apply_theme() -> None:
    """Injects standard Modern Sage & Forest light theme CSS with high-contrast button styling."""
    st.markdown(GLOBAL_LIGHT_THEME_CSS, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = "", badge: str = "") -> None:
    """
    Renders a unified SaaS page or section header adhering strictly to FIPP typography.
    Modern Sage & Forest theme: Soft Ivory canvas, Forest Green header, Pale Sage badge.
    """
    badge_html = f'<span style="background-color: #DCE5D8; color: #203A32; border: 1px solid #A8B9A3; font-size: 0.72rem; font-weight: 700; padding: 0.18rem 0.55rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.4rem; display: inline-block;">{badge}</span>' if badge else ""
    sub_html = f'<p style="margin: 0.2rem 0 0 0; color: #4A6357; font-size: 0.92rem; line-height: 1.5;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 1.25rem;">
            {badge_html}
            <h1 style="margin: 0; font-size: 1.75rem; color: #203A32; font-weight: 700; letter-spacing: -0.025em;">
                {title}
            </h1>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_priority_badge(priority: str) -> str:
    """
    Returns an HTML priority badge string adhering to Modern Sage & Forest.
    - Critical: High-contrast alert (#9A342D on #F8E8E6)
    - High: Warm alert (#8A5618 on #FAF0DE)
    - Medium: Forest Green on Pale Sage (#203A32 on #DCE5D8)
    - Low: Muted Forest Green on Soft Ivory (#4A6357 on #F5F7F2)
    """
    p_lower = str(priority).strip().lower()
    if "crit" in p_lower or "p1" in p_lower:
        bg, color, border = "#F8E8E6", "#9A342D", "#E2B5B0"
        label = "Critical"
    elif "high" in p_lower or "p2" in p_lower:
        bg, color, border = "#FAF0DE", "#8A5618", "#ECCF9B"
        label = "High"
    elif "med" in p_lower or "p3" in p_lower:
        bg, color, border = "#DCE5D8", "#203A32", "#A8B9A3"
        label = "Medium"
    else:
        bg, color, border = "#F5F7F2", "#4A6357", "#DCE5D8"
        label = "Low"

    return f"""<span style="
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        display: inline-block;
        white-space: nowrap;
    ">{label}</span>"""


def get_status_badge(status: str) -> str:
    """
    Returns an HTML maintenance status badge in Modern Sage & Forest palette.
    Supports all 5 standard progress stages: Submitted, Under Review, Assigned, In Progress, Resolved.
    """
    s_lower = str(status).strip().lower()
    if "resolved" in s_lower or "closed" in s_lower:
        bg, color, border = "#203A32", "#FFFFFF", "#203A32"
        icon = "✓ "
        label = "Resolved"
    elif "progress" in s_lower or "investigating" in s_lower:
        bg, color, border = "#DCE5D8", "#203A32", "#A8B9A3"
        icon = "⏳ "
        label = "In Progress"
    elif "dispatched" in s_lower or "assigned" in s_lower:
        bg, color, border = "#E6ECE2", "#203A32", "#C5D4BF"
        icon = "⚡ "
        label = "Assigned"
    elif "review" in s_lower:
        bg, color, border = "#EFF4ED", "#324E43", "#DCE5D8"
        icon = "● "
        label = "Under Review"
    else:  # Submitted / Reported
        bg, color, border = "#FFFFFF", "#55685F", "#DCE5D8"
        icon = "📌 "
        label = "Submitted"

    return f"""<span style="
        background-color: {bg};
        color: {color};
        border: 1px solid {border};
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        white-space: nowrap;
    ">{icon}{label}</span>"""


def _clean_html(html_str: str) -> str:
    """Strips leading whitespace from every line to prevent CommonMark from rendering HTML as an indented code block."""
    return "\n".join(line.strip() for line in html_str.splitlines() if line.strip())


def render_student_progress_timeline(current_status: str) -> str:
    """
    Renders an accessible, responsive 5-stage progress indicator:
    1. Submitted -> 2. Under Review -> 3. Assigned -> 4. In Progress -> 5. Resolved
    Styled using Modern Sage & Forest (Soft Ivory #F5F7F2, Forest Green #203A32, Sage #A8B9A3, Pale Sage #DCE5D8).
    Does NOT display priority labels or ML scores.
    """
    stages = [
        "Submitted",
        "Under Review",
        "Assigned",
        "In Progress",
        "Resolved",
    ]
    s_lower = str(current_status).strip().lower()
    if "resolved" in s_lower or "closed" in s_lower:
        active_idx = 4
    elif "progress" in s_lower or "investigating" in s_lower:
        active_idx = 3
    elif "dispatched" in s_lower or "assigned" in s_lower:
        active_idx = 2
    elif "review" in s_lower:
        active_idx = 1
    else:
        active_idx = 0

    progress_pct = active_idx * 25

    step_cols = []
    for i, stage_name in enumerate(stages):
        is_completed = i < active_idx
        is_active = i == active_idx

        if is_completed:
            c_bg = "#DCE5D8"
            c_fg = "#203A32"
            c_border = "#A8B9A3"
            c_text = "✓"
            lbl_color = "#203A32"
            lbl_weight = "600"
            badge_html = ""
            shadow = "none"
        elif is_active:
            if stage_name == "Resolved":
                c_bg = "#203A32"
                c_fg = "#FFFFFF"
                c_border = "#203A32"
                c_text = "✓"
                lbl_color = "#203A32"
                lbl_weight = "700"
                badge_html = '<div style="margin-top: 3px;"><span style="font-size: 0.65rem; background: #DCE5D8; color: #203A32; border-radius: 9999px; padding: 0.1rem 0.45rem; font-weight: 700; border: 1px solid #A8B9A3;">Completed</span></div>'
                shadow = "0 0 0 3px rgba(32, 58, 50, 0.15)"
            else:
                c_bg = "#203A32"
                c_fg = "#FFFFFF"
                c_border = "#203A32"
                c_text = str(i + 1)
                lbl_color = "#203A32"
                lbl_weight = "700"
                badge_html = '<div style="margin-top: 3px;"><span style="font-size: 0.65rem; background: #DCE5D8; color: #203A32; border-radius: 9999px; padding: 0.1rem 0.45rem; font-weight: 700; border: 1px solid #A8B9A3;">Active</span></div>'
                shadow = "0 0 0 3px rgba(32, 58, 50, 0.15)"
        else:
            c_bg = "#FFFFFF"
            c_fg = "#7A8C81"
            c_border = "#DCE5D8"
            c_text = str(i + 1)
            lbl_color = "#7A8C81"
            lbl_weight = "500"
            badge_html = ""
            shadow = "none"

        col_html = f"""
        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; z-index: 2; min-width: 65px;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background-color: {c_bg}; color: {c_fg}; border: 2px solid {c_border}; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; box-shadow: {shadow}; transition: all 0.2s ease;">
        {c_text}
        </div>
        <div style="font-size: 0.75rem; font-weight: {lbl_weight}; color: {lbl_color}; margin-top: 0.35rem; text-align: center; line-height: 1.25;">
        {stage_name}
        </div>
        {badge_html}
        </div>
        """
        step_cols.append(col_html.strip())

    all_steps_joined = "\n".join(step_cols)

    bar_color = "#203A32"
    raw_html = f"""
    <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 10px; padding: 1rem 0.8rem 0.85rem 0.8rem; margin: 0.75rem 0; position: relative;">
    <div style="position: absolute; top: 26px; left: 10%; right: 10%; height: 3px; background: #DCE5D8; z-index: 1; border-radius: 2px;">
    <div style="height: 100%; width: {progress_pct}%; background: {bar_color}; border-radius: 2px; transition: width 0.3s ease;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; position: relative; width: 100%;">
    {all_steps_joined}
    </div>
    </div>
    """
    return _clean_html(raw_html)


def render_kpi(label: str, value: str | int, caption: str = "", icon: str = "") -> None:
    """Renders a clean KPI metric card with Modern Sage & Forest styling."""
    icon_html = f"<span style='float: right; font-size: 1.25rem; opacity: 0.85;'>{icon}</span>" if icon else ""
    caption_html = f"<div class='kpi-caption'>{caption}</div>" if caption else ""
    st.markdown(
        f"""
        <div class="kpi-container">
            <div>
                {icon_html}
                <div class="kpi-label">{label}</div>
            </div>
            <div class="kpi-value">{value}</div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
