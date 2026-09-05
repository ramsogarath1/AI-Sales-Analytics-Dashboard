"""
Structured Error Response Helpers and Exception Handlers for FastAPI.
Formats error responses consistently as:
{
    "error": true,
    "message": "...",
    "code": "..."
}
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("sales_analytics.errors")

def create_error_response(status_code: int, message: str, code: str) -> JSONResponse:
    """Helper to generate standardized JSON error response with backward-compatible detail field."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "message": message,
            "code": code,
            "detail": message
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler providing structured error details."""
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)

    message = str(detail) if isinstance(detail, str) else "An error occurred"
    code_map = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        413: "FILE_TOO_LARGE",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    code = code_map.get(exc.status_code, "ERROR")
    return create_error_response(exc.status_code, message, code)

async def unhandled_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception handler to avoid leaking stack traces."""
    logger.exception(f"Unhandled exception on path {request.url.path}: {str(exc)}")
    return create_error_response(
        status_code=500,
        message="An internal server error occurred.",
        code="INTERNAL_SERVER_ERROR"
    )
