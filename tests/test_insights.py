"""
Phase 4 Insights Engine Test Suite.
Verifies Z-score anomaly detection, risk indicators, edge-case dataset resilience, and GET /api/insights API.
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_insights_secret_key_32bytes!"

from backend.main import app
from backend.services.insights_engine import InsightsEngine

class TestPhase4Insights(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = os.path.join(os.path.dirname(__file__), "..", "data", "test_datasets")

        try:
            from backend.services.dataset_store import clear_active_dataset
            from backend.database.connection import get_db_session, init_db
            from backend.database.models import DatasetRecord, CacheRecord
            from backend.utils.rate_limiter import clear_rate_limit_store
        except ImportError:
            from services.dataset_store import clear_active_dataset
            from database.connection import get_db_session, init_db
            from database.models import DatasetRecord, CacheRecord
            from utils.rate_limiter import clear_rate_limit_store

        clear_rate_limit_store()
        init_db()

        # Register & login test user
        email = "insightstest@example.com"
        pwd = "password123"
        cls.client.post("/api/auth/register", json={"email": email, "password": pwd})
        login_res = cls.client.post("/api/auth/login", json={"email": email, "password": pwd})
        cls.token = login_res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

        with get_db_session() as db:
            db.query(CacheRecord).delete()
            db.query(DatasetRecord).delete()
        clear_active_dataset()


    def test_01_insights_before_upload(self):
        """Verifies GET /api/insights returns status no_data cleanly when no file uploaded."""
        res = self.client.get("/api/insights", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertEqual(res_json["status"], "no_data")
        self.assertEqual(res_json["summary"]["total_insights"], 0)

    def test_02_normal_revenue_series(self):
        """Verifies normal revenue series produces insights without crashing or false anomalies."""
        df_normal = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"],
            "sales_amount": [100.0, 105.0, 102.0, 104.0],
            "product_name": ["Widget A", "Widget B", "Widget A", "Widget B"]
        })
        detected = {"order_date": "order_date", "sales": "sales_amount", "product": "product_name"}
        insights = InsightsEngine.generate_all_insights(df_normal, detected)
        self.assertIsNotNone(insights)
        self.assertEqual(len(insights["anomalies"]), 0)  # No extreme spikes/drops

    def test_03_revenue_spike_detection(self):
        """Verifies Z-score detects an extreme revenue spike (Z > 2.0)."""
        df_spike = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01"],
            "sales_amount": [100.0, 100.0, 100.0, 100.0, 1000.0]  # Extreme spike in month 5
        })
        detected = {"order_date": "order_date", "sales": "sales_amount"}
        insights = InsightsEngine.generate_all_insights(df_spike, detected)
        anomalies = insights["anomalies"]
        self.assertTrue(len(anomalies) > 0)
        self.assertEqual(anomalies[0]["subtype"], "revenue_spike")
        self.assertEqual(anomalies[0]["period"], "2025-05")

    def test_04_revenue_drop_detection(self):
        """Verifies Z-score detects an extreme revenue drop (Z < -2.0)."""
        df_drop = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01"],
            "sales_amount": [1000.0, 1000.0, 1000.0, 1000.0, 50.0]  # Extreme drop in month 5
        })
        detected = {"order_date": "order_date", "sales": "sales_amount"}
        insights = InsightsEngine.generate_all_insights(df_drop, detected)
        anomalies = insights["anomalies"]
        self.assertTrue(len(anomalies) > 0)
        self.assertEqual(anomalies[0]["subtype"], "revenue_drop")

    def test_05_missing_date_column(self):
        """Verifies missing date column omits time anomalies without crashing."""
        df_nodate = pd.DataFrame({
            "product_name": ["Item A", "Item B"],
            "sales_amount": [50.0, 75.0]
        })
        detected = {"sales": "sales_amount", "product": "product_name"}
        insights = InsightsEngine.generate_all_insights(df_nodate, detected)
        self.assertEqual(len(insights["anomalies"]), 0)

    def test_06_missing_revenue_column(self):
        """Verifies missing revenue column handles gracefully without crashing."""
        df_norev = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-01-02"],
            "product_name": ["Item A", "Item B"]
        })
        detected = {"order_date": "order_date", "product": "product_name"}
        insights = InsightsEngine.generate_all_insights(df_norev, detected)
        self.assertIsNotNone(insights)

    def test_07_missing_product_category_region(self):
        """Verifies missing dimensional columns omit product/category/region insights without error."""
        df_bare = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-02-01", "2025-03-01"],
            "sales_amount": [100.0, 200.0, 300.0]
        })
        detected = {"order_date": "order_date", "sales": "sales_amount"}
        insights = InsightsEngine.generate_all_insights(df_bare, detected)
        self.assertEqual(len(insights["products"]), 0)
        self.assertEqual(len(insights["categories"]), 0)
        self.assertEqual(len(insights["regions"]), 0)

    def test_08_very_small_dataset(self):
        """Verifies very small dataset (< 3 rows) does not crash."""
        df_small = pd.DataFrame({
            "order_date": ["2025-01-01"],
            "sales_amount": [100.0]
        })
        detected = {"order_date": "order_date", "sales": "sales_amount"}
        insights = InsightsEngine.generate_all_insights(df_small, detected)
        self.assertEqual(len(insights["anomalies"]), 0)

    def test_09_constant_revenue(self):
        """Verifies constant revenue (std = 0) generates zero false anomalies."""
        df_const = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"],
            "sales_amount": [100.0, 100.0, 100.0, 100.0]
        })
        detected = {"order_date": "order_date", "sales": "sales_amount"}
        insights = InsightsEngine.generate_all_insights(df_const, detected)
        self.assertEqual(len(insights["anomalies"]), 0)

    def test_10_zero_negative_revenue(self):
        """Verifies zero/negative revenue/profit generates appropriate risk warnings."""
        df_neg = pd.DataFrame({
            "order_date": ["2025-01-01", "2025-02-01"],
            "sales_amount": [100.0, 100.0],
            "profit": [-50.0, -100.0]
        })
        detected = {"order_date": "order_date", "sales": "sales_amount", "profit": "profit"}
        insights = InsightsEngine.generate_all_insights(df_neg, detected)
        risks = insights["risks"]
        self.assertTrue(any(r["subtype"] == "negative_margin" for r in risks))

    def test_11_api_insights_after_upload(self):
        """Verifies GET /api/insights returns success payload after valid file upload."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            upload_res = self.client.post(
                "/api/upload",
                files={"file": ("valid_sales_data.csv", f, "text/csv")},
                headers=self.headers
            )
        self.assertEqual(upload_res.status_code, 200)

        res = self.client.get("/api/insights", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertEqual(res_json["status"], "success")
        self.assertIn("summary", res_json)

if __name__ == "__main__":
    unittest.main()
