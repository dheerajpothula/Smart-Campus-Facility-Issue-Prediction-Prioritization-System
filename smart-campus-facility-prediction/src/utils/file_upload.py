"""
FIPP Secure File Upload Handler.
Validates uploaded complaint attachments against magic bytes, file size,
path traversal, and image stream corruption. Enforces storage outside the web root.
"""
import hashlib
import io
import os
import re
import secrets
from pathlib import Path
from typing import Any, Tuple, Optional

# Constants
MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB strict limit
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# Magic byte signatures
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC_PREFIX = b"\xff\xd8\xff"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_upload_dir() -> Path:
    """Returns the dedicated uploads directory located outside public web roots."""
    env_dir = os.environ.get("FIPP_UPLOAD_DIR")
    if env_dir:
        target = Path(env_dir).resolve()
    else:
        target = PROJECT_ROOT / "data" / "uploads"
    target.mkdir(parents=True, exist_ok=True)
    return target


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes raw filenames to prevent path traversal, hidden files,
    and special shell characters.
    """
    if not filename:
        return "attachment.jpg"

    # Extract base name only (blocks ../ or ..\ path traversal)
    base = os.path.basename(filename).strip()

    # Prevent hidden files
    base = base.lstrip(".")

    # Separate stem and extension
    name, ext = os.path.splitext(base)
    ext = ext.lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".jpg"

    # Sanitize characters in the stem
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
    clean_stem = re.sub(r"_+", "_", clean_stem).strip("_")

    if not clean_stem:
        clean_stem = "photo"

    return f"{clean_stem[:40]}{ext}"


def generate_secure_upload_filename(token: str, original_filename: str) -> str:
    """
    Generates a cryptographically random, collision-free filename
    bound to the complaint token.
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".jpg"

    clean_token = re.sub(r"[^a-zA-Z0-9_\-]", "", token or "CMP")
    random_entropy = secrets.token_hex(6)
    return f"{clean_token}_{random_entropy}{ext}"


def validate_image_content(file_bytes: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> Tuple[bool, Optional[str]]:
    """
    Validates file content using size, magic bytes signature, and image structure parsing.
    Prevents disguised executables, HTML polyglots, and corrupted payloads.

    Returns:
        (is_valid, error_message)
    """
    # 1. Size bounds check
    if not file_bytes:
        return False, "File is empty (0 bytes)."

    if len(file_bytes) > max_bytes:
        size_mb = len(file_bytes) / (1024 * 1024)
        return False, f"File exceeds the maximum 10MB limit (provided {size_mb:.2f} MB)."

    # 2. Magic bytes check
    is_png = file_bytes.startswith(PNG_MAGIC)
    is_jpeg = file_bytes.startswith(JPEG_MAGIC_PREFIX)

    if not (is_png or is_jpeg):
        return False, "Invalid image format. Only authentic PNG and JPEG images are accepted."

    # 3. Image stream decoding check via Pillow
    try:
        from PIL import Image

        img_stream = io.BytesIO(file_bytes)
        with Image.open(img_stream) as img:
            img.verify()  # Verifies header integrity without loading full raster to memory
            if img.format not in ("PNG", "JPEG"):
                return False, f"File content declared as {img.format}, but only PNG/JPEG are permitted."
    except Exception as exc:
        return False, f"Image decoding verification failed: {exc}"

    return True, None


def process_and_save_upload(
    uploaded_file: Any,
    token: str = "CMP",
    upload_dir: Optional[Path] = None,
) -> Tuple[bool, str, Optional[dict]]:
    """
    Complete secure upload pipeline:
    - Reads buffer without exceeding limit.
    - Runs magic bytes and Pillow structure checks.
    - Generates randomized filename bound to complaint token.
    - Saves strictly inside upload_dir with path traversal verification.

    Returns:
        (success, message, metadata_dict)
    """
    if uploaded_file is None:
        return False, "No file provided.", None

    target_dir = (upload_dir or get_upload_dir()).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    # Read bytes safely
    try:
        if hasattr(uploaded_file, "getvalue"):
            file_bytes = uploaded_file.getvalue()
            orig_name = getattr(uploaded_file, "name", "upload.jpg")
        elif hasattr(uploaded_file, "read"):
            file_bytes = uploaded_file.read()
            orig_name = getattr(uploaded_file, "name", "upload.jpg")
        elif isinstance(uploaded_file, bytes):
            file_bytes = uploaded_file
            orig_name = "upload.jpg"
        else:
            return False, "Unsupported file upload object.", None
    except Exception as exc:
        return False, f"Failed to read upload stream: {exc}", None

    # Validate content
    is_valid, err = validate_image_content(file_bytes)
    if not is_valid:
        return False, err or "Validation failed.", None

    # Generate secure name
    secure_name = generate_secure_upload_filename(token, orig_name)
    sanitized_original = sanitize_filename(orig_name)
    destination_path = target_dir / secure_name

    # Path traversal safety assertion
    try:
        resolved_dest = destination_path.resolve()
        resolved_target = target_dir.resolve()
        # Ensure destination is strictly inside target directory
        if not str(resolved_dest).startswith(str(resolved_target)):
            return False, "Security violation: Path traversal attempt detected.", None
    except Exception as exc:
        return False, f"Filesystem resolution error: {exc}", None

    # Write file
    try:
        with open(destination_path, "wb") as f:
            f.write(file_bytes)
    except Exception as exc:
        return False, f"Failed to persist file to disk: {exc}", None

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    metadata = {
        "stored_filename": secure_name,
        "original_filename": sanitized_original,
        "file_path": str(destination_path),
        "file_size": len(file_bytes),
        "sha256": sha256_hash,
    }

    return True, "File successfully validated and saved.", metadata
