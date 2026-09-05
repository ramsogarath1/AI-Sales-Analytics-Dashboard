"""
Dataset Management Service for AI-Sales-Analytics-Dashboard.
Manages dataset metadata in SQLite, raw file persistence in uploads/, safe path operations,
user ownership enforcement, user-scoped dataset activation, in-memory DataFrame caching, and safe deletion.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException

try:
    from backend.database.models import DatasetRecord
    from backend.services.cache_service import invalidate_cache_for_dataset
    from backend.services import dataset_store
    from backend.services.storage_service import StorageService
    from backend.utils.security import (
        calculate_sha256,
        generate_dataset_id,
        sanitize_filename,
        safe_path_join,
        validate_upload_content,
        make_error_detail,
    )
except ImportError:
    from database.models import DatasetRecord
    from services.cache_service import invalidate_cache_for_dataset
    from services import dataset_store
    from services.storage_service import StorageService
    from utils.security import (
        calculate_sha256,
        generate_dataset_id,
        sanitize_filename,
        safe_path_join,
        validate_upload_content,
        make_error_detail,
    )

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory parsed DataFrame cache: {dataset_id: (df, detected_cols, file_info)}
_PARSED_DATASET_CACHE: Dict[str, Tuple[pd.DataFrame, Dict[str, Optional[str]], Dict[str, Any]]] = {}

def register_dataset(
    db: Session,
    original_filename: str,
    file_bytes: bytes,
    user_id: Optional[str] = None
) -> DatasetRecord:
    """
    Validates, hashes, stores file, cleans dataset, and creates database record bound to user_id.
    If exact file hash exists for user, reuses or updates existing dataset entry.
    """
    clean_name, ext = validate_upload_content(original_filename, file_bytes)
    dataset_hash = calculate_sha256(file_bytes)

    # Check for existing duplicate dataset hash owned by this user
    query = db.query(DatasetRecord).filter(DatasetRecord.dataset_hash == dataset_hash)
    if user_id:
        query = query.filter(DatasetRecord.user_id == user_id)
    existing = query.first()

    if existing and StorageService.file_exists(existing.file_path):
        # Deactivate user's other datasets
        db_filter = db.query(DatasetRecord)
        if user_id:
            db_filter = db_filter.filter(DatasetRecord.user_id == user_id)
        db_filter.update({"is_active": False})

        existing.is_active = True
        db.commit()
        db.refresh(existing)
        
        get_dataset_data(db, existing.dataset_id, user_id=user_id)
        return existing

    dataset_id = generate_dataset_id()
    stored_filename = f"{dataset_id}{ext}"
    target_path = StorageService.save_file(stored_filename, file_bytes)

    try:
        from backend.services.data_processor import inspect_and_clean_data
    except ImportError:
        from services.data_processor import inspect_and_clean_data

    try:
        df, detected_cols, summary = inspect_and_clean_data(file_bytes, clean_name)
        row_count = summary.get("row_count") or len(df)
        col_count = summary.get("column_count") or len(df.columns)
        status = "processed"
        error_msg = None
    except Exception as e:
        row_count = None
        col_count = None
        status = "error"
        error_msg = str(e)
        df, detected_cols, summary = None, {}, {}

    # Deactivate user's other datasets
    db_filter = db.query(DatasetRecord)
    if user_id:
        db_filter = db_filter.filter(DatasetRecord.user_id == user_id)
    db_filter.update({"is_active": False})

    record = DatasetRecord(
        dataset_id=dataset_id,
        user_id=user_id,
        original_filename=clean_name,
        stored_filename=stored_filename,
        file_path=str(target_path),
        file_size=len(file_bytes),
        file_type=ext.lstrip("."),
        row_count=row_count,
        column_count=col_count,
        dataset_hash=dataset_hash,
        processing_status=status,
        error_message=error_msg,
        is_active=True
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    if status == "processed" and df is not None:
        file_info = {
            "dataset_id": dataset_id,
            "user_id": user_id,
            "filename": clean_name,
            "file_size": len(file_bytes),
            "dataset_hash": dataset_hash,
            "processing_summary": summary
        }
        _PARSED_DATASET_CACHE[dataset_id] = (df, detected_cols, file_info)
        dataset_store.set_active_dataset(df, detected_cols, file_info, user_id=user_id)

    return record

def list_datasets(db: Session, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns metadata for all datasets owned by user_id."""
    query = db.query(DatasetRecord)
    if user_id:
        query = query.filter(DatasetRecord.user_id == user_id)
    records = query.order_by(DatasetRecord.upload_timestamp.desc()).all()
    return [rec.to_dict() for rec in records]

def get_dataset_record(db: Session, dataset_id: str, user_id: Optional[str] = None) -> DatasetRecord:
    """Gets DatasetRecord owned by user_id or raises 404 HTTPException."""
    if not dataset_id:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("Dataset ID is required", "INVALID_DATASET_ID")
        )
    query = db.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset_id)
    if user_id:
        query = query.filter(DatasetRecord.user_id == user_id)

    record = query.first()
    if not record:
        raise HTTPException(
            status_code=404,
            detail=make_error_detail(f"Dataset '{dataset_id}' not found", "DATASET_NOT_FOUND")
        )
    return record

def get_dataset_metadata(db: Session, dataset_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Returns dictionary metadata for specified dataset_id owned by user_id."""
    record = get_dataset_record(db, dataset_id, user_id=user_id)
    return record.to_dict()

def get_dataset_data(
    db: Session,
    dataset_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Optional[str]], Dict[str, Any]]:
    """
    Retrieves DataFrame, detected columns, and file_info for a dataset_id owned by user_id.
    If dataset_id is None, uses current active dataset for user_id.
    """
    try:
        from backend.services.data_processor import inspect_and_clean_data
    except ImportError:
        from services.data_processor import inspect_and_clean_data

    if not dataset_id:
        query = db.query(DatasetRecord).filter(DatasetRecord.is_active == True)
        if user_id:
            query = query.filter(DatasetRecord.user_id == user_id)
        active_rec = query.first()

        if active_rec:
            dataset_id = active_rec.dataset_id
        else:
            active_df, detected_cols, file_info = dataset_store.get_active_dataset(user_id=user_id)
            if active_df is not None:
                return active_df, detected_cols, file_info
            raise HTTPException(
                status_code=404,
                detail=make_error_detail("No active dataset selected for analysis", "NO_ACTIVE_DATASET")
            )

    # Validate dataset existence and ownership against DB first
    record = get_dataset_record(db, dataset_id, user_id=user_id)

    if dataset_id in _PARSED_DATASET_CACHE:
        df, detected_cols, file_info = _PARSED_DATASET_CACHE[dataset_id]
        dataset_store.set_active_dataset(df, detected_cols, file_info, user_id=user_id)
        return df, detected_cols, file_info

    if record.processing_status != "processed":
        raise HTTPException(
            status_code=400,
            detail=make_error_detail(f"Dataset processing error: {record.error_message}", "DATASET_PROCESSING_ERROR")
        )

    file_bytes = StorageService.read_file(record.file_path)

    df, detected_cols, summary = inspect_and_clean_data(file_bytes, record.original_filename)
    file_info = {
        "dataset_id": dataset_id,
        "user_id": record.user_id,
        "filename": record.original_filename,
        "file_size": record.file_size,
        "dataset_hash": record.dataset_hash,
        "processing_summary": summary
    }

    _PARSED_DATASET_CACHE[dataset_id] = (df, detected_cols, file_info)
    if record.is_active:
        dataset_store.set_active_dataset(df, detected_cols, file_info, user_id=user_id)

    return df, detected_cols, file_info

def set_active_dataset_id(db: Session, dataset_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Sets specified dataset_id as active for user_id in DB and updates dataset_store."""
    record = get_dataset_record(db, dataset_id, user_id=user_id)

    db_filter = db.query(DatasetRecord)
    if user_id:
        db_filter = db_filter.filter(DatasetRecord.user_id == user_id)
    db_filter.update({"is_active": False})

    record.is_active = True
    db.commit()
    db.refresh(record)

    df, detected_cols, file_info = get_dataset_data(db, dataset_id, user_id=user_id)
    dataset_store.set_active_dataset(df, detected_cols, file_info, user_id=user_id)

    return record.to_dict()

def delete_dataset(db: Session, dataset_id: str, user_id: Optional[str] = None) -> bool:
    """
    Safely deletes dataset record owned by user_id, physical file, invalidates cache,
    and updates active dataset for user_id.
    """
    record = get_dataset_record(db, dataset_id, user_id=user_id)
    was_active = record.is_active

    if record.file_path:
        StorageService.delete_file(record.file_path)

    invalidate_cache_for_dataset(db, dataset_id)
    _PARSED_DATASET_CACHE.pop(dataset_id, None)

    db.delete(record)
    db.commit()

    if was_active:
        query = db.query(DatasetRecord)
        if user_id:
            query = query.filter(DatasetRecord.user_id == user_id)
        latest = query.order_by(DatasetRecord.upload_timestamp.desc()).first()

        if latest:
            latest.is_active = True
            db.commit()
            try:
                get_dataset_data(db, latest.dataset_id, user_id=user_id)
            except Exception:
                dataset_store.clear_active_dataset(user_id=user_id)
        else:
            dataset_store.clear_active_dataset(user_id=user_id)

    return True
