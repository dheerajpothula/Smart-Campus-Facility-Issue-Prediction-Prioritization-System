"""
Facility Operations Control Centre — Unified Requests Management.
Implements Phase 2: All Requests (Search, Multi-Filter, Sorting, Pagination, Enterprise Table,
and Right-Side Complaint Details Panel).
Preserves Modern Sage & Forest color system and enterprise dashboard usability patterns.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from dashboard.components.admin_header import render_admin_header
from dashboard.components.complaint_details import render_complaint_details_panel
from dashboard.components.styles import get_priority_badge, get_status_badge, _clean_html
from src.data.complaints_store import get_complaints_df, PROGRESS_STAGES


def reset_requests_filters(view_mode: str) -> None:
    """
    Safely resets all filter and search session-state variables BEFORE widget instantiation.
    Executed as an on_click callback by Streamlit prior to script execution.
    """
    st.session_state[f"search_{view_mode}"] = ""
    st.session_state[f"sort_{view_mode}"] = "Newest first"
    st.session_state[f"f_stat_{view_mode}"] = "All Statuses"
    st.session_state[f"f_cat_{view_mode}"] = "All Categories"
    st.session_state[f"f_loc_{view_mode}"] = "All Locations"
    st.session_state[f"f_date_{view_mode}"] = "All Dates"
    st.session_state[f"f_prio_{view_mode}"] = "All Priorities"
    st.session_state[f"page_sel_{view_mode}"] = 1


def render_requests_view(view_mode: str = "all") -> None:
    """
    Renders the unified request management interface for the given view mode.

    Args:
        view_mode: One of 'all', 'new', 'in_progress', 'resolved'.
    """
    # Safe session-state initialization before creating widgets
    if st.query_params.get("search"):
        st.session_state[f"search_{view_mode}"] = st.query_params.get("search")
    else:
        st.session_state.setdefault(f"search_{view_mode}", "")
    st.session_state.setdefault(f"sort_{view_mode}", "Newest first")
    st.session_state.setdefault(f"f_stat_{view_mode}", "All Statuses")
    st.session_state.setdefault(f"f_cat_{view_mode}", "All Categories")
    st.session_state.setdefault(f"f_loc_{view_mode}", "All Locations")
    st.session_state.setdefault(f"f_date_{view_mode}", "All Dates")
    st.session_state.setdefault(f"f_prio_{view_mode}", "All Priorities")
    st.session_state.setdefault(f"page_sel_{view_mode}", 1)

    titles = {
        "all": ("All Requests", "Manage and review submitted facility complaints.", "FACILITY OPERATIONS · ALL REQUESTS"),
        "new": ("New / Unassigned", "Review newly submitted facility complaints awaiting administrative action.", "NEW & UNASSIGNED TRIAGE"),
        "in_progress": ("In Progress", "Active repair operations, dispatched technical squads, and ongoing maintenance tasks.", "IN PROGRESS WORK ORDERS"),
        "resolved": ("Resolved", "Permanent historical archive of verified, closed, and resolved campus facility tickets.", "RESOLVED FACILITY ARCHIVE"),
    }

    title, subtitle, kicker = titles.get(view_mode, titles["all"])
    render_admin_header(page_title=title, subtitle=subtitle, kicker=kicker)

    raw_df = get_complaints_df()

    if raw_df.empty:
        st.info("No facility tickets currently loaded in the repository.")
        return

    # Defensive column extraction for staff assignments
    staff_s = raw_df["assigned_staff"] if "assigned_staff" in raw_df.columns else pd.Series([""] * len(raw_df), index=raw_df.index)
    allotted_s = raw_df["allotted_person"] if "allotted_person" in raw_df.columns else pd.Series([""] * len(raw_df), index=raw_df.index)
    is_unassigned_record = staff_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"]) & \
                           allotted_s.fillna("").astype(str).str.strip().isin(["", "Unassigned", "None"])

    # Base filtering by view mode
    if view_mode == "new":
        is_submitted = raw_df["status"] == "Submitted"
        is_unassigned_review = (raw_df["status"] == "Under Review") & is_unassigned_record
        mode_df = raw_df[is_submitted | is_unassigned_review]
    elif view_mode == "in_progress":
        mode_df = raw_df[raw_df["status"].isin(["In Progress", "Under Review", "Assigned"])]
    elif view_mode == "resolved":
        mode_df = raw_df[raw_df["status"] == "Resolved"]
    else:
        mode_df = raw_df.copy()

    # 1. SUMMARY INFORMATION: Compact, restrained summary indicators calculated dynamically
    if view_mode == "new":
        total_new_count = int((raw_df["status"] == "Submitted").sum())
        awaiting_review_count = int((raw_df["status"] == "Under Review").sum())
        unassigned_count = int(
            ((raw_df["status"].isin(["Submitted", "Under Review"])) & is_unassigned_record).sum()
        )
        st.markdown(
            f"""
            <div style="display: flex; gap: 0.65rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.85rem;">
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">Total New Requests</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{total_new_count}</span>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #55685F;"></span>
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">Awaiting Review</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{awaiting_review_count}</span>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #A8B9A3;"></span>
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">Unassigned</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{unassigned_count}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        total_count = len(raw_df)
        new_count = int((raw_df["status"] == "Submitted").sum())
        in_prog_count = int(raw_df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum())
        resolved_count = int((raw_df["status"] == "Resolved").sum())

        st.markdown(
            f"""
            <div style="display: flex; gap: 0.65rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.85rem;">
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">Total Requests</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{total_count}</span>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #55685F;"></span>
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">New</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{new_count}</span>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #A8B9A3;"></span>
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">In Progress</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{in_prog_count}</span>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #203A32;"></span>
                    <span style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.04em; color: #55685F;">Resolved</span>
                    <span style="font-size: 0.95rem; font-weight: 800; color: #203A32;">{resolved_count}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. SEARCH & FILTERS TOOLBAR: Single compact, unified toolbar
    st.markdown(
        """
        <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 8px; padding: 0.75rem 1rem 0.5rem 1rem; margin-bottom: 0.85rem;">
            <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F; margin-bottom: 0.4rem;">
                Search, Filters &amp; Sorting
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Toolbar Row 1: Search text input, Sort dropdown, Reset action
    c_srch, c_srt, c_rst = st.columns([3.2, 1.8, 0.9])
    with c_srch:
        search_query = st.text_input(
            "Search Requests",
            placeholder="Search by Complaint Token, Student ID, or Issue Title...",
            key=f"search_{view_mode}",
            label_visibility="collapsed",
        )
    with c_srt:
        sort_options = ["Newest first", "Oldest first", "Highest existing priority"]
        if st.session_state.get(f"sort_{view_mode}") not in sort_options:
            st.session_state[f"sort_{view_mode}"] = "Newest first"
        cur_sort = st.session_state[f"sort_{view_mode}"]
        cur_sort_idx = sort_options.index(cur_sort)
        sort_by = st.selectbox(
            "Sort Records",
            options=sort_options,
            index=cur_sort_idx,
            key=f"sort_{view_mode}",
            label_visibility="collapsed",
        )
    with c_rst:
        st.button(
            "Clear Filters",
            key=f"btn_reset_{view_mode}",
            type="secondary",
            use_container_width=True,
            on_click=reset_requests_filters,
            args=(view_mode,),
        )

    # Toolbar Row 2: Five compact filters supporting stored fields
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.1, 1.2, 1.2, 1.1, 1.1])

    with f_col1:
        if view_mode == "all":
            status_choices = ["All Statuses"] + PROGRESS_STAGES + ["Withdrawn"]
        elif view_mode == "new":
            status_choices = ["All Statuses", "Submitted", "Under Review"]
        else:
            status_choices = ["All Statuses"]
        if st.session_state.get(f"f_stat_{view_mode}") not in status_choices:
            st.session_state[f"f_stat_{view_mode}"] = "All Statuses"
        cur_stat = st.session_state[f"f_stat_{view_mode}"]
        cur_stat_idx = status_choices.index(cur_stat)
        sel_status = st.selectbox("Status", options=status_choices, index=cur_stat_idx, key=f"f_stat_{view_mode}")

    with f_col2:
        all_cats = sorted(list(set(raw_df["facility_type"].dropna().unique()) | set(raw_df.get("category", pd.Series(dtype=object)).dropna().unique())))
        cat_choices = ["All Categories"] + [c for c in all_cats if str(c).strip()]
        if st.session_state.get(f"f_cat_{view_mode}") not in cat_choices:
            st.session_state[f"f_cat_{view_mode}"] = "All Categories"
        cur_cat = st.session_state[f"f_cat_{view_mode}"]
        cur_cat_idx = cat_choices.index(cur_cat)
        sel_cat = st.selectbox("Category", options=cat_choices, index=cur_cat_idx, key=f"f_cat_{view_mode}")

    with f_col3:
        all_locs = sorted(list(set(raw_df["building"].dropna().unique()) | set(raw_df["location"].dropna().unique())))
        loc_choices = ["All Locations"] + [l for l in all_locs if str(l).strip()]
        if st.session_state.get(f"f_loc_{view_mode}") not in loc_choices:
            st.session_state[f"f_loc_{view_mode}"] = "All Locations"
        cur_loc = st.session_state[f"f_loc_{view_mode}"]
        cur_loc_idx = loc_choices.index(cur_loc)
        sel_loc = st.selectbox("Building / Location", options=loc_choices, index=cur_loc_idx, key=f"f_loc_{view_mode}")

    with f_col4:
        date_choices = ["All Dates", "Today", "Past 7 Days", "Past 30 Days"]
        if st.session_state.get(f"f_date_{view_mode}") not in date_choices:
            st.session_state[f"f_date_{view_mode}"] = "All Dates"
        cur_date = st.session_state[f"f_date_{view_mode}"]
        cur_date_idx = date_choices.index(cur_date)
        sel_date = st.selectbox("Submission Date", options=date_choices, index=cur_date_idx, key=f"f_date_{view_mode}")

    with f_col5:
        prio_choices = ["All Priorities", "Critical", "High", "Medium", "Low"]
        if st.session_state.get(f"f_prio_{view_mode}") not in prio_choices:
            st.session_state[f"f_prio_{view_mode}"] = "All Priorities"
        cur_prio = st.session_state[f"f_prio_{view_mode}"]
        cur_prio_idx = prio_choices.index(cur_prio)
        sel_prio = st.selectbox("MCPI Priority", options=prio_choices, index=cur_prio_idx, key=f"f_prio_{view_mode}")

    st.markdown("</div>", unsafe_allow_html=True)

    # 3. APPLY SEARCH, FILTERS & SORTING
    filtered_df = mode_df.copy()

    # Search: Complaint token, Student ID, Issue title
    if search_query.strip():
        q = search_query.strip().lower()
        m_tok = filtered_df["complaint_id"].fillna("").str.lower().str.contains(q, regex=False)
        m_title = filtered_df["title"].fillna("").str.lower().str.contains(q, regex=False)
        m_stu = filtered_df["student_id"].fillna("").str.lower().str.contains(q, regex=False)
        m_name = filtered_df["student_name"].fillna("").str.lower().str.contains(q, regex=False)
        m_desc = filtered_df["description"].fillna("").str.lower().str.contains(q, regex=False)
        filtered_df = filtered_df[m_tok | m_title | m_stu | m_name | m_desc]

    # Filters
    if sel_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["status"] == sel_status]

    if sel_cat != "All Categories":
        m_c1 = filtered_df["facility_type"] == sel_cat
        m_c2 = filtered_df.get("category", pd.Series(dtype=object)) == sel_cat
        filtered_df = filtered_df[m_c1 | m_c2]

    if sel_loc != "All Locations":
        m_bld = filtered_df["building"] == sel_loc
        m_loc = filtered_df["location"].fillna("").str.contains(sel_loc, regex=False)
        filtered_df = filtered_df[m_bld | m_loc]

    if sel_date != "All Dates" and "date_reported" in filtered_df.columns:
        dts = pd.to_datetime(filtered_df["date_reported"], errors="coerce")
        today = pd.Timestamp.now().normalize()
        if sel_date == "Today":
            filtered_df = filtered_df[dts.dt.normalize() == today]
        elif sel_date == "Past 7 Days":
            filtered_df = filtered_df[dts.dt.normalize() >= (today - pd.Timedelta(days=7))]
        elif sel_date == "Past 30 Days":
            filtered_df = filtered_df[dts.dt.normalize() >= (today - pd.Timedelta(days=30))]

    if sel_prio != "All Priorities" and "priority_tier" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["priority_tier"] == sel_prio]

    # Sorting
    if sort_by == "Newest first" and "date_reported" in filtered_df.columns:
        filtered_df = filtered_df.assign(_d_s=pd.to_datetime(filtered_df["date_reported"], errors="coerce")).sort_values(by="_d_s", ascending=False).drop(columns=["_d_s"])
    elif sort_by == "Oldest first" and "date_reported" in filtered_df.columns:
        filtered_df = filtered_df.assign(_d_s=pd.to_datetime(filtered_df["date_reported"], errors="coerce")).sort_values(by="_d_s", ascending=True).drop(columns=["_d_s"])
    elif sort_by == "Highest existing priority":
        if "priority_score" in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by="priority_score", ascending=False)
        elif "priority_tier" in filtered_df.columns:
            tier_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            filtered_df = filtered_df.assign(_t_s=filtered_df["priority_tier"].map(tier_order).fillna(0)).sort_values(by="_t_s", ascending=False).drop(columns=["_t_s"])

    # Selected complaint for Right-Side Details Panel
    selected_cid = st.session_state.get("admin_selected_complaint_id")
    selected_record = None
    if selected_cid and not raw_df.empty:
        matching = raw_df[raw_df["complaint_id"] == selected_cid]
        if not matching.empty:
            selected_record = matching.iloc[0].to_dict()
        else:
            st.session_state["admin_selected_complaint_id"] = None

    # Layout: Split view if a complaint row is selected
    if selected_record:
        col_table, col_details = st.columns([1.5, 1.0], gap="medium")
    else:
        col_table = st.container()
        col_details = None

    with col_table:
        # Results count & Export action
        c_meta_left, c_meta_right = st.columns([3, 1])
        with c_meta_left:
            mode_note = " <span style='font-size: 0.74rem; color: #6D8276;'>(Queue view · Details panel open)</span>" if selected_record else ""
            st.markdown(
                f"<div style='font-size: 0.84rem; font-weight: 600; color: #4A6357; padding: 0.35rem 0;'>"
                f"Showing <strong>{len(filtered_df)}</strong> of {len(mode_df)} requests{mode_note}"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c_meta_right:
            st.download_button(
                "Export CSV",
                data=filtered_df.to_csv(index=False),
                file_name=f"fipp_{view_mode}_requests.csv",
                mime="text/csv",
                type="secondary",
                use_container_width=True,
                key=f"dl_csv_{view_mode}",
            )

        # Useful Empty State
        if filtered_df.empty:
            empty_title = "No New or Unassigned Complaints" if mode_df.empty and view_mode == "new" else "No matching complaints found"
            empty_msg = (
                "All campus facility complaints have been reviewed and dispatched to maintenance squads. Newly submitted student queries will appear here automatically."
                if mode_df.empty and view_mode == "new"
                else "No submitted facility complaints match your active search query or filter criteria. Try resetting filters to view all records."
            )
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px dashed #A8B9A3; border-radius: 8px; padding: 2.25rem 1.5rem; text-align: center; margin: 1.25rem 0;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #203A32; margin-bottom: 0.35rem;">{empty_title}</div>
                    <div style="font-size: 0.85rem; color: #55685F; max-width: 460px; margin: 0 auto 1.25rem auto;">
                        {empty_msg}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c_empty_reset, _ = st.columns([1.5, 3])
            with c_empty_reset:
                st.button(
                    "Clear Filters",
                    key=f"btn_empty_reset_{view_mode}",
                    type="primary",
                    use_container_width=True,
                    on_click=reset_requests_filters,
                    args=(view_mode,),
                )
            return

        # Pagination: 10 complaints per page
        page_size = 10
        total_items = len(filtered_df)
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        cur_page = st.session_state.get(f"page_sel_{view_mode}", 1)
        if cur_page > total_pages:
            cur_page = 1
            st.session_state[f"page_sel_{view_mode}"] = 1

        if total_pages > 1:
            c_p1, c_p2 = st.columns([1.2, 3])
            with c_p1:
                page_num = st.selectbox(
                    "Page",
                    options=list(range(1, total_pages + 1)),
                    index=cur_page - 1,
                    key=f"page_sel_{view_mode}",
                )
            start_idx = (page_num - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            page_df = filtered_df.iloc[start_idx:end_idx]
            with c_p2:
                st.markdown(
                    f"<div style='font-size: 0.8rem; color: #6D8276; padding: 0.6rem 0;'>"
                    f"Showing complaints {start_idx + 1}–{end_idx} of {total_items}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            page_df = filtered_df

        # 4. COMPLAINT TABLE: Clean, readable enterprise table (not wrapped in oversized cards)
        if selected_record:
            # Master-detail split view: Core columns fit cleanly without text truncation or button clipping
            col_widths = [1.15, 2.3, 1.2, 0.95, 1.4]
            headers = [
                ("TOKEN", "left"),
                ("ISSUE", "left"),
                ("STATUS", "left"),
                ("PRIORITY", "left"),
                ("ACTION", "right"),
            ]
        else:
            # Full table view: All requested columns displayed with balanced widths
            col_widths = [1.1, 2.35, 0.95, 1.15, 1.15, 0.95, 1.05, 0.85, 1.0]
            headers = [
                ("TOKEN", "left"),
                ("ISSUE", "left"),
                ("STUDENT ID", "left"),
                ("CATEGORY", "left"),
                ("LOCATION", "left"),
                ("SUBMITTED", "left"),
                ("STATUS", "left"),
                ("PRIORITY", "left"),
                ("ACTION", "right"),
            ]

        # Table Header
        h_cols = st.columns(col_widths)
        for idx, (head_text, align) in enumerate(headers):
            h_cols[idx].markdown(
                f"<div class='fipp-th-text' style='text-align: {align}; padding: 0.35rem 0;'>{head_text}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='border-bottom: 2px solid #DCE5D8; margin-bottom: 0.3rem;'></div>", unsafe_allow_html=True)

        # Table Rows
        for _, row in page_df.iterrows():
            cid = str(row["complaint_id"])
            title = str(row.get("title") or "—")
            stu_id = str(row.get("student_id") or "—")
            cat = str(row.get("facility_type") or row.get("category") or "—")
            loc = str(row.get("building") or row.get("location") or "—")
            dt = row.get("date_reported") or "—"

            # Clean date formatting
            if dt != "—":
                try:
                    dt = pd.to_datetime(dt).strftime("%d %b %Y")
                except Exception:
                    dt = str(dt)[:10]

            status = row.get("status", "Submitted")
            s_badge = get_status_badge(status)

            prio = row.get("priority_tier")
            p_badge = get_priority_badge(prio) if prio else "<span style='color: #8A9E93; font-size: 0.8rem;'>—</span>"

            is_active = (cid == selected_cid)

            r_cols = st.columns(col_widths)

            if selected_record:
                # 5-column master view for split pane
                with r_cols[0]:
                    st.markdown(
                        f"<div class='fipp-cell-token' style='padding: 0.4rem 0;'>{cid}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[1]:
                    st.markdown(
                        f"<div class='fipp-cell-title' style='padding: 0.4rem 0;' title='{title}'>{title}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[2]:
                    st.markdown(
                        f"<div style='padding: 0.3rem 0;'>{s_badge}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[3]:
                    st.markdown(
                        f"<div style='padding: 0.3rem 0;'>{p_badge}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[4]:
                    btn_label = "Viewing" if is_active else "Inspect"
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(btn_label, key=f"btn_inspect_{view_mode}_{cid}", type=btn_type, use_container_width=True):
                        if is_active:
                            st.session_state["admin_selected_complaint_id"] = None
                        else:
                            st.session_state["admin_selected_complaint_id"] = cid
                        st.rerun()
            else:
                # Complete 9-column enterprise view for full table
                with r_cols[0]:
                    st.markdown(
                        f"<div class='fipp-cell-token' style='padding: 0.4rem 0;'>{cid}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[1]:
                    st.markdown(
                        f"<div class='fipp-cell-title' style='padding: 0.4rem 0;' title='{title}'>{title}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[2]:
                    st.markdown(
                        f"<div style='font-family: monospace; font-size: 0.78rem; color: #55685F; padding: 0.4rem 0; white-space: nowrap;'>{stu_id}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[3]:
                    st.markdown(
                        f"<div class='fipp-cell-muted' style='padding: 0.4rem 0;' title='{cat}'>{cat}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[4]:
                    st.markdown(
                        f"<div class='fipp-cell-muted' style='padding: 0.4rem 0;' title='{loc}'>{loc}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[5]:
                    st.markdown(
                        f"<div class='fipp-cell-date' style='padding: 0.4rem 0;'>{dt}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[6]:
                    st.markdown(
                        f"<div style='padding: 0.3rem 0;'>{s_badge}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[7]:
                    st.markdown(
                        f"<div style='padding: 0.3rem 0;'>{p_badge}</div>",
                        unsafe_allow_html=True,
                    )
                with r_cols[8]:
                    btn_label = "Viewing" if is_active else "Inspect"
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(btn_label, key=f"btn_inspect_{view_mode}_{cid}", type=btn_type, use_container_width=True):
                        if is_active:
                            st.session_state["admin_selected_complaint_id"] = None
                        else:
                            st.session_state["admin_selected_complaint_id"] = cid
                        st.rerun()

            # Subtle row separator
            sep_border = "2px solid #203A32" if is_active else "1px solid #EDF2EB"
            st.markdown(f"<div style='border-bottom: {sep_border}; margin: 0 0 0.15rem 0;'></div>", unsafe_allow_html=True)

    # 5. RIGHT-SIDE COMPLAINT DETAILS PANEL
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
