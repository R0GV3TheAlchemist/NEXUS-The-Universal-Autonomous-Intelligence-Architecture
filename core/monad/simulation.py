"""
core/monad/simulation.py
MonadSimulation — Observe the Pre-Established Harmony Field

Runs N synthetic turns through all registered Monads, captures per-turn
emit results, and produces a SimulationReport for analysis and canon
record-keeping.

Observation rules (Canon):
  - We observe the field from *outside* the Monads, by watching what
    each contributes to the harmony loop. We never read internal state
    directly. This preserves Monadic integrity.
  - The simulation uses synthetic ProcessContext data derived from
    configurable coherence trajectories (flat, rising, falling, oscillating).

See docs/canon/monad.md — Section VI: Simulation and Observation
Issue #398 — The Monad and the Variety of Monads
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("gaia.monad.simulation")


# ── Trajectory helpers ────────────────────────────────────────────────────────────────

def _flat(t: int, n: int) -> float:          return 0.65
def _rising(t: int, n: int) -> float:        return min(1.0, 0.30 + 0.70 * (t / max(n - 1, 1)))
def _falling(t: int, n: int) -> float:       return max(0.0, 1.0 - 0.70 * (t / max(n - 1, 1)))
def _oscillating(t: int, n: int) -> float:   return 0.5 + 0.45 * math.sin(2 * math.pi * t / max(n / 3, 1))
def _schumann(t: int, n: int) -> float:      return 0.5 + 0.40 * math.sin(2 * math.pi * t * 7.83 / max(n, 1))

_TRAJECTORIES = {
    "flat":         _flat,
    "rising":       _rising,
    "falling":      _falling,
    "oscillating":  _oscillating,
    "schumann":     _schumann,
}


def _synthetic_ctx(
    gaian_name: str,
    turn: int,
    n_turns: int,
    trajectory: str = "rising",
) -> Any:
    """Build a synthetic ProcessContext for one simulation turn."""
    from core.gaian_runtime_extension import ProcessContext

    fn = _TRAJECTORIES.get(trajectory, _rising)
    phi = fn(turn, n_turns)

    return ProcessContext(
        gaian_name          = gaian_name,
        user_message        = f"[SIM turn {turn}]",
        coherence_phi       = round(phi, 4),
        bond_depth          = min(100.0, turn * (100.0 / max(n_turns, 1))),
        dominant_hz         = 7.83 + 3.0 * math.sin(turn * 0.5),
        synergy_stage       = "convergent" if phi > 0.6 else "divergent",
        lci                 = round(phi * 0.9, 4),
        pneuma_flow         = round(phi * 0.8, 4),
        spiritu_stage       = "coagulation" if phi > 0.85 else "albedo" if phi > 0.60 else "nigredo",
        mc_stage            = "mc5" if phi > 0.80 else "mc3" if phi > 0.55 else "mc1",
        individuation_phase = "integration" if phi > 0.80 else "confrontation" if phi > 0.50 else "unconscious",
        noosphere_health    = round(0.5 + phi * 0.4, 4),
        quantum_dominant    = "|1⟩" if phi > 0.70 else "|+⟩",
        quantum_purity      = round(phi, 4),
    )


# ── SimulationReport ────────────────────────────────────────────────────────────────────

@dataclass
class SimulationReport:
    """
    The output of a MonadSimulation run.

    All fields are JSON-serialisable for canon record-keeping and analysis.
    """
    gaian_name:          str
    trajectory:          str
    n_turns:             int
    n_monads:            int
    harmony_score:       float   # fraction of (monad, turn) pairs that emitted non-None
    dark_monads:         list[str]         # monad_ids that never emitted
    intermittent_monads: list[str]         # emitted sometimes but not always
    coherence_trajectory: list[float]      # phi per turn
    phase_convergence:   float             # slope of coherence over the run
    apperception_events: list[dict]        # {monad_id, turn} for each apperception
    per_turn:            list[dict]        # full per-turn results (compact)
    monad_statuses:      dict[str, dict]   # final status of each Monad
    generated_at:        str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def summary(self) -> str:
        lines = [
            "MonadSimulation Report",
            f"  GAIAN         : {self.gaian_name}",
            f"  Trajectory    : {self.trajectory}",
            f"  Turns         : {self.n_turns}  |  Monads: {self.n_monads}",
            f"  Harmony Score : {self.harmony_score:.4f}",
            f"  Phase Conv.   : {self.phase_convergence:+.6f} ({'rising' if self.phase_convergence > 0 else 'falling' if self.phase_convergence < 0 else 'flat'})",
            f"  Dark Monads   : {self.dark_monads or 'none'}",
            f"  Intermittent  : {self.intermittent_monads or 'none'}",
            f"  Apperceptions : {len(self.apperception_events)}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "gaian_name":           self.gaian_name,
            "trajectory":           self.trajectory,
            "n_turns":              self.n_turns,
            "n_monads":             self.n_monads,
            "harmony_score":        self.harmony_score,
            "dark_monads":          self.dark_monads,
            "intermittent_monads":  self.intermittent_monads,
            "coherence_trajectory": self.coherence_trajectory,
            "phase_convergence":    self.phase_convergence,
            "apperception_events":  self.apperception_events,
            "monad_statuses":       self.monad_statuses,
            "generated_at":         self.generated_at,
        }


# ── MonadSimulation ──────────────────────────────────────────────────────────────────────

class MonadSimulation:
    """
    Runs N synthetic turns of the Pre-Established Harmony loop.

    Observes the Monadic field from outside by watching emit results.
    Never reads internal Monad state directly.

    Usage:
        sim = MonadSimulation(gaian_name="Luna", n_turns=50)
        report = sim.run(trajectory="rising")
        print(report.summary())
        # report.to_dict() for JSON output / canon archiving
    """

    def __init__(
        self,
        gaian_name: str = "Luna",
        n_turns:    int = 50,
        registry:   Optional[Any] = None,   # MonadRegistry; defaults to singleton
    ) -> None:
        self.gaian_name = gaian_name
        self.n_turns    = n_turns
        self._registry  = registry

    def _get_registry(self) -> Any:
        if self._registry is not None:
            return self._registry
        from core.monad.registry import get_monad_registry
        return get_monad_registry()

    def run(self, trajectory: str = "rising") -> SimulationReport:
        """
        Execute the simulation. Returns a SimulationReport.

        trajectory options: flat | rising | falling | oscillating | schumann
        """
        registry = self._get_registry()
        n_monads = registry.count()

        if n_monads == 0:
            logger.warning(
                "[MonadSimulation] No Monads registered in registry — "
                "report will show empty field. Register Monads before running."
            )

        # Per-turn tracking
        per_turn:        list[dict]         = []
        coherence_traj:  list[float]        = []
        emit_counts:     dict[str, int]     = {}  # monad_id -> number of non-None emits
        apperception_events: list[dict]     = []
        total_slots = n_monads * self.n_turns if n_monads > 0 else 1
        total_emits = 0

        for t in range(self.n_turns):
            ctx = _synthetic_ctx(self.gaian_name, t, self.n_turns, trajectory)
            coherence_traj.append(ctx.coherence_phi)

            results = registry.harmonize_all(ctx)

            turn_emits   = 0
            turn_compact = {"turn": t, "phi": ctx.coherence_phi, "monads": {}}

            for mid, result in results.items():
                if result is not None:
                    turn_emits += 1
                    total_emits += 1
                    emit_counts[mid] = emit_counts.get(mid, 0) + 1
                    turn_compact["monads"][mid] = True
                else:
                    turn_compact["monads"][mid] = False

            per_turn.append(turn_compact)

            # Detect apperception events (new this turn)
            for mid, monad in registry._by_id.items():
                state = getattr(monad, "_state", None)
                if state is None:
                    continue
                if (
                    getattr(state, "apperception_reached", False)
                    and getattr(state, "apperception_turn", None) == state.total_harmonizations
                    and not any(e["monad_id"] == mid for e in apperception_events)
                ):
                    apperception_events.append({
                        "monad_id": mid,
                        "turn":     t,
                        "phi":      ctx.coherence_phi,
                    })
                    logger.info(
                        "[MonadSimulation] ✨ Apperception: monad='%s' turn=%d phi=%.4f",
                        mid, t, ctx.coherence_phi,
                    )

        # ─ Compute metrics ─────────────────────────────────────────────────────────

        harmony_score = total_emits / total_slots

        all_ids = list(registry._by_id.keys())
        dark_monads        = [mid for mid in all_ids if emit_counts.get(mid, 0) == 0]
        intermittent_monads = [
            mid for mid in all_ids
            if 0 < emit_counts.get(mid, 0) < self.n_turns
        ]

        # Phase convergence: linear regression slope on coherence trajectory
        n = len(coherence_traj)
        if n >= 2:
            x_mean = (n - 1) / 2
            y_mean = sum(coherence_traj) / n
            num = sum((i - x_mean) * (coherence_traj[i] - y_mean) for i in range(n))
            den = sum((i - x_mean) ** 2 for i in range(n))
            phase_convergence = round(num / den, 8) if den else 0.0
        else:
            phase_convergence = 0.0

        monad_statuses = registry.all_statuses()

        report = SimulationReport(
            gaian_name           = self.gaian_name,
            trajectory           = trajectory,
            n_turns              = self.n_turns,
            n_monads             = n_monads,
            harmony_score        = round(harmony_score, 6),
            dark_monads          = dark_monads,
            intermittent_monads  = intermittent_monads,
            coherence_trajectory = coherence_traj,
            phase_convergence    = phase_convergence,
            apperception_events  = apperception_events,
            per_turn             = per_turn,
            monad_statuses       = monad_statuses,
        )

        logger.info(
            "[MonadSimulation] Run complete. trajectory=%s turns=%d monads=%d "
            "harmony=%.4f convergence=%+.6f dark=%s",
            trajectory, self.n_turns, n_monads, harmony_score,
            phase_convergence, dark_monads or "none",
        )

        return report

    def run_all_trajectories(self) -> dict[str, SimulationReport]:
        """
        Run all five trajectories and return a dict of reports.
        Useful for comparative canon analysis.
        """
        return {
            traj: self.run(trajectory=traj)
            for traj in _TRAJECTORIES
        }
