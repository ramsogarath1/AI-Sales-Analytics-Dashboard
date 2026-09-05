"""
User-Scoped In-Memory Dataset Store Manager for AI Sales Analytics Dashboard.
Retains active dataset context per user_id across upload, analytics, insights, and AI endpoints.
Prevents active dataset cross-user leakage.
"""

from typing import Optional, Dict, Any, Tuple
import pandas as pd

# Map of user_id -> (DataFrame, detected_columns_dict, file_info_dict)
_USER_ACTIVE_STORE: Dict[str, Tuple[pd.DataFrame, Dict[str, Optional[str]], Dict[str, Any]]] = {}

def set_active_dataset(
    df: pd.DataFrame,
    detected_cols: Dict[str, Optional[str]],
    file_info: Dict[str, Any],
    user_id: Optional[str] = None
):
    """Stores active DataFrame, detected columns, and file_info for a specific user_id."""
    key = user_id or "default_user"
    _USER_ACTIVE_STORE[key] = (df, detected_cols, file_info)

def get_active_dataset(
    user_id: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Optional[str]]], Optional[Dict[str, Any]]]:
    """Retrieves active dataset tuple (DataFrame, detected_columns, file_info) for a user_id."""
    key = user_id or "default_user"
    return _USER_ACTIVE_STORE.get(key, (None, None, None))

def clear_active_dataset(user_id: Optional[str] = None):
    """Clears stored dataset for specified user_id, or all users if user_id is None."""
    global _USER_ACTIVE_STORE
    if user_id:
        _USER_ACTIVE_STORE.pop(user_id, None)
    else:
        _USER_ACTIVE_STORE = {}
