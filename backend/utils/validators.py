"""
File Validation Utilities for Security & Reliability.
Checks supported extensions, file size limits, and sanitizes filenames.
"""

import os
from fastapi import HTTPException, UploadFile
from backend.utils.security import validate_upload_content

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit

def validate_uploaded_file(file: UploadFile, file_bytes: bytes) -> str:
    """
    Validates file extension, non-emptiness, size limit, content parsing, and sanitizes filename.
    Backward-compatible wrapper for validate_upload_content.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail={"error": True, "message": "No file was uploaded.", "code": "NO_FILE"}
        )

    filename = file.filename
    # validate_upload_content raises HTTPException with detailed dict
    sanitized_filename, _ = validate_upload_content(filename, file_bytes)
    return sanitized_filename

