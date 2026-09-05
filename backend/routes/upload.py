"""
Upload Endpoint Route (`POST /api/upload`).
Receives CSV/Excel datasets, validates file properties, registers dataset record in DB bound to current user,
hashes file content, stores raw data safely, and executes data processing pipeline.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.utils.dependencies import get_current_user
from backend.utils.validators import validate_uploaded_file
from backend.utils.security import make_error_detail
from backend.services import dataset_service, data_processor

router = APIRouter()

@router.post("/upload")
async def upload_sales_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Accepts CSV, XLSX, and XLS sales files for authenticated user.
    Harden checks: max file size limit (413), content parsing (400), path traversal (400).
    Hashes file content with SHA-256 and registers dataset metadata bound to current_user.id.
    """
    try:
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail=make_error_detail("No file was uploaded.", "NO_FILE")
            )

        file_bytes = await file.read()
        sanitized_filename = validate_uploaded_file(file, file_bytes)

        # Register dataset in SQLite database & filesystem storage associated with current_user
        record = dataset_service.register_dataset(
            db,
            original_filename=sanitized_filename,
            file_bytes=file_bytes,
            user_id=current_user.id
        )

        # Obtain process_sales_file result for backward compatibility
        result = data_processor.process_sales_file(file_bytes, sanitized_filename)

        record_dict = record.to_dict()
        result["dataset_id"] = record.dataset_id
        result["dataset_hash"] = record.dataset_hash
        result["user_id"] = current_user.id
        result["metadata"] = record_dict

        return {
            "status": "success",
            "message": f"Successfully processed dataset '{sanitized_filename}'",
            "dataset_id": record.dataset_id,
            "dataset_hash": record.dataset_hash,
            "user_id": current_user.id,
            "data": result
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=make_error_detail(f"An unexpected error occurred while processing file: {str(ex)}", "INTERNAL_SERVER_ERROR")
        )
