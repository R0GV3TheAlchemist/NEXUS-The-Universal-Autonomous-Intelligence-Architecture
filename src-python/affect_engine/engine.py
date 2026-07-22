# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Affect Engine — AffectEngine
# Phase E: NotImplementedError stubs replaced with live PAD model outputs.
# Accepts: text, biometric, schumann_sync signals.
# Outputs: live AffectState (P, A, D + label + confidence).
# Maintains: rolling history, EMA smoothing, arc trend analysis.
# Wires into: Planetary Ledger on every ingest.

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

from .pad import AffectState, _EMA_ALPHA, classify_pad
from .signal_parsers import BiometricParser, SchumannSyncParser, TextSentimentParser

logger = logging.getLogger("affect_engine.engine")

_HISTORY_MAXLEN = 200


class AffectEngine:
    """
    Live Affect Engine for NEXUS / GAIA-OS.

    Maintains a rolling PAD state vector updated via EMA blending.
    Accepts multi-modal signals: text, biometric, schumann_sync.
    Emits every state update to the Planetary Ledger.

    Architecture: NEXUS_UNIVERSAL_OS.md Domain 2.2
    GAIAN Law V: Emotional Sovereignty

    Usage::

        engine = AffectEngine(ledger=ledger)
        state = engine.ingest({"text": "Phase E is live. Feeling focused."})
        print(state.label, state.pleasure, state.arousal)

        state = engine.ingest({
            "heart_rate": 68.0,
            "hrv": 55.0,
            "schumann_alignment": 0.87,
            "schumann_coherence": 0.91,
        })
    """

    def __init__(
        self,
        memory: Any | None = None,
        ledger: Any | None = None,
        session_id: str | None = None,
        ema_alpha: float = _EMA_ALPHA,
    ) -> None:
        self.memory = memory
        self._ledger = ledger
        self._session_id = session_id
        self._alpha = ema_alpha
        self.current_state: AffectState = AffectState()  # neutral start
        self._history: deque[AffectState] = deque(maxlen=_HISTORY_MAXLEN)
        self._lock = threading.Lock()
        self._text_parser    = TextSentimentParser()
        self._bio_parser     = BiometricParser()
        self._schumann_parser = SchumannSyncParser()
        self._backend_name   = "pad-ema-lexicon"
        logger.info("AffectEngine initialised (backend=%s)", self._backend_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> AffectState:
        """Return the current live AffectState."""
        with self._lock:
            return self.current_state

    def ingest(self, signal: dict[str, Any]) -> AffectState:
        """
        Ingest a multi-modal signal dict and update the live PAD state.

        Recognised keys:
          text                  : str  — free text to score sentiment
          heart_rate            : float (bpm)
          hrv                   : float (ms RMSSD)
          skin_conductance      : float (μS)
          schumann_alignment    : float 0–1
          schumann_coherence    : float 0–1
          pleasure / arousal / dominance : float — direct PAD override
          label                 : str  — manual label override

        Returns:
            Updated AffectState.
        """
        with self._lock:
            new_state = self._parse_signal(signal)
            blended = self.current_state.blend(new_state, alpha=self._alpha)
            self._history.append(blended)
            self.current_state = blended

        self._ledger_write(blended)
        logger.debug(
            "ingest label=%s P=%.3f A=%.3f D=%.3f",
            blended.label, blended.pleasure, blended.arousal, blended.dominance,
        )
        return blended

    def arc_trend(self, window: int = 10) -> dict[str, Any]:
        """
        Return affect arc trend over the last `window` states.

        Returns a dict with:
          window         : int  — number of samples used
          mean_pleasure  : float
          mean_arousal   : float
          mean_dominance : float
          pleasure_delta : float — last vs first in window
          arousal_delta  : float
          dominance_delta: float
          dominant_label : str  — most frequent label in window
          trajectory     : str  — "rising", "falling", "stable"
        """
        with self._lock:
            history = list(self._history)[-window:]

        if not history:
            return {
                "window": 0,
                "mean_pleasure": 0.0,
                "mean_arousal": 0.5,
                "mean_dominance": 0.5,
                "pleasure_delta": 0.0,
                "arousal_delta": 0.0,
                "dominance_delta": 0.0,
                "dominant_label": "neutral",
                "trajectory": "stable",
            }

        n = len(history)
        mean_p = round(sum(s.pleasure  for s in history) / n, 4)
        mean_a = round(sum(s.arousal   for s in history) / n, 4)
        mean_d = round(sum(s.dominance for s in history) / n, 4)
        delta_p = round(history[-1].pleasure  - history[0].pleasure,  4)
        delta_a = round(history[-1].arousal   - history[0].arousal,   4)
        delta_d = round(history[-1].dominance - history[0].dominance, 4)

        label_counts: dict[str, int] = {}
        for s in history:
            label_counts[s.label] = label_counts.get(s.label, 0) + 1
        dominant_label = max(label_counts, key=lambda k: label_counts[k])

        # Trajectory: driven by pleasure delta (primary valence axis)
        if delta_p > 0.05:
            trajectory = "rising"
        elif delta_p < -0.05:
            trajectory = "falling"
        else:
            trajectory = "stable"

        return {
            "window": n,
            "mean_pleasure":   mean_p,
            "mean_arousal":    mean_a,
            "mean_dominance":  mean_d,
            "pleasure_delta":  delta_p,
            "arousal_delta":   delta_a,
            "dominance_delta": delta_d,
            "dominant_label":  dominant_label,
            "trajectory":      trajectory,
        }

    def reset(self) -> None:
        """Reset PAD state to neutral and clear history."""
        with self._lock:
            self.current_state = AffectState()
            self._history.clear()
        logger.info("AffectEngine reset to neutral")

    @property
    def history(self) -> list[AffectState]:
        with self._lock:
            return list(self._history)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_signal(self, signal: dict[str, Any]) -> AffectState:
        """Parse all recognised signal keys into a single new AffectState."""
        base = self.current_state
        partial_states: list[AffectState] = []

        # 1. Text sentiment
        if "text" in signal and signal["text"]:
            delta = self._text_parser.parse(signal["text"])
            partial_states.append(delta.to_state(base))

        # 2. Biometric
        bio_keys = ("heart_rate", "hrv", "skin_conductance")
        if any(k in signal for k in bio_keys):
            delta = self._bio_parser.parse(
                heart_rate=signal.get("heart_rate"),
                hrv=signal.get("hrv"),
                skin_conductance=signal.get("skin_conductance"),
            )
            partial_states.append(delta.to_state(base))

        # 3. Schumann sync
        if "schumann_alignment" in signal:
            delta = self._schumann_parser.parse(
                alignment_score=signal["schumann_alignment"],
                coherence=signal.get("schumann_coherence", 0.7),
            )
            partial_states.append(delta.to_state(base))

        # 4. Direct PAD override
        if any(k in signal for k in ("pleasure", "arousal", "dominance")):
            p = signal.get("pleasure", base.pleasure)
            a = signal.get("arousal",  base.arousal)
            d = signal.get("dominance", base.dominance)
            label = signal.get("label") or classify_pad(p, a, d)
            partial_states.append(AffectState(
                pleasure=p, arousal=a, dominance=d, label=label, sources=["direct"],
            ))

        if not partial_states:
            return base  # no-op

        # Average all partial states
        n = len(partial_states)
        avg_p = sum(s.pleasure  for s in partial_states) / n
        avg_a = sum(s.arousal   for s in partial_states) / n
        avg_d = sum(s.dominance for s in partial_states) / n
        avg_c = sum(s.confidence for s in partial_states) / n
        all_sources = list({src for s in partial_states for src in s.sources})

        from .pad import clamp
        return AffectState(
            pleasure=round(clamp(avg_p, -1.0, 1.0), 4),
            arousal=round(clamp(avg_a,  0.0,  1.0), 4),
            dominance=round(clamp(avg_d, 0.0, 1.0), 4),
            label=classify_pad(avg_p, avg_a, avg_d),
            confidence=round(avg_c, 4),
            sources=all_sources,
        )

    def _ledger_write(self, state: AffectState) -> None:
        if self._ledger is None:
            return
        try:
            from planetary_ledger import EventType
            self._ledger.append(
                event_type=EventType.CUSTOM,
                payload={"affect_state": state.to_dict(), "engine": "affect_engine"},
                tags=["affect", "pad", "phase-e"],
                session_id=self._session_id,
            )
        except Exception:
            logger.exception("AffectEngine ledger write failed")
