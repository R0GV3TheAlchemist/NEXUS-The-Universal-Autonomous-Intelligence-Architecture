"""Issue #187 — SelfHealingEngine: wraps every Synergy Orchestrator job with
retry, circuit-breaker, and graceful degradation.

Canon C30: No silent failures — every degradation surfaces to the user.
Canon C01: Sovereignty — user can always retry or override fallback.
Canon C34: Presence — GAIA stays present and functional in degraded conditions.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from .circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from .degraded_fallbacks import DEGRADED_FALLBACKS, DegradedFallback
from .retry_policy import RetryPolicy, get_retry_policy

logger = logging.getLogger(__name__)


class WorkflowFailure(Exception):
    """Raised when a skill exhausts all retries with no available fallback."""
    def __init__(self, skill_id: str, attempts: int):
        super().__init__(
            f"Workflow failure: '{skill_id}' failed after {attempts} attempts "
            f"with no fallback available."
        )
        self.skill_id = skill_id
        self.attempts = attempts


class NonRetryableError(Exception):
    """Wraps errors that should never be retried (auth failures, policy violations)."""
    pass


@dataclass
class HealingResult:
    result: Any                               # The actual payload from the skill
    degraded: bool = False                    # Was a fallback used?
    fallback_used: str | None = None          # Which fallback mode fired
    attempts: int = 1                         # How many attempts were needed
    total_duration_ms: float = 0.0            # Wall-clock time including retries
    dq_confidence_multiplier: float = 1.0    # Applied to DecisionQuality downstream
    user_message: str | None = None           # Surfaced in degradation UI if degraded
    skill_id: str = ""


class SelfHealingEngine:
    """Wraps all Synergy Orchestrator job execution with resilience logic.

    Usage:
        engine = SelfHealingEngine(telemetry=telemetry_collector)
        result = await engine.execute_with_healing(
            skill_id="crystal_graphrag",
            job=job,
            fn=crystal.query,
        )
    """

    def __init__(self, telemetry: Any | None = None):
        self._telemetry = telemetry
        self._breakers: dict[str, CircuitBreaker] = {}

    def _get_breaker(self, skill_id: str) -> CircuitBreaker:
        if skill_id not in self._breakers:
            self._breakers[skill_id] = CircuitBreaker(skill_id=skill_id)
        return self._breakers[skill_id]

    async def execute_with_healing(
        self,
        skill_id: str,
        fn: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        fallback: DegradedFallback | None = None,
        **kwargs: Any,
    ) -> HealingResult:
        """Execute fn through retry + circuit-breaker + fallback chain.

        Steps:
        1. Check circuit breaker state
        2. Attempt fn up to RetryPolicy.max_attempts
        3. If all retries exhausted → apply DegradedFallback if available
        4. Emit telemetry event at each stage
        5. Return HealingResult with degraded flag and DQ multiplier
        """
        policy = get_retry_policy(skill_id)
        breaker = self._get_breaker(skill_id)
        fallback = fallback or DEGRADED_FALLBACKS.get(skill_id)
        start = time.perf_counter()
        last_error: Exception | None = None

        for attempt in range(1, policy.max_attempts + 1):
            try:
                result = await breaker.call(fn, *args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                await self._emit(skill_id, "success", attempt, duration_ms=duration_ms)
                return HealingResult(
                    result=result,
                    degraded=False,
                    attempts=attempt,
                    total_duration_ms=duration_ms,
                    skill_id=skill_id,
                )

            except CircuitOpenError as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.warning("[SelfHealingEngine] %s", e)
                await self._emit(skill_id, "circuit_open", attempt, duration_ms=duration_ms)
                last_error = e
                break  # Circuit is open — skip retries, go straight to fallback

            except Exception as e:
                last_error = e
                if not policy.is_retryable(e):
                    duration_ms = (time.perf_counter() - start) * 1000
                    await self._emit(skill_id, "non_retryable_error", attempt,
                                     error=str(e), duration_ms=duration_ms)
                    raise NonRetryableError(
                        f"Non-retryable error in '{skill_id}': {type(e).__name__}: {e}"
                    ) from e

                if attempt < policy.max_attempts:
                    logger.warning(
                        "[SelfHealingEngine] '%s' attempt %d/%d failed (%s) — retrying",
                        skill_id, attempt, policy.max_attempts, type(e).__name__,
                    )
                    await self._emit(skill_id, "retry", attempt, error=str(e))
                    await policy.sleep(attempt)
                else:
                    await self._emit(skill_id, "exhausted", attempt, error=str(e))

        # All retries exhausted — attempt fallback
        if fallback is not None:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.warning(
                "[SelfHealingEngine] '%s' exhausted retries — applying fallback '%s'",
                skill_id, fallback.mode.value,
            )
            fallback_result = await self._apply_fallback(skill_id, fallback)
            await self._emit(skill_id, "fallback_used", policy.max_attempts,
                             fallback_mode=fallback.mode.value, duration_ms=duration_ms)
            return HealingResult(
                result=fallback_result,
                degraded=True,
                fallback_used=fallback.mode.value,
                attempts=policy.max_attempts,
                total_duration_ms=duration_ms,
                dq_confidence_multiplier=fallback.dq_confidence_multiplier,
                user_message=fallback.user_message,
                skill_id=skill_id,
            )

        raise WorkflowFailure(skill_id=skill_id, attempts=policy.max_attempts)

    async def _apply_fallback(
        self, skill_id: str, fallback: DegradedFallback
    ) -> Any:
        """Execute the fallback strategy and return its payload."""
        from .degraded_fallbacks import FallbackMode

        if fallback.mode == FallbackMode.CACHED:
            return await self._load_cache(skill_id, fallback.max_cache_age_min)
        if fallback.mode == FallbackMode.STATIC_RESPONSE:
            return fallback.static_payload
        if fallback.mode in (
            FallbackMode.SKIP,
            FallbackMode.AFFECTIVE_ONLY,
            FallbackMode.DOWNGRADE,
            FallbackMode.MANUAL_INPUT,
        ):
            return {"fallback": fallback.mode.value, "user_message": fallback.user_message}
        return None

    async def _load_cache(self, skill_id: str, max_age_min: int | None) -> Any:
        """Load cached payload for skill. Override in production with real cache layer."""
        logger.info("[SelfHealingEngine] Loading cache for '%s' (max_age=%s min)",
                    skill_id, max_age_min)
        return {"source": "cache", "skill_id": skill_id, "max_age_min": max_age_min}

    async def _emit(self, skill_id: str, event_type: str, attempt: int,
                    error: str | None = None, fallback_mode: str | None = None,
                    duration_ms: float = 0.0) -> None:
        """Emit telemetry event to Agent Telemetry Hub (Issue #188)."""
        if self._telemetry is None:
            return
        try:
            await self._telemetry.emit({
                "source": "self_healing_engine",
                "skill_id": skill_id,
                "event_type": event_type,
                "attempt": attempt,
                "error": error,
                "fallback_mode": fallback_mode,
                "duration_ms": round(duration_ms, 2),
                "degraded": fallback_mode is not None,
            })
        except Exception:
            pass  # Telemetry must never crash the healing engine

    def get_all_health(self) -> list[dict]:
        """Return health snapshot for every registered circuit breaker."""
        return [cb.health for cb in self._breakers.values()]

    def get_skill_health(self, skill_id: str) -> dict:
        return self._get_breaker(skill_id).health
