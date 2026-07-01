"""
GAIA OS HTTP Middleware.

Two middleware components:
  1. BearerAuthMiddleware   — extracts caller_id from Bearer token
  2. RequestLogMiddleware   — logs method, path, status, duration

The caller_id extracted here is stored in request.state.caller_id
and used by every route handler to build the APIRequest.

Auth design:
  - Token format: any opaque string. The token value IS the caller_id.
    This keeps the auth model simple and transparent:
    a token of 'gaian-abc123' gives the bearer caller_id='gaian-abc123',
    which means they can act on behalf of that GAIAN.
  - If require_auth=False (no tokens configured), all requests
    get caller_id='http-anonymous' and proceed freely.
  - 401 is returned only when require_auth=True and no valid token
    is present. The response body matches GAIAResponse format.
"""
from __future__ import annotations

import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from server.config import ServerConfig

logger = logging.getLogger("gaia.server")


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """
    Extract caller_id from Authorization: Bearer <token>.

    If require_auth is False, all requests get caller_id='http-anonymous'.
    If require_auth is True and no valid token is presented, 401 is returned.
    The /docs, /redoc, /openapi.json, and /health endpoints are always allowed.
    """
    ALWAYS_ALLOW = {"/docs", "/redoc", "/openapi.json",
                    "/health", "/v1/os/version", "/v1/os/health"}

    def __init__(self, app, config: ServerConfig) -> None:
        super().__init__(app)
        self._config = config
        self._token_map = {t: t for t in config.bearer_tokens}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.ALWAYS_ALLOW:
            request.state.caller_id = "http-public"
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

        if self._config.require_auth:
            if token not in self._token_map:
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "code": "permission_denied",
                        "message": "Valid Bearer token required.",
                        "payload": {},
                        "request_id": "",
                    },
                )

        request.state.caller_id = self._token_map.get(token, "http-anonymous")
        return await call_next(request)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log every request: method, path, status code, duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
