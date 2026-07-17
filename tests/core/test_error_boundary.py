"""
tests/core/test_error_boundary.py

Test suite for core/error_boundary.py

Covers:
  - BoundarySeverity enum values and C30 SILENT guard
  - GAIABoundaryError dataclass: fields, _summary, to_dict
  - RecoveryResult dataclass
  - ErrorBoundary sync context manager:
      FATAL re-raises as GAIABoundaryError
      DEGRADED swallows when recovery succeeds
      RECOVERABLE re-raises even when recovery succeeds
      recovery callback receives the GAIABoundaryError
      recovery callback failure still re-raises
      catch filter passes non-matching exceptions through unchanged
      no-exception path returns cleanly
  - ErrorBoundary async context manager: mirrors sync + async recovery support
  - ErrorBoundary.wrap() sync decorator
  - ErrorBoundary.wrap_async() async decorator
  - Shorthand factories: boundary(), fatal(), recoverable(), degraded()
  - Constructor guards: SILENT rejected, bad reraise combos rejected

Canon refs: C01, C30
"""
from __future__ import annotations

import asyncio
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _imports():
    from core.error_boundary import (
        ErrorBoundary,
        GAIABoundaryError,
        BoundarySeverity,
        RecoveryResult,
        boundary,
        fatal,
        recoverable,
        degraded,
    )
    return (
        ErrorBoundary, GAIABoundaryError, BoundarySeverity,
        RecoveryResult, boundary, fatal, recoverable, degraded,
    )


# ---------------------------------------------------------------------------
# BoundarySeverity
# ---------------------------------------------------------------------------

class TestBoundarySeverity:
    def test_enum_values(self):
        from core.error_boundary import BoundarySeverity
        assert BoundarySeverity.FATAL.value       == "fatal"
        assert BoundarySeverity.RECOVERABLE.value == "recoverable"
        assert BoundarySeverity.DEGRADED.value    == "degraded"
        assert BoundarySeverity.SILENT.value      == "silent"

    def test_silent_forbidden_in_constructor(self):
        from core.error_boundary import ErrorBoundary, BoundarySeverity
        with pytest.raises(ValueError, match="SILENT"):
            ErrorBoundary("comp", "op", severity=BoundarySeverity.SILENT)

    def test_reraise_false_requires_degraded(self):
        from core.error_boundary import ErrorBoundary, BoundarySeverity
        with pytest.raises(ValueError, match="DEGRADED"):
            ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.FATAL,
                recovery=lambda e: None,
                reraise=False,
            )

    def test_reraise_false_requires_recovery(self):
        from core.error_boundary import ErrorBoundary, BoundarySeverity
        with pytest.raises(ValueError, match="recovery callback"):
            ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.DEGRADED,
                recovery=None,
                reraise=False,
            )


# ---------------------------------------------------------------------------
# GAIABoundaryError
# ---------------------------------------------------------------------------

class TestGAIABoundaryError:
    def _make(self, **kw):
        from core.error_boundary import GAIABoundaryError, BoundarySeverity
        defaults = dict(
            component="gaia.test",
            operation="test_op",
            original=ValueError("boom"),
            severity=BoundarySeverity.FATAL,
        )
        defaults.update(kw)
        return GAIABoundaryError(**defaults)

    def test_is_exception(self):
        err = self._make()
        assert isinstance(err, Exception)

    def test_summary_contains_component_and_operation(self):
        err = self._make()
        s = str(err)
        assert "gaia.test" in s
        assert "test_op" in s

    def test_summary_contains_original_type(self):
        err = self._make()
        assert "ValueError" in str(err)

    def test_summary_contains_severity(self):
        err = self._make()
        assert "fatal" in str(err)

    def test_to_dict_keys(self):
        d = self._make().to_dict()
        expected = {
            "component", "operation", "original_type", "original_message",
            "severity", "recovery_attempted", "recovery_succeeded",
            "correlation_id", "occurred_at", "context",
        }
        assert expected.issubset(d.keys())

    def test_to_dict_original_type(self):
        d = self._make(original=RuntimeError("x")).to_dict()
        assert d["original_type"] == "RuntimeError"

    def test_recovery_flags_default_false(self):
        err = self._make()
        assert err.recovery_attempted is False
        assert err.recovery_succeeded is False


# ---------------------------------------------------------------------------
# RecoveryResult
# ---------------------------------------------------------------------------

class TestRecoveryResult:
    def test_succeeded_true(self):
        from core.error_boundary import RecoveryResult
        r = RecoveryResult(succeeded=True, value=42)
        assert r.succeeded is True
        assert r.value == 42

    def test_succeeded_false(self):
        from core.error_boundary import RecoveryResult
        r = RecoveryResult(succeeded=False)
        assert r.succeeded is False
        assert r.value is None


# ---------------------------------------------------------------------------
# Sync context manager
# ---------------------------------------------------------------------------

class TestSyncContextManager:
    def test_fatal_reraises_as_boundary_error(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        with pytest.raises(GAIABoundaryError) as exc_info:
            with ErrorBoundary("comp", "op", BoundarySeverity.FATAL):
                raise ValueError("original")
        assert isinstance(exc_info.value.original, ValueError)

    def test_fatal_boundary_error_has_correct_component(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        with pytest.raises(GAIABoundaryError) as exc_info:
            with ErrorBoundary("gaia.memory", "persist", BoundarySeverity.FATAL):
                raise RuntimeError("db down")
        assert exc_info.value.component == "gaia.memory"
        assert exc_info.value.operation == "persist"

    def test_no_exception_passes_through(self):
        from core.error_boundary import ErrorBoundary
        result = []
        with ErrorBoundary("comp", "op"):
            result.append(42)
        assert result == [42]

    def test_degraded_swallows_when_recovery_succeeds(self):
        from core.error_boundary import ErrorBoundary, BoundarySeverity
        called = []
        def recover(be):
            called.append(be)
        # Should NOT raise
        with ErrorBoundary(
            "comp", "op",
            severity=BoundarySeverity.DEGRADED,
            recovery=recover,
            reraise=False,
        ):
            raise ValueError("non-critical")
        assert len(called) == 1

    def test_degraded_still_raises_if_recovery_fails(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        def bad_recover(be):
            raise RuntimeError("recovery also broken")
        with pytest.raises(GAIABoundaryError):
            with ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.DEGRADED,
                recovery=bad_recover,
                reraise=False,
            ):
                raise ValueError("original")

    def test_recoverable_reraises_even_when_recovery_succeeds(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        def recover(be): pass
        with pytest.raises(GAIABoundaryError):
            with ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.RECOVERABLE,
                recovery=recover,
                reraise=True,
            ):
                raise ValueError("will propagate")

    def test_recovery_callback_receives_boundary_error(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        received = []
        def recover(be):
            received.append(be)
        try:
            with ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.DEGRADED,
                recovery=recover,
                reraise=False,
            ):
                raise ValueError("check")
        except GAIABoundaryError:
            pass
        assert len(received) == 1
        assert isinstance(received[0], GAIABoundaryError)

    def test_catch_filter_passes_non_matching_exception_through(self):
        from core.error_boundary import ErrorBoundary
        # Only catch TypeError; raise ValueError — should pass through raw
        with pytest.raises(ValueError):
            with ErrorBoundary("comp", "op", catch=(TypeError,)):
                raise ValueError("not caught")

    def test_boundary_error_stored_on_instance(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        eb = ErrorBoundary("comp", "op", BoundarySeverity.FATAL)
        with pytest.raises(GAIABoundaryError):
            with eb:
                raise RuntimeError("stored")
        assert eb.boundary_error is not None
        assert isinstance(eb.boundary_error.original, RuntimeError)

    def test_context_metadata_attached(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        ctx = {"task_id": "abc123"}
        with pytest.raises(GAIABoundaryError) as exc_info:
            with ErrorBoundary("comp", "op", context=ctx):
                raise ValueError("ctx test")
        assert exc_info.value.context["task_id"] == "abc123"


# ---------------------------------------------------------------------------
# Async context manager
# ---------------------------------------------------------------------------

class TestAsyncContextManager:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_async_fatal_reraises(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity
        async def _inner():
            with pytest.raises(GAIABoundaryError):
                async with ErrorBoundary("comp", "op", BoundarySeverity.FATAL):
                    raise ValueError("async boom")
        self._run(_inner())

    def test_async_no_exception_passes_through(self):
        from core.error_boundary import ErrorBoundary
        result = []
        async def _inner():
            async with ErrorBoundary("comp", "op"):
                result.append(99)
        self._run(_inner())
        assert result == [99]

    def test_async_degraded_swallows_when_recovery_succeeds(self):
        from core.error_boundary import ErrorBoundary, BoundarySeverity
        called = []
        def recover(be):
            called.append(True)
        async def _inner():
            async with ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.DEGRADED,
                recovery=recover,
                reraise=False,
            ):
                raise RuntimeError("async non-critical")
        self._run(_inner())
        assert called == [True]

    def test_async_recovery_callback_can_be_async(self):
        from core.error_boundary import ErrorBoundary, BoundarySeverity
        called = []
        async def async_recover(be):
            called.append(True)
        async def _inner():
            async with ErrorBoundary(
                "comp", "op",
                severity=BoundarySeverity.DEGRADED,
                recovery=async_recover,
                reraise=False,
            ):
                raise RuntimeError("async recovery test")
        self._run(_inner())
        assert called == [True]

    def test_async_catch_filter(self):
        from core.error_boundary import ErrorBoundary
        async def _inner():
            with pytest.raises(ValueError):
                async with ErrorBoundary("comp", "op", catch=(TypeError,)):
                    raise ValueError("not caught async")
        self._run(_inner())


# ---------------------------------------------------------------------------
# wrap() sync decorator
# ---------------------------------------------------------------------------

class TestWrapDecorator:
    def test_wrap_reraises_as_boundary_error(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity

        @ErrorBoundary.wrap("comp", "op", BoundarySeverity.FATAL)
        def broken():
            raise ValueError("wrapped")

        with pytest.raises(GAIABoundaryError):
            broken()

    def test_wrap_passes_return_value(self):
        from core.error_boundary import ErrorBoundary

        @ErrorBoundary.wrap("comp", "op")
        def ok():
            return 123

        assert ok() == 123

    def test_wrap_preserves_function_name(self):
        from core.error_boundary import ErrorBoundary

        @ErrorBoundary.wrap("comp", "op")
        def my_func():
            pass

        assert my_func.__name__ == "my_func"


# ---------------------------------------------------------------------------
# wrap_async() decorator
# ---------------------------------------------------------------------------

class TestWrapAsyncDecorator:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_wrap_async_reraises_as_boundary_error(self):
        from core.error_boundary import ErrorBoundary, GAIABoundaryError, BoundarySeverity

        @ErrorBoundary.wrap_async("comp", "op", BoundarySeverity.FATAL)
        async def broken():
            raise ValueError("async wrapped")

        async def _inner():
            with pytest.raises(GAIABoundaryError):
                await broken()

        self._run(_inner())

    def test_wrap_async_passes_return_value(self):
        from core.error_boundary import ErrorBoundary

        @ErrorBoundary.wrap_async("comp", "op")
        async def ok():
            return 456

        assert self._run(ok()) == 456

    def test_wrap_async_preserves_function_name(self):
        from core.error_boundary import ErrorBoundary

        @ErrorBoundary.wrap_async("comp", "op")
        async def my_async_func():
            pass

        assert my_async_func.__name__ == "my_async_func"


# ---------------------------------------------------------------------------
# Shorthand factories
# ---------------------------------------------------------------------------

class TestShorthandFactories:
    def test_boundary_returns_error_boundary(self):
        from core.error_boundary import boundary, ErrorBoundary
        assert isinstance(boundary("comp", "op"), ErrorBoundary)

    def test_fatal_returns_fatal_severity(self):
        from core.error_boundary import fatal, BoundarySeverity
        eb = fatal("comp", "op")
        assert eb.severity == BoundarySeverity.FATAL
        assert eb.reraise is True

    def test_recoverable_sets_recovery(self):
        from core.error_boundary import recoverable, BoundarySeverity
        fn = lambda e: None
        eb = recoverable("comp", "op", recovery=fn)
        assert eb.severity == BoundarySeverity.RECOVERABLE
        assert eb.recovery is fn

    def test_degraded_sets_reraise_false(self):
        from core.error_boundary import degraded, BoundarySeverity
        fn = lambda e: None
        eb = degraded("comp", "op", recovery=fn)
        assert eb.severity == BoundarySeverity.DEGRADED
        assert eb.reraise is False

    def test_degraded_swallows_in_practice(self):
        from core.error_boundary import degraded
        calls = []
        with degraded("comp", "op", recovery=lambda e: calls.append(1)):
            raise ValueError("swallowed")
        assert calls == [1]
