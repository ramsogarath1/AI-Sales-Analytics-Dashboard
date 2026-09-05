"""
Dataset Management API Routes.
Provides protected endpoints for listing, inspecting, selecting, and deleting datasets owned by current user.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.utils.dependencies import get_current_user
from backend.services import dataset_service

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.get("", response_model=List[Dict[str, Any]])
def list_all_datasets(
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """GET /api/datasets — Returns metadata for datasets owned by current authenticated user."""
    return dataset_service.list_datasets(db, user_id=current_user.id)

@router.get("/{dataset_id}", response_model=Dict[str, Any])
def get_dataset_metadata(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """GET /api/datasets/{dataset_id} — Returns metadata for a single dataset owned by current user."""
    return dataset_service.get_dataset_metadata(db, dataset_id, user_id=current_user.id)

@router.post("/{dataset_id}/select", response_model=Dict[str, Any])
def select_active_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """POST /api/datasets/{dataset_id}/select — Selects/activates a dataset for current user."""
    return dataset_service.set_active_dataset_id(db, dataset_id, user_id=current_user.id)

@router.delete("/{dataset_id}", response_model=Dict[str, Any])
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """DELETE /api/datasets/{dataset_id} — Safely deletes a dataset owned by current user."""
    success = dataset_service.delete_dataset(db, dataset_id, user_id=current_user.id)
    return {
        "success": success,
        "message": f"Dataset '{dataset_id}' deleted successfully.",
        "dataset_id": dataset_id
    }
