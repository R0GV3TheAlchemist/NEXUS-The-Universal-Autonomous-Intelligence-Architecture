"""
crystal/engine.py
CrystalCore — the tick loop that assembles CrystalState from the four streams.

Tick schedule (from spec C-CC01 §2):
  - On app launch (once)
  - Every 15 minutes while the app is active
  - Immediately when GAIA completes a conversation turn (lightweight)

All stream fetching is async over localhost HTTP.
Graceful degradation: any stream failure → neutral default; no exception raised.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing   import Optional

import httpx

from .coherence     import compute_coherence
from .narrative     import build_narrative
from .orb_params    import derive_orb_params
from .persona_tone  import derive_persona_tone
from .types         import (
    CoherenceBand, CrystalState, OrbParams, PersonaTone,
    band_from_psi,
)

try:
    from ..config import API_BASE
except ImportError:
    import os
    API_BASE = os.environ.get("GAIA_API_BASE", "http://localhost:8000")

logger = logging.getLogger("gaia.crystal")

_HTTP_TIMEOUT = 4.0

# Stream endpoints
_URL_AFFECT   = f"{API_BASE}/affect/trend"
_URL_STAGE    = f"{API_BASE}/stage/record"
_URL_SHADOW   = f"{API_BASE}/shadow/state"
_URL_SCHUMANN = f"{API_BASE}/schumann/state"

# Defaults when streams are unavailable
_NEUTRAL_MARKERS = {
    "decision_entropy":        50.0,
    "hrv_coherence":           50.0,
    "journaling_depth":        50.0,
    "focus_session_length":    50.0,
    "goal_completion_rate":    50.0,
    "emotional_arc_stability": 50.0,
}


class CrystalCore:
    """
    Assembles a CrystalState from the four live streams on each tick.

    Maintains an in-memory cache of the latest state.
    History (list of CrystalState) is kept for up to 7 × 96 = 672 ticks.
    """

    MAX_HISTORY = 672  # 7 days × 96 ticks/day (15-min cadence)

    def __init__(self, principal_id: str = "default") -> None:
        self.principal_id = principal_id
        self._latest: Optional[CrystalState] = None
        self._history: list[CrystalState] = []
        self._tick_lock = asyncio.Lock()

    # ------------------------------------------------------------------ public

    async def tick(self) -> CrystalState:
        """Run a full evaluation tick and return the updated CrystalState."""
        async with self._tick_lock:
            state = await self._build_state()
            self._latest = state
            self._history.append(state)
            if len(self._history) > self.MAX_HISTORY:
                self._history = self._history[-self.MAX_HISTORY:]
            logger.debug(
                "Crystal tick complete — Ψ=%.3f band=%s tone=%s",
                state.coherence,
                state.coherence_band.value,
                state.persona_tone.value,
            )
            return state

    @property
    def latest(self) -> Optional[CrystalState]:
        """Return the most recent CrystalState without triggering a new tick."""
        return self._latest

    def history(self, days: int = 7) -> list[CrystalState]:
        """Return history ticks from the last N days (approximate by tick count)."""
        ticks_per_day = 96  # one tick per 15 minutes
        max_ticks = days * ticks_per_day
        return self._history[-max_ticks:]

    # ----------------------------------------------------------------- private

    async def _build_state(self) -> CrystalState:
        """Fetch all streams, compute Ψ, and assemble a CrystalState."""
        affect, stage, shadow, schumann = await asyncio.gather(
            self._fetch_affect(),
            self._fetch_stage(),
            self._fetch_shadow(),
            self._fetch_schumann(),
            return_exceptions=True,
        )

        # If a gather element is an exception, replace with empty dict / defaults
        affect   = affect   if isinstance(affect,   dict) else {}
        stage    = stage    if isinstance(stage,    dict) else {}
        shadow   = shadow   if isinstance(shadow,   dict) else {}
        schumann = schumann if isinstance(schumann, dict) else {}

        # ── Extract affect fields ──────────────────────────────────────────
        arc_stability = float(affect.get("arc_stability",  0.5))
        valence_trend = float(affect.get("valence_trend",  0.0))
        volatility    = float(affect.get("volatility",     0.0))
        dominant_emotion = str(affect.get("dominant_emotion", "neutral"))

        # ── Extract stage fields ───────────────────────────────────────────
        marker_scores = dict(stage.get("marker_scores", _NEUTRAL_MARKERS))
        active_stage  = int(stage.get("stage", 3))

        # ── Extract shadow fields ──────────────────────────────────────────
        shadow_available     = bool(shadow)
        integration_progress = float(shadow.get("integration_progress", 0.5))
        shadow_intensity     = float(shadow.get("shadow_intensity",     0.0))
        active_archetype     = str(shadow.get("active_archetype")  or "Unknown")

        # ── Extract schumann fields ────────────────────────────────────────
        schumann_available = bool(schumann)
        alignment_score    = float(schumann.get("alignment_score", 0.5))
        schumann_confidence= float(schumann.get("confidence",      0.0))
        disturbance_raw    = str(schumann.get("disturbance_level", "unavailable"))
        # Normalise disturbance string
        disturbance = disturbance_raw if disturbance_raw in (
            "stable", "elevated", "disturbed"
        ) else "unavailable"

        # ── Compute coherence ──────────────────────────────────────────────
        psi, A, S, E, H = compute_coherence(
            arc_stability=arc_stability,
            valence_trend=valence_trend,
            volatility=volatility,
            marker_scores=marker_scores,
            integration_progress=integration_progress,
            shadow_intensity=shadow_intensity,
            shadow_available=shadow_available,
            schumann_alignment=alignment_score,
            schumann_confidence=schumann_confidence,
            schumann_available=schumann_available,
        )

        band      = band_from_psi(psi)
        tone      = derive_persona_tone(band)
        narrative = build_narrative(band, dominant_emotion, disturbance)

        # Build intermediate state (without orb_params) to pass to derive_orb_params
        # We need a partially assembled state — so we build the orb params last.
        partial = _PartialState(
            coherence=psi,
            coherence_band=band,
            dominant_emotion=dominant_emotion,
        )
        orb = derive_orb_params(partial)  # type: ignore[arg-type]

        return CrystalState(
            timestamp=datetime.now(timezone.utc),
            affect_coherence=A,
            stage_coherence=S,
            shadow_integration=E,
            schumann_alignment=H,
            coherence=psi,
            coherence_band=band,
            dominant_emotion=dominant_emotion,
            active_stage=active_stage,
            active_archetype=active_archetype,
            schumann_disturbance=disturbance,
            inner_narrative=narrative,
            persona_tone=tone,
            orb_params=orb,
        )

    # ── Stream fetchers ────────────────────────────────────────────────────

    async def _fetch_affect(self) -> dict:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(f"{_URL_AFFECT}/{self.principal_id}")
            r.raise_for_status()
            return r.json()

    async def _fetch_stage(self) -> dict:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(f"{_URL_STAGE}/{self.principal_id}")
            r.raise_for_status()
            return r.json()

    async def _fetch_shadow(self) -> dict:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(f"{_URL_SHADOW}/{self.principal_id}")
            r.raise_for_status()
            return r.json()

    async def _fetch_schumann(self) -> dict:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(_URL_SCHUMANN)
            r.raise_for_status()
            return r.json()


# ---------------------------------------------------------------------------
# Lightweight proxy for orb param derivation (avoids circular import)
# We pass a duck-typed object to derive_orb_params so it can read
# .coherence, .coherence_band, and .dominant_emotion.
# ---------------------------------------------------------------------------

class _PartialState:
    def __init__(
        self,
        coherence:        float,
        coherence_band:   CoherenceBand,
        dominant_emotion: str,
    ) -> None:
        self.coherence        = coherence
        self.coherence_band   = coherence_band
        self.dominant_emotion = dominant_emotion
