"""
core/sovereign_memory/types.py
==============================
Data contracts for the sovereign memory sub-system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AffectSnapshot:
    """A point-in-time snapshot of the user's affective state."""

    id:               str
    session_id:       str
    timestamp:        datetime
    valence:          float        = 0.0    # [-1, 1]
    arousal:          float        = 0.0    # [0, 1]
    dominance:        float        = 0.5    # [0, 1]
    primary_emotion:  str          = "neutral"
    metadata:         Dict[str, Any] = field(default_factory=dict)


__all__ = ["AffectSnapshot"]
