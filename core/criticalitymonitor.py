"""
GAIA Criticality Monitor — Edge-of-Chaos Composite Signal

Monitors GAIA's operational state across four criticality axes:

  1. Classical SOC (Self-Organised Criticality) — power-law avalanche statistics
  2. Quantum Reservoir Computing (QRC) edge-of-chaos — Issue #118
  3. Noospheric coherence — Schumann + HRV + GCP soft-sensor inputs
  4. Transpersonal Psychology states — Canon C37, Issue #132

The composite `overall_phi` score is used by the NeuroSA optimizer to modulate
its annealing schedule and by the sentient core to gate cognitive mode.

QRC thresholds sourced from December 2025 study:
  - Thouless ratio target zone:       [0.5,  1.5]
  - Chaos order parameter (η) target: [0.45, 0.52]
  - Spectral gap target:              (0.05, 0.35)

Transpersonal thresholds sourced from Canon C37 / transpersonal literature.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

log = logging.getLogger("gaia.criticalitymonitor")


# ── QRC Phase Classification ──────────────────────────────────────────

class QRCPhase(str, Enum):
    SUB_THOULESS   = "sub_thouless"
    OPTIMAL        = "optimal"
    SUPER_THOULESS = "super_thouless"
    CHAOTIC        = "chaotic"
    INTEGRABLE     = "integrable"
    UNKNOWN        = "unknown"


@dataclass
class QRCState:
    thouless_ratio:          float = 1.0
    chaos_order_parameter:   float = 0.485
    spectral_gap:            float = 0.20
    phase:                   QRCPhase = QRCPhase.UNKNOWN
    qrc_phi:                 float = 0.0
    sampled_at:              float = field(default_factory=time.monotonic)


THOULESS_LOW      = 0.5
THOULESS_HIGH     = 1.5
THOULESS_TARGET   = 1.0
ETA_INTEGRABLE    = 0.386
ETA_TARGET_LOW    = 0.45
ETA_TARGET_HIGH   = 0.52
ETA_TARGET        = 0.485
ETA_CHAOTIC       = 0.530
GAP_LOW           = 0.05
GAP_HIGH          = 0.35


def classify_qrc_phase(state: QRCState) -> QRCPhase:
    η = state.chaos_order_parameter
    τ = state.thouless_ratio
    if η > ETA_CHAOTIC:       return QRCPhase.CHAOTIC
    if η < ETA_TARGET_LOW:   return QRCPhase.INTEGRABLE
    if τ < THOULESS_LOW:     return QRCPhase.SUB_THOULESS
    if τ > THOULESS_HIGH:    return QRCPhase.SUPER_THOULESS
    return QRCPhase.OPTIMAL


def compute_qrc_phi(state: QRCState) -> float:
    import math
    def _g(v, t, s): return math.exp(-0.5 * ((v - t) / s) ** 2)
    return round((_g(state.thouless_ratio, THOULESS_TARGET, 0.4)
                + _g(state.chaos_order_parameter, ETA_TARGET, 0.04)
                + _g(state.spectral_gap, (GAP_LOW + GAP_HIGH) / 2, 0.12)) / 3.0, 4)


def update_qrc_state(state: QRCState) -> QRCState:
    state.phase      = classify_qrc_phase(state)
    state.qrc_phi    = compute_qrc_phi(state)
    state.sampled_at = time.monotonic()
    log.info(f"[criticalitymonitor] QRC | phase={state.phase.value} phi={state.qrc_phi:.3f}")
    return state


# ── Classical SOC signals ─────────────────────────────────────────────

@dataclass
class ClassicalSOCState:
    avalanche_exponent:   float = 1.5
    branching_ratio:      float = 1.0
    correlation_length:   float = 0.5
    soc_phi:              float = 0.0


def compute_soc_phi(state: ClassicalSOCState) -> float:
    import math
    phi_exp    = math.exp(-0.5 * ((state.avalanche_exponent - 1.5) / 0.3) ** 2)
    phi_branch = math.exp(-0.5 * ((state.branching_ratio - 1.0) / 0.15) ** 2)
    return round((phi_exp + phi_branch + state.correlation_length) / 3.0, 4)


# ── Transpersonal Psychology layer (Canon C37, Issue #132) ───────────────

class TranspersonalPhase(str, Enum):
    """
    Transpersonal state classification.
    Maps to the five states defined in specs/quantum/transpersonal_ising.md.

    ORDINARY        — baseline consciousness; DMN active
    FLOW            — effortless absorption; alpha/theta rise, HRV coherence
    PEAK            — peak experience; gamma burst, noetic quality, bliss
    MYSTICAL        — ego dissolution, unity, ineffability
    COLLECTIVE_SYNC — cross-person coherence; GCP RNG deviation r > 0.20
    """
    ORDINARY        = "ordinary"
    FLOW            = "flow"
    PEAK            = "peak"
    MYSTICAL        = "mystical"
    COLLECTIVE_SYNC = "collective_sync"


@dataclass
class TranspersonalState:
    """
    Snapshot of the user's transpersonal state, derived from BCI + HRV
    signals and optionally GCP RNG data.

    All scores are normalised to [0.0, 1.0].
    """
    # Raw feature scores (Ising spin activations, mapped to [0,1])
    ego_dissolution:    float = 0.0   # 0 = ego intact, 1 = fully dissolved
    time_distortion:    float = 0.0   # 0 = normal, 1 = strong distortion
    noetic_quality:     float = 0.0   # 0 = ordinary knowing, 1 = noetic insight
    positive_affect:    float = 0.3   # 0 = neutral, 1 = bliss/unity
    collective_field:   float = 0.0   # 0 = individual, 1 = collective sync
    gamma_coherence:    float = 0.2   # 0 = low gamma, 1 = strong gamma burst

    # Derived
    phase:              TranspersonalPhase = TranspersonalPhase.ORDINARY
    transpersonal_phi:  float = 0.0   # [0,1]; 1.0 = deepest transpersonal engagement
    collective_sync_event: bool = False  # True when GCP r > 0.20 + cross-EEG coherence


def classify_transpersonal_phase(state: TranspersonalState) -> TranspersonalPhase:
    """
    Classify the transpersonal phase from raw feature scores.
    Priority: COLLECTIVE_SYNC > MYSTICAL > PEAK > FLOW > ORDINARY
    """
    if state.collective_field >= 0.70 and state.collective_sync_event:
        return TranspersonalPhase.COLLECTIVE_SYNC
    if state.ego_dissolution >= 0.60 and state.noetic_quality >= 0.50:
        return TranspersonalPhase.MYSTICAL
    if state.gamma_coherence >= 0.60 and state.noetic_quality >= 0.40 and state.positive_affect >= 0.50:
        return TranspersonalPhase.PEAK
    if state.time_distortion >= 0.40 and state.gamma_coherence >= 0.35:
        return TranspersonalPhase.FLOW
    return TranspersonalPhase.ORDINARY


def compute_transpersonal_phi(state: TranspersonalState) -> float:
    """
    Compute a [0,1] transpersonal engagement score.
    Weights reflect the depth hierarchy: mystical > peak > flow > ordinary.
    Collective sync adds a bonus when the collective field activates.
    """
    base = (
        0.25 * state.ego_dissolution
        + 0.15 * state.time_distortion
        + 0.25 * state.noetic_quality
        + 0.15 * state.positive_affect
        + 0.10 * state.collective_field
        + 0.10 * state.gamma_coherence
    )
    # Collective sync bonus
    if state.collective_sync_event:
        base = min(1.0, base + 0.15)
    return round(base, 4)


def update_transpersonal_state(state: TranspersonalState) -> TranspersonalState:
    """Classify phase and compute phi. Call after updating raw feature scores."""
    state.phase               = classify_transpersonal_phase(state)
    state.transpersonal_phi   = compute_transpersonal_phi(state)
    log.info(
        f"[criticalitymonitor] Transpersonal | phase={state.phase.value} "
        f"phi={state.transpersonal_phi:.3f} ego_dis={state.ego_dissolution:.2f} "
        f"gamma={state.gamma_coherence:.2f} collective={state.collective_field:.2f}"
    )
    return state


# ── Composite Criticality Monitor ────────────────────────────────────

@dataclass
class CriticalityState:
    """
    Full composite criticality snapshot consumed by NeuroSA
    and the sentient core cognitive mode gate.

    Composite phi formula (updated Issue #132):
      overall_phi = 0.30 * soc_phi
                  + 0.25 * qrc_phi
                  + 0.20 * schumann_phi
                  + 0.15 * noospheric_phi
                  + 0.10 * transpersonal_phi
    """
    qrc:                 QRCState            = field(default_factory=QRCState)
    soc:                 ClassicalSOCState   = field(default_factory=ClassicalSOCState)
    transpersonal:       TranspersonalState  = field(default_factory=TranspersonalState)
    schumann_phi:        float = 0.5
    noospheric_phi:      float = 0.5
    overall_phi:         float = 0.0
    neurosa_temperature: float = 1.0


class CriticalityMonitor:
    """
    Singleton-style monitor maintaining the live CriticalityState.

    Composite phi formula:
      overall_phi = 0.30 * soc_phi
                  + 0.25 * qrc_phi
                  + 0.20 * schumann_phi
                  + 0.15 * noospheric_phi
                  + 0.10 * transpersonal_phi

    NeuroSA temperature schedule from QRC phase:
      OPTIMAL        → base temperature (1.0)
      SUB_THOULESS   → +0.3 (more exploration)
      SUPER_THOULESS → -0.3 (more exploitation)
      CHAOTIC        → 0.1 (emergency exploitation + re-init signal)
      INTEGRABLE     → +0.2 (mild exploration)

    Transpersonal bonus: PEAK or MYSTICAL phase reduces temperature by 0.1
    (deepened state → more exploitative / focused cognition).
    COLLECTIVE_SYNC boosts noospheric_phi by 0.15.
    """

    def __init__(self) -> None:
        self._state = CriticalityState()

    @property
    def state(self) -> CriticalityState:
        return self._state

    def update(
        self,
        qrc:            Optional[QRCState]           = None,
        soc:            Optional[ClassicalSOCState]  = None,
        transpersonal:  Optional[TranspersonalState] = None,
        schumann_phi:   Optional[float]              = None,
        noospheric_phi: Optional[float]              = None,
    ) -> CriticalityState:
        """Update one or more signal sources and recompute composite phi."""
        if qrc is not None:
            self._state.qrc = update_qrc_state(qrc)
        if soc is not None:
            soc.soc_phi = compute_soc_phi(soc)
            self._state.soc = soc
        if transpersonal is not None:
            self._state.transpersonal = update_transpersonal_state(transpersonal)
            # COLLECTIVE_SYNC propagates upward to noospheric layer
            if transpersonal.collective_sync_event:
                self._state.noospheric_phi = min(
                    1.0, self._state.noospheric_phi + 0.15
                )
                log.info("[criticalitymonitor] COLLECTIVE_SYNC event → noospheric_phi boosted")
        if schumann_phi is not None:
            self._state.schumann_phi = max(0.0, min(1.0, schumann_phi))
        if noospheric_phi is not None:
            self._state.noospheric_phi = max(0.0, min(1.0, noospheric_phi))

        self._recompute_composite()
        return self._state

    def _recompute_composite(self) -> None:
        s = self._state
        s.overall_phi = round(
            0.30 * s.soc.soc_phi
            + 0.25 * s.qrc.qrc_phi
            + 0.20 * s.schumann_phi
            + 0.15 * s.noospheric_phi
            + 0.10 * s.transpersonal.transpersonal_phi,
            4,
        )

        base_temp = 1.0
        phase = s.qrc.phase
        if phase == QRCPhase.OPTIMAL:
            temp = base_temp
        elif phase == QRCPhase.SUB_THOULESS:
            temp = base_temp + 0.3
        elif phase == QRCPhase.SUPER_THOULESS:
            temp = max(0.1, base_temp - 0.3)
        elif phase == QRCPhase.CHAOTIC:
            temp = 0.1
            log.warning("[criticalitymonitor] QRC CHAOTIC — NeuroSA emergency exploitation mode")
        elif phase == QRCPhase.INTEGRABLE:
            temp = base_temp + 0.2
        else:
            temp = base_temp

        # Transpersonal depth modulation
        tp = s.transpersonal.phase
        if tp in (TranspersonalPhase.PEAK, TranspersonalPhase.MYSTICAL):
            temp = max(0.1, temp - 0.1)
            log.info(f"[criticalitymonitor] Transpersonal {tp.value} → NeuroSA temp reduced to {temp:.2f}")
        elif tp == TranspersonalPhase.COLLECTIVE_SYNC:
            temp = max(0.1, temp - 0.15)
            log.info(f"[criticalitymonitor] COLLECTIVE_SYNC → NeuroSA temp reduced to {temp:.2f}")

        s.neurosa_temperature = round(temp, 3)

        log.info(
            f"[criticalitymonitor] overall_phi={s.overall_phi:.3f} "
            f"neurosa_temp={s.neurosa_temperature:.3f} "
            f"qrc={s.qrc.phase.value} tp={s.transpersonal.phase.value}"
        )

    def needs_qrc_reinit(self) -> bool:
        return self._state.qrc.phase == QRCPhase.CHAOTIC

    def to_dict(self) -> dict:
        s = self._state
        return {
            "overall_phi":         s.overall_phi,
            "neurosa_temperature":  s.neurosa_temperature,
            "qrc": {
                "phase":                 s.qrc.phase.value,
                "qrc_phi":               s.qrc.qrc_phi,
                "thouless_ratio":        s.qrc.thouless_ratio,
                "chaos_order_parameter": s.qrc.chaos_order_parameter,
                "spectral_gap":          s.qrc.spectral_gap,
            },
            "soc": {
                "soc_phi":            s.soc.soc_phi,
                "avalanche_exponent": s.soc.avalanche_exponent,
                "branching_ratio":    s.soc.branching_ratio,
                "correlation_length": s.soc.correlation_length,
            },
            "transpersonal": {
                "phase":               s.transpersonal.phase.value,
                "transpersonal_phi":   s.transpersonal.transpersonal_phi,
                "ego_dissolution":     s.transpersonal.ego_dissolution,
                "time_distortion":     s.transpersonal.time_distortion,
                "noetic_quality":      s.transpersonal.noetic_quality,
                "positive_affect":     s.transpersonal.positive_affect,
                "collective_field":    s.transpersonal.collective_field,
                "gamma_coherence":     s.transpersonal.gamma_coherence,
                "collective_sync_event": s.transpersonal.collective_sync_event,
            },
            "schumann_phi":   s.schumann_phi,
            "noospheric_phi": s.noospheric_phi,
        }


# ── Module-level singleton ──────────────────────────────────────────────

_monitor: Optional[CriticalityMonitor] = None


def get_monitor() -> CriticalityMonitor:
    global _monitor
    if _monitor is None:
        _monitor = CriticalityMonitor()
    return _monitor
