"""
FIPP 2.0 — Cryptographic Security, Bootstrap Administration & Authorized Student Registry.

Provides:
- OWASP-compliant PBKDF2-HMAC-SHA256 password hashing (600,000 iterations, random 16-byte salt)
- Strong password policy validation and cryptographically random generator
- Idempotent first-run administrator bootstrap (`fipp.admin`) with mandatory first-login change
- Authorized student registry validation using exact 8-digit string IDs (preserving leading zeroes)
- Signed JWT access/refresh token issuance and persisted revocation list
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import jwt

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ADMIN_ACCOUNTS_FILE,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    OWASP_PBKDF2_ITERATIONS,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SMART_CAMPUS_DIR,
    STUDENT_REGISTRY_FILE,
)

_AUTH_LOCK = threading.RLock()
_REVOKED_TOKENS_FILE = SMART_CAMPUS_DIR / "data" / "processed" / "revoked_tokens.json"
_REVOKED_TOKENS: set = set()

INITIAL_ADMIN_USERNAME = "fipp.admin"
INITIAL_ADMIN_DISPLAY_NAME = "FIPP System Administrator"

STUDENT_ID_PATTERN = re.compile(r"^\d{8}$")
PASSWORD_SYMBOLS = "!@#$%^&*-_=+"


# ---------------------------------------------------------------------------
# Password Hashing & Strong Password Policy
# ---------------------------------------------------------------------------

def hash_password(plain_password: str, iterations: int = OWASP_PBKDF2_ITERATIONS, salt: Optional[bytes] = None) -> str:
    """Computes a PBKDF2-HMAC-SHA256 hash formatted as `pbkdf2_sha256$<iter>$<salt_hex>$<digest_hex>`."""
    if not plain_password:
        return ""
    if salt is None:
        salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verifies a plaintext password against a stored modular PBKDF2 hash in constant time."""
    if not plain_password or not stored_hash or not stored_hash.startswith("pbkdf2_sha256$"):
        return False
    parts = stored_hash.split("$")
    if len(parts) != 4:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_digest = parts[3]
        if iterations < 100_000 or not salt:
            return False
        computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations).hex()
        return hmac.compare_digest(computed, expected_digest)
    except Exception:
        return False


def validate_strong_password(password: str, username: Optional[str] = None) -> None:
    """Enforces strong administrator password policy; raises ValueError on violation."""
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")
    if any(ch.isspace() for ch in password):
        raise ValueError("Password must not contain whitespace characters.")
    if not any(ch.isupper() for ch in password):
        raise ValueError("Password must include at least one uppercase letter.")
    if not any(ch.islower() for ch in password):
        raise ValueError("Password must include at least one lowercase letter.")
    if not any(ch.isdigit() for ch in password):
        raise ValueError("Password must include at least one numeric digit.")
    if not any(not ch.isalnum() for ch in password):
        raise ValueError("Password must include at least one special character.")
    if username and username.strip().lower() in password.lower():
        raise ValueError("Password must not contain the administrator username.")


def generate_secure_password(length: int = 20) -> str:
    """Generates a cryptographically random strong temporary password."""
    target_len = max(16, int(length))
    upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    lower = "abcdefghijkmnopqrstuvwxyz"
    digits = "23456789"
    symbols = PASSWORD_SYMBOLS
    all_chars = upper + lower + digits + symbols

    chars = [
        secrets.choice(upper),
        secrets.choice(upper),
        secrets.choice(lower),
        secrets.choice(lower),
        secrets.choice(digits),
        secrets.choice(digits),
        secrets.choice(symbols),
        secrets.choice(symbols),
    ]
    while len(chars) < target_len:
        chars.append(secrets.choice(all_chars))
    secrets.SystemRandom().shuffle(chars)
    candidate = "".join(chars)
    validate_strong_password(candidate, INITIAL_ADMIN_USERNAME)
    return candidate


# ---------------------------------------------------------------------------
# Token Revocation Persistence
# ---------------------------------------------------------------------------

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
    """Revokes a JWT token upon logout and persists revocation atomically to disk."""
    if not token:
        return
    with _AUTH_LOCK:
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
    """Checks whether a JWT token has been explicitly revoked."""
    if not token:
        return False
    _load_revoked_tokens()
    return token in _REVOKED_TOKENS


# ---------------------------------------------------------------------------
# Persistent Admin Account Store & Idempotent Bootstrap
# ---------------------------------------------------------------------------

def _get_admin_store_path() -> Path:
    env_override = os.environ.get("FIPP_ADMIN_STORE_FILE", "").strip()
    return Path(env_override) if env_override else ADMIN_ACCOUNTS_FILE


def _load_admin_store() -> Dict[str, Any]:
    path = _get_admin_store_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("accounts"), dict):
                return data
        except Exception:
            pass
    return {"bootstrapped": False, "accounts": {}}


def _save_admin_store(store: Dict[str, Any]) -> None:
    path = _get_admin_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    try:
        temp_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
    except Exception as exc:
        raise RuntimeError("Failed to persist administrator accounts securely.") from exc
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def bootstrap_initial_admin(
    username: str = INITIAL_ADMIN_USERNAME,
    display_name: str = INITIAL_ADMIN_DISPLAY_NAME,
) -> Dict[str, Any]:
    """
    Idempotently creates the initial `fipp.admin` administrator account on first run.
    Never recreates, resets, or overwrites an existing account once bootstrapped.
    Returns `temporary_password` ONLY at creation time (caller displays once in stdout).
    """
    norm_username = (username or INITIAL_ADMIN_USERNAME).strip().lower()
    if not norm_username:
        raise ValueError("Administrator username cannot be empty.")

    with _AUTH_LOCK:
        store = _load_admin_store()
        accounts = store.setdefault("accounts", {})
        if store.get("bootstrapped") or norm_username in accounts or len(accounts) > 0:
            return {
                "created": False,
                "already_initialized": True,
                "username": norm_username,
                "display_name": accounts.get(norm_username, {}).get("name", display_name),
            }

        temp_password = generate_secure_password(20)
        pwd_hash = hash_password(temp_password, iterations=OWASP_PBKDF2_ITERATIONS)
        now_iso = datetime.now(timezone.utc).isoformat()

        accounts[norm_username] = {
            "id": norm_username,
            "username": norm_username,
            "name": display_name,
            "role": "admin",
            "title": "System Administrator",
            "department": "Campus Facility & Maintenance Operations",
            "email": "",
            "password_hash": pwd_hash,
            "must_change_password": True,
            "token_version": 1,
            "is_active": True,
            "created_at": now_iso,
            "password_updated_at": None,
        }
        store["bootstrapped"] = True
        store["bootstrapped_at"] = now_iso
        _save_admin_store(store)

        return {
            "created": True,
            "already_initialized": False,
            "username": norm_username,
            "display_name": display_name,
            "must_change_password": True,
            "temporary_password": temp_password,
        }


def rotate_admin_temporary_password(
    username: str = INITIAL_ADMIN_USERNAME,
    display_name: str = INITIAL_ADMIN_DISPLAY_NAME,
) -> Dict[str, Any]:
    """
    Rotates the initial administrator's credential to a fresh cryptographically random
    temporary password, enforces mandatory first-login password change, and invalidates
    any previously issued sessions via `token_version` increment.
    """
    norm_username = (username or INITIAL_ADMIN_USERNAME).strip().lower()
    if not norm_username:
        raise ValueError("Administrator username cannot be empty.")

    with _AUTH_LOCK:
        store = _load_admin_store()
        accounts = store.setdefault("accounts", {})
        rec = accounts.get(norm_username)
        if not rec:
            return bootstrap_initial_admin(username=norm_username, display_name=display_name)

        new_temp_password = generate_secure_password(20)
        while verify_password(new_temp_password, rec.get("password_hash", "")):
            new_temp_password = generate_secure_password(20)

        now_iso = datetime.now(timezone.utc).isoformat()
        rec["name"] = display_name or rec.get("name", INITIAL_ADMIN_DISPLAY_NAME)
        rec["password_hash"] = hash_password(new_temp_password, iterations=OWASP_PBKDF2_ITERATIONS)
        rec["must_change_password"] = True
        rec["is_active"] = True
        rec["token_version"] = int(rec.get("token_version", 1)) + 1
        rec["password_updated_at"] = now_iso
        store["bootstrapped"] = True
        _save_admin_store(store)

        return {
            "created": False,
            "rotated": True,
            "username": norm_username,
            "display_name": rec["name"],
            "must_change_password": True,
            "temporary_password": new_temp_password,
        }


def get_admin_account(username: str) -> Optional[Dict[str, Any]]:
    """Retrieves an administrator account record (case-insensitive username match)."""
    if not username:
        return None
    norm = username.strip().lower()
    with _AUTH_LOCK:
        accounts = _load_admin_store().get("accounts", {})
        rec = accounts.get(norm)
        if rec:
            return rec
        for acc in accounts.values():
            if str(acc.get("id", "")).lower() == norm or str(acc.get("username", "")).lower() == norm:
                return acc
    return None


def authenticate_admin_user(username: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """Authenticates an active administrator from the persistent account store."""
    if not username or not plain_password:
        return None
    rec = get_admin_account(username)
    if not rec or not rec.get("is_active", True):
        return None
    if verify_password(plain_password, rec.get("password_hash", "")):
        return {
            "id": rec["id"],
            "name": rec["name"],
            "role": "admin",
            "title": rec.get("title", "System Administrator"),
            "department": rec.get("department", ""),
            "email": rec.get("email", ""),
            "block": None,
            "room_number": None,
            "must_change_password": bool(rec.get("must_change_password", False)),
            "token_version": int(rec.get("token_version", 1)),
            "is_active": bool(rec.get("is_active", True)),
        }
    return None


def change_admin_password(username: str, current_password: str, new_password: str) -> Dict[str, Any]:
    """
    Verifies current password, enforces strong password policy on new password,
    persists new PBKDF2-HMAC-SHA256 hash, and clears `must_change_password`.
    """
    with _AUTH_LOCK:
        store = _load_admin_store()
        accounts = store.get("accounts", {})
        norm = username.strip().lower()
        rec = accounts.get(norm)
        if not rec or not rec.get("is_active", True):
            raise ValueError("Administrator account was not found or is inactive.")
        if not verify_password(current_password, rec.get("password_hash", "")):
            raise ValueError("Current password is incorrect.")
        if current_password == new_password:
            raise ValueError("New password must differ from your current password.")
        validate_strong_password(new_password, rec.get("username", norm))

        rec["password_hash"] = hash_password(new_password, iterations=OWASP_PBKDF2_ITERATIONS)
        rec["must_change_password"] = False
        rec["token_version"] = int(rec.get("token_version", 1)) + 1
        rec["password_updated_at"] = datetime.now(timezone.utc).isoformat()
        _save_admin_store(store)

        return {
            "id": rec["id"],
            "name": rec["name"],
            "role": "admin",
            "title": rec.get("title", "System Administrator"),
            "department": rec.get("department", ""),
            "email": rec.get("email", ""),
            "block": None,
            "room_number": None,
            "must_change_password": False,
            "token_version": int(rec["token_version"]),
            "is_active": True,
        }


# ---------------------------------------------------------------------------
# Authorized Student Registry (8-Digit String ID + Registered Student Name)
# ---------------------------------------------------------------------------

def _get_student_registry_path() -> Path:
    env_override = os.environ.get("FIPP_STUDENT_REGISTRY_FILE", "").strip()
    return Path(env_override) if env_override else STUDENT_REGISTRY_FILE


def validate_student_id(student_id: Any) -> str:
    """
    Strictly validates an eight-digit numeric string student ID.
    Rejects non-strings (prevents integer coercion stripping leading zeroes),
    alphabetic characters, spaces, and lengths != 8.
    """
    if not isinstance(student_id, str):
        raise ValueError("Student ID must be an eight-digit numeric string preserving leading zeroes.")
    cleaned = student_id.strip()
    if not STUDENT_ID_PATTERN.fullmatch(cleaned):
        raise ValueError("Student ID must consist of exactly eight numeric digits (0-9).")
    return cleaned


def validate_student_name(student_name: Any) -> str:
    """Trims and validates the student's full name."""
    if not isinstance(student_name, str):
        raise ValueError("Student name must be a valid text string.")
    collapsed = " ".join(student_name.strip().split())
    if len(collapsed) < 2 or len(collapsed) > 100:
        raise ValueError("Student name must be between 2 and 100 characters.")
    if not any(ch.isalpha() for ch in collapsed):
        raise ValueError("Student name must contain alphabetic characters.")
    return collapsed


def _load_student_registry() -> List[Dict[str, Any]]:
    path = _get_student_registry_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def _save_student_registry(records: List[Dict[str, Any]]) -> None:
    path = _get_student_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    try:
        temp_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
    except Exception as exc:
        raise RuntimeError("Failed to persist student registry securely.") from exc
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def list_students() -> List[Dict[str, Any]]:
    """Returns all administrator-provisioned student registry records."""
    with _AUTH_LOCK:
        return list(_load_student_registry())


def get_student_record(student_id: str) -> Optional[Dict[str, Any]]:
    """Looks up an authorized student strictly by exact 8-digit string ID."""
    if not isinstance(student_id, str):
        return None
    cleaned = student_id.strip()
    if not STUDENT_ID_PATTERN.fullmatch(cleaned):
        return None
    with _AUTH_LOCK:
        for rec in _load_student_registry():
            if str(rec.get("student_id", "")) == cleaned:
                return rec
    return None


def normalize_student_name(student_name: str) -> str:
    """Consistent case-folded whitespace-collapsed student name normalization."""
    return " ".join((student_name or "").strip().split()).casefold()


class StudentIdentityMismatchError(ValueError):
    """Raised when an existing 8-digit Student ID is submitted with a non-matching name."""


class StudentAccountDeactivatedError(PermissionError):
    """Raised when an inactive/disabled student account attempts login."""


def provision_student(
    student_id: str,
    name: str,
    block: Optional[str] = None,
    room_number: Optional[str] = None,
    provisioned_by: str = INITIAL_ADMIN_USERNAME,
) -> Dict[str, Any]:
    """Provisions a student record under administrator control (optional administrative workflow)."""
    valid_id = validate_student_id(student_id)
    valid_name = validate_student_name(name)
    now_iso = datetime.now(timezone.utc).isoformat()
    with _AUTH_LOCK:
        records = _load_student_registry()
        if any(str(r.get("student_id", "")) == valid_id for r in records):
            raise ValueError(f"Student ID '{valid_id}' is already registered.")
        entry = {
            "student_id": valid_id,
            "name": valid_name,
            "normalized_name": normalize_student_name(valid_name),
            "block": block.strip() if isinstance(block, str) and block.strip() else None,
            "room_number": room_number.strip() if isinstance(room_number, str) and room_number.strip() else None,
            "is_active": True,
            "registration_source": "admin_provisioned",
            "identity_verification": "admin_entered",
            "registered_at": now_iso,
            "last_login_at": None,
            "provisioned_at": now_iso,
            "provisioned_by": provisioned_by,
        }
        records.append(entry)
        _save_student_registry(records)
        return entry


def update_student_enrollment(
    student_id: str,
    is_active: Optional[bool] = None,
    name: Optional[str] = None,
    block: Optional[str] = None,
    room_number: Optional[str] = None,
) -> Dict[str, Any]:
    """Updates status or performs administrator-controlled name/detail correction for a student."""
    valid_id = validate_student_id(student_id)
    with _AUTH_LOCK:
        records = _load_student_registry()
        for rec in records:
            if str(rec.get("student_id", "")) == valid_id:
                if is_active is not None:
                    rec["is_active"] = bool(is_active)
                if name is not None:
                    valid_name = validate_student_name(name)
                    rec["name"] = valid_name
                    rec["normalized_name"] = normalize_student_name(valid_name)
                if block is not None:
                    rec["block"] = block.strip() or None
                if room_number is not None:
                    rec["room_number"] = room_number.strip() or None
                rec["updated_at"] = datetime.now(timezone.utc).isoformat()
                _save_student_registry(records)
                return rec
        raise ValueError(f"Student ID '{valid_id}' was not found in the student registry.")


def _build_student_profile(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(rec["student_id"]),
        "name": str(rec["name"]),
        "role": "student",
        "title": "Self-Registered Student",
        "department": "",
        "email": "",
        "block": rec.get("block"),
        "room_number": rec.get("room_number"),
        "must_change_password": False,
        "identity_verification": rec.get("identity_verification", "self_declared_unverified"),
        "is_active": True,
    }


def authenticate_or_register_student(student_name: str, student_id: str) -> Tuple[Dict[str, Any], bool]:
    """
    Self-registration and login workflow for students using Student Name + exact 8-digit Student ID:
    - Case A (New student ID): validates inputs, automatically creates and persists a student record
      marked `self_declared_unverified` (not institutionally verified), and returns `(profile, True)`.
    - Case B (Existing student ID): verifies account is active and matches normalized name.
      If name matches, updates `last_login_at` without creating duplicates and returns `(profile, False)`.
      If name differs, raises StudentIdentityMismatchError without overwriting existing record.
    """
    valid_id = validate_student_id(student_id)
    valid_name = validate_student_name(student_name)
    norm_input_name = normalize_student_name(valid_name)
    now_iso = datetime.now(timezone.utc).isoformat()

    with _AUTH_LOCK:
        records = _load_student_registry()
        for rec in records:
            if str(rec.get("student_id", "")) == valid_id:
                if not rec.get("is_active", True):
                    raise StudentAccountDeactivatedError(
                        "This student profile has been deactivated by an administrator."
                    )
                stored_norm = normalize_student_name(str(rec.get("name", "")))
                if stored_norm != norm_input_name:
                    raise StudentIdentityMismatchError(
                        "This 8-digit Student ID is already registered under a different name. "
                        "Self-service identity overwrite is not permitted; please contact a Campus Administrator to request a name correction."
                    )
                rec["last_login_at"] = now_iso
                _save_student_registry(records)
                return _build_student_profile(rec), False

        new_entry = {
            "student_id": valid_id,
            "name": valid_name,
            "normalized_name": norm_input_name,
            "block": None,
            "room_number": None,
            "is_active": True,
            "registration_source": "self_registered",
            "identity_verification": "self_declared_unverified",
            "registered_at": now_iso,
            "last_login_at": now_iso,
            "provisioned_at": now_iso,
            "provisioned_by": "self_registration",
        }
        records.append(new_entry)
        _save_student_registry(records)
        return _build_student_profile(new_entry), True


def authenticate_student(student_name: str, student_id: str) -> Optional[Dict[str, Any]]:
    """Compatibility wrapper returning authenticated/registered student profile or None."""
    try:
        profile, _ = authenticate_or_register_student(student_name, student_id)
        return profile
    except (ValueError, StudentIdentityMismatchError, StudentAccountDeactivatedError):
        return None


def authenticate_user(identifier: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates administrator credentials only.
    Legacy demo accounts and hardcoded credentials have been permanently removed.
    """
    return authenticate_admin_user(identifier, plain_password)


# ---------------------------------------------------------------------------
# Signed JWT Generation & Decoding
# ---------------------------------------------------------------------------

def create_access_token(user_profile: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token containing verified identity claims."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_profile["id"]),
        "id": str(user_profile["id"]),
        "name": user_profile["name"],
        "role": user_profile["role"],
        "title": user_profile.get("title", ""),
        "department": user_profile.get("department", ""),
        "email": user_profile.get("email", ""),
        "block": user_profile.get("block"),
        "room_number": user_profile.get("room_number"),
        "must_change_password": bool(user_profile.get("must_change_password", False)),
        "token_version": int(user_profile.get("token_version", 1)),
        "identity_verification": user_profile.get("identity_verification"),
        "token_type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_profile: Dict[str, Any]) -> str:
    """Generates a signed refresh token preserving user role claim."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_profile["id"]),
        "id": str(user_profile["id"]),
        "role": user_profile["role"],
        "token_version": int(user_profile.get("token_version", 1)),
        "token_type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except (jwt.PyJWTError, Exception):
        return None
