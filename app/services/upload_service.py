"""
FIPP 2.0 — Secure File Upload Service.
Validates uploaded complaint attachments against magic bytes, file size,
path traversal, and image stream corruption. Enforces storage outside the web root.
"""
import hashlib
import io
import os
import re
import secrets
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from PIL import Image

from app.core.config import UPLOAD_DIR

MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB strict limit
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# Magic byte signatures
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC_PREFIX = b"\xff\xd8\xff"


class UploadService:
    """Manages secure file validation, sanitization, and disk storage."""

    @staticmethod
    def validate_image_bytes(file_bytes: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> Tuple[bool, Optional[str]]:
        """
        Validates raw file content using size, binary magic bytes signature,
        and image structure parsing.
        """
        if not file_bytes:
            return False, "File is empty (0 bytes)."

        if len(file_bytes) > max_bytes:
            size_mb = len(file_bytes) / (1024 * 1024)
            return False, f"File exceeds maximum 10MB limit (provided {size_mb:.2f} MB)."

        # Binary magic bytes check
        is_png = file_bytes.startswith(PNG_MAGIC)
        is_jpeg = file_bytes.startswith(JPEG_MAGIC_PREFIX)
        if not (is_png or is_jpeg):
            return False, "Invalid image format. Only authentic PNG and JPEG images are allowed."

        # Raster structure verification with Pillow
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
        except Exception as exc:
            return False, f"Corrupted or invalid image stream: {exc}"

        return True, None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes raw filenames to prevent path traversal, hidden files, and shell characters."""
        if not filename:
            return "attachment.jpg"
        base = os.path.basename(filename).strip().lstrip(".")
        name, ext = os.path.splitext(base)
        ext = ext.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            ext = ".jpg"
        clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        clean_stem = re.sub(r"_+", "_", clean_stem).strip("_")
        return f"{clean_stem[:40] or 'photo'}{ext}"

    @classmethod
    def process_and_save_upload(
        cls,
        file_bytes: bytes,
        original_filename: str,
        token_prefix: str = "CMP-PHOTO"
    ) -> Dict[str, Any]:
        """
        Validates, sanitizes, and writes uploaded image bytes to the secure uploads directory.
        """
        is_valid, err = cls.validate_image_bytes(file_bytes)
        if not is_valid:
            return {"success": False, "error": err}

        safe_orig = cls.sanitize_filename(original_filename)
        ext = Path(safe_orig).suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            ext = ".jpg"

        entropy = secrets.token_hex(6)
        clean_token = re.sub(r"[^a-zA-Z0-9_\-]", "", token_prefix or "CMP")
        stored_filename = f"{clean_token}_{entropy}{ext}"
        destination = UPLOAD_DIR / stored_filename

        try:
            with open(destination, "wb") as f:
                f.write(file_bytes)
            sha256 = hashlib.sha256(file_bytes).hexdigest()
            return {
                "success": True,
                "stored_filename": stored_filename,
                "original_filename": safe_orig,
                "sha256": sha256,
                "size_bytes": len(file_bytes),
                "storage_path": str(destination),
            }
        except Exception as exc:
            return {"success": False, "error": f"Failed to persist file to disk: {exc}"}

    @classmethod
    def save_file(cls, file_bytes: bytes, original_filename: str, token_prefix: str = "CMP-PHOTO") -> Tuple[str, str, Path]:
        """Convenience helper to persist image file and return (filename, sha256, path)."""
        res = cls.process_and_save_upload(file_bytes, original_filename, token_prefix)
        if not res["success"]:
            raise ValueError(res.get("error", "Failed to save file."))
        return res["stored_filename"], res["sha256"], Path(res["storage_path"])


upload_service = UploadService()
