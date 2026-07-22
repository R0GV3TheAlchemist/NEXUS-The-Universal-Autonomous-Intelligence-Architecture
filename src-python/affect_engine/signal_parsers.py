# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Affect Engine — Signal Parsers
# Phase E: Convert raw input signals into PAD delta vectors.
# Parsers: text sentiment, biometric (HRV/HR/skin conductance), Schumann sync.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .pad import AffectState, classify_pad, clamp


# ---------------------------------------------------------------------------
# PADDelta — a signal's contribution to the PAD state
# ---------------------------------------------------------------------------

@dataclass
class PADDelta:
    """Additive delta to be applied to the current PAD state."""
    pleasure:  float = 0.0
    arousal:   float = 0.0
    dominance: float = 0.0
    confidence: float = 1.0
    source: str = "unknown"

    def to_state(self, base: AffectState) -> AffectState:
        """Apply this delta on top of a base state."""
        p = clamp(base.pleasure  + self.pleasure,  -1.0,  1.0)
        a = clamp(base.arousal   + self.arousal,    0.0,  1.0)
        d = clamp(base.dominance + self.dominance,  0.0,  1.0)
        return AffectState(
            pleasure=round(p, 4),
            arousal=round(a, 4),
            dominance=round(d, 4),
            label=classify_pad(p, a, d),
            confidence=round(self.confidence, 4),
            sources=[self.source],
        )


# ---------------------------------------------------------------------------
# Text sentiment parser (lexicon-based, no ML deps required)
# ---------------------------------------------------------------------------

_POSITIVE_WORDS = {
    "great", "excellent", "amazing", "wonderful", "fantastic", "brilliant",
    "happy", "love", "joy", "elated", "thrilled", "good", "nice", "awesome",
    "excited", "grateful", "proud", "confident", "calm", "peaceful", "focused",
    "ready", "strong", "energized", "alive", "free", "clear", "alive", "inspired",
    "progress", "success", "win", "yes", "perfect", "beautiful", "serene", "alive",
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "sad", "depressed", "anxious",
    "worried", "scared", "angry", "frustrated", "hate", "upset", "stressed",
    "tired", "exhausted", "overwhelmed", "lost", "broken", "fail", "wrong",
    "error", "problem", "issue", "trouble", "pain", "hurt", "cry", "fear",
    "no", "never", "can't", "won't", "don't", "isn't", "wasn't", "didn't",
}
_HIGH_AROUSAL_WORDS = {
    "urgent", "emergency", "now", "immediately", "critical", "alert", "alarm",
    "excited", "thrilled", "panic", "rush", "fast", "quick", "intense",
    "explosive", "chaotic", "furious", "terrified", "electrified",
}
_LOW_AROUSAL_WORDS = {
    "sleepy", "tired", "bored", "calm", "quiet", "slow", "gentle", "soft",
    "relaxed", "still", "peaceful", "serene", "tranquil", "drowsy",
}


class TextSentimentParser:
    """Lexicon-based text → PADDelta parser. Zero external dependencies."""

    def parse(self, text: str) -> PADDelta:
        if not text or not isinstance(text, str):
            return PADDelta(source="text")

        tokens = set(re.findall(r"\b\w+\b", text.lower()))
        n = max(len(tokens), 1)

        pos_score = len(tokens & _POSITIVE_WORDS) / n
        neg_score = len(tokens & _NEGATIVE_WORDS) / n
        hi_arousal = len(tokens & _HIGH_AROUSAL_WORDS) / n
        lo_arousal = len(tokens & _LOW_AROUSAL_WORDS) / n

        pleasure  = clamp((pos_score - neg_score) * 2.0, -1.0, 1.0)
        arousal   = clamp((hi_arousal - lo_arousal) * 2.0, -0.3, 0.3)  # delta, not absolute
        dominance = clamp(pos_score * 0.4, 0.0, 0.3)  # positive text raises dominance slightly

        confidence = min(1.0, (pos_score + neg_score + hi_arousal + lo_arousal) * 5)
        return PADDelta(
            pleasure=round(pleasure, 4),
            arousal=round(arousal, 4),
            dominance=round(dominance, 4),
            confidence=round(max(0.1, confidence), 4),
            source="text",
        )


# ---------------------------------------------------------------------------
# Biometric parser (HRV / HR / skin conductance → PADDelta)
# Based on established psychophysiology mappings:
#   High HR + low HRV = high arousal, negative valence
#   High HRV         = calm, positive valence, higher dominance
#   High GSR         = high arousal
# ---------------------------------------------------------------------------

# Reference resting-state baselines
_HR_REST   = 70.0    # bpm
_HRV_REST  = 50.0    # ms RMSSD
_GSR_REST  = 5.0     # μS


class BiometricParser:
    """Biometric signal → PADDelta using psychophysiology mappings."""

    def parse(
        self,
        heart_rate: float | None = None,
        hrv: float | None = None,
        skin_conductance: float | None = None,
    ) -> PADDelta:
        pleasure  = 0.0
        arousal   = 0.0
        dominance = 0.0
        sources_used = 0

        if heart_rate is not None:
            hr_delta = (heart_rate - _HR_REST) / _HR_REST
            arousal  += clamp(hr_delta * 0.6, -0.3, 0.3)
            pleasure += clamp(-hr_delta * 0.3, -0.3, 0.3)
            sources_used += 1

        if hrv is not None:
            hrv_ratio = hrv / _HRV_REST
            pleasure  += clamp((hrv_ratio - 1.0) * 0.4, -0.3, 0.3)
            arousal   += clamp(-(hrv_ratio - 1.0) * 0.3, -0.25, 0.25)
            dominance += clamp((hrv_ratio - 1.0) * 0.2, -0.2, 0.2)
            sources_used += 1

        if skin_conductance is not None:
            gsr_delta = (skin_conductance - _GSR_REST) / max(_GSR_REST, 0.1)
            arousal   += clamp(gsr_delta * 0.4, -0.25, 0.35)
            sources_used += 1

        confidence = min(1.0, sources_used / 3.0 + 0.2)
        return PADDelta(
            pleasure=round(clamp(pleasure, -1.0, 1.0), 4),
            arousal=round(clamp(arousal, -0.5, 0.5), 4),
            dominance=round(clamp(dominance, -0.3, 0.3), 4),
            confidence=round(confidence, 4),
            source="biometric",
        )


# ---------------------------------------------------------------------------
# Schumann sync parser
# High alignment score → increased calm, positive valence, coherence
# ---------------------------------------------------------------------------

class SchumannSyncParser:
    """Schumann sync reading → PADDelta."""

    def parse(self, alignment_score: float, coherence: float) -> PADDelta:
        """
        A fully aligned (score=1.0, coherence=1.0) Schumann reading maps to:
          +0.15 pleasure (resonance feels good)
          -0.10 arousal  (resonance is calming)
          +0.10 dominance (coherence = inner stability)
        Scales linearly with alignment_score.
        """
        factor = clamp(alignment_score, 0.0, 1.0)
        coh    = clamp(coherence, 0.0, 1.0)
        return PADDelta(
            pleasure=round( 0.15 * factor * coh, 4),
            arousal=round( -0.10 * factor * coh, 4),
            dominance=round(0.10 * factor * coh, 4),
            confidence=round(0.5 + 0.5 * factor, 4),
            source="schumann",
        )
