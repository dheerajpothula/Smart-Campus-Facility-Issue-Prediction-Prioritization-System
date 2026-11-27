"""
FIPP 2.0 — Secure One-Time Administrator Bootstrap CLI.

Usage:
    python -m app.bootstrap_admin            # Idempotent first-run creation
    python -m app.bootstrap_admin --rotate   # Rotate to a fresh one-time temp password
    python -m app.bootstrap_admin --reset --username <user> --password-stdin

Creates, rotates, or resets the administrator account in `admin_accounts.json`
with an OWASP PBKDF2-HMAC-SHA256 hash.

Idempotent: without `--rotate` or `--reset`, if any admin account already exists,
this command does NOT recreate, reset, or overwrite the account.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.security import (  # noqa: E402
    bootstrap_initial_admin,
    reset_admin_credentials,
    rotate_admin_temporary_password,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FIPP 2.0 Administrator Bootstrap & Credential Handover CLI")
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Generate a fresh temporary one-time password for the initial admin and require first-login change.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Update the single administrator account username and password securely (reads password from FIPP_RESET_ADMIN_PASSWORD, --password-stdin, or prompt).",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Target administrator username when using --reset.",
    )
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read the new administrator password from standard input when using --reset.",
    )
    parser.add_argument(
        "--require-password-change",
        action="store_true",
        help="Require password rotation on next login when using --reset.",
    )
    args = parser.parse_args(argv)

    if args.reset:
        target_username = (args.username or os.environ.get("FIPP_RESET_ADMIN_USERNAME") or "").strip()
        if not target_username:
            raise SystemExit("Administrator username is required with --reset (--username or FIPP_RESET_ADMIN_USERNAME).")
        if args.password_stdin:
            target_password = sys.stdin.readline().rstrip("\r\n")
        else:
            env_pwd = os.environ.get("FIPP_RESET_ADMIN_PASSWORD", "")
            target_password = env_pwd if env_pwd else getpass.getpass("New Administrator Password: ")
        if not target_password:
            raise SystemExit("Administrator password cannot be empty.")

        res = reset_admin_credentials(
            new_username=target_username,
            new_password=target_password,
            require_password_change=args.require_password_change,
        )
        print(
            f"[OK] Administrator credentials reset cleanly for '{res['username']}' "
            f"(role={res['role']}, must_change_password={res['must_change_password']}, "
            f"accounts={res['account_count']})."
        )
        return 0

    result = rotate_admin_temporary_password() if args.rotate else bootstrap_initial_admin()
    if result.get("created") or result.get("rotated"):
        action_label = "CREDENTIAL ROTATION COMPLETED" if result.get("rotated") else "INITIAL ADMINISTRATOR BOOTSTRAP COMPLETED"
        print("=================================================================")
        print(f"FIPP 2.0 {action_label}")
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
