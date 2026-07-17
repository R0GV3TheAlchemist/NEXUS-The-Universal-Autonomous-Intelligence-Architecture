# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/error_boundary.py

GAIA Structured Exception Handling + Recovery (Issue #811, Priority 2)

This module provides two complementary tools:

1.  ErrorBoundary — a context manager and decorator that wraps any
    callable or `with` block, catches exceptions, emits a canonical
    GAIAEvent log entry, optionally executes a recovery callback, and
    re-raises (or swallows) depending on configured policy.  Nothing
    ever fails silently.

2.  install_error_handlers() — re-exported from core.infra.error_boundary
    for FastAPI HTTP exception handling (unchanged; existing callers
    continue to work).

Design goals
------------
- C01 Sovereignty : every failure is disclosed and logged; no silent swallows.
- C30 No Silent Failures : every except block logs or re-raises (both here).
- Uniform envelope : failures surface as GAIABoundaryError with rich metadata
  (component, operation, severity, recovery_attempted, correlation_id).
- Recovery hooks  : callers register async or sync fallback callables that
  run before the error propagates, enabling graceful degradation.
- Zero external deps beyond the GAIA logger.

HTTP boundary (FastAPI handlers)
---------------------------------
The HTTP-specific handlers live in core/infra/error_boundary.py and are
re-exported below so all existing callers keep working.

Canon Ref: C01, C30, Issue #811 Priority 2
"""
from __future__ import annotations

import asyncio
import functools
import traceback
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypeVar

from core.logger import GAIAEvent, correlation_id_ctx, get_logger

_logger = get_logger("gaia.error_boundary")

F = TypeVar("F", bound=Callable[..., Any])


# ------------------------------------------------------------------ #
#  Re-export HTTP boundary (FastAPI) — backward compat               #
# ------------------------------------------------------------------ #

from core.infra.error_boundary import (  # noqa: F401, E402
    install_error_handlers,
    _code,
    _envelope,
    _handle_http_exception,
    _handle_validation_error,
    _handle_unhandled_exception,
)


# ------------------------------------------------------------------ #
#  Severity enum                                                      #
# ------------------------------------------------------------------ #

class BoundarySeverity(str, Enum):
    """
    How the error boundary treats a caught exception.

    FATAL     — log + re-raise; no recovery attempted.
    RECOVERABLE — log + run recovery callback + re-raise if recovery fails.
    DEGRADED  — log + run recovery callback + swallow if recovery succeeds.
    SILENT    — FORBIDDEN by Canon. Kept as a named value so it can be
                detected and rejected explicitly.
    """
    FATAL       = "fatal"
    RECOVERABLE = "recoverable"
    DEGRADED    = "degraded"
    # SILENT is here only to be caught and rejected — never use it.
    SILENT      = "silent"


# ------------------------------------------------------------------ #
#  GAIABoundaryError — the canonical error envelope                  #
# ------------------------------------------------------------------ #

@dataclass
class GAIABoundaryError(Exception):
    """
    Raised (or stored) whenever ErrorBoundary catches an exception.

    Attributes
    ----------
    component         : GAIA module / subsystem where the error occurred
                        (e.g. "gaia.memory_store", "gaia.planner").
    operation         : Name of the specific operation that failed
                        (e.g. "persist_memory", "build_plan").
    original          : The original exception instance.
    severity          : How the boundary classified this failure.
    recovery_attempted: True when a recovery callback was invoked.
    recovery_succeeded: True when the recovery callback completed without
                        raising.
    correlation_id    : Request/trace correlation ID at time of failure.
    occurred_at       : UTC timestamp of the original exception.
    context           : Arbitrary metadata dict from the call site.
    traceback_str     : Full traceback string (server-side only; never
                        forwarded to clients).
    """
    component:          str
    operation:          str
    original:           BaseException
    severity:           BoundarySeverity          = BoundarySeverity.FATAL
    recovery_attempted: bool                      = False
    recovery_succeeded: bool                      = False
    correlation_id:     str                       = field(default_factory=lambda: correlation_id_ctx.get("-"))
    occurred_at:        datetime                  = field(default_factory=lambda: datetime.now(timezone.utc))
    context:            dict[str, Any]            = field(default_factory=dict)
    traceback_str:      str                       = ""

    # Make it behave like a proper Exception
    def __post_init__(self) -> None:
        super().__init__(self._summary())

    def _summary(self) -> str:
        return (
            f"[{self.component}:{self.operation}] "
            f"{type(self.original).__name__}: {self.original} "
            f"(severity={self.severity.value}, "
            f"recovery={'ok' if self.recovery_succeeded else 'no'})"
        )

    def to_dict(self) -> dict:
        """Serialize for logging / artifact storage."""
        return {
            "component":          self.component,
            "operation":          self.operation,
            "original_type":      type(self.original).__name__,
            "original_message":   str(self.original),
            "severity":           self.severity.value,
            "recovery_attempted": self.recovery_attempted,
            "recovery_succeeded": self.recovery_succeeded,
            "correlation_id":     self.correlation_id,
            "occurred_at":        self.occurred_at.isoformat(),
            "context":            self.context,
        }


# ------------------------------------------------------------------ #
#  Recovery result                                                    #
# ------------------------------------------------------------------ #

@dataclass
class RecoveryResult:
    """Returned by ErrorBoundary.run() and __aenter__ when recovery ran."""
    succeeded:   bool
    value:       Any             = None   # return value from recovery callable
    error:       Optional[GAIABoundaryError] = None


# ------------------------------------------------------------------ #
#  ErrorBoundary                                                      #
# ------------------------------------------------------------------ #

class ErrorBoundary:
    """
    Wraps a block of code or a callable with structured exception handling.

    Context manager (sync)
    ----------------------
        with ErrorBoundary("gaia.planner", "build_plan") as boundary:
            result = planner.build(task)

    Context manager (async)
    -----------------------
        async with ErrorBoundary.async_ctx("gaia.memory", "persist") as boundary:
            await memory.persist(record)

    Decorator (sync)
    ----------------
        @ErrorBoundary.wrap("gaia.search", "execute_query")
        def execute_query(self, q: str) -> list:
            ...

    Decorator (async)
    -----------------
        @ErrorBoundary.wrap_async("gaia.search", "execute_query")
        async def execute_query(self, q: str) -> list:
            ...

    Parameters
    ----------
    component   : Dotted module name (used in logs + GAIABoundaryError).
    operation   : Name of the operation being guarded.
    severity    : How to handle failures (default: FATAL = log + re-raise).
    recovery    : Optional sync callable to invoke on failure.
                  Receives (GAIABoundaryError) as sole argument.
                  If it raises, the original boundary error is re-raised.
    reraise     : If True (default), re-raise after logging (and optional
                  recovery).  If False, swallow — only valid when
                  severity=DEGRADED and recovery is provided.
    context     : Extra metadata dict to attach to the GAIABoundaryError.
    catch       : Tuple of exception types to catch (default: Exception).
                  BaseException subtypes like KeyboardInterrupt are
                  intentionally excluded by default.
    """

    def __init__(
        self,
        component: str,
        operation: str,
        severity:  BoundarySeverity = BoundarySeverity.FATAL,
        recovery:  Optional[Callable[["GAIABoundaryError"], Any]] = None,
        reraise:   bool = True,
        context:   Optional[dict[str, Any]] = None,
        catch:     tuple[type[BaseException], ...] = (Exception,),
    ) -> None:
        # Reject SILENT — Canon C30
        if severity is BoundarySeverity.SILENT:
            raise ValueError(
                "BoundarySeverity.SILENT is forbidden by Canon C30. "
                "Use DEGRADED with a recovery callback instead."
            )
        if not reraise and severity is not BoundarySeverity.DEGRADED:
            raise ValueError(
                "reraise=False is only valid with severity=DEGRADED. "
                "Non-degraded failures must propagate. (C30)"
            )
        if not reraise and recovery is None:
            raise ValueError(
                "reraise=False requires a recovery callback. "
                "Swallowing errors without recovery is a silent failure. (C30)"
            )

        self.component = component
        self.operation = operation
        self.severity  = severity
        self.recovery  = recovery
        self.reraise   = reraise
        self.context   = context or {}
        self.catch     = catch

        # Set after __exit__ / __aexit__ to let callers inspect
        self.boundary_error: Optional[GAIABoundaryError] = None
        self.recovery_result: Optional[RecoveryResult]   = None

    # ---------------------------------------------------------------- #
    #  Sync context manager                                            #
    # ---------------------------------------------------------------- #

    def __enter__(self) -> "ErrorBoundary":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None or not issubclass(exc_type, self.catch):
            return False   # nothing to handle

        tb_str = traceback.format_exc()
        boundary_error = GAIABoundaryError(
            component=self.component,
            operation=self.operation,
            original=exc_val,
            severity=self.severity,
            context=self.context,
            traceback_str=tb_str,
        )
        self.boundary_error = boundary_error

        self._log(boundary_error, tb_str)

        # Recovery
        if self.recovery is not None:
            boundary_error.recovery_attempted = True
            try:
                result_value = self.recovery(boundary_error)
                boundary_error.recovery_succeeded = True
                self.recovery_result = RecoveryResult(
                    succeeded=True, value=result_value, error=boundary_error
                )
            except Exception as rec_exc:
                _logger.error(
                    f"[{self.component}:{self.operation}] Recovery callback "
                    f"raised {type(rec_exc).__name__}: {rec_exc}",
                    extra={"event": GAIAEvent.ERROR.value},
                )
                self.recovery_result = RecoveryResult(
                    succeeded=False, error=boundary_error
                )

        if not self.reraise and (
            self.recovery_result and self.recovery_result.succeeded
        ):
            return True   # swallow — recovery succeeded

        raise boundary_error from exc_val

    # ---------------------------------------------------------------- #
    #  Async context manager                                           #
    # ---------------------------------------------------------------- #

    async def __aenter__(self) -> "ErrorBoundary":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None or not issubclass(exc_type, self.catch):
            return False

        tb_str = traceback.format_exc()
        boundary_error = GAIABoundaryError(
            component=self.component,
            operation=self.operation,
            original=exc_val,
            severity=self.severity,
            context=self.context,
            traceback_str=tb_str,
        )
        self.boundary_error = boundary_error

        self._log(boundary_error, tb_str)

        # Recovery (supports both async and sync callbacks)
        if self.recovery is not None:
            boundary_error.recovery_attempted = True
            try:
                result = self.recovery(boundary_error)
                if asyncio.iscoroutine(result):
                    result = await result
                boundary_error.recovery_succeeded = True
                self.recovery_result = RecoveryResult(
                    succeeded=True, value=result, error=boundary_error
                )
            except Exception as rec_exc:
                _logger.error(
                    f"[{self.component}:{self.operation}] Async recovery callback "
                    f"raised {type(rec_exc).__name__}: {rec_exc}",
                    extra={"event": GAIAEvent.ERROR.value},
                )
                self.recovery_result = RecoveryResult(
                    succeeded=False, error=boundary_error
                )

        if not self.reraise and (
            self.recovery_result and self.recovery_result.succeeded
        ):
            return True

        raise boundary_error from exc_val

    # ---------------------------------------------------------------- #
    #  Decorator factories                                             #
    # ---------------------------------------------------------------- #

    @classmethod
    def wrap(
        cls,
        component: str,
        operation: str,
        severity:  BoundarySeverity = BoundarySeverity.FATAL,
        recovery:  Optional[Callable] = None,
        reraise:   bool = True,
        context:   Optional[dict] = None,
        catch:     tuple[type[BaseException], ...] = (Exception,),
    ) -> Callable[[F], F]:
        """Sync function decorator."""
        def decorator(fn: F) -> F:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                with cls(
                    component=component, operation=operation,
                    severity=severity, recovery=recovery,
                    reraise=reraise, context=context or {},
                    catch=catch,
                ):
                    return fn(*args, **kwargs)
            return wrapper  # type: ignore[return-value]
        return decorator

    @classmethod
    def wrap_async(
        cls,
        component: str,
        operation: str,
        severity:  BoundarySeverity = BoundarySeverity.FATAL,
        recovery:  Optional[Callable] = None,
        reraise:   bool = True,
        context:   Optional[dict] = None,
        catch:     tuple[type[BaseException], ...] = (Exception,),
    ) -> Callable[[F], F]:
        """Async function decorator."""
        def decorator(fn: F) -> F:
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                async with cls(
                    component=component, operation=operation,
                    severity=severity, recovery=recovery,
                    reraise=reraise, context=context or {},
                    catch=catch,
                ):
                    return await fn(*args, **kwargs)
            return wrapper  # type: ignore[return-value]
        return decorator

    # ---------------------------------------------------------------- #
    #  Internal logging                                                #
    # ---------------------------------------------------------------- #

    def _log(self, be: GAIABoundaryError, tb_str: str) -> None:
        """Emit the canonical GAIAEvent log entry."""
        log_fn = {
            BoundarySeverity.FATAL:       _logger.error,
            BoundarySeverity.RECOVERABLE: _logger.warning,
            BoundarySeverity.DEGRADED:    _logger.warning,
        }.get(be.severity, _logger.error)

        log_fn(
            f"[{be.component}:{be.operation}] "
            f"{type(be.original).__name__}: {be.original}",
            extra={
                "event":        GAIAEvent.ERROR.value,
                "component":    be.component,
                "operation":    be.operation,
                "severity":     be.severity.value,
                "exc_type":     type(be.original).__name__,
                "correlation_id": be.correlation_id,
                "traceback":    tb_str,
                **be.context,
            },
        )


# ------------------------------------------------------------------ #
#  Module-level convenience helpers                                   #
# ------------------------------------------------------------------ #

def boundary(
    component: str,
    operation: str,
    severity: BoundarySeverity = BoundarySeverity.FATAL,
    recovery: Optional[Callable] = None,
    reraise: bool = True,
    context: Optional[dict] = None,
    catch: tuple[type[BaseException], ...] = (Exception,),
) -> ErrorBoundary:
    """
    Shorthand factory — returns a ready-to-use ErrorBoundary.

    Sync usage:
        with boundary("gaia.planner", "build_plan"):
            planner.build(task)

    Async usage:
        async with boundary("gaia.memory", "persist"):
            await memory.persist(record)
    """
    return ErrorBoundary(
        component=component,
        operation=operation,
        severity=severity,
        recovery=recovery,
        reraise=reraise,
        context=context,
        catch=catch,
    )


def fatal(
    component: str, operation: str, **kwargs
) -> ErrorBoundary:
    """Shorthand: FATAL boundary — log + always re-raise."""
    return boundary(component, operation, BoundarySeverity.FATAL, **kwargs)


def recoverable(
    component: str,
    operation: str,
    recovery: Callable,
    **kwargs,
) -> ErrorBoundary:
    """Shorthand: RECOVERABLE boundary — log + recovery callback + re-raise."""
    return boundary(
        component, operation,
        BoundarySeverity.RECOVERABLE,
        recovery=recovery,
        **kwargs,
    )


def degraded(
    component: str,
    operation: str,
    recovery: Callable,
    **kwargs,
) -> ErrorBoundary:
    """
    Shorthand: DEGRADED boundary — log + recovery + swallow on success.
    Use for non-critical operations where a cached/default result is
    acceptable (e.g. optional metrics flush, non-critical cache warm).
    """
    return boundary(
        component, operation,
        BoundarySeverity.DEGRADED,
        recovery=recovery,
        reraise=False,
        **kwargs,
    )


__all__ = [
    # HTTP boundary (infra re-exports)
    "install_error_handlers",
    # General boundary
    "ErrorBoundary",
    "GAIABoundaryError",
    "BoundarySeverity",
    "RecoveryResult",
    # Shorthand factories
    "boundary",
    "fatal",
    "recoverable",
    "degraded",
]
