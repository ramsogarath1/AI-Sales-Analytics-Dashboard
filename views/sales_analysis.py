"""
Sales Analysis View Component (Phase 3 Deep-Dive Analytics).
Renders time-series velocity charts, MoM growth metrics, and Orders vs Revenue visualizations.
"""

import requests
import streamlit as st
import pandas as pd
from components.chart_card import render_chart_placeholder
from components.charts import render_monthly_revenue_chart, render_orders_vs_revenue_chart

from config import get_backend_url

def get_auth_headers():
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def fetch_analytics():
    try:
        url = f"{get_backend_url()}/api/analytics"
        res = requests.get(url, headers=get_auth_headers(), timeout=5)
        if res.status_code == 200 and res.json().get("status") == "success":
            return res.json().get("analytics")
    except Exception:
        pass
    return st.session_state.get("analytics_data")

def render_sales_analysis_view():
    """Renders the Sales Analysis page layout with real time-series visualizations."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: inherit;">📈 Detailed Sales & Revenue Analysis</h2>
            <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
                Deep-dive examination of revenue velocity, transaction counts, and month-over-month growth.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    analytics = fetch_analytics()
    time_data = analytics.get("time_analysis", {}) if analytics else {}

    if analytics and time_data.get("available"):
        col1, col2 = st.columns(2)
        with col1:
            render_monthly_revenue_chart(time_data)
        with col2:
            render_orders_vs_revenue_chart(time_data)

        # Monthly Breakdown Data Table
        if time_data.get("monthly_revenue"):
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            st.markdown("### 📅 Monthly Performance Breakdown")
            
            df_monthly = pd.DataFrame(time_data["monthly_revenue"])
            rows_html = []
            for _, row in df_monthly.iterrows():
                mom_str = f"{row['mom_growth_pct']:+.1f}%" if pd.notna(row.get('mom_growth_pct')) else "N/A"
                badge_cls = "color: #10b981;" if "+" in mom_str else ("color: #ef4444;" if "-" in mom_str else "color: #9ca3af;")
                rows_html.append(
                    f"<tr>"
                    f"<td style='font-weight:600;'>{row['year_month']}</td>"
                    f"<td>${row['revenue']:,.2f}</td>"
                    f"<td>{row['orders']:,}</td>"
                    f"<td style='{badge_cls} font-weight:600;'>{mom_str}</td>"
                    f"</tr>"
                )
            
            table_html = f"""
            <table class="data-table">
                <thead><tr><th>Year-Month</th><th>Gross Revenue</th><th>Total Orders</th><th>MoM Growth %</th></tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Upload a sales dataset in **Data Upload** to view time-series revenue analysis.")
        col1, col2 = st.columns(2)
        with col1:
            render_chart_placeholder("Daily & Weekly Sales Velocity", "Granular view of daily revenue fluctuations.", "📅", "Area Chart")
        with col2:
            render_chart_placeholder("Orders vs Revenue", "Dual-axis comparison of order volume vs revenue.", "⚖️", "Grouped Bar Chart")
