"""
core/infra/error_boundary.py
(formerly core/error_boundary.py — Phase C physical migration)

GAIA Global Error Boundary — Sprint G-6

Installs FastAPI exception handlers that:
  1. Catch every exception before FastAPI's default handler.
  2. Return a structured JSON envelope on every error path.
  3. Emit a canonical GAIAEvent log entry (never leaks tracebacks to clients).
  4. Attach the per-request X-Correlation-ID to every error response so
     clients can correlate errors with server-side log entries.

Error envelope shape:
  {
    "ok":            false,
    "error": {
      "code":           "NOT_FOUND",          # machine-readable
      "message":        "GAIAN 'luna' not found",   # safe for clients
      "correlation_id": "req-abc123def456",   # matches X-Correlation-ID header
      "status":         404
    }
  }

Usage (in server.py, after app = FastAPI(...)):
    from core.error_boundary import install_error_handlers
    install_error_handlers(app)

Canon Ref: C01 (Sovereignty — honest failure disclosure), C30 (No silent failures)
"""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.logger import GAIAEvent, correlation_id_ctx, get_logger

_logger = get_logger("gaia.error_boundary")

# ------------------------------------------------------------------ #
#  HTTP status → machine-readable code map                           #
# ------------------------------------------------------------------ #

_STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def _code(status_code: int) -> str:
    return _STATUS_CODES.get(status_code, f"HTTP_{status_code}")


# ------------------------------------------------------------------ #
#  Envelope builder                                                   #
# ------------------------------------------------------------------ #

def _envelope(status_code: int, message: str, detail: Any = None) -> dict:
    """
    Build the canonical GAIA error envelope.
    `detail` is only included when it adds useful, non-sensitive info
    (e.g. validation field errors).  It is never a traceback.
    """
    inner: dict[str, Any] = {
        "code":           _code(status_code),
        "message":        message,
        "correlation_id": correlation_id_ctx.get("-"),
        "status":         status_code,
    }
    if detail is not None:
        inner["detail"] = detail
    return {"ok": False, "error": inner}


def _json(status_code: int, message: str, detail: Any = None) -> JSONResponse:
    body = _envelope(status_code, message, detail)
    resp = JSONResponse(status_code=status_code, content=body)
    resp.headers["X-Correlation-ID"] = correlation_id_ctx.get("-")
    return resp


# ------------------------------------------------------------------ #
#  Handlers                                                           #
# ------------------------------------------------------------------ #

async def _handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Covers FastAPI HTTPException and Starlette HTTPException."""
    _logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "event":       GAIAEvent.ERROR.value,
            "status_code": exc.status_code,
            "path":        request.url.path,
        },
    )
    message = str(exc.detail) if exc.detail else _code(exc.status_code)
    return _json(exc.status_code, message)


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 Unprocessable Entity — includes field-level errors (safe to expose)."""
    errors = [
        {
            "field":   " -> ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", ""),
            "type":    err.get("type", ""),
        }
        for err in exc.errors()
    ]
    _logger.warning(
        f"Validation error on {request.url.path}: {len(errors)} field(s)",
        extra={
            "event":        GAIAEvent.ERROR.value,
            "path":         request.url.path,
            "error_count":  len(errors),
        },
    )
    return _json(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        f"Request validation failed ({len(errors)} error(s))",
        detail=errors,
    )


async def _handle_unhandled_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all for any exception that escapes FastAPI's normal handling.
    Logs the full traceback server-side; returns a generic 500 to the client
    — never leaks internal details.
    """
    tb = traceback.format_exc()
    _logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {type(exc).__name__}: {exc}",
        extra={
            "event":          GAIAEvent.UNHANDLED_EXCEPTION.value,
            "path":           request.url.path,
            "method":         request.method,
            "exc_type":       type(exc).__name__,
            "traceback":      tb,
        },
    )
    return _json(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "An unexpected error occurred. Check server logs for details.",
    )


# ------------------------------------------------------------------ #
#  Installer                                                          #
# ------------------------------------------------------------------ #

def install_error_handlers(app: FastAPI) -> None:
    """
    Register all GAIA error handlers on the given FastAPI application.
    Call once, immediately after `app = FastAPI(...)`, before any routes.

    Order matters: more-specific exception types must be registered first
    because FastAPI matches the first handler whose type is an isinstance
    match for the raised exception.

    NOTE: In Starlette >= 1.0 / FastAPI >= 0.100, add_exception_handler(Exception)
    is not guaranteed to intercept route-level exceptions because Starlette's
    internal middleware stack re-raises before the handler sees them.  We
    therefore install a middleware catch-all as the primary 500 guard and keep
    the exception handler as a secondary safety net.
    """

    @app.middleware("http")
    async def _catch_all_middleware(request: Request, call_next):
        """Primary catch-all: wraps every request so no unhandled exception escapes."""
        try:
            return await call_next(request)
        except Exception as exc:
            tb = traceback.format_exc()
            _logger.error(
                f"Unhandled exception on {request.method} {request.url.path}: "
                f"{type(exc).__name__}: {exc}",
                extra={
                    "event":     GAIAEvent.UNHANDLED_EXCEPTION.value,
                    "path":      request.url.path,
                    "method":    request.method,
                    "exc_type":  type(exc).__name__,
                    "traceback": tb,
                },
            )
            return _json(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "An unexpected error occurred. Check server logs for details.",
            )

    # 1. RequestValidationError (422) — before generic HTTPException
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]

    # 2. FastAPI HTTPException (inherits from Starlette)
    app.add_exception_handler(HTTPException, _handle_http_exception)  # type: ignore[arg-type]

    # 3. Starlette base HTTPException (routing 404/405 before route handlers run)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]

    # 4. Secondary catch-all — belt-and-suspenders for any handler that bypasses middleware
    app.add_exception_handler(Exception, _handle_unhandled_exception)  # type: ignore[arg-type]

    _logger.info(
        "Error boundary installed (4 handlers: validation, http, starlette, unhandled)",
        extra={"event": GAIAEvent.SERVER_START.value},
    )
