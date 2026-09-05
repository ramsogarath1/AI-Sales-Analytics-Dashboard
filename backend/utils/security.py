"""
Security Utilities for AI-Sales-Analytics-Dashboard.
Handles password hashing (bcrypt), JWT generation/verification (PyJWT), SHA-256 hashing,
path traversal prevention, upload content validation, and security configuration.
"""

import hashlib
import os
import uuid
import io
import datetime
from pathlib import Path
import bcrypt
import jwt
import pandas as pd
from fastapi import HTTPException

# Environment Configuration with defaults
def get_max_upload_size_bytes() -> int:
    size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    return size_mb * 1024 * 1024

def get_max_ai_question_length() -> int:
    return int(os.getenv("MAX_AI_QUESTION_LENGTH", "1000"))

def get_jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        # Check if running under automated tests
        if os.getenv("TESTING", "").lower() == "true" or "test" in os.getenv("DATABASE_URL", ""):
            return "test_secure_jwt_secret_key_32_bytes_long_minimum!"
        raise ValueError(
            "CRITICAL SECURITY ERROR: 'JWT_SECRET_KEY' environment variable is not configured. "
            "Set JWT_SECRET_KEY in your .env file."
        )
    return secret

def get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")

def get_access_token_expire_minutes() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def get_frontend_origin() -> str:
    return os.getenv("FRONTEND_ORIGIN", "http://localhost:8501")

# Password Hashing & Verification
def hash_password(plain_password: str) -> str:
    """Hashes password using bcrypt with random salt (cost factor 12)."""
    if not plain_password or len(plain_password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    pwd_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

# JWT Token Generation & Verification
def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    """Generates signed JWT access token containing claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=get_access_token_expire_minutes()
        )
    to_encode.update({"exp": expire})
    secret_key = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)

def decode_access_token(token: str) -> dict:
    """
    Decodes and validates JWT token signature and expiration.
    Raises HTTPException 401 if invalid or expired.
    """
    secret_key = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=make_error_detail("Authentication token has expired. Please log in again.", "TOKEN_EXPIRED")
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401,
            detail=make_error_detail(f"Invalid authentication token: {str(e)}", "INVALID_TOKEN")
        )

# Dataset & File Hashing / ID Helpers
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

def calculate_sha256(content: bytes) -> str:
    """Calculates SHA-256 hash of raw bytes."""
    return hashlib.sha256(content).hexdigest()

def generate_user_id() -> str:
    """Generates unique, safe user ID."""
    return f"usr_{uuid.uuid4().hex[:12]}"

def generate_dataset_id() -> str:
    """Generates unique, safe dataset ID."""
    return f"ds_{uuid.uuid4().hex[:12]}"

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename to prevent path traversal or injection."""
    if not filename:
        return "dataset.csv"
    clean_name = os.path.basename(filename.replace("\x00", ""))
    clean_name = clean_name.replace("/", "").replace("\\", "").replace("..", "")
    return clean_name or "dataset.csv"

def safe_path_join(base_dir: Path, filename: str) -> Path:
    """
    Safely joins base_dir and filename, enforcing that target path is within base_dir.
    Raises HTTPException 400 if path traversal is detected.
    """
    base_path = Path(base_dir).resolve()
    clean_name = sanitize_filename(filename)
    target_path = (base_path / clean_name).resolve()

    try:
        target_path.relative_to(base_path)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": True, "message": "Invalid filename path traversal detected", "code": "INVALID_PATH"}
        )
    return target_path

def make_error_detail(message: str, code: str) -> dict:
    """Helper creating error payload with both message and backward-compatible detail field."""
    return {
        "error": True,
        "message": message,
        "code": code,
        "detail": message
    }

def validate_upload_content(filename: str, file_bytes: bytes):
    """
    Harden file upload validation:
    - Extension check
    - File size check (413 Payload Too Large)
    - Non-empty check (400 Bad Request)
    - Parsing check to prevent spoofed/corrupted files (400 Bad Request)
    """
    if not filename:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("No file uploaded", "NO_FILE")
        )

    clean_name = sanitize_filename(filename)
    _, ext = os.path.splitext(clean_name)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail(
                f"Unsupported file type '{ext}'. Allowed extensions are: .csv, .xlsx, .xls",
                "UNSUPPORTED_FILE_TYPE"
            )
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("The uploaded file is empty (0 bytes).", "EMPTY_FILE")
        )

    max_bytes = get_max_upload_size_bytes()
    if len(file_bytes) > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=make_error_detail(
                f"File size exceeds maximum allowed limit of {max_mb} MB.",
                "FILE_TOO_LARGE"
            )
        )

    try:
        bio = io.BytesIO(file_bytes)
        if ext == ".csv":
            pd.read_csv(bio, nrows=5)
        elif ext in (".xlsx", ".xls"):
            engine = "openpyxl" if ext == ".xlsx" else "xlrd"
            pd.read_excel(bio, nrows=5, engine=engine)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail(
                f"Corrupted or malformed file content: {str(e)}",
                "INVALID_FILE_CONTENT"
            )
        )

    return clean_name, ext
