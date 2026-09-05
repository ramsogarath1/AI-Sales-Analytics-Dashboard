"""
AI Analyst Endpoint Routes (`POST /api/ai/executive-summary`, `POST /api/ai/ask`).
Connects to AIService to produce AI executive briefings and answer natural language data questions
for current authenticated user, with database-backed response caching and question length limits.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import UserRecord
from backend.utils.dependencies import get_current_user
from backend.utils.security import make_error_detail, get_max_ai_question_length
from backend.services import dataset_service, cache_service
from backend.services.ai_service import AIService, is_ai_configured

router = APIRouter()

class ExecutiveSummaryRequest(BaseModel):
    dataset_id: Optional[str] = None

class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="User question about dataset")
    dataset_id: Optional[str] = None

@router.post("/ai/executive-summary")
def generate_executive_summary(
    body: Optional[ExecutiveSummaryRequest] = None,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Generates an executive briefing from verified analytics & insights payload for current_user.
    Caches identical executive summary calls per dataset per user.
    """
    target_id = body.dataset_id if body else None

    if target_id:
        df, detected_cols, file_info = dataset_service.get_dataset_data(db, target_id, user_id=current_user.id)
    else:
        try:
            df, detected_cols, file_info = dataset_service.get_dataset_data(db, None, user_id=current_user.id)
        except HTTPException as http_ex:
            if http_ex.status_code == 404:
                return {
                    "status": "no_data",
                    "message": "No dataset uploaded or selected.",
                    "executive_summary": "Please upload a sales dataset to generate an executive briefing."
                }
            raise http_ex

    cur_dataset_id = file_info.get("dataset_id", target_id or "active")
    cur_dataset_hash = file_info.get("dataset_hash", "default_hash")
    cache_key = cache_service.generate_cache_key("ai_summary", cur_dataset_id, cur_dataset_hash, user_id=current_user.id)

    # Check cache
    cached_result = cache_service.get_cache(db, cache_key)
    if cached_result:
        cached_result["cache_hit"] = True
        return cached_result

    result = AIService.generate_executive_summary(df, detected_cols, file_info)
    
    if result and result.get("status") == "success":
        cache_service.set_cache(
            db,
            dataset_id=cur_dataset_id,
            dataset_hash=cur_dataset_hash,
            cache_key=cache_key,
            cache_type="ai_summary",
            data=result
        )
    result["cache_hit"] = False
    return result

@router.post("/ai/ask")
def ask_question(
    body: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Answers executive business questions using verified context for current_user.
    Hardens question length validation (max limit) and caches identical Q&A queries per user.
    """
    if not body.question or not body.question.strip():
        raise HTTPException(
            status_code=400,
            detail=make_error_detail("Question cannot be empty.", "EMPTY_QUESTION")
        )

    max_len = get_max_ai_question_length()
    if len(body.question) > max_len:
        raise HTTPException(
            status_code=400,
            detail=make_error_detail(f"Question length exceeds maximum limit of {max_len} characters.", "QUESTION_TOO_LONG")
        )

    if body.dataset_id:
        df, detected_cols, file_info = dataset_service.get_dataset_data(db, body.dataset_id, user_id=current_user.id)
    else:
        try:
            df, detected_cols, file_info = dataset_service.get_dataset_data(db, None, user_id=current_user.id)
        except HTTPException as http_ex:
            if http_ex.status_code == 404:
                return {
                    "status": "no_data",
                    "message": "No dataset uploaded or selected.",
                    "answer": "Please upload a sales dataset before asking questions."
                }
            raise http_ex

    cur_dataset_id = file_info.get("dataset_id", body.dataset_id or "active")
    cur_dataset_hash = file_info.get("dataset_hash", "default_hash")
    normalized_q = body.question.strip().lower()
    cache_key = cache_service.generate_cache_key("ai_ask", cur_dataset_id, cur_dataset_hash, user_id=current_user.id, extra=normalized_q)

    # Check cache
    cached_result = cache_service.get_cache(db, cache_key)
    if cached_result:
        cached_result["cache_hit"] = True
        return cached_result

    result = AIService.ask_data_analyst(body.question, df, detected_cols, file_info)

    if result and result.get("status") == "success":
        cache_service.set_cache(
            db,
            dataset_id=cur_dataset_id,
            dataset_hash=cur_dataset_hash,
            cache_key=cache_key,
            cache_type="ai_ask",
            data=result
        )
    result["cache_hit"] = False
    return result

@router.get("/ai/status")
def ai_status():
    """Returns status of AI provider configuration."""
    return {
        "configured": is_ai_configured(),
        "provider": "openai" if is_ai_configured() else "mock (fallback)"
    }
