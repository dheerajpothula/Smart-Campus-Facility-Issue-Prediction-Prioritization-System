"""
FIPP 2.0 — Secure One-Time Administrator Bootstrap CLI.

Usage:
    python -m app.bootstrap_admin

Creates the initial `fipp.admin` account (`FIPP System Administrator`) on first run
with a cryptographically generated 20-character temporary password stored exclusively
as an OWASP PBKDF2-HMAC-SHA256 hash in `admin_accounts.json`.

Idempotent: if `fipp.admin` or any admin account already exists, this command does NOT
recreate, reset, or overwrite the account.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.security import bootstrap_initial_admin  # noqa: E402


def main() -> int:
    result = bootstrap_initial_admin()
    if result.get("created"):
        print("=================================================================")
        print("FIPP 2.0 INITIAL ADMINISTRATOR BOOTSTRAP COMPLETED")
        print("=================================================================")
        print(f"Display Name       : {result['display_name']}")
        print(f"Username           : {result['username']}")
        print("Role               : admin")
        print(f"Temporary Password : {result['temporary_password']}")
        print("Password Policy    : MANDATORY CHANGE REQUIRED ON FIRST LOGIN")
        print("Security Notice    : Store this temporary password safely now. It is")
        print("                     never written to disk, logs, or source code.")
        print("=================================================================")
    else:
        print(
            f"[OK] Administrator bootstrap already initialized for '{result.get('username')}'. "
            "Existing account was preserved unchanged."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
