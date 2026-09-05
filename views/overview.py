"""
Overview Dashboard View Component (Phase 3 Interactive BI Dashboard).
Connects to GET /api/analytics and renders real Plotly visualizations and live KPIs.
"""

import requests
import streamlit as st
from components.kpi_card import render_kpi_card
from components.chart_card import render_chart_placeholder
from components.charts import (
    render_monthly_revenue_chart,
    render_category_revenue_chart,
    render_top_products_chart,
    render_regional_revenue_chart
)

from config import get_backend_url

def get_auth_headers():
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def fetch_analytics():
    """Fetches analytics data from FastAPI backend with session caching."""
    try:
        url = f"{get_backend_url()}/api/analytics"
        res = requests.get(url, headers=get_auth_headers(), timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                st.session_state.analytics_data = data.get("analytics")
                st.session_state.analytics_file_info = data.get("file_info")
                return data.get("analytics")
    except Exception:
        pass
    return st.session_state.get("analytics_data")

def render_overview_view():
    """Renders the Overview Dashboard page layout."""
    
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: inherit;">📊 Executive Overview</h2>
            <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
                High-level business summary, revenue metrics, and interactive sales visualizations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    analytics = fetch_analytics()
    has_data = analytics is not None and "kpis" in analytics
    kpis = analytics.get("kpis", {}) if has_data else {}

    rev_str = f"${kpis['total_revenue']:,.2f}" if (has_data and kpis.get("total_revenue") is not None) else "$0.00"
    orders_str = f"{kpis['total_orders']:,}" if (has_data and kpis.get("total_orders") is not None) else "0"
    cust_str = f"{kpis['total_customers']:,}" if (has_data and kpis.get("total_customers") is not None) else "0"
    aov_str = f"${kpis['average_order_value']:,.2f}" if (has_data and kpis.get("average_order_value") is not None) else "$0.00"
    badge_str = "Live Dataset" if has_data else "Awaiting Data Upload"

    # KPI Cards Row (4 Columns for Desktop/Laptop)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        render_kpi_card("Total Revenue", rev_str, "💰", "Gross sales total", badge_str)
    with kpi_col2:
        render_kpi_card("Total Orders", orders_str, "🛍️", "Completed transactions", badge_str)
    with kpi_col3:
        render_kpi_card("Total Customers", cust_str, "👥", "Unique purchasers", badge_str)
    with kpi_col4:
        render_kpi_card("Average Order Value", aov_str, "🏷️", "Revenue per transaction", badge_str)

    st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)

    if has_data:
        # Real Interactive Plotly Charts Grid
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            render_monthly_revenue_chart(analytics.get("time_analysis", {}))
        with row1_col2:
            render_category_revenue_chart(analytics.get("category_analysis", {}))

        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            render_top_products_chart(analytics.get("product_analysis", {}))
        with row2_col2:
            render_regional_revenue_chart(analytics.get("regional_analysis", {}))
    else:
        # Fallback Placeholder Grid
        st.info("ℹ️ **No active dataset loaded**: Upload a sales dataset in **Data Upload** to view live interactive Plotly charts.")
        
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            render_chart_placeholder("Monthly Sales Trend", "Month-over-month revenue velocity and trajectories.", "📈", "Line Chart")
        with row1_col2:
            render_chart_placeholder("Sales by Category", "Gross revenue distribution across product categories.", "📊", "Bar Chart")

        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            render_chart_placeholder("Top Products", "Ranked view of top revenue-generating SKUs.", "🏆", "Horizontal Bar")
        with row2_col2:
            render_chart_placeholder("Regional Sales", "Geographic revenue allocation and territory share.", "🗺️", "Pie / Donut Chart")
