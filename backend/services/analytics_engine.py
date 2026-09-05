"""
Analytics Processing Engine for AI Sales Analytics Dashboard.
Computes comprehensive metrics across Time, Product, Category, Customer, and Regional dimensions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def clean_float(val: Any, decimals: int = 2) -> Optional[float]:
    """Safely converts numpy/pandas float to python float, replacing NaN/Inf with None."""
    if val is None or pd.isna(val) or np.isinf(val):
        return None
    return round(float(val), decimals)

def clean_int(val: Any) -> Optional[int]:
    """Safely converts numpy/pandas int to python int, replacing NaN/Inf with None."""
    if val is None or pd.isna(val) or np.isinf(val):
        return None
    return int(val)

def records_with_none(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts a DataFrame to records, replacing float NaN with None for valid JSON serialization."""
    clean_df = df.replace({np.nan: None})
    return clean_df.to_dict(orient="records")

class AnalyticsEngine:
    
    @staticmethod
    def compute_general_kpis(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        sales_col = detected_cols.get("sales")
        order_col = detected_cols.get("order_id")
        cust_col = detected_cols.get("customer_id")
        qty_col = detected_cols.get("quantity")
        profit_col = detected_cols.get("profit")

        # Revenue
        total_rev = None
        if sales_col and sales_col in df.columns:
            total_rev = clean_float(df[sales_col].sum(skipna=True))
        elif qty_col and "unit_price" in df.columns:
            total_rev = clean_float((df[qty_col] * df["unit_price"]).sum(skipna=True))

        # Orders
        total_orders = df[order_col].nunique(dropna=True) if (order_col and order_col in df.columns) else len(df)
        total_orders = clean_int(total_orders) or 1

        # Customers
        total_cust = df[cust_col].nunique(dropna=True) if (cust_col and cust_col in df.columns) else None
        total_cust = clean_int(total_cust)

        # Quantity
        total_qty = df[qty_col].sum(skipna=True) if (qty_col and qty_col in df.columns) else None
        total_qty = clean_int(total_qty)

        # AOV
        aov = clean_float(total_rev / total_orders) if (total_rev is not None and total_orders > 0) else None

        # Avg Qty Per Order
        avg_qty_order = clean_float(total_qty / total_orders) if (total_qty is not None and total_orders > 0) else None

        # Profit & Margin
        total_profit = df[profit_col].sum(skipna=True) if (profit_col and profit_col in df.columns) else None
        total_profit = clean_float(total_profit)

        profit_margin_pct = None
        if total_profit is not None and total_rev is not None and total_rev > 0:
            profit_margin_pct = clean_float((total_profit / total_rev) * 100)

        return {
            "total_revenue": total_rev,
            "total_orders": total_orders,
            "total_customers": total_cust,
            "total_quantity": total_qty,
            "average_order_value": aov,
            "avg_quantity_per_order": avg_qty_order,
            "total_profit": total_profit,
            "profit_margin_pct": profit_margin_pct
        }

    @staticmethod
    def compute_time_analytics(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        date_col = detected_cols.get("order_date")
        sales_col = detected_cols.get("sales")
        order_col = detected_cols.get("order_id")

        if not date_col or date_col not in df.columns or not sales_col or sales_col in [None]:
            return {"available": False, "reason": "Order Date or Sales column not identified in dataset"}

        df_time = df.copy()
        df_time["dt"] = pd.to_datetime(df_time[date_col], format="mixed", errors="coerce")
        df_time = df_time.dropna(subset=["dt"])

        if len(df_time) == 0:
            return {"available": False, "reason": "No valid date values found in Order Date column"}

        df_time["sales_num"] = pd.to_numeric(df_time[sales_col], errors="coerce").fillna(0)

        # 1. Daily Revenue
        df_daily = df_time.groupby(df_time["dt"].dt.strftime("%Y-%m-%d")).agg(
            revenue=("sales_num", "sum"),
            orders=(order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        ).reset_index()
        df_daily.columns = ["date", "revenue", "orders"]

        # 2. Weekly Revenue
        df_time["year_week"] = df_time["dt"].dt.strftime("%G-W%V")
        df_weekly = df_time.groupby("year_week").agg(
            revenue=("sales_num", "sum"),
            orders=(order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        ).reset_index().sort_values("year_week")
        df_weekly["revenue"] = df_weekly["revenue"].apply(clean_float)

        # 3. Monthly Revenue & MoM Growth
        df_time["year_month"] = df_time["dt"].dt.strftime("%Y-%m")
        df_monthly = df_time.groupby("year_month").agg(
            revenue=("sales_num", "sum"),
            orders=(order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        ).reset_index().sort_values("year_month")

        df_monthly["mom_growth_pct"] = df_monthly["revenue"].pct_change() * 100
        df_monthly["revenue"] = df_monthly["revenue"].apply(clean_float)
        df_monthly["mom_growth_pct"] = df_monthly["mom_growth_pct"].apply(lambda v: clean_float(v, 1))

        # 4. Yearly Revenue
        df_time["year"] = df_time["dt"].dt.strftime("%Y")
        df_yearly = df_time.groupby("year").agg(
            revenue=("sales_num", "sum"),
            orders=(order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        ).reset_index().sort_values("year")
        df_yearly["revenue"] = df_yearly["revenue"].apply(clean_float)

        return {
            "available": True,
            "daily_revenue": records_with_none(df_daily),
            "weekly_revenue": records_with_none(df_weekly),
            "monthly_revenue": records_with_none(df_monthly),
            "yearly_revenue": records_with_none(df_yearly)
        }

    @staticmethod
    def compute_product_analytics(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        prod_col = detected_cols.get("product")
        sales_col = detected_cols.get("sales")
        qty_col = detected_cols.get("quantity")
        profit_col = detected_cols.get("profit")

        if not prod_col or prod_col not in df.columns:
            return {"available": False, "reason": "Product column not identified in dataset"}

        df_prod = df.copy()
        df_prod["sales_num"] = pd.to_numeric(df_prod[sales_col], errors="coerce").fillna(0) if sales_col else 0
        df_prod["qty_num"] = pd.to_numeric(df_prod[qty_col], errors="coerce").fillna(0) if qty_col else 1
        df_prod["profit_num"] = pd.to_numeric(df_prod[profit_col], errors="coerce").fillna(0) if profit_col else 0

        agg_dict = {
            "revenue": ("sales_num", "sum"),
            "quantity": ("qty_num", "sum")
        }
        if profit_col:
            agg_dict["profit"] = ("profit_num", "sum")

        grouped = df_prod.groupby(prod_col).agg(**agg_dict).reset_index()
        total_rev = grouped["revenue"].sum() or 1.0

        grouped["revenue_contribution_pct"] = (grouped["revenue"] / total_rev) * 100
        grouped["revenue"] = grouped["revenue"].apply(clean_float)
        grouped["quantity"] = grouped["quantity"].apply(clean_int)
        grouped["revenue_contribution_pct"] = grouped["revenue_contribution_pct"].apply(lambda v: clean_float(v, 1))

        if profit_col:
            grouped["profit"] = grouped["profit"].apply(clean_float)

        top_by_revenue = records_with_none(grouped.sort_values("revenue", ascending=False).head(10))
        top_by_quantity = records_with_none(grouped.sort_values("quantity", ascending=False).head(10))
        bottom_by_revenue = records_with_none(grouped.sort_values("revenue", ascending=True).head(10))

        return {
            "available": True,
            "top_products_by_revenue": top_by_revenue,
            "top_products_by_quantity": top_by_quantity,
            "bottom_products_by_revenue": bottom_by_revenue
        }

    @staticmethod
    def compute_category_analytics(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        cat_col = detected_cols.get("category")
        sales_col = detected_cols.get("sales")
        order_col = detected_cols.get("order_id")
        profit_col = detected_cols.get("profit")

        if not cat_col or cat_col not in df.columns:
            return {"available": False, "reason": "Category column not identified in dataset"}

        df_cat = df.copy()
        df_cat["sales_num"] = pd.to_numeric(df_cat[sales_col], errors="coerce").fillna(0) if sales_col else 0
        df_cat["profit_num"] = pd.to_numeric(df_cat[profit_col], errors="coerce").fillna(0) if profit_col else 0

        agg_dict = {
            "revenue": ("sales_num", "sum"),
            "orders": (order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        }
        if profit_col:
            agg_dict["profit"] = ("profit_num", "sum")

        grouped = df_cat.groupby(cat_col).agg(**agg_dict).reset_index()
        total_rev = grouped["revenue"].sum() or 1.0

        grouped["revenue_contribution_pct"] = (grouped["revenue"] / total_rev) * 100
        grouped["revenue"] = grouped["revenue"].apply(clean_float)
        grouped["orders"] = grouped["orders"].apply(clean_int)
        grouped["revenue_contribution_pct"] = grouped["revenue_contribution_pct"].apply(lambda v: clean_float(v, 1))

        if profit_col:
            grouped["profit"] = grouped["profit"].apply(clean_float)

        return {
            "available": True,
            "categories": records_with_none(grouped.sort_values("revenue", ascending=False))
        }

    @staticmethod
    def compute_customer_analytics(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        cust_col = detected_cols.get("customer_id")
        sales_col = detected_cols.get("sales")
        order_col = detected_cols.get("order_id")

        if not cust_col or cust_col not in df.columns:
            return {"available": False, "reason": "Customer ID/Name column not identified in dataset"}

        df_cust = df.copy()
        df_cust["sales_num"] = pd.to_numeric(df_cust[sales_col], errors="coerce").fillna(0) if sales_col else 0

        grouped = df_cust.groupby(cust_col).agg(
            revenue=("sales_num", "sum"),
            orders=(order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        ).reset_index()

        grouped["avg_revenue_per_order"] = (grouped["revenue"] / grouped["orders"]).apply(clean_float)
        grouped["revenue"] = grouped["revenue"].apply(clean_float)
        grouped["orders"] = grouped["orders"].apply(clean_int)

        total_customers = len(grouped)
        total_rev = df_cust["sales_num"].sum()
        avg_rev_per_customer = clean_float(total_rev / total_customers) if total_customers > 0 else 0.0

        repeat_cnt = len(grouped[grouped["orders"] > 1])
        one_time_cnt = len(grouped[grouped["orders"] == 1])
        repeat_pct = clean_float((repeat_cnt / total_customers) * 100, 1) if total_customers > 0 else 0.0

        top_by_revenue = records_with_none(grouped.sort_values("revenue", ascending=False).head(10))
        top_by_orders = records_with_none(grouped.sort_values("orders", ascending=False).head(10))

        spending_records = grouped["revenue"].dropna().tolist()

        return {
            "available": True,
            "total_customers": total_customers,
            "avg_revenue_per_customer": avg_rev_per_customer,
            "repeat_customers_count": repeat_cnt,
            "one_time_customers_count": one_time_cnt,
            "repeat_customer_pct": repeat_pct,
            "top_customers_by_revenue": top_by_revenue,
            "top_customers_by_orders": top_by_orders,
            "customer_spending_distribution": spending_records
        }

    @staticmethod
    def compute_regional_analytics(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        reg_col = detected_cols.get("region")
        sales_col = detected_cols.get("sales")
        order_col = detected_cols.get("order_id")
        profit_col = detected_cols.get("profit")

        if not reg_col or reg_col not in df.columns:
            return {"available": False, "reason": "Region column not identified in dataset"}

        df_reg = df.copy()
        df_reg["sales_num"] = pd.to_numeric(df_reg[sales_col], errors="coerce").fillna(0) if sales_col else 0
        df_reg["profit_num"] = pd.to_numeric(df_reg[profit_col], errors="coerce").fillna(0) if profit_col else 0

        agg_dict = {
            "revenue": ("sales_num", "sum"),
            "orders": (order_col, "nunique") if (order_col and order_col in df.columns) else ("sales_num", "count")
        }
        if profit_col:
            agg_dict["profit"] = ("profit_num", "sum")

        grouped = df_reg.groupby(reg_col).agg(**agg_dict).reset_index()
        total_rev = grouped["revenue"].sum() or 1.0

        grouped["revenue_contribution_pct"] = (grouped["revenue"] / total_rev) * 100
        grouped["revenue"] = grouped["revenue"].apply(clean_float)
        grouped["orders"] = grouped["orders"].apply(clean_int)
        grouped["revenue_contribution_pct"] = grouped["revenue_contribution_pct"].apply(lambda v: clean_float(v, 1))

        if profit_col:
            grouped["profit"] = grouped["profit"].apply(clean_float)

        return {
            "available": True,
            "regions": records_with_none(grouped.sort_values("revenue", ascending=False))
        }

    @classmethod
    def compute_full_analytics(cls, df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
        return {
            "kpis": cls.compute_general_kpis(df, detected_cols),
            "time_analysis": cls.compute_time_analytics(df, detected_cols),
            "product_analysis": cls.compute_product_analytics(df, detected_cols),
            "category_analysis": cls.compute_category_analytics(df, detected_cols),
            "customer_analysis": cls.compute_customer_analytics(df, detected_cols),
            "regional_analysis": cls.compute_regional_analytics(df, detected_cols)
        }
