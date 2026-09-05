"""
Sidebar Component providing primary navigation and theme controls.
"""

import streamlit as st
from config import NAV_OPTIONS, NAV_ICONS, NAV_OVERVIEW, APP_TITLE, VERSION

def render_sidebar():
    """
    Renders sidebar navigation and controls.
    
    Returns:
        selected_nav (str): Currently selected page title
    """
    with st.sidebar:
        # App branding header
        st.markdown(
            f"""
            <div style="padding: 0.8rem 0 1.2rem 0; border-bottom: 1px solid rgba(156, 163, 175, 0.15); margin-bottom: 1.2rem;">
                <div style="font-size: 1.15rem; font-weight: 700; color: #3b82f6; display: flex; align-items: center; gap: 8px;">
                    ⚡ AI Sales Analytics
                </div>
                <div style="font-size: 0.72rem; color: #9ca3af; margin-top: 4px;">
                    Data Analyst Portfolio App • {VERSION}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #9ca3af; margin-bottom: 0.5rem;'>Navigation</div>", unsafe_allow_html=True)
        
        # Navigation Radio Selection with icons
        formatted_options = [f"{NAV_ICONS[opt]} {opt}" for opt in NAV_OPTIONS]
        
        selected_index = 0
        if "selected_page" in st.session_state:
            try:
                selected_index = NAV_OPTIONS.index(st.session_state.selected_page)
            except ValueError:
                selected_index = 0

        nav_choice = st.radio(
            label="Main Menu",
            options=formatted_options,
            index=selected_index,
            label_visibility="collapsed"
        )

        # Extract clean nav option name without icon
        clean_nav = nav_choice.split(" ", 1)[1] if " " in nav_choice else nav_choice
        st.session_state.selected_page = clean_nav

        st.markdown("<div style='margin-top: 2rem; border-top: 1px solid rgba(156, 163, 175, 0.15); padding-top: 1.2rem;'></div>", unsafe_allow_html=True)
        
        # Status Card
        st.markdown(
            """
            <div style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 10px; padding: 0.9rem; font-size: 0.78rem;">
                <div style="font-weight: 600; color: #60a5fa; margin-bottom: 4px;">📌 Phase 1 Active</div>
                <div style="color: #9ca3af; line-height: 1.4;">
                    Frontend UI & component architecture initialized. Ingest your dataset in <b>Data Upload</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        return clean_nav
