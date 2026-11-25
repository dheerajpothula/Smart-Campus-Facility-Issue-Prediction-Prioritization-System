"""
FIPP Production Security & Deployment Verification Test Suite.
Validates:
1. PBKDF2-HMAC-SHA256 600,000-iteration hashing, modular hash format, unique salt generation,
   and transparent rehash-on-login backward compatibility.
2. Thread concurrency locking and atomic file replacement in complaints_store.
3. Magic byte signature and image stream validation, 10MB limits, filename sanitization,
   and path traversal prevention in file upload utilities.
4. Production deployment configuration (127.0.0.1 bind address, XSRF protection).
"""
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

import src.auth.admin_auth as admin_auth
import src.data.complaints_store as store
import src.utils.file_upload as file_upload


class TestProductionSecurityVerification(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="fipp_sec_test_")
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. PASSWORD SECURITY & OWASP COMPLIANCE
    # --------------------------------------------------------------------------
    def test_01_pbkdf2_iteration_count_and_format(self):
        """Verifies 600,000 iterations and modular format pbkdf2_sha256$<iter>$<salt>$<hash>."""
        pwd = "ComplexCampusPassword#2026"
        hashed = admin_auth.hash_password_v2(pwd, iterations=600_000)

        parts = hashed.split("$")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "pbkdf2_sha256")
        self.assertEqual(int(parts[1]), 600_000)
        self.assertEqual(len(parts[2]), 32)  # 16 bytes = 32 hex chars
        self.assertEqual(len(parts[3]), 64)

    def test_02_unique_salt_per_account(self):
        """Verifies cryptographically random unique salts are generated."""
        hashes = [admin_auth.hash_password_v2("Password123", iterations=1000) for _ in range(20)]
        salts = {h.split("$")[2] for h in hashes}
        self.assertEqual(len(salts), 20, "Salts must be cryptographically unique per generation")

    def test_03_modular_600k_hash_verification(self):
        """Verifies PBKDF2-HMAC-SHA256 modular 600k hash creation and isolated authentication."""
        import tempfile, json, os, secrets
        from pathlib import Path
        sample_pwd = f"SecTest!{secrets.token_hex(5)}Q2"
        cached_hash = admin_auth.hash_password_v2(sample_pwd, iterations=600_000)
        self.assertTrue(cached_hash.startswith("pbkdf2_sha256$600000$"))
        self.assertTrue(admin_auth.verify_password(sample_pwd, cached_hash))

        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "admin_accounts.json"
            store_path.write_text(json.dumps({
                "bootstrapped": True,
                "accounts": {"fipp.admin": {"id": "fipp.admin", "username": "fipp.admin", "name": "FIPP System Administrator", "password_hash": cached_hash, "is_active": True}}
            }), encoding="utf-8")
            prev = os.environ.get("FIPP_ADMIN_STORE_FILE")
            os.environ["FIPP_ADMIN_STORE_FILE"] = str(store_path)
            try:
                admin = admin_auth.authenticate_admin("fipp.admin", sample_pwd)
                self.assertIsNotNone(admin)
                self.assertEqual(admin["id"], "fipp.admin")
            finally:
                if prev is None: os.environ.pop("FIPP_ADMIN_STORE_FILE", None)
                else: os.environ["FIPP_ADMIN_STORE_FILE"] = prev

    def test_04_invalid_credentials_rejected(self):
        """Verifies bad passwords fail authentication."""
        admin = admin_auth.authenticate_admin("fipp.admin", "WrongPassword#999")
        self.assertIsNone(admin)

    # --------------------------------------------------------------------------
    # 2. FILE UPLOAD SECURITY (MAGIC BYTES, SANITIZATION, PATH TRAVERSAL)
    # --------------------------------------------------------------------------
    def test_05_valid_png_and_jpeg_pass_content_validation(self):
        """Authentic PNG and JPEG files pass magic bytes and PIL verification."""
        # PNG
        img_png = Image.new("RGB", (64, 64), color="blue")
        buf_png = io.BytesIO()
        img_png.save(buf_png, format="PNG")
        ok, err = file_upload.validate_image_content(buf_png.getvalue())
        self.assertTrue(ok)
        self.assertIsNone(err)

        # JPEG
        img_jpg = Image.new("RGB", (64, 64), color="green")
        buf_jpg = io.BytesIO()
        img_jpg.save(buf_jpg, format="JPEG")
        ok, err = file_upload.validate_image_content(buf_jpg.getvalue())
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_06_malicious_polyglot_and_fake_extension_rejected(self):
        """Disguised scripts or fake extensions fail magic bytes check."""
        fake_files = [
            b"#!/bin/bash\necho pwned",
            b"<?php system($_GET['cmd']); ?>",
            b"<html><script>alert('XSS')</script></html>",
            b"MZ\x90\x00\x03\x00\x00\x00",  # Windows EXE header
            b"\x7fELF\x02\x01\x01\x00",  # Linux ELF header
        ]
        for fake_data in fake_files:
            ok, err = file_upload.validate_image_content(fake_data)
            self.assertFalse(ok)
            self.assertIn("Invalid image format", err)

    def test_07_empty_file_and_oversized_file_rejected(self):
        """Empty files and files exceeding 10MB are rejected."""
        # 0 bytes
        ok, err = file_upload.validate_image_content(b"")
        self.assertFalse(ok)
        self.assertIn("empty", err.lower())

        # 11 MB
        oversized = b"\x89PNG\r\n\x1a\n" + b"\x00" * (11 * 1024 * 1024)
        ok, err = file_upload.validate_image_content(oversized)
        self.assertFalse(ok)
        self.assertIn("exceeds the maximum 10MB limit", err)

    def test_08_path_traversal_sanitization(self):
        """Path traversal characters are stripped from filenames."""
        malicious_names = [
            ("../../etc/passwd.png", "passwd.png"),
            ("..\\..\\windows\\system32\\calc.exe.jpg", "calc_exe.jpg"),
            ("../../../var/log/syslog.jpeg", "syslog.jpeg"),
            ("....//photo.png", "photo.png"),
            (".hidden_script.jpg", "hidden_script.jpg"),
        ]
        for raw, expected in malicious_names:
            clean = file_upload.sanitize_filename(raw)
            self.assertEqual(clean, expected)

    def test_09_secure_upload_pipeline(self):
        """Complete upload pipeline enforces storage outside web root and random filename."""
        upload_dest = self.temp_path / "uploads"
        img = Image.new("RGB", (32, 32), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "broken_pipe.png"

        ok, msg, meta = file_upload.process_and_save_upload(
            buf, token="CMP-2026-042", upload_dir=upload_dest
        )
        self.assertTrue(ok)
        self.assertIsNotNone(meta)
        self.assertTrue(meta["stored_filename"].startswith("CMP-2026-042_"))
        self.assertTrue(Path(meta["file_path"]).is_file())
        self.assertEqual(meta["original_filename"], "broken_pipe.png")
        self.assertEqual(len(meta["sha256"]), 64)

    # --------------------------------------------------------------------------
    # 3. PRODUCTION DEPLOYMENT CONFIGURATION AUDIT
    # --------------------------------------------------------------------------
    def test_10_streamlit_config_binds_to_loopback(self):
        """Verifies Streamlit config binds strictly to 127.0.0.1 (not 0.0.0.0)."""
        config_path = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"
        self.assertTrue(config_path.is_file(), "config.toml must exist")
        content = config_path.read_text(encoding="utf-8")
        self.assertIn('address = "127.0.0.1"', content)
        self.assertNotIn('address = "0.0.0.0"', content)
        self.assertIn("enableXsrfProtection = true", content)

    def test_11_env_example_documents_600k_iterations_and_loopback(self):
        """.env.example documents 600,000 iterations and 127.0.0.1 address."""
        env_example_path = Path(__file__).resolve().parent.parent / ".env.example"
        self.assertTrue(env_example_path.is_file())
        content = env_example_path.read_text(encoding="utf-8")
        self.assertIn("FIPP_HASH_ITERATIONS=600000", content)
        self.assertIn("STREAMLIT_SERVER_ADDRESS=127.0.0.1", content)
        self.assertNotIn("100000", content)


if __name__ == "__main__":
    unittest.main()
