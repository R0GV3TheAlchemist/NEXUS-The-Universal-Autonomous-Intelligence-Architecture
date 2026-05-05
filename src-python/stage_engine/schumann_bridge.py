"""
Stage Engine ← Schumann Bridge  (Issue #63 / #64 integration)

Converts a SchumannState snapshot (from the Schumann Alignment Layer)
into the two values that StageEngine.evaluate() needs:

    alignment_score_100 : float   — 0–100 scale; appended to the
                                    alignment_score_history list.
    env_modifier        : float   — multiplicative modifier in [0.8, 1.0]
                                    applied to the overall composite score
                                    when Schumann is disturbed or untrusted.

Design contract
---------------
* This module MUST NOT import anything from schumann.*  directly at
  module level — the Schumann layer is an optional dependency.
  SchumannState is accepted as a plain dict OR as the typed object;
  the bridge handles both via duck typing.
* When Schumann is unavailable (confidence < 0.4 or no state object),
  the bridge returns a neutral alignment_score_100 = 50.0 and
  env_modifier = 1.0  (no effect on stage scoring).
"""

from __future__ import annotations

from typing import Any, Optional


def schumann_to_alignment(
    schumann_state: Optional[Any],
) -> tuple[float, float]:
    """
    Convert a SchumannState (typed or dict) into Stage Engine inputs.

    Returns
    -------
    (alignment_score_100, env_modifier)

    alignment_score_100 : float
        Schumann alignment score scaled to 0–100.  Suitable for
        appending to StageEngine.evaluate(alignment_score_history).

    env_modifier : float in [0.8, 1.0]
        Applied to the stage composite to represent environmental
        turbulence.  1.0 = quiet / trusted; 0.8 = disturbed / unavailable.
        Stage Engine multiplies the composite by this value BEFORE
        comparing against forward thresholds.
    """
    if schumann_state is None:
        return 50.0, 1.0

    # Support both typed SchumannState objects and plain dicts (e.g. from IPC)
    if isinstance(schumann_state, dict):
        confidence      = float(schumann_state.get("confidence", 0.0))
        alignment       = float(schumann_state.get("alignment_score", 0.5))
        disturbance     = schumann_state.get("disturbance_level", "unavailable")
        is_trusted      = bool(schumann_state.get("is_trusted", confidence >= 0.4))
    else:
        # Typed SchumannState object
        confidence      = float(getattr(schumann_state, "confidence", 0.0))
        alignment       = float(getattr(schumann_state, "alignment_score", 0.5))
        disturbance_obj = getattr(schumann_state, "disturbance_level", None)
        disturbance     = disturbance_obj.value if hasattr(disturbance_obj, "value") else str(disturbance_obj)
        is_trusted      = bool(getattr(schumann_state, "is_trusted", confidence >= 0.4))

    if not is_trusted:
        return 50.0, 1.0

    alignment_score_100 = max(0.0, min(100.0, alignment * 100.0))

    # Environmental modifier based on disturbance level
    _modifier_map = {
        "stable"     : 1.00,
        "elevated"   : 0.95,
        "disturbed"  : 0.85,
        "unavailable": 1.00,   # unavailable → neutral, not penalised
    }
    env_modifier = _modifier_map.get(disturbance, 1.0)

    return alignment_score_100, env_modifier
