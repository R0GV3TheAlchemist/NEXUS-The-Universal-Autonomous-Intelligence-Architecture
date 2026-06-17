"""
gaia/core/d6_engine.py
======================
D6 Meta-Coherence Engine — Standalone Layer
Canon reference: GAIA_D6_META_COHERENCE_ENGINE.md, C52 Part II
Issues: #576, #571

This module extracts the D6 mode recommendation logic from GAIAState and
elevates it into a standalone engine with:
  - External probe support (biometrics, Noosphere load, Schumann)
  - Intervention event logging
  - Mode transition history
  - Dimensional health reporting
  - Talisman-aware mode adjustment

Design principle:
  GAIAState is the DATA layer (what is the state).
  D6Engine is the DECISION layer (what should happen given the state).
  They are cleanly separated. D6Engine reads GAIAState; it does not IS GAIAState.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from gaia.core.state import GAIAMode, GAIAState


# ---------------------------------------------------------------------------
# InterventionSeverity
# ---------------------------------------------------------------------------

class InterventionSeverity(str, Enum):
    """
    Severity levels for D6Engine intervention events.
    Used by both InterventionEvent and the frontend HUD severity ring.
    """
    INFO     = "INFO"
    WARN     = "WARN"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Probe types
# ---------------------------------------------------------------------------

@dataclass
class EngineProbes:
    """
    External signals that supplement GAIAState scalar fields.
    All values are optional — the engine degrades gracefully to
    pure GAIAState-based decisions when probes are absent.
    """
    # Biometric probes (C153 / Embodiment Layer)
    heart_rate_variability: Optional[float] = None
    sleep_quality: Optional[float] = None
    movement_today: Optional[float] = None

    # Noosphere probes (C43, #435)
    noosphere_load: Optional[float] = None
    collective_coherence: Optional[float] = None

    # Environmental probes
    schumann_coherence: Optional[float] = None
    lunar_phase_load: Optional[float] = None

    # Session probes
    session_duration_hours: Optional[float] = None
    time_since_rest_hours: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "heart_rate_variability": self.heart_rate_variability,
            "sleep_quality": self.sleep_quality,
            "movement_today": self.movement_today,
            "noosphere_load": self.noosphere_load,
            "collective_coherence": self.collective_coherence,
            "schumann_coherence": self.schumann_coherence,
            "lunar_phase_load": self.lunar_phase_load,
            "session_duration_hours": self.session_duration_hours,
            "time_since_rest_hours": self.time_since_rest_hours,
        }


# ---------------------------------------------------------------------------
# Intervention Event
# ---------------------------------------------------------------------------

@dataclass
class InterventionEvent:
    """
    Logged when D6Engine recommends a mode change or flags a concern.
    These events form the engine's decision audit trail.
    """
    t: float = field(default_factory=time.time)
    previous_mode: Optional[GAIAMode] = None
    recommended_mode: Optional[GAIAMode] = None
    trigger: str = ""
    dimensional_flags: Dict[str, bool] = field(default_factory=dict)
    probe_signals: Dict[str, Any] = field(default_factory=dict)
    severity: str = InterventionSeverity.INFO
    auto_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "t": self.t,
            "previous_mode": self.previous_mode.value if self.previous_mode else None,
            "recommended_mode": self.recommended_mode.value if self.recommended_mode else None,
            "trigger": self.trigger,
            "dimensional_flags": self.dimensional_flags,
            "probe_signals": self.probe_signals,
            "severity": self.severity,
            "auto_applied": self.auto_applied,
        }


# ---------------------------------------------------------------------------
# D6Inputs — structured input bundle for compute_next_state()
# ---------------------------------------------------------------------------

@dataclass
class D6Inputs:
    """
    Structured input bundle for the compute_next_state() functional API.

    This is the pure-function complement to D6Engine.evaluate().
    Use when you want a stateless transformation rather than a stateful engine.

    Fields:
        current_state:      The current GAIAState.
        architect_request:  True if the Architect has explicitly requested a mode.
        recent_error_rate:  Fraction of recent interactions that resulted in errors (0–1).
        session_hours:      Hours the current session has been active.
        new_data_present:   True if new canon / memory data is available for ingestion.
        threat_detected:    True if Sentinel has flagged an active threat.
        probes:             Optional EngineProbes for biometric / environmental signals.
    """
    current_state: GAIAState
    architect_request: bool = False
    recent_error_rate: Optional[float] = None
    session_hours: Optional[float] = None
    new_data_present: bool = False
    threat_detected: bool = False
    probes: Optional[EngineProbes] = None


# ---------------------------------------------------------------------------
# D6Decision — structured output bundle from compute_next_state()
# ---------------------------------------------------------------------------

@dataclass
class D6Decision:
    """
    Structured output from compute_next_state().

    Fields:
        next_state:     The (possibly updated) GAIAState after the decision.
        interventions:  List of human-readable intervention strings logged.
        rationale:      Single-sentence explanation of why this decision was made.
        severity:       InterventionSeverity level of the decision.
        mode_changed:   True if next_state.mode differs from the input state.mode.
    """
    next_state: GAIAState
    interventions: List[str] = field(default_factory=list)
    rationale: str = ""
    severity: str = InterventionSeverity.INFO
    mode_changed: bool = False


# ---------------------------------------------------------------------------
# clamp() — used by state_store and other consumers
# ---------------------------------------------------------------------------

def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp value into [min_val, max_val].
    Used extensively in GAIAStateStore field updates.

    Examples:
        >>> clamp(1.5)
        1.0
        >>> clamp(-0.1)
        0.0
        >>> clamp(0.7)
        0.7
    """
    return max(min_val, min(max_val, value))


# ---------------------------------------------------------------------------
# compute_next_state() — pure-function API
# ---------------------------------------------------------------------------

def compute_next_state(inputs: D6Inputs) -> D6Decision:
    """
    Pure-function D6 decision API.

    Constructs a temporary D6Engine, runs evaluate() with the supplied
    inputs, and returns a D6Decision without mutating global state.

    Args:
        inputs: D6Inputs bundle.

    Returns:
        D6Decision with next_state, rationale, severity, and interventions.
    """
    engine = D6Engine(auto_apply=False)
    probes = inputs.probes or EngineProbes(
        session_duration_hours=inputs.session_hours,
    )

    # Threat override: force PROTECT immediately
    if inputs.threat_detected:
        state = inputs.current_state
        interventions = ["Threat detected — Sentinel override → PROTECT mode."]
        prev_mode = state.mode
        state.update(mode=GAIAMode.PROTECT)
        return D6Decision(
            next_state=state,
            interventions=interventions,
            rationale="Sentinel threat flag — PROTECT override applied.",
            severity=InterventionSeverity.CRITICAL,
            mode_changed=prev_mode != GAIAMode.PROTECT,
        )

    # High error rate → push toward REFLECT
    if inputs.recent_error_rate is not None and inputs.recent_error_rate > 0.4:
        state = inputs.current_state
        prev_mode = state.mode
        state.update(mode=GAIAMode.REFLECT)
        return D6Decision(
            next_state=state,
            interventions=[f"Error rate {inputs.recent_error_rate:.0%} → REFLECT for recalibration."],
            rationale="High recent error rate — shifting to REFLECT.",
            severity=InterventionSeverity.WARN,
            mode_changed=prev_mode != GAIAMode.REFLECT,
        )

    # Standard D6Engine evaluation
    event = engine.evaluate(inputs.current_state, probes)
    state = inputs.current_state
    prev_mode = state.mode

    if event.recommended_mode and event.recommended_mode != state.mode:
        state.update(mode=event.recommended_mode)

    return D6Decision(
        next_state=state,
        interventions=[event.trigger] if event.trigger else [],
        rationale=event.trigger or "Mode optimal for current state.",
        severity=event.severity,
        mode_changed=prev_mode != state.mode,
    )


# ---------------------------------------------------------------------------
# D6 Meta-Coherence Engine
# ---------------------------------------------------------------------------

class D6Engine:
    """
    The D6 Meta-Coherence Engine — GAIA's operational awareness layer.

    Responsibilities:
      1. Read GAIAState + external probes
      2. Determine the correct operational mode
      3. Log intervention events with full audit trail
      4. Optionally auto-apply mode changes (configurable)
      5. Provide dimensional health report for frontend HUD

    Usage:
        engine = D6Engine(auto_apply=True)
        event = engine.evaluate(state, probes)
        report = engine.health_report(state, probes)
    """

    def __init__(
        self,
        auto_apply: bool = False,
        on_intervention: Optional[Callable[[InterventionEvent], None]] = None,
    ):
        self.auto_apply = auto_apply
        self.on_intervention = on_intervention
        self.intervention_log: List[InterventionEvent] = []

    def evaluate(
        self,
        state: GAIAState,
        probes: Optional[EngineProbes] = None,
    ) -> InterventionEvent:
        probes = probes or EngineProbes()
        flags = state.dimensional_health
        probe_override: Optional[GAIAMode] = self._probe_override(state, probes)
        base_recommendation = state.recommended_mode()
        recommended = probe_override if probe_override is not None else base_recommendation
        trigger, severity = self._explain(state, probes, flags, probe_override)

        event = InterventionEvent(
            previous_mode=state.mode,
            recommended_mode=recommended,
            trigger=trigger,
            dimensional_flags=flags,
            probe_signals={k: v for k, v in probes.to_dict().items() if v is not None},
            severity=severity,
        )

        if self.auto_apply and recommended != state.mode:
            state.update(mode=recommended)
            event.auto_applied = True

        self.intervention_log.append(event)
        if self.on_intervention:
            self.on_intervention(event)

        return event

    def _probe_override(
        self,
        state: GAIAState,
        probes: EngineProbes,
    ) -> Optional[GAIAMode]:
        if (
            probes.session_duration_hours is not None
            and probes.session_duration_hours > 6.0
            and probes.time_since_rest_hours is not None
            and probes.time_since_rest_hours > 5.0
        ):
            return GAIAMode.REST
        if probes.heart_rate_variability is not None and probes.heart_rate_variability < 0.2:
            return GAIAMode.RECOVER
        if probes.sleep_quality is not None and probes.sleep_quality < 0.25:
            return GAIAMode.RECOVER if state.energy < 0.4 else GAIAMode.REST
        if (
            probes.noosphere_load is not None
            and probes.noosphere_load > 0.8
            and state.mode not in (GAIAMode.PROTECT, GAIAMode.REST, GAIAMode.RECOVER)
        ):
            return GAIAMode.PROTECT
        if (
            probes.schumann_coherence is not None
            and probes.schumann_coherence < 0.2
            and state.mode in (GAIAMode.BUILD, GAIAMode.CREATE)
        ):
            return GAIAMode.REFLECT
        return None

    def _explain(
        self,
        state: GAIAState,
        probes: EngineProbes,
        flags: Dict[str, bool],
        probe_override: Optional[GAIAMode],
    ) -> tuple:
        if flags["D1_critical"]:
            return "D1 Physical critical — energy below 15%. REST required.", InterventionSeverity.CRITICAL
        if flags["D2_distress"] and state.energy < 0.4:
            return "D2 Emotional distress + low energy. RECOVER required.", InterventionSeverity.CRITICAL
        if flags["D2_distress"]:
            return "D2 Emotional distress. Stress above 75%. PROTECT or RECOVER.", InterventionSeverity.WARN
        if flags["D3_saturated"]:
            return "D3 Mental saturated. High entropy + low energy. Simplify or rest.", InterventionSeverity.WARN
        if probe_override == GAIAMode.REST and probes.session_duration_hours:
            return (
                f"Session active {probes.session_duration_hours:.1f}h without rest. "
                f"Human sovereignty requires recovery. (Architect Protocol #578)",
                InterventionSeverity.WARN,
            )
        if probe_override == GAIAMode.RECOVER and probes.heart_rate_variability:
            return "Low HRV detected. Physiological recovery signal.", InterventionSeverity.WARN
        if probe_override == GAIAMode.PROTECT and probes.noosphere_load:
            return (
                f"High Noosphere load ({probes.noosphere_load:.2f}). "
                "Collective field stress — boundary holding recommended.",
                InterventionSeverity.INFO,
            )
        if flags["D6_approaching"]:
            return "D6 Unity approaching. Meta-Field conditions optimal. INTEGRATE.", InterventionSeverity.INFO
        if state.mode == state.recommended_mode():
            return "Current mode is optimal for present state.", InterventionSeverity.INFO
        return "Mode recommendation based on GAIAState field analysis.", InterventionSeverity.INFO

    def health_report(
        self,
        state: GAIAState,
        probes: Optional[EngineProbes] = None,
    ) -> Dict[str, Any]:
        probes = probes or EngineProbes()
        event = self.evaluate(state, probes)
        return {
            "state": state.to_dict(include_history=False),
            "dimensional_health": state.dimensional_health,
            "priority_dimension": state.priority_dimension,
            "current_mode": state.mode.value,
            "recommended_mode": event.recommended_mode.value if event.recommended_mode else None,
            "mode_is_optimal": state.mode == event.recommended_mode,
            "latest_intervention": event.to_dict(),
            "intervention_count": len(self.intervention_log),
            "probe_signals": probes.to_dict(),
            "report_time": time.time(),
        }

    def recent_interventions(self, n: int = 10) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.intervention_log[-n:]]

    def critical_interventions(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.intervention_log if e.severity == InterventionSeverity.CRITICAL]
