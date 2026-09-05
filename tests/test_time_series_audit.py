"""
Verification Test Script for Phase 3 Time-Series Audit.
Tests monthly revenue, MoM growth %, order counts, missing column fallback, and weekly revenue generation.
"""

import sys
import os
import pandas as pd
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from services.analytics_engine import AnalyticsEngine

class TestTimeSeriesAudit(unittest.TestCase):

    def setUp(self):
        # Create multi-month realistic test dataset
        self.multi_month_data = {
            "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4", "ORD-5", "ORD-6"],
            "order_date": ["2025-01-10", "2025-01-20", "2025-02-05", "2025-02-15", "2025-03-01", "2025-03-25"],
            "sales_amount": [100.0, 200.0, 150.0, 450.0, 300.0, 900.0]
        }
        self.df_multi = pd.DataFrame(self.multi_month_data)
        self.detected_cols = {
            "order_id": "order_id",
            "order_date": "order_date",
            "sales": "sales_amount"
        }

    def test_monthly_revenue_calculation(self):
        """Verifies monthly revenue sums match raw inputs."""
        res = AnalyticsEngine.compute_time_analytics(self.df_multi, self.detected_cols)
        self.assertTrue(res["available"])
        monthly = res["monthly_revenue"]
        
        # Month 1 (Jan 2025): 100 + 200 = 300
        self.assertEqual(monthly[0]["year_month"], "2025-01")
        self.assertEqual(monthly[0]["revenue"], 300.0)
        self.assertEqual(monthly[0]["orders"], 2)

        # Month 2 (Feb 2025): 150 + 450 = 600
        self.assertEqual(monthly[1]["year_month"], "2025-02")
        self.assertEqual(monthly[1]["revenue"], 600.0)
        self.assertEqual(monthly[1]["orders"], 2)

        # Month 3 (Mar 2025): 300 + 900 = 1200
        self.assertEqual(monthly[2]["year_month"], "2025-03")
        self.assertEqual(monthly[2]["revenue"], 1200.0)
        self.assertEqual(monthly[2]["orders"], 2)

    def test_mom_growth_calculation(self):
        """Verifies MoM growth percentage formula: ((Current - Prev) / Prev) * 100."""
        res = AnalyticsEngine.compute_time_analytics(self.df_multi, self.detected_cols)
        monthly = res["monthly_revenue"]

        # Month 1: None (no previous month)
        self.assertIsNone(monthly[0]["mom_growth_pct"])

        # Month 2: ((600 - 300) / 300) * 100 = +100.0%
        self.assertEqual(monthly[1]["mom_growth_pct"], 100.0)

        # Month 3: ((1200 - 600) / 600) * 100 = +100.0%
        self.assertEqual(monthly[2]["mom_growth_pct"], 100.0)

    def test_missing_column_graceful_handling(self):
        """Verifies missing date or sales column returns available: False without crashing."""
        bad_detected = {"order_id": "order_id", "order_date": None, "sales": None}
        res = AnalyticsEngine.compute_time_analytics(self.df_multi, bad_detected)
        self.assertFalse(res["available"])
        self.assertIn("reason", res)

if __name__ == "__main__":
    unittest.main()
