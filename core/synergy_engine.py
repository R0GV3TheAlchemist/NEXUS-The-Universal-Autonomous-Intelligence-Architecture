"""
Synergy Engine — integrates multiple GAIA sub-engines into coherent output.

Provides:
  - SynergyEngine : main orchestrator class
      - evaluate()             : score + keyword resolution pass
      - compute_from_adapter() : resolve a GAIAStateAdapter → compute()
      - compute_from_params()  : canonical G-8 call site (dict-based)
      - get_history()          : return evaluation history
      - reset()                : clear history
  - _resolve_keyword_conflicts : internal helper (tested directly)
  - _classify_stage            : internal helper (tested directly)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.state_adapter import GAIAStateAdapter

log = logging.getLogger(__name__)


class SynergyStage(str, Enum):
    INITIATION = "initiation"
    ACTIVATION = "activation"
    INTEGRATION = "integration"
    SYNTHESIS = "synthesis"
    COMPLETION = "completion"


@dataclass
class SynergyResult:
    """Result of a synergy evaluation pass."""

    stage: SynergyStage = SynergyStage.INITIATION
    score: float = 0.0
    conflicts: List[str] = field(default_factory=list)
    resolved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "score": self.score,
            "conflicts": self.conflicts,
            "resolved": self.resolved,
            "metadata": self.metadata,
        }


# ------------------------------------------------------------------ #
#  Internal helpers — tested directly by test suite                   #
# ------------------------------------------------------------------ #

def _resolve_keyword_conflicts(keywords: List[str]) -> List[str]:
    """
    Resolve keyword conflicts by deduplicating and normalising.
    Returns a sorted, deduplicated list of keywords.
    """
    seen = set()
    resolved = []
    for kw in keywords:
        normalised = kw.strip().lower()
        if normalised and normalised not in seen:
            seen.add(normalised)
            resolved.append(normalised)
    return sorted(resolved)


def _classify_stage(score: float) -> SynergyStage:
    """
    Classify a numerical synergy score into a SynergyStage.

    Bands:
      0.0 – 0.2   → INITIATION
      0.2 – 0.4   → ACTIVATION
      0.4 – 0.6   → INTEGRATION
      0.6 – 0.8   → SYNTHESIS
      0.8 – 1.0   → COMPLETION
    """
    if score < 0.2:
        return SynergyStage.INITIATION
    if score < 0.4:
        return SynergyStage.ACTIVATION
    if score < 0.6:
        return SynergyStage.INTEGRATION
    if score < 0.8:
        return SynergyStage.SYNTHESIS
    return SynergyStage.COMPLETION


# ------------------------------------------------------------------ #
#  Main class                                                          #
# ------------------------------------------------------------------ #

class SynergyEngine:
    """Integrates sub-engine outputs into a single synergy pass."""

    def __init__(self) -> None:
        self._history: List[SynergyResult] = []
        log.info("SynergyEngine initialised")

    def evaluate(
        self,
        keywords: Optional[List[str]] = None,
        score: float = 0.0,
    ) -> SynergyResult:
        resolved = _resolve_keyword_conflicts(keywords or [])
        stage = _classify_stage(score)
        result = SynergyResult(
            stage=stage,
            score=score,
            resolved=resolved,
        )
        self._history.append(result)
        return result

    def compute_from_adapter(self, adapter: "GAIAStateAdapter") -> Any:
        """Resolve a GAIAStateAdapter and delegate to self.compute().

        Args:
            adapter: A GAIAStateAdapter (or AsyncGAIAStateAdapter) instance
                     wrapping the GaianRecord for this computation.

        Returns:
            Whatever self.compute() returns (typically a tuple of
            (SynergyReading, new_state)).
        """
        params = adapter.to_synergy_params()
        return self.compute(**params)  # type: ignore[attr-defined]

    def compute_from_params(self, params: dict) -> Any:
        """Canonical G-8 call site — dict-based entry point.

        Prefer this over bare compute() for all new call sites.
        The bare compute() signature is considered deprecated for
        external callers.
        """
        return self.compute(**params)  # type: ignore[attr-defined]

    def get_history(self) -> List[SynergyResult]:
        return list(self._history)

    def reset(self) -> None:
        self._history.clear()


_synergy_engine: Optional[SynergyEngine] = None


def get_synergy_engine() -> SynergyEngine:
    global _synergy_engine
    if _synergy_engine is None:
        _synergy_engine = SynergyEngine()
    return _synergy_engine
