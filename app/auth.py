"""
Role-Based Authentication & Authorization Module.
Provides secure token generation, user validation, and route protection
for Student and Administrator personas.
"""

import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends

SECRET_KEY = "smart-campus-facility-auth-secret-key-2026"

# Default system users
REGISTERED_USERS: Dict[str, Dict[str, Any]] = {
    "STU101": {
        "id": "STU101",
        "name": "Rahul Sharma",
        "role": "student",
        "password": "student123",
        "department": "Computer Science & Engineering",
        "email": "rahul.sharma@campus.edu"
    },
    "STU102": {
        "id": "STU102",
        "name": "Priya Patel",
        "role": "student",
        "password": "student123",
        "department": "Electrical & Electronics",
        "email": "priya.patel@campus.edu"
    },
    "ADMIN01": {
        "id": "ADMIN01",
        "name": "Dr. K. V. Raman",
        "role": "admin",
        "password": "admin123",
        "department": "Director of Campus Facilities & Operations",
        "email": "admin.facilities@campus.edu"
    }
}

def create_access_token(user: Dict[str, Any]) -> str:
    """Generates an HMAC-signed session token containing user payload."""
    payload = {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "department": user["department"],
        "exp": int(time.time()) + (86400 * 7)  # 7 days
    }
    payload_str = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    return f"{payload_str}.{signature}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates signature and returns payload."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_str, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload_bytes = base64.urlsafe_b64decode(payload_str.encode())
        payload = json.loads(payload_bytes.decode())
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates username and password against registered directory."""
    user = REGISTERED_USERS.get(username.strip().upper())
    if not user:
        # Case-insensitive fallback
        for u in REGISTERED_USERS.values():
            if u["id"].lower() == username.strip().lower() or u["email"].lower() == username.strip().lower():
                user = u
                break
    if user and user["password"] == password:
        return user
    return None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency extracting and validating user from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in."
        )
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:]
    user_payload = decode_access_token(token)
    if not user_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please re-authenticate."
        )
    return user_payload

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Requires Administrator role; returns 403 Forbidden for students."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrator privileges required."
        )
    return current_user

def require_student(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Requires Student role (or allows Admin to preview student interface)."""
    if current_user.get("role") not in ["student", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Student account required."
        )
    return current_user
