"""
FIPP 2.0 — Core Configuration Module.
Centralizes environment settings, security keys, token lifetimes, CORS origins, and filesystem paths.
Eliminates hardcoded fallback secret literals and fails securely in pilot/production environments.
"""
import os
import secrets
from pathlib import Path
from typing import List

# Base filesystem directories
CURRENT_DIR = Path(__file__).resolve().parent
APP_DIR = CURRENT_DIR.parent
PROJECT_ROOT = APP_DIR.parent
SMART_CAMPUS_DIR = PROJECT_ROOT / "smart-campus-facility-prediction"

# Runtime environment mode: development | test | pilot | production
FIPP_ENV = os.environ.get("FIPP_ENV", "development").strip().lower()
IS_STRICT_DEPLOY = FIPP_ENV in {"pilot", "production", "prod", "staging"}

# Cryptographic Secret & Salt Configuration (zero hardcoded fallback literals)
_env_jwt_secret = os.environ.get("FIPP_JWT_SECRET", "").strip()
_env_auth_salt = os.environ.get("FIPP_AUTH_SALT", "").strip()

if IS_STRICT_DEPLOY:
    if not _env_jwt_secret or len(_env_jwt_secret) < 32:
        raise RuntimeError(
            "FIPP_JWT_SECRET must be set to a strong (>=32 char) secret in pilot/production environments."
        )
    if not _env_auth_salt or len(_env_auth_salt) < 16:
        raise RuntimeError(
            "FIPP_AUTH_SALT must be set to a strong (>=16 char) salt in pilot/production environments."
        )

# In non-strict local dev/test without env vars, generate ephemeral per-process cryptographic material
JWT_SECRET_KEY = _env_jwt_secret or secrets.token_urlsafe(48)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("FIPP_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("FIPP_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password Hashing Configuration (OWASP PBKDF2-HMAC-SHA256)
OWASP_PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 100_000
AUTH_SALT = _env_auth_salt.encode("utf-8") if _env_auth_salt else secrets.token_bytes(32)

# Data & Identity Store Paths (optional env overrides for isolated QA/test harnesses)
_env_data_file = os.environ.get("FIPP_DATA_FILE", "").strip()
_env_upload_dir = os.environ.get("FIPP_UPLOAD_DIR", "").strip()
_env_admin_store = os.environ.get("FIPP_ADMIN_STORE_FILE", "").strip()
_env_student_registry = os.environ.get("FIPP_STUDENT_REGISTRY_FILE", "").strip()
_env_blocks_file = os.environ.get("FIPP_CAMPUS_BLOCKS_FILE", "").strip()

PRIMARY_JSON_DATA_FILE = (
    Path(_env_data_file)
    if _env_data_file
    else (SMART_CAMPUS_DIR / "data" / "processed" / "complaints.json")
)
HISTORICAL_CSV_DATA_FILE = APP_DIR / "data" / "campus_complaints_dataset.csv"
SQLITE_DB_PATH = APP_DIR / "data" / "fipp_relational.db"
UPLOAD_DIR = Path(_env_upload_dir) if _env_upload_dir else (SMART_CAMPUS_DIR / "data" / "uploads")

ADMIN_ACCOUNTS_FILE = (
    Path(_env_admin_store)
    if _env_admin_store
    else (SMART_CAMPUS_DIR / "data" / "processed" / "admin_accounts.json")
)
STUDENT_REGISTRY_FILE = (
    Path(_env_student_registry)
    if _env_student_registry
    else (SMART_CAMPUS_DIR / "data" / "processed" / "student_registry.json")
)
CAMPUS_BLOCKS_SEED_FILE = APP_DIR / "data" / "campus_blocks_reference.json"
CAMPUS_BLOCKS_OVERRIDE_FILE = (
    Path(_env_blocks_file)
    if _env_blocks_file
    else (SMART_CAMPUS_DIR / "data" / "processed" / "campus_blocks_override.json")
)

# Explicit Trusted CORS Configuration (never wildcard '*' with allow_credentials=True)
_default_cors_origins: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]
_env_cors = os.environ.get("FIPP_CORS_ORIGINS", "").strip()
CORS_ORIGINS: List[str] = (
    [o.strip() for o in _env_cors.split(",") if o.strip() and o.strip() != "*"]
    if _env_cors
    else _default_cors_origins
)

# Ensure critical data directories exist
PRIMARY_JSON_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
STUDENT_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
CAMPUS_BLOCKS_OVERRIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
