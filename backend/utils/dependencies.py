"""
FastAPI Dependencies for Authentication & Authorization.
Extracts and validates JWT Bearer tokens from incoming HTTP request headers.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.utils.security import decode_access_token, make_error_detail

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db)
) -> UserRecord:
    """
    FastAPI dependency validating Authorization Bearer token header.
    Decodes JWT, verifies user existence and active status, and returns UserRecord.
    Raises HTTPException 401 if missing, invalid, or expired.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail=make_error_detail("Authentication credentials missing. Please log in.", "UNAUTHORIZED")
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=make_error_detail("Invalid token payload structure", "INVALID_TOKEN")
        )

    user = db.query(UserRecord).filter(UserRecord.id == user_id, UserRecord.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail=make_error_detail("User account not found or inactive", "USER_NOT_FOUND")
        )

    return user
