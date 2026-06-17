# core/research/synthesizer.py
# F821 fix: added missing import for RetrievedSource.
# Alias fix: added Synthesizer = ResearchSynthesizer for test compatibility.

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RetrievedSource:
    """A single retrieved source document for synthesis."""
    source_id: str
    content: str
    url: Optional[str] = None
    confidence: float = 1.0
    source_type: str = "document"   # 'document', 'canon', 'web', 'memory'


@dataclass
class SynthesisResult:
    """Output of the ResearchSynthesizer."""
    summary: str
    sources: List[RetrievedSource]
    falsification_conditions: List[str]
    confidence: float


class ResearchSynthesizer:
    """
    Synthesises multi-source research into a coherent answer.

    Each source is evaluated for:
      - Contribution to the synthesis
      - Falsification conditions (per C04 epistemic rigor)
      - Confidence weighting
    """

    def synthesize(
        self,
        query: str,
        sources: List[RetrievedSource],
    ) -> SynthesisResult:
        """Synthesise sources into a result."""
        summary_parts = [s.content[:200] for s in sources]
        summary = " | ".join(summary_parts) if summary_parts else "No sources available."

        falsifications = [
            self._generate_falsification(source)
            for source in sources
        ]

        confidence = (
            sum(s.confidence for s in sources) / len(sources)
            if sources
            else 0.0
        )

        return SynthesisResult(
            summary=summary,
            sources=sources,
            falsification_conditions=falsifications,
            confidence=round(confidence, 3),
        )

    def _generate_falsification(
        self,
        source: RetrievedSource,
    ) -> str:
        """Generate a falsification condition per source type."""
        if source.source_type == "canon":
            return f"Canon source {source.source_id} would be falsified by a superseding C-series document."
        if source.source_type == "web":
            return f"Web source {source.source_id} would be falsified by a more recent publication at the same URL."
        return f"Source {source.source_id} would be falsified by direct empirical contradiction."


# ---------------------------------------------------------------------------
# Alias - test suite compatibility
# Tests import: from core.research.synthesizer import Synthesizer
# ---------------------------------------------------------------------------
Synthesizer = ResearchSynthesizer
