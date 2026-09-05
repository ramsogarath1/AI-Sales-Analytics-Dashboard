"""
AI Insights & Executive Analyst View Component (Phase 5 Complete Intelligence Portal).
Displays AI Executive Briefings, interactive Natural Language Chat, and Statistical Insights.
"""

import requests
import streamlit as st
from typing import Dict, Any, List

from config import get_backend_url

def get_auth_headers():
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def fetch_insights_data() -> Dict[str, Any]:
    try:
        url = f"{get_backend_url()}/api/insights"
        res = requests.get(url, headers=get_auth_headers(), timeout=5)
        if res.status_code == 200 and res.json().get("status") == "success":
            return res.json()
    except Exception:
        pass
    return {}

def fetch_ai_summary() -> Dict[str, Any]:
    try:
        url = f"{get_backend_url()}/api/ai/executive-summary"
        res = requests.post(url, headers=get_auth_headers(), timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_ai_answer(question: str) -> Dict[str, Any]:
    try:
        url = f"{get_backend_url()}/api/ai/ask"
        res = requests.post(url, json={"question": question}, headers=get_auth_headers(), timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception as ex:
        return {"status": "error", "answer": f"Error communicating with AI Analyst service: {str(ex)}"}
    return {"status": "error", "answer": "Could not connect to AI Analyst service."}

def render_insight_card(title: str, description: str, metric_value: str, period: str, severity: str, confidence: str, icon: str = "💡"):
    badge_color_map = {
        "high": ("rgba(239, 68, 68, 0.15)", "#f87171", "🚨 High Severity"),
        "medium": ("rgba(245, 158, 11, 0.15)", "#fbbf24", "⚠️ Medium Severity"),
        "low": ("rgba(59, 130, 246, 0.15)", "#60a5fa", "ℹ️ Low Severity"),
        "info": ("rgba(16, 185, 129, 0.15)", "#34d399", "✅ Opportunity")
    }
    bg_badge, text_badge, label_badge = badge_color_map.get(severity.lower(), badge_color_map["info"])

    html_code = f"""
    <div class="metric-card-container" style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div style="font-weight: 700; font-size: 0.95rem; color: inherit;">
                {icon} {title}
            </div>
            <span style="background: {bg_badge}; color: {text_badge}; font-size: 0.72rem; font-weight: 600; padding: 3px 9px; border-radius: 6px;">
                {label_badge}
            </span>
        </div>
        <div style="font-size: 0.825rem; color: #9ca3af; line-height: 1.5; margin-bottom: 0.75rem;">
            {description}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(156, 163, 175, 0.15); padding-top: 0.5rem; font-size: 0.75rem; color: #9ca3af;">
            <span>Period: <b>{period}</b></span>
            <span>Key Metric: <b style="color: #3b82f6;">{metric_value}</b></span>
            <span>Confidence: <b style="color: #34d399;">{confidence}</b></span>
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def render_ai_insights_view():
    """Renders AI Insights & Executive Analyst page layout."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: inherit;">🤖 AI Executive Analyst & Intelligence Center</h2>
            <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
                Executive briefings, natural language data Q&A, Z-score anomaly scans, and business risk indicators.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    insights_payload = fetch_insights_data()
    has_dataset = (insights_payload and insights_payload.get("status") == "success")

    if not has_dataset:
        st.info("ℹ️ **AI Analyst Standby**: Upload a sales dataset in **Data Upload** to activate executive briefings, data chat, and statistical scans.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                <div class="metric-card-container">
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">👔 AI Executive Briefings</div>
                    <div style="font-size: 0.825rem; color: #9ca3af; line-height: 1.5;">
                        Generates natural language executive summaries, key findings, and strategic business recommendations.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                """
                <div class="metric-card-container">
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">💬 Ask Your Data Analyst</div>
                    <div style="font-size: 0.825rem; color: #9ca3af; line-height: 1.5;">
                        Ask natural language questions ("What happened to revenue?") answered strictly using verified dataset metrics.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        return

    # Tabs for AI Executive Analyst & Statistical Insights
    tab_summary, tab_chat, tab_statistical = st.tabs([
        "👔 AI Executive Briefing",
        "💬 Ask Your Data Analyst",
        "📊 Statistical Insights & Anomalies"
    ])

    with tab_summary:
        with st.spinner("🧠 AI Analyst synthesizing executive briefing..."):
            ai_resp = fetch_ai_summary()

        if ai_resp and ai_resp.get("status") == "success":
            provider_tag = f"Powered by {ai_resp.get('provider', 'AI Analyst')}"
            
            st.markdown(
                f"""
                <div class="metric-card-container" style="background: rgba(59, 130, 246, 0.04); border-color: rgba(59, 130, 246, 0.3); margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-weight: 700; font-size: 1.1rem; color: #3b82f6;">👔 Executive Briefing</span>
                        <span style="font-size: 0.72rem; color: #60a5fa; background: rgba(59,130,246,0.15); padding: 2px 8px; border-radius: 6px;">{provider_tag}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: inherit; line-height: 1.6;">
                        {ai_resp.get('summary')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📌 Key Findings")
                for f in ai_resp.get("key_findings", []):
                    st.markdown(f"- {f}")

                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                st.markdown("### 🚀 Growth Opportunities")
                for o in ai_resp.get("opportunities", []):
                    st.markdown(f"- 🟢 {o}")

            with col2:
                st.markdown("### ⚠️ Identified Business Risks")
                for r in ai_resp.get("risks", []):
                    st.markdown(f"- 🔴 {r}")

                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                st.markdown("### 🎯 Recommended Management Actions")
                for rec in ai_resp.get("recommendations", []):
                    st.markdown(f"- ⚡ {rec}")

    with tab_chat:
        st.markdown(
            """
            <div style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.1rem; font-weight: 700; margin: 0;">💬 Natural Language Data Queries</h3>
                <p style="font-size: 0.8rem; color: #9ca3af; margin-top: 2px;">
                    Ask questions about your sales data. Answers are strictly generated from verified dataset context.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("**Quick Example Questions:**")
        q_cols = st.columns(4)
        selected_example = None
        with q_cols[0]:
            if st.button("What happened to revenue?"):
                selected_example = "What happened to revenue?"
        with q_cols[1]:
            if st.button("What are my biggest risks?"):
                selected_example = "What are my biggest risks?"
        with q_cols[2]:
            if st.button("Which products perform best?"):
                selected_example = "Which products perform best?"
        with q_cols[3]:
            if st.button("Give me 3 recommendations"):
                selected_example = "Give me 3 business recommendations."

        user_query = st.text_input(
            label="Type your dataset question:",
            value=selected_example or "",
            placeholder="e.g. Which region generated the highest revenue?",
            key="user_analyst_question"
        )

        if user_query:
            with st.spinner(f"🔍 Analyzing dataset context for: '{user_query}'..."):
                ans_resp = fetch_ai_answer(user_query)

            st.markdown(
                f"""
                <div class="metric-card-container" style="margin-top: 1rem; border-color: #3b82f6;">
                    <div style="font-weight: 600; font-size: 0.85rem; color: #9ca3af; margin-bottom: 0.4rem;">
                        Question: <span style="color: #f9fafb;">"{user_query}"</span>
                    </div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #3b82f6; margin-bottom: 0.5rem;">
                        🧠 AI Analyst Answer:
                    </div>
                    <div style="font-size: 0.88rem; color: inherit; line-height: 1.6;">
                        {ans_resp.get('answer', 'No answer available.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_statistical:
        summary = insights_payload.get("summary", {})
        
        st.markdown("### 📊 Statistical Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Insights", summary.get("total_insights", 0))
        with m2:
            st.metric("Revenue Anomalies", summary.get("anomalies_detected", 0))
        with m3:
            st.metric("Risk Indicators", summary.get("risks_identified", 0))
        with m4:
            st.metric("Growth Drivers", summary.get("growth_opportunities", 0))

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        anomalies = insights_payload.get("anomalies", [])
        if anomalies:
            st.markdown("### 🔍 Revenue Anomalies (Z-Score Detection)")
            for item in anomalies:
                render_insight_card(
                    title=item["title"], description=item["description"],
                    metric_value=item["metric_value"], period=item["period"],
                    severity=item["severity"], confidence=item["confidence"],
                    icon="🚨" if item.get("subtype") == "revenue_drop" else "⚡"
                )

        growth = insights_payload.get("growth", [])
        if growth:
            st.markdown("### 📈 Growth & Trend Patterns")
            for item in growth:
                render_insight_card(
                    title=item["title"], description=item["description"],
                    metric_value=item["metric_value"], period=item["period"],
                    severity=item["severity"], confidence=item["confidence"], icon="🚀"
                )

        risks = insights_payload.get("risks", [])
        if risks:
            st.markdown("### ⚠️ Business Risk Indicators")
            for item in risks:
                render_insight_card(
                    title=item["title"], description=item["description"],
                    metric_value=item["metric_value"], period=item["period"],
                    severity=item["severity"], confidence=item["confidence"], icon="⚠️"
                )
