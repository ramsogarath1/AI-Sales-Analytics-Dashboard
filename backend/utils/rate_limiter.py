"""
In-Process Rate Limiter for Authentication Protection.
Tracks login attempts per client identifier (email / IP) within a sliding time window.
Prevents brute-force authentication attacks.
"""

import time
from typing import Dict, List
from fastapi import HTTPException
from backend.utils.security import make_error_detail

_RATE_LIMIT_STORE: Dict[str, List[float]] = {}

def check_login_rate_limit(identifier: str, max_requests: int = 10, window_seconds: int = 60):
    """
    Enforces sliding-window rate limits on authentication requests.
    Raises HTTPException 429 if request limit exceeded.
    """
    now = time.time()
    key = identifier.lower().strip()

    if key not in _RATE_LIMIT_STORE:
        _RATE_LIMIT_STORE[key] = []

    # Clean timestamps outside window
    _RATE_LIMIT_STORE[key] = [
        ts for ts in _RATE_LIMIT_STORE[key] if now - ts < window_seconds
    ]

    if len(_RATE_LIMIT_STORE[key]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=make_error_detail(
                "Too many authentication attempts. Please wait 1 minute before trying again.",
                "RATE_LIMIT_EXCEEDED"
            )
        )

    _RATE_LIMIT_STORE[key].append(now)

def clear_rate_limit_store():
    """Clears rate limit store (useful for automated testing)."""
    global _RATE_LIMIT_STORE
    _RATE_LIMIT_STORE = {}
