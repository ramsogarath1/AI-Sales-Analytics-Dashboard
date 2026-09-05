"""
Insights Endpoint Route (`GET /api/insights`).
Generates statistical anomalies, growth trends, risk indicators, and pattern insights for current user with database caching.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.utils.dependencies import get_current_user
from backend.utils.security import make_error_detail
from backend.services import dataset_service, cache_service
from backend.services.insights_engine import InsightsEngine

router = APIRouter()

@router.get("/insights")
def get_statistical_insights(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Returns statistical intelligence payload including Z-score anomalies,
    growth trends, concentration risks, and product/category/regional insights for current_user.
    Supports dataset_id query parameter and SQLite caching.
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
                    "summary": {"total_insights": 0, "anomalies_detected": 0, "risks_identified": 0, "growth_opportunities": 0},
                    "anomalies": [], "growth": [], "products": [], "categories": [], "regions": [], "risks": []
                }
            raise http_ex

    if df is None or len(df) == 0:
        return {
            "status": "no_data",
            "message": "Dataset is empty.",
            "summary": {"total_insights": 0, "anomalies_detected": 0, "risks_identified": 0, "growth_opportunities": 0},
            "anomalies": [], "growth": [], "products": [], "categories": [], "regions": [], "risks": []
        }

    cur_dataset_id = file_info.get("dataset_id", dataset_id or "active")
    cur_dataset_hash = file_info.get("dataset_hash", "default_hash")
    cache_key = cache_service.generate_cache_key("insights", cur_dataset_id, cur_dataset_hash, user_id=current_user.id)

    # Check cache
    cached_data = cache_service.get_cache(db, cache_key)
    if cached_data:
        return {
            "status": "success",
            "message": f"Retrieved statistical insights from cache for '{file_info.get('filename', cur_dataset_id)}'",
            "file_info": file_info,
            "summary": cached_data.get("summary", {}),
            "anomalies": cached_data.get("anomalies", []),
            "growth": cached_data.get("growth", []),
            "products": cached_data.get("products", []),
            "categories": cached_data.get("categories", []),
            "regions": cached_data.get("regions", []),
            "risks": cached_data.get("risks", []),
            "cache_hit": True
        }

    try:
        insights_data = InsightsEngine.generate_all_insights(df, detected_cols)
        
        # Save in database cache
        cache_service.set_cache(
            db,
            dataset_id=cur_dataset_id,
            dataset_hash=cur_dataset_hash,
            cache_key=cache_key,
            cache_type="insights",
            data=insights_data
        )

        return {
            "status": "success",
            "message": f"Generated {insights_data['summary']['total_insights']} statistical insights for '{file_info.get('filename', cur_dataset_id)}'",
            "file_info": file_info,
            "summary": insights_data["summary"],
            "anomalies": insights_data["anomalies"],
            "growth": insights_data["growth"],
            "products": insights_data["products"],
            "categories": insights_data["categories"],
            "regions": insights_data["regions"],
            "risks": insights_data["risks"],
            "cache_hit": False
        }
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=make_error_detail(f"Failed to compute insights: {str(ex)}", "INSIGHTS_FAILED")
        )
