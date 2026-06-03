"""Issue #187 — DegradedFallbacks: per-engine graceful degradation strategies.

Canon C30: No silent failures — every fallback surfaces a user_message.
Canon C01: Sovereignty — user always receives a [Retry →] action option.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FallbackMode(str, Enum):
    CACHED = "cached"                        # Return last known cached value
    MANUAL_INPUT = "manual_input"            # Prompt user to provide input manually
    DOWNGRADE = "downgrade_to_vector"        # Drop to simpler/cheaper model
    AFFECTIVE_ONLY = "affective_only"        # Biometric fallback: affective inference only
    SKIP = "skip"                            # Skip this engine, reduce DQ confidence
    STATIC_RESPONSE = "static_response"      # Return a safe static placeholder


@dataclass
class DegradedFallback:
    mode: FallbackMode
    user_message: str
    max_cache_age_min: int | None = None     # Only relevant for CACHED mode
    static_payload: Any | None = None        # Only relevant for STATIC_RESPONSE mode
    dq_confidence_multiplier: float = 0.75  # Applied to DecisionQuality when fallback fires
    allow_retry: bool = True                 # Show [Retry →] in UI


DEGRADED_FALLBACKS: dict[str, DegradedFallback] = {
    # Planetary hub offline → use last known snapshot (max 15 min old)
    "planetary_signal_hub": DegradedFallback(
        mode=FallbackMode.CACHED,
        max_cache_age_min=15,
        user_message=(
            "Planetary signals unavailable — showing last known state "
            "(up to 15 min ago). Earth context may be slightly stale."
        ),
        dq_confidence_multiplier=0.85,
    ),

    # Research Desk article loader fails → offer manual paste
    "article_loader": DegradedFallback(
        mode=FallbackMode.MANUAL_INPUT,
        user_message=(
            "Article fetch failed. You can paste the content directly "
            "and GAIA will process it from here."
        ),
        dq_confidence_multiplier=0.90,
    ),

    # Crystal GraphRAG query fails → fall back to flat vector search
    "crystal_graphrag": DegradedFallback(
        mode=FallbackMode.DOWNGRADE,
        user_message=(
            "Graph search temporarily unavailable — using semantic similarity only. "
            "Relationship context is excluded from this response."
        ),
        dq_confidence_multiplier=0.70,
    ),

    # Biometric engine offline → use affective state inference only
    "biometric_coherence": DegradedFallback(
        mode=FallbackMode.AFFECTIVE_ONLY,
        user_message=(
            "Wearable offline — coherence is estimated from voice tone and "
            "affective signals only. HRV-based guidance is paused."
        ),
        dq_confidence_multiplier=0.80,
    ),

    # Soul Mirror unavailable → skip, continue with analytical response
    "soul_mirror": DegradedFallback(
        mode=FallbackMode.SKIP,
        user_message=(
            "Soul Mirror is temporarily unavailable. "
            "Responding analytically — emotional attunement is reduced."
        ),
        dq_confidence_multiplier=0.75,
    ),

    # Dev Suite code execution fails → surface error cleanly
    "dev_suite_executor": DegradedFallback(
        mode=FallbackMode.STATIC_RESPONSE,
        user_message=(
            "Code execution environment is unavailable right now. "
            "Your code has been preserved — try again when the sandbox recovers."
        ),
        static_payload={"status": "execution_unavailable", "code_preserved": True},
        dq_confidence_multiplier=0.0,
        allow_retry=True,
    ),

    # Dream Weaver unavailable → skip journal capture
    "dream_weaver": DegradedFallback(
        mode=FallbackMode.SKIP,
        user_message=(
            "Dream journaling is temporarily unavailable. "
            "Your entry has been queued locally and will sync when the service recovers."
        ),
        dq_confidence_multiplier=0.90,
    ),
}
