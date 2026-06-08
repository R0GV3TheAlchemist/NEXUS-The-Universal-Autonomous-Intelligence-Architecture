"""
core/stage_bridge/types.py
==========================
Data contracts for the stage bridge sub-system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class FeelingState:
    """Composite feeling state bridging affect inference to stage engine."""

    affect_state:     str
    intensity:        float        = 0.5    # [0, 1]
    valence:          float        = 0.0    # [-1, 1]
    arousal:          float        = 0.0    # [0, 1]
    source:           str          = "inference"
    metadata:         Dict[str, Any] = field(default_factory=dict)


__all__ = ["FeelingState"]
