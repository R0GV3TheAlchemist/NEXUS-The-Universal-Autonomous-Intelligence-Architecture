"""
GAIA Adversarial Validator — v0.6
GAIA's self-challenge mechanism.

Instead of passively accepting claims, every node in the network
evaluates whether it agrees, disputes, or is uncertain about a claim.
The aggregate of these opinions becomes the adversarial validation result.

This is what makes GAIA self-correcting:
  - Reliable nodes reinforce each other's claims
  - Inconsistent or low-quality nodes lose influence over time
  - Contradictions become informative (not just noise)
  - Truth emerges under adversarial pressure, not democratic averaging

v0.6: heuristic opinion model (confidence thresholds)
v0.7: NLI-based semantic agreement detection
v0.8: formal proof-checking for logical claims
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

SUPPORT_THRESHOLD  = 0.65   # confidence above this → "support"
REJECT_THRESHOLD   = 0.35   # confidence below this → "reject"


class ValidationResult:
    """Result of an adversarial validation round for a single claim."""

    def __init__(
        self,
        claim_id: str,
        votes: Dict[str, int],
        node_opinions: List[Dict[str, Any]]
    ):
        self.claim_id      = claim_id
        self.votes         = votes          # {"support": n, "reject": n, "uncertain": n}
        self.node_opinions = node_opinions  # per-node breakdown
        self.timestamp     = datetime.utcnow().isoformat()

    @property
    def verdict(self) -> str:
        """Overall network verdict on this claim."""
        s = self.votes.get("support", 0)
        r = self.votes.get("reject", 0)
        u = self.votes.get("uncertain", 0)
        total = s + r + u
        if total == 0:
            return "no_data"
        if s > r and s > u:
            return "network_supported"
        if r > s and r > u:
            return "network_rejected"
        return "network_contested"

    @property
    def support_ratio(self) -> float:
        total = sum(self.votes.values())
        return round(self.votes.get("support", 0) / total, 4) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id":      self.claim_id,
            "verdict":       self.verdict,
            "votes":         self.votes,
            "support_ratio": self.support_ratio,
            "node_opinions": self.node_opinions,
            "timestamp":     self.timestamp
        }

    def __repr__(self) -> str:
        return (
            f"ValidationResult(claim={self.claim_id[:8]}..., "
            f"verdict={self.verdict}, "
            f"support={self.votes.get('support', 0)}, "
            f"reject={self.votes.get('reject', 0)}, "
            f"uncertain={self.votes.get('uncertain', 0)})"
        )


class AdversarialValidator:
    """
    Challenges claims across the network.
    Each node evaluates whether it agrees, disputes, or is uncertain.
    The aggregate of opinions becomes the validation verdict.
    """

    def challenge(
        self,
        claim: Dict[str, Any],
        node_states: Dict[str, Dict[str, Any]]
    ) -> ValidationResult:
        """
        Run an adversarial validation round for a single claim.
        Returns a ValidationResult with per-node opinions and aggregate verdict.
        """
        votes = {"support": 0, "reject": 0, "uncertain": 0}
        node_opinions = []

        for node_id, snapshot in node_states.items():
            state = snapshot.get("state", snapshot)  # handle both formats
            opinion = self._evaluate_node_opinion(claim, state)
            votes[opinion] += 1
            node_opinions.append({
                "node_id":  node_id,
                "opinion":  opinion,
                "basis":    self._opinion_basis(claim, state)
            })

        return ValidationResult(
            claim_id=claim.get("id", ""),
            votes=votes,
            node_opinions=node_opinions
        )

    def challenge_batch(
        self,
        claims: List[Dict[str, Any]],
        node_states: Dict[str, Dict[str, Any]]
    ) -> List[ValidationResult]:
        """Run adversarial validation for a batch of claims."""
        return [self.challenge(c, node_states) for c in claims]

    def _evaluate_node_opinion(
        self,
        claim: Dict[str, Any],
        state: Dict[str, Any]
    ) -> str:
        """
        A node's opinion on a claim is determined by:
        1. Does the node have this claim in its local state?
        2. If yes: what is its confidence?
        3. If no: check for semantically similar claims (v0.7+)
        """
        claim_id = claim.get("id", "")
        local = state.get(claim_id)

        if not local:
            # v0.7+: semantic similarity check here
            return "uncertain"

        local_conf = local.get("confidence", 0.5)

        if local_conf >= SUPPORT_THRESHOLD:
            return "support"
        if local_conf <= REJECT_THRESHOLD:
            return "reject"
        return "uncertain"

    def _opinion_basis(
        self,
        claim: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return the basis for a node's opinion (for audit trail)."""
        claim_id = claim.get("id", "")
        local = state.get(claim_id)
        if not local:
            return {"reason": "claim_not_in_local_state"}
        return {
            "reason":     "local_confidence_threshold",
            "confidence": local.get("confidence", 0),
            "status":     local.get("status", "unknown")
        }
