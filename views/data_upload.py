"""
Data Upload & Dataset Management View Component (Phase 7A Protected API Integration).
Connects to FastAPI backend (/api/upload and /api/datasets) using JWT Bearer authentication headers.
Handles dataset switching, dataset deletion, persistent storage metadata, and real-time processing status.
"""

import requests
import streamlit as st
from config import get_backend_url
from components.kpi_card import render_kpi_card

def get_backend_api_url() -> str:
    return f"{get_backend_url()}/api"

def get_auth_headers():
    """Helper returning Authorization header dictionary from Streamlit session state."""
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def fetch_datasets():
    """Helper to retrieve list of uploaded datasets for authenticated user."""
    headers = get_auth_headers()
    try:
        res = requests.get(f"{get_backend_api_url()}/datasets", headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def select_dataset(dataset_id: str):
    """Helper to trigger dataset selection on backend."""
    headers = get_auth_headers()
    try:
        res = requests.post(f"{get_backend_api_url()}/datasets/{dataset_id}/select", headers=headers, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def delete_dataset_api(dataset_id: str):
    """Helper to delete dataset on backend."""
    headers = get_auth_headers()
    try:
        res = requests.delete(f"{get_backend_api_url()}/datasets/{dataset_id}", headers=headers, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def render_data_upload_view():
    """Renders Data Upload and Dataset Management layout for authenticated user."""
    
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: inherit;">📁 Dataset Management & Ingestion Portal</h2>
            <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
                Upload, select, inspect, and manage persistent sales datasets bound to your account.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    headers = get_auth_headers()

    # 1. Dataset Management & Selection Section
    datasets = fetch_datasets()
    
    if datasets:
        st.markdown("### 🗄️ Your Uploaded Datasets")
        
        # Display dataset selection bar
        active_dataset = next((d for d in datasets if d.get("is_active")), None)
        
        col_select, col_actions = st.columns([3, 1])
        
        with col_select:
            dataset_options = {
                f"{d['filename']} ({d['rows'] or 0} rows, {d['columns'] or 0} cols) {'[ACTIVE]' if d.get('is_active') else ''}": d['dataset_id']
                for d in datasets
            }
            default_index = 0
            if active_dataset:
                for idx, (label, d_id) in enumerate(dataset_options.items()):
                    if d_id == active_dataset['dataset_id']:
                        default_index = idx
                        break

            selected_label = st.selectbox(
                "Select Active Dataset for Analysis:",
                options=list(dataset_options.keys()),
                index=default_index,
                key="dataset_select_box"
            )
            selected_id = dataset_options[selected_label]

        with col_actions:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if selected_id != (active_dataset.get("dataset_id") if active_dataset else None):
                if st.button("⚡ Activate Dataset", use_container_width=True, key="btn_activate"):
                    if select_dataset(selected_id):
                        st.session_state.processed_data = None
                        st.success(f"Activated dataset `{selected_id}`.")
                        st.rerun()
                    else:
                        st.error("Failed to activate dataset.")

        # Show Table of Uploaded Datasets
        st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
        ds_cols = st.columns([2, 1, 1, 1, 1, 1])
        ds_cols[0].markdown("**Filename**")
        ds_cols[1].markdown("**Dataset ID**")
        ds_cols[2].markdown("**Rows**")
        ds_cols[3].markdown("**Columns**")
        ds_cols[4].markdown("**Status**")
        ds_cols[5].markdown("**Action**")

        for ds in datasets:
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 1, 1, 1])
            is_act = ds.get("is_active")
            badge = "🟢 Active" if is_act else "⚪ Idle"
            
            c1.markdown(f"**{ds['filename']}**" if is_act else ds['filename'])
            c2.markdown(f"`{ds['dataset_id']}`")
            c3.markdown(f"{ds.get('rows') or 0:,}")
            c4.markdown(f"{ds.get('columns') or 0}")
            c5.markdown(badge)
            
            with c6:
                if st.button("🗑️ Delete", key=f"del_{ds['dataset_id']}", use_container_width=True):
                    if delete_dataset_api(ds['dataset_id']):
                        st.session_state.processed_data = None
                        st.success(f"Deleted dataset `{ds['dataset_id']}`.")
                        st.rerun()
                    else:
                        st.error("Failed to delete dataset.")

        st.markdown("---")

    # 2. File Uploader Section
    st.markdown("### 📤 Upload New Dataset")
    uploaded_file = st.file_uploader(
        label="Upload Sales Data File",
        type=["csv", "xlsx", "xls"],
        help="Upload CSV, XLSX, or XLS files (Max size: 25MB).",
        key="sales_file_uploader"
    )

    if uploaded_file is not None:
        if ("last_uploaded_filename" not in st.session_state or 
            st.session_state.last_uploaded_filename != uploaded_file.name):
            
            with st.spinner(f"⏳ Ingesting & cleaning '{uploaded_file.name}' via FastAPI backend..."):
                try:
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")
                    }
                    
                    response = requests.post(
                        f"{get_backend_api_url()}/upload",
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        st.session_state.processed_data = res_data.get("data")
                        st.session_state.last_uploaded_filename = uploaded_file.name
                        st.success(f"✅ Successfully ingested & saved **'{uploaded_file.name}'**!")
                        st.rerun()
                    else:
                        err_payload = response.json()
                        err_detail = err_payload.get("detail", {})
                        msg = err_detail.get("message") if isinstance(err_detail, dict) else str(err_detail)
                        st.error(f"❌ Upload Failed ({response.status_code}): {msg}")
                        st.session_state.processed_data = None
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"⚠️ Backend Offline: Could not connect to FastAPI server at `{get_backend_url()}`.")
                    st.session_state.processed_data = None
                except Exception as ex:
                    st.error(f"❌ Unexpected Error: {str(ex)}")
                    st.session_state.processed_data = None

    # Render Processed Data Inspection
    if "processed_data" in st.session_state and st.session_state.processed_data is not None:
        data = st.session_state.processed_data
        kpis = data.get("calculated_kpis", {})
        file_info = data.get("file_info", {})

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("### 📊 Active Dataset Summary & Computed KPIs")

        # 1. KPI Cards Row
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            rev_val = f"${kpis['total_revenue']:,.2f}" if kpis.get("total_revenue") is not None else "N/A"
            render_kpi_card("Total Revenue", rev_val, "💰", "Gross sales total", "Active Dataset")
        with kpi_c2:
            orders_val = f"{kpis['total_orders']:,}" if kpis.get("total_orders") is not None else "0"
            render_kpi_card("Total Orders", orders_val, "🛍️", "Unique transactions", "Active Dataset")
        with kpi_c3:
            cust_val = f"{kpis['total_customers']:,}" if kpis.get("total_customers") is not None else "N/A"
            render_kpi_card("Total Customers", cust_val, "👥", "Unique buyers", "Active Dataset")
        with kpi_c4:
            aov_val = f"${kpis['average_order_value']:,.2f}" if kpis.get("average_order_value") is not None else "N/A"
            render_kpi_card("Avg Order Value", aov_val, "🏷️", "Revenue / Transaction", "Active Dataset")

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # 2. File Metadata & Data Health Metrics
        col_meta, col_clean = st.columns(2)
        
        with col_meta:
            st.markdown(
                f"""
                <div class="metric-card-container">
                    <div style="font-weight: 700; font-size: 1rem; margin-bottom: 0.8rem; color: #3b82f6;">
                        📋 Dataset Metadata
                    </div>
                    <div style="font-size: 0.85rem; line-height: 1.8;">
                        <b>Filename:</b> <code>{file_info.get('filename')}</code><br/>
                        <b>Dataset ID:</b> <code>{data.get('dataset_id', file_info.get('dataset_id', 'N/A'))}</code><br/>
                        <b>SHA-256 Hash:</b> <code>{data.get('dataset_hash', file_info.get('dataset_hash', 'N/A'))[:16]}...</code><br/>
                        <b>Cleaned Row Count:</b> {data.get('cleaned_row_count'):,}<br/>
                        <b>Original Columns:</b> {data.get('original_column_count')}<br/>
                        <b>Duplicates Removed:</b> {data.get('duplicate_count')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_clean:
            logs_html = "".join([f"<li>{log}</li>" for log in data.get("cleaning_summary", [])])
            st.markdown(
                f"""
                <div class="metric-card-container">
                    <div style="font-weight: 700; font-size: 1rem; margin-bottom: 0.8rem; color: #10b981;">
                        🧼 Cleaning Operation Log
                    </div>
                    <ul style="font-size: 0.825rem; line-height: 1.6; color: #9ca3af; margin: 0; padding-left: 1.2rem;">
                        {logs_html}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
