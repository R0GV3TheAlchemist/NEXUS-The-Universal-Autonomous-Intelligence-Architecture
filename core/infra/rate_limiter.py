"""
core/infra/rate_limiter.py
(formerly core/rate_limiter.py — Phase C physical migration)

GAIA Rate Limiting + Abuse Protection — Sprint G-7

Two-layer defence:

  Layer 1 — RateLimitMiddleware (global, per-IP)
    Applied to every request before route handlers run.
    Protects against unauthenticated flood attacks.
    Default: 120 requests / 60 seconds per IP.

  Layer 2 — rate_limit() FastAPI dependency (per-user, per-endpoint)
    Applied per-route via Depends(rate_limit(...)).
    Finer-grained throttle on expensive endpoints (chat, query/stream).
    Default: 30 requests / 60 seconds per authenticated user.

Algorithm: sliding window (deque of timestamps per key).
  - No external dependencies (no Redis, no slowapi).
  - In-process only — resets on restart. Acceptable for single-process
    deployment; swap _store for Redis in a multi-replica setup.

On breach: returns/raises HTTP 429 with the canonical GAIA error envelope
(from G-6 error_boundary) and sets Retry-After + X-RateLimit-* headers.

Canon Ref: C01 (Sovereignty — protect the system from abuse),
           C30 (No silent failures — 429 must be explicit and informative)
"""

from __future__ import annotations

import time
from collections import deque
from typing import Callable, Deque, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.logger import GAIAEvent, correlation_id_ctx, get_logger

_logger = get_logger("gaia.rate_limiter")


# ------------------------------------------------------------------ #
#  In-Process Sliding Window Store                                    #
# ------------------------------------------------------------------ #

_store: Dict[str, Deque[float]] = {}


def _sliding_window_check(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> Tuple[bool, int, int]:
    """
    Check whether `key` is within its rate limit.

    Returns:
        (allowed, remaining, retry_after_seconds)
        - allowed:      True if the request should proceed.
        - remaining:    Requests remaining in current window.
        - retry_after:  Seconds until the oldest request ages out.
                        0 when allowed.
    """
    now = time.monotonic()
    cutoff = now - window_seconds

    if key not in _store:
        _store[key] = deque()

    window: Deque[float] = _store[key]

    while window and window[0] < cutoff:
        window.popleft()

    count = len(window)

    if count >= max_requests:
        retry_after = int(window[0] - cutoff) + 1
        return False, 0, retry_after

    window.append(now)
    remaining = max_requests - len(window)
    return True, remaining, 0


def clear_store() -> None:
    """Reset the in-process store. Used in tests."""
    _store.clear()


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

_BYPASS_PATHS = frozenset({"/status", "/docs", "/openapi.json", "/redoc"})


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return getattr(request.client, "host", "unknown")


def _rate_limit_headers(
    remaining: int,
    limit: int,
    window: int,
    retry_after: int = 0,
) -> dict:
    headers = {
        "X-RateLimit-Limit":     str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window":    str(window),
    }
    if retry_after:
        headers["Retry-After"] = str(retry_after)
    return headers


def _build_429(retry_after: int, cid: str, limit: int, window: int) -> JSONResponse:
    body = {
        "ok": False,
        "error": {
            "code":           "RATE_LIMITED",
            "message":        f"Too many requests. Retry after {retry_after} second(s).",
            "correlation_id": cid,
            "status":         429,
        },
    }
    headers = _rate_limit_headers(0, limit, window, retry_after)
    headers["X-Correlation-ID"] = cid
    return JSONResponse(status_code=429, content=body, headers=headers)


# ------------------------------------------------------------------ #
#  Layer 1: Global IP Middleware                                      #
# ------------------------------------------------------------------ #

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global per-IP rate limiter. Applied to all routes except _BYPASS_PATHS.

    Defaults:
        max_requests=120, window_seconds=60
    Override via environment:
        GAIA_RATE_IP_MAX      (default 120)
        GAIA_RATE_IP_WINDOW   (default 60 seconds)
    """
    import os as _os
    _MAX     = int(_os.environ.get("GAIA_RATE_IP_MAX",    "120"))
    _WINDOW  = int(_os.environ.get("GAIA_RATE_IP_WINDOW", "60"))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in _BYPASS_PATHS:
            return await call_next(request)

        ip  = _client_ip(request)
        key = f"ip:{ip}"
        cid = correlation_id_ctx.get("-")

        allowed, remaining, retry_after = _sliding_window_check(
            key, self._MAX, self._WINDOW
        )

        if not allowed:
            _logger.warning(
                f"IP rate limit exceeded: {ip}",
                extra={
                    "event":       GAIAEvent.ERROR.value,
                    "ip":          ip,
                    "limit":       self._MAX,
                    "window":      self._WINDOW,
                    "retry_after": retry_after,
                },
            )
            return _build_429(retry_after, cid, self._MAX, self._WINDOW)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"]     = str(self._MAX)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"]    = str(self._WINDOW)
        return response


# ------------------------------------------------------------------ #
#  Layer 2: Per-User / Per-Endpoint Dependency                        #
# ------------------------------------------------------------------ #

def rate_limit(
    max_requests:   int = 30,
    window_seconds: int = 60,
    scope:          str = "user",
) -> Callable:
    """
    FastAPI dependency factory for per-authenticated-user sliding window
    rate limiting on individual endpoints.

    Args:
        max_requests:   Maximum requests in the window. Default: 30.
        window_seconds: Window length in seconds. Default: 60.
        scope:          Key prefix for namespace isolation.
    """
    async def _dependency(request: Request) -> None:
        from core.auth import verify_token

        auth_header = request.headers.get("Authorization", "")
        user_id: Optional[str] = None
        if auth_header.startswith("Bearer "):
            try:
                payload = verify_token(auth_header[7:])
                user_id = payload.user_id
            except Exception:
                pass

        key = f"{scope}:user:{user_id}" if user_id else f"{scope}:ip:{_client_ip(request)}"
        cid = correlation_id_ctx.get("-")

        allowed, remaining, retry_after = _sliding_window_check(
            key, max_requests, window_seconds
        )

        if not allowed:
            _logger.warning(
                f"Endpoint rate limit exceeded: scope={scope} key={key}",
                extra={
                    "event":       GAIAEvent.ERROR.value,
                    "scope":       scope,
                    "user_id":     user_id,
                    "limit":       max_requests,
                    "window":      window_seconds,
                    "retry_after": retry_after,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Retry after {retry_after} second(s).",
                headers={
                    **_rate_limit_headers(0, max_requests, window_seconds, retry_after),
                    "X-Correlation-ID": cid,
                },
            )

    return _dependency
