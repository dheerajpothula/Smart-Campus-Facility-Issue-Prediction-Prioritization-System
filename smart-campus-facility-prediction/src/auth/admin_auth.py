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
# Default demo password corresponding to this hash: 'Admin@2026'
# Overridable via FIPP_ADMIN_PASSWORD environment variable.
_DEFAULT_HASH = "f9058ebaefae3b04aeca2a5269de49bf633b9d68bdb29004c46e97d379e205ca"

_ADMIN_CREDENTIALS_STORE: Dict[str, Dict[str, Any]] = {
    "ADM-2026-001": {
        "id": "ADM-2026-001",
        "name": "Dr. Robert Davies",
        "title": "Facility Operations Lead",
        "password_hash": _DEFAULT_HASH,
        "is_active": True,
    },
    "admin": {
        "id": "admin",
        "name": "System Administrator",
        "title": "Campus Infrastructure Admin",
        "password_hash": _DEFAULT_HASH,
        "is_active": True,
    },
    "ADM-2026-002": {
        "id": "ADM-2026-002",
        "name": "Sarah Jenkins",
        "title": "Maintenance Dispatcher",
        "password_hash": _DEFAULT_HASH,
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
        admin_id: The administrator identifier (e.g. 'ADM-2026-001' or 'admin').
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

    # Check against environment override if specified
    env_password = os.environ.get("FIPP_ADMIN_PASSWORD")
    if env_password:
        expected_hash = hash_password(env_password)
    else:
        expected_hash = record["password_hash"]

    candidate_hash = hash_password(plain_password)

    # Constant-time comparison to protect against timing attacks
    if hmac.compare_digest(candidate_hash, expected_hash):
        return {
            "id": record["id"],
            "name": record["name"],
            "title": record.get("title", "Administrator"),
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
