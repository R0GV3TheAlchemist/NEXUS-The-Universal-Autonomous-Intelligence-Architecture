"""
Noosphere — collective intelligence / coherence field layer for GAIA-OS.

Provides:
  - Noosphere          : main class tracking coherence state
  - CoherenceEvent     : dataclass for individual coherence observations
  - NoosphereLayer     : enum of recognised layers
  - get_noosphere()    : module-level singleton accessor
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

log = logging.getLogger(__name__)

NOOSPHERE_CONTENT: str = ""  # legacy placeholder


class NoosphereLayer(str, Enum):
    INDIVIDUAL = "individual"
    COLLECTIVE = "collective"
    PLANETARY = "planetary"
    COSMIC = "cosmic"


@dataclass
class CoherenceEvent:
    """A single coherence observation from the noosphere."""

    layer: NoosphereLayer = NoosphereLayer.INDIVIDUAL
    magnitude: float = 0.0
    source: str = "unknown"
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "layer": self.layer.value,
            "magnitude": self.magnitude,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class Noosphere:
    """Manages the collective coherence field."""

    def __init__(self) -> None:
        self._events: List[CoherenceEvent] = []
        self._coherence: float = 0.0
        log.info("Noosphere initialised (stub)")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def register_event(self, event: CoherenceEvent) -> None:
        self._events.append(event)
        self._coherence = min(1.0, self._coherence + event.magnitude * 0.01)
        log.debug("CoherenceEvent registered: %s", event)

    def get_coherence(self) -> float:
        return self._coherence

    def get_events(self) -> List[CoherenceEvent]:
        return list(self._events)

    def reset(self) -> None:
        self._events.clear()
        self._coherence = 0.0

    def to_dict(self) -> dict:
        return {
            "coherence": self._coherence,
            "event_count": len(self._events),
        }


# ------------------------------------------------------------------ #
#  Module-level singleton                                              #
# ------------------------------------------------------------------ #

_noosphere: Optional[Noosphere] = None


def get_noosphere() -> Noosphere:
    """Return the module-level singleton Noosphere."""
    global _noosphere
    if _noosphere is None:
        _noosphere = Noosphere()
    return _noosphere
