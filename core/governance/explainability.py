"""
core/governance/explainability.py
Explainability — canon-grounded decision explanation layer.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CanonCitation:
    """A reference to a specific canon document / section."""
    canon_id:   str
    section:    str = ""
    excerpt:    str = ""
    weight:     float = 1.0

    def to_dict(self) -> dict:
        return {
            "canon_id": self.canon_id,
            "section":  self.section,
            "excerpt":  self.excerpt,
            "weight":   self.weight,
        }


@dataclass
class ExplainabilityRecord:
    decision:   str
    citations:  List[CanonCitation] = field(default_factory=list)
    rationale:  str = ""
    confidence: float = 1.0

    def add_citation(self, citation: CanonCitation) -> None:
        self.citations.append(citation)

    def to_dict(self) -> dict:
        return {
            "decision":   self.decision,
            "citations":  [c.to_dict() for c in self.citations],
            "rationale":  self.rationale,
            "confidence": self.confidence,
        }


class ExplainabilityEngine:
    """Generates canon-grounded explanations for GAIA decisions."""

    def __init__(self) -> None:
        self._records: List[ExplainabilityRecord] = []

    def explain(
        self,
        decision:   str,
        citations:  Optional[List[CanonCitation]] = None,
        rationale:  str = "",
        confidence: float = 1.0,
    ) -> ExplainabilityRecord:
        record = ExplainabilityRecord(
            decision=decision,
            citations=citations or [],
            rationale=rationale,
            confidence=confidence,
        )
        self._records.append(record)
        return record

    def history(self) -> List[ExplainabilityRecord]:
        return list(self._records)
