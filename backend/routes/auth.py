"""
Authentication API Router (`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`).
Handles user account creation, credentials verification, JWT issuance, and user profile inspection.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.services import auth_service
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password (min 8 characters)")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """POST /api/auth/register — Registers a new user account."""
    user_data = auth_service.register_user(db, body.email, body.password)
    return {
        "status": "success",
        "message": "User account registered successfully.",
        "user": user_data
    }

@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """POST /api/auth/login — Authenticates user credentials and issues JWT access token."""
    return auth_service.authenticate_user(db, body.email, body.password)

@router.get("/me", response_model=Dict[str, Any])
def get_current_user_profile(current_user: UserRecord = Depends(get_current_user)):
    """GET /api/auth/me — Returns profile info for currently authenticated user."""
    return current_user.to_dict()
