"""
FIPP 2.0 — Secure File Upload API Routes.
Validates uploaded photo attachments against binary magic bytes (PNG/JPEG),
Pillow raster corruption checks, 10MB size limit, and path traversal vulnerabilities.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.config import UPLOAD_DIR
from app.services.upload_service import upload_service

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


@router.post("/photo")
async def upload_complaint_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Validates and securely persists a complaint photo attachment.
    Enforces authentic PNG/JPEG magic bytes, raster structure checks, and 10MB limit.
    """
    content = await file.read()

    # 1. Validate magic bytes and image integrity
    is_valid, error_msg = upload_service.validate_image_bytes(content)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg or "Uploaded file failed security validation.",
        )

    # 2. Persist with randomized safe filename
    filename, sha256_hash, file_path = upload_service.save_file(content, file.filename or "attachment.jpg")

    return {
        "success": True,
        "original_filename": file.filename,
        "stored_filename": filename,
        "sha256": sha256_hash,
        "size_bytes": len(content),
        "message": "Photo attachment verified and stored securely.",
    }


@router.get("/{filename}")
def get_uploaded_photo(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves an authenticated attachment file safely, preventing directory traversal.
    """
    safe_name = Path(filename).name
    file_path = UPLOAD_DIR / safe_name

    if not file_path.is_file() or not str(file_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested attachment does not exist.",
        )

    ext = safe_name.lower().split(".")[-1]
    media_type = "image/png" if ext == "png" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)
