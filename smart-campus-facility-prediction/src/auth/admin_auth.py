"""
Secure Administrator Authentication Module for FIPP Legacy Rollback.

All sample administrator accounts, plaintext passwords, and hardcoded salt literals
have been removed. Reads exclusively from the bootstrapped `admin_accounts.json`
store (shared with FIPP 2.0 backend).
"""
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

OWASP_RECOMMENDED_ITERATIONS = 600_000
LEGACY_HASH_ITERATIONS = 100_000

_ADMIN_CREDENTIALS_STORE: Dict[str, Dict[str, Any]] = {}
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
_ADMIN_ACCOUNTS_FILE = _DATA_DIR / "admin_accounts.json"


def _get_admin_accounts_path() -> Path:
    env_override = os.environ.get("FIPP_ADMIN_STORE_FILE", "").strip()
    return Path(env_override) if env_override else _ADMIN_ACCOUNTS_FILE


def hash_password_v2(
    plain_password: str,
    iterations: int = OWASP_RECOMMENDED_ITERATIONS,
    salt: Optional[bytes] = None,
) -> str:
    """Computes an OWASP PBKDF2-HMAC-SHA256 modular hash (`pbkdf2_sha256$<iter>$<salt>$<digest>`)."""
    if not plain_password:
        return ""
    if salt is None:
        salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived}"


def hash_password(plain_password: str, salt: Optional[bytes] = None) -> str:
    """Computes a secure modular PBKDF2-HMAC-SHA256 hash using a random per-call salt."""
    return hash_password_v2(plain_password, iterations=OWASP_RECOMMENDED_ITERATIONS, salt=salt)


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Constant-time verification against modular `pbkdf2_sha256$<iter>$<salt>$<digest>` hashes."""
    if not plain_password or not stored_hash:
        return False
    clean_stored = stored_hash.strip()
    if clean_stored.startswith("pbkdf2_sha256$"):
        parts = clean_stored.split("$")
        if len(parts) == 4:
            try:
                iterations = int(parts[1])
                salt = bytes.fromhex(parts[2])
                expected_digest = parts[3]
                if iterations < 100_000 or not salt:
                    return False
                candidate_digest = hashlib.pbkdf2_hmac(
                    "sha256", plain_password.encode("utf-8"), salt, iterations
                ).hex()
                return hmac.compare_digest(candidate_digest, expected_digest)
            except Exception:
                return False
    return False


def _load_admin_accounts() -> Dict[str, Dict[str, Any]]:
    path = _get_admin_accounts_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("accounts"), dict):
                return data["accounts"]
        except Exception:
            pass
    return {}


def authenticate_admin(admin_id: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """Authenticates an administrator exclusively against persistent bootstrapped accounts."""
    if not admin_id or not plain_password:
        return None
    accounts = _load_admin_accounts()
    norm_id = admin_id.strip().lower()
    record = accounts.get(norm_id)
    if not record:
        for val in accounts.values():
            if str(val.get("id", "")).lower() == norm_id or str(val.get("username", "")).lower() == norm_id:
                record = val
                break
    if not record or not record.get("is_active", True):
        return None
    if verify_password(plain_password, str(record.get("password_hash", ""))):
        return {
            "id": record["id"],
            "name": record["name"],
            "title": record.get("title", "System Administrator"),
            "role_title": record.get("title", "System Administrator"),
            "role": "admin",
            "must_change_password": bool(record.get("must_change_password", False)),
            "authenticated_at": datetime.now().isoformat(),
        }
    return None


def verify_admin_session(auth_user: Optional[Dict[str, Any]]) -> bool:
    if not auth_user or not isinstance(auth_user, dict):
        return False
    return auth_user.get("role") == "admin" and bool(auth_user.get("id"))
