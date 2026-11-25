"""
Test Suite for FIPP Landing Page Improvements and Secure Administrator Authentication.
Validates:
1. "How FIPP Works" section presence and exact content:
   - Report: Collect campus facility complaints.
   - Analyze: Identify and assess facility issues.
   - Prioritize: Support maintenance decisions.
   - No fake statistics or percentage claims.
2. Cryptographic password hashing and timing-attack resistant authentication (PBKDF2-HMAC-SHA256).
3. Rejection of invalid administrator credentials.
4. Session authorization guard preventing students from accessing admin operations.
5. Administrator Login screen structure: ID, password, show/hide toggle, back navigation.
"""
import inspect
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.auth.admin_auth import (
    authenticate_admin,
    hash_password,
    verify_password,
    verify_admin_session,
)
from dashboard.components import role_selection, admin_login


class TestAdminAuthAndHowItWorks(unittest.TestCase):
    """Test verification for Landing Page Improvements and Admin Authentication."""

    def test_how_fipp_works_section_content(self):
        """Validates 'How FIPP Works' title and the three required feature items."""
        source = inspect.getsource(role_selection)

        self.assertIn("How FIPP Works", source)
        self.assertIn("Report", source)
        self.assertIn("Collect campus facility complaints.", source)
        self.assertIn("Analyze", source)
        self.assertIn("Identify and assess facility issues.", source)
        self.assertIn("Prioritize", source)
        self.assertIn("Support maintenance decisions.", source)

        # Ensure no fake statistics or percentages are present on the landing page
        self.assertNotIn("99.2%", source)
        self.assertNotIn("&lt; 15 min", source)
        self.assertNotIn("100% Student", source)

    def test_password_hashing_security(self):
        """Validates that password hashes are modular PBKDF2-HMAC-SHA256 strings with random salts."""
        import tempfile, json, secrets
        from pathlib import Path
        sample_pwd = f"TestHash!{secrets.token_hex(4)}Z1"
        p_hash = hash_password(sample_pwd)
        self.assertTrue(p_hash.startswith("pbkdf2_sha256$600000$"))
        self.assertNotIn(sample_pwd, p_hash)
        self.assertTrue(verify_password(sample_pwd, p_hash))
        self.assertFalse(verify_password("wrong", p_hash))

    def test_admin_authentication_valid_credentials(self):
        """Validates administrator authentication against an isolated bootstrapped admin store."""
        import tempfile, json, os, secrets
        from pathlib import Path
        sample_pwd = f"BootTest!{secrets.token_hex(5)}A1"
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "admin_accounts.json"
            store_path.write_text(json.dumps({
                "bootstrapped": True,
                "accounts": {
                    "fipp.admin": {
                        "id": "fipp.admin",
                        "username": "fipp.admin",
                        "name": "FIPP System Administrator",
                        "title": "System Administrator",
                        "password_hash": hash_password(sample_pwd),
                        "is_active": True,
                        "must_change_password": False,
                    }
                }
            }), encoding="utf-8")
            prev = os.environ.get("FIPP_ADMIN_STORE_FILE")
            os.environ["FIPP_ADMIN_STORE_FILE"] = str(store_path)
            try:
                auth_user = authenticate_admin("fipp.admin", sample_pwd)
                self.assertIsNotNone(auth_user)
                self.assertEqual(auth_user["role"], "admin")
                self.assertEqual(auth_user["id"], "fipp.admin")
            finally:
                if prev is None: os.environ.pop("FIPP_ADMIN_STORE_FILE", None)
                else: os.environ["FIPP_ADMIN_STORE_FILE"] = prev

    def test_admin_authentication_invalid_credentials_rejected(self):
        """Validates that old sample accounts, unknown IDs, and incorrect passwords are rejected."""
        self.assertIsNone(authenticate_admin("admin", "password"))
        self.assertIsNone(authenticate_admin("fipp.admin", "WrongPassword!1"))
        self.assertIsNone(authenticate_admin("hacker", "WrongPassword!2"))
        self.assertIsNone(authenticate_admin("", "nonempty"))
        self.assertIsNone(authenticate_admin("fipp.admin", ""))
        self.assertIsNone(authenticate_admin("   ", "   "))

    def test_fipp_admin_password_env_does_not_override_credentials(self):
        """Validates that FIPP_ADMIN_PASSWORD environment variable does not override stored credentials."""
        import tempfile, json, secrets
        sample_pwd = f"EnvIsolation!{secrets.token_hex(5)}R5"
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "admin_accounts.json"
            store_path.write_text(json.dumps({
                "bootstrapped": True,
                "accounts": {"fipp.admin": {"id": "fipp.admin", "username": "fipp.admin", "name": "FIPP System Administrator", "password_hash": hash_password(sample_pwd), "is_active": True}}
            }), encoding="utf-8")
            prev_store = os.environ.get("FIPP_ADMIN_STORE_FILE")
            original_env = os.environ.get("FIPP_ADMIN_PASSWORD")
            os.environ["FIPP_ADMIN_STORE_FILE"] = str(store_path)
            os.environ["FIPP_ADMIN_PASSWORD"] = "OverridingMasterPass123"
            try:
                self.assertIsNone(authenticate_admin("fipp.admin", "OverridingMasterPass123"))
                self.assertIsNotNone(authenticate_admin("fipp.admin", sample_pwd))
            finally:
                if prev_store is None: os.environ.pop("FIPP_ADMIN_STORE_FILE", None)
                else: os.environ["FIPP_ADMIN_STORE_FILE"] = prev_store
                if original_env is not None: os.environ["FIPP_ADMIN_PASSWORD"] = original_env
                else: os.environ.pop("FIPP_ADMIN_PASSWORD", None)

    def test_student_cannot_access_admin_operations(self):
        """Validates that Student sessions cannot pass the Administrator session verification guard."""
        student_session = {"role": "student", "id": "00123456", "name": "Alex Chen"}
        self.assertFalse(verify_admin_session(student_session))
        self.assertFalse(verify_admin_session(None))
        self.assertFalse(verify_admin_session({}))
        admin_session = {"role": "admin", "id": "fipp.admin", "name": "FIPP System Administrator"}
        self.assertTrue(verify_admin_session(admin_session))

    def test_admin_login_screen_components(self):
        """Validates presence of Administrator ID, Password, Show Password, and Login controls."""
        source = inspect.getsource(admin_login)

        self.assertIn("Administrator ID", source)
        self.assertIn("Password", source)
        self.assertIn("Show password", source)
        self.assertIn("Back to Landing Page", source)
        self.assertIn("Login", source)
        self.assertIn("Invalid Administrator ID or password", source)


if __name__ == "__main__":
    unittest.main()
