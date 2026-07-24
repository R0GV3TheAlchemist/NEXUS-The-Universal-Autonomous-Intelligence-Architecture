# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
Uncertainty Layer — Capability Domain 20

Every GAIA output must carry: Confidence, Evidence, Assumptions, Unknowns,
Sensitivity, Failure Modes. Not just: Answer.

This alone would be a major leap in production AI reliability.

Related: Issue #753 Tier 3 Domain 20 (Uncertainty Layer)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class UncertaintyEnvelope:
    """
    Wraps any GAIA output with a full uncertainty characterization.

    Fields:
        output:          The actual answer/result
        confidence:      0.0–1.0 — overall confidence in this output
        evidence:        What evidence supports this output
        assumptions:     What must be true for this to be valid
        unknowns:        What we don't know that could change this
        sensitivity:     Which assumptions, if wrong, most change the output
        failure_modes:   Ways this output could be wrong
        source_domains:  Which GAIA domains contributed (Provenance)
    """
    output: Any
    confidence: float
    evidence: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    sensitivity: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    source_domains: list[str] = field(default_factory=list)

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        return self.confidence >= threshold

    def summary(self) -> str:
        """Human-readable uncertainty summary."""
        return (
            f"Confidence: {self.confidence:.0%} | "
            f"Evidence sources: {len(self.evidence)} | "
            f"Unknowns: {len(self.unknowns)} | "
            f"Failure modes: {len(self.failure_modes)}"
        )


class UncertaintyLayer:
    """
    Wraps outputs from any GAIA domain in an UncertaintyEnvelope.

    TODO (Issue #753 Domain 20):
    - Implement evidence extraction from RAG pipeline
    - Implement assumption detection from reasoning chain
    - Implement sensitivity analysis for key claims
    - Integrate with Provenance Layer (Domain 21) for source attribution
    """

    def wrap(
        self,
        output: Any,
        confidence: float,
        evidence: Optional[list[str]] = None,
        assumptions: Optional[list[str]] = None,
        unknowns: Optional[list[str]] = None,
        failure_modes: Optional[list[str]] = None,
    ) -> UncertaintyEnvelope:
        """
        Wrap an output in an UncertaintyEnvelope.
        TODO: implement full population from reasoning chain — Issue #753 Domain 20
        """
        return UncertaintyEnvelope(
            output=output,
            confidence=confidence,
            evidence=evidence or [],
            assumptions=assumptions or [],
            unknowns=unknowns or [],
            failure_modes=failure_modes or [],
        )
