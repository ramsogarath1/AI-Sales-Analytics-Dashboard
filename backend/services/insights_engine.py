"""
Statistical Intelligence & Insights Engine for AI Sales Analytics Dashboard.
Performs Z-score anomaly detection, trend & growth analysis, concentration risk assessment,
and generates structured statistical business insights.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from services.analytics_engine import AnalyticsEngine

class InsightsEngine:

    @staticmethod
    def detect_revenue_anomalies(time_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detects revenue spikes and drops using sample Z-score outlier detection.
        Adaptive Threshold: Z > 1.5 for small samples (N <= 8), Z > 2.0 for larger samples.
        """
        anomalies = []
        if not time_data or not time_data.get("available"):
            return anomalies

        monthly = time_data.get("monthly_revenue", [])
        if len(monthly) < 3:
            daily = time_data.get("daily_revenue", [])
            series_data = daily
            date_key = "date"
        else:
            series_data = monthly
            date_key = "year_month"

        if len(series_data) < 3:
            return anomalies

        revs = [item["revenue"] for item in series_data if item.get("revenue") is not None]
        if len(revs) < 3:
            return anomalies

        mean_rev = float(np.mean(revs))
        std_rev = float(np.std(revs, ddof=1)) if len(revs) > 1 else 0.0

        if std_rev == 0.0:
            return anomalies

        threshold = 1.5 if len(revs) <= 8 else 2.0

        for item in series_data:
            rev = item.get("revenue")
            period = item.get(date_key, "Unknown Period")
            if rev is None:
                continue

            z_score = (rev - mean_rev) / std_rev

            if z_score > threshold:
                dev_pct = ((rev - mean_rev) / mean_rev) * 100 if mean_rev > 0 else 0
                anomalies.append({
                    "type": "anomaly",
                    "subtype": "revenue_spike",
                    "title": f"Unusual Revenue Spike in {period}",
                    "description": f"Revenue of ${rev:,.2f} in period {period} is statistically higher than average (${mean_rev:,.2f}) by +{dev_pct:.1f}% (Z-Score: +{z_score:.2f}).",
                    "metric_value": f"${rev:,.2f}",
                    "period": period,
                    "severity": "medium" if z_score < 2.5 else "high",
                    "confidence": "High"
                })
            elif z_score < -threshold:
                dev_pct = ((mean_rev - rev) / mean_rev) * 100 if mean_rev > 0 else 0
                anomalies.append({
                    "type": "anomaly",
                    "subtype": "revenue_drop",
                    "title": f"Unusual Revenue Drop in {period}",
                    "description": f"Revenue of ${rev:,.2f} in period {period} dropped significantly below average (${mean_rev:,.2f}) by -{dev_pct:.1f}% (Z-Score: {z_score:.2f}).",
                    "metric_value": f"${rev:,.2f}",
                    "period": period,
                    "severity": "high",
                    "confidence": "High"
                })

        return anomalies

    @staticmethod
    def detect_growth_trends(time_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies strongest growth periods, largest declines, and sustained trend streaks."""
        growth_insights = []
        if not time_data or not time_data.get("available"):
            return growth_insights

        monthly = time_data.get("monthly_revenue", [])
        if len(monthly) < 2:
            return growth_insights

        growth_items = [m for m in monthly if m.get("mom_growth_pct") is not None]
        if not growth_items:
            return growth_insights

        # 1. Strongest Growth Period
        max_growth = max(growth_items, key=lambda x: x["mom_growth_pct"])
        if max_growth["mom_growth_pct"] > 0:
            growth_insights.append({
                "type": "growth",
                "subtype": "strongest_growth",
                "title": f"Peak Revenue Growth Momentum ({max_growth['year_month']})",
                "description": f"Month {max_growth['year_month']} achieved the highest MoM growth velocity at +{max_growth['mom_growth_pct']:.1f}%, generating ${max_growth['revenue']:,.2f}.",
                "metric_value": f"+{max_growth['mom_growth_pct']:.1f}%",
                "period": max_growth["year_month"],
                "severity": "info",
                "confidence": "High"
            })

        # 2. Largest Decline Period
        min_growth = min(growth_items, key=lambda x: x["mom_growth_pct"])
        if min_growth["mom_growth_pct"] < 0:
            growth_insights.append({
                "type": "growth",
                "subtype": "largest_decline",
                "title": f"Sharpest Revenue Contraction ({min_growth['year_month']})",
                "description": f"Month {min_growth['year_month']} experienced the largest sales contraction at {min_growth['mom_growth_pct']:.1f}%, dropping revenue to ${min_growth['revenue']:,.2f}.",
                "metric_value": f"{min_growth['mom_growth_pct']:.1f}%",
                "period": min_growth["year_month"],
                "severity": "medium",
                "confidence": "High"
            })

        # 3. Streak Analysis (Sustained Growth / Decline)
        growth_streaks = 0
        decline_streaks = 0
        current_type = None

        for item in growth_items:
            pct = item["mom_growth_pct"]
            if pct > 0:
                if current_type == "growth":
                    growth_streaks += 1
                else:
                    current_type = "growth"
                    growth_streaks = 1
            elif pct < 0:
                if current_type == "decline":
                    decline_streaks += 1
                else:
                    current_type = "decline"
                    decline_streaks = 1

        if growth_streaks >= 2:
            growth_insights.append({
                "type": "growth",
                "subtype": "sustained_growth",
                "title": "Sustained Multi-Month Growth Streak",
                "description": f"Revenue has demonstrated positive MoM growth for {growth_streaks} consecutive periods, indicating upward business momentum.",
                "metric_value": f"{growth_streaks} Consecutive Months",
                "period": "Recent Months",
                "severity": "info",
                "confidence": "High"
            })

        return growth_insights

    @staticmethod
    def detect_product_insights(prod_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates product performance leaders, bottom SKUs, and concentration metrics."""
        insights = []
        if not prod_data or not prod_data.get("available"):
            return insights

        top_by_rev = prod_data.get("top_products_by_revenue", [])
        if top_by_rev:
            top_sku = top_by_rev[0]
            name_key = [k for k in top_sku.keys() if k not in ["revenue", "quantity", "profit", "revenue_contribution_pct"]][0]
            insights.append({
                "type": "product",
                "subtype": "leader",
                "title": f"Top Performing SKU: {top_sku[name_key]}",
                "description": f"The leading product SKU '{top_sku[name_key]}' generated ${top_sku['revenue']:,.2f}, representing {top_sku['revenue_contribution_pct']:.1f}% of total product sales.",
                "metric_value": f"${top_sku['revenue']:,.2f}",
                "period": "Overall",
                "severity": "info",
                "confidence": "High"
            })

            top_1_share = top_sku.get("revenue_contribution_pct", 0)
            if top_1_share >= 35.0:
                insights.append({
                    "type": "product",
                    "subtype": "product_concentration",
                    "title": "High Single-Product Revenue Concentration",
                    "description": f"A single product SKU '{top_sku[name_key]}' generates {top_1_share:.1f}% of total company sales. High dependency on one SKU poses inventory and demand risks.",
                    "metric_value": f"{top_1_share:.1f}% Share",
                    "period": "Overall",
                    "severity": "high",
                    "confidence": "High"
                })

        return insights

    @staticmethod
    def detect_category_insights(cat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates category leadership, revenue share, and dominance insights."""
        insights = []
        if not cat_data or not cat_data.get("available"):
            return insights

        cats = cat_data.get("categories", [])
        if cats:
            top_cat = cats[0]
            name_key = [k for k in top_cat.keys() if k not in ["revenue", "orders", "profit", "revenue_contribution_pct"]][0]
            insights.append({
                "type": "category",
                "subtype": "category_leader",
                "title": f"Category Leader: {top_cat[name_key]}",
                "description": f"Category '{top_cat[name_key]}' drives the majority of catalog revenue (${top_cat['revenue']:,.2f}), accounting for {top_cat['revenue_contribution_pct']:.1f}% of overall sales.",
                "metric_value": f"{top_cat['revenue_contribution_pct']:.1f}% Share",
                "period": "Overall",
                "severity": "info",
                "confidence": "High"
            })

            if top_cat.get("revenue_contribution_pct", 0) >= 60.0:
                insights.append({
                    "type": "category",
                    "subtype": "category_dependency",
                    "title": "Single-Category Revenue Dependency",
                    "description": f"Category '{top_cat[name_key]}' accounts for {top_cat['revenue_contribution_pct']:.1f}% of total sales. Business revenue is heavily reliant on a single product category.",
                    "metric_value": f"{top_cat['revenue_contribution_pct']:.1f}% Share",
                    "period": "Overall",
                    "severity": "medium",
                    "confidence": "High"
                })

        return insights

    @staticmethod
    def detect_regional_insights(reg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates geographic top regions, underperforming territories, and regional share."""
        insights = []
        if not reg_data or not reg_data.get("available"):
            return insights

        regs = reg_data.get("regions", [])
        if regs:
            top_reg = regs[0]
            name_key = [k for k in top_reg.keys() if k not in ["revenue", "orders", "profit", "revenue_contribution_pct"]][0]
            insights.append({
                "type": "region",
                "subtype": "top_region",
                "title": f"Top Performing Territory: {top_reg[name_key]}",
                "description": f"Region '{top_reg[name_key]}' leads geographic sales with ${top_reg['revenue']:,.2f} in revenue across {top_reg['orders']:,} orders ({top_reg['revenue_contribution_pct']:.1f}% share).",
                "metric_value": f"${top_reg['revenue']:,.2f}",
                "period": "Overall",
                "severity": "info",
                "confidence": "High"
            })

            if len(regs) > 1:
                bottom_reg = regs[-1]
                b_name_key = [k for k in bottom_reg.keys() if k not in ["revenue", "orders", "profit", "revenue_contribution_pct"]][0]
                insights.append({
                    "type": "region",
                    "subtype": "weakest_region",
                    "title": f"Underperforming Territory: {bottom_reg[b_name_key]}",
                    "description": f"Region '{bottom_reg[b_name_key]}' generated the lowest revenue (${bottom_reg['revenue']:,.2f}), representing only {bottom_reg['revenue_contribution_pct']:.1f}% of total sales.",
                    "metric_value": f"{bottom_reg['revenue_contribution_pct']:.1f}% Share",
                    "period": "Overall",
                    "severity": "low",
                    "confidence": "High"
                })

        return insights

    @staticmethod
    def detect_business_risks(df: pd.DataFrame, analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scans dataset for volatility risk, recent revenue decline, and low-margin warnings."""
        risks = []

        # 1. Sales Volatility Risk via Coefficient of Variation (CV = std / mean)
        time_data = analytics.get("time_analysis", {})
        if time_data and time_data.get("available"):
            monthly = time_data.get("monthly_revenue", [])
            if len(monthly) >= 3:
                revs = [m["revenue"] for m in monthly if m.get("revenue") is not None]
                if len(revs) >= 3 and np.mean(revs) > 0:
                    cv = float(np.std(revs, ddof=1) / np.mean(revs))
                    if cv > 0.5:
                        risks.append({
                            "type": "risk",
                            "subtype": "high_volatility",
                            "title": "High Monthly Revenue Volatility Detected",
                            "description": f"Monthly revenue exhibits high fluctuation (Coefficient of Variation: {cv:.2f}). Unpredictable month-to-month sales velocity creates cash flow forecasting risks.",
                            "metric_value": f"CV: {cv:.2f}",
                            "period": "Time Series",
                            "severity": "high",
                            "confidence": "High"
                        })

            # 2. Recent Revenue Contraction Risk (Last Month < Prev Month by > 15%)
            if len(monthly) >= 2:
                last_m = monthly[-1]
                prev_m = monthly[-2]
                if last_m.get("mom_growth_pct") is not None and last_m["mom_growth_pct"] <= -15.0:
                    risks.append({
                        "type": "risk",
                        "subtype": "recent_decline",
                        "title": f"Recent Sales Contraction Warning ({last_m['year_month']})",
                        "description": f"Latest month ({last_m['year_month']}) revenue contracted by {last_m['mom_growth_pct']:.1f}% compared to {prev_m['year_month']}.",
                        "metric_value": f"{last_m['mom_growth_pct']:.1f}% Decline",
                        "period": last_m["year_month"],
                        "severity": "medium",
                        "confidence": "High"
                    })

        # 3. Profit Margin Risk (if Profit < 10% or negative)
        kpis = analytics.get("kpis", {})
        margin = kpis.get("profit_margin_pct")
        if margin is not None:
            if margin < 0:
                risks.append({
                    "type": "risk",
                    "subtype": "negative_margin",
                    "title": "Critical Profit Margin Loss Warning",
                    "description": f"Overall profit margin is negative ({margin:.1f}%). Business costs exceed gross revenue across ingested transactions.",
                    "metric_value": f"{margin:.1f}% Margin",
                    "period": "Overall",
                    "severity": "high",
                    "confidence": "High"
                })
            elif margin < 10.0:
                risks.append({
                    "type": "risk",
                    "subtype": "low_margin",
                    "title": "Low Profit Margin Alert",
                    "description": f"Overall gross profit margin is low at {margin:.1f}%. Slim margins leave little buffer against supply chain or discount pressure.",
                    "metric_value": f"{margin:.1f}% Margin",
                    "period": "Overall",
                    "severity": "medium",
                    "confidence": "High"
                })

        return risks

    @classmethod
    def generate_all_insights(cls, df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Orchestrates full statistical insights payload across all analytical dimensions."""
        analytics = AnalyticsEngine.compute_full_analytics(df, detected_cols)
        
        anomalies = cls.detect_revenue_anomalies(analytics.get("time_analysis", {}))
        growth = cls.detect_growth_trends(analytics.get("time_analysis", {}))
        products = cls.detect_product_insights(analytics.get("product_analysis", {}))
        categories = cls.detect_category_insights(analytics.get("category_analysis", {}))
        regions = cls.detect_regional_insights(analytics.get("regional_analysis", {}))
        risks = cls.detect_business_risks(df, analytics)

        total_insights = len(anomalies) + len(growth) + len(products) + len(categories) + len(regions) + len(risks)

        summary = {
            "total_insights": total_insights,
            "anomalies_detected": len(anomalies),
            "risks_identified": len(risks),
            "growth_opportunities": len(growth),
            "product_insights": len(products),
            "category_insights": len(categories),
            "regional_insights": len(regions)
        }

        return {
            "summary": summary,
            "anomalies": anomalies,
            "growth": growth,
            "products": products,
            "categories": categories,
            "regions": regions,
            "risks": risks
        }
