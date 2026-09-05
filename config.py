"""
App Configuration & CSS Styling System for AI-Sales-Analytics-Dashboard.
Defines constants, theme styles, fonts, and custom CSS injections.
"""

import os

APP_TITLE = "AI Sales Analytics Dashboard"
APP_SUBTITLE = "Professional Data Analytics & Business Intelligence Portal"
VERSION = "1.0.0 (Phase 1 Frontend Architecture)"

def get_backend_url() -> str:
    """Returns configured backend API URL, defaulting to local FastAPI endpoint."""
    return os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# Navigation Options required by specifications
NAV_OVERVIEW = "Overview"
NAV_SALES = "Sales Analysis"
NAV_CUSTOMER = "Customer Analysis"
NAV_PRODUCT = "Product Analysis"
NAV_AI_INSIGHTS = "AI Insights"
NAV_UPLOAD = "Data Upload"

NAV_OPTIONS = [
    NAV_OVERVIEW,
    NAV_SALES,
    NAV_CUSTOMER,
    NAV_PRODUCT,
    NAV_AI_INSIGHTS,
    NAV_UPLOAD,
]

NAV_ICONS = {
    NAV_OVERVIEW: "📊",
    NAV_SALES: "📈",
    NAV_CUSTOMER: "👥",
    NAV_PRODUCT: "📦",
    NAV_AI_INSIGHTS: "🤖",
    NAV_UPLOAD: "📁",
}

def get_custom_css(is_dark: bool = True) -> str:
    """Generates modern zinc/slate theme CSS for Streamlit UI."""
    
    bg_color = "#090d16" if is_dark else "#f8fafc"
    card_bg = "#111827" if is_dark else "#ffffff"
    card_border = "#1f2937" if is_dark else "#e2e8f0"
    text_primary = "#f9fafb" if is_dark else "#0f172a"
    text_muted = "#9ca3af" if is_dark else "#64748b"
    accent_blue = "#3b82f6"
    subtle_bg = "#1f2937" if is_dark else "#f1f5f9"
    
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Hide standard Streamlit chrome */
    header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
    div[data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container {{
        background-color: {bg_color} !important;
        color: {text_primary} !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .block-container {{
        padding: 1.5rem 2rem 2.5rem !important;
        max-width: 1400px !important;
    }}

    /* Modern Metric Cards */
    .metric-card-container {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .metric-card-container:hover {{
        border-color: {accent_blue};
    }}
    .metric-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }}
    .metric-title {{
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {text_muted};
    }}
    .metric-icon {{
        font-size: 1.1rem;
        opacity: 0.8;
    }}
    .metric-value {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: {text_primary};
        margin-bottom: 0.25rem;
    }}
    .metric-subtitle {{
        font-size: 0.75rem;
        color: {text_muted};
    }}
    .metric-badge {{
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }}
    .badge-info {{
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
    }}

    /* Modern Placeholder Containers */
    .placeholder-card {{
        background-color: {card_bg};
        border: 1px dashed {card_border};
        border-radius: 12px;
        padding: 2rem 1.5rem;
        text-align: center;
        min-height: 280px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }}
    .placeholder-title {{
        font-size: 1rem;
        font-weight: 600;
        color: {text_primary};
        margin-top: 0.5rem;
    }}
    .placeholder-desc {{
        font-size: 0.825rem;
        color: {text_muted};
        max-width: 320px;
        margin-top: 0.25rem;
    }}
    .placeholder-badge {{
        margin-top: 1rem;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 10px;
        background-color: {subtle_bg};
        color: {text_muted};
        border-radius: 9999px;
        font-weight: 600;
    }}

    /* Custom Header Bar */
    .app-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid {card_border};
    }}
    .app-header-title {{
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: {text_primary};
        margin: 0;
    }}
    .app-header-sub {{
        font-size: 0.85rem;
        color: {text_muted};
        margin-top: 2px;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {card_bg} !important;
        border-right: 1px solid {card_border} !important;
    }}

    /* Button styling */
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }}
    </style>
    """
