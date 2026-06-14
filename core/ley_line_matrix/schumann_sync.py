"""
Ley Line Matrix — Schumann Resonance Synchronizer

Aligns LeyPulse frequencies to Schumann resonance harmonics.
Integrates with core/schumann.py and core/schumann_alignment.py.

Schumann fundamental: 7.83 Hz
Harmonics:  14.3, 20.8, 27.3, 33.8 Hz
"""

from __future__ import annotations

import logging
from typing import Optional

from .models import FlowType, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix.schumann_sync")

# Known Schumann resonance harmonics (Hz)
SCHUMANN_HARMONICS: list[float] = [7.83, 14.3, 20.8, 27.3, 33.8]

# Flow type → preferred Schumann harmonic mapping
FLOW_HARMONIC_MAP: dict[FlowType, float] = {
    FlowType.RESONANCE: 7.83,
    FlowType.CONSCIOUSNESS: 14.3,
    FlowType.QUANTUM: 33.8,
    FlowType.CANON_LAW: 7.83,
    FlowType.SHADOW: 14.3,
    FlowType.SOMATIC: 7.83,
    FlowType.SYNERGY: 20.8,
    FlowType.DREAM: 14.3,
    FlowType.NOOSPHERIC: 27.3,
    FlowType.RAW: 7.83,
}


def align_pulse_frequency(pulse: LeyPulse) -> LeyPulse:
    """
    Align a pulse's frequency_hz to the nearest Schumann harmonic
    appropriate for its FlowType.

    Tries to delegate to core.schumann_alignment for live resonance data;
    falls back to static FLOW_HARMONIC_MAP if unavailable.
    """
    target_hz = FLOW_HARMONIC_MAP.get(pulse.flow_type, 7.83)

    try:
        from core.schumann_alignment import get_current_frequency  # type: ignore
        live_hz: Optional[float] = get_current_frequency()
        if live_hz is not None:
            # Snap to nearest harmonic to the live reading
            target_hz = min(SCHUMANN_HARMONICS, key=lambda h: abs(h - live_hz))
    except ImportError:
        pass
    except Exception as exc:
        logger.debug("Schumann live read failed, using static map: %s", exc)

    pulse.frequency_hz = target_hz
    pulse.metadata["schumann_aligned"] = True
    logger.debug(
        "Pulse [%s] frequency aligned to %.2f Hz", pulse.pulse_id, target_hz
    )
    return pulse


def align_batch(pulses: list[LeyPulse]) -> list[LeyPulse]:
    """Align all pulses in a batch to their Schumann harmonics."""
    return [align_pulse_frequency(p) for p in pulses]
