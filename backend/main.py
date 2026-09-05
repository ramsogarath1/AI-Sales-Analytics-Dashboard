"""
FastAPI Server Entry Point for AI Sales Analytics Dashboard.
Initializes SQLite database schema on startup, registers routers, sets up global error handlers,
and configures CORS middleware.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes.auth import router as auth_router
from backend.routes.upload import router as upload_router
from backend.routes.analytics import router as analytics_router
from backend.routes.insights import router as insights_router
from backend.routes.ai import router as ai_router
from backend.routes.datasets import router as datasets_router
from backend.utils.errors import http_exception_handler, unhandled_exception_handler

app = FastAPI(
    title="AI Sales Analytics API",
    description="FastAPI backend for dataset ingestion, automated data cleaning, BI analytics, statistical insights, persistent dataset management, caching, JWT authentication, and AI Analyst briefings.",
    version="7.1.0 (Phase 7B Zero-Cost Deployment)"
)

# Initialize database tables
init_db()

# Global Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Enable CORS middleware with configurable origins
raw_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:8501,http://127.0.0.1:8501")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
for default_origin in ["http://localhost:8501", "http://127.0.0.1:8501"]:
    if default_origin not in allowed_origins:
        allowed_origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(upload_router, prefix="/api", tags=["Data Processing"])
app.include_router(analytics_router, prefix="/api", tags=["Business Analytics"])
app.include_router(insights_router, prefix="/api", tags=["Statistical Intelligence"])
app.include_router(ai_router, prefix="/api", tags=["AI Analyst Engine"])
app.include_router(datasets_router, tags=["Dataset Management"])

@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend operational status."""
    return {
        "status": "online",
        "service": "AI Sales Analytics Backend",
        "phase": "7B"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
