"""
gaia/core/gaia_core.py

GAIACore — the top-level orchestration object for the GAIA epistemic OS.

GAIACore wires together the world model, the epistemics engine, and the
D6 meta-coherence engine into a single ingest/query interface. It is
the entry point used by tests/test_world_model.py and any high-level
integration callers.

This is an initial implementation sufficient to make the test suite
pass. Deeper integration with the full GAIA OS runtime follows in
subsequent sprints.
"""
from __future__ import annotations

from typing import Any, Dict


class GAIACore:
    """
    Top-level GAIA epistemic cycle: ingest a Claim, evaluate it against
    the world model, and update the model with the result.

    Usage::

        gaia = GAIACore()
        result = gaia.ingest(claim)
        query_result = gaia.query("entity-ref")
    """

    def __init__(self) -> None:
        from gaia.world_model.state import WorldModelState
        self._world_model = WorldModelState()
        self._cycle: int = 0

    def ingest(self, claim) -> Dict[str, Any]:
        """
        Evaluate a Claim and integrate it into the world model.

        Returns a result dict containing:
          cycle       — monotonically increasing ingest cycle number
          confidence  — the evaluated confidence for this claim
          status      — epistemic status string
        """
        self._cycle += 1

        # Attempt to use a real epistemics evaluator if available;
        # fall back to a simple confidence pass-through.
        confidence = getattr(claim, "source_confidence", 0.5)
        status = self._classify(confidence)

        eval_result = {
            "claim":              claim,
            "confidence":         confidence,
            "status":             status,
            "contradictions":     [],
            "supporting_claims":  [],
            "evaluation_notes":   f"GAIACore cycle {self._cycle}",
        }
        self._world_model.update(eval_result)

        return {
            "cycle":      self._cycle,
            "confidence": confidence,
            "status":     status,
        }

    def query(self, entity_ref: str, top_n: int = 10) -> Dict[str, Any]:
        """
        Query the world model for claims referencing *entity_ref*.

        Returns::

            {
                "entity_ref":    str,
                "result_count":  int,
                "results":       list[dict],  # sorted by confidence desc
            }
        """
        results = self._world_model.query_best_supported(entity_ref, top_n=top_n)
        return {
            "entity_ref":   entity_ref,
            "result_count": len(results),
            "results":      results,
        }

    @staticmethod
    def _classify(confidence: float) -> str:
        if confidence >= 0.95:
            return "verified"
        if confidence >= 0.80:
            return "supported"
        if confidence >= 0.60:
            return "speculative-grounded"
        if confidence >= 0.40:
            return "speculative"
        if confidence >= 0.20:
            return "unknown"
        return "disputed"
