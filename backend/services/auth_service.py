"""
Authentication Service for User Registration, Password Verification, and Token Issuance.
Handles email normalization, password hashing, database persistence, and rate limiting.
"""

import re
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.database.models import UserRecord
from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_user_id,
    make_error_detail,
    get_access_token_expire_minutes,
)
from backend.utils.rate_limiter import check_login_rate_limit

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def register_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    """
    Validates, normalizes, hashes password, and registers a new UserRecord.
    Raises HTTPException 400 for bad input, 409 for duplicate email.
    """
    if not email or not email.strip():
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("Email address is required.", "INVALID_EMAIL")
        )

    clean_email = email.strip().lower()
    if not re.match(EMAIL_REGEX, clean_email):
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("Invalid email address format.", "INVALID_EMAIL")
        )

    if not password or len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("Password must be at least 8 characters long.", "WEAK_PASSWORD")
        )

    # Check duplicate email
    existing_user = db.query(UserRecord).filter(UserRecord.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=make_error_detail("An account with this email address already exists.", "EMAIL_ALREADY_EXISTS")
        )

    pwd_hash = hash_password(password)
    user_id = generate_user_id()

    user = UserRecord(
        id=user_id,
        email=clean_email,
        password_hash=pwd_hash,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user.to_dict()

def authenticate_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    """
    Authenticates user credentials against stored bcrypt hash with rate limiting.
    On success, returns JWT access token.
    On failure, returns generic HTTP 401 error.
    """
    if not email or not password:
        raise HTTPException(
            status_code=401,
            detail=make_error_detail("Invalid email or password.", "INVALID_CREDENTIALS")
        )

    clean_email = email.strip().lower()
    check_login_rate_limit(clean_email)

    user = db.query(UserRecord).filter(UserRecord.email == clean_email, UserRecord.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail=make_error_detail("Invalid email or password.", "INVALID_CREDENTIALS")
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    expires_in_seconds = get_access_token_expire_minutes() * 60

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in_seconds,
        "user": user.to_dict()
    }
