"""
core/memory/tiers/tier_router.py

MemoryTierRouter — coordinates reads and writes across HOT / WARM / COLD.

Promotion rules:
  COLD → WARM   on direct get() if entry found in cold
  WARM → HOT    on direct get() if entry found in warm

Demotion rules:
  HOT  → WARM   run via demote_stale_hot()  (call from a scheduler)
  WARM → COLD   run via demote_stale_warm() (call from a scheduler)

All demotion methods are safe to call concurrently.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .hot_tier import HotTier
from .warm_tier import WarmTier
from .cold_tier import ColdTier


class MemoryTierRouter:
    """
    Unified read/write interface across all three memory tiers.

    Parameters
    ----------
    hot  : HotTier
    warm : WarmTier
    cold : ColdTier
    hot_ttl : float
        TTL (seconds) assigned to entries promoted into the hot tier.
    cold_score_threshold : float
        Warm entries with score() below this value are demoted to cold.
    """

    def __init__(
        self,
        hot: Optional[HotTier] = None,
        warm: Optional[WarmTier] = None,
        cold: Optional[ColdTier] = None,
        hot_ttl: float = 300.0,
        cold_score_threshold: float = 0.05,
    ) -> None:
        self.hot = hot or HotTier()
        self.warm = warm or WarmTier()
        self.cold = cold or ColdTier()
        self.hot_ttl = hot_ttl
        self.cold_score_threshold = cold_score_threshold

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def put(
        self,
        key: str,
        value: Any,
        *,
        tags: Optional[List[str]] = None,
        relevance: float = 1.0,
        tier: str = "hot",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Write an entry to the specified tier (default: 'hot').
        Returns the tier the entry was written to.
        """
        tags = tags or []
        if tier == "hot":
            self.hot.put(key, value, tags=tags, ttl=self.hot_ttl)
            self.warm.put(key, value, tags=tags, relevance=relevance, metadata=metadata)
            return "hot"
        elif tier == "warm":
            self.warm.put(key, value, tags=tags, relevance=relevance, metadata=metadata)
            return "warm"
        elif tier == "cold":
            self.cold.put(key, value, tags=tags, metadata=metadata or {})
            return "cold"
        else:
            raise ValueError(f"Unknown tier: {tier!r}. Must be 'hot', 'warm', or 'cold'.")

    # ------------------------------------------------------------------
    # Read (with automatic promotion)
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Read a value, promoting upward through tiers on cache miss."""
        # 1. Hot tier
        value = self.hot.get(key)
        if value is not None:
            return value

        # 2. Warm tier — promote to hot on hit
        warm_entry = self.warm.get_entry(key)
        if warm_entry is not None:
            self.hot.put(
                key,
                warm_entry.value,
                tags=warm_entry.tags,
                ttl=self.hot_ttl,
            )
            return warm_entry.value

        # 3. Cold tier — promote to warm then hot on hit
        cold_entry = self.cold.get_entry(key)
        if cold_entry is not None:
            self.warm.put(
                key,
                cold_entry.value,
                tags=cold_entry.tags,
                relevance=0.5,
                metadata=cold_entry.metadata,
            )
            self.hot.put(
                key,
                cold_entry.value,
                tags=cold_entry.tags,
                ttl=self.hot_ttl,
            )
            return cold_entry.value

        return None

    def contains(self, key: str) -> bool:
        return (
            self.hot.contains(key)
            or bool(self.warm.get_entry(key))
            or self.cold.contains(key)
        )

    def delete(self, key: str) -> bool:
        """Remove from all tiers.  Returns True if found anywhere."""
        a = self.hot.delete(key)
        b = self.warm.delete(key)
        c = self.cold.delete(key)
        return a or b or c

    # ------------------------------------------------------------------
    # Demotion / maintenance
    # ------------------------------------------------------------------

    def demote_stale_hot(self) -> int:
        """Push TTL-expired hot entries down to warm.  Returns count."""
        # Hot tier auto-evicts on read; here we just sweep proactively.
        evicted = self.hot._sweep_expired()
        return evicted

    def demote_stale_warm(self) -> int:
        """
        Move warm entries below cold_score_threshold into cold storage.
        Returns count demoted.
        """
        stale = self.warm.stale_entries()
        scored_low = [
            e for e in self.warm.top_entries(n=10_000)
            if e.score(self.warm.half_life) < self.cold_score_threshold
        ]
        victims = {e.key: e for e in stale + scored_low}
        for entry in victims.values():
            self.cold.put(
                entry.key,
                entry.value,
                tags=entry.tags,
                source_tier="warm",
                metadata=entry.metadata,
            )
            self.warm.delete(entry.key)
        return len(victims)

    def stats(self) -> Dict[str, Any]:
        return {
            "hot": self.hot.stats(),
            "warm": {"count": self.warm.count()},
            "cold": self.cold.stats(),
        }
