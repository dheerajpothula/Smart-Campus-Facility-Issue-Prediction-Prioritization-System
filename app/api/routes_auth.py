"""
FIPP 2.0 — Authentication API Routes.
Provides secure administrator login, mandatory first-login password update,
authorized eight-digit student login, session inspection, token refresh, and logout.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.api.deps import get_current_user, rate_limit_auth_requests
from app.core.security import (
    StudentAccountDeactivatedError,
    StudentIdentityMismatchError,
    authenticate_admin_user,
    authenticate_or_register_student,
    change_admin_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_admin_account,
    get_student_record,
    is_token_revoked,
    revoke_token,
)
from app.models.data_models import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    StudentLoginRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
_auth_rate_limit = rate_limit_auth_requests(max_requests=25, window_seconds=60)


def _to_user_profile(user: Dict[str, Any]) -> UserProfile:
    return UserProfile(
        id=str(user["id"]),
        name=str(user["name"]),
        role=str(user["role"]),
        title=user.get("title", ""),
        department=user.get("department", ""),
        email=user.get("email", ""),
        block=user.get("block"),
        room_number=user.get("room_number"),
        must_change_password=bool(user.get("must_change_password", False)),
        identity_verification=user.get("identity_verification"),
    )


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(_auth_rate_limit)])
def login(payload: LoginRequest):
    """
    Authenticates administrator credentials using OWASP PBKDF2-HMAC-SHA256 verification.
    Issues signed JWT access and refresh tokens.
    """
    user = authenticate_admin_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    profile = _to_user_profile(user)

    return TokenResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in_seconds=3600,
        user=profile,
        message=(
            "Temporary initial password must be changed before accessing operations."
            if profile.must_change_password
            else f"Welcome, {user['name']}."
        ),
    )


@router.post("/student/login", response_model=TokenResponse, dependencies=[Depends(_auth_rate_limit)])
def student_login(payload: StudentLoginRequest):
    """
    Self-registration and sign-in endpoint for students using Student Name and exact 8-digit Student ID.
    - New valid 8-digit Student IDs are automatically created and persisted in the local student registry.
    - Existing Student IDs authenticate if the normalized name matches; mismatched names are rejected
      with 409 Conflict without overwriting or leaking existing identity records.
    """
    try:
        user, is_new = authenticate_or_register_student(payload.student_name, payload.student_id)
    except StudentAccountDeactivatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except StudentIdentityMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist student registration record safely.",
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    profile = _to_user_profile(user)

    msg = (
        f"Student profile registered under self-declared identity. Welcome, {user['name']} ({user['id']})."
        if is_new
        else f"Welcome back, {user['name']} ({user['id']})."
    )

    return TokenResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in_seconds=3600,
        user=profile,
        is_new_registration=is_new,
        message=msg,
    )


@router.post("/change-password", response_model=TokenResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Changes an authenticated administrator's password, enforces strong password rules,
    clears the mandatory first-login flag, and returns refreshed tokens.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrator accounts have passwords managed through this endpoint.",
        )

    try:
        updated_user = change_admin_password(
            username=current_user["id"],
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update administrator credentials securely.",
        )

    # Revoke prior access token and issue updated clean session token
    old_token = current_user.get("token")
    if old_token:
        revoke_token(old_token)

    access_token = create_access_token(updated_user)
    refresh_token = create_refresh_token(updated_user)
    profile = _to_user_profile(updated_user)

    return TokenResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in_seconds=3600,
        user=profile,
        message="Administrator password updated successfully.",
    )


@router.get("/me")
def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the verified profile and operational role of the authenticated caller."""
    return {"success": True, "user": current_user}


@router.post("/refresh")
def refresh_access_token(payload: RefreshTokenRequest):
    """
    Validates a cryptographic refresh token, checks revocation and enrollment status,
    and issues a fresh 60-minute access token.
    """
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("token_type") != "refresh" or is_token_revoked(payload.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid, revoked, or has expired. Please authenticate again.",
        )

    user_id = str(decoded.get("sub") or decoded.get("id") or "")
    role = str(decoded.get("role") or "admin").lower()

    if role == "student":
        stu = get_student_record(user_id)
        if not stu or not stu.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Student account no longer active.",
            )
        user_profile = {
            "id": str(stu["student_id"]),
            "name": str(stu["name"]),
            "role": "student",
            "title": "Self-Registered Student",
            "department": "",
            "email": "",
            "block": stu.get("block"),
            "room_number": stu.get("room_number"),
            "must_change_password": False,
            "identity_verification": stu.get("identity_verification", "self_declared_unverified"),
        }
    else:
        adm = get_admin_account(user_id)
        if not adm or not adm.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Administrator account no longer active.",
            )
        if int(decoded.get("token_version", 1)) != int(adm.get("token_version", 1)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalidated due to administrator credential rotation.",
            )
        user_profile = {
            "id": str(adm["id"]),
            "name": str(adm["name"]),
            "role": "admin",
            "title": adm.get("title", "System Administrator"),
            "department": adm.get("department", ""),
            "email": adm.get("email", ""),
            "must_change_password": bool(adm.get("must_change_password", False)),
            "token_version": int(adm.get("token_version", 1)),
        }

    new_access_token = create_access_token(user_profile)
    return {
        "success": True,
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in_seconds": 3600,
    }


@router.post("/logout")
def logout(
    payload: Optional[RefreshTokenRequest] = Body(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Logs out user session and revokes active access and optional refresh tokens."""
    raw_token = current_user.get("token")
    if raw_token:
        revoke_token(raw_token)
    if payload and payload.refresh_token:
        revoke_token(payload.refresh_token)
    return {
        "success": True,
        "message": f"Session closed for {current_user['name']}. Please discard local authentication tokens.",
    }
