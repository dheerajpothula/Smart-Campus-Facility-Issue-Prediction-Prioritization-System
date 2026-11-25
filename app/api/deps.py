"""
FIPP 2.0 — FastAPI Security Dependencies, Rate Limiting, and RBAC Enforcers.
Extracts and validates signed Bearer JWT tokens against live admin and student stores,
and enforces mandatory first-login password change and server-side RBAC boundaries.
"""
import threading
import time
from collections import defaultdict, deque
from typing import Any, Callable, Deque, Dict, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import (
    decode_token,
    get_admin_account,
    get_student_record,
    is_token_revoked,
)

security_scheme = HTTPBearer(auto_error=False)

_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)


def reset_rate_limiter() -> None:
    """Clears in-memory rate-limit counters (intended for isolated tests)."""
    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_BUCKETS.clear()


def rate_limit_admin_intelligence(max_requests: int = 60, window_seconds: int = 60) -> Callable:
    """Creates a per-user/IP sliding-window rate limiter dependency for intelligence endpoints."""

    def _limiter(
        request: Request,
        current_user: Dict[str, Any] = Depends(require_admin),
    ) -> Dict[str, Any]:
        now = time.monotonic()
        client_host = request.client.host if request.client else "unknown"
        bucket_key = f"{current_user.get('id', client_host)}:{request.url.path}"
        with _RATE_LIMIT_LOCK:
            q = _RATE_LIMIT_BUCKETS[bucket_key]
            cutoff = now - window_seconds
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Intelligence endpoint rate limit exceeded. Please retry shortly.",
                )
            q.append(now)
        return current_user

    return _limiter


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Extracts Bearer token from Authorization header, verifies signature & revocation,
    and checks the caller against the persistent admin store or authorized student registry.
    """
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    elif authorization:
        parts = authorization.strip().split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has been invalidated by logout. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(payload.get("sub") or payload.get("id") or "").strip()
    role = str(payload.get("role") or "").strip().lower()

    if role == "admin":
        user = get_admin_account(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Administrator account is no longer provisioned. Please authenticate again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator account has been suspended or deactivated.",
            )
        return {
            "id": str(user["id"]),
            "name": str(user["name"]),
            "role": "admin",
            "title": str(user.get("title", "System Administrator")),
            "department": str(user.get("department", "")),
            "email": str(user.get("email", "")),
            "block": None,
            "room_number": None,
            "must_change_password": bool(user.get("must_change_password", False)),
            "token": token,
        }

    if role == "student":
        student = get_student_record(user_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Student identity is no longer authorized. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not student.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student account access has been deactivated.",
            )
        return {
            "id": str(student["student_id"]),
            "name": str(student["name"]),
            "role": "student",
            "title": "Enrolled Student",
            "department": "",
            "email": "",
            "block": student.get("block"),
            "room_number": student.get("room_number"),
            "must_change_password": False,
            "token": token,
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid role claim in session token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Guards administrator-only operational endpoints and enforces first-login password change."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required. Insufficient operational privileges.",
        )
    if current_user.get("must_change_password"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required before accessing administrator controls.",
        )
    return current_user


def require_student(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Guards student portal endpoints and enforces student identity."""
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student portal access only. Authenticated persona is not a student.",
        )
    return current_user
