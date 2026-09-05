"""
Sales Data Processing Engine.
Handles dataset ingestion, inspection, column normalization, data cleaning, column detection, and KPI calculation.
"""

import io
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
try:
    from backend.services.dataset_store import set_active_dataset
except ImportError:
    from services.dataset_store import set_active_dataset


# Keywords dictionary for flexible sales column detection
COLUMN_DETECTION_PATTERNS = {
    "order_id": [r"order_?id", r"trans(action)?_?id", r"invoice_?id", r"receipt_?id", r"^id$"],
    "order_date": [r"order_?date", r"^date$", r"sale_?date", r"trans(action)?_?date", r"timestamp", r"time"],
    "customer_id": [r"cust(omer)?_?id", r"cust(omer)?_?name", r"client_?id", r"buyer_?id", r"^customer$"],
    "product": [r"product_?name", r"^product$", r"item_?name", r"^item$", r"sku", r"title"],
    "category": [r"^category$", r"sub_?category", r"department", r"^dept$", r"prod(uct)?_?cat(egory)?"],
    "region": [r"^region$", r"^country$", r"^state$", r"^city$", r"territory", r"location", r"zone"],
    "quantity": [r"^quantity$", r"^qty$", r"units?_?sold", r"units?", r"item_?count"],
    "sales": [r"^sales$", r"^revenue$", r"total_?amount", r"sales?_?amount", r"gross_?sales", r"^amount$"],
    "profit": [r"^profit$", r"net_?profit", r"margin", r"gross_?margin", r"gain"]
}

def is_text_column(series: pd.Series) -> bool:
    """Helper to detect string/text columns across Pandas 2 & 3 versions."""
    return pd.api.types.is_string_dtype(series) or series.dtype in ["object", "str", "string"]

def load_dataframe_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Reads a CSV or Excel file from byte stream into a Pandas DataFrame."""
    lower_filename = filename.lower()
    
    try:
        if lower_filename.endswith(".csv"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
                    return df
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
            raise ValueError("Failed to parse CSV file with standard character encodings.")
            
        elif lower_filename.endswith((".xlsx", ".xls")):
            engine = "openpyxl" if lower_filename.endswith(".xlsx") else "xlrd"
            df = pd.read_excel(io.BytesIO(file_bytes), engine=engine)
            return df
            
        else:
            raise ValueError(f"Unsupported file format: {filename}")
            
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading dataset '{filename}': {str(err)}"
        )

def normalize_column_names(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, str], List[str]]:
    """
    Normalizes column names by stripping whitespace, casting to lower_snake_case,
    and resolving duplicates safely.
    """
    original_cols = [str(col) for col in df.columns]
    mapping = {}
    normalized_cols = []
    seen = {}
    summary_logs = []

    for orig in original_cols:
        cleaned = orig.strip()
        cleaned = re.sub(r"[^\w\s]", "_", cleaned)
        cleaned = re.sub(r"\s+", "_", cleaned)
        cleaned = re.sub(r"_+", "_", cleaned).strip("_").lower()

        if not cleaned:
            cleaned = "unnamed_column"

        if cleaned in seen:
            seen[cleaned] += 1
            unique_name = f"{cleaned}_{seen[cleaned]}"
            summary_logs.append(f"Renamed duplicate column '{orig}' to '{unique_name}'")
        else:
            seen[cleaned] = 0
            unique_name = cleaned

        mapping[orig] = unique_name
        normalized_cols.append(unique_name)

    df_cleaned = df.copy()
    df_cleaned.columns = normalized_cols
    return df_cleaned, mapping, summary_logs

def detect_sales_columns(columns: List[str], df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Detects standard sales schema fields from normalized column names and data types.
    """
    detected = {key: None for key in COLUMN_DETECTION_PATTERNS.keys()}

    for role, patterns in COLUMN_DETECTION_PATTERNS.items():
        for col in columns:
            for pattern in patterns:
                if re.search(pattern, col, re.IGNORECASE):
                    detected[role] = col
                    break
            if detected[role] is not None:
                break

    if detected["order_date"] is None:
        for col in columns:
            if "date" in col or "time" in col:
                detected["order_date"] = col
                break

    if detected["sales"] is None:
        for col in columns:
            if ("amount" in col or "price" in col or "val" in col) and pd.api.types.is_numeric_dtype(df[col]):
                detected["sales"] = col
                break

    return detected

def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
    """
    Performs data cleaning without destructive deletion:
    - Strips string cell whitespace
    - Removes duplicate rows
    - Cleans numeric columns containing currency symbols ($ , € £)
    - Converts date strings to ISO format using format="mixed"
    """
    df_clean = df.copy()
    summary_logs = []

    # 1. Remove Duplicate Rows
    orig_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    dups_removed = orig_rows - len(df_clean)
    if dups_removed > 0:
        summary_logs.append(f"Removed {dups_removed} exact duplicate row(s)")
    else:
        summary_logs.append("No duplicate rows found")

    # 2. Trim Whitespace & sanitize NaN strings in text columns
    string_cols = [c for c in df_clean.columns if is_text_column(df_clean[c])]
    for col in string_cols:
        df_clean[col] = df_clean[col].astype(str).str.strip()
        df_clean[col] = df_clean[col].replace(["nan", "None", "null", "NaN", ""], np.nan)
    if len(string_cols) > 0:
        summary_logs.append(f"Sanitized whitespace across {len(string_cols)} text column(s)")

    # 3. Clean numeric columns containing currency formatting
    for col in df_clean.columns:
        if is_text_column(df_clean[col]):
            sample_str = df_clean[col].dropna().astype(str).head(10).str.cat()
            if re.search(r"[\$\,\u20AC\u00A3\u20B9]", sample_str):
                cleaned_numeric = df_clean[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
                numeric_converted = pd.to_numeric(cleaned_numeric, errors="coerce")
                if numeric_converted.notna().sum() > 0:
                    df_clean[col] = numeric_converted
                    summary_logs.append(f"Cleaned currency formatting and cast '{col}' to numeric")

    # 4. Standardize Date columns where possible (using format='mixed' for heterogeneous date strings)
    for col in df_clean.columns:
        if "date" in col or "time" in col:
            try:
                converted_dates = pd.to_datetime(df_clean[col], format="mixed", errors="coerce")
                if converted_dates.notna().sum() > (0.5 * len(df_clean)):
                    df_clean[col] = converted_dates.dt.strftime("%Y-%m-%d")
                    summary_logs.append(f"Standardized date column '{col}' to ISO format (YYYY-MM-DD)")
            except Exception:
                pass

    return df_clean, summary_logs

def calculate_kpis(df: pd.DataFrame, detected_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """Calculates core business KPIs when target columns exist."""
    kpis = {
        "total_revenue": None,
        "total_orders": None,
        "total_customers": None,
        "average_order_value": None,
        "total_quantity": None,
        "total_profit": None
    }

    # Revenue
    sales_col = detected_cols.get("sales")
    if sales_col and sales_col in df.columns:
        numeric_sales = pd.to_numeric(df[sales_col], errors="coerce")
        rev = float(numeric_sales.sum(skipna=True))
        kpis["total_revenue"] = round(rev, 2)
    elif detected_cols.get("quantity") and "unit_price" in df.columns:
        try:
            qty = pd.to_numeric(df[detected_cols["quantity"]], errors="coerce")
            price = pd.to_numeric(df["unit_price"], errors="coerce")
            kpis["total_revenue"] = round(float((qty * price).sum(skipna=True)), 2)
        except Exception:
            pass

    # Orders
    order_col = detected_cols.get("order_id")
    if order_col and order_col in df.columns:
        kpis["total_orders"] = int(df[order_col].nunique(dropna=True))
    else:
        kpis["total_orders"] = int(len(df))

    # Customers
    cust_col = detected_cols.get("customer_id")
    if cust_col and cust_col in df.columns:
        kpis["total_customers"] = int(df[cust_col].nunique(dropna=True))

    # Average Order Value (AOV)
    if kpis["total_revenue"] is not None and kpis["total_orders"] is not None and kpis["total_orders"] > 0:
        kpis["average_order_value"] = round(kpis["total_revenue"] / kpis["total_orders"], 2)

    # Quantity
    qty_col = detected_cols.get("quantity")
    if qty_col and qty_col in df.columns:
        kpis["total_quantity"] = int(pd.to_numeric(df[qty_col], errors="coerce").sum(skipna=True))

    # Profit
    profit_col = detected_cols.get("profit")
    if profit_col and profit_col in df.columns:
        kpis["total_profit"] = round(float(pd.to_numeric(df[profit_col], errors="coerce").sum(skipna=True)), 2)

    return kpis

def process_sales_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Main orchestrator for dataset inspection, cleaning, column detection, and KPI calculation.
    """
    # 1. Read raw dataframe
    df_raw = load_dataframe_from_bytes(file_bytes, filename)
    orig_rows, orig_cols = len(df_raw), len(df_raw.columns)

    if orig_rows == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file '{filename}' contains 0 data rows."
        )

    # 2. Normalize columns
    df_norm, col_mapping, norm_logs = normalize_column_names(df_raw)

    # 3. Inspect raw statistics
    raw_missing_summary = df_raw.isna().sum().to_dict()
    raw_missing_summary = {str(k): int(v) for k, v in raw_missing_summary.items()}
    raw_dup_count = int(df_raw.duplicated().sum())

    # 4. Clean Dataset
    df_clean, clean_logs = clean_data(df_norm)
    all_cleaning_logs = norm_logs + clean_logs
    cleaned_rows = len(df_clean)

    # 5. Detect Sales Columns on cleaned data
    detected_cols = detect_sales_columns(list(df_clean.columns), df_clean)

    col_details = []
    possible_date_cols = []
    possible_numeric_cols = []

    for col in df_clean.columns:
        dtype_str = str(df_clean[col].dtype)
        unique_cnt = int(df_clean[col].nunique(dropna=True))
        missing_cnt = int(df_clean[col].isna().sum())
        
        if "date" in col or "time" in col or "datetime" in dtype_str:
            possible_date_cols.append(col)
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            possible_numeric_cols.append(col)

        col_details.append({
            "column_name": col,
            "data_type": dtype_str,
            "unique_values": unique_cnt,
            "missing_count": missing_cnt
        })

    # 6. Calculate KPIs
    kpis = calculate_kpis(df_clean, detected_cols)

    # 7. Generate Warnings
    warnings = []
    if detected_cols["sales"] is None and kpis["total_revenue"] is None:
        warnings.append("Could not automatically identify a Revenue/Sales column.")
    if detected_cols["order_date"] is None:
        warnings.append("Could not automatically identify an Order Date column.")
    if detected_cols["region"] is None:
        warnings.append("Could not automatically identify a Region/Location column.")
    if detected_cols["customer_id"] is None:
        warnings.append("Could not automatically identify a Customer ID/Name column.")

    file_info = {
        "filename": filename,
        "file_size_bytes": len(file_bytes),
        "file_size_kb": round(len(file_bytes) / 1024, 2)
    }

    # Store active dataset in memory cache for analytics route
    set_active_dataset(df_clean, detected_cols, file_info)

    return {
        "file_info": file_info,
        "original_row_count": orig_rows,
        "original_column_count": orig_cols,
        "cleaned_row_count": cleaned_rows,
        "duplicate_count": raw_dup_count,
        "column_mapping": col_mapping,
        "column_information": col_details,
        "missing_value_summary": raw_missing_summary,
        "possible_date_columns": possible_date_cols,
        "possible_numeric_columns": possible_numeric_cols,
        "detected_columns": detected_cols,
        "cleaning_summary": all_cleaning_logs,
        "calculated_kpis": kpis,
        "warnings": warnings
    }

def inspect_and_clean_data(file_bytes: bytes, filename: str):
    """
    Ingests raw file bytes, normalizes columns, cleans dataset, and detects sales schema roles.
    Returns (cleaned_dataframe, detected_columns_dict, processing_summary_dict).
    """
    res = process_sales_file(file_bytes, filename)
    try:
        from backend.services.dataset_store import get_active_dataset
    except ImportError:
        from services.dataset_store import get_active_dataset

    df_clean, detected_cols, _ = get_active_dataset()
    return df_clean, detected_cols, res

