"""
Phase 7B Zero-Cost Deployment Verification Tests.
Verifies backend operational status, health check endpoints, AI_PROVIDER=none/mock fallback,
missing OPENAI_API_KEY graceful execution, storage missing-file handling, and frontend config resolution.
"""

import os
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Ensure testing environment variables
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase7b_deployment.db"
os.environ["JWT_SECRET_KEY"] = "test_secure_jwt_secret_key_32_bytes_long_minimum!"

from backend.main import app
from backend.services.ai_service import AIService, is_ai_configured, get_ai_provider, MockAIProvider
from backend.services.storage_service import StorageService
from config import get_backend_url

client = TestClient(app)

def test_health_endpoints_unauthenticated():
    """Verify GET /health and GET /api/health respond with 200 OK without requiring auth headers."""
    res_root = client.get("/health")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root.get("status") == "online"
    assert data_root.get("phase") == "7B"

    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    data_api = res_api.json()
    assert data_api.get("status") == "online"
    assert data_api.get("phase") == "7B"

def test_ai_provider_none_without_openai_key(monkeypatch):
    """Verify application operates cleanly when AI_PROVIDER=none and OPENAI_API_KEY is empty/unset."""
    monkeypatch.setenv("AI_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)
    # is_ai_configured() returns False for external provider when provider=none, defaulting safely to MockAIProvider
    assert is_ai_configured() is False

def test_ai_provider_mock_fallback(monkeypatch):
    """Verify AI_PROVIDER=mock functions deterministically without external network requests."""
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)
    assert is_ai_configured() is True

def test_frontend_backend_url_resolution(monkeypatch):
    """Verify get_backend_url reads BACKEND_URL env var and strips trailing slash."""
    monkeypatch.setenv("BACKEND_URL", "https://api.my-dashboard-app.onrender.com/")
    assert get_backend_url() == "https://api.my-dashboard-app.onrender.com"

    monkeypatch.delenv("BACKEND_URL", raising=False)
    assert get_backend_url() == "http://127.0.0.1:8000"

def test_storage_service_missing_file_handling():
    """Verify StorageService handles missing files with clear 404 error detail."""
    non_existent_file = "uploads/non_existent_dataset_12345.csv"
    
    assert StorageService.file_exists(non_existent_file) is False
    assert StorageService.delete_file(non_existent_file) is False

    with pytest.raises(Exception) as exc_info:
        StorageService.read_file(non_existent_file)
    
    assert "404" in str(exc_info.value) or exc_info.value.status_code == 404
