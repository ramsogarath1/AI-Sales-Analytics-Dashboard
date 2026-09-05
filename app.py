"""
AI Sales Analytics Dashboard - Main Streamlit Application Entry Point.
Phase 7A Route Protection & Authentication Controller.
"""

import streamlit as st
from config import (
    APP_TITLE, APP_SUBTITLE, get_custom_css,
    NAV_OVERVIEW, NAV_SALES, NAV_CUSTOMER, NAV_PRODUCT, NAV_AI_INSIGHTS, NAV_UPLOAD
)
from components.sidebar import render_sidebar
from views.overview import render_overview_view
from views.sales_analysis import render_sales_analysis_view
from views.customer_analysis import render_customer_analysis_view
from views.product_analysis import render_product_analysis_view
from views.ai_insights import render_ai_insights_view
from views.data_upload import render_data_upload_view
from views.login import render_login_view

def main():
    # 1. Streamlit Page Configuration (Must be first Streamlit command)
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. Theme & Authentication State Initialization
    if "theme_dark" not in st.session_state:
        st.session_state.theme_dark = True

    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None

    # 3. Inject Theme CSS System
    st.markdown(get_custom_css(is_dark=st.session_state.theme_dark), unsafe_allow_html=True)

    # 4. Route Guard: Unauthenticated Users Redirected to Login
    if not st.session_state.auth_token:
        render_login_view()
        return

    # 5. Render Sidebar Navigation & Capture Selected Page
    selected_page = render_sidebar()

    # 6. Top Bar Header, User Account Info & Theme Toggle
    header_col1, header_col2, header_col3 = st.columns([5, 2, 1])
    with header_col1:
        st.markdown(
            f"""
            <div class="app-header">
                <div>
                    <h1 class="app-header-title">⚡ {APP_TITLE}</h1>
                    <div class="app-header-sub">{APP_SUBTITLE}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with header_col2:
        user_email = st.session_state.get("user_email", "Authenticated User")
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 6px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: #60a5fa;">👤 {user_email}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user_email = None
            st.session_state.user_id = None
            st.session_state.processed_data = None
            st.rerun()

    with header_col3:
        theme_icon = "☀️ Light" if st.session_state.theme_dark else "🌙 Dark"
        if st.button(theme_icon, key="theme_toggle_btn", help="Toggle Dark / Light visual theme"):
            st.session_state.theme_dark = not st.session_state.theme_dark
            st.rerun()

    # 7. Route Controller to Protected View Modules
    if selected_page == NAV_OVERVIEW:
        render_overview_view()
    elif selected_page == NAV_SALES:
        render_sales_analysis_view()
    elif selected_page == NAV_CUSTOMER:
        render_customer_analysis_view()
    elif selected_page == NAV_PRODUCT:
        render_product_analysis_view()
    elif selected_page == NAV_AI_INSIGHTS:
        render_ai_insights_view()
    elif selected_page == NAV_UPLOAD:
        render_data_upload_view()
    else:
        render_overview_view()

if __name__ == "__main__":
    main()
