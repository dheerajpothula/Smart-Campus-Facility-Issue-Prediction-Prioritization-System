"""
FIPP 2.0 — FastAPI Security Dependencies and RBAC Enforcers.
Extracts and validates signed Bearer JWT tokens and enforces server-side
Student and Administrator role boundaries.
"""
from typing import Any, Dict, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import SYSTEM_USER_STORE, decode_token, is_token_revoked

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Extracts Bearer token from authorization header, decodes and validates signature,
    and returns verified user claims.
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

    user_id = str(payload.get("sub") or payload.get("id"))
    user = SYSTEM_USER_STORE.get(user_id) or SYSTEM_USER_STORE.get(user_id.upper())

    if user and not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been suspended or deactivated.",
        )

    return {
        "id": user_id,
        "name": payload.get("name", user.get("name", "") if user else ""),
        "role": payload.get("role", user.get("role", "") if user else ""),
        "title": payload.get("title", user.get("title", "") if user else ""),
        "department": payload.get("department", user.get("department", "") if user else ""),
        "email": payload.get("email", user.get("email", "") if user else ""),
        "block": payload.get("block", user.get("block") if user else None),
        "room_number": payload.get("room_number", user.get("room_number") if user else None),
        "token": token,
    }


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Guards administrator-only operational endpoints."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required. Insufficient operational privileges.",
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
