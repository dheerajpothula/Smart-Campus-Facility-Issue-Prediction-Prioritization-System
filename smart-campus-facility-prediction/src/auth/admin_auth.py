"""
Secure Administrator Authentication Module for FIPP.
Provides cryptographic password hashing (PBKDF2-HMAC-SHA256 with salt),
credential verification with timing-attack prevention (hmac.compare_digest),
and session authorization guards outside frontend code.
"""
import hashlib
import hmac
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Static dedicated cryptographic salt for Administrator password hashing
_AUTH_SALT = b"fipp_secure_salt_2026_aiml"
_HASH_ITERATIONS = 100_000

# Pre-computed PBKDF2-HMAC-SHA256 password hashes for authorized Administrators.
# Plaintext passwords are NEVER stored in code or database.
_ADMIN_CREDENTIALS_STORE: Dict[str, Dict[str, Any]] = {
    "ADM-2026-001": {
        "id": "ADM-2026-001",
        "name": "Dr. Robert Davies",
        "title": "Facility Operations Lead",
        "password_hash": "e70edb936a5ebea8ae511e3f3c31ba85e568ae1e0d15d6d561f460f05d1acf5a",
        "is_active": True,
    },
    "ADM-2026-002": {
        "id": "ADM-2026-002",
        "name": "Sarah Jenkins",
        "title": "Campus Infrastructure Admin",
        "password_hash": "14ed4b75d80509c8f2b55d8ed7c44be15638c5d9bf185bb22f7cc2ac54f2fa39",
        "is_active": True,
    },
    "ADM-2026-003": {
        "id": "ADM-2026-003",
        "name": "David Miller",
        "title": "Maintenance Dispatcher",
        "password_hash": "a25ad46752736c276c34fed62c7c7b9350aa67b9c763f3ba91d67aee012abfd7",
        "is_active": True,
    },
}


def hash_password(plain_password: str, salt: bytes = _AUTH_SALT) -> str:
    """
    Computes a PBKDF2-HMAC-SHA256 hash for a given plaintext password and salt.

    Args:
        plain_password: The plaintext password string to hash.
        salt: The cryptographic salt bytes.

    Returns:
        Hex-encoded 64-character hash string.
    """
    if not plain_password:
        return ""
    return hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        _HASH_ITERATIONS,
    ).hex()


def authenticate_admin(admin_id: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """
    Validates administrator credentials against the secure hash store.
    Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.

    Args:
        admin_id: The administrator identifier (e.g. 'ADM-2026-001', 'ADM-2026-002', 'ADM-2026-003').
        plain_password: The candidate plaintext password.

    Returns:
        Dict with authenticated admin profile if valid, None if invalid.
    """
    if not admin_id or not plain_password:
        return None

    norm_id = admin_id.strip()
    # Case-insensitive lookup match for convenience while preserving canonical ID
    record = None
    for key, val in _ADMIN_CREDENTIALS_STORE.items():
        if key.lower() == norm_id.lower():
            record = val
            break

    if not record or not record.get("is_active"):
        return None

    # Individual assigned credential hash from the secure store.
    # Note: FIPP_ADMIN_PASSWORD does not override individual authorized credentials
    # so that each administrator must authenticate with their assigned password.
    expected_hash = record["password_hash"]

    candidate_hash = hash_password(plain_password)

    # Constant-time comparison to protect against timing attacks
    if hmac.compare_digest(candidate_hash, expected_hash):
        return {
            "id": record["id"],
            "name": record["name"],
            "title": record.get("title", "Administrator"),
            "role_title": record.get("title", "Administrator"),
            "role": "admin",
            "authenticated_at": datetime.now().isoformat(),
        }

    return None


def verify_admin_session(auth_user: Optional[Dict[str, Any]]) -> bool:
    """
    Guards admin operations and views against unauthorized or non-admin access.

    Args:
        auth_user: The session state auth_user dict.

    Returns:
        True if the session belongs to a valid authenticated Administrator, False otherwise.
    """
    if not auth_user or not isinstance(auth_user, dict):
        return False
    return auth_user.get("role") == "admin" and bool(auth_user.get("id"))
