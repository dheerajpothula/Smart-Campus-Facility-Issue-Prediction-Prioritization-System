"""
Facility Operations Control Centre — Unified Requests Management.
Implements:
- Phase 5: All Requests (Search, Multi-Filter, Sorting, Pagination, Unified Table)
- Phase 7: New / Unassigned (Triage, Assignment, Review)
- Phase 8: In Progress (Active Technical Repairs, Progress Logs, Resolution)
- Phase 9: Resolved (Permanent Archive, Reopening, History Preservation)
- Phase 6: Right-Side Complaint Details Panel Integration
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from dashboard.components.admin_header import render_admin_header
from dashboard.components.complaint_details import render_complaint_details_panel
from dashboard.components.styles import get_priority_badge, get_status_badge, _clean_html
from src.data.complaints_store import get_complaints_df, PROGRESS_STAGES


def render_requests_view(view_mode: str = "all") -> None:
    """
    Renders the unified request management interface for the given view mode.

    Args:
        view_mode: One of 'all', 'new', 'in_progress', 'resolved'.
    """
    titles = {
        "all": ("All Requests", "Surveillance and lifecycle management of all campus facility tickets and work orders.", "ALL REQUESTS REGISTER"),
        "new": ("New / Unassigned", "Incoming complaints awaiting administrator evaluation, priority validation, and squad dispatch.", "NEW & UNASSIGNED TRIAGE"),
        "in_progress": ("In Progress", "Active repair operations, dispatched technical squads, and ongoing maintenance tasks.", "IN PROGRESS WORK ORDERS"),
        "resolved": ("Resolved", "Permanent historical archive of verified, closed, and resolved campus facility tickets.", "RESOLVED FACILITY ARCHIVE"),
    }

    title, subtitle, kicker = titles.get(view_mode, titles["all"])
    render_admin_header(page_title=title, subtitle=subtitle, kicker=kicker)

    raw_df = get_complaints_df()

    if raw_df.empty:
        st.info("No facility tickets currently loaded in the repository.")
        return

    # Base filtering by view mode
    if view_mode == "new":
        mode_df = raw_df[raw_df["status"] == "Submitted"]
    elif view_mode == "in_progress":
        mode_df = raw_df[raw_df["status"].isin(["In Progress", "Under Review", "Assigned"])]
    elif view_mode == "resolved":
        mode_df = raw_df[raw_df["status"] == "Resolved"]
    else:
        mode_df = raw_df.copy()

    # Search & Interactive Filter Bar
    with st.expander("🔍 Search, Filters & Sorting Options", expanded=True):
        c_search, c_sort = st.columns([2.5, 1.5])
        with c_search:
            search_query = st.text_input(
                "Search Requests",
                placeholder="Search by Complaint Token (e.g. CMP-2026-001), Student ID, or Issue Title...",
                key=f"search_{view_mode}",
            )
        with c_sort:
            sort_by = st.selectbox(
                "Sort Records By",
                options=["Newest First", "Oldest First", "Highest Priority (MCPI)"],
                index=0,
                key=f"sort_{view_mode}",
            )

        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            if view_mode == "all":
                status_choices = ["All Statuses"] + PROGRESS_STAGES + ["Withdrawn"]
                sel_status = st.selectbox("Status Filter", options=status_choices, key=f"f_stat_{view_mode}")
            else:
                sel_status = "All Statuses"

        with f_col2:
            all_cats = sorted(list(raw_df["facility_type"].dropna().unique()))
            cat_choices = ["All Categories"] + all_cats
            sel_cat = st.selectbox("Category Filter", options=cat_choices, key=f"f_cat_{view_mode}")

        with f_col3:
            all_locs = sorted(list(raw_df["building"].dropna().unique()))
            if not all_locs:
                all_locs = sorted(list(raw_df["location"].dropna().unique()))
            loc_choices = ["All Locations"] + all_locs
            sel_loc = st.selectbox("Building / Location", options=loc_choices, key=f"f_loc_{view_mode}")

        with f_col4:
            priority_choices = ["All Priorities", "Critical", "High", "Medium", "Low"]
            sel_prio = st.selectbox("MCPI Priority Tier", options=priority_choices, key=f"f_prio_{view_mode}")

    # Apply search and filters
    filtered_df = mode_df.copy()

    # Search: Complaint token, Student ID, Issue title
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["complaint_id"].str.lower().str.contains(q, na=False)
            | filtered_df["title"].str.lower().str.contains(q, na=False)
            | filtered_df["student_id"].fillna("").str.lower().str.contains(q, na=False)
            | filtered_df["student_name"].fillna("").str.lower().str.contains(q, na=False)
            | filtered_df["description"].str.lower().str.contains(q, na=False)
        ]

    # Filters
    if sel_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["status"] == sel_status]
    if sel_cat != "All Categories":
        filtered_df = filtered_df[filtered_df["facility_type"] == sel_cat]
    if sel_loc != "All Locations":
        filtered_df = filtered_df[
            (filtered_df["building"] == sel_loc) | (filtered_df["location"].str.contains(sel_loc, na=False))
        ]
    if sel_prio != "All Priorities":
        filtered_df = filtered_df[filtered_df["priority_tier"] == sel_prio]

    # Sorting
    if sort_by == "Newest First" and "date_reported" in filtered_df.columns:
        filtered_df["_sort_d"] = pd.to_datetime(filtered_df["date_reported"], errors="coerce")
        filtered_df = filtered_df.sort_values(by="_sort_d", ascending=False).drop(columns=["_sort_d"])
    elif sort_by == "Oldest First" and "date_reported" in filtered_df.columns:
        filtered_df["_sort_d"] = pd.to_datetime(filtered_df["date_reported"], errors="coerce")
        filtered_df = filtered_df.sort_values(by="_sort_d", ascending=True).drop(columns=["_sort_d"])
    elif sort_by == "Highest Priority (MCPI)" and "priority_score" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by="priority_score", ascending=False)

    # Check for selected complaint for right-side details panel
    selected_cid = st.session_state.get("admin_selected_complaint_id")
    selected_record = None
    if selected_cid and not raw_df.empty:
        matching = raw_df[raw_df["complaint_id"] == selected_cid]
        if not matching.empty:
            selected_record = matching.iloc[0].to_dict()
        else:
            st.session_state["admin_selected_complaint_id"] = None

    # Layout: Split if a complaint is selected
    if selected_record:
        col_table, col_details = st.columns([1.35, 1.0], gap="large")
    else:
        col_table = st.container()
        col_details = None

    with col_table:
        # Results count & Export
        c_meta_left, c_meta_right = st.columns([3, 1])
        with c_meta_left:
            st.markdown(
                f"<div style='font-size: 0.9rem; font-weight: 700; color: #203A32; padding: 0.4rem 0;'>"
                f"Showing <strong>{len(filtered_df)}</strong> of {len(mode_df)} records in active view:"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c_meta_right:
            st.download_button(
                "📥 Export CSV",
                data=filtered_df.to_csv(index=False),
                file_name=f"fipp_{view_mode}_requests.csv",
                mime="text/csv",
                type="secondary",
                use_container_width=True,
                key=f"dl_csv_{view_mode}",
            )

        if filtered_df.empty:
            st.warning("No complaint records match your current search and filter criteria.")
            return

        # Pagination: 10 items per page
        page_size = 10
        total_items = len(filtered_df)
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        if total_pages > 1:
            c_p1, c_p2 = st.columns([1, 3])
            with c_p1:
                page_num = st.selectbox(
                    "Page",
                    options=list(range(1, total_pages + 1)),
                    index=0,
                    key=f"page_sel_{view_mode}",
                )
            start_idx = (page_num - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            page_df = filtered_df.iloc[start_idx:end_idx]
        else:
            page_df = filtered_df

        # Render styled complaint rows
        for _, row in page_df.iterrows():
            cid = row["complaint_id"]
            title = row.get("title", "Issue")
            cat = row.get("facility_type") or row.get("category", "General")
            loc = row.get("location", "Campus")
            status = row.get("status", "Submitted")
            s_badge = get_status_badge(status)
            p_badge = get_priority_badge(row.get("priority_tier", "Medium"))
            score = row.get("priority_score", 0.0)
            dt = row.get("date_reported", "")
            stu_id = row.get("student_id")
            stu_name = row.get("student_name")
            allotted = row.get("allotted_person")

            is_active = (cid == selected_cid)
            card_border = "border: 2px solid #203A32; background: #FAFBF9;" if is_active else "border: 1px solid #DCE5D8; background: #FFFFFF;"

            if stu_id:
                reporter_html = f'<span style="background-color: #DCE5D8; color: #203A32; border: 1px solid #A8B9A3; padding: 0.12rem 0.45rem; border-radius: 4px; font-size: 0.74rem; font-weight: 600;">🎓 {stu_name or "Student"} ({stu_id})</span>'
            else:
                rep_by = row.get("reported_by", "Staff")
                reporter_html = f'<span style="background-color: #F0F4ED; color: #203A32; border: 1px solid #DCE5D8; padding: 0.12rem 0.45rem; border-radius: 4px; font-size: 0.74rem; font-weight: 600;">👤 {rep_by}</span>'

            staff_html = f"<span style='color: #4A6357; font-size: 0.76rem;'>&bull; Assigned: <strong>{allotted}</strong></span>" if allotted else ""

            st.markdown(
                _clean_html(
                    f"""
                    <div class="dashboard-card" style="
                        {card_border}
                        border-radius: 10px;
                        padding: 0.95rem 1.25rem;
                        margin-bottom: 0.65rem;
                        box-shadow: 0 1px 4px rgba(32, 58, 50, 0.03);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; flex-wrap: wrap;">
                            <div style="flex: 1; min-width: 260px;">
                                <div style="display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.3rem;">
                                    <span style="font-family: monospace; font-size: 0.8rem; font-weight: 800; color: #203A32; background: #DCE5D8; padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid #A8B9A3;">
                                        {cid}
                                    </span>
                                    <span style="font-size: 0.75rem; font-weight: 600; color: #4A6357; background: #F0F4ED; padding: 0.15rem 0.45rem; border-radius: 4px;">
                                        {cat}
                                    </span>
                                    {reporter_html}
                                    {staff_html}
                                </div>
                                <h4 style="margin: 0.2rem 0; font-size: 1.02rem; font-weight: 750; color: #203A32;">
                                    {title}
                                </h4>
                                <div style="font-size: 0.79rem; color: #6D8276; margin-top: 0.25rem;">
                                    📍 <strong>{loc}</strong> &bull; 📅 {dt} &bull; Priority Score: <strong>{score}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 0.4rem;">
                                {p_badge}
                                {s_badge}
                            </div>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            # Inspect Button for Row
            btn_col, _ = st.columns([1.2, 3])
            with btn_col:
                btn_text = "Viewing Details 🔍" if is_active else "Inspect Ticket →"
                if st.button(btn_text, key=f"btn_inspect_{view_mode}_{cid}", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state["admin_selected_complaint_id"] = cid
                    st.rerun()

    # Right-side details panel
    if col_details is not None and selected_record is not None:
        with col_details:
            render_complaint_details_panel(selected_record)


def render_all_requests_page() -> None:
    render_requests_view("all")


def render_new_unassigned_page() -> None:
    render_requests_view("new")


def render_in_progress_page() -> None:
    render_requests_view("in_progress")


def render_resolved_page() -> None:
    render_requests_view("resolved")
