"""
Reusable Metric Card Component for rendering KPI widgets.
"""

import streamlit as st

def render_kpi_card(title: str, value: str, icon: str = "📊", subtitle: str = "Awaiting Data Upload", badge_text: str = "Phase 1 Placeholder"):
    """
    Renders a styled HTML KPI Metric Card.
    
    Args:
        title: KPI Title (e.g. "Total Revenue")
        value: KPI Metric Value (e.g. "$0.00")
        icon: Display emoji/icon
        subtitle: Subtext description
        badge_text: Status badge text
    """
    html_code = f"""
    <div class="metric-card-container">
        <div class="metric-header">
            <span class="metric-title">{title}</span>
            <span class="metric-icon">{icon}</span>
        </div>
        <div class="metric-value">{value}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem;">
            <span class="metric-subtitle">{subtitle}</span>
            <span class="metric-badge badge-info">{badge_text}</span>
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
