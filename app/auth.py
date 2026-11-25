"""
Legacy Prototype Auth Module (Deprecated).

All hardcoded sample accounts and static secret keys have been removed.
All live authentication uses `app.core.security` (persistent administrator
accounts and authorized student registry with PBKDF2-HMAC-SHA256 & JWTs).
"""
from typing import Any, Dict, Optional
from fastapi import Depends

from app.api.deps import get_current_user as _get_current_user
from app.api.deps import require_admin as _require_admin
from app.api.deps import require_student as _require_student
from app.core.security import authenticate_admin_user, create_access_token, decode_token

REGISTERED_USERS: Dict[str, Dict[str, Any]] = {}


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    return decode_token(token)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    return authenticate_admin_user(username, password)


def get_current_user(current_user: Dict[str, Any] = Depends(_get_current_user)) -> Dict[str, Any]:
    return current_user


def require_admin(current_user: Dict[str, Any] = Depends(_require_admin)) -> Dict[str, Any]:
    return current_user


def require_student(current_user: Dict[str, Any] = Depends(_require_student)) -> Dict[str, Any]:
    return current_user
