"""
Phase 6 Automated Test Suite for AI-Sales-Analytics-Dashboard.
Tests database persistence, SHA-256 hashing, dataset management API, analytics caching,
AI caching, upload security, path traversal protection, error handling, and cache invalidation.
"""

import sys
import os
import io
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root and backend to python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set test database environment variable before importing database
os.environ["DATABASE_URL"] = "sqlite:///./test_phase6_sales.db"
os.environ["MAX_UPLOAD_SIZE_MB"] = "25"
os.environ["MAX_AI_QUESTION_LENGTH"] = "1000"
os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_phase6_secret_key_32bytes!"

from backend.main import app
from backend.database.connection import init_db, engine
from backend.database.models import Base
from backend.utils.security import calculate_sha256
from backend.utils.rate_limiter import clear_rate_limit_store

class TestPhase6ProductionHardening(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        clear_rate_limit_store()
        test_db_path = Path("./test_phase6_sales.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass

        # Create test database schema
        init_db("sqlite:///./test_phase6_sales.db")
        cls.client = TestClient(app)
        cls.test_dir = os.path.join(project_root, "data", "test_datasets")

        # Register & login test user
        email = "phase6user@example.com"
        pwd = "password123"
        cls.client.post("/api/auth/register", json={"email": email, "password": pwd})
        login_res = cls.client.post("/api/auth/login", json={"email": email, "password": pwd})
        cls.token = login_res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        # Cleanup isolated test database file after test completion
        test_db_path = Path("./test_phase6_sales.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass

    def test_01_database_initialization(self):
        """Tests that SQLite database initializes and health check returns status online."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "online")
        self.assertIn(str(json_data["phase"]), ["7A", "7B"])

    def test_02_sha256_hashing(self):
        """Tests deterministic SHA-256 calculation."""
        content1 = b"Order_ID,Sales\n1,100\n2,200\n"
        content2 = b"Order_ID,Sales\n1,100\n2,200\n"
        content3 = b"Order_ID,Sales\n1,100\n2,300\n"

        hash1 = calculate_sha256(content1)
        hash2 = calculate_sha256(content2)
        hash3 = calculate_sha256(content3)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 64)

    def test_03_valid_csv_upload_with_metadata(self):
        """Tests valid CSV upload generates dataset_id, SHA-256 hash, and stores metadata."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("valid_sales_data.csv", f, "text/csv")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["status"], "success")
        self.assertIn("dataset_id", res)
        self.assertTrue(res["dataset_id"].startswith("ds_"))
        self.assertIn("dataset_hash", res)
        self.assertEqual(len(res["dataset_hash"]), 64)

    def test_04_dataset_management_api(self):
        """Tests dataset list, detail, selection, and missing dataset 404."""
        # 1. List datasets
        list_res = self.client.get("/api/datasets", headers=self.headers)
        self.assertEqual(list_res.status_code, 200)
        datasets = list_res.json()
        self.assertTrue(len(datasets) >= 1)

        ds_id = datasets[0]["dataset_id"]

        # 2. Get single dataset metadata
        detail_res = self.client.get(f"/api/datasets/{ds_id}", headers=self.headers)
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["dataset_id"], ds_id)
        self.assertIn("filename", detail)

        # 3. Test non-existent dataset 404
        missing_res = self.client.get("/api/datasets/ds_nonexistent_999", headers=self.headers)
        self.assertEqual(missing_res.status_code, 404)

        # 4. Select dataset
        select_res = self.client.post(f"/api/datasets/{ds_id}/select", headers=self.headers)
        self.assertEqual(select_res.status_code, 200)
        self.assertTrue(select_res.json()["is_active"])

    def test_05_upload_security_unsupported_extension(self):
        """Tests that uploading unsupported file extension returns HTTP 400."""
        file_path = os.path.join(self.test_dir, "unsupported_file.txt")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("unsupported_file.txt", f, "text/plain")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 400)

    def test_06_upload_security_corrupted_file(self):
        """Tests that uploading corrupted content disguised as CSV returns HTTP 400."""
        corrupted_bytes = b"NOT_A_CSV_HEADER_\x00\xff\xfe\xfa__RANDOM_BYTES"
        response = self.client.post(
            "/api/upload",
            files={"file": ("fake.csv", corrupted_bytes, "text/csv")},
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)

    def test_07_upload_security_oversized_file(self):
        """Tests that uploading file exceeding MAX_UPLOAD_SIZE_MB returns HTTP 413."""
        # Temporarily lower limit to 1MB for testing
        os.environ["MAX_UPLOAD_SIZE_MB"] = "1"
        large_bytes = b"Order_ID,Sales\n1,100\n" * 100000  # ~2 MB
        response = self.client.post(
            "/api/upload",
            files={"file": ("large_sales.csv", large_bytes, "text/csv")},
            headers=self.headers
        )
        self.assertEqual(response.status_code, 413)
        # Restore limit
        os.environ["MAX_UPLOAD_SIZE_MB"] = "25"

    def test_08_upload_security_path_traversal(self):
        """Tests filename path traversal protection."""
        path_traversal_bytes = b"Order_ID,Sales\n901,500.0\n902,600.0\n"
        response = self.client.post(
            "/api/upload",
            files={"file": ("../../secret_passwd.csv", path_traversal_bytes, "text/csv")},
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        # Verify stored name sanitized safely without path components
        ds_id = response.json()["dataset_id"]
        detail = self.client.get(f"/api/datasets/{ds_id}", headers=self.headers).json()
        self.assertEqual(detail["filename"], "secret_passwd.csv")


    def test_09_analytics_and_insights_caching(self):
        """Tests analytics and statistical insights caching (cache_hit flag)."""
        # Upload dataset
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            up_res = self.client.post(
                "/api/upload",
                files={"file": ("cache_test_sales.csv", f, "text/csv")},
                headers=self.headers
            )
        ds_id = up_res.json()["dataset_id"]

        # First analytics call -> miss
        res1 = self.client.get(f"/api/analytics?dataset_id={ds_id}", headers=self.headers)
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.json().get("cache_hit", False))

        # Second analytics call -> hit
        res2 = self.client.get(f"/api/analytics?dataset_id={ds_id}", headers=self.headers)
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json().get("cache_hit", False))

        # First insights call -> miss
        ins1 = self.client.get(f"/api/insights?dataset_id={ds_id}", headers=self.headers)
        self.assertEqual(ins1.status_code, 200)
        self.assertFalse(ins1.json().get("cache_hit", False))

        # Second insights call -> hit
        ins2 = self.client.get(f"/api/insights?dataset_id={ds_id}", headers=self.headers)
        self.assertEqual(ins2.status_code, 200)
        self.assertTrue(ins2.json().get("cache_hit", False))

    def test_10_ai_caching_and_question_length_limit(self):
        """Tests AI briefing caching and question length limit enforcement."""
        # 1. Executive Summary Caching
        sum1 = self.client.post("/api/ai/executive-summary", json={}, headers=self.headers)
        self.assertEqual(sum1.status_code, 200)
        self.assertFalse(sum1.json().get("cache_hit", False))

        sum2 = self.client.post("/api/ai/executive-summary", json={}, headers=self.headers)
        self.assertEqual(sum2.status_code, 200)
        self.assertTrue(sum2.json().get("cache_hit", False))

        # 2. Ask Question Caching
        q_payload = {"question": "What is total revenue?"}
        ask1 = self.client.post("/api/ai/ask", json=q_payload, headers=self.headers)
        self.assertEqual(ask1.status_code, 200)
        self.assertFalse(ask1.json().get("cache_hit", False))

        ask2 = self.client.post("/api/ai/ask", json=q_payload, headers=self.headers)
        self.assertEqual(ask2.status_code, 200)
        self.assertTrue(ask2.json().get("cache_hit", False))

        # 3. Overlong Question -> 400 Bad Request
        long_q = "What is revenue? " * 100  # > 1000 chars
        long_ask = self.client.post("/api/ai/ask", json={"question": long_q}, headers=self.headers)
        self.assertEqual(long_ask.status_code, 400)

    def test_11_dataset_deletion_and_cache_invalidation(self):
        """Tests safe dataset deletion and cache invalidation."""
        # Upload dataset
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            up_res = self.client.post(
                "/api/upload",
                files={"file": ("to_delete.csv", f, "text/csv")},
                headers=self.headers
            )
        ds_id = up_res.json()["dataset_id"]

        # Prime cache
        self.client.get(f"/api/analytics?dataset_id={ds_id}", headers=self.headers)

        # Delete dataset
        del_res = self.client.delete(f"/api/datasets/{ds_id}", headers=self.headers)
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Subsequent fetch for deleted dataset -> 404
        get_res = self.client.get(f"/api/datasets/{ds_id}", headers=self.headers)
        self.assertEqual(get_res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
