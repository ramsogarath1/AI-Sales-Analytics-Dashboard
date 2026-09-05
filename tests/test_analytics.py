import sys
import os
import unittest
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_analytics_secret_key_32bytes!"

from backend.main import app

class TestPhase3Analytics(unittest.TestCase):

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
        email = "analyticstest@example.com"
        pwd = "password123"
        cls.client.post("/api/auth/register", json={"email": email, "password": pwd})
        login_res = cls.client.post("/api/auth/login", json={"email": email, "password": pwd})
        cls.token = login_res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

        with get_db_session() as db:
            db.query(CacheRecord).delete()
            db.query(DatasetRecord).delete()
        clear_active_dataset()


    def test_01_analytics_before_upload(self):
        """Verifies GET /api/analytics returns status no_data when no dataset is uploaded."""
        response = self.client.get("/api/analytics", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["status"], "no_data")
        self.assertIsNone(res_json["analytics"])

    def test_02_analytics_after_valid_upload(self):
        """Verifies analytics calculations on valid_sales_data.csv."""
        file_path = os.path.join(self.test_dir, "valid_sales_data.csv")
        with open(file_path, "rb") as f:
            upload_res = self.client.post(
                "/api/upload",
                files={"file": ("valid_sales_data.csv", f, "text/csv")},
                headers=self.headers
            )
        self.assertEqual(upload_res.status_code, 200)

        # Call GET /api/analytics
        res = self.client.get("/api/analytics", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertEqual(res_json["status"], "success")

        analytics = res_json["analytics"]
        self.assertIsNotNone(analytics)

        # 1. General KPIs Verification
        kpis = analytics["kpis"]
        self.assertEqual(kpis["total_revenue"], 915.5)
        self.assertEqual(kpis["total_orders"], 5)
        self.assertEqual(kpis["total_customers"], 4)
        self.assertEqual(kpis["average_order_value"], 183.1)
        self.assertEqual(kpis["total_quantity"], 9)
        self.assertEqual(kpis["total_profit"], 235.0)

        # 2. Time Analysis Verification
        time_ana = analytics["time_analysis"]
        self.assertTrue(time_ana["available"])
        monthly = time_ana["monthly_revenue"]
        self.assertEqual(len(monthly), 1)
        self.assertEqual(monthly[0]["year_month"], "2025-01")
        self.assertEqual(monthly[0]["revenue"], 915.5)

        # 3. Product Analysis Verification
        prod_ana = analytics["product_analysis"]
        self.assertTrue(prod_ana["available"])
        top_prods = prod_ana["top_products_by_revenue"]
        self.assertEqual(len(top_prods), 5)
        # Standardized column name is product_name
        self.assertEqual(top_prods[0]["product_name"], "Ergonomic Chair")
        self.assertEqual(top_prods[0]["revenue"], 400.0)

        # 4. Category Analysis Verification
        cat_ana = analytics["category_analysis"]
        self.assertTrue(cat_ana["available"])
        cats = cat_ana["categories"]
        self.assertEqual(len(cats), 3)

        # 5. Customer Analysis Verification
        cust_ana = analytics["customer_analysis"]
        self.assertTrue(cust_ana["available"])
        self.assertEqual(cust_ana["total_customers"], 4)
        self.assertEqual(cust_ana["repeat_customers_count"], 1)

        # 6. Regional Analysis Verification
        reg_ana = analytics["regional_analysis"]
        self.assertTrue(reg_ana["available"])
        self.assertEqual(len(reg_ana["regions"]), 4)

if __name__ == "__main__":
    unittest.main()
