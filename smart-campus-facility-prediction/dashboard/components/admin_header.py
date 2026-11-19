"""
Facility Operations Control Centre — Top Header Component.
Renders the unified administrative header across all Control Centre views:
- System Identification: FIPP ADMINISTRATION • Control Centre
- Page Title and Operational Subtitle
- Authenticated Administrator Identity & Role Badge (e.g. ADM-2026-001 • Facility Operations Lead)
- Quick Logout / Session Action
"""
import streamlit as st


def render_admin_header(
    page_title: str,
    subtitle: str = "",
    kicker: str = "FACILITY OPERATIONS CONTROL CENTRE",
) -> None:
    """
    Renders the professional Control Centre header banner in Modern Sage & Forest styling.

    Args:
        page_title: The main title of the active section (e.g. 'Overview', 'All Requests').
        subtitle: Operational context or instructions for facility staff.
        kicker: Uppercase eyebrow identifying the Control Centre scope.
    """
    auth = st.session_state.get("auth_user") or {}
    admin_name = auth.get("name", "Administrator")
    admin_id = auth.get("id", "ADM-2026-001")
    admin_title = auth.get("title") or auth.get("role_title", "Facility Operations Lead")

    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #DCE5D8;
            border-left: 5px solid #203A32;
            border-radius: 12px;
            padding: 1.25rem 1.6rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(32, 58, 50, 0.04);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        ">
            <div>
                <div style="
                    font-size: 0.72rem;
                    font-weight: 800;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    color: #4A6357;
                    margin-bottom: 0.25rem;
                ">
                    FIPP ADMINISTRATION &bull; {kicker}
                </div>
                <h1 style="
                    margin: 0 0 0.25rem 0;
                    font-size: 1.65rem;
                    font-weight: 800;
                    color: #203A32;
                    letter-spacing: -0.02em;
                    line-height: 1.2;
                ">
                    {page_title}
                </h1>
                <p style="
                    margin: 0;
                    font-size: 0.88rem;
                    color: #4A6357;
                    line-height: 1.45;
                ">
                    {subtitle}
                </p>
            </div>
            <div style="
                background: #F5F7F2;
                border: 1px solid #DCE5D8;
                border-radius: 10px;
                padding: 0.65rem 1rem;
                display: flex;
                align-items: center;
                gap: 0.85rem;
            ">
                <div style="
                    width: 38px;
                    height: 38px;
                    border-radius: 8px;
                    background-color: #DCE5D8;
                    border: 1px solid #A8B9A3;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.25rem;
                ">
                    🛡️
                </div>
                <div>
                    <div style="font-size: 0.86rem; font-weight: 700; color: #203A32;">
                        {admin_name}
                    </div>
                    <div style="font-size: 0.76rem; color: #4A6357; font-weight: 500;">
                        {admin_title} &bull; <code style="font-size: 0.72rem; color: #203A32; background: #DCE5D8; padding: 0.1rem 0.35rem; border-radius: 4px;">{admin_id}</code>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
