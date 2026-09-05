"""
Cache Service for AI-Sales-Analytics-Dashboard.
Provides database-backed caching for analytics, statistical insights, and AI completions.
Handles cache hit/miss logging and automatic invalidation on dataset change/deletion.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from backend.database.models import CacheRecord

logger = logging.getLogger("sales_analytics.cache")

def generate_cache_key(prefix: str, dataset_id: str, dataset_hash: str, user_id: str = "default_user", extra: str = "") -> str:
    """Generates a deterministic cache key string incorporating user ownership."""
    raw_str = f"{prefix}:{user_id}:{dataset_id}:{dataset_hash}:{extra}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def get_cache(db: Session, cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieves cached JSON result if cache key exists."""
    try:
        record = db.query(CacheRecord).filter(CacheRecord.cache_key == cache_key).first()
        if record:
            logger.info(f"Cache HIT for key: {cache_key[:16]}...")
            return json.loads(record.result_json)
        logger.info(f"Cache MISS for key: {cache_key[:16]}...")
        return None
    except Exception as e:
        logger.error(f"Error reading cache for key {cache_key}: {e}")
        return None

def set_cache(
    db: Session,
    dataset_id: str,
    dataset_hash: str,
    cache_key: str,
    cache_type: str,
    data: Dict[str, Any]
) -> bool:
    """Stores JSON-serializable result in cache database."""
    try:
        result_json = json.dumps(data, default=str)
        # Check if key already exists
        record = db.query(CacheRecord).filter(CacheRecord.cache_key == cache_key).first()
        if record:
            record.result_json = result_json
            record.created_at = datetime.utcnow()
        else:
            record = CacheRecord(
                dataset_id=dataset_id,
                dataset_hash=dataset_hash,
                cache_key=cache_key,
                cache_type=cache_type,
                result_json=result_json,
                created_at=datetime.utcnow()
            )
            db.add(record)
        db.commit()
        logger.info(f"Cached successfully: key={cache_key[:16]} type={cache_type}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting cache for key {cache_key}: {e}")
        return False

def invalidate_cache_for_dataset(db: Session, dataset_id: str) -> int:
    """Deletes all cache entries associated with a specific dataset_id."""
    try:
        deleted_count = db.query(CacheRecord).filter(CacheRecord.dataset_id == dataset_id).delete()
        db.commit()
        logger.info(f"Invalidated {deleted_count} cache entries for dataset_id={dataset_id}")
        return deleted_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error invalidating cache for dataset_id {dataset_id}: {e}")
        return 0
