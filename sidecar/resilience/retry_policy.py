"""RetryPolicy model and per-skill registry — GAIA-OS Issue #187.

Canon refs:
  C30 — No silent failures: every retry attempt is logged; exhausted retries surface to user.
  C01 — Sovereignty: retry behaviour is transparent and user-inspectable via Telemetry Hub.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------

class RetryableError(Exception):
    """Transient errors that warrant automatic retry (network, timeout, service unavailable)."""


class NonRetryableError(Exception):
    """Permanent errors that must NOT be retried (auth failure, policy violation, sandbox escape)."""


class WorkflowFailure(Exception):
    """Raised when all retry attempts are exhausted and no fallback is available."""


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------

@dataclass
class RetryPolicy:
    """Configurable retry policy for a GAIA engine or skill.

    Attributes:
        max_attempts:       Total invocation attempts (1 = no retries).
        backoff_strategy:   'fixed' | 'exponential' | 'jitter'
        base_delay_ms:      Initial delay between retries in milliseconds.
        max_delay_ms:       Cap on delay growth for exponential/jitter strategies.
        retryable_errors:   Error class names that trigger a retry.
        non_retryable_errors: Error class names that abort immediately.
    """

    max_attempts: int = 3
    backoff_strategy: str = "exponential"  # 'fixed' | 'exponential' | 'jitter'
    base_delay_ms: int = 500
    max_delay_ms: int = 10_000
    retryable_errors: list[str] = field(default_factory=lambda: [
        "RetryableError",
        "TimeoutError",
        "ConnectionError",
        "ServiceUnavailable",
        "aiohttp.ClientError",
        "asyncio.TimeoutError",
    ])
    non_retryable_errors: list[str] = field(default_factory=lambda: [
        "NonRetryableError",
        "AuthError",
        "PolicyViolation",
        "SandboxEscape",
        "PermissionError",
    ])

    def is_retryable(self, exc: Exception) -> bool:
        """Return True if the exception class name appears in retryable_errors."""
        name = type(exc).__name__
        return name in self.retryable_errors

    def is_non_retryable(self, exc: Exception) -> bool:
        """Return True if the exception class name appears in non_retryable_errors."""
        name = type(exc).__name__
        return name in self.non_retryable_errors

    def delay_seconds(self, attempt: int) -> float:
        """Compute delay (seconds) before the next attempt.

        Args:
            attempt: 1-based attempt number that just failed.
        """
        if self.backoff_strategy == "fixed":
            delay_ms = self.base_delay_ms
        elif self.backoff_strategy == "exponential":
            delay_ms = min(self.base_delay_ms * (2 ** (attempt - 1)), self.max_delay_ms)
        elif self.backoff_strategy == "jitter":
            cap = min(self.base_delay_ms * (2 ** (attempt - 1)), self.max_delay_ms)
            delay_ms = random.uniform(0, cap)
        else:
            delay_ms = self.base_delay_ms
        return delay_ms / 1000.0


# ---------------------------------------------------------------------------
# Per-skill retry registry
# ---------------------------------------------------------------------------

#: Maps skill_id → RetryPolicy.  Overrides DEFAULT_RETRY_POLICY for specific engines.
SKILL_RETRY_POLICIES: dict[str, RetryPolicy] = {
    # Planetary hub may be slow; allow more time between retries.
    "planetary_signal_hub": RetryPolicy(
        max_attempts=3,
        backoff_strategy="exponential",
        base_delay_ms=1_000,
        max_delay_ms=8_000,
    ),
    # Research Desk article loading: fast fixed retry.
    "article_loader": RetryPolicy(
        max_attempts=2,
        backoff_strategy="fixed",
        base_delay_ms=300,
    ),
    # Crystal GraphRAG: jitter to avoid thundering-herd on graph DB.
    "crystal_graphrag": RetryPolicy(
        max_attempts=3,
        backoff_strategy="jitter",
        base_delay_ms=500,
        max_delay_ms=5_000,
    ),
    # Biometric engine: fast, local — minimal retry.
    "biometric_coherence": RetryPolicy(
        max_attempts=2,
        backoff_strategy="fixed",
        base_delay_ms=200,
    ),
    # Dev Suite code execution: non-idempotent; single attempt only.
    "dev_suite_executor": RetryPolicy(
        max_attempts=1,
    ),
}

#: Fallback for any skill not explicitly registered.
DEFAULT_RETRY_POLICY = RetryPolicy()


def get_policy(skill_id: str) -> RetryPolicy:
    """Return the RetryPolicy for *skill_id*, falling back to DEFAULT_RETRY_POLICY."""
    return SKILL_RETRY_POLICIES.get(skill_id, DEFAULT_RETRY_POLICY)
