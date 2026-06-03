"""pytest suite for Issue #187 — Self-Healing Workflow Engine.

Covers:
- CircuitBreaker state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- RetryPolicy backoff computation (fixed, exponential, jitter)
- SelfHealingEngine: retry success, retry exhaustion + fallback, non-retryable errors
- DQ confidence multiplier applied correctly on fallback
- Canon C30: user_message always present when degraded
"""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from resilience.retry_policy import RetryPolicy, BackoffStrategy
from resilience.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError
from resilience.degraded_fallbacks import DEGRADED_FALLBACKS, DegradedFallback, FallbackMode
from resilience.self_healing_engine import (
    SelfHealingEngine, HealingResult, WorkflowFailure, NonRetryableError
)


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------

class TestRetryPolicy:
    def test_exponential_backoff_doubles(self):
        p = RetryPolicy(base_delay_ms=500, backoff_strategy=BackoffStrategy.EXPONENTIAL)
        assert p.compute_delay_ms(1) == 500
        assert p.compute_delay_ms(2) == 1000
        assert p.compute_delay_ms(3) == 2000

    def test_fixed_backoff_constant(self):
        p = RetryPolicy(base_delay_ms=300, backoff_strategy=BackoffStrategy.FIXED)
        for attempt in range(1, 5):
            assert p.compute_delay_ms(attempt) == 300

    def test_max_delay_capped(self):
        p = RetryPolicy(base_delay_ms=1000, max_delay_ms=2500, backoff_strategy=BackoffStrategy.EXPONENTIAL)
        assert p.compute_delay_ms(10) == 2500

    def test_retryable_error_recognized(self):
        p = RetryPolicy()
        assert p.is_retryable(TimeoutError())
        assert p.is_retryable(ConnectionError())

    def test_non_retryable_error_rejected(self):
        p = RetryPolicy()

        class AuthError(Exception):
            pass

        assert not p.is_retryable(AuthError())

    def test_jitter_within_bounds(self):
        p = RetryPolicy(base_delay_ms=500, backoff_strategy=BackoffStrategy.JITTER)
        for _ in range(20):
            delay = p.compute_delay_ms(3)
            assert delay >= 500
            assert delay <= p.max_delay_ms


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def _make_cb(self, **kwargs) -> CircuitBreaker:
        return CircuitBreaker(
            skill_id="test_skill",
            failure_rate_threshold=0.5,
            min_calls_in_window=2,
            open_duration_seconds=0,  # immediate probe for tests
            **kwargs,
        )

    @pytest.mark.asyncio
    async def test_starts_closed(self):
        cb = self._make_cb()
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_stays_closed(self):
        cb = self._make_cb()
        async def ok(): return "ok"
        await cb.call(ok)
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self):
        cb = self._make_cb()

        async def fail():
            raise ConnectionError("timeout")

        with pytest.raises(ConnectionError):
            await cb.call(fail)
        with pytest.raises(ConnectionError):
            await cb.call(fail)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_raises_circuit_open_error(self):
        cb = self._make_cb(open_duration_seconds=9999)
        cb.state = CircuitState.OPEN
        import time
        cb._opened_at = time.monotonic()

        async def ok(): return "ok"
        with pytest.raises(CircuitOpenError):
            await cb.call(ok)

    @pytest.mark.asyncio
    async def test_half_open_probe_success_closes(self):
        cb = self._make_cb()
        cb.state = CircuitState.OPEN
        cb._opened_at = 0.0  # immediate recovery

        async def ok(): return "recovered"
        result = await cb.call(ok)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_probe_failure_reopens(self):
        cb = self._make_cb()
        cb.state = CircuitState.OPEN
        cb._opened_at = 0.0

        async def fail():
            raise TimeoutError("still down")

        with pytest.raises(TimeoutError):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

    def test_health_report_keys(self):
        cb = self._make_cb()
        h = cb.health
        for key in ("skill_id", "state", "failure_rate", "total_calls_in_window"):
            assert key in h


# ---------------------------------------------------------------------------
# SelfHealingEngine
# ---------------------------------------------------------------------------

class TestSelfHealingEngine:
    def _make_engine(self) -> SelfHealingEngine:
        return SelfHealingEngine(telemetry=None)

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        engine = self._make_engine()
        async def fn(): return {"data": "ok"}
        result = await engine.execute_with_healing("crystal_graphrag", fn)
        assert not result.degraded
        assert result.attempts == 1
        assert result.result == {"data": "ok"}

    @pytest.mark.asyncio
    async def test_retry_then_success(self):
        engine = self._make_engine()
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("transient")
            return {"data": "recovered"}

        result = await engine.execute_with_healing("article_loader", fn)
        assert not result.degraded
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries_triggers_fallback(self):
        engine = self._make_engine()

        async def fn():
            raise TimeoutError("always fails")

        result = await engine.execute_with_healing("crystal_graphrag", fn)
        assert result.degraded
        assert result.fallback_used == FallbackMode.DOWNGRADE.value
        assert result.dq_confidence_multiplier == 0.70
        assert result.user_message is not None  # Canon C30

    @pytest.mark.asyncio
    async def test_no_fallback_raises_workflow_failure(self):
        engine = self._make_engine()

        async def fn():
            raise TimeoutError("always fails")

        with pytest.raises(WorkflowFailure):
            await engine.execute_with_healing("unknown_skill_xyz", fn, fallback=None)

    @pytest.mark.asyncio
    async def test_non_retryable_error_propagates_immediately(self):
        engine = self._make_engine()

        async def fn():
            class AuthError(Exception):
                pass
            raise AuthError("forbidden")

        with pytest.raises(NonRetryableError):
            await engine.execute_with_healing("crystal_graphrag", fn)

    @pytest.mark.asyncio
    async def test_dq_multiplier_1_when_not_degraded(self):
        engine = self._make_engine()
        async def fn(): return "ok"
        result = await engine.execute_with_healing("soul_mirror", fn)
        assert result.dq_confidence_multiplier == 1.0

    @pytest.mark.asyncio
    async def test_planetary_hub_fallback_cached(self):
        engine = self._make_engine()

        async def fn():
            raise ConnectionError("feed down")

        result = await engine.execute_with_healing("planetary_signal_hub", fn)
        assert result.degraded
        assert result.fallback_used == FallbackMode.CACHED.value
        assert result.dq_confidence_multiplier == 0.85


# ---------------------------------------------------------------------------
# DegradedFallbacks — Canon C30 compliance
# ---------------------------------------------------------------------------

class TestDegradedFallbacks:
    def test_all_fallbacks_have_user_message(self):
        for skill_id, fallback in DEGRADED_FALLBACKS.items():
            assert fallback.user_message, f"'{skill_id}' fallback missing user_message (Canon C30)"

    def test_dq_multiplier_in_valid_range(self):
        for skill_id, fallback in DEGRADED_FALLBACKS.items():
            assert 0.0 <= fallback.dq_confidence_multiplier <= 1.0, (
                f"'{skill_id}' dq_confidence_multiplier out of range"
            )

    def test_required_skills_have_fallbacks(self):
        required = [
            "planetary_signal_hub", "article_loader",
            "crystal_graphrag", "biometric_coherence",
        ]
        for skill_id in required:
            assert skill_id in DEGRADED_FALLBACKS, f"Missing fallback for '{skill_id}'"
