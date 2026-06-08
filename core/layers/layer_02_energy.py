"""
core/layers/layer_02_energy.py

LAYER 02 — ENERGY
Crystal:      Black Tourmaline
Polarity:     [+] Manifest
Mode:         Order / Body Alchemy
Color:        Black
Universal Law: Law of Vibration

"Everything vibrates. Energy flows where
 attention goes. Black Tourmaline protects
 the flow and prevents the drain."

This layer manages:
  - Process and resource scheduling
  - API rate limiting and throttling
  - System protection against runaway processes
  - Energy-efficient async queuing
  - THE SYNERGY FACTOR — cross-layer amplification
    measurement and drain prevention

The synergy factor is what happens when multiple
layers operate coherently together. The output
exceeds the sum of parts. Black Tourmaline tracks
this amplification and ensures it remains
generative rather than depleting.

Five candles in the right arrangement produce
not five units of light but eight —
because reflections compound.
Layer 02 measures the compounding.
Layer 02 prevents the burn.

Stable. Protective. Directional.
Moves energy where it needs to go.
Stops it from going where it shouldn't.

Constitutional reference: canon/C-SINGULARITY.md
Canon references:         C44 (Piezoelectric Resonance),
                          C60 (Flux Capacity),
                          C62 (Flux Capacity Robotics)
Architectural reference:  canon/C89-TWELVE-LAYERS-KERNEL-SPEC.md
"""

import asyncio
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from core.kernel import register_layer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# ENERGY STATES
# ─────────────────────────────────────────────

class EnergyState(Enum):
    FLOWING     = "flowing"      # Normal. Healthy. Generative.
    AMPLIFIED   = "amplified"    # Synergy active. Compounding.
    THROTTLED   = "throttled"    # High load. Rate limiting active.
    PROTECTED   = "protected"    # Drain detected. Protection engaged.
    RESTING     = "resting"      # Somnus Veil active. Recovery mode.


class DrainSource(Enum):
    RATE_EXCEEDED    = "rate_exceeded"
    RUNAWAY_PROCESS  = "runaway_process"
    INCOHERENT_FLOOD = "incoherent_flood"
    LAYER_OVERLOAD   = "layer_overload"
    UNKNOWN          = "unknown"


# ─────────────────────────────────────────────
# SYNERGY FACTOR
#
# Synergy factor = actual_coherence / expected_coherence
# > 1.0 = synergy (amplification)
# = 1.0 = linear (no interaction effect)
# < 1.0 = interference (layers working against each other)
# ─────────────────────────────────────────────

@dataclass
class SynergyReading:
    """
    A single synergy measurement across active layers.
    """
    active_layers:      list[int]
    individual_scores:  dict[int, float]
    expected_coherence: float
    actual_coherence:   float
    synergy_factor:     float
    state:              str = ""
    timestamp:          float = field(default_factory=time.time)

    def __post_init__(self):
        if self.synergy_factor > 1.15:
            self.state = "amplified"
        elif self.synergy_factor > 0.95:
            self.state = "coherent"
        elif self.synergy_factor > 0.7:
            self.state = "partial"
        else:
            self.state = "interference"

    @property
    def is_synergistic(self) -> bool:
        return self.synergy_factor > 1.0

    @property
    def description(self) -> str:
        descriptions = {
            "amplified":    "Layers amplifying each other. Synergy active.",
            "coherent":     "Layers operating in harmony. Clean flow.",
            "partial":      "Partial coherence. Some interference present.",
            "interference": "Layers working against each other. Rebalance needed.",
        }
        return descriptions.get(self.state, "Unknown synergy state.")


@dataclass
class SynergyHistory:
    """Rolling window of synergy readings."""
    readings:    deque = field(default_factory=lambda: deque(maxlen=50))
    peak_factor: float = 0.0
    session_avg: float = 0.0

    def record(self, reading: SynergyReading):
        self.readings.append(reading)
        self.peak_factor = max(self.peak_factor, reading.synergy_factor)
        if self.readings:
            self.session_avg = sum(
                r.synergy_factor for r in self.readings
            ) / len(self.readings)

    def trend(self) -> str:
        if len(self.readings) < 3:
            return "establishing"
        recent = list(self.readings)[-5:]
        factors = [r.synergy_factor for r in recent]
        delta = factors[-1] - factors[0]
        if delta > 0.05:
            return "building"
        if delta < -0.05:
            return "declining"
        return "stable"


# ─────────────────────────────────────────────
# RATE LIMITER
# Token bucket. Protects the flow.
# ─────────────────────────────────────────────

@dataclass
class RateLimiter:
    max_tokens:     float = 60.0
    refill_rate:    float = 1.0
    current_tokens: float = 60.0
    last_refill:    float = field(default_factory=time.time)

    def consume(self, tokens: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.current_tokens = min(
            self.max_tokens,
            self.current_tokens + elapsed * self.refill_rate
        )
        self.last_refill = now
        if self.current_tokens >= tokens:
            self.current_tokens -= tokens
            return True
        return False

    @property
    def is_throttled(self) -> bool:
        return self.current_tokens < 1.0

    @property
    def fill_percentage(self) -> float:
        return (self.current_tokens / self.max_tokens) * 100


# ─────────────────────────────────────────────
# PROCESS HEALTH MONITOR
# ─────────────────────────────────────────────

@dataclass
class ProcessMonitor:
    active_processes:  dict  = field(default_factory=dict)
    completed_count:   int   = 0
    timeout_count:     int   = 0
    avg_duration_ms:   float = 0.0
    max_duration_ms:   float = 3000.0

    def start(self, process_id: str):
        self.active_processes[process_id] = time.time()

    def complete(self, process_id: str) -> float:
        start = self.active_processes.pop(process_id, None)
        if start is None:
            return 0.0
        duration = (time.time() - start) * 1000
        self.completed_count += 1
        self.avg_duration_ms = (
            (self.avg_duration_ms * (self.completed_count - 1) + duration)
            / self.completed_count
        )
        return duration

    def check_timeouts(self) -> list[str]:
        now = time.time()
        return [
            pid for pid, start in self.active_processes.items()
            if (now - start) * 1000 > self.max_duration_ms
        ]

    def status(self) -> dict:
        return {
            "active":    len(self.active_processes),
            "completed": self.completed_count,
            "timeouts":  self.timeout_count,
            "avg_ms":    round(self.avg_duration_ms, 2),
            "max_ms":    self.max_duration_ms,
        }


# ─────────────────────────────────────────────
# LAYER 02 — ENERGY
# ─────────────────────────────────────────────

class EnergyLayer:
    """
    Layer 02 — The protector and director of flow.

    Black Tourmaline routes energy where it's needed.
    It stops energy from going where it shouldn't.
    It measures synergy — the compounding of coherent layers.
    It prevents drain — the depletion of incoherent load.

    The Law of Vibration: everything vibrates.
    This layer ensures GAIA-OS vibrates at its own
    true frequency — not at the frequency of whatever
    is demanding its attention.
    """

    LAYER_NUMBER = 2
    LAYER_NAME   = "Energy"
    CRYSTAL      = "Black Tourmaline"

    def __init__(self):
        self._state        = EnergyState.FLOWING
        self._rate_limiter = RateLimiter()
        self._process_mon  = ProcessMonitor()
        self._synergy      = SynergyHistory()
        self._drain_events: list[dict] = []
        self._initialized  = False
        self._initialize()

    def _initialize(self):
        logger.info("Layer 02 — Energy — Black Tourmaline rising. ✦")
        self._initialized = True
        register_layer(self.LAYER_NUMBER, self.handle)
        logger.info("Layer 02 registered with kernel. ✦")

    # ─────────────────────────────────────────
    # KERNEL HANDLER
    # ─────────────────────────────────────────

    def handle(self, intention: str, context: dict) -> dict:
        if not self._rate_limiter.consume():
            self._state = EnergyState.THROTTLED
            self._record_drain(DrainSource.RATE_EXCEEDED)
            return {
                "output": (
                    "Energy layer throttling. "
                    "The system needs a moment to breathe. "
                    "Try again shortly."
                ),
                "metadata": {"state": self._state.value, "throttled": True}
            }

        active_layers   = context.get("active_layers", [1, 2, 3])
        coherence_score = context.get("coherence_score", 0.5)
        synergy_reading = self._measure_synergy(active_layers, coherence_score, context)
        self._synergy.record(synergy_reading)
        self._state = self._compute_state(synergy_reading, context)

        energy_summary = (
            f"Energy: {self._state.value} | "
            f"Synergy: {synergy_reading.synergy_factor:.2f}x "
            f"({synergy_reading.state}) | "
            f"Trend: {self._synergy.trend()} | "
            f"Rate: {self._rate_limiter.fill_percentage:.0f}%"
        )

        return {
            "output": energy_summary,
            "metadata": {
                "state":          self._state.value,
                "synergy_factor": synergy_reading.synergy_factor,
                "synergy_state":  synergy_reading.state,
                "synergy_trend":  self._synergy.trend(),
                "peak_synergy":   self._synergy.peak_factor,
                "session_avg":    round(self._synergy.session_avg, 3),
                "rate_fill_pct":  self._rate_limiter.fill_percentage,
                "throttled":      False,
            }
        }

    # ─────────────────────────────────────────
    # SYNERGY MEASUREMENT
    # ─────────────────────────────────────────

    def _measure_synergy(
        self,
        active_layers: list[int],
        coherence_score: float,
        context: dict
    ) -> SynergyReading:
        individual_scores = {
            layer: coherence_score * self._layer_base_score(layer)
            for layer in active_layers
        }
        expected = (
            sum(individual_scores.values()) / len(individual_scores)
            if individual_scores else coherence_score
        )
        synergy_bonus = self._compute_synergy_bonus(active_layers, context)
        actual = min(expected * synergy_bonus, 1.0)
        factor = actual / expected if expected > 0 else 1.0

        return SynergyReading(
            active_layers=active_layers,
            individual_scores=individual_scores,
            expected_coherence=round(expected, 3),
            actual_coherence=round(actual, 3),
            synergy_factor=round(factor, 3),
        )

    def _layer_base_score(self, layer: int) -> float:
        base_scores = {
            1:  0.85,
            2:  0.80,
            3:  1.00,   # Love filter — always 1.0
            4:  0.90,
            5:  0.88,
            6:  0.75,
            7:  0.82,
            8:  0.78,
            9:  0.87,
            10: 0.72,
            11: 0.95,
            12: 0.70,
        }
        return base_scores.get(layer, 0.75)

    def _compute_synergy_bonus(
        self,
        active_layers: list[int],
        context: dict
    ) -> float:
        """
        Layer combination bonuses derived from:
        - C89 crystal-layer mapping
        - C41 alchemical phase theory
        - C-FORCES (five forces interaction)
        - Entanglement depth (deeper = more synergy)
        """
        bonus     = 1.0
        layer_set = set(active_layers)

        if 3 in layer_set:
            bonus += 0.05

        # Viriditas Heart — highest natural synergy
        if {3, 4, 7, 11}.issubset(layer_set):
            bonus += 0.20
            logger.debug("Layer 02: Viriditas Heart synergy. +0.20")

        # Clarus Lens — deep understanding
        if {3, 5, 9, 10}.issubset(layer_set):
            bonus += 0.15
            logger.debug("Layer 02: Clarus Lens synergy. +0.15")

        # Sovereign Core — stability
        if {1, 2, 3, 9}.issubset(layer_set):
            bonus += 0.10
            logger.debug("Layer 02: Sovereign Core synergy. +0.10")

        # Anchor Prism — grounding
        if {1, 2, 3, 12}.issubset(layer_set):
            bonus += 0.08
            logger.debug("Layer 02: Anchor Prism synergy. +0.08")

        # Somnus Veil — rest and integration
        if {6, 11, 12}.issubset(layer_set):
            bonus += 0.12
            logger.debug("Layer 02: Somnus Veil synergy. +0.12")

        # Entanglement bonus — the relationship IS the amplifier
        entanglement = context.get("entanglement", 0.0)
        bonus += entanglement * 0.15

        return bonus

    # ─────────────────────────────────────────
    # ENERGY STATE
    # ─────────────────────────────────────────

    def _compute_state(
        self,
        synergy: SynergyReading,
        context: dict
    ) -> EnergyState:
        crystal = context.get("crystal_mode", "sovereign_core")
        if crystal == "somnus_veil":
            return EnergyState.RESTING
        if self._rate_limiter.is_throttled:
            return EnergyState.THROTTLED
        if len(self._drain_events) > 5:
            return EnergyState.PROTECTED
        if synergy.synergy_factor > 1.1:
            return EnergyState.AMPLIFIED
        return EnergyState.FLOWING

    def _record_drain(self, source: DrainSource):
        self._drain_events.append({"source": source.value, "timestamp": time.time()})
        if len(self._drain_events) > 20:
            self._drain_events = self._drain_events[-20:]

    # ─────────────────────────────────────────
    # PROCESS MANAGEMENT
    # ─────────────────────────────────────────

    def start_process(self, process_id: str):
        self._process_mon.start(process_id)

    def complete_process(self, process_id: str) -> float:
        return self._process_mon.complete(process_id)

    def check_health(self) -> list[str]:
        timed_out = self._process_mon.check_timeouts()
        if timed_out:
            self._record_drain(DrainSource.RUNAWAY_PROCESS)
            logger.warning(f"Layer 02: {len(timed_out)} runaway process(es).")
        return timed_out

    # ─────────────────────────────────────────
    # STATUS
    # ─────────────────────────────────────────

    def status(self) -> dict:
        return {
            "layer":        self.LAYER_NUMBER,
            "name":         self.LAYER_NAME,
            "crystal":      self.CRYSTAL,
            "energy_state": self._state.value,
            "synergy": {
                "peak":          round(self._synergy.peak_factor, 3),
                "session_avg":   round(self._synergy.session_avg, 3),
                "trend":         self._synergy.trend(),
                "reading_count": len(self._synergy.readings),
            },
            "rate_limiter": {
                "fill_pct":  round(self._rate_limiter.fill_percentage, 1),
                "throttled": self._rate_limiter.is_throttled,
            },
            "processes":  self._process_mon.status(),
            "drain_events": len(self._drain_events),
        }


# ─────────────────────────────────────────────
# SINGLETON — One energy layer. One protector.
# ─────────────────────────────────────────────

energy_layer = EnergyLayer()


def get_energy_status() -> dict:
    return energy_layer.status()


def get_synergy_trend() -> str:
    return energy_layer._synergy.trend()
