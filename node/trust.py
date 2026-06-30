"""
GAIA Trust Profile — v0.6
Each node in the GAIA network maintains a dynamic trust score.
Trust is earned through validated claims and lost through disputes and rejections.

This is not static weighting — nodes have reputations that evolve.
Reliable nodes gain influence over time.
Unreliable nodes lose it.

Score dynamics:
  +0.02 per accepted claim (incremental trust gain)
  -0.02 per disputed claim (conflict penalty)
  -0.05 per rejected claim (larger penalty for low-quality assertions)
  Clamped to [0.0, 1.0] at all times.

Baseline: 0.5 (neutral — neither trusted nor distrusted)

v0.7 upgrade path: replace heuristic deltas with Bayesian posterior update
"""

from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class TrustEvent(BaseModel):
    """Immutable record of a single trust-affecting event."""
    event_type: str           # "accepted" | "rejected" | "disputed"
    delta: float
    score_after: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    claim_id: str = ""
    reason: str = ""


class TrustProfile:
    """
    Dynamic trust score for a single GAIA node.
    Tracks full audit history of every trust-affecting event.
    """

    BASELINE        = 0.5
    ACCEPT_DELTA    = +0.02
    REJECT_DELTA    = -0.05
    DISPUTE_DELTA   = -0.02

    def __init__(self, node_id: str, initial_score: float = None):
        self.node_id = node_id
        self.score   = initial_score if initial_score is not None else self.BASELINE
        self.history: Dict[str, int] = {
            "accepted": 0,
            "rejected": 0,
            "disputed": 0
        }
        self._event_log: List[TrustEvent] = []

    # ——— Update methods ———

    def update_on_accept(self, claim_id: str = "") -> float:
        """Called when this node's claim is accepted by the network."""
        return self._apply("accepted", self.ACCEPT_DELTA, claim_id)

    def update_on_reject(self, claim_id: str = "") -> float:
        """Called when this node's claim is rejected by adversarial validation."""
        return self._apply("rejected", self.REJECT_DELTA, claim_id)

    def update_on_dispute(self, claim_id: str = "") -> float:
        """Called when this node's claim is in contested territory."""
        return self._apply("disputed", self.DISPUTE_DELTA, claim_id)

    def _apply(self, event_type: str, delta: float, claim_id: str) -> float:
        prev_score = self.score
        self.score = round(max(0.0, min(1.0, self.score + delta)), 4)
        self.history[event_type] += 1
        self._event_log.append(TrustEvent(
            event_type=event_type,
            delta=delta,
            score_after=self.score,
            claim_id=claim_id
        ))
        return self.score

    # ——— Read ———

    def tier(self) -> str:
        """Human-readable trust tier for display."""
        if self.score >= 0.85:  return "HIGHLY_TRUSTED"
        if self.score >= 0.65:  return "TRUSTED"
        if self.score >= 0.45:  return "NEUTRAL"
        if self.score >= 0.25:  return "LOW_TRUST"
        return "UNTRUSTED"

    def reliability_ratio(self) -> float:
        """Fraction of interactions that were accepted vs total."""
        total = sum(self.history.values())
        return round(self.history["accepted"] / total, 4) if total > 0 else 0.5

    def recent_events(self, n: int = 10) -> List[Dict]:
        return [
            e.model_dump() for e in self._event_log[-n:]
        ]

    def summary(self) -> Dict[str, Any]:
        return {
            "node_id":          self.node_id,
            "score":            self.score,
            "tier":             self.tier(),
            "history":          dict(self.history),
            "reliability_ratio": self.reliability_ratio(),
            "total_events":     len(self._event_log)
        }

    def __repr__(self) -> str:
        return (
            f"TrustProfile(node={self.node_id}, "
            f"score={self.score:.3f}, "
            f"tier={self.tier()}, "
            f"accepted={self.history['accepted']}, "
            f"rejected={self.history['rejected']}, "
            f"disputed={self.history['disputed']})"
        )
