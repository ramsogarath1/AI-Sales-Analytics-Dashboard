"""
Login & Registration View Component (Phase 7A Authentication).
Provides user authentication portal for logging in or creating a new user account.
"""

import requests
import streamlit as st
from config import get_backend_url

def get_auth_url() -> str:
    return f"{get_backend_url()}/api/auth"

def extract_error_message(res, default_msg: str) -> str:
    """Safely extracts human-readable error message from backend HTTP response."""
    try:
        payload = res.json()
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, dict):
                msg = detail.get("message") or detail.get("detail")
                if isinstance(msg, str) and msg.strip():
                    return msg
            elif isinstance(detail, str) and detail.strip():
                return detail
            msg = payload.get("message")
            if isinstance(msg, str) and msg.strip():
                return msg
    except Exception:
        pass
    return default_msg

def render_login_view():
    """Renders Login and Registration forms with session state management."""
    
    st.markdown(
        """
        <div style="max-width: 480px; margin: 2rem auto; text-align: center;">
            <h2 style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;">🔐 AI Sales Analytics Portal</h2>
            <p style="font-size: 0.9rem; color: #9ca3af;">
                Sign in to access your secure sales dashboards, BI analytics, statistical insights, and AI Executive Analyst.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab_login, tab_register = st.tabs(["🔑 Log In", "📝 Create Account"])
        
        with tab_login:
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="user@example.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                submit_login = st.form_submit_button("⚡ Log In", use_container_width=True)
                
                if submit_login:
                    if not email or not password:
                        st.error("Please fill in both email and password fields.")
                    else:
                        with st.spinner("Authenticating credentials..."):
                            try:
                                res = requests.post(
                                    f"{get_auth_url()}/login",
                                    json={"email": email, "password": password},
                                    timeout=10
                                )
                                if res.status_code == 200:
                                    data = res.json()
                                    st.session_state.auth_token = data.get("access_token")
                                    st.session_state.user_email = data.get("user", {}).get("email", email)
                                    st.session_state.user_id = data.get("user", {}).get("user_id")
                                    st.success("✅ Login successful!")
                                    st.rerun()
                                else:
                                    err_msg = extract_error_message(res, "Invalid email or password.")
                                    st.error(f"❌ {err_msg}")
                            except requests.exceptions.ConnectionError:
                                st.error(f"⚠️ Backend Offline: Could not connect to FastAPI server at `{get_backend_url()}`.")
                            except Exception as ex:
                                st.error(f"❌ Login Error: {str(ex)}")

        with tab_register:
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            with st.form("register_form"):
                reg_email = st.text_input("Email Address", placeholder="newuser@example.com", key="reg_email")
                reg_password = st.text_input("Password (min 8 chars)", type="password", placeholder="••••••••", key="reg_password")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="reg_confirm")
                submit_reg = st.form_submit_button("✨ Register Account", use_container_width=True)
                
                if submit_reg:
                    if not reg_email or not reg_password:
                        st.error("Please fill in all required fields.")
                    elif len(reg_password) < 8:
                        st.error("Password must be at least 8 characters long.")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Creating user account..."):
                            try:
                                res = requests.post(
                                    f"{get_auth_url()}/register",
                                    json={"email": reg_email, "password": reg_password},
                                    timeout=10
                                )
                                if res.status_code == 201 or res.status_code == 200:
                                    st.success("✅ Account created successfully! Logging you in...")
                                    # Auto-login after registration
                                    login_res = requests.post(
                                        f"{get_auth_url()}/login",
                                        json={"email": reg_email, "password": reg_password},
                                        timeout=10
                                    )
                                    if login_res.status_code == 200:
                                        data = login_res.json()
                                        st.session_state.auth_token = data.get("access_token")
                                        st.session_state.user_email = data.get("user", {}).get("email", reg_email)
                                        st.session_state.user_id = data.get("user", {}).get("user_id")
                                        st.rerun()
                                else:
                                    err_msg = extract_error_message(res, "Registration failed.")
                                    st.error(f"❌ {err_msg}")
                            except Exception as ex:
                                st.error(f"❌ Registration Error: {str(ex)}")
