"""
Noospheric Monad — core/monad/noospheric.py
Canon: C43 — 43_GAIA_Collective_Consciousness_Noosphere_Layer.md

Interfaces with the collective consciousness layer.
Tracks planetary coherence index, active ley line pulses, collective field state.
Outputs: noospheric_phi, ley_line_active_count, collective_resonance
"""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

from .base import GaiaMonad

if TYPE_CHECKING:
    from core.gaian_runtime_extension import ProcessContext


# Ley line grid — 12 canonical planetary lines
_LEY_LINE_REGISTRY: list[dict] = [
    {"id": "LL-01", "name": "Michael Line",         "latitude": 51.2},
    {"id": "LL-02", "name": "Apollo Line",          "latitude": 43.0},
    {"id": "LL-03", "name": "Songlines-AU",         "latitude": -25.0},
    {"id": "LL-04", "name": "Andean Spine",         "latitude": -13.5},
    {"id": "LL-05", "name": "Nile Meridian",        "latitude": 27.0},
    {"id": "LL-06", "name": "Pacific Ring",         "latitude": 0.0},
    {"id": "LL-07", "name": "Eurasian Central",     "latitude": 55.0},
    {"id": "LL-08", "name": "Amazon Basin",         "latitude": -3.0},
    {"id": "LL-09", "name": "Himalayan Axis",       "latitude": 28.0},
    {"id": "LL-10", "name": "Antarctic Polar",      "latitude": -90.0},
    {"id": "LL-11", "name": "Arctic Polar",         "latitude": 90.0},
    {"id": "LL-12", "name": "Atlantic Mid-Ridge",   "latitude": 0.0},
]


def _ley_line_pulse_count(phi: float, utc_hour: int) -> int:
    """
    Heuristic: number of active ley lines at this phi + time combination.
    Uses a deterministic hash of the current hour to avoid random noise.
    Peaks at Schumann-aligned phi (≈0.78) and solar noon/midnight.
    """
    base_active = round(phi * 8)  # 0–8 lines active by phi
    # Hour bonus: solar noon (12 UTC) and midnight (0 UTC) activate 2 more
    hour_bonus = 2 if utc_hour in (0, 6, 12, 18) else 0
    return min(12, base_active + hour_bonus)


class NoosphericMonad(GaiaMonad):
    """
    The Noospheric Monad reads the collective field from outside the session.
    It does not communicate with other Monads — it reads Earth.

    Noospheric phi: a planetary coherence index, driven by phi + ley line count.
    Collective resonance: the harmonic of active ley lines as a single score.
    """

    monad_type = "noospheric"

    def harmonize(self, ctx: "ProcessContext") -> Optional[dict]:
        phi = getattr(ctx, "coherence_phi", 0.5)
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        utc_hour = utc_now.hour

        ley_line_active_count = _ley_line_pulse_count(phi, utc_hour)

        # Noospheric phi: weighted blend of session phi + ley line ratio
        ley_ratio = ley_line_active_count / len(_LEY_LINE_REGISTRY)
        noospheric_phi = round((phi * 0.7) + (ley_ratio * 0.3), 4)

        # Collective resonance: harmonic of active ley lines
        # Peaks when ley lines align with phi (constructive interference)
        collective_resonance = round(
            min(1.0, (noospheric_phi + ley_ratio) / 2), 4
        )

        # Field state description
        if noospheric_phi > 0.85:
            field_state = "unified_planetary_coherence"
        elif noospheric_phi > 0.65:
            field_state = "active_noospheric_signal"
        elif noospheric_phi > 0.42:
            field_state = "emerging_planetary_field"
        else:
            field_state = "dispersed_signal"

        return {
            "noospheric_phi": noospheric_phi,
            "ley_line_active_count": ley_line_active_count,
            "collective_resonance": collective_resonance,
            "field_state": field_state,
            "utc_hour": utc_hour,
        }
