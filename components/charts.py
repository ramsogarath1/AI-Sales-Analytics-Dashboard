"""
Interactive Plotly Chart Generators with Theme Styling for AI Sales Analytics Dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List, Optional

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#9ca3af", size=11),
    margin=dict(l=10, r=10, t=25, b=10),
    xaxis=dict(
        gridcolor="rgba(156, 163, 175, 0.1)",
        zerolinecolor="rgba(156, 163, 175, 0.1)",
        tickfont=dict(size=10, color="#9ca3af"),
    ),
    yaxis=dict(
        gridcolor="rgba(156, 163, 175, 0.1)",
        zerolinecolor="rgba(156, 163, 175, 0.1)",
        tickfont=dict(size=10, color="#9ca3af"),
    ),
)

def render_monthly_revenue_chart(time_data: Dict[str, Any]):
    """Renders 1. Monthly Revenue Trend Line Chart."""
    if not time_data or not time_data.get("available") or not time_data.get("monthly_revenue"):
        st.warning("⚠️ Monthly revenue trend is unavailable for this dataset.")
        return

    df = pd.DataFrame(time_data["monthly_revenue"])
    fig = px.line(
        df, x="year_month", y="revenue",
        markers=True,
        labels={"year_month": "Month", "revenue": "Revenue ($)"},
        color_discrete_sequence=["#3b82f6"]
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=7, color="#60a5fa"))
    fig.update_layout(**PLOT_LAYOUT, height=320)
    fig.update_yaxes(tickprefix="$")

    st.markdown(
        """
        <div class="metric-card-container">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">📈 Monthly Revenue Velocity</div>
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 0.8rem;">Month-over-month revenue trajectories and growth momentum.</div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

def render_category_revenue_chart(cat_data: Dict[str, Any]):
    """Renders 2. Revenue by Category Bar Chart."""
    if not cat_data or not cat_data.get("available") or not cat_data.get("categories"):
        st.warning("⚠️ Category breakdown is unavailable for this dataset.")
        return

    df = pd.DataFrame(cat_data["categories"])
    name_col = [c for c in df.columns if c not in ["revenue", "orders", "profit", "revenue_contribution_pct"]][0]
    fig = px.bar(
        df, x=name_col, y="revenue",
        color=name_col,
        text_auto=".2s",
        labels={name_col: "Category", "revenue": "Revenue ($)"},
        color_discrete_sequence=["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"]
    )
    fig.update_layout(**PLOT_LAYOUT, showlegend=False, height=320)
    fig.update_yaxes(tickprefix="$")

    st.markdown(
        """
        <div class="metric-card-container">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">📊 Revenue by Product Category</div>
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 0.8rem;">Gross sales volume allocated per product category.</div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

def render_top_products_chart(prod_data: Dict[str, Any]):
    """Renders 4. Top 10 Products Horizontal Bar Chart."""
    if not prod_data or not prod_data.get("available") or not prod_data.get("top_products_by_revenue"):
        st.warning("⚠️ Product analytics unavailable for this dataset.")
        return

    df = pd.DataFrame(prod_data["top_products_by_revenue"]).sort_values("revenue", ascending=True)
    name_col = [c for c in df.columns if c not in ["revenue", "quantity", "profit", "revenue_contribution_pct"]][0]
    fig = px.bar(
        df, y=name_col, x="revenue",
        orientation="h",
        text_auto=".2s",
        labels={name_col: "Product SKU", "revenue": "Revenue ($)"},
        color_discrete_sequence=["#10b981"]
    )
    fig.update_layout(**PLOT_LAYOUT, height=320)
    fig.update_xaxes(tickprefix="$")

    st.markdown(
        """
        <div class="metric-card-container">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">🏆 Top 10 Products by Revenue</div>
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 0.8rem;">Highest revenue-generating SKUs ranked.</div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

def render_regional_revenue_chart(reg_data: Dict[str, Any]):
    """Renders 3. Regional Revenue Distribution Chart."""
    if not reg_data or not reg_data.get("available") or not reg_data.get("regions"):
        st.warning("⚠️ Regional analytics unavailable for this dataset.")
        return

    df = pd.DataFrame(reg_data["regions"])
    name_col = [c for c in df.columns if c not in ["revenue", "orders", "profit", "revenue_contribution_pct"]][0]
    fig = px.pie(
        df, names=name_col, values="revenue",
        hole=0.45,
        color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#f43f5e"]
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(**PLOT_LAYOUT, showlegend=False, height=320)

    st.markdown(
        """
        <div class="metric-card-container">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">🗺️ Regional Sales Distribution</div>
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 0.8rem;">Geographic sales share comparison across territories.</div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

def render_orders_vs_revenue_chart(time_data: Dict[str, Any]):
    """Renders 5. Orders vs Revenue Comparison Chart."""
    if not time_data or not time_data.get("available") or not time_data.get("monthly_revenue"):
        st.warning("⚠️ Time trend data unavailable for Orders vs Revenue comparison.")
        return

    df = pd.DataFrame(time_data["monthly_revenue"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["year_month"], y=df["revenue"], name="Revenue ($)", marker_color="#3b82f6", yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["year_month"], y=df["orders"], name="Orders Count", mode="lines+markers", line=dict(color="#f59e0b", width=3), yaxis="y2"))

    fig.update_layout(
        **PLOT_LAYOUT,
        yaxis=dict(title="Revenue ($)", tickprefix="$", gridcolor="rgba(156, 163, 175, 0.1)"),
        yaxis2=dict(title="Orders", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=340
    )

    st.markdown(
        """
        <div class="metric-card-container">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">⚖️ Orders Volume vs Revenue Growth</div>
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 0.8rem;">Comparison between transaction count and total monetary value.</div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

def render_customer_distribution_chart(cust_data: Dict[str, Any]):
    """Renders 6. Customer Revenue Distribution Histogram."""
    if not cust_data or not cust_data.get("available") or not cust_data.get("customer_spending_distribution"):
        st.warning("⚠️ Customer spending distribution unavailable for this dataset.")
        return

    spend_list = cust_data["customer_spending_distribution"]
    df = pd.DataFrame({"spending": spend_list})
    fig = px.histogram(
        df, x="spending",
        nbins=12,
        labels={"spending": "Customer Revenue ($)", "count": "Customer Count"},
        color_discrete_sequence=["#8b5cf6"]
    )
    fig.update_layout(**PLOT_LAYOUT, height=340)
    fig.update_xaxes(tickprefix="$")

    st.markdown(
        """
        <div class="metric-card-container">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">👥 Customer Spending Distribution</div>
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 0.8rem;">Histogram grouping customers by total spending tiers.</div>
        """,
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
