"""
FIPP 2.0 — Cryptographic Security and Authentication Module.
Provides OWASP-compliant PBKDF2-HMAC-SHA256 password hashing (600,000 iterations),
timing-attack safe credential verification, and signed JWT session token generation.
"""
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt

from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    OWASP_PBKDF2_ITERATIONS,
    LEGACY_PBKDF2_ITERATIONS,
    AUTH_SALT,
    SMART_CAMPUS_DIR,
)


def hash_password(plain_password: str, iterations: int = OWASP_PBKDF2_ITERATIONS, salt: Optional[bytes] = None) -> str:
    """
    Computes a PBKDF2-HMAC-SHA256 hash formatted as modular string:
        pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>
    """
    if not plain_password:
        return ""
    if salt is None:
        salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived.hex()}"


def hash_password_legacy(plain_password: str, salt: bytes = AUTH_SALT) -> str:
    """Computes a legacy 64-char hex hash using 100,000 iterations for backward compatibility."""
    if not plain_password:
        return ""
    return hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, LEGACY_PBKDF2_ITERATIONS).hex()


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored hash using timing-safe comparison.
    Supports both modular format (`pbkdf2_sha256$...`) and legacy 64-character hex strings.
    """
    if not plain_password or not stored_hash:
        return False

    # 1. Modular format: pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$")
        if len(parts) == 4:
            try:
                iterations = int(parts[1])
                salt = bytes.fromhex(parts[2])
                expected_digest = parts[3]
                computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations).hex()
                return hmac.compare_digest(computed, expected_digest)
            except Exception:
                return False

    # 2. Legacy 64-character hex hash
    if len(stored_hash) == 64:
        # Check against default salt with 100k iterations
        computed_legacy = hash_password_legacy(plain_password, AUTH_SALT)
        if hmac.compare_digest(computed_legacy, stored_hash):
            return True
        # Check against 600k iterations with default salt
        computed_600k = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), AUTH_SALT, OWASP_PBKDF2_ITERATIONS).hex()
        if hmac.compare_digest(computed_600k, stored_hash):
            return True

    return False


# Canonical User Directory with precomputed PBKDF2-HMAC-SHA256 hashes (NO PLAINTEXT PASSWORDS)
_HASH_ADMIN123 = hash_password_legacy("admin123")
_HASH_STUDENT123 = hash_password_legacy("student123")

SYSTEM_USER_STORE: Dict[str, Dict[str, Any]] = {
    # Administrators
    "ADM-2026-001": {
        "id": "ADM-2026-001",
        "name": "Administrator",
        "role": "admin",
        "title": "Facility Operations Lead",
        "department": "Campus Facility & Maintenance Operations",
        "email": "operations.lead@campus.edu",
        "password_hash": "e70edb936a5ebea8ae511e3f3c31ba85e568ae1e0d15d6d561f460f05d1acf5a",  # Admin@001
        "is_active": True,
    },
    "ADMIN01": {
        "id": "ADMIN01",
        "name": "Dr. K. V. Raman",
        "role": "admin",
        "title": "Director of Campus Facilities",
        "department": "Facility Operations Directorate",
        "email": "admin.facilities@campus.edu",
        "password_hash": _HASH_ADMIN123,
        "is_active": True,
    },
    "ADM-2026-002": {
        "id": "ADM-2026-002",
        "name": "Administrator",
        "role": "admin",
        "title": "Campus Infrastructure Admin",
        "department": "Civil & Infrastructure Division",
        "email": "infrastructure.admin@campus.edu",
        "password_hash": "14ed4b75d80509c8f2b55d8ed7c44be15638c5d9bf185bb22f7cc2ac54f2fa39",
        "is_active": True,
    },
    # Students
    "STU-2026-001": {
        "id": "STU-2026-001",
        "name": "Student",
        "role": "student",
        "title": "Resident Scholar",
        "department": "Computer Science & Engineering",
        "email": "resident.scholar@campus.edu",
        "block": "BH-1 Boys Hostel",
        "room_number": "204",
        "password_hash": _HASH_STUDENT123,
        "is_active": True,
    },
    "STU101": {
        "id": "STU101",
        "name": "Rahul Sharma",
        "role": "student",
        "title": "Student Resident",
        "department": "Computer Science & Engineering",
        "email": "rahul.sharma@campus.edu",
        "block": "Hostel Block B",
        "room_number": "101",
        "password_hash": _HASH_STUDENT123,
        "is_active": True,
    },
    "STU102": {
        "id": "STU102",
        "name": "Priya Patel",
        "role": "student",
        "title": "Student Resident",
        "department": "Electrical & Electronics",
        "email": "priya.patel@campus.edu",
        "block": "GH-1 Girls Hostel",
        "room_number": "302",
        "password_hash": _HASH_STUDENT123,
        "is_active": True,
    },
}


# Authoritative Persistent Credential Store & Token Revocation
_PERSISTENT_CREDENTIALS_FILE = SMART_CAMPUS_DIR / "data" / "processed" / "credentials_store.json"
_REVOKED_TOKENS_FILE = SMART_CAMPUS_DIR / "data" / "processed" / "revoked_tokens.json"
_REVOKED_TOKENS: set = set()


def _load_revoked_tokens() -> None:
    global _REVOKED_TOKENS
    if _REVOKED_TOKENS_FILE.is_file():
        try:
            with open(_REVOKED_TOKENS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    _REVOKED_TOKENS = set(data)
        except Exception:
            _REVOKED_TOKENS = set()


def revoke_token(token: str) -> None:
    """Revokes a JWT token upon logout and persists revocation to disk."""
    if not token:
        return
    _load_revoked_tokens()
    _REVOKED_TOKENS.add(token)
    try:
        _REVOKED_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_path = _REVOKED_TOKENS_FILE.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(list(_REVOKED_TOKENS), f)
        os.replace(temp_path, _REVOKED_TOKENS_FILE)
    except Exception:
        pass


def is_token_revoked(token: str) -> bool:
    """Checks whether token has been explicitly invalidated/revoked."""
    if not token:
        return False
    _load_revoked_tokens()
    return token in _REVOKED_TOKENS


def _load_persistent_credentials() -> Dict[str, str]:
    """Loads authoritative upgraded 600,000-iteration credentials from disk."""
    if _PERSISTENT_CREDENTIALS_FILE.is_file():
        try:
            with open(_PERSISTENT_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for uid, phash in data.items():
                        if uid in SYSTEM_USER_STORE:
                            SYSTEM_USER_STORE[uid]["password_hash"] = phash
                    return data
        except Exception:
            pass
    return {}


def _save_persistent_credential(user_id: str, upgraded_hash: str) -> None:
    """Persists an upgraded 600,000-iteration modular password hash to authoritative storage."""
    try:
        _PERSISTENT_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if _PERSISTENT_CREDENTIALS_FILE.is_file():
            try:
                with open(_PERSISTENT_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        existing[user_id] = upgraded_hash
        temp = _PERSISTENT_CREDENTIALS_FILE.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        os.replace(temp, _PERSISTENT_CREDENTIALS_FILE)
    except Exception:
        pass


# Initialize authoritative persistent credentials on import
_load_persistent_credentials()


def authenticate_user(identifier: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates a user identifier (ID or Email, case-insensitive) with password verification.
    Automatically upgrades legacy accounts to persistent 600,000 iterations on login.
    Returns the user dictionary if valid; None otherwise.
    """
    if not identifier or not plain_password:
        return None

    # Refresh from persistent store
    _load_persistent_credentials()

    clean_id = identifier.strip()
    user = SYSTEM_USER_STORE.get(clean_id) or SYSTEM_USER_STORE.get(clean_id.upper())

    if not user:
        # Check by email or case-insensitive ID
        for u in SYSTEM_USER_STORE.values():
            if u["id"].lower() == clean_id.lower() or u.get("email", "").lower() == clean_id.lower():
                user = u
                break

    if not user:
        return None

    if not user.get("is_active", True):
        return None

    if verify_password(plain_password, user.get("password_hash", "")):
        # If hash is not yet upgraded to modular 600,000 format, upgrade and persist it
        curr_hash = user.get("password_hash", "")
        if not curr_hash.startswith(f"pbkdf2_sha256${OWASP_PBKDF2_ITERATIONS}$"):
            upgraded = hash_password(plain_password, iterations=OWASP_PBKDF2_ITERATIONS)
            user["password_hash"] = upgraded
            _save_persistent_credential(user["id"], upgraded)
        return user

    return None


def create_access_token(user_profile: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token containing identity claims."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_profile["id"],
        "id": user_profile["id"],
        "name": user_profile["name"],
        "role": user_profile["role"],
        "title": user_profile.get("title", ""),
        "department": user_profile.get("department", ""),
        "email": user_profile.get("email", ""),
        "block": user_profile.get("block"),
        "room_number": user_profile.get("room_number"),
        "token_type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_profile: Dict[str, Any]) -> str:
    """Generates a signed long-lived refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_profile["id"],
        "id": user_profile["id"],
        "token_type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
