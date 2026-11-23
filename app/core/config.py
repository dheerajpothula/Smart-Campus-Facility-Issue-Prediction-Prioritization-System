"""
FIPP 2.0 — Core Configuration Module.
Centralizes environment settings, security keys, token lifetimes, and filesystem paths.
"""
import os
from pathlib import Path
from typing import List

# Base filesystem directories
CURRENT_DIR = Path(__file__).resolve().parent
APP_DIR = CURRENT_DIR.parent
PROJECT_ROOT = APP_DIR.parent
SMART_CAMPUS_DIR = PROJECT_ROOT / "smart-campus-facility-prediction"

# Security & JWT Configuration
JWT_SECRET_KEY = os.environ.get("FIPP_JWT_SECRET", "fipp_super_secret_production_key_2026_aiml_secure_campus")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("FIPP_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))       # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("FIPP_REFRESH_TOKEN_EXPIRE_DAYS", "7"))          # 7 days

# Password Hashing Configuration
OWASP_PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 100_000
DEFAULT_AUTH_SALT = b"fipp_secure_salt_2026_aiml"
AUTH_SALT = os.environ.get("FIPP_AUTH_SALT", "").encode("utf-8") or DEFAULT_AUTH_SALT

# Data Store Paths
PRIMARY_JSON_DATA_FILE = SMART_CAMPUS_DIR / "data" / "processed" / "complaints.json"
HISTORICAL_CSV_DATA_FILE = APP_DIR / "data" / "campus_complaints_dataset.csv"
SQLITE_DB_PATH = APP_DIR / "data" / "fipp_relational.db"
UPLOAD_DIR = SMART_CAMPUS_DIR / "data" / "uploads"

# CORS Configuration
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "*",
]

# Ensure critical data directories exist
PRIMARY_JSON_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
