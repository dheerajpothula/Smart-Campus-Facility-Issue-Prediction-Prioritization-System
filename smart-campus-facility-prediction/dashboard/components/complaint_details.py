"""
Right-Side Complaint Details Panel Component for FIPP Administrator Control Centre.
Displays comprehensive complaint, student, MCPI prediction, administrative remarks,
and lifecycle management actions in a persistent side panel without navigating away from request tables.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from dashboard.components.styles import get_priority_badge, get_status_badge, _clean_html
from src.data.complaints_store import (
    PROGRESS_STAGES,
    update_complaint_status_extended,
    reopen_complaint,
    assign_complaint_staff,
)

MAINTENANCE_SQUADS = [
    "Unassigned",
    "Hostel Maintenance Unit",
    "Electrical Maintenance Squad",
    "Plumbing Response Team",
    "HVAC & Cooling Systems Unit",
    "Civil Infrastructure Team",
    "Sanitation & Housekeeping Squad",
    "Carpentry & Furniture Repairs",
    "IT & Network Operations Desk",
]


def render_complaint_details_panel(complaint_record: dict | None) -> None:
    """
    Renders the Right-Side Complaint Details Panel.

    Args:
        complaint_record: The complaint ticket dictionary to display.
    """
    if not complaint_record:
        st.info("Select any complaint from the list to view its complete operational profile.")
        return

    cid = complaint_record.get("complaint_id", "CMP-2026-000")
    curr_status = complaint_record.get("status", "Submitted")
    status_badge = get_status_badge(curr_status)
    priority_tier = complaint_record.get("priority_tier", "Medium")
    priority_score = complaint_record.get("priority_score", 0.0)
    prio_badge = get_priority_badge(priority_tier)

    # Panel Container with Modern Sage & Forest styling
    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #DCE5D8;
            border-top: 4px solid #203A32;
            border-radius: 12px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(32, 58, 50, 0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #DCE5D8; padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <div>
                    <span style="
                        font-family: monospace;
                        font-size: 0.88rem;
                        font-weight: 800;
                        color: #203A32;
                        background: #DCE5D8;
                        padding: 0.2rem 0.55rem;
                        border-radius: 4px;
                        border: 1px solid #A8B9A3;
                    ">{cid}</span>
                    <span style="font-size: 0.76rem; color: #4A6357; font-weight: 600; margin-left: 0.4rem;">
                        Inspection Panel
                    </span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.4rem;">
                    {prio_badge}
                    {status_badge}
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Close button
    c_close_col, _ = st.columns([1, 2])
    with c_close_col:
        if st.button("✕ Close Panel", key=f"btn_close_panel_{cid}", type="secondary", use_container_width=True):
            st.session_state["admin_selected_complaint_id"] = None
            st.rerun()

    # 1. STUDENT INFORMATION SECTION
    stu_name = complaint_record.get("student_name") or complaint_record.get("reported_by") or "Campus Reporter"
    stu_id = complaint_record.get("student_id") or "Staff / Internal Log"
    contact_no = complaint_record.get("contact_number") or complaint_record.get("mobile_number") or "Not provided"

    st.markdown(
        f"""
        <div style="background: #F5F7F2; border: 1px solid #DCE5D8; border-radius: 8px; padding: 0.85rem 1rem; margin: 0.9rem 0;">
            <div style="font-size: 0.74rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #203A32; margin-bottom: 0.4rem;">
                👤 Student / Reporter Information
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; font-size: 0.84rem;">
                <div><span style="color: #6D8276;">Name:</span> <strong>{stu_name}</strong></div>
                <div><span style="color: #6D8276;">Student ID:</span> <code>{stu_id}</code></div>
                <div><span style="color: #6D8276;">Contact No:</span> <strong>{contact_no}</strong></div>
                <div><span style="color: #6D8276;">Reported By:</span> {complaint_record.get("reported_by", "Student Portal")}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. COMPLAINT INFORMATION SECTION
    title = complaint_record.get("title", "Facility Issue")
    msg_type = complaint_record.get("message_type", "Complaint / Query")
    cat = complaint_record.get("category") or complaint_record.get("facility_type", "General")
    sub_cat = complaint_record.get("sub_category", "Standard")
    spec_cat = complaint_record.get("specific_category") or "General Issue"
    bld = complaint_record.get("building") or complaint_record.get("block", "Campus Grounds")
    loc = complaint_record.get("location", "Campus")
    spec_loc = complaint_record.get("specific_location") or "Specified area"
    desc = complaint_record.get("description", "No description provided.")
    supp_doc = complaint_record.get("supporting_document") or "None submitted"
    dt_rep = complaint_record.get("date_reported", "Recently")

    st.markdown(
        f"""
        <div style="margin-bottom: 0.85rem;">
            <div style="font-size: 0.74rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #203A32; margin-bottom: 0.35rem;">
                📋 Complaint Details
            </div>
            <h4 style="margin: 0 0 0.45rem 0; font-size: 1.05rem; color: #203A32; font-weight: 700;">{title}</h4>
            <div style="font-size: 0.83rem; color: #4A6357; line-height: 1.5; margin-bottom: 0.6rem; background: #FFFFFF; border: 1px solid #DCE5D8; border-left: 3px solid #A8B9A3; border-radius: 6px; padding: 0.65rem 0.85rem;">
                <strong>Description:</strong><br/>{desc}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem; font-size: 0.82rem; color: #203A32;">
                <div><span style="color: #6D8276;">Message Type:</span> <strong>{msg_type}</strong></div>
                <div><span style="color: #6D8276;">Category:</span> <strong>{cat}</strong></div>
                <div><span style="color: #6D8276;">Subcategory:</span> {sub_cat}</div>
                <div><span style="color: #6D8276;">Specific Type:</span> {spec_cat}</div>
                <div><span style="color: #6D8276;">Building / Block:</span> <strong>{bld}</strong></div>
                <div><span style="color: #6D8276;">Location:</span> {loc}</div>
                <div><span style="color: #6D8276;">Submission Date:</span> {dt_rep}</div>
                <div><span style="color: #6D8276;">Attachment:</span> 📎 {supp_doc}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. MCPI PREDICTION INFORMATION
    sev = complaint_record.get("severity", "Medium")
    loc_type = complaint_record.get("location_type", "Standard Facility")
    rec_risk = complaint_record.get("recurrence_risk", 0.3)
    imp_scale = complaint_record.get("impact_scale", 0.5)
    rec_count = complaint_record.get("recurrence_count", 0)

    st.markdown(
        f"""
        <div style="background: #F0F4ED; border: 1px solid #DCE5D8; border-radius: 8px; padding: 0.85rem 1rem; margin: 0.9rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                <span style="font-size: 0.74rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #203A32;">
                    ⚡ MCPI Priority &amp; Heuristics
                </span>
                <span style="font-size: 0.78rem; font-weight: 700; color: #203A32;">
                    Score: {priority_score} / 100
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem; font-size: 0.82rem; color: #203A32;">
                <div><span style="color: #6D8276;">Severity:</span> <strong>{sev}</strong></div>
                <div><span style="color: #6D8276;">Location Criticality:</span> {loc_type}</div>
                <div><span style="color: #6D8276;">Recurrence Risk:</span> {int(rec_risk * 100)}% ({rec_count} previous)</div>
                <div><span style="color: #6D8276;">Impact Scale:</span> {int(imp_scale * 100)}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. ADMINISTRATIVE & ASSIGNMENT STATUS
    staff_member = complaint_record.get("allotted_person") or "Unassigned"
    action_taken = complaint_record.get("action_taken") or "No operational remarks recorded."
    closing_remarks = complaint_record.get("closing_remarks")

    st.markdown(
        f"""
        <div style="margin-bottom: 0.85rem;">
            <div style="font-size: 0.74rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #203A32; margin-bottom: 0.35rem;">
                ⚙️ Administrative Status
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem; font-size: 0.82rem; color: #203A32; margin-bottom: 0.5rem;">
                <div><span style="color: #6D8276;">Current Status:</span> <strong>{curr_status}</strong></div>
                <div><span style="color: #6D8276;">Assigned Staff:</span> <strong>{staff_member}</strong></div>
            </div>
            <div style="font-size: 0.82rem; background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.55rem 0.75rem; color: #203A32;">
                <strong>Latest Operational Remarks:</strong><br/>{action_taken}
            </div>
            {f'<div style="font-size: 0.82rem; margin-top: 0.4rem; background: #DCE5D8; border-radius: 6px; padding: 0.45rem 0.65rem; color: #203A32;"><strong>Resolution Notes:</strong> {closing_remarks}</div>' if closing_remarks else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 5. STATUS HISTORY
    history_list = complaint_record.get("remarks_history") or []
    if history_list:
        with st.expander(f"📜 Status & Remarks History ({len(history_list)})", expanded=False):
            for h in history_list:
                h_date = h.get("update_date", "")
                h_name = h.get("name", "System")
                h_rem = h.get("remarks", "")
                st.markdown(
                    f"""
                    <div style="border-left: 2px solid #A8B9A3; padding-left: 0.6rem; margin-bottom: 0.6rem; font-size: 0.79rem;">
                        <div style="color: #4A6357; font-weight: 600;">{h_date} &bull; {h_name}</div>
                        <div style="color: #203A32;">{h_rem}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<hr style='margin: 0.9rem 0; border: none; border-top: 1px solid #DCE5D8;'/>", unsafe_allow_html=True)

    # 6. ADMINISTRATIVE ACTIONS FORM
    st.markdown(
        "<div style='font-size: 0.88rem; font-weight: 750; color: #203A32; margin-bottom: 0.4rem;'>🛠️ Operational Actions</div>",
        unsafe_allow_html=True,
    )

    auth = st.session_state.get("auth_user") or {}
    admin_id = auth.get("id", "ADM-2026-001")
    admin_title = auth.get("title") or auth.get("role_title", "Facility Operations Lead")

    # If ticket is currently Resolved, offer Reopen Action
    if curr_status == "Resolved":
        st.info("This ticket is currently marked as **Resolved**. You may reopen it with an explanation.")
        reopen_reason = st.text_input(
            "Reopening Justification (Mandatory)",
            placeholder="e.g. Issue recurred, repairs incomplete...",
            key=f"input_reopen_reason_{cid}",
        )
        if st.button("🔄 Reopen Complaint", key=f"btn_reopen_{cid}", type="primary", use_container_width=True):
            if not reopen_reason.strip():
                st.error("Please provide a justification to reopen this complaint.")
            else:
                ok = reopen_complaint(
                    complaint_id=cid,
                    remarks=reopen_reason.strip(),
                    admin_id=admin_id,
                    admin_title=admin_title,
                )
                if ok:
                    st.success(f"Complaint {cid} has been reopened to 'Under Review'.")
                    st.rerun()
                else:
                    st.error("Failed to reopen complaint.")
        return

    # Normal Lifecycle Actions
    curr_stage_idx = PROGRESS_STAGES.index(curr_status) if curr_status in PROGRESS_STAGES else 0

    new_status = st.selectbox(
        "Update Complaint Status",
        options=PROGRESS_STAGES,
        index=curr_stage_idx,
        key=f"panel_status_sel_{cid}",
    )

    # Assigned staff selection
    current_staff_idx = 0
    if staff_member in MAINTENANCE_SQUADS:
        current_staff_idx = MAINTENANCE_SQUADS.index(staff_member)

    assigned_staff = st.selectbox(
        "Assign Maintenance Squad / Technician",
        options=MAINTENANCE_SQUADS,
        index=current_staff_idx,
        key=f"panel_staff_sel_{cid}",
    )

    admin_remarks = st.text_area(
        "Administrative Remarks / Dispatch Log",
        value="" if curr_status == new_status else f"Status transition to {new_status}.",
        placeholder="Enter technical observations, repair schedule, or completion notes...",
        height=85,
        key=f"panel_remarks_{cid}",
    )

    is_resolving = (new_status == "Resolved")
    if is_resolving:
        st.warning("⚠️ Marking as **Resolved** requires clear resolution remarks explaining the work completed.")

    if st.button("💾 Save Operational Update", key=f"btn_save_panel_{cid}", type="primary", use_container_width=True):
        if is_resolving and not admin_remarks.strip():
            st.error("Resolution remarks are mandatory when marking a ticket as Resolved.")
        else:
            final_staff = assigned_staff if assigned_staff != "Unassigned" else None
            ok = update_complaint_status_extended(
                complaint_id=cid,
                new_status=new_status,
                remarks=admin_remarks.strip() if admin_remarks.strip() else None,
                admin_id=admin_id,
                admin_title=admin_title,
                assigned_staff=final_staff,
            )
            if ok:
                st.success(f"Ticket {cid} updated to **{new_status}**!")
                st.rerun()
            else:
                st.error("Failed to update ticket.")
