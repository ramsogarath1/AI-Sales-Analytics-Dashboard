"""
Backend Automated Test Suite for Phase 2 API Verification.
Tests file upload validation, column inspection, data cleaning, KPI calculation, and error handling with JWT auth.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add project root and backend to python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_backend_secret_key_32_bytes_minimum!"

from backend.main import app
from backend.database.connection import init_db

class TestPhase2Backend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.test_dir = os.path.join(project_root, "data", "test_datasets")

        # Register & authenticate test user
        email = "backendtest@example.com"
        pwd = "password123"
        cls.client.post("/api/auth/register", json={"email": email, "password": pwd})
        login_res = cls.client.post("/api/auth/login", json={"email": email, "password": pwd})
        cls.token = login_res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_health_check(self):
        """Tests API health endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    def test_02_valid_csv_upload(self):
        """Tests uploading a valid sales CSV dataset."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("valid_sales_data.csv", f, "text/csv")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["status"], "success")
        
        data = res_json["data"]
        self.assertEqual(data["original_row_count"], 6)
        self.assertEqual(data["cleaned_row_count"], 5)  # 1 duplicate removed
        self.assertIn("total_revenue", data["calculated_kpis"])
        self.assertEqual(data["calculated_kpis"]["total_revenue"], 915.5)
        self.assertEqual(data["calculated_kpis"]["total_orders"], 5)

    def test_03_valid_xlsx_upload(self):
        """Tests uploading a valid Excel (.xlsx) sales dataset."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.xlsx")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("valid_sales_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["status"], "success")
        self.assertEqual(res_json["data"]["cleaned_row_count"], 5)

    def test_04_empty_file_upload(self):
        """Tests that uploading an empty file returns HTTP 400."""
        file_path = os.path.join(self.test_dir, "empty_file.csv")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("empty_file.csv", f, "text/csv")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.json()["detail"].lower())

    def test_05_unsupported_file_type(self):
        """Tests that uploading an unsupported file format (.txt) returns HTTP 400."""
        file_path = os.path.join(self.test_dir, "unsupported_file.txt")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("unsupported_file.txt", f, "text/plain")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("unsupported file type", response.json()["detail"].lower())

    def test_06_missing_sales_columns(self):
        """Tests uploading a dataset missing sales columns returns warnings."""
        file_path = os.path.join(self.test_dir, "missing_columns.csv")
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/upload",
                files={"file": ("missing_columns.csv", f, "text/csv")},
                headers=self.headers
            )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        data = res_json["data"]
        self.assertTrue(len(data["warnings"]) > 0)
        self.assertIsNone(data["calculated_kpis"]["total_revenue"])

if __name__ == "__main__":
    unittest.main()
