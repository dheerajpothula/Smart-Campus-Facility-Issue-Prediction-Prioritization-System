"""
FIPP 2.0 — Student Portal API Routes.
Enforces strict server-side student data isolation:
A student can only submit complaints under their own identity, view their own tickets,
withdraw their pending queries, and submit resolution feedback.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import require_student
from app.models.data_models import (
    ComplaintDetail,
    FeedbackRequest,
    StudentComplaintCreate,
    StudentComplaintListResponse,
    WithdrawalRequest,
)
from app.services.complaint_service import complaint_service

router = APIRouter(prefix="/api/student", tags=["Student Portal"])


@router.post("/complaints/submit")
def submit_complaint(
    payload: StudentComplaintCreate,
    current_user: Dict[str, Any] = Depends(require_student),
):
    """
    Submits a new campus facility complaint for the authenticated student.
    Validates mandatory declarations, 10-digit phone, future availability date,
    and assigns a sequential canonical token (CMP-2026-XXX).
    """
    try:
        new_ticket = complaint_service.create_complaint(
            student_id=current_user["id"],
            student_name=current_user["name"],
            data=payload,
        )
        normalized = complaint_service.normalize_record(new_ticket)
        return {
            "success": True,
            "token": normalized["complaint_id"],
            "complaint": ComplaintDetail(**normalized),
            "message": f"Complaint {normalized['complaint_id']} has been registered successfully.",
        }
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist complaint submission safely.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process complaint submission: {str(exc)}",
        )


@router.get("/complaints", response_model=StudentComplaintListResponse)
def get_student_complaints(
    search: Optional[str] = Query(None, description="Search by ID, title, or keywords"),
    current_user: Dict[str, Any] = Depends(require_student),
):
    """
    Retrieves the complete complaint history belonging strictly to the authenticated student.
    """
    records = complaint_service.get_student_complaints(student_id=current_user["id"], search=search)
    normalized_list = [ComplaintDetail(**complaint_service.normalize_record(r)) for r in records]

    total = len(normalized_list)
    open_cnt = sum(1 for r in normalized_list if r.status not in ["Resolved", "Withdrawn"])
    closed_cnt = sum(1 for r in normalized_list if r.status in ["Resolved", "Withdrawn"])

    return StudentComplaintListResponse(
        student_id=current_user["id"],
        student_name=current_user["name"],
        total_complaints=total,
        open_complaints=open_cnt,
        closed_complaints=closed_cnt,
        records=normalized_list,
    )


@router.get("/complaints/{complaint_id}", response_model=ComplaintDetail)
def get_complaint_details(
    complaint_id: str,
    current_user: Dict[str, Any] = Depends(require_student),
):
    """
    Retrieves detailed information for a specific complaint.
    Enforces student ownership: Returns 404/403 if the record does not belong to the caller.
    """
    record = complaint_service.get_by_id(complaint_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' was not found.",
        )

    # Server-side isolation check
    if record.get("student_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this complaint record.",
        )

    normalized = complaint_service.normalize_record(record)
    return ComplaintDetail(**normalized)


@router.post("/complaints/{complaint_id}/withdraw")
def withdraw_complaint(
    complaint_id: str,
    payload: WithdrawalRequest,
    current_user: Dict[str, Any] = Depends(require_student),
):
    """
    Allows a student to withdraw an open query that has not yet been resolved.
    """
    try:
        success = complaint_service.withdraw_complaint(
            complaint_id=complaint_id,
            student_id=current_user["id"],
            reason=payload.reason,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist complaint withdrawal safely.",
        )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot withdraw complaint. Verify ownership and that the complaint is not already Resolved or Withdrawn.",
        )
    return {
        "success": True,
        "message": f"Complaint {complaint_id} has been withdrawn successfully.",
    }


@router.post("/complaints/{complaint_id}/feedback")
def submit_complaint_feedback(
    complaint_id: str,
    payload: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(require_student),
):
    """
    Records student 5-star resolution feedback and satisfaction ratings for a resolved complaint.
    """
    try:
        success = complaint_service.submit_feedback(
            complaint_id=complaint_id,
            student_id=current_user["id"],
            rating=payload.rating,
            comments=payload.comments,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist student feedback safely.",
        )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted by the ticket owner on complaints with 'Resolved' status.",
        )
    return {
        "success": True,
        "message": "Thank you! Your feedback has been recorded.",
    }
