"""
Customer Analysis View Component (Phase 3 Buyer Intelligence).
Renders customer spending distribution, repeat vs one-time metrics, and top customer rankings.
"""

import requests
import streamlit as st
import pandas as pd
from components.kpi_card import render_kpi_card
from components.chart_card import render_chart_placeholder
from components.charts import render_customer_distribution_chart

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

def render_customer_analysis_view():
    """Renders Customer Analysis page layout."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: inherit;">👥 Customer Behavior & Value Insights</h2>
            <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
                Analyze buyer spending tiers, purchase frequency, and repeat customer retention.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    analytics = fetch_analytics()
    cust_data = analytics.get("customer_analysis", {}) if analytics else {}

    if analytics and cust_data.get("available"):
        # Customer KPI Row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("Total Customers", f"{cust_data['total_customers']:,}", "👥", "Unique buyers", "Live Data")
        with c2:
            render_kpi_card("Avg Rev / Customer", f"${cust_data['avg_revenue_per_customer']:,.2f}", "💵", "Revenue per customer", "Live Data")
        with c3:
            render_kpi_card("Repeat Customers", f"{cust_data['repeat_customers_count']:,}", "🔄", "Multiple purchases", "Live Data")
        with c4:
            render_kpi_card("Repeat Rate %", f"{cust_data['repeat_customer_pct']:.1f}%", "📊", "Retention percentage", "Live Data")

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            render_customer_distribution_chart(cust_data)
            
        with col2:
            st.markdown("### 🏆 Top Customers by Revenue")
            top_cust = cust_data.get("top_customers_by_revenue", [])
            df_top = pd.DataFrame(top_cust)
            
            rows_html = []
            for _, r in df_top.iterrows():
                rows_html.append(
                    f"<tr>"
                    f"<td style='font-weight:600;'>{r['customer_id']}</td>"
                    f"<td>${r['revenue']:,.2f}</td>"
                    f"<td>{r['orders']:,}</td>"
                    f"<td>${r['avg_revenue_per_order']:,.2f}</td>"
                    f"</tr>"
                )
            table_html = f"""
            <table class="data-table">
                <thead><tr><th>Customer ID</th><th>Total Spend</th><th>Orders</th><th>AOV</th></tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Upload a sales dataset in **Data Upload** to view customer retention & spending insights.")
        col1, col2 = st.columns(2)
        with col1:
            render_chart_placeholder("Customer Spending Tiers", "Segmentation of buyers into VIP and regular tiers.", "💎", "Bar Chart")
        with col2:
            render_chart_placeholder("Repeat Purchase Rate", "Proportion of single-time vs loyal returning buyers.", "🔄", "Pie Chart")
