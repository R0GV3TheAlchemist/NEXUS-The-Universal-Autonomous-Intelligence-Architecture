# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Affect Engine — Phase E: operational

from .pad import AffectState, classify_pad, PAD_LABELS  if False else None
from .pad import AffectState, classify_pad
from .engine import AffectEngine
from .signal_parsers import (
    PADDelta,
    TextSentimentParser,
    BiometricParser,
    SchumannSyncParser,
)

__all__ = [
    "AffectState",
    "AffectEngine",
    "classify_pad",
    "PADDelta",
    "TextSentimentParser",
    "BiometricParser",
    "SchumannSyncParser",
]
