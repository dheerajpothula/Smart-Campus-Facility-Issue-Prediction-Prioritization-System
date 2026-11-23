"""
Secure Administrator Authentication Module for FIPP.
Provides cryptographic password hashing (PBKDF2-HMAC-SHA256 with salt),
credential verification with timing-attack prevention (hmac.compare_digest),
and session authorization guards outside frontend code.
"""
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# OWASP Recommended Iteration Thresholds:
# PBKDF2-HMAC-SHA256: >= 600,000 iterations (OWASP Password Storage Cheat Sheet).
OWASP_RECOMMENDED_ITERATIONS = 600_000
LEGACY_HASH_ITERATIONS = 100_000

# Dedicated cryptographic salt for legacy administrator password hashing.
# Configurable via FIPP_AUTH_SALT environment variable with secure fallback.
_DEFAULT_SALT = b"fipp_secure_salt_2026_aiml"
_ENV_SALT = os.environ.get("FIPP_AUTH_SALT")
_AUTH_SALT = _ENV_SALT.encode("utf-8") if _ENV_SALT else _DEFAULT_SALT
_HASH_ITERATIONS = int(os.environ.get("FIPP_HASH_ITERATIONS", str(OWASP_RECOMMENDED_ITERATIONS)))

# Pre-computed PBKDF2-HMAC-SHA256 password hashes for authorized Administrators.
# Plaintext passwords are NEVER stored in code or database.
_ADMIN_CREDENTIALS_STORE: Dict[str, Dict[str, Any]] = {
    "ADM-2026-001": {
        "id": "ADM-2026-001",
        "name": "Administrator",
        "title": "Facility Operations Lead",
        "password_hash": "e70edb936a5ebea8ae511e3f3c31ba85e568ae1e0d15d6d561f460f05d1acf5a",
        "is_active": True,
        "hash_version": "v1_legacy_100k",
    },
    "ADM-2026-002": {
        "id": "ADM-2026-002",
        "name": "Administrator",
        "title": "Campus Infrastructure Admin",
        "password_hash": "14ed4b75d80509c8f2b55d8ed7c44be15638c5d9bf185bb22f7cc2ac54f2fa39",
        "is_active": True,
        "hash_version": "v1_legacy_100k",
    },
    "ADM-2026-003": {
        "id": "ADM-2026-003",
        "name": "Administrator",
        "title": "Maintenance Dispatcher",
        "password_hash": "a25ad46752736c276c34fed62c7c7b9350aa67b9c763f3ba91d67aee012abfd7",
        "is_active": True,
        "hash_version": "v1_legacy_100k",
    },
}


def hash_password(plain_password: str, salt: bytes = _AUTH_SALT) -> str:
    """
    Computes a legacy PBKDF2-HMAC-SHA256 hash for a given plaintext password and salt.
    Maintained for backward-compatibility with existing seed credentials and test suites.

    Args:
        plain_password: The plaintext password string to hash.
        salt: The cryptographic salt bytes.

    Returns:
        Hex-encoded 64-character hash string.
    """
    if not plain_password:
        return ""
    # For backward compatibility with legacy seed credentials, use 100k if default salt
    iterations = LEGACY_HASH_ITERATIONS if salt == _AUTH_SALT else _HASH_ITERATIONS
    return hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    ).hex()


def hash_password_v2(
    plain_password: str,
    iterations: int = OWASP_RECOMMENDED_ITERATIONS,
    salt: Optional[bytes] = None,
) -> str:
    """
    Computes an upgraded PBKDF2-HMAC-SHA256 password hash using a unique cryptographically
    random 16-byte salt and at least 600,000 iterations (OWASP Password Storage Guideline).

    Returns:
        Modular string format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    if not plain_password:
        return ""
    if salt is None:
        salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored hash with constant-time comparison.
    Supports both upgraded modular format (600,000+ iterations with unique salt)
    and legacy 64-character hex format (100,000 iterations).

    Args:
        plain_password: The candidate plaintext password.
        stored_hash: Stored hash string (modular or raw hex).

    Returns:
        True if valid, False otherwise.
    """
    if not plain_password or not stored_hash:
        return False

    clean_stored = stored_hash.strip()

    # Check for upgraded modular format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    if clean_stored.startswith("pbkdf2_sha256$"):
        parts = clean_stored.split("$")
        if len(parts) == 4:
            try:
                iterations = int(parts[1])
                salt = bytes.fromhex(parts[2])
                expected_digest = parts[3]
                candidate_digest = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain_password.encode("utf-8"),
                    salt,
                    iterations,
                ).hex()
                return hmac.compare_digest(candidate_digest, expected_digest)
            except Exception:
                return False

    # Fallback to legacy 64-character hex format (100k iterations with _AUTH_SALT)
    if len(clean_stored) == 64:
        candidate_legacy = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            _AUTH_SALT,
            LEGACY_HASH_ITERATIONS,
        ).hex()
        if hmac.compare_digest(candidate_legacy, clean_stored):
            return True

        # Also check with configured _HASH_ITERATIONS if different
        if _HASH_ITERATIONS != LEGACY_HASH_ITERATIONS:
            candidate_custom = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                _AUTH_SALT,
                _HASH_ITERATIONS,
            ).hex()
            if hmac.compare_digest(candidate_custom, clean_stored):
                return True

    return False


# Persistent storage for transparently upgraded credentials (rehash-on-login)
# Persists upgraded hashes to disk across server restarts without relying on transient memory
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
_PERSISTENT_CREDENTIALS_FILE = _DATA_DIR / "credentials_store.json"
_UPGRADED_CREDENTIALS_CACHE: Dict[str, str] = {}


def _load_persistent_credentials() -> Dict[str, str]:
    if _PERSISTENT_CREDENTIALS_FILE.is_file():
        try:
            with open(_PERSISTENT_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _UPGRADED_CREDENTIALS_CACHE.update(data)
                    return data
        except Exception:
            pass
    return {}


def _save_persistent_credential(admin_id: str, upgraded_hash: str) -> None:
    try:
        _PERSISTENT_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if _PERSISTENT_CREDENTIALS_FILE.is_file():
            try:
                with open(_PERSISTENT_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        existing[admin_id] = upgraded_hash
        temp = _PERSISTENT_CREDENTIALS_FILE.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        os.replace(temp, _PERSISTENT_CREDENTIALS_FILE)
    except Exception:
        pass


# Load any existing upgraded credentials on module initialization
_load_persistent_credentials()


def authenticate_admin(admin_id: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """
    Validates administrator credentials against the secure hash store.
    Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.
    Automatically upgrades legacy accounts to OWASP-compliant 600k unique-salt hashes upon successful login,
    persisting upgraded credentials to disk across restarts.

    Args:
        admin_id: The administrator identifier (e.g. 'ADM-2026-001', 'ADM-2026-002', 'ADM-2026-003').
        plain_password: The candidate plaintext password.

    Returns:
        Dict with authenticated admin profile if valid, None if invalid.
    """
    if not admin_id or not plain_password:
        return None

    # Refresh latest persistent credentials from disk
    _load_persistent_credentials()

    norm_id = admin_id.strip()
    # Case-insensitive lookup match for convenience while preserving canonical ID
    record = None
    for key, val in _ADMIN_CREDENTIALS_STORE.items():
        if key.lower() == norm_id.lower():
            record = val
            break

    if not record or not record.get("is_active"):
        return None

    # Check environment variable override or upgraded persistent cache before seed store
    safe_env_id = record["id"].replace("-", "_").upper()
    env_hash = os.environ.get(f"FIPP_ADMIN_HASH_{safe_env_id}")
    if env_hash:
        expected_hash = env_hash.strip()
    elif record["id"] in _UPGRADED_CREDENTIALS_CACHE:
        expected_hash = _UPGRADED_CREDENTIALS_CACHE[record["id"]]
    else:
        expected_hash = record["password_hash"]

    # Constant-time comparison to protect against timing attacks
    if verify_password(plain_password, expected_hash):
        # Safe rehash-on-login: if using legacy 100k shared salt, transparently upgrade to 600k unique salt
        if not expected_hash.startswith("pbkdf2_sha256$"):
            upgraded = hash_password_v2(plain_password, iterations=OWASP_RECOMMENDED_ITERATIONS)
            _UPGRADED_CREDENTIALS_CACHE[record["id"]] = upgraded
            _save_persistent_credential(record["id"], upgraded)

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
