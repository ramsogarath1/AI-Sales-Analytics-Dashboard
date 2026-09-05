"""
Storage Service Abstraction for AI-Sales-Analytics-Dashboard.
Manages dataset storage operations (local filesystem by default) with clean abstractions,
safe path checks, and informative handling for ephemeral server environments.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import HTTPException

try:
    from backend.utils.security import sanitize_filename, safe_path_join, make_error_detail
except ImportError:
    from utils.security import sanitize_filename, safe_path_join, make_error_detail

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class StorageService:
    """Storage Service for dataset file operations."""

    @staticmethod
    def get_uploads_dir() -> Path:
        base_dir = Path(os.getenv("STORAGE_DIR", "uploads"))
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    @classmethod
    def save_file(cls, filename: str, file_bytes: bytes) -> Path:
        """Saves file bytes securely to configured storage directory."""
        target_path = safe_path_join(cls.get_uploads_dir(), filename)
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return target_path

    @classmethod
    def read_file(cls, file_path_str: str) -> bytes:
        """
        Reads file bytes from storage.
        Raises 404 HTTPException if missing (e.g. following ephemeral server restarts).
        """
        target_path = Path(file_path_str)
        if not target_path.exists():
            raise HTTPException(
                status_code=404,
                detail=make_error_detail(
                    "Dataset file missing from server storage (ephemeral storage restart). Please re-upload dataset.",
                    "FILE_NOT_FOUND"
                )
            )
        with open(target_path, "rb") as f:
            return f.read()

    @classmethod
    def delete_file(cls, file_path_str: str) -> bool:
        """Safely removes file from storage."""
        if not file_path_str:
            return False
        try:
            target_path = Path(file_path_str)
            if target_path.exists():
                target_path.unlink()
                return True
        except Exception:
            pass
        return False

    @classmethod
    def file_exists(cls, file_path_str: str) -> bool:
        """Checks if file exists in storage."""
        return Path(file_path_str).exists() if file_path_str else False
