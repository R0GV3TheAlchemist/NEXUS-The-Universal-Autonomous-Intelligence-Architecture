"""SelfHealingEngine — wraps every Synergy Orchestrator job with resilience.

This is the central resilience coordinator for GAIA-OS Issue #187.  Every
engine job dispatched by OrchestratorV2 passes through here before hitting
the underlying skill.  The engine:

  1. Checks the CircuitBreaker for the skill.
  2. Retries according to the skill's RetryPolicy.
  3. Activates a DegradedFallback if all retries are exhausted.
  4. Adjusts DecisionQuality confidence when a fallback fires.
  5. Emits a healing event to Agent Telemetry Hub (Issue #188).
  6. Surfaces a user-facing degradation indicator (never silent).

Canon refs:
  C30 — No silent failures.
  C01 — Sovereignty: user always receives a retry option.
  C34 — Presence: GAIA remains present even in degraded state.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from .circuit_breaker import CircuitBreaker, CircuitOpenError
from .degraded_fallbacks import DegradedFallback
from .retry_policy import (
    WorkflowFailure,
    get_policy,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class HealingResult:
    """Return value from SelfHealingEngine.execute_with_healing().

    Attributes:
        result:         The engine output (or fallback result).
        degraded:       True if a fallback was used instead of the real engine.
        fallback_used:  The DegradedFallback.mode string if degraded, else None.
        attempts:       How many invocation attempts were made.
        total_latency_s: Wall-clock seconds from first attempt to resolution.
        dq_confidence_factor: Multiplier to apply to DecisionQuality.confidence.
    """

    result: Any
    degraded: bool = False
    fallback_used: Optional[str] = None
    attempts: int = 1
    total_latency_s: float = 0.0
    dq_confidence_factor: float = 1.0
    user_message: Optional[str] = None  # Surfaced in UI when degraded.


@dataclass
class HealingEvent:
    """Telemetry event emitted to Agent Telemetry Hub (Issue #188)."""

    skill_id: str
    outcome: str           # 'success' | 'fallback' | 'non_retryable' | 'circuit_open'
    attempts: int
    total_latency_s: float
    fallback_mode: Optional[str] = None
    error_type: Optional[str] = None
    dq_confidence_factor: float = 1.0


# ---------------------------------------------------------------------------
# SelfHealingEngine
# ---------------------------------------------------------------------------

class SelfHealingEngine:
    """Resilience wrapper for all Synergy Orchestrator engine jobs.

    Usage inside OrchestratorV2::

        healing = SelfHealingEngine()

        results = await asyncio.gather(*[
            healing.execute_with_healing(
                skill_id=job.engine,
                job_fn=lambda: engine.respond(job),
                fallback=DEGRADED_FALLBACKS.get(job.engine),
            )
            for job in parallel_jobs
        ])

        for r in results:
            if r.degraded:
                dq.confidence *= r.dq_confidence_factor
    """

    def __init__(
        self,
        telemetry_emit: Optional[Callable[[HealingEvent], Awaitable[None]]] = None,
    ) -> None:
        """Args:
            telemetry_emit: Async callback that forwards HealingEvent to the
                            Agent Telemetry Hub (Issue #188).  Optional so the
                            engine can be used before the Hub is wired up.
        """
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._telemetry_emit = telemetry_emit

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def execute_with_healing(
        self,
        skill_id: str,
        job_fn: Callable[[], Awaitable[Any]],
        fallback: Optional[DegradedFallback] = None,
    ) -> HealingResult:
        """Execute *job_fn* for *skill_id* with full resilience wrapping.

        Args:
            skill_id:  Identifier matching a key in SKILL_RETRY_POLICIES /
                       DEGRADED_FALLBACKS (e.g. 'crystal_graphrag').
            job_fn:    Async callable that invokes the engine.  Called up to
                       policy.max_attempts times.
            fallback:  DegradedFallback to activate if all retries fail.  If
                       None and all retries fail, WorkflowFailure is raised.

        Returns:
            HealingResult with the engine output or fallback result.

        Raises:
            NonRetryableError: Immediately on non-retryable errors.
            WorkflowFailure:   All retries exhausted, no fallback available.
        """
        cb = self._get_or_create_circuit_breaker(skill_id)
        policy = get_policy(skill_id)
        start = time.perf_counter()
        last_exc: Optional[Exception] = None

        # ---- Circuit breaker check ----------------------------------------
        try:
            cb.allow_request()
        except CircuitOpenError as exc:
            logger.warning(
                "[SelfHealingEngine] '%s' circuit is OPEN — fast-fail.", skill_id
            )
            elapsed = time.perf_counter() - start
            await self._emit(HealingEvent(
                skill_id=skill_id,
                outcome="circuit_open",
                attempts=0,
                total_latency_s=elapsed,
                error_type="CircuitOpenError",
            ))
            if fallback:
                return await self._apply_fallback(skill_id, fallback, attempts=0, elapsed=elapsed)
            raise

        # ---- Retry loop ------------------------------------------------------
        for attempt in range(1, policy.max_attempts + 1):
            try:
                result = await job_fn()
                cb.record_success()
                elapsed = time.perf_counter() - start
                await self._emit(HealingEvent(
                    skill_id=skill_id,
                    outcome="success",
                    attempts=attempt,
                    total_latency_s=elapsed,
                ))
                logger.debug(
                    "[SelfHealingEngine] '%s' succeeded on attempt %d (%.2fs).",
                    skill_id, attempt, elapsed,
                )
                return HealingResult(
                    result=result,
                    degraded=False,
                    attempts=attempt,
                    total_latency_s=elapsed,
                )

            except Exception as exc:
                last_exc = exc
                cb.record_failure(exc)

                if policy.is_non_retryable(exc):
                    elapsed = time.perf_counter() - start
                    logger.error(
                        "[SelfHealingEngine] '%s' non-retryable error '%s' — aborting.",
                        skill_id, type(exc).__name__,
                    )
                    await self._emit(HealingEvent(
                        skill_id=skill_id,
                        outcome="non_retryable",
                        attempts=attempt,
                        total_latency_s=elapsed,
                        error_type=type(exc).__name__,
                    ))
                    raise

                if attempt < policy.max_attempts:
                    delay = policy.delay_seconds(attempt)
                    logger.warning(
                        "[SelfHealingEngine] '%s' attempt %d failed ('%s') — "
                        "retrying in %.2fs.",
                        skill_id, attempt, type(exc).__name__, delay,
                    )
                    await asyncio.sleep(delay)

        # ---- All retries exhausted -------------------------------------------
        elapsed = time.perf_counter() - start
        logger.error(
            "[SelfHealingEngine] '%s' exhausted %d attempts — activating fallback.",
            skill_id, policy.max_attempts,
        )

        if fallback:
            return await self._apply_fallback(
                skill_id, fallback, attempts=policy.max_attempts, elapsed=elapsed
            )

        await self._emit(HealingEvent(
            skill_id=skill_id,
            outcome="fallback",
            attempts=policy.max_attempts,
            total_latency_s=elapsed,
            error_type=type(last_exc).__name__ if last_exc else None,
        ))
        raise WorkflowFailure(
            f"'{skill_id}' failed after {policy.max_attempts} attempts "
            f"and no fallback is configured."
        ) from last_exc

    def circuit_health(self, skill_id: str) -> dict[str, Any]:
        """Return the CircuitBreaker health snapshot for *skill_id*."""
        cb = self._get_or_create_circuit_breaker(skill_id)
        return cb.health_summary()

    def all_circuit_health(self) -> dict[str, dict[str, Any]]:
        """Return health snapshots for all registered circuit breakers."""
        return {sid: cb.health_summary() for sid, cb in self._circuit_breakers.items()}

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _get_or_create_circuit_breaker(self, skill_id: str) -> CircuitBreaker:
        if skill_id not in self._circuit_breakers:
            self._circuit_breakers[skill_id] = CircuitBreaker(skill_id=skill_id)
        return self._circuit_breakers[skill_id]

    async def _apply_fallback(
        self,
        skill_id: str,
        fallback: DegradedFallback,
        attempts: int,
        elapsed: float,
    ) -> HealingResult:
        """Activate *fallback* and return a degraded HealingResult."""
        logger.warning(
            "[SelfHealingEngine] '%s' using degraded fallback mode '%s': %s",
            skill_id, fallback.mode, fallback.user_message,
        )
        await self._emit(HealingEvent(
            skill_id=skill_id,
            outcome="fallback",
            attempts=attempts,
            total_latency_s=elapsed,
            fallback_mode=fallback.mode,
            dq_confidence_factor=fallback.dq_confidence_factor,
        ))
        return HealingResult(
            result=None,            # Caller must handle None + degraded=True.
            degraded=True,
            fallback_used=fallback.mode,
            attempts=attempts,
            total_latency_s=elapsed,
            dq_confidence_factor=fallback.dq_confidence_factor,
            user_message=fallback.user_message,
        )

    async def _emit(self, event: HealingEvent) -> None:
        """Forward *event* to Agent Telemetry Hub if a callback is registered."""
        if self._telemetry_emit is not None:
            try:
                await self._telemetry_emit(event)
            except Exception:
                # Telemetry must never crash the engine.  C30 — no silent failures
                # means we log, not suppress.
                logger.exception(
                    "[SelfHealingEngine] Telemetry emit failed for skill '%s'.",
                    event.skill_id,
                )
