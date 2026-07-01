"""
GAIA Epistemic Evaluator — Ontology-Aware (v0.2)
Now evaluates claims against the structured ontology,
not just text similarity.

Upgrade path:
  v0.1: keyword overlap
  v0.2: entity-level + keyword overlap  ← THIS VERSION
  v0.3: semantic NLI-based contradiction detection
  v0.4: Bayesian confidence propagation
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ontology.registry import OntologyRegistry

# Scoring weights
SUPPORT_BOOST    = 0.08
CONTRA_PENALTY   = 0.12
SOURCE_BONUS     = 0.05
ENTITY_MATCH_BOOST = 0.06  # NEW in v0.2: entity-level match bonus

# Status thresholds
THRESHOLDS = {
    "verified":             0.85,
    "supported":            0.65,
    "speculative-grounded": 0.45,
    "speculative":          0.25,
}


class EpistemicEvaluator:
    """
    Ontology-aware epistemic evaluator.
    Evaluates claims against both the text knowledge base
    and the structured entity graph in the ontology.
    """

    def evaluate(
        self,
        claim,
        ontology: "OntologyRegistry",
        knowledge_base: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Full epistemic evaluation of a claim against the ontology.
        """
        kb = knowledge_base or {}

        # 1. Text-based related claims
        text_related = self._find_text_related(claim, kb)

        # 2. Entity-based related claims (NEW in v0.2)
        entity_related = self._find_entity_related(claim, ontology)

        # Merge, deduplicate
        all_related_ids = {c.id for c in entity_related}
        merged_related = list(entity_related)
        for c in text_related:
            if c.id not in all_related_ids:
                merged_related.append(c)
                all_related_ids.add(c.id)

        # 3. Detect contradictions
        contradictions = self._detect_contradictions(claim, merged_related)

        # 4. Supporting claims
        supporting = [
            c for c in merged_related
            if c.status in ("supported", "verified", "speculative-grounded")
        ]

        # 5. Compute confidence
        confidence = self._compute_confidence(
            claim, supporting, contradictions, entity_related
        )

        # 6. Assign status
        status = self._assign_status(confidence, contradictions)

        return {
            "claim":           claim,
            "confidence":      confidence,
            "status":          status,
            "contradictions":  contradictions,
            "supporting":      supporting,
            "related_entities": claim.entities,
            "evaluation_method": "ontology-aware-v0.2",
        }

    # ——— internal ———

    def _find_text_related(
        self,
        claim,
        knowledge_base: Dict[str, Any]
    ) -> List:
        """Find related claims via keyword overlap (v0.1 method, retained)."""
        words = set(claim.statement.lower().split())
        related = []
        for existing in knowledge_base.values():
            if hasattr(existing, 'id') and existing.id == claim.id:
                continue
            if hasattr(existing, 'statement'):
                entry_words = set(existing.statement.lower().split())
                if len(words & entry_words) >= 3:
                    related.append(existing)
        return related

    def _find_entity_related(
        self,
        claim,
        ontology: "OntologyRegistry"
    ) -> List:
        """
        Find claims in the ontology that share entity references.
        This is the v0.2 upgrade: structured entity-level matching.
        """
        if not claim.entities:
            return []
        related = []
        seen = set()
        for entity_id in claim.entities:
            for existing_claim in ontology.get_claims_for_entity(entity_id):
                if existing_claim.id != claim.id and existing_claim.id not in seen:
                    related.append(existing_claim)
                    seen.add(existing_claim.id)
        return related

    def _detect_contradictions(self, claim, related: List) -> List:
        positive = {"supported", "verified"}
        negative = {"disputed", "contradicted"}
        contradictions = []
        for r in related:
            a_pos = claim.status in positive
            b_neg = r.status in negative
            a_neg = claim.status in negative
            b_pos = r.status in positive
            if (a_pos and b_neg) or (a_neg and b_pos):
                contradictions.append(r)
        return contradictions

    def _compute_confidence(
        self,
        claim,
        supporting: List,
        contradictions: List,
        entity_related: List
    ) -> float:
        base = 0.30
        base += len(getattr(claim, 'sources', [])) * SOURCE_BONUS
        base += len(supporting) * SUPPORT_BOOST
        base -= len(contradictions) * CONTRA_PENALTY
        base += len(entity_related) * ENTITY_MATCH_BOOST  # v0.2 entity bonus
        return round(max(0.0, min(1.0, base)), 4)

    def _assign_status(self, confidence: float, contradictions: List) -> str:
        if contradictions:
            return "disputed"
        for status, threshold in THRESHOLDS.items():
            if confidence >= threshold:
                return status
        return "speculative"
