"""
Admin Complaint Management Page.
Provides data ingestion, complete ticket registry, status lifecycle management, and technician dispatch actions.
Displays all student complaints with Student ID, Student Name, ML predictions, and status controls.
"""
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from dashboard.components.styles import get_priority_badge, get_status_badge, _clean_html
from dashboard.components.empty_state import render_empty_state
from src.data.complaints_store import (
    get_complaints_df,
    add_complaint,
    update_complaint_status,
)
from src.prediction.priority_scoring import get_current_weights, calculate_priority_score

PROGRESS_STAGES = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved"]


def render_page() -> None:
    """Renders the Admin Complaint Management view."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <h1 style="margin: 0; font-size: 1.75rem; color: #1A1A1A; font-weight: 700;">
                📋 Campus Complaint Management & Dispatch
            </h1>
            <p style="margin: 0.2rem 0 0 0; color: #555555; font-size: 0.92rem;">
                Unified management of student-submitted issues, external dataset ingestion, and operational ticket lifecycles.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_register, tab_new, tab_upload = st.tabs(
        ["🗂️ Unified Complaint Register", "➕ Admin Ticket Intake", "📥 Dataset Ingestion (CSV)"]
    )

    # =========================================================================
    # TAB 1: UNIFIED COMPLAINT REGISTER
    # =========================================================================
    with tab_register:
        df = get_complaints_df()

        if df.empty:
            render_empty_state(
                title="Complaint Register Empty",
                subtitle="No facility tickets are currently recorded in the active store.",
                description="Student-submitted issues or imported logs will appear here automatically.",
                icon="📭",
                badge_label="Status: Empty",
            )
        else:
            # Search & Filter Bar
            c_s1, c_s2, c_s3, c_s4 = st.columns([2, 1, 1, 1])
            with c_s1:
                q = st.text_input(
                    "Search issues by keyword",
                    placeholder="Filter by title, description, or room...",
                    label_visibility="collapsed",
                )
            with c_s2:
                facs = ["All Categories"] + sorted(list(df["facility_type"].dropna().unique()))
                sel_fac = st.selectbox("Category", options=facs, label_visibility="collapsed")
            with c_s3:
                sevs = ["All Severities", "Critical", "High", "Medium", "Low"]
                sel_sev = st.selectbox("Severity", options=sevs, label_visibility="collapsed")
            with c_s4:
                stats = ["All Statuses"] + PROGRESS_STAGES
                sel_stat = st.selectbox("Status", options=stats, label_visibility="collapsed")

            view_df = df.copy()
            if sel_fac != "All Categories":
                view_df = view_df[view_df["facility_type"] == sel_fac]
            if sel_sev != "All Severities":
                view_df = view_df[view_df["severity"] == sel_sev]
            if sel_stat != "All Statuses":
                view_df = view_df[view_df["status"] == sel_stat]
            if q.strip():
                query = q.strip().lower()
                view_df = view_df[
                    view_df["title"].str.lower().str.contains(query, na=False)
                    | view_df["description"].str.lower().str.contains(query, na=False)
                    | view_df["location"].str.lower().str.contains(query, na=False)
                    | view_df["complaint_id"].str.lower().str.contains(query, na=False)
                    | view_df["reported_by"].fillna("").str.lower().str.contains(query, na=False)
                    | view_df["student_id"].fillna("").str.lower().str.contains(query, na=False)
                    | view_df["student_name"].fillna("").str.lower().str.contains(query, na=False)
                ]

            st.markdown(f"**Showing {len(view_df)} tickets** in active university register (including Student submissions):")

            # Render styled complaint rows
            for _, r in view_df.iterrows():
                cid = r["complaint_id"]
                p_badge = get_priority_badge(r.get("priority_tier", "Medium"))
                curr_status = r.get("status", "Submitted")
                s_badge = get_status_badge(curr_status)
                title = r.get("title", "Issue")
                desc = r.get("description", "")
                loc = r.get("location", "Campus")
                fac = r.get("facility_type", "General")
                sev = r.get("severity", "Medium")
                dt = r.get("date_reported", "")
                est = r.get("estimated_resolution", "Pending")
                score = r.get("priority_score", 0.0)

                stu_id = r.get("student_id")
                stu_name = r.get("student_name")
                reported_by = r.get("reported_by", "Staff")

                if stu_id:
                    reporter_badge = f'<span style="background-color: #EAE3D2; color: #1A1A1A; border: 1px solid #D8CFBD; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">🎓 Student: {stu_name or "Student"} ({stu_id})</span>'
                else:
                    reporter_badge = f'<span style="background-color: #F6F3EB; color: #2D2D2D; border: 1px solid #EAE3D2; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">👤 {reported_by}</span>'

                action_text = r.get("action_taken", "Under review by maintenance dispatcher.")

                st.markdown(
                    _clean_html(
                        f"""
                        <div class="dashboard-card" style="margin-bottom: 0.85rem; padding: 1.1rem 1.3rem; border: 1px solid #EAE3D2;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                                <div>
                                    <span style="font-family: monospace; font-size: 0.8rem; font-weight: 700; color: #1A1A1A; background-color: #EAE3D2; padding: 0.15rem 0.45rem; border-radius: 4px; border: 1px solid #D8CFBD;">
                                        {cid}
                                    </span>
                                    <span style="font-size: 0.75rem; font-weight: 600; color: #1A1A1A; background-color: #F6F3EB; padding: 0.15rem 0.45rem; border-radius: 4px; margin-left: 0.35rem; border: 1px solid #EAE3D2;">
                                        {fac}
                                    </span>
                                    <span style="margin-left: 0.4rem;">
                                        {reporter_badge}
                                    </span>
                                    <h4 style="margin: 0.35rem 0 0.2rem 0; color: #1A1A1A; font-size: 1.08rem; font-weight: 700;">{title}</h4>
                                </div>
                                <div style="display: flex; align-items: center; gap: 0.6rem;">
                                    <span style="font-size: 0.78rem; color: #555555;">Severity: <strong>{sev}</strong></span>
                                    <span style="font-size: 0.78rem; color: #555555;">Score: <strong>{score}</strong></span>
                                    {p_badge}
                                    {s_badge}
                                </div>
                            </div>
                            <p style="color: #2D2D2D; font-size: 0.88rem; margin: 0.4rem 0 0.6rem 0; line-height: 1.5;">{desc}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #555555; border-top: 1px solid #EAE3D2; padding-top: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                                <span>📍 <strong>Location:</strong> {loc} • Reported: {dt}</span>
                                <span>⏱️ <strong>Est. SLA:</strong> <span style="color: #1A1A1A; font-weight: 600;">{est}</span></span>
                            </div>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

                # Admin Lifecycle & Status Management Controls
                with st.expander(f"⚙️ Manage Status & Maintenance Dispatch for {cid}", expanded=False):
                    m_c1, m_c2, m_c3 = st.columns([1.5, 2.5, 1])
                    with m_c1:
                        curr_idx = PROGRESS_STAGES.index(curr_status) if curr_status in PROGRESS_STAGES else 0
                        new_stat = st.selectbox(
                            "Update Status",
                            options=PROGRESS_STAGES,
                            index=curr_idx,
                            key=f"stat_sel_{cid}",
                        )
                    with m_c2:
                        new_action = st.text_input(
                            "Technician Action / Log",
                            value=action_text,
                            key=f"act_input_{cid}",
                        )
                    with m_c3:
                        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
                        if st.button("Save Update", key=f"save_stat_{cid}", type="primary", use_container_width=True):
                            update_complaint_status(cid, new_stat, action_taken=new_action)
                            st.success(f"Ticket {cid} updated to **{new_stat}**!")
                            st.rerun()

    # =========================================================================
    # TAB 2: MANUAL INCIDENT REGISTRATION (ADMIN)
    # =========================================================================
    with tab_new:
        st.markdown("### ➕ Admin Incident Intake Form")
        st.markdown("Register maintenance tickets logged via phone, campus patrol, or physical inspection.")

        with st.form("form_admin_new_complaint", clear_on_submit=True):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                new_title = st.text_input("Issue Headline / Summary", placeholder="e.g., Short circuit in Physics Lab 201")
                new_facility = st.selectbox(
                    "Facility Subsystem",
                    ["Electrical or lighting issues", "Plumbing", "HVAC", "Water cooler or water supply", "Washroom cleanliness", "Garbage overflow", "Other maintenance issues"],
                )
                new_loc = st.text_input("Specific Location", placeholder="e.g., Academic Block 2 - Room 201")
            with col_t2:
                new_loc_type = st.selectbox(
                    "Zone Criticality",
                    ["Computer Lab", "Chemistry Lab", "Server Room", "Lecture Hall", "Hostel Washroom", "Hostel Room", "Central Library", "Corridor / Common Area"],
                )
                new_severity = st.selectbox("Reported Severity", ["Low", "Medium", "High", "Critical"])
                new_reporter = st.text_input("Reported By", placeholder="e.g., Facility Inspector / Campus Engineer")

            new_desc = st.text_area(
                "Detailed Description",
                placeholder="Provide physical symptoms, affected students, sparking, water leaks, or potential safety hazards...",
            )

            col_sub1, _ = st.columns([1.5, 3])
            with col_sub1:
                submitted = st.form_submit_button("Submit Admin Ticket", type="primary", use_container_width=True)

            if submitted:
                if not new_title.strip() or not new_desc.strip():
                    st.error("Please provide both an issue headline and a detailed description.")
                else:
                    new_rec = {
                        "title": new_title.strip(),
                        "description": new_desc.strip(),
                        "facility_type": new_facility,
                        "location": new_loc.strip() if new_loc.strip() else "Campus",
                        "location_type": new_loc_type,
                        "severity": new_severity,
                        "recurrence_risk": 0.45 if new_severity in ["Critical", "High"] else 0.20,
                        "impact_scale": 0.80 if "Lab" in new_loc_type or "Server" in new_loc_type else 0.45,
                        "is_recurring": False,
                        "recurrence_count": 0,
                        "status": "Submitted",
                        "reported_by": new_reporter.strip() if new_reporter.strip() else "Facility Staff",
                        "estimated_resolution": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                        "action_taken": "Logged into active triage queue.",
                    }
                    new_id = add_complaint(new_rec)
                    st.success(f"Admin complaint registered successfully! Assigned Ticket ID: **{new_id}**")
                    st.rerun()

    # =========================================================================
    # TAB 3: DATA INGESTION & CSV IMPORT
    # =========================================================================
    with tab_upload:
        st.markdown("### 📥 University Facility Records Ingestion")
        st.markdown(
            "Upload official university maintenance logs (CSV / Excel format) to append bulk records into the operational repository."
        )

        uploaded_file = st.file_uploader("Upload complaint dataset (CSV format)", type=["csv"])
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                st.write("Uploaded dataset preview:", uploaded_df.head(3))
                if st.button("Append Dataset to Campus Repository", type="primary"):
                    records_to_add = uploaded_df.to_dict(orient="records")
                    for rec in records_to_add:
                        if "title" not in rec and "description" in rec:
                            rec["title"] = str(rec["description"])[:40]
                        add_complaint(rec)
                    st.success(f"Appended {len(records_to_add)} records to the active repository.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing uploaded file: {e}")
