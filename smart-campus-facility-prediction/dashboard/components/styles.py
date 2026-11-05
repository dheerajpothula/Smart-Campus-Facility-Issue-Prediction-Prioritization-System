"""
Global Light Theme Styling and UI Utilities.
Strict 60/30/10 Color Harmony with High-Contrast Accessible Buttons:
- 60% Warm Chalk: #FDFBF7 (background canvas, large areas)
- 30% Deep Charcoal: #1A1A1A (typography, icons, thin borders, headers)
- 10% Soft Tan: #EAE3D2 (cards, subtle accents, badges)

Button Hierarchy & Visibility:
- Primary Buttons: Warm Dark Tan / Brown (#756044) with Crisp White (#FFFFFF) text.
  Hover: #5D4A32. Focus: outline & ring.
- Secondary Buttons: Soft Tan (#EAE3D2) with Deep Charcoal (#1A1A1A) text.
  Hover: #D8CDB8. Border: #D8CFBD.
- Outline Buttons: Transparent/Warm Chalk with Deep Charcoal (#1A1A1A) border & text.
  Hover: #EAE3D2.
- Disabled Buttons: Muted Tan (#EDE8DE) with legible dark tan text (#8C8274).
"""
import streamlit as st


GLOBAL_LIGHT_THEME_CSS = """
<style>
    /* =========================================================================
       GLOBAL 60/30/10 COLOR HARMONY & BUTTON DESIGN TOKENS
       ========================================================================= */
    :root {
        --warm-chalk: #FDFBF7;
        --deep-charcoal: #1A1A1A;
        --charcoal-light: #2D2D2D;
        --charcoal-muted: #555555;
        --charcoal-subtle: #767676;
        --charcoal-border: #DCD6C8;

        --soft-tan: #EAE3D2;
        --soft-tan-light: #F6F3EB;
        --soft-tan-dark: #D8CDB8;
        --soft-tan-border: #D8CFBD;

        /* Primary Button: Warm, Dark Tan / Brown */
        --primary-btn-bg: #756044;
        --primary-btn-text: #FFFFFF;
        --primary-btn-hover: #5D4A32;
        --primary-btn-border: #756044;

        /* Secondary Button: Soft Tan */
        --secondary-btn-bg: #EAE3D2;
        --secondary-btn-text: #1A1A1A;
        --secondary-btn-hover: #D8CDB8;
        --secondary-btn-border: #D8CFBD;

        --card-bg: #FFFFFF;
        --card-border: #EAE3D2;

        --radius: 10px;
        --shadow-soft: 0 1px 3px rgba(26, 26, 26, 0.04), 0 4px 6px -1px rgba(26, 26, 26, 0.03);
        --shadow-hover: 0 10px 15px -3px rgba(26, 26, 26, 0.06), 0 4px 6px -4px rgba(26, 26, 26, 0.03);
    }

    /* Enforce Warm Chalk background and Deep Charcoal readable typography */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--warm-chalk) !important;
        color: var(--deep-charcoal) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* Main view container padding */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1320px !important;
    }

    /* Hide default Streamlit left sidebar so Admin right sidebar is primary */
    [data-testid="stSidebar"] {
        display: none !important;
    }

    /* Header typography */
    h1 {
        color: var(--deep-charcoal) !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.4rem !important;
    }
    h2 {
        color: var(--deep-charcoal) !important;
        font-weight: 600 !important;
        font-size: 1.35rem !important;
        letter-spacing: -0.01em !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    h3 {
        color: var(--deep-charcoal) !important;
        font-weight: 600 !important;
        font-size: 1.12rem !important;
        margin-bottom: 0.35rem !important;
    }
    p, li, span {
        color: var(--deep-charcoal);
        line-height: 1.55;
    }

    /* CRITICAL: Inherit button label styling so global p rules do not override button contrast */
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
       Warm, dark tan/brown (#756044) with crisp white text (#FFFFFF).
       Hover: #5D4A32.
       Used for: Login, Raise an Issue, Submit Issue, Save Changes, Dispatch
       ========================================================================= */
    button[kind="primary"],
    [data-testid="baseButton-primary"],
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"],
    .primary-btn button {
        background-color: var(--primary-btn-bg) !important;
        color: var(--primary-btn-text) !important;
        border: 1px solid var(--primary-btn-border) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.25rem !important;
        cursor: pointer !important;
        box-shadow: 0 1px 3px rgba(117, 96, 68, 0.25) !important;
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
    .primary-btn button p,
    .primary-btn button span {
        color: #FFFFFF !important;
    }
    button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover,
    .primary-btn button:hover {
        background-color: var(--primary-btn-hover) !important;
        border-color: var(--primary-btn-hover) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 8px -1px rgba(93, 74, 50, 0.3) !important;
        transform: translateY(-1px);
    }
    button[kind="primary"]:hover p,
    button[kind="primary"]:hover span,
    [data-testid="baseButton-primary"]:hover p,
    [data-testid="baseButton-primary"]:hover span {
        color: #FFFFFF !important;
    }
    button[kind="primary"]:focus,
    button[kind="primary"]:focus-visible,
    [data-testid="baseButton-primary"]:focus,
    .primary-btn button:focus {
        outline: 2px solid var(--primary-btn-hover) !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(117, 96, 68, 0.35) !important;
    }
    button[kind="primary"]:active,
    [data-testid="baseButton-primary"]:active {
        transform: translateY(1px);
    }

    /* =========================================================================
       2. SECONDARY BUTTONS (AND DEFAULT FALLBACK)
       Soft Tan (#EAE3D2) with Deep Charcoal (#1A1A1A) text.
       Hover: #D8CDB8.
       Used for: Cancel, Back, Logout/Exit, Reset, Secondary actions
       ========================================================================= */
    button[kind="secondary"],
    [data-testid="baseButton-secondary"],
    .stButton > button[kind="secondary"],
    .stFormSubmitButton > button[kind="secondary"],
    .secondary-btn button,
    .stButton > button,
    .stFormSubmitButton > button {
        background-color: var(--secondary-btn-bg) !important;
        color: var(--secondary-btn-text) !important;
        border: 1px solid var(--secondary-btn-border) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.25rem !important;
        cursor: pointer !important;
        box-shadow: 0 1px 2px rgba(26, 26, 26, 0.05) !important;
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
    .stButton > button p,
    .stButton > button span,
    .stFormSubmitButton > button p,
    .stFormSubmitButton > button span {
        color: var(--deep-charcoal) !important;
    }
    button[kind="secondary"]:hover,
    [data-testid="baseButton-secondary"]:hover,
    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    .secondary-btn button:hover {
        background-color: var(--secondary-btn-hover) !important;
        border-color: #C5B9A2 !important;
        color: var(--deep-charcoal) !important;
        box-shadow: 0 3px 6px rgba(26, 26, 26, 0.08) !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"]:hover p,
    button[kind="secondary"]:hover span,
    .stButton > button:hover p,
    .stButton > button:hover span {
        color: var(--deep-charcoal) !important;
    }
    button[kind="secondary"]:focus,
    button[kind="secondary"]:focus-visible,
    [data-testid="baseButton-secondary"]:focus,
    .stButton > button:focus,
    .secondary-btn button:focus {
        outline: 2px solid #756044 !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(216, 205, 184, 0.5) !important;
    }
    button[kind="secondary"]:active,
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* =========================================================================
       3. OUTLINE BUTTONS
       Transparent or Warm Chalk with Deep Charcoal (#1A1A1A) border & text.
       Hover: Soft Tan (#EAE3D2).
       ========================================================================= */
    .outline-btn button,
    button.outline-btn {
        background-color: transparent !important;
        color: var(--deep-charcoal) !important;
        border: 1px solid var(--deep-charcoal) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.25rem !important;
        transition: all 0.15s ease-in-out !important;
        cursor: pointer !important;
    }
    .outline-btn button p,
    .outline-btn button span {
        color: var(--deep-charcoal) !important;
    }
    .outline-btn button:hover {
        background-color: var(--soft-tan) !important;
        border-color: var(--deep-charcoal) !important;
        color: var(--deep-charcoal) !important;
        transform: translateY(-1px);
    }
    .outline-btn button:focus {
        outline: 2px solid var(--deep-charcoal) !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.15) !important;
    }

    /* =========================================================================
       4. DISABLED BUTTONS
       Clearly muted yet readable labels without losing context.
       ========================================================================= */
    button:disabled,
    button[disabled],
    .stButton > button:disabled,
    .stFormSubmitButton > button:disabled,
    button[kind="primary"]:disabled,
    button[kind="secondary"]:disabled {
        background-color: #EDE8DE !important;
        color: #8C8274 !important;
        border-color: #DFD7C8 !important;
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
        color: #8C8274 !important;
    }

    /* SaaS Dashboard Cards */
    .dashboard-card {
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius);
        padding: 1.25rem 1.4rem;
        box-shadow: var(--shadow-soft);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
    }
    .dashboard-card:hover {
        border-color: var(--soft-tan-dark);
        box-shadow: var(--shadow-hover);
    }

    /* Right Sidebar Container Styling */
    .admin-sidebar-box {
        background-color: #FFFFFF;
        border: 1px solid var(--soft-tan);
        border-radius: var(--radius);
        padding: 1.25rem 1.15rem;
        box-shadow: var(--shadow-soft);
        margin-bottom: 1rem;
    }

    /* KPI Metric Cards */
    .kpi-container {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-soft);
        height: 100%;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .kpi-container:hover {
        box-shadow: var(--shadow-hover);
        border-color: var(--soft-tan-dark);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--charcoal-subtle);
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: var(--deep-charcoal);
        line-height: 1.2;
    }
    .kpi-caption {
        font-size: 0.76rem;
        color: var(--charcoal-subtle);
        margin-top: 0.3rem;
    }

    /* Inputs, Selectboxes, Tabs */
    .stTextInput input, .stSelectbox select, .stTextArea textarea,
    [data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--soft-tan-border) !important;
        border-radius: 8px !important;
        color: var(--deep-charcoal) !important;
        font-size: 0.92rem !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus,
    [data-baseweb="select"]:focus-within {
        border-color: var(--primary-btn-bg) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(117, 96, 68, 0.25) !important;
    }

    /* Tab navigation polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--soft-tan-border) !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: var(--charcoal-muted) !important;
        border-radius: 6px 6px 0 0 !important;
        transition: color 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--deep-charcoal) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--deep-charcoal) !important;
        border-bottom: 2px solid var(--primary-btn-bg) !important;
    }

    /* Radio navigation on right sidebar */
    [data-testid="stRadio"] label {
        font-size: 0.92rem !important;
        color: var(--deep-charcoal) !important;
        cursor: pointer !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 6px !important;
        transition: background-color 0.15s ease !important;
    }
    [data-testid="stRadio"] label:hover {
        background-color: var(--soft-tan-light) !important;
    }

    /* File uploader button */
    [data-testid="stFileUploader"] section button {
        background-color: var(--secondary-btn-bg) !important;
        color: var(--deep-charcoal) !important;
        border: 1px solid var(--secondary-btn-border) !important;
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
    """Injects standard 60/30/10 light theme CSS with high-contrast button styling."""
    st.markdown(GLOBAL_LIGHT_THEME_CSS, unsafe_allow_html=True)


def get_priority_badge(priority: str) -> str:
    """
    Returns an HTML priority badge string adhering to Warm Chalk, Deep Charcoal, and Soft Tan.
    - Critical: Deep Charcoal (#1A1A1A on #EBDCDA)
    - High: Soft Tan Dark (#1A1A1A on #EAE3D2)
    - Medium: Soft Tan Light (#1A1A1A on #F6F3EB)
    - Low: Warm Outline (#4A4A4A on #FFFFFF)
    """
    p_lower = str(priority).strip().lower()
    if "crit" in p_lower or "p1" in p_lower:
        bg, color, border = "#EBDCDA", "#1A1A1A", "#D3BCB9"
        label = "Critical"
    elif "high" in p_lower or "p2" in p_lower:
        bg, color, border = "#EAE3D2", "#1A1A1A", "#D8CFBD"
        label = "High"
    elif "med" in p_lower or "p3" in p_lower:
        bg, color, border = "#F6F3EB", "#2D2D2D", "#EAE3D2"
        label = "Medium"
    else:
        bg, color, border = "#FFFFFF", "#555555", "#EAE3D2"
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
    Returns an HTML maintenance status badge.
    Pill with clean border in 60/30/10 palette.
    Supports all 5 standard progress stages: Submitted, Under Review, Assigned, In Progress, Resolved.
    """
    s_lower = str(status).strip().lower()
    if "resolved" in s_lower or "closed" in s_lower:
        bg, color, border = "#1A1A1A", "#FDFBF7", "#1A1A1A"
        icon = "✓ "
        label = "Resolved"
    elif "progress" in s_lower or "investigating" in s_lower:
        bg, color, border = "#EAE3D2", "#1A1A1A", "#D8CFBD"
        icon = "⏳ "
        label = "In Progress"
    elif "dispatched" in s_lower or "assigned" in s_lower:
        bg, color, border = "#F2ECE1", "#1A1A1A", "#E0D7C5"
        icon = "⚡ "
        label = "Assigned"
    elif "review" in s_lower:
        bg, color, border = "#F6F3EB", "#2D2D2D", "#EAE3D2"
        icon = "● "
        label = "Under Review"
    else:  # Submitted / Reported
        bg, color, border = "#FFFFFF", "#555555", "#D8CFBD"
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
        display: inline-block;
        white-space: nowrap;
    ">{icon}{label}</span>"""


def _clean_html(html_str: str) -> str:
    """Strips leading whitespace from every line to prevent CommonMark from rendering HTML as an indented code block."""
    return "\n".join(line.strip() for line in html_str.splitlines() if line.strip())


def render_student_progress_timeline(current_status: str) -> str:
    """
    Renders an accessible, responsive 5-stage progress indicator:
    1. Submitted -> 2. Under Review -> 3. Assigned -> 4. In Progress -> 5. Resolved
    Styled using 60/30/10 (Warm Chalk, Deep Charcoal, Soft Tan).
    Does NOT display priority labels or ML scores.
    Guaranteed clean unindented HTML output to prevent Streamlit from interpreting HTML as code.
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
            c_bg = "#EAE3D2"
            c_fg = "#1A1A1A"
            c_border = "#D8CFBD"
            c_text = "✓"
            lbl_color = "#2D2D2D"
            lbl_weight = "600"
            badge_html = ""
            shadow = "none"
        elif is_active:
            if stage_name == "Resolved":
                c_bg = "#1A1A1A"
                c_fg = "#FDFBF7"
                c_border = "#1A1A1A"
                c_text = "✓"
                lbl_color = "#1A1A1A"
                lbl_weight = "700"
                badge_html = '<div style="margin-top: 3px;"><span style="font-size: 0.65rem; background: #EAE3D2; color: #1A1A1A; border-radius: 9999px; padding: 0.1rem 0.45rem; font-weight: 700; border: 1px solid #D8CFBD;">Completed</span></div>'
                shadow = "0 0 0 3px rgba(26, 26, 26, 0.15)"
            else:
                c_bg = "#1A1A1A"
                c_fg = "#FDFBF7"
                c_border = "#1A1A1A"
                c_text = str(i + 1)
                lbl_color = "#1A1A1A"
                lbl_weight = "700"
                badge_html = '<div style="margin-top: 3px;"><span style="font-size: 0.65rem; background: #EAE3D2; color: #1A1A1A; border-radius: 9999px; padding: 0.1rem 0.45rem; font-weight: 700; border: 1px solid #D8CFBD;">Active</span></div>'
                shadow = "0 0 0 3px rgba(26, 26, 26, 0.15)"
        else:
            c_bg = "#FDFBF7"
            c_fg = "#767676"
            c_border = "#D8CFBD"
            c_text = str(i + 1)
            lbl_color = "#767676"
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

    bar_color = "#1A1A1A"
    raw_html = f"""
    <div style="background: #FDFBF7; border: 1px solid #EAE3D2; border-radius: 10px; padding: 1rem 0.8rem 0.85rem 0.8rem; margin: 0.75rem 0; position: relative;">
    <div style="position: absolute; top: 26px; left: 10%; right: 10%; height: 3px; background: #EAE3D2; z-index: 1; border-radius: 2px;">
    <div style="height: 100%; width: {progress_pct}%; background: {bar_color}; border-radius: 2px; transition: width 0.3s ease;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; position: relative; width: 100%;">
    {all_steps_joined}
    </div>
    </div>
    """
    return _clean_html(raw_html)


def render_kpi(label: str, value: str | int, caption: str = "", icon: str = "") -> None:
    """Renders a clean KPI metric card with soft tan borders in 60/30/10 palette."""
    icon_html = f"<span style='float: right; font-size: 1.25rem; opacity: 0.8;'>{icon}</span>" if icon else ""
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
