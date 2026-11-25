"""
FIPP 2.0 — Core Configuration Module.
Centralizes environment settings, security keys, token lifetimes, CORS origins, and filesystem paths.
Fails securely in pilot/production environments when required secrets are missing or insecure.
"""
import os
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

# Security & JWT Configuration
DEV_DEFAULT_JWT_SECRET = "fipp_super_secret_production_key_2026_aiml_secure_campus"
DEV_DEFAULT_AUTH_SALT = b"fipp_secure_salt_2026_aiml"

_env_jwt_secret = os.environ.get("FIPP_JWT_SECRET", "").strip()
_env_auth_salt = os.environ.get("FIPP_AUTH_SALT", "").strip()

if IS_STRICT_DEPLOY:
    if not _env_jwt_secret or len(_env_jwt_secret) < 32 or _env_jwt_secret == DEV_DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "FIPP_JWT_SECRET must be set to a strong (>=32 char) non-default secret in pilot/production environments."
        )
    if not _env_auth_salt or len(_env_auth_salt) < 16 or _env_auth_salt.encode("utf-8") == DEV_DEFAULT_AUTH_SALT:
        raise RuntimeError(
            "FIPP_AUTH_SALT must be set to a strong (>=16 char) non-default salt in pilot/production environments."
        )

JWT_SECRET_KEY = _env_jwt_secret or DEV_DEFAULT_JWT_SECRET
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("FIPP_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))       # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("FIPP_REFRESH_TOKEN_EXPIRE_DAYS", "7"))          # 7 days

# Password Hashing Configuration
OWASP_PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 100_000
DEFAULT_AUTH_SALT = DEV_DEFAULT_AUTH_SALT
AUTH_SALT = _env_auth_salt.encode("utf-8") if _env_auth_salt else DEFAULT_AUTH_SALT

# Data Store Paths (optional env overrides for isolated QA/benchmark harnesses)
_env_data_file = os.environ.get("FIPP_DATA_FILE", "").strip()
_env_upload_dir = os.environ.get("FIPP_UPLOAD_DIR", "").strip()

PRIMARY_JSON_DATA_FILE = Path(_env_data_file) if _env_data_file else (SMART_CAMPUS_DIR / "data" / "processed" / "complaints.json")
HISTORICAL_CSV_DATA_FILE = APP_DIR / "data" / "campus_complaints_dataset.csv"
SQLITE_DB_PATH = APP_DIR / "data" / "fipp_relational.db"
UPLOAD_DIR = Path(_env_upload_dir) if _env_upload_dir else (SMART_CAMPUS_DIR / "data" / "uploads")

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
