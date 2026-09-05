"""
Analytics Endpoint Route (`GET /api/analytics`).
Computes multi-dimensional business metrics from specified or active dataset owned by current user with database caching.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.utils.dependencies import get_current_user
from backend.utils.security import make_error_detail
from backend.services import dataset_service, cache_service
from backend.services.analytics_engine import AnalyticsEngine

router = APIRouter()

@router.get("/analytics")
def get_sales_analytics(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Returns structured business analytics across Time, Product, Category, Customer, and Region for current_user.
    Supports dataset_id query parameter and caches calculation results in SQLite database.
    """
    if dataset_id:
        df, detected_cols, file_info = dataset_service.get_dataset_data(db, dataset_id, user_id=current_user.id)
    else:
        try:
            df, detected_cols, file_info = dataset_service.get_dataset_data(db, None, user_id=current_user.id)
        except HTTPException as http_ex:
            if http_ex.status_code == 404:
                return {
                    "status": "no_data",
                    "message": "No sales dataset has been uploaded or selected yet.",
                    "analytics": None
                }
            raise http_ex

    if df is None or len(df) == 0:
        return {
            "status": "no_data",
            "message": "Dataset is empty.",
            "analytics": None
        }

    cur_dataset_id = file_info.get("dataset_id", dataset_id or "active")
    cur_dataset_hash = file_info.get("dataset_hash", "default_hash")
    cache_key = cache_service.generate_cache_key("analytics", cur_dataset_id, cur_dataset_hash, user_id=current_user.id)

    # Check cache
    cached_data = cache_service.get_cache(db, cache_key)
    if cached_data:
        return {
            "status": "success",
            "message": f"Analytics retrieved from cache for dataset '{file_info.get('filename', cur_dataset_id)}'",
            "file_info": file_info,
            "analytics": cached_data,
            "cache_hit": True
        }

    try:
        analytics_result = AnalyticsEngine.compute_full_analytics(df, detected_cols)
        # Store in cache
        cache_service.set_cache(
            db,
            dataset_id=cur_dataset_id,
            dataset_hash=cur_dataset_hash,
            cache_key=cache_key,
            cache_type="analytics",
            data=analytics_result
        )

        return {
            "status": "success",
            "message": f"Analytics generated for '{file_info.get('filename', cur_dataset_id)}'",
            "file_info": file_info,
            "analytics": analytics_result,
            "cache_hit": False
        }
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=make_error_detail(f"Failed to compute analytics: {str(ex)}", "ANALYTICS_FAILED")
        )
