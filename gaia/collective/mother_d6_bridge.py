"""
gaia.collective.mother_d6_bridge
================================
Wire 3 — MotherThread → EngineProbes → D6Engine → HUD
Issue #589, Phase 1

This module is the translation layer between the collective field world
(MotherThread / CollectiveField / MotherPulse) and the cognitive state
world (D6Engine / EngineProbes).

Where Wire 2 feeds D6 from physical sensors (biometric, body-level),
Wire 3 feeds D6 from the collective field (planetary, relational).
Together they complete the full probe picture:

  Wire 2: heart_rate_variability, movement_today, noosphere_load (physical)
  Wire 3: collective_coherence, schumann_coherence, session_duration_hours,
          noosphere_load (collective blend)

Responsibilities
----------------
1.  Subscribe to MotherThread via get_mother_thread().subscribe().
2.  On every MotherPulse, extract CollectiveField values.
3.  Translate into EngineProbes fields.
4.  Call D6Engine.evaluate(state, probes) → fires on_intervention (Wire 1).

Signal Mapping  (MotherThread → EngineProbes)
----------------------------------------------
  CollectiveField.collective_phi
      → collective_coherence  [0,1]
        High collective_phi = high resonance = supportive field.
        D6Engine uses this to modulate REST vs FLOW recommendations.

  schumann_aligned_count / consenting_gaians
      → schumann_coherence  [0,1]
        Fraction of consenting Gaians Schumann-aligned.
        0 when no consenting Gaians (no field yet).

  avg_noosphere_health  (from CollectiveField)
      → noosphere_load  (inverted: high health = low load)
        Blended with Wire 2's physical noosphere_load if available.

  pulse.sequence × PULSE_INTERVAL_SECONDS / 3600
      → session_duration_hours
        Approximates session age from pulse count.
        Precise session tracking (Wire 4) will replace this.

Canon refs: C04, C43, C44, C47
Issues: #589 (Wire 3), #261 (MotherThread v2), #576 (state router)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from core.mother_thread import (
    PULSE_INTERVAL_SECONDS,
    CollectiveField,
    MotherThread,
    get_mother_thread,
)
from gaia.core.d6_engine import D6Engine, EngineProbes, InterventionEvent
from gaia.core.state import GAIAState

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

@dataclass
class MotherProbeResult:
    """
    Intermediate result from a single MotherThread pulse translation.
    Carries the translated probes and collective field metadata.
    """
    probes: EngineProbes
    pulse_sequence: int             = 0
    consenting_gaians: int          = 0
    collective_phi: float           = 0.0
    schumann_ratio: float           = 0.0
    field_coherence_label: str      = "dormant"
    noosphere_stage: str            = "Geosphere"
    timestamp: float                = field(default_factory=time.time)


def translate_pulse_to_probes(
    pulse_dict: Dict[str, Any],
    wire2_noosphere_load: Optional[float] = None,
) -> MotherProbeResult:
    """
    Core Wire 3 translation function.

    Takes a MotherPulse dict (from MotherThread.subscribe() or
    MotherThread._beat().to_dict()) and maps its CollectiveField
    values to the appropriate EngineProbes slots.

    Parameters
    ----------
    pulse_dict:
        MotherPulse.to_dict() output.
    wire2_noosphere_load:
        Optional noosphere_load value from Wire 2 (physical sensors).
        When provided, Wire 3's collective noosphere load is blended with
        Wire 2's value using a 60/40 physical/collective weight.
        This prevents double-counting while preserving both signals.

    Returns
    -------
    MotherProbeResult with translated EngineProbes and pulse metadata.
    """
    cf: Dict[str, Any] = pulse_dict.get("collective_field", {})
    sequence: int = pulse_dict.get("sequence", 0)

    # ——— collective_coherence ← collective_phi ——————————————————————————
    collective_phi: float = float(cf.get("collective_phi", 0.0))
    collective_coherence: float = round(min(1.0, max(0.0, collective_phi)), 3)

    # ——— schumann_coherence ← schumann_aligned_count / consenting_gaians ———
    consenting: int = int(cf.get("consenting_gaians", 0))
    schumann_count: int = int(cf.get("schumann_aligned_count", 0))
    schumann_ratio: float = round(schumann_count / consenting, 3) if consenting > 0 else 0.0
    schumann_coherence: float = schumann_ratio

    # ——— noosphere_load ← 1.0 - avg_noosphere_health ———————————————————
    #   High collective noosphere_health → low load (supportive field)
    avg_noosphere_health: float = float(cf.get("avg_noosphere_health", 0.5))
    collective_noosphere_load: float = round(1.0 - avg_noosphere_health, 3)

    # Blend Wire 2 (physical) and Wire 3 (collective) noosphere loads
    # Weight: 60% physical (Wire 2), 40% collective (Wire 3)
    # Rationale: physical sensor data is more immediately actionable.
    if wire2_noosphere_load is not None:
        blended_noosphere = round(
            0.60 * wire2_noosphere_load + 0.40 * collective_noosphere_load, 3
        )
    else:
        blended_noosphere = collective_noosphere_load

    # ——— session_duration_hours ← pulse.sequence × PULSE_INTERVAL_SECONDS ———
    #   Each pulse represents PULSE_INTERVAL_SECONDS of session time.
    #   Wire 4 (session tracking) will replace this with exact session clock.
    session_seconds: float = sequence * PULSE_INTERVAL_SECONDS
    session_duration_hours: float = round(session_seconds / 3600.0, 4)

    probes = EngineProbes(
        collective_coherence   = collective_coherence,
        schumann_coherence     = schumann_coherence,
        noosphere_load         = blended_noosphere,
        session_duration_hours = session_duration_hours,
        # Wire 2 fields (heart_rate_variability, movement_today) are not
        # populated here — they come from ESBtoD6Bridge. D6Engine merges
        # probes from multiple sources via evaluate(); the last write wins
        # for each field, so Wire 2 and Wire 3 compose cleanly.
    )

    return MotherProbeResult(
        probes                = probes,
        pulse_sequence        = sequence,
        consenting_gaians     = consenting,
        collective_phi        = collective_phi,
        schumann_ratio        = schumann_ratio,
        field_coherence_label = str(cf.get("field_coherence_label", "dormant")),
        noosphere_stage       = str(cf.get("noosphere_stage", "Geosphere")),
    )


# ---------------------------------------------------------------------------
# MotherToD6Bridge — async subscriber
# ---------------------------------------------------------------------------

class MotherToD6Bridge:
    """
    Wire 3 — async subscriber that listens to MotherThread pulse events
    and feeds translated EngineProbes into D6Engine.

    Usage
    -----
    ::

        bridge = MotherToD6Bridge(
            mother=get_mother_thread(),
            engine=d6_engine,
            state=gaia_state,
        )
        # In an async context (FastAPI lifespan or pytest-asyncio):
        task = asyncio.create_task(bridge.run())
        # To stop:
        bridge.stop()
        await task

    Wire 3 → Wire 1 signal path
    ----------------------------
        MotherThread._beat()
            → MotherPulse broadcast
            → MotherToD6Bridge.run() receives pulse dict
            → translate_pulse_to_probes()
            → D6Engine.evaluate(state, probes)
            → on_intervention(event)           ← Wire 1
            → WebSocket broadcast              ← HUD receives INTERVENTION_EVENT

    Wire 2 + Wire 3 composition
    ---------------------------
    Wire 2 runs in its own background thread (ESBtoD6Bridge).
    Wire 3 runs in the asyncio event loop (MotherToD6Bridge).
    They both call D6Engine.evaluate() independently on their own schedules.
    D6Engine is stateless per evaluate() call — each call is independent.
    The two wires compose at the EngineProbes level via the
    wire2_noosphere_load blend parameter.

    Issue #589, Phase 1, Wire 3.
    """

    def __init__(
        self,
        mother: MotherThread,
        engine: D6Engine,
        state: GAIAState,
        wire2_noosphere_source: Optional[object] = None,
        on_probe_ready: Optional[object] = None,
    ) -> None:
        """
        Parameters
        ----------
        mother:
            The live MotherThread singleton.
        engine:
            The D6Engine singleton — must have on_intervention wired (Wire 1).
        state:
            The GAIAState singleton that D6Engine evaluates against.
        wire2_noosphere_source:
            Optional callable() → float that returns the most recent
            noosphere_load from Wire 2 (ESBtoD6Bridge.last_result).
            When provided, Wire 3 blends the physical and collective
            noosphere signals per the 60/40 weighting.
        on_probe_ready:
            Optional callback(MotherProbeResult) for observability / testing.
        """
        self._mother       = mother
        self._engine       = engine
        self._state        = state
        self._wire2_source = wire2_noosphere_source
        self._on_probe     = on_probe_ready
        self._stop         = False
        self._cycle_count  = 0
        self._error_count  = 0
        self._last_result: Optional[MotherProbeResult] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Signal the subscriber loop to exit on next pulse."""
        self._stop = True

    @property
    def is_running(self) -> bool:
        return not self._stop

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def last_result(self) -> Optional[MotherProbeResult]:
        return self._last_result

    # ------------------------------------------------------------------
    # Core: single pulse evaluation
    # ------------------------------------------------------------------

    def process_pulse(self, pulse_dict: Dict[str, Any]) -> tuple[MotherProbeResult, InterventionEvent]:
        """
        Process a single MotherPulse dict → translate → D6 evaluate.

        Exposed as a public synchronous method so tests can call it
        directly without needing a running asyncio event loop or a
        live MotherThread pulse subscription.

        Returns
        -------
        (MotherProbeResult, InterventionEvent)
        """
        # Optionally blend Wire 2 noosphere load
        wire2_noosphere: Optional[float] = None
        if self._wire2_source is not None:
            try:
                wire2_noosphere = self._wire2_source()
            except Exception:
                pass

        probe_result = translate_pulse_to_probes(
            pulse_dict,
            wire2_noosphere_load=wire2_noosphere,
        )

        if self._on_probe is not None:
            try:
                self._on_probe(probe_result)
            except Exception:  # noqa: BLE001
                pass

        event = self._engine.evaluate(self._state, probe_result.probes)
        self._last_result = probe_result
        self._cycle_count += 1

        log.debug(
            "Wire 3 cycle %d: seq=%d phi=%.3f schumann=%.3f "
            "noosphere=%.3f session=%.2fh → D6 severity=%s",
            self._cycle_count,
            probe_result.pulse_sequence,
            probe_result.collective_phi,
            probe_result.schumann_ratio,
            probe_result.probes.noosphere_load or 0.0,
            probe_result.probes.session_duration_hours or 0.0,
            event.severity,
        )
        return probe_result, event

    # ------------------------------------------------------------------
    # Async subscription loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """
        Subscribe to MotherThread and process every pulse until stop() is called.

        This is the live production entry point. Call as an asyncio Task:
            asyncio.create_task(bridge.run())
        """
        log.info("Wire 3 started — MotherToD6Bridge subscribing to MotherThread")
        try:
            async for pulse_dict in self._mother.subscribe():
                if self._stop:
                    break
                try:
                    self.process_pulse(pulse_dict)
                except Exception as exc:  # noqa: BLE001
                    self._error_count += 1
                    log.error(
                        "Wire 3 pulse error (cycle %d): %s",
                        self._cycle_count, exc,
                        exc_info=True,
                    )
        except asyncio.CancelledError:
            pass
        finally:
            log.info(
                "Wire 3 stopped — %d cycles, %d errors",
                self._cycle_count, self._error_count,
            )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_wire3(
    engine: D6Engine,
    state: GAIAState,
    wire2_noosphere_source: Optional[object] = None,
    mother: Optional[MotherThread] = None,
) -> MotherToD6Bridge:
    """
    Factory function. Uses the module-level MotherThread singleton unless
    a specific instance is provided.

    Wire up all three wires in main.py with:

        w3 = create_wire3(engine=_engine, state=_state,
                          wire2_noosphere_source=lambda: (
                              _esb_bridge.last_result.probes.noosphere_load
                              if _esb_bridge.last_result else None
                          ))
        asyncio.create_task(w3.run())
    """
    return MotherToD6Bridge(
        mother=mother or get_mother_thread(),
        engine=engine,
        state=state,
        wire2_noosphere_source=wire2_noosphere_source,
    )
