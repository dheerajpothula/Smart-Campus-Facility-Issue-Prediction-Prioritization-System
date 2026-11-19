"""
Right-Side Complaint Details Panel Component for FIPP Administrator Control Centre.
Displays comprehensive complaint, student, MCPI prediction, administrative remarks,
and lifecycle management actions in a persistent side panel without navigating away from request tables.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from pathlib import Path
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
        st.info("Select any complaint from the table to view its operational details.")
        return

    cid = complaint_record.get("complaint_id", "CMP-2026-000")
    curr_status = complaint_record.get("status", "Submitted")
    status_badge = get_status_badge(curr_status)
    priority_tier = complaint_record.get("priority_tier", "Medium")
    priority_score = complaint_record.get("priority_score", 0.0)
    prio_badge = get_priority_badge(priority_tier) if priority_tier else "<span style='color: #8A9E93; font-size: 0.8rem;'>—</span>"

    # Header with Token and Close Action
    c_head_left, c_head_right = st.columns([3.2, 1.2])
    with c_head_left:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                <span style="
                    font-family: monospace;
                    font-size: 0.95rem;
                    font-weight: 800;
                    color: #203A32;
                    background: #DCE5D8;
                    padding: 0.2rem 0.55rem;
                    border-radius: 4px;
                    border: 1px solid #A8B9A3;
                ">{cid}</span>
                {status_badge}
                {prio_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_head_right:
        if st.button("✕ Close", key=f"btn_close_panel_{cid}", type="secondary", use_container_width=True):
            st.session_state["admin_selected_complaint_id"] = None
            st.rerun()

    # Panel Container with Modern Sage & Forest styling
    st.markdown(
        """
        <div style="border-top: 2px solid #DCE5D8; margin-bottom: 0.75rem;"></div>
        """,
        unsafe_allow_html=True,
    )

    # A. COMPLAINT INFORMATION SECTION
    title = complaint_record.get("title") or "—"
    cat = complaint_record.get("facility_type") or complaint_record.get("category") or "—"
    sub_cat = complaint_record.get("sub_category") or "—"
    spec_cat = complaint_record.get("specific_category") or "—"
    bld = complaint_record.get("building") or complaint_record.get("block") or "—"
    floor = complaint_record.get("floor") or "—"
    room_area = complaint_record.get("room_no") or complaint_record.get("specific_location") or complaint_record.get("location") or "—"
    desc = complaint_record.get("description") or "No description provided."
    dt_rep = complaint_record.get("date_reported") or "—"

    st.markdown(
        f"""
        <div style="margin-bottom: 0.85rem;">
            <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F; margin-bottom: 0.3rem;">
                Complaint Details
            </div>
            <div style="font-size: 1.05rem; color: #203A32; font-weight: 700; margin-bottom: 0.4rem; line-height: 1.35;">
                {title}
            </div>
            <div style="font-size: 0.83rem; color: #324E43; line-height: 1.5; margin-bottom: 0.6rem; background: #FFFFFF; border: 1px solid #DCE5D8; border-left: 3px solid #203A32; border-radius: 6px; padding: 0.65rem 0.85rem;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #55685F; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.2rem;">Full Description</div>
                {desc}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem 0.65rem; font-size: 0.82rem; color: #203A32; background: #F8FAF7; border: 1px solid #EDF2EB; border-radius: 6px; padding: 0.6rem 0.75rem;">
                <div><span style="color: #6D8276;">Token:</span> <strong>{cid}</strong></div>
                <div><span style="color: #6D8276;">Category:</span> <strong>{cat}</strong></div>
                <div><span style="color: #6D8276;">Subcategory:</span> {sub_cat}</div>
                <div><span style="color: #6D8276;">Specific Type:</span> {spec_cat}</div>
                <div><span style="color: #6D8276;">Building / Block:</span> <strong>{bld}</strong></div>
                <div><span style="color: #6D8276;">Floor:</span> {floor}</div>
                <div><span style="color: #6D8276;">Room / Area:</span> <strong>{room_area}</strong></div>
                <div><span style="color: #6D8276;">Submitted:</span> {dt_rep}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # B. STUDENT INFORMATION SECTION
    stu_name = complaint_record.get("student_name") or complaint_record.get("reported_by") or "—"
    stu_id = complaint_record.get("student_id") or "—"
    raw_contact = complaint_record.get("contact_number") or complaint_record.get("mobile_number")
    if raw_contact and str(raw_contact).strip() and str(raw_contact).strip() not in ["Not provided", "None", "nan", "—"]:
        contact_no = str(raw_contact).strip()
    else:
        contact_no = "—"

    st.markdown(
        f"""
        <div style="margin-bottom: 0.85rem;">
            <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F; margin-bottom: 0.3rem;">
                Student Details
            </div>
            <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.6rem 0.75rem; font-size: 0.82rem; display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem 0.65rem;">
                <div><span style="color: #6D8276;">Student Name:</span> <strong>{stu_name}</strong></div>
                <div><span style="color: #6D8276;">Student ID:</span> <code>{stu_id}</code></div>
                <div><span style="color: #6D8276;">Contact No:</span> <strong>{contact_no}</strong></div>
                <div><span style="color: #6D8276;">Reporter:</span> {complaint_record.get("reported_by", "Student Portal")}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # C. COMPLAINT STATUS & MCPI PRIORITY
    staff_member = complaint_record.get("allotted_person") or "Unassigned"
    sev = complaint_record.get("severity") or "—"
    loc_type = complaint_record.get("location_type") or "Standard Facility"
    rec_risk = complaint_record.get("recurrence_risk", 0.0)
    imp_scale = complaint_record.get("impact_scale", 0.0)

    st.markdown(
        f"""
        <div style="margin-bottom: 0.85rem;">
            <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F; margin-bottom: 0.3rem;">
                Administrative Information
            </div>
            <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.6rem 0.75rem; font-size: 0.82rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem 0.65rem; margin-bottom: 0.4rem;">
                    <div><span style="color: #6D8276;">Current Status:</span> <strong>{curr_status}</strong></div>
                    <div><span style="color: #6D8276;">Assigned Squad:</span> <strong>{staff_member}</strong></div>
                    <div><span style="color: #6D8276;">Priority Tier:</span> <strong>{priority_tier or '—'}</strong></div>
                    <div><span style="color: #6D8276;">MCPI Score:</span> <strong>{priority_score} / 100</strong></div>
                </div>
                <div style="border-top: 1px solid #EDF2EB; padding-top: 0.35rem; font-size: 0.76rem; color: #55685F; display: flex; gap: 0.75rem; flex-wrap: wrap;">
                    <span>Severity: <strong>{sev}</strong></span>
                    <span>Location Criticality: <strong>{loc_type}</strong></span>
                    <span>Recurrence Risk: <strong>{int(rec_risk * 100)}%</strong></span>
                    <span>Impact Scale: <strong>{int(imp_scale * 100)}%</strong></span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # D. ATTACHMENTS
    supp_doc = complaint_record.get("supporting_document")
    has_attachment = False
    attachment_name = None
    attachment_path = None

    if supp_doc and str(supp_doc).strip() not in ["", "None", "None submitted", "nan", "null"]:
        attachment_name = str(supp_doc).strip()
        candidate_paths = [
            Path(attachment_name),
            Path("data/uploads") / attachment_name,
            Path("data/processed") / attachment_name,
        ]
        attachment_path = next((p for p in candidate_paths if p.is_file()), None)
        has_attachment = True

    st.markdown(
        """
        <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F; margin-bottom: 0.3rem;">
            D. Attachments
        </div>
        """,
        unsafe_allow_html=True,
    )

    if has_attachment:
        if attachment_path:
            with open(attachment_path, "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label=f"Download Attachment ({attachment_path.name})",
                data=file_bytes,
                file_name=attachment_path.name,
                key=f"dl_attachment_{cid}",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: #F8FAF7; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.82rem; color: #203A32;">
                    Attached File Reference: <code>{attachment_name}</code>
                    <div style="font-size: 0.74rem; color: #6D8276; margin-top: 0.15rem;">(File record stored; file not present in local filesystem)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div style="background: #F8FAF7; border: 1px dashed #DCE5D8; border-radius: 6px; padding: 0.45rem 0.75rem; font-size: 0.8rem; color: #6D8276;">
                — No attachments submitted with this ticket.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # E. REMARKS AND STATUS HISTORY
    history_list = complaint_record.get("remarks_history") or []
    st.markdown(
        f"""
        <div style="margin-top: 0.85rem; margin-bottom: 0.3rem;">
            <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F;">
                Remarks &amp; History ({len(history_list)})
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if history_list:
        with st.expander(f"View Status History ({len(history_list)} entries)", expanded=False):
            for h in history_list:
                h_date = h.get("update_date", "Earlier")
                h_name = h.get("name", "System")
                h_rem = h.get("remarks", "")
                h_prev = h.get("previous_status")
                h_new = h.get("new_status")
                trans_text = f" &bull; {h_prev} → {h_new}" if h_prev and h_new else ""
                st.markdown(
                    f"""
                    <div style="border-left: 2px solid #A8B9A3; padding-left: 0.6rem; margin-bottom: 0.6rem; font-size: 0.79rem;">
                        <div style="color: #4A6357; font-weight: 600;">{h_date} &bull; {h_name}{trans_text}</div>
                        <div style="color: #203A32; margin-top: 0.15rem;">{h_rem}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        action_taken = complaint_record.get("action_taken") or "No operational remarks recorded."
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #DCE5D8; border-radius: 6px; padding: 0.45rem 0.65rem; font-size: 0.8rem; color: #4A6357;">
                {action_taken}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='border-top: 1px solid #DCE5D8; margin: 0.9rem 0 0.65rem 0;'></div>", unsafe_allow_html=True)

    # F. OPERATIONAL ACTIONS FORM
    st.markdown(
        """
        <div style="font-size: 0.72rem; font-weight: 750; text-transform: uppercase; letter-spacing: 0.05em; color: #55685F; margin-bottom: 0.35rem;">
            Operational Actions
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth = st.session_state.get("auth_user") or {}
    admin_id = auth.get("id", "ADM-2026-001")
    admin_title = auth.get("title") or auth.get("role_title", "Facility Operations Lead")

    # If ticket is currently Resolved, offer Reopen Action
    if curr_status == "Resolved":
        st.info("This ticket is currently marked as **Resolved**. You may reopen it with an operational justification.")
        reopen_reason = st.text_input(
            "Reopening Justification (Mandatory)",
            placeholder="e.g. Issue recurred, repairs incomplete...",
            key=f"input_reopen_reason_{cid}",
        )
        if st.button("Reopen Complaint", key=f"btn_reopen_{cid}", type="primary", use_container_width=True):
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
        height=80,
        key=f"panel_remarks_{cid}",
    )

    is_resolving = (new_status == "Resolved")
    if is_resolving:
        st.warning("Marking as **Resolved** requires clear resolution remarks explaining the work completed.")

    if st.button("Save Operational Update", key=f"btn_save_panel_{cid}", type="primary", use_container_width=True):
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
