"""
core/governance/explainability.py
Explainability — canon-grounded decision explanation layer.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class CanonCitation:
    """A reference to a specific canon document / section."""
    canon_id: str
    section:  str   = ""
    excerpt:  str   = ""
    weight:   float = 1.0

    def to_dict(self) -> dict:
        return {
            "canon_id": self.canon_id,
            "section":  self.section,
            "excerpt":  self.excerpt,
            "weight":   self.weight,
        }


@dataclass
class DecisionReport:
    """
    Structured report summarising a single GAIA decision with
    canon citations and human-readable rationale.
    """
    decision_id:  str
    decision:     str
    rationale:    str                  = ""
    confidence:   float                = 1.0
    citations:    List[CanonCitation]  = field(default_factory=list)
    metadata:     Dict[str, Any]       = field(default_factory=dict)
    timestamp:    str                  = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    doctrine_ref: str = "C-EXPLAINABILITY:1.0"

    def add_citation(self, citation: CanonCitation) -> None:
        self.citations.append(citation)

    def to_dict(self) -> dict:
        return {
            "decision_id":  self.decision_id,
            "decision":     self.decision,
            "rationale":    self.rationale,
            "confidence":   round(self.confidence, 4),
            "citations":    [c.to_dict() for c in self.citations],
            "metadata":     self.metadata,
            "timestamp":    self.timestamp,
            "doctrine_ref": self.doctrine_ref,
        }


@dataclass
class ExplainabilityRecord:
    """Legacy record — kept for back-compat."""
    decision:   str
    citations:  List[CanonCitation] = field(default_factory=list)
    rationale:  str   = ""
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
        rationale:  str   = "",
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


# Alias
DecisionExplainer = ExplainabilityEngine
