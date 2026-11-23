"""
FIPP 2.0 — Authentication API Routes.
Provides secure token issuance, identity inspection, token refreshing, and logout.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import (
    SYSTEM_USER_STORE,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
)
from app.models.data_models import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Authenticates user credentials using OWASP PBKDF2-HMAC-SHA256 verification.
    Issues signed JWT access and refresh tokens.
    """
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your identification ID and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    user_profile = UserProfile(
        id=user["id"],
        name=user["name"],
        role=user["role"],
        title=user.get("title", ""),
        department=user.get("department", ""),
        email=user.get("email", ""),
        block=user.get("block"),
        room_number=user.get("room_number"),
    )

    return TokenResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in_seconds=3600,
        user=user_profile,
        message=f"Welcome, {user['name']} ({user['role'].capitalize()})",
    )


@router.get("/me")
def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the verified profile and operational role of the authenticated caller."""
    return {"success": True, "user": current_user}


@router.post("/refresh")
def refresh_access_token(payload: RefreshTokenRequest):
    """
    Validates a cryptographic refresh token and issues a fresh 60-minute access token.
    """
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has expired. Please authenticate again.",
        )

    user_id = str(decoded.get("sub") or decoded.get("id"))
    user = SYSTEM_USER_STORE.get(user_id) or SYSTEM_USER_STORE.get(user_id.upper())
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active.",
        )

    new_access_token = create_access_token(user)
    return {
        "success": True,
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in_seconds": 3600,
    }


@router.post("/logout")
def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logs out user session and confirms token invalidation."""
    raw_token = current_user.get("token")
    if raw_token:
        revoke_token(raw_token)
    return {
        "success": True,
        "message": f"Session closed for {current_user['name']}. Please discard local authentication tokens.",
    }
