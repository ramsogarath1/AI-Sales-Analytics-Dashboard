"""
Phase 7A Multi-User Isolation & Security Test Suite.
Verifies complete server-side dataset ownership enforcement between User A and User B.
Ensures User A cannot view, analyze, retrieve, ask AI about, or delete User B's datasets.
Tests cache isolation between separate user accounts.
"""

import sys
import os
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

os.environ["DATABASE_URL"] = "sqlite:///./test_phase7_isolation.db"
os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_user_isolation_secret_key_32_bytes_minimum!"

from backend.main import app
from backend.database.connection import init_db
from backend.utils.rate_limiter import clear_rate_limit_store

class TestUserIsolation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        clear_rate_limit_store()
        test_db_path = Path("./test_phase7_isolation.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass

        init_db("sqlite:///./test_phase7_isolation.db")
        cls.client = TestClient(app)
        cls.test_dir = os.path.join(project_root, "data", "test_datasets")

        # 1. Register & Login User A
        reg_a = cls.client.post("/api/auth/register", json={"email": "usera@example.com", "password": "passwordUserA123"})
        login_a = cls.client.post("/api/auth/login", json={"email": "usera@example.com", "password": "passwordUserA123"})
        cls.tokenA = login_a.json()["access_token"]
        cls.headersA = {"Authorization": f"Bearer {cls.tokenA}"}
        me_a = cls.client.get("/api/auth/me", headers=cls.headersA)
        cls.userA_id = me_a.json()["user_id"]

        # 2. Register & Login User B
        reg_b = cls.client.post("/api/auth/register", json={"email": "userb@example.com", "password": "passwordUserB123"})
        login_b = cls.client.post("/api/auth/login", json={"email": "userb@example.com", "password": "passwordUserB123"})
        cls.tokenB = login_b.json()["access_token"]
        cls.headersB = {"Authorization": f"Bearer {cls.tokenB}"}
        me_b = cls.client.get("/api/auth/me", headers=cls.headersB)
        cls.userB_id = me_b.json()["user_id"]

        # 3. Upload Dataset A as User A
        csv_a = b"Order_ID,Order_Date,Customer_ID,Product,Category,Region,Sales,Quantity\n101,2025-01-01,C1,Widget A,Cat1,North,500.0,5\n"
        up_a = cls.client.post(
            "/api/upload",
            files={"file": ("dataset_A.csv", csv_a, "text/csv")},
            headers=cls.headersA
        )
        cls.datasetA_id = up_a.json()["dataset_id"]

        # 4. Upload Dataset B as User B
        csv_b = b"Order_ID,Order_Date,Customer_ID,Product,Category,Region,Sales,Quantity\n201,2025-02-01,C2,Gadget B,Cat2,South,999.0,2\n"
        up_b = cls.client.post(
            "/api/upload",
            files={"file": ("dataset_B.csv", csv_b, "text/csv")},
            headers=cls.headersB
        )
        cls.datasetB_id = up_b.json()["dataset_id"]

    @classmethod
    def tearDownClass(cls):
        test_db_path = Path("./test_phase7_isolation.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass

    def test_01_user_dataset_list_isolation(self):
        """Verifies GET /api/datasets returns only datasets owned by authenticated user."""
        # User A list
        res_a = self.client.get("/api/datasets", headers=self.headersA)
        self.assertEqual(res_a.status_code, 200)
        ds_list_a = [d["dataset_id"] for d in res_a.json()]
        self.assertIn(self.datasetA_id, ds_list_a)
        self.assertNotIn(self.datasetB_id, ds_list_a)

        # User B list
        res_b = self.client.get("/api/datasets", headers=self.headersB)
        self.assertEqual(res_b.status_code, 200)
        ds_list_b = [d["dataset_id"] for d in res_b.json()]
        self.assertIn(self.datasetB_id, ds_list_b)
        self.assertNotIn(self.datasetA_id, ds_list_b)

    def test_02_user_dataset_metadata_isolation(self):
        """Verifies User A cannot access User B's dataset metadata (returns HTTP 404)."""
        # User A attempts to read User B's dataset
        res = self.client.get(f"/api/datasets/{self.datasetB_id}", headers=self.headersA)
        self.assertEqual(res.status_code, 404)
        self.assertIn("not found", res.json()["message"].lower())

    def test_03_user_analytics_isolation(self):
        """Verifies User A cannot compute analytics on User B's dataset (returns HTTP 404)."""
        res = self.client.get(f"/api/analytics?dataset_id={self.datasetB_id}", headers=self.headersA)
        self.assertEqual(res.status_code, 404)

    def test_04_user_insights_isolation(self):
        """Verifies User A cannot access statistical insights for User B's dataset (returns HTTP 404)."""
        res = self.client.get(f"/api/insights?dataset_id={self.datasetB_id}", headers=self.headersA)
        self.assertEqual(res.status_code, 404)

    def test_05_user_ai_summary_isolation(self):
        """Verifies User A cannot generate AI summary for User B's dataset (returns HTTP 404)."""
        res = self.client.post("/api/ai/executive-summary", json={"dataset_id": self.datasetB_id}, headers=self.headersA)
        self.assertEqual(res.status_code, 404)

    def test_06_user_ai_ask_isolation(self):
        """Verifies User A cannot ask AI questions about User B's dataset (returns HTTP 404)."""
        payload = {"dataset_id": self.datasetB_id, "question": "What is the total revenue?"}
        res = self.client.post("/api/ai/ask", json=payload, headers=self.headersA)
        self.assertEqual(res.status_code, 404)

    def test_07_user_delete_dataset_isolation(self):
        """Verifies User A cannot delete User B's dataset (returns HTTP 404)."""
        res = self.client.delete(f"/api/datasets/{self.datasetB_id}", headers=self.headersA)
        self.assertEqual(res.status_code, 404)

        # Verify Dataset B still exists safely for User B
        check_b = self.client.get(f"/api/datasets/{self.datasetB_id}", headers=self.headersB)
        self.assertEqual(check_b.status_code, 200)

    def test_08_cache_isolation(self):
        """Verifies query results cached for User B are not accessible to User A."""
        # Prime cache for User B
        b_res = self.client.get(f"/api/analytics?dataset_id={self.datasetB_id}", headers=self.headersB)
        self.assertEqual(b_res.status_code, 200)

        # User A attempts to fetch using User B's dataset ID -> 404 Not Found
        a_res = self.client.get(f"/api/analytics?dataset_id={self.datasetB_id}", headers=self.headersA)
        self.assertEqual(a_res.status_code, 404)

    def test_09_full_cross_user_attack_pattern(self):
        """
        Mandatory Attack Pattern Test:
        1. User B populates cache for Dataset B across analytics, insights, AI summary, and AI ask.
        2. User A attempts to target Dataset B across ALL endpoints using Dataset B's ID.
        3. Verifies ALL endpoints return HTTP 404 DATASET_NOT_FOUND with zero data leakage.
        """
        # Step 1: User B primes all cache layers for Dataset B
        b_ana = self.client.get(f"/api/analytics?dataset_id={self.datasetB_id}", headers=self.headersB)
        self.assertEqual(b_ana.status_code, 200)

        b_ins = self.client.get(f"/api/insights?dataset_id={self.datasetB_id}", headers=self.headersB)
        self.assertEqual(b_ins.status_code, 200)

        b_sum = self.client.post("/api/ai/executive-summary", json={"dataset_id": self.datasetB_id}, headers=self.headersB)
        self.assertEqual(b_sum.status_code, 200)

        b_ask = self.client.post("/api/ai/ask", json={"dataset_id": self.datasetB_id, "question": "What is revenue?"}, headers=self.headersB)
        self.assertEqual(b_ask.status_code, 200)

        # Step 2: User A launches cross-tenant attack using Dataset B's ID across ALL endpoints
        # 1. Dataset detail
        a_detail = self.client.get(f"/api/datasets/{self.datasetB_id}", headers=self.headersA)
        self.assertEqual(a_detail.status_code, 404)

        # 2. Analytics
        a_ana = self.client.get(f"/api/analytics?dataset_id={self.datasetB_id}", headers=self.headersA)
        self.assertEqual(a_ana.status_code, 404)

        # 3. Insights
        a_ins = self.client.get(f"/api/insights?dataset_id={self.datasetB_id}", headers=self.headersA)
        self.assertEqual(a_ins.status_code, 404)

        # 4. AI Executive Summary
        a_sum = self.client.post("/api/ai/executive-summary", json={"dataset_id": self.datasetB_id}, headers=self.headersA)
        self.assertEqual(a_sum.status_code, 404)

        # 5. AI Ask
        a_ask = self.client.post("/api/ai/ask", json={"dataset_id": self.datasetB_id, "question": "What is revenue?"}, headers=self.headersA)
        self.assertEqual(a_ask.status_code, 404)

        # 6. Dataset Delete
        a_del = self.client.delete(f"/api/datasets/{self.datasetB_id}", headers=self.headersA)
        self.assertEqual(a_del.status_code, 404)

        # Step 3: Verify User B's dataset is still fully intact and functional for User B
        b_check = self.client.get(f"/api/datasets/{self.datasetB_id}", headers=self.headersB)
        self.assertEqual(b_check.status_code, 200)

if __name__ == "__main__":
    unittest.main()
