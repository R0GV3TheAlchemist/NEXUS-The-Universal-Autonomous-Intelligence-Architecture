"""Issue #187 — RetryPolicy: per-skill retry configuration with exponential/jitter backoff.

Canon C30: No silent failures — every retry attempt is logged.
Canon C01: Sovereignty — non-retryable errors (AuthError, PolicyViolation) never retry.
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class BackoffStrategy(str, Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    JITTER = "jitter"


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay_ms: int = 500
    max_delay_ms: int = 10_000
    retryable_errors: list[str] = field(
        default_factory=lambda: ["TimeoutError", "ConnectionError", "ServiceUnavailable"]
    )
    non_retryable_errors: list[str] = field(
        default_factory=lambda: ["AuthError", "PolicyViolation", "SandboxEscape"]
    )

    def is_retryable(self, error: Exception) -> bool:
        error_name = type(error).__name__
        if error_name in self.non_retryable_errors:
            return False
        return error_name in self.retryable_errors

    def compute_delay_ms(self, attempt: int) -> int:
        """Compute delay in milliseconds for a given attempt (1-indexed)."""
        if self.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.base_delay_ms
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.base_delay_ms * (2 ** (attempt - 1))
        else:  # JITTER
            base = self.base_delay_ms * (2 ** (attempt - 1))
            delay = random.randint(self.base_delay_ms, base)
        return min(delay, self.max_delay_ms)

    async def sleep(self, attempt: int) -> None:
        delay_s = self.compute_delay_ms(attempt) / 1000.0
        await asyncio.sleep(delay_s)


# Per-skill policy overrides — engines that need different behaviour
SKILL_RETRY_POLICIES: dict[str, RetryPolicy] = {
    # Planetary hub: slower backoff — upstream feeds are rate-limited
    "planetary_signal_hub": RetryPolicy(
        max_attempts=3,
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        base_delay_ms=1_000,
        max_delay_ms=15_000,
    ),
    # Crystal GraphRAG: fast retry — usually a transient lock
    "crystal_graphrag": RetryPolicy(
        max_attempts=4,
        backoff_strategy=BackoffStrategy.JITTER,
        base_delay_ms=200,
        max_delay_ms=3_000,
    ),
    # Biometric engine: no retry on hardware-level errors
    "biometric_coherence": RetryPolicy(
        max_attempts=2,
        backoff_strategy=BackoffStrategy.FIXED,
        base_delay_ms=300,
        non_retryable_errors=["AuthError", "PolicyViolation", "SandboxEscape", "HardwareError"],
    ),
    # Article loader: retry with jitter — network latency
    "article_loader": RetryPolicy(
        max_attempts=3,
        backoff_strategy=BackoffStrategy.JITTER,
        base_delay_ms=800,
        max_delay_ms=8_000,
    ),
}


def get_retry_policy(skill_id: str) -> RetryPolicy:
    return SKILL_RETRY_POLICIES.get(skill_id, RetryPolicy())
