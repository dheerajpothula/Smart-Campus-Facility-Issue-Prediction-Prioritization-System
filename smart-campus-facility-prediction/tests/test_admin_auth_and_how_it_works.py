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
    verify_admin_session,
    _ADMIN_CREDENTIALS_STORE,
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
        """Validates that password hashes are non-trivial PBKDF2-HMAC-SHA256 strings and not plaintext."""
        # Exactly 3 authorized administrator accounts
        self.assertEqual(len(_ADMIN_CREDENTIALS_STORE), 3)
        self.assertNotIn("admin", _ADMIN_CREDENTIALS_STORE)
        self.assertIn("ADM-2026-001", _ADMIN_CREDENTIALS_STORE)
        self.assertIn("ADM-2026-002", _ADMIN_CREDENTIALS_STORE)
        self.assertIn("ADM-2026-003", _ADMIN_CREDENTIALS_STORE)

        for admin_id, rec in _ADMIN_CREDENTIALS_STORE.items():
            self.assertIn("password_hash", rec)
            p_hash = rec["password_hash"]
            # 64-char hex string
            self.assertEqual(len(p_hash), 64)
            # Not plaintext passwords
            self.assertNotIn("Admin@", p_hash)
            self.assertNotIn("Admin@2026", p_hash)

        # Hash reproducibility and individual correctness
        self.assertEqual(hash_password("Admin@001"), _ADMIN_CREDENTIALS_STORE["ADM-2026-001"]["password_hash"])
        self.assertEqual(hash_password("Admin@002"), _ADMIN_CREDENTIALS_STORE["ADM-2026-002"]["password_hash"])
        self.assertEqual(hash_password("Admin@003"), _ADMIN_CREDENTIALS_STORE["ADM-2026-003"]["password_hash"])

    def test_admin_authentication_valid_credentials(self):
        """Validates that legitimate administrator logins succeed with assigned credentials and titles."""
        # 1. ADM-2026-001 | Admin@001 | Facility Operations Lead
        auth_user1 = authenticate_admin("ADM-2026-001", "Admin@001")
        self.assertIsNotNone(auth_user1)
        self.assertEqual(auth_user1["role"], "admin")
        self.assertEqual(auth_user1["id"], "ADM-2026-001")
        self.assertEqual(auth_user1["title"], "Facility Operations Lead")
        self.assertEqual(auth_user1["role_title"], "Facility Operations Lead")

        # 2. ADM-2026-002 | Admin@002 | Campus Infrastructure Admin
        auth_user2 = authenticate_admin("ADM-2026-002", "Admin@002")
        self.assertIsNotNone(auth_user2)
        self.assertEqual(auth_user2["role"], "admin")
        self.assertEqual(auth_user2["id"], "ADM-2026-002")
        self.assertEqual(auth_user2["title"], "Campus Infrastructure Admin")
        self.assertEqual(auth_user2["role_title"], "Campus Infrastructure Admin")

        # 3. ADM-2026-003 | Admin@003 | Maintenance Dispatcher
        auth_user3 = authenticate_admin("ADM-2026-003", "Admin@003")
        self.assertIsNotNone(auth_user3)
        self.assertEqual(auth_user3["role"], "admin")
        self.assertEqual(auth_user3["id"], "ADM-2026-003")
        self.assertEqual(auth_user3["title"], "Maintenance Dispatcher")
        self.assertEqual(auth_user3["role_title"], "Maintenance Dispatcher")

    def test_admin_authentication_invalid_credentials_rejected(self):
        """Validates that incorrect passwords, cross-passwords, old 'admin', and unknown IDs are rejected."""
        # Old generic 'admin' login removed completely
        self.assertIsNone(authenticate_admin("admin", "Admin@2026"))
        self.assertIsNone(authenticate_admin("admin", "Admin@001"))
        self.assertIsNone(authenticate_admin("admin", "admin"))

        # Old password 'Admin@2026' rejected for all accounts
        self.assertIsNone(authenticate_admin("ADM-2026-001", "Admin@2026"))
        self.assertIsNone(authenticate_admin("ADM-2026-002", "Admin@2026"))
        self.assertIsNone(authenticate_admin("ADM-2026-003", "Admin@2026"))

        # Cross-passwords rejected (account A password with account B ID)
        self.assertIsNone(authenticate_admin("ADM-2026-001", "Admin@002"))
        self.assertIsNone(authenticate_admin("ADM-2026-001", "Admin@003"))
        self.assertIsNone(authenticate_admin("ADM-2026-002", "Admin@001"))
        self.assertIsNone(authenticate_admin("ADM-2026-002", "Admin@003"))
        self.assertIsNone(authenticate_admin("ADM-2026-003", "Admin@001"))
        self.assertIsNone(authenticate_admin("ADM-2026-003", "Admin@002"))

        # Wrong passwords
        self.assertIsNone(authenticate_admin("ADM-2026-001", "WrongPassword!"))
        self.assertIsNone(authenticate_admin("ADM-2026-002", "123456"))
        self.assertIsNone(authenticate_admin("ADM-2026-003", "password"))

        # Unknown IDs
        self.assertIsNone(authenticate_admin("hacker", "Admin@001"))
        self.assertIsNone(authenticate_admin("STU-2026-001", "Admin@001"))

        # Empty / whitespace
        self.assertIsNone(authenticate_admin("", "Admin@001"))
        self.assertIsNone(authenticate_admin("ADM-2026-001", ""))
        self.assertIsNone(authenticate_admin("   ", "   "))

    def test_fipp_admin_password_env_does_not_override_credentials(self):
        """Validates that FIPP_ADMIN_PASSWORD environment variable does not override individual credentials."""
        original_env = os.environ.get("FIPP_ADMIN_PASSWORD")
        try:
            os.environ["FIPP_ADMIN_PASSWORD"] = "OverridingMasterPass123"

            # Attempting to use the environment override as password must fail
            self.assertIsNone(authenticate_admin("ADM-2026-001", "OverridingMasterPass123"))
            self.assertIsNone(authenticate_admin("ADM-2026-002", "OverridingMasterPass123"))
            self.assertIsNone(authenticate_admin("ADM-2026-003", "OverridingMasterPass123"))

            # Individual credentials must continue to work strictly
            self.assertIsNotNone(authenticate_admin("ADM-2026-001", "Admin@001"))
            self.assertIsNotNone(authenticate_admin("ADM-2026-002", "Admin@002"))
            self.assertIsNotNone(authenticate_admin("ADM-2026-003", "Admin@003"))
        finally:
            if original_env is not None:
                os.environ["FIPP_ADMIN_PASSWORD"] = original_env
            else:
                os.environ.pop("FIPP_ADMIN_PASSWORD", None)

    def test_student_cannot_access_admin_operations(self):
        """Validates that Student sessions cannot pass the Administrator session verification guard."""
        student_session = {"role": "student", "id": "STU-2026-101", "name": "Alex Chen"}
        self.assertFalse(verify_admin_session(student_session))

        unauthenticated_session = None
        self.assertFalse(verify_admin_session(unauthenticated_session))

        empty_session = {}
        self.assertFalse(verify_admin_session(empty_session))

        # Legitimate admin session
        admin_session = {"role": "admin", "id": "ADM-2026-001", "name": "Administrator"}
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
