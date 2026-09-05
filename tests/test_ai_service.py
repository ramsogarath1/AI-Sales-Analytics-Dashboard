"""
Phase 5 AI Service Test Suite.
Verifies AI provider configuration, OpenAI/Mock provider abstractions, response parsing, fallback behavior, and endpoints.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_ai_secret_key_32bytes!"

from backend.main import app
from backend.services.ai_service import AIService, MockAIProvider, OpenAIProvider, is_ai_configured, get_ai_provider
from backend.database.connection import init_db
from backend.utils.rate_limiter import clear_rate_limit_store

class TestPhase5AIService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        clear_rate_limit_store()
        init_db()
        cls.client = TestClient(app)
        cls.test_dir = os.path.join(project_root, "data", "test_datasets")

        # Register & login test user
        email = "aitestuser@example.com"
        pwd = "password123"
        cls.client.post("/api/auth/register", json={"email": email, "password": pwd})
        login_res = cls.client.post("/api/auth/login", json={"email": email, "password": pwd})
        cls.token = login_res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_ai_configuration_check(self):
        """1. Verifies AI service configuration detection."""
        with patch.dict(os.environ, {"AI_PROVIDER": "mock"}):
            self.assertTrue(is_ai_configured())
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": ""}):
            self.assertFalse(is_ai_configured())

    def test_02_missing_api_key_fallback(self):
        """2. Verifies missing API key defaults to MockAIProvider."""
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": ""}):
            provider = get_ai_provider()
            self.assertIsInstance(provider, MockAIProvider)

    def test_03_valid_analytics_context(self):
        """3. Verifies MockAIProvider generates briefing from valid analytics context."""
        context = {
            "file_info": {"filename": "test.csv"},
            "analytics": {"kpis": {"total_revenue": 1000.0, "total_orders": 5, "average_order_value": 200.0}},
            "insights": {"growth": [{"description": "Growth up 20%"}], "risks": []}
        }
        provider = MockAIProvider()
        summary = provider.generate_summary(context)
        self.assertEqual(summary["status"], "success")
        self.assertIn("1,000.00", summary["summary"])

    def test_04_empty_analytics_context(self):
        """4. Verifies provider handles empty analytics context without crashing."""
        context = {}
        provider = MockAIProvider()
        summary = provider.generate_summary(context)
        self.assertEqual(summary["status"], "success")
        self.assertIsNotNone(summary["summary"])

    def test_05_ai_response_parsing(self):
        """5. Verifies OpenAIProvider correctly parses JSON completion."""
        mock_json_str = '```json\n{"summary": "Test Summary", "key_findings": ["F1"], "risks": [], "opportunities": [], "recommendations": []}\n```'
        provider = OpenAIProvider(api_key="sk-testkey")
        with patch.object(provider, "_call_openai_chat", return_value=mock_json_str):
            res = provider.generate_summary({"test": True})
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["summary"], "Test Summary")

    def test_06_invalid_ai_response_fallback(self):
        """6. Verifies invalid AI response (malformed JSON) falls back to Mock provider."""
        provider = OpenAIProvider(api_key="sk-testkey")
        with patch.object(provider, "_call_openai_chat", return_value="INVALID NON-JSON RESPONSE"):
            res = provider.generate_summary({"test": True})
            # Should fall back to mock summary cleanly without crashing
            self.assertEqual(res["status"], "success")
            self.assertIn("fallback", res.get("provider", ""))

    def test_07_api_failure_handling(self):
        """7. Verifies external HTTP connection error falls back to Mock provider."""
        provider = OpenAIProvider(api_key="sk-testkey")
        with patch.object(provider, "_call_openai_chat", side_effect=Exception("HTTP 500 Connection Timeout")):
            res = provider.generate_summary({"test": True})
            self.assertEqual(res["status"], "success")
            self.assertIn("warning", res)

    def test_08_missing_dataset_handling(self):
        """8. Verifies calling AIService without active dataset returns status no_data."""
        res_summary = AIService.generate_executive_summary(None, None, None)
        self.assertEqual(res_summary["status"], "no_data")
        
        res_ask = AIService.ask_data_analyst("What is revenue?", None, None, None)
        self.assertEqual(res_ask["status"], "no_data")
        self.assertIn("does not contain enough information", res_ask["answer"])

    def test_09_post_ai_executive_summary_endpoint(self):
        """9. Verifies POST /api/ai/executive-summary endpoint."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            self.client.post("/api/upload", files={"file": ("valid_sales_data.csv", f, "text/csv")}, headers=self.headers)

        res = self.client.post("/api/ai/executive-summary", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertEqual(res_json["status"], "success")
        self.assertIn("summary", res_json)

    def test_10_post_ai_ask_endpoint(self):
        """10. Verifies POST /api/ai/ask endpoint."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            self.client.post("/api/upload", files={"file": ("valid_sales_data.csv", f, "text/csv")}, headers=self.headers)

        res = self.client.post("/api/ai/ask", json={"question": "What is total revenue?"}, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertEqual(res_json["status"], "success")
        self.assertIn("915.50", res_json["answer"])

        # Test unmapped question
        res_unmapped = self.client.post("/api/ai/ask", json={"question": "What is the employee turnover rate?"}, headers=self.headers)
        self.assertEqual(res_unmapped.status_code, 200)
        self.assertIn("does not contain enough information", res_unmapped.json()["answer"])

if __name__ == "__main__":
    unittest.main()
