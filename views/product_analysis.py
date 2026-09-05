"""
Product Analysis View Component (Phase 3 Portfolio Analytics).
Renders top & bottom product rankings, category contribution %, and unit sales performance.
"""

import requests
import streamlit as st
import pandas as pd
from components.chart_card import render_chart_placeholder
from components.charts import render_top_products_chart, render_category_revenue_chart

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

def render_product_analysis_view():
    """Renders Product Analysis page layout."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: inherit;">📦 Product & Category Portfolio Analytics</h2>
            <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
                Identify top SKUs, revenue contribution percentages, unit sales volume, and underperforming items.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    analytics = fetch_analytics()
    prod_data = analytics.get("product_analysis", {}) if analytics else {}
    cat_data = analytics.get("category_analysis", {}) if analytics else {}

    if analytics and (prod_data.get("available") or cat_data.get("available")):
        col1, col2 = st.columns(2)
        with col1:
            render_top_products_chart(prod_data)
        with col2:
            render_category_revenue_chart(cat_data)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # Product Tables
        tbl_col1, tbl_col2 = st.columns(2)
        
        with tbl_col1:
            st.markdown("### 🏆 Top Products by Revenue")
            top_prods = prod_data.get("top_products_by_revenue", [])
            df_top = pd.DataFrame(top_prods)
            
            if len(df_top) > 0:
                name_col = [c for c in df_top.columns if c not in ["revenue", "quantity", "profit", "revenue_contribution_pct"]][0]
                rows_html = []
                for _, r in df_top.iterrows():
                    rows_html.append(
                        f"<tr>"
                        f"<td style='font-weight:600;'>{r[name_col]}</td>"
                        f"<td>${r['revenue']:,.2f}</td>"
                        f"<td>{r['quantity']:,}</td>"
                        f"<td>{r['revenue_contribution_pct']:.1f}%</td>"
                        f"</tr>"
                    )
                table_html = f"""
                <table class="data-table">
                    <thead><tr><th>Product Name</th><th>Revenue</th><th>Units</th><th>Contribution %</th></tr></thead>
                    <tbody>{''.join(rows_html)}</tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)

        with tbl_col2:
            st.markdown("### 🔻 Bottom 10 Products by Revenue")
            bot_prods = prod_data.get("bottom_products_by_revenue", [])
            df_bot = pd.DataFrame(bot_prods)
            
            if len(df_bot) > 0:
                name_col = [c for c in df_bot.columns if c not in ["revenue", "quantity", "profit", "revenue_contribution_pct"]][0]
                rows_html = []
                for _, r in df_bot.iterrows():
                    rows_html.append(
                        f"<tr>"
                        f"<td style='font-weight:600;'>{r[name_col]}</td>"
                        f"<td>${r['revenue']:,.2f}</td>"
                        f"<td>{r['quantity']:,}</td>"
                        f"<td>{r['revenue_contribution_pct']:.1f}%</td>"
                        f"</tr>"
                    )
                table_html = f"""
                <table class="data-table">
                    <thead><tr><th>Product Name</th><th>Revenue</th><th>Units</th><th>Contribution %</th></tr></thead>
                    <tbody>{''.join(rows_html)}</tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)

    else:
        st.info("ℹ️ Upload a sales dataset in **Data Upload** to view product & category portfolio analytics.")
        col1, col2 = st.columns(2)
        with col1:
            render_chart_placeholder("Top Products by Revenue", "Ranked view of top SKUs.", "🏆", "Horizontal Bar")
        with col2:
            render_chart_placeholder("Category Sales Comparison", "Revenue comparison per product category.", "🏷️", "Bar Chart")
