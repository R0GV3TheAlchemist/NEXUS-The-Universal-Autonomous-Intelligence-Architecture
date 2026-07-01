"""
GAIA Core Loop
The primary runtime cycle of the GAIA epistemic world model OS.

This is the system behaviour:
  input → claim → evaluate → update world model
       → detect contradictions → resolve/flag
       → persist state → agents query updated ground truth
"""

from typing import Dict, Any
from datetime import datetime

from .ontology.registry import OntologyRegistry
from .epistemics.claim import Claim
from .epistemics.evaluator import EpistemicEvaluator
from .contradiction.detector import ContradictionDetector
from .contradiction.resolver import ContradictionResolver
from .world_model.state import WorldModelState


class GAIACore:
    """
    GAIACore is the central runtime of the GAIA epistemic world model.

    It orchestrates the full epistemic cycle:
    1. Ingest a claim
    2. Evaluate it against the current knowledge base
    3. Update the world model
    4. Detect and resolve contradictions
    5. Persist the updated state
    6. Serve queries from agents

    This is the system that defines what agents believe is real.
    """

    def __init__(self):
        self.ontology = OntologyRegistry()
        self.evaluator = EpistemicEvaluator()
        self.detector = ContradictionDetector()
        self.resolver = ContradictionResolver()
        self.world_model = WorldModelState()
        self._knowledge_base: Dict[str, Claim] = {}  # claim_id → Claim
        self._cycle_count = 0
        self._initialized_at = datetime.utcnow()

        print(f"GAIA Core v0.1 initialised at {self._initialized_at.isoformat()}")
        print("The system that defines what agents believe is real. Ready.")

    def ingest(self, claim: Claim) -> Dict[str, Any]:
        """
        The primary GAIA cycle.
        Takes a Claim, evaluates it, updates the world model,
        handles contradictions, and returns the full result.

        This is the GAIA core loop.
        """
        self._cycle_count += 1

        # 1. Evaluate the claim epistemically
        result = self.evaluator.evaluate(claim, self._knowledge_base)

        # 2. Update claim with computed confidence + status
        claim.confidence = result["confidence"]
        claim.status = result["status"]
        claim.provenance_chain.append(result["evaluation_notes"])

        # 3. Flag contradictions on the claim
        for contradiction in result.get("contradictions", []):
            if contradiction.id not in claim.contradiction_flags:
                claim.contradiction_flags.append(contradiction.id)

        # 4. Add to knowledge base
        self._knowledge_base[claim.id] = claim

        # 5. Update the world model
        self.world_model.update(result)

        # 6. Resolve contradictions if any
        resolution_results = []
        if result["contradictions"]:
            conflict_pairs = [(claim, c) for c in result["contradictions"]]
            resolution_results = self.resolver.resolve_batch(conflict_pairs)

        return {
            "cycle": self._cycle_count,
            "claim_id": claim.id,
            "status": claim.status,
            "confidence": claim.confidence,
            "contradictions_detected": len(result["contradictions"]),
            "resolutions": resolution_results,
            "world_model_stats": self.world_model.stats()
        }

    def query(
        self,
        entity_id: str,
        min_confidence: float = 0.0
    ) -> Dict[str, Any]:
        """
        Agent query interface.
        'What is the best-supported current state of X?'
        """
        results = self.world_model.query_best_supported(entity_id, min_confidence)
        return {
            "entity_id": entity_id,
            "query_timestamp": datetime.utcnow().isoformat(),
            "result_count": len(results),
            "results": results
        }

    def snapshot(self) -> Dict[str, Any]:
        """Full world model snapshot — 'Git for reality' commit point."""
        return {
            "gaia_version": "0.1.0",
            "snapshot_timestamp": datetime.utcnow().isoformat(),
            "cycle_count": self._cycle_count,
            "ontology_stats": self.ontology.stats(),
            "world_model": self.world_model.snapshot()
        }

    def __repr__(self) -> str:
        return (
            f"GAIACore(v0.1, cycles={self._cycle_count}, "
            f"claims={len(self._knowledge_base)}, "
            f"world_model={self.world_model})"
        )
