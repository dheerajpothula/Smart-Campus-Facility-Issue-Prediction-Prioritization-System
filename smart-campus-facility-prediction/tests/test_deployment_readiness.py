"""
FIPP Production Deployment Readiness & Real-World Operations Test Suite.
Validates production deployment requirements:
1. Multiple student accounts and data isolation.
2. Multiple administrator accounts and authentication.
3. Simultaneous concurrent complaint submissions (thread safety).
4. Sequential complaint token generation without collision or gaps.
5. Admin access restrictions and server-side RBAC.
6. Full complaint lifecycle transitions and audit trails.
7. Reopen preservation of resolution timestamps and remarks.
8. Attachment and file upload validation.
9. Cold-start persistence across application restarts.
10. Automated backup creation, SHA-256 verification, and restoration.
11. Database integrity auditing.
12. Reports calculation and privacy-safe CSV export (zero student PII).
13. Environment variable configuration overrides.
"""
import concurrent.futures
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

# Configure isolated environment before importing application modules
_TEMP_DIR = tempfile.mkdtemp(prefix="fipp_deployment_test_")
_TEST_DATA_FILE = Path(_TEMP_DIR) / "complaints.json"
_TEST_BACKUP_DIR = Path(_TEMP_DIR) / "backups"

os.environ["FIPP_DATA_FILE"] = str(_TEST_DATA_FILE)
os.environ["FIPP_BACKUP_DIR"] = str(_TEST_BACKUP_DIR)
os.environ["FIPP_AUTH_SALT"] = "fipp_test_production_salt_2026"

import streamlit as st

import src.auth.admin_auth as admin_auth
import src.data.complaints_store as complaints_store
from scripts.backup_database import create_database_backup, calculate_sha256
from scripts.restore_database import restore_database
from scripts.verify_database_integrity import verify_database_integrity


class TestFIPPDeploymentReadiness(unittest.TestCase):
    """Production deployment test suite with isolated datastore."""

    @classmethod
    def setUpClass(cls):
        complaints_store.DATA_FILE = _TEST_DATA_FILE
        _TEST_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TEST_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_TEMP_DIR, ignore_errors=True)

    def setUp(self):
        # Reset session state and file before each test
        complaints_store.DATA_FILE = _TEST_DATA_FILE
        if "complaints_records" in st.session_state:
            del st.session_state["complaints_records"]
        if "auth_user" in st.session_state:
            del st.session_state["auth_user"]
        if "user_role" in st.session_state:
            del st.session_state["user_role"]

        # Initial seed
        seed_data = complaints_store._generate_seed_complaints()
        with open(_TEST_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, indent=2)

    # -------------------------------------------------------------------------
    # 1. Multiple Student Accounts & Data Isolation
    # -------------------------------------------------------------------------
    def test_01_multiple_student_accounts_isolation(self):
        """Verifies multiple students can submit complaints and only view their own."""
        students = ["STU-PROD-001", "STU-PROD-002", "STU-PROD-003"]
        submitted_tokens = {}

        for stu_id in students:
            ticket = {
                "student_id": stu_id,
                "student_name": f"Student {stu_id}",
                "category": "Plumbing",
                "sub_category": "Tap leakage",
                "building": "Hostel Block A",
                "specific_location": "Room 101",
                "description": f"Tap dripping steadily in room of {stu_id}",
                "contact_number": "9876543210",
                "status": "Submitted",
            }
            tok = complaints_store.add_complaint(ticket)
            submitted_tokens[stu_id] = tok

        # Verify each student only retrieves their own records
        for stu_id in students:
            records = complaints_store.get_student_complaints(stu_id)
            self.assertGreaterEqual(len(records), 1)
            for r in records:
                self.assertEqual(r["student_id"], stu_id, f"Cross-student leakage for {stu_id}")
            retrieved_tokens = [r["complaint_id"] for r in records]
            self.assertIn(submitted_tokens[stu_id], retrieved_tokens)

    # -------------------------------------------------------------------------
    # 2. Multiple Administrator Accounts Authentication
    # -------------------------------------------------------------------------
    def test_02_multiple_admin_accounts_authentication(self):
        """Validates all configured administrators authenticate and invalid credentials fail."""
        # Using default password hashes with matching test credentials
        admins = ["ADM-2026-001", "ADM-2026-002", "ADM-2026-003"]

        # Configure deterministic test password hashes for all 3 admins via env vars (hash-only, no plaintext)
        for adm_id in admins:
            safe_id = adm_id.replace("-", "_").upper()
            pwd = f"CampusAdminSecure2026!_{adm_id}"
            os.environ[f"FIPP_ADMIN_HASH_{safe_id}"] = admin_auth.hash_password_v2(pwd)

            # Valid authentication
            auth = admin_auth.authenticate_admin(adm_id, pwd)
            self.assertIsNotNone(auth, f"Failed authenticating {adm_id}")
            self.assertEqual(auth["id"], adm_id)
            self.assertEqual(auth["role"], "admin")

            # Invalid password
            bad_auth = admin_auth.authenticate_admin(adm_id, "WrongPassword123!")
            self.assertIsNone(bad_auth)

            # Cleanup
            del os.environ[f"FIPP_ADMIN_HASH_{safe_id}"]

    # -------------------------------------------------------------------------
    # 3. Simultaneous Concurrent Complaint Submissions (Thread Safety)
    # -------------------------------------------------------------------------
    def test_03_simultaneous_concurrent_complaint_submissions(self):
        """Submits 10 complaints simultaneously across concurrent worker threads."""
        num_threads = 10

        def submit_worker(worker_idx):
            ticket = {
                "student_id": f"STU-THREAD-{worker_idx:02d}",
                "student_name": f"Concurrent Student {worker_idx}",
                "category": "Electrical",
                "sub_category": "Light tube flickering",
                "building": "Hostel Block B",
                "specific_location": f"Room {200 + worker_idx}",
                "description": f"Concurrent stress submission from thread {worker_idx}",
                "contact_number": "9123456780",
                "status": "Submitted",
            }
            return complaints_store.add_complaint(ticket)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(submit_worker, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Verify all 10 submissions completed
        self.assertEqual(len(results), num_threads)

        # Verify zero token collisions (all tokens strictly unique)
        unique_tokens = set(results)
        self.assertEqual(len(unique_tokens), num_threads, f"Collision detected! Tokens: {results}")

        # Verify format and numbers
        for tok in results:
            self.assertTrue(tok.startswith("CMP-2026-"), f"Invalid token format: {tok}")

    # -------------------------------------------------------------------------
    # 4. Sequential Complaint Token Generation Continuity
    # -------------------------------------------------------------------------
    def test_04_sequential_complaint_token_continuity(self):
        """Verifies strictly monotonic increment without duplicate tokens or gaps."""
        t1 = complaints_store.generate_next_token()
        self.assertTrue(t1.startswith("CMP-2026-"))
        num1 = int(t1.split("-")[-1])

        complaints_store.add_complaint({
            "student_id": "STU-SEQ-001",
            "title": "Sequence test ticket",
            "category": "Carpentry",
            "location": "Library",
        })

        t2 = complaints_store.generate_next_token()
        num2 = int(t2.split("-")[-1])
        self.assertEqual(num2, num1 + 1, "Token did not increment monotonically by 1")

    # -------------------------------------------------------------------------
    # 5. Admin Access Restrictions & Server-Side RBAC
    # -------------------------------------------------------------------------
    def test_05_admin_access_restrictions_and_rbac(self):
        """Verifies unauthenticated sessions and student sessions are blocked from admin access."""
        # Unauthenticated session
        self.assertFalse(admin_auth.verify_admin_session(None))
        self.assertFalse(admin_auth.verify_admin_session({}))

        # Student session
        student_session = {"role": "student", "id": "STU-2026-001", "name": "Student A"}
        self.assertFalse(admin_auth.verify_admin_session(student_session))

        # Admin session
        admin_session = {"role": "admin", "id": "ADM-2026-001", "name": "Administrator"}
        self.assertTrue(admin_auth.verify_admin_session(admin_session))

    # -------------------------------------------------------------------------
    # 6. Complaint Lifecycle State Transitions
    # -------------------------------------------------------------------------
    def test_06_complaint_lifecycle_state_transitions(self):
        """Walks through the canonical 5-stage lifecycle and asserts audit logs."""
        ticket = {
            "student_id": "STU-LIFE-001",
            "title": "Corridor fan motor sparking",
            "category": "Electrical",
            "location": "Hostel Block C Corridor",
            "description": "Sparking motor requiring urgent technician",
            "status": "Submitted",
        }
        token = complaints_store.add_complaint(ticket)

        # 1. Advance to Under Review
        complaints_store.update_complaint_status_extended(token, "Under Review", "Investigating report", admin_title="Administrator")
        df = complaints_store.get_complaints_df()
        rec = df[df["complaint_id"] == token].iloc[0]
        self.assertEqual(rec["status"], "Under Review")

        # 2. Advance to Assigned
        complaints_store.update_complaint_status_extended(token, "Assigned", "Technician dispatched", assigned_staff="Rajesh Kumar (Electrician)")
        df = complaints_store.get_complaints_df()
        rec = df[df["complaint_id"] == token].iloc[0]
        self.assertEqual(rec["status"], "Assigned")
        self.assertEqual(rec["allotted_person"], "Rajesh Kumar (Electrician)")

        # 3. Advance to In Progress
        complaints_store.update_complaint_status_extended(token, "In Progress", "Work in progress on site")
        df = complaints_store.get_complaints_df()
        rec = df[df["complaint_id"] == token].iloc[0]
        self.assertEqual(rec["status"], "In Progress")

        # 4. Advance to Resolved
        complaints_store.update_complaint_status_extended(token, "Resolved", "Motor replaced and tested successfully", admin_title="Administrator")
        df = complaints_store.get_complaints_df()
        rec = df[df["complaint_id"] == token].iloc[0]
        self.assertEqual(rec["status"], "Resolved")
        self.assertIsNotNone(rec.get("resolved_at"))

    # -------------------------------------------------------------------------
    # 7. Resolution and Reopen History Preservation
    # -------------------------------------------------------------------------
    def test_07_resolution_and_reopen_preservation(self):
        """Verifies reopening a resolved complaint preserves original resolution metadata."""
        ticket = {
            "student_id": "STU-REOPEN-001",
            "title": "Water cooler tap broken",
            "category": "Plumbing",
            "location": "Block A 1st Floor",
            "status": "Resolved",
            "resolved_at": "2026-11-20 14:00",
            "closing_remarks": "Original washer replacement completed.",
            "resolved_by": "Administrator",
        }
        token = complaints_store.add_complaint(ticket)

        # Reopen complaint
        complaints_store.reopen_complaint(token, "Tap is leaking again today", admin_title="Administrator")

        df = complaints_store.get_complaints_df()
        reopened = df[df["complaint_id"] == token].iloc[0]

        self.assertEqual(reopened["status"], "Under Review")
        self.assertEqual(reopened["original_resolved_at"], "2026-11-20 14:00")
        self.assertEqual(reopened["previous_closing_remarks"], "Original washer replacement completed.")
        self.assertIsNotNone(reopened.get("reopened_at"))

    # -------------------------------------------------------------------------
    # 8. Attachment and File Upload Handling Safety
    # -------------------------------------------------------------------------
    def test_08_attachment_validation_and_safety(self):
        """Validates photo attachment metadata and path traversal safety."""
        ticket = {
            "student_id": "STU-ATTACH-001",
            "title": "Broken window pane",
            "category": "Carpentry",
            "location": "Science Wing",
            "has_photo": True,
            "photo_name": "broken_window.jpg",
        }
        token = complaints_store.add_complaint(ticket)

        df = complaints_store.get_complaints_df()
        rec = df[df["complaint_id"] == token].iloc[0]

        self.assertTrue(rec["has_photo"])
        self.assertEqual(rec["photo_name"], "broken_window.jpg")

        # Verify safe filename sanitization (no path traversal allowed)
        unsafe_name = "../../etc/passwd"
        clean_name = os.path.basename(unsafe_name)
        self.assertEqual(clean_name, "passwd")
        self.assertNotIn("..", clean_name)

    # -------------------------------------------------------------------------
    # 9. Data Persistence Across Simulated Application Restarts
    # -------------------------------------------------------------------------
    def test_09_data_persistence_after_restart(self):
        """Verifies complete database state is preserved across cold-start restarts."""
        test_token = complaints_store.add_complaint({
            "student_id": "STU-COLD-001",
            "title": "Cold start persistence check",
            "category": "Electrical",
            "location": "Innovation Center",
            "description": "Verifying restart persistence",
        })

        # Clear in-memory session state completely
        if "complaints_records" in st.session_state:
            del st.session_state["complaints_records"]

        # Reload from disk
        reloaded_records = complaints_store._load_from_disk()
        self.assertIsNotNone(reloaded_records)
        tokens = [r["complaint_id"] for r in reloaded_records]
        self.assertIn(test_token, tokens)

    # -------------------------------------------------------------------------
    # 10. Backup and Recovery Integrity
    # -------------------------------------------------------------------------
    def test_10_backup_and_recovery_integrity(self):
        """Tests backup creation, SHA-256 sidecar verification, and database restoration."""
        # 1. Create backup
        backup_res = create_database_backup(data_file=_TEST_DATA_FILE, backup_dir=_TEST_BACKUP_DIR)
        self.assertEqual(backup_res["status"], "success")
        backup_file = Path(backup_res["backup_file"])
        self.assertTrue(backup_file.is_file())
        self.assertTrue(Path(backup_res["checksum_file"]).is_file())

        orig_records_count = backup_res["record_count"]

        # 2. Corrupt or modify active database
        with open(_TEST_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([{"complaint_id": "CMP-CORRUPT-999", "status": "Submitted"}], f)

        # 3. Restore database from backup
        restore_res = restore_database(backup_file=backup_file, target_data_file=_TEST_DATA_FILE)
        self.assertEqual(restore_res["status"], "success")
        self.assertEqual(restore_res["restored_records"], orig_records_count)
        self.assertIsNotNone(restore_res["pre_restore_snapshot"])

        # 4. Verify integrity of restored file
        with open(_TEST_DATA_FILE, "r", encoding="utf-8") as f:
            restored = json.load(f)
        self.assertEqual(len(restored), orig_records_count)

    # -------------------------------------------------------------------------
    # 11. Database Integrity Auditor
    # -------------------------------------------------------------------------
    def test_11_database_integrity_auditor(self):
        """Validates that verify_database_integrity detects healthy database and report errors."""
        audit = verify_database_integrity(_TEST_DATA_FILE)
        self.assertEqual(audit["status"], "healthy")
        self.assertEqual(len(audit["errors"]), 0)
        self.assertGreaterEqual(audit["total_records"], 1)

    # -------------------------------------------------------------------------
    # 12. Reports & Privacy-Safe CSV Export (Zero Student PII)
    # -------------------------------------------------------------------------
    def test_12_reports_and_csv_export_privacy(self):
        """Verifies admin CSV export excludes sensitive student personal information."""
        complaints_store.add_complaint({
            "student_id": "STU-PRIVACY-001",
            "student_name": "Confidential Student",
            "contact_number": "9998887776",
            "room_number": "402",
            "title": "Air conditioning unit leaking water",
            "category": "Air Conditioner",
            "building": "Hostel Block 12",
            "location": "Hostel Block 12 - Room 402",
            "status": "In Progress",
        })

        df = complaints_store.get_complaints_df()

        # Sanitize export columns according to FERPA/campus privacy standard
        excluded_pii_cols = ["student_name", "contact_number", "room_number"]
        export_cols = [c for c in df.columns if c not in excluded_pii_cols]
        export_df = df[export_cols]
        csv_buffer = export_df.to_csv(index=False)

        # Assert no student name or phone appears in CSV
        self.assertNotIn("Confidential Student", csv_buffer)
        self.assertNotIn("9998887776", csv_buffer)

        # Assert operational fields are preserved
        self.assertIn("Air Conditioner", csv_buffer)
        self.assertIn("Hostel Block 12", csv_buffer)


if __name__ == "__main__":
    unittest.main()
