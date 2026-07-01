"""
GAIA Contradiction Resolver
Resolves conflicts between claims using source trust weighting.
Flags unresolvable conflicts for human review.
"""

from typing import List, Tuple, Dict
from ..epistemics.claim import Claim


class ContradictionResolver:
    """
    Given a conflict pair (claim_a, claim_b), the resolver:
    1. Compares source confidence weights
    2. Resolves if confidence differential is sufficient
    3. Flags for human review if differential is insufficient

    Resolution threshold: if one claim's confidence exceeds the other
    by more than RESOLUTION_THRESHOLD, the higher-confidence claim wins.
    """

    RESOLUTION_THRESHOLD = 0.20  # Minimum confidence differential to auto-resolve
    HUMAN_REVIEW_FLAG = "REQUIRES_HUMAN_REVIEW"

    def resolve(
        self,
        claim_a: Claim,
        claim_b: Claim
    ) -> Dict:
        """
        Attempt to resolve a contradiction between two claims.

        Returns:
            dict with keys: winner, loser, resolution_type, notes
        """
        diff = abs(claim_a.confidence - claim_b.confidence)

        if diff >= self.RESOLUTION_THRESHOLD:
            winner = claim_a if claim_a.confidence > claim_b.confidence else claim_b
            loser = claim_b if winner == claim_a else claim_a
            return {
                "winner": winner,
                "loser": loser,
                "resolution_type": "auto_resolved",
                "confidence_differential": diff,
                "notes": (
                    f"Auto-resolved: '{winner.source}' (conf={winner.confidence:.3f}) "
                    f"outweighs '{loser.source}' (conf={loser.confidence:.3f}) "
                    f"by {diff:.3f}"
                )
            }
        else:
            return {
                "winner": None,
                "loser": None,
                "resolution_type": self.HUMAN_REVIEW_FLAG,
                "confidence_differential": diff,
                "notes": (
                    f"Insufficient confidence differential ({diff:.3f} < {self.RESOLUTION_THRESHOLD}). "
                    f"Claims: '{claim_a.id[:8]}' vs '{claim_b.id[:8]}'. "
                    f"Human review required."
                )
            }

    def resolve_batch(
        self,
        conflicts: List[Tuple[Claim, Claim]]
    ) -> List[Dict]:
        """Resolve a batch of conflict pairs."""
        return [self.resolve(a, b) for a, b in conflicts]
