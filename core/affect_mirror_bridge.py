"""
core/affect_mirror_bridge.py

Backward-compatibility shim.

The legacy `core/affect_inference.py` module exposed a flat
affect-inference API.  New code should import from
`core.affective_mirror` directly.  This shim re-exports the
canonical names so existing code does not need an immediate update.

Deprecated — will be removed in the next major refactor.
"""
from __future__ import annotations

from core.affective_mirror import (  # noqa: F401
    AffectiveChannel,
    AffectiveState,
    AffectiveMirror,
    BiometricAffectInference,
    ChannelReading,
    CrisisDetector,
    CrisisMarker,
    EmotionLabel,
    EmotionalArcTracker,
    AffectiveFusion,
    SoulMirrorAffectBridge,
    TextSentimentAnalyzer,
    VoiceProsodyAnalyzer,
)

__all__ = [
    "AffectiveChannel",
    "AffectiveState",
    "AffectiveMirror",
    "BiometricAffectInference",
    "ChannelReading",
    "CrisisDetector",
    "CrisisMarker",
    "EmotionLabel",
    "EmotionalArcTracker",
    "AffectiveFusion",
    "SoulMirrorAffectBridge",
    "TextSentimentAnalyzer",
    "VoiceProsodyAnalyzer",
]
