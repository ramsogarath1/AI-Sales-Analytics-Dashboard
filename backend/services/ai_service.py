"""
AI Executive Analyst & Provider Service Abstraction.
Supports OpenAI, Gemini, and deterministic Mock/Fallback providers with environment configuration.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
try:
    from backend.services.analytics_engine import AnalyticsEngine
    from backend.services.insights_engine import InsightsEngine
except ImportError:
    from services.analytics_engine import AnalyticsEngine
    from services.insights_engine import InsightsEngine


SYSTEM_PROMPT = """You are a senior professional Data Analyst and Executive Business Consultant.
Your task is to analyze sales data and answer executive questions.

CRITICAL ANALYST RULES:
1. Use ONLY the supplied analytics context JSON.
2. Never invent numbers, trends, or missing facts.
3. Do NOT claim causation unless explicitly supported by the supplied data.
4. Keep explanations clear, professional, concise, and business-focused.
5. If the supplied context does not contain enough information to answer a question, explicitly state: "The uploaded dataset does not contain enough information to answer this."
6. Always quote exact numbers and values from the context when available.
"""

# Simple in-memory response cache to prevent redundant API calls
_AI_RESPONSE_CACHE: Dict[str, Any] = {}

def get_env_var(key: str, default: str = "") -> str:
    """Reads environment variable with fallback."""
    return os.environ.get(key, default).strip()

def is_ai_configured() -> bool:
    """Checks if a valid external AI provider key is configured."""
    provider = get_env_var("AI_PROVIDER", "none").lower()
    if provider == "mock":
        return True
    elif provider == "openai":
        key = get_env_var("OPENAI_API_KEY")
        return bool(key and key != "your_openai_api_key_here")
    elif provider == "gemini":
        key = get_env_var("GEMINI_API_KEY")
        return bool(key and key != "your_gemini_api_key_here")
    return False

class BaseAIProvider:
    """Abstract Base Class for AI Providers."""
    def generate_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
        
    def ask(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class MockAIProvider(BaseAIProvider):
    """
    Deterministic Fallback Provider.
    Generates rule-based analyst summaries & answers strictly from context when no API key is set.
    """
    def generate_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        kpis = context.get("analytics", {}).get("kpis", {})
        insights = context.get("insights", {})
        summary_meta = insights.get("summary", {})

        total_rev = kpis.get("total_revenue", 0.0) or 0.0
        total_orders = kpis.get("total_orders", 0) or 0
        aov = kpis.get("average_order_value", 0.0) or 0.0
        total_cust = kpis.get("total_customers")

        summary_text = (
            f"Gross revenue for the ingested dataset reached ${total_rev:,.2f} across {total_orders:,} completed transactions, "
            f"yielding an Average Order Value (AOV) of ${aov:,.2f}. "
        )
        if total_cust:
            summary_text += f"The active catalog served {total_cust:,} unique purchasing customers. "

        findings = []
        for g in insights.get("growth", []):
            findings.append(g["description"])
        for p in insights.get("products", []):
            findings.append(p["description"])
        for c in insights.get("categories", []):
            findings.append(c["description"])

        if not findings:
            findings = [f"Dataset contains {total_orders} order transactions generating ${total_rev:,.2f} in sales."]

        risks_list = [r["description"] for r in insights.get("risks", [])]
        if not risks_list:
            risks_list = ["No critical business risks or negative margin indicators detected in current data."]

        anomalies_list = [a["description"] for a in insights.get("anomalies", [])]

        recs = [
            "Monitor high-performing product SKUs to ensure adequate inventory levels.",
            "Focus marketing efforts on top-performing sales regions to maximize acquisition efficiency."
        ]
        if kpis.get("profit_margin_pct") is not None and kpis["profit_margin_pct"] < 15.0:
            recs.append("Review discounting strategies to improve overall gross profit margins.")

        return {
            "status": "success",
            "provider": "mock",
            "summary": summary_text,
            "key_findings": findings,
            "anomalies": anomalies_list,
            "risks": risks_list,
            "opportunities": [g["description"] for g in insights.get("growth", [])] or ["Expand distribution in leading product categories."],
            "recommendations": recs
        }

    def ask(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = question.lower()
        kpis = context.get("analytics", {}).get("kpis", {})
        insights = context.get("insights", {})

        # Keyword mapping to context metrics
        if "revenue" in q_lower or "sales" in q_lower or "performance" in q_lower or "decrease" in q_lower or "growth" in q_lower:
            rev = kpis.get("total_revenue", 0.0)
            orders = kpis.get("total_orders", 0)
            aov = kpis.get("average_order_value", 0.0)
            growth_info = insights.get("growth", [])
            trend_desc = growth_info[0]["description"] if growth_info else "Revenue trajectories follow uploaded order records."
            answer = f"Total Gross Revenue is ${rev:,.2f} across {orders:,} orders with an AOV of ${aov:,.2f}. Trend analysis: {trend_desc}"
            
        elif "risk" in q_lower or "warning" in q_lower or "threat" in q_lower:
            risks = insights.get("risks", [])
            if risks:
                risk_text = " • ".join([r["description"] for r in risks])
                answer = f"Identified Risk Indicators: {risk_text}"
            else:
                answer = "No critical business risks or negative margin warnings were detected in the uploaded dataset."

        elif "product" in q_lower or "sku" in q_lower or "best" in q_lower or "item" in q_lower:
            prods = insights.get("products", [])
            if prods:
                prod_text = " • ".join([p["description"] for p in prods])
                answer = f"Product Performance: {prod_text}"
            else:
                answer = "Product column information is not available in the uploaded dataset."

        elif "category" in q_lower or "dept" in q_lower:
            cats = insights.get("categories", [])
            if cats:
                cat_text = " • ".join([c["description"] for c in cats])
                answer = f"Category Performance: {cat_text}"
            else:
                answer = "Category column information is not available in the uploaded dataset."

        elif "recommendation" in q_lower or "suggest" in q_lower or "action" in q_lower:
            answer = "Management Recommendations: 1. Maintain inventory buffer for top revenue SKUs. 2. Focus regional campaigns on high-conversion territories. 3. Monitor discounting impact on gross profit margin."

        else:
            answer = "The uploaded dataset does not contain enough information to answer this."

        return {
            "status": "success",
            "provider": "mock",
            "question": question,
            "answer": answer
        }

class OpenAIProvider(BaseAIProvider):
    """OpenAI API Provider implementation."""
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"

    def _call_openai_chat(self, messages: List[Dict[str, str]]) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            return res_json["choices"][0]["message"]["content"]

    def generate_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt_content = f"Supply Analytics Context JSON:\n{json.dumps(context, indent=2)}\n\nGenerate an Executive Business Summary JSON with keys: summary (string), key_findings (array of strings), risks (array of strings), opportunities (array of strings), recommendations (array of strings)."
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content}
        ]
        try:
            raw_resp = self._call_openai_chat(messages)
            # Clean possible markdown block wrappers ```json ... ```
            cleaned = raw_resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
            parsed["status"] = "success"
            parsed["provider"] = "openai"
            return parsed
        except Exception as ex:
            # Fallback to Mock Provider if external API fails
            fallback = MockAIProvider().generate_summary(context)
            fallback["provider"] = "openai (fallback to mock)"
            fallback["warning"] = f"OpenAI API call failed: {str(ex)}"
            return fallback

    def ask(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt_content = f"Supply Analytics Context JSON:\n{json.dumps(context, indent=2)}\n\nQuestion: {question}\n\nProvide a direct, concise business analyst answer using ONLY the context above."
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content}
        ]
        try:
            answer = self._call_openai_chat(messages)
            return {
                "status": "success",
                "provider": "openai",
                "question": question,
                "answer": answer.strip()
            }
        except Exception as ex:
            fallback = MockAIProvider().ask(question, context)
            fallback["provider"] = "openai (fallback to mock)"
            fallback["warning"] = f"OpenAI API call failed: {str(ex)}"
            return fallback

def get_ai_provider() -> BaseAIProvider:
    """Factory function instantiating configured AI Provider."""
    provider_type = get_env_var("AI_PROVIDER", "none").lower()
    
    if provider_type == "openai":
        api_key = get_env_var("OPENAI_API_KEY")
        if api_key and api_key != "your_openai_api_key_here":
            model = get_env_var("OPENAI_MODEL", "gpt-4o-mini")
            return OpenAIProvider(api_key=api_key, model=model)
            
    return MockAIProvider()

class AIService:
    """Main Orchestrator for AI Executive Analyst Features."""
    
    @classmethod
    def generate_executive_summary(cls, df, detected_cols, file_info) -> Dict[str, Any]:
        if df is None:
            return {
                "status": "no_data",
                "message": "No sales dataset uploaded yet. Upload a dataset via POST /api/upload.",
                "summary": "No data available."
            }

        analytics = AnalyticsEngine.compute_full_analytics(df, detected_cols)
        insights = InsightsEngine.generate_all_insights(df, detected_cols)
        context = {
            "file_info": file_info,
            "analytics": analytics,
            "insights": insights
        }

        cache_key = f"summary_{file_info.get('filename')}"
        if cache_key in _AI_RESPONSE_CACHE:
            return _AI_RESPONSE_CACHE[cache_key]

        provider = get_ai_provider()
        result = provider.generate_summary(context)
        _AI_RESPONSE_CACHE[cache_key] = result
        return result

    @classmethod
    def ask_data_analyst(cls, question: str, df, detected_cols, file_info) -> Dict[str, Any]:
        if df is None:
            return {
                "status": "no_data",
                "question": question,
                "answer": "The uploaded dataset does not contain enough information to answer this."
            }

        analytics = AnalyticsEngine.compute_full_analytics(df, detected_cols)
        insights = InsightsEngine.generate_all_insights(df, detected_cols)
        context = {
            "file_info": file_info,
            "analytics": analytics,
            "insights": insights
        }

        cache_key = f"ask_{file_info.get('filename')}_{question.strip().lower()}"
        if cache_key in _AI_RESPONSE_CACHE:
            return _AI_RESPONSE_CACHE[cache_key]

        provider = get_ai_provider()
        result = provider.ask(question, context)
        _AI_RESPONSE_CACHE[cache_key] = result
        return result
