"""
Reusable Chart Placeholder Container Component.
Renders clean placeholder areas for dashboard visualizations prior to dataset upload.
"""

import streamlit as st

def render_chart_placeholder(title: str, subtitle: str, icon: str = "📈", chart_type: str = "Line Chart"):
    """
    Renders a styled container for visualization placeholders.
    
    Args:
        title: Section title (e.g., "Monthly Sales Trend")
        subtitle: Subtext description of expected chart
        icon: Display emoji/icon
        chart_type: Expected chart type badge
    """
    html_code = f"""
    <div class="placeholder-card">
        <div style="font-size: 2.2rem; opacity: 0.85;">{icon}</div>
        <div class="placeholder-title">{title}</div>
        <div class="placeholder-desc">{subtitle}</div>
        <div class="placeholder-badge">Expected Viz: {chart_type} • Phase 2</div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
