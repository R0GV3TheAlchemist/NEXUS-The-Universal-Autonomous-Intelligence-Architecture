# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
tests/core/test_error_boundary.py

Unit tests for core/error_boundary.py — ErrorBoundary, GAIABoundaryError,
BoundarySeverity, and shorthand helpers.

Canon Ref: C01, C30, Issue #811
"""
from __future__ import annotations

import asyncio
import pytest

from core.error_boundary import (
    BoundarySeverity,
    ErrorBoundary,
    GAIABoundaryError,
    RecoveryResult,
    boundary,
    degraded,
    fatal,
    recoverable,
)


# ------------------------------------------------------------------ #
#  GAIABoundaryError                                                  #
# ------------------------------------------------------------------ #

class TestGAIABoundaryError:
    def test_to_dict_shape(self):
        err = GAIABoundaryError(
            component="gaia.test",
            operation="test_op",
            original=ValueError("boom"),
        )
        d = err.to_dict()
        assert d["component"] == "gaia.test"
        assert d["operation"] == "test_op"
        assert d["original_type"] == "ValueError"
        assert d["original_message"] == "boom"
        assert d["severity"] == "fatal"
        assert "occurred_at" in d

    def test_summary_in_args(self):
        err = GAIABoundaryError(
            component="c", operation="op", original=RuntimeError("x")
        )
        assert "c:op" in str(err)
        assert "RuntimeError" in str(err)


# ------------------------------------------------------------------ #
#  BoundarySeverity guards                                            #
# ------------------------------------------------------------------ #

class TestBoundarySeverityGuards:
    def test_silent_forbidden(self):
        with pytest.raises(ValueError, match="SILENT is forbidden"):
            ErrorBoundary("c", "op", severity=BoundarySeverity.SILENT)

    def test_no_reraise_without_degraded_raises(self):
        with pytest.raises(ValueError, match="reraise=False"):
            ErrorBoundary(
                "c", "op",
                severity=BoundarySeverity.FATAL,
                reraise=False,
                recovery=lambda e: None,
            )

    def test_no_reraise_without_recovery_raises(self):
        with pytest.raises(ValueError, match="requires a recovery callback"):
            ErrorBoundary(
                "c", "op",
                severity=BoundarySeverity.DEGRADED,
                reraise=False,
                recovery=None,
            )


# ------------------------------------------------------------------ #
#  Sync context manager                                               #
# ------------------------------------------------------------------ #

class TestSyncContextManager:
    def test_no_exception_passes_through(self):
        with ErrorBoundary("c", "op"):
            result = 1 + 1
        assert result == 2

    def test_exception_raises_boundary_error(self):
        with pytest.raises(GAIABoundaryError) as exc_info:
            with ErrorBoundary("gaia.test", "sync_op"):
                raise ValueError("test error")
        be = exc_info.value
        assert be.component == "gaia.test"
        assert be.operation == "sync_op"
        assert isinstance(be.original, ValueError)
        assert be.severity is BoundarySeverity.FATAL

    def test_recovery_callback_called(self):
        recovered = []

        def recovery(be: GAIABoundaryError):
            recovered.append(be.original)

        with pytest.raises(GAIABoundaryError):
            with ErrorBoundary(
                "gaia.test", "sync_op",
                severity=BoundarySeverity.RECOVERABLE,
                recovery=recovery,
            ):
                raise RuntimeError("failure")

        assert len(recovered) == 1
        assert isinstance(recovered[0], RuntimeError)

    def test_degraded_swallows_on_recovery_success(self):
        def recovery(be):
            return "fallback"

        with ErrorBoundary(
            "gaia.test", "degraded_op",
            severity=BoundarySeverity.DEGRADED,
            recovery=recovery,
            reraise=False,
        ) as eb:
            raise ConnectionError("cache miss")

        assert eb.recovery_result is not None
        assert eb.recovery_result.succeeded is True
        assert eb.recovery_result.value == "fallback"

    def test_boundary_error_set_on_self(self):
        eb = ErrorBoundary("c", "op")
        with pytest.raises(GAIABoundaryError):
            with eb:
                raise KeyError("missing")
        assert eb.boundary_error is not None
        assert isinstance(eb.boundary_error.original, KeyError)

    def test_only_catches_specified_types(self):
        """An exception not in catch tuple propagates unchanged."""
        with pytest.raises(TypeError):
            with ErrorBoundary("c", "op", catch=(ValueError,)):
                raise TypeError("wrong type")


# ------------------------------------------------------------------ #
#  Async context manager                                              #
# ------------------------------------------------------------------ #

class TestAsyncContextManager:
    def test_async_no_exception(self):
        async def run():
            async with ErrorBoundary("c", "op"):
                return 42
        assert asyncio.run(run()) == 42

    def test_async_exception_raises_boundary_error(self):
        async def run():
            async with ErrorBoundary("gaia.test", "async_op"):
                raise ValueError("async boom")

        with pytest.raises(GAIABoundaryError) as exc_info:
            asyncio.run(run())
        assert isinstance(exc_info.value.original, ValueError)

    def test_async_recovery_async_callable(self):
        recovered = []

        async def async_recovery(be: GAIABoundaryError):
            recovered.append(be.component)

        async def run():
            with pytest.raises(GAIABoundaryError):
                async with ErrorBoundary(
                    "gaia.test", "async_rec",
                    severity=BoundarySeverity.RECOVERABLE,
                    recovery=async_recovery,
                ):
                    raise IOError("io fail")

        asyncio.run(run())
        assert recovered == ["gaia.test"]

    def test_async_degraded_swallows(self):
        async def recovery(be):
            return "async_fallback"

        async def run():
            async with ErrorBoundary(
                "c", "op",
                severity=BoundarySeverity.DEGRADED,
                recovery=recovery,
                reraise=False,
            ) as eb:
                raise TimeoutError("slow")
            return eb.recovery_result

        result = asyncio.run(run())
        assert result.succeeded is True
        assert result.value == "async_fallback"


# ------------------------------------------------------------------ #
#  Decorators                                                         #
# ------------------------------------------------------------------ #

class TestDecorators:
    def test_wrap_sync(self):
        @ErrorBoundary.wrap("gaia.test", "wrapped_fn")
        def flaky():
            raise ValueError("wrapped fail")

        with pytest.raises(GAIABoundaryError):
            flaky()

    def test_wrap_async(self):
        @ErrorBoundary.wrap_async("gaia.test", "wrapped_async")
        async def flaky_async():
            raise RuntimeError("async fail")

        with pytest.raises(GAIABoundaryError):
            asyncio.run(flaky_async())

    def test_wrap_preserves_return_value(self):
        @ErrorBoundary.wrap("c", "op")
        def add(a, b):
            return a + b

        assert add(2, 3) == 5


# ------------------------------------------------------------------ #
#  Shorthand helpers                                                  #
# ------------------------------------------------------------------ #

class TestShorthands:
    def test_fatal_reraises(self):
        with pytest.raises(GAIABoundaryError):
            with fatal("c", "op"):
                raise ValueError()

    def test_recoverable_calls_recovery(self):
        log = []
        with pytest.raises(GAIABoundaryError):
            with recoverable("c", "op", recovery=lambda be: log.append(1)):
                raise ValueError()
        assert log == [1]

    def test_degraded_swallows(self):
        with degraded("c", "op", recovery=lambda be: "ok") as eb:
            raise ValueError("not critical")
        assert eb.recovery_result.succeeded
