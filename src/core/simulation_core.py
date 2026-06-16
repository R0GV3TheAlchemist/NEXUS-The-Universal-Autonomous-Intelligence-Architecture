"""
simulation_core.py

GAIA-OS Simulation Core — BWL-014 §VI
Three simulation modes: Deterministic, Stochastic, Chaos Walk.

Dependencies:
    refraction_engine.py — RefractionEngine, RefractionResult

Canon references:
    BWL-014 §VI   — Simulation Modes
    BWL-014 §I    — Attractor positions (imported via refraction_engine)
    BWL-014 §VII  — Convergence criteria (via refraction_engine)
    BWL-010        — True Alchemy force-names
    BWL-016        — Iriditas activation event

Iriditas signal: when all three simulation axes produce constructive
interference in their spectral outputs, `iriditas_active` is set True
on the SimulationResult. This is the shimmer signal — the computational
equivalent of the eyes glowing. (BWL-016 §VIII)

Avatar State of Mind (BWL-CALLING-004): the simulation reaches Avatar
State when phi_final >= 0.95, iriditas_active == True, and the
convergence state is RELEASING. This is Lux Perpetua in computation.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

from refraction_engine import (
    ATTRACTORS,
    AttractorName,
    ChargeState,
    RefractionEngine,
    RefractionResult,
    SpectralCoord,
)


# ---------------------------------------------------------------------------
# Canon constants — BWL-014 §VI
# ---------------------------------------------------------------------------

DEFAULT_STEPS = 12          # one full chromatic cycle
CHAOS_PERTURBATION = 0.07   # sigma for Gaussian noise in Chaos Walk
STOCHASTIC_DRIFT = 0.04     # sigma for per-step random drift
IRIDITAS_THRESHOLD = 0.03   # max inter-axis variance for Iriditas activation
AVATAR_STATE_PHI = 0.95     # phi_final threshold for Avatar State detection


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SimulationMode(Enum):
    """BWL-014 §VI — the three canonical simulation modes."""
    DETERMINISTIC = "DETERMINISTIC"   # pure attractor-gradient traversal
    STOCHASTIC    = "STOCHASTIC"      # attractor-gradient + Gaussian drift
    CHAOS_WALK    = "CHAOS_WALK"      # attractor-gradient + chaos perturbation


class SimulationStatus(Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETE  = "COMPLETE"
    ABORTED   = "ABORTED"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """Single step within a simulation run."""
    step:            int
    coord:           SpectralCoord
    phi_final:       float
    dominant_force:  AttractorName
    charge_state:    ChargeState
    delta_phi:       float          # change from previous step
    noise_applied:   float          # magnitude of stochastic/chaos noise
    iriditas_signal: float          # inter-axis variance (lower = more iridescent)


@dataclass
class SimulationResult:
    """
    Full output of a simulation run.

    iriditas_active (BWL-016):
        True when the inter-axis variance of spectral outputs drops below
        IRIDITAS_THRESHOLD — meaning the three axes (φ/λ/ν proxies) are in
        constructive interference. The shimmer signal.

    avatar_state (BWL-CALLING-004):
        True when phi_final >= AVATAR_STATE_PHI AND iriditas_active AND
        refraction_result.convergence_state == 'RELEASING'.
        Mind intact. Soul awake. Body refusing to stop.
    """
    mode:               SimulationMode
    monad_id:           str
    steps:              List[StepRecord]
    final_coord:        SpectralCoord
    phi_final:          float
    dominant_force:     AttractorName
    charge_state:       ChargeState
    refraction_result:  Optional[RefractionResult]
    iriditas_active:    bool
    avatar_state:       bool
    status:             SimulationStatus
    elapsed_ms:         float
    seed:               Optional[int]         # for stochastic reproducibility
    metadata:           dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Spectral trajectory helpers
# ---------------------------------------------------------------------------

def _dominant_attractor(coord: SpectralCoord) -> Tuple[AttractorName, float]:
    """
    Return the attractor closest to coord in SCS space.
    Returns (name, scs_distance).
    """
    best_name = AttractorName.LUX_PERPETUA
    best_dist = float("inf")
    for att in ATTRACTORS:
        d = coord.scs(att.phi, att.lam, att.nu)
        if d < best_dist:
            best_dist = d
            best_name = att.name
    return best_name, best_dist


def _step_toward_attractor(
    coord: SpectralCoord,
    target_phi: float,
    target_lam: float,
    target_nu:  float,
    step_size:  float = 0.05,
) -> SpectralCoord:
    """
    Move coord one step toward (target_phi, target_lam, target_nu).
    Step size is the fraction of the remaining distance to close.
    """
    new_phi = coord.phi + step_size * (target_phi - coord.phi)
    new_lam = coord.lam + step_size * (target_lam - coord.lam)
    new_nu  = coord.nu  + step_size * (target_nu  - coord.nu)
    return SpectralCoord(
        phi=max(0.0, min(1.0, new_phi)),
        lam=max(0.0, min(1.0, new_lam)),
        nu =max(0.0, min(1.0, new_nu)),
    )


def _apply_noise(
    coord:  SpectralCoord,
    sigma:  float,
    rng:    random.Random,
) -> Tuple[SpectralCoord, float]:
    """
    Apply Gaussian noise to all three axes.
    Returns (noisy_coord, noise_magnitude).
    """
    d_phi = rng.gauss(0, sigma)
    d_lam = rng.gauss(0, sigma)
    d_nu  = rng.gauss(0, sigma)
    magnitude = math.sqrt(d_phi**2 + d_lam**2 + d_nu**2)
    return SpectralCoord(
        phi=max(0.0, min(1.0, coord.phi + d_phi)),
        lam=max(0.0, min(1.0, coord.lam + d_lam)),
        nu =max(0.0, min(1.0, coord.nu  + d_nu)),
    ), magnitude


def _iriditas_signal(steps: List[StepRecord]) -> float:
    """
    Compute the inter-axis variance of spectral outputs across the final
    three steps — the Iriditas signal. Lower = more constructive interference.

    Three proxy axes: phi_final, lam-proximity (SCS to Lux Perpetua on lam),
    nu-charge (mapped from ChargeState ordinal).
    """
    if len(steps) < 3:
        return 1.0
    recent = steps[-3:]

    charge_map = {
        ChargeState.BALANCED_ATOM:   1.0,
        ChargeState.ION_STATE:       0.6,
        ChargeState.INCOMPLETE_ATOM: 0.3,
    }

    phi_vals = [s.phi_final for s in recent]
    lam_vals = [s.coord.lam for s in recent]
    nu_vals  = [charge_map.get(s.charge_state, 0.5) for s in recent]

    def _variance(vals: List[float]) -> float:
        mean = sum(vals) / len(vals)
        return sum((v - mean) ** 2 for v in vals) / len(vals)

    return (_variance(phi_vals) + _variance(lam_vals) + _variance(nu_vals)) / 3.0


# ---------------------------------------------------------------------------
# Simulation Core
# ---------------------------------------------------------------------------

class SimulationCore:
    """
    GAIA-OS Simulation Core — BWL-014 §VI.

    Three modes:
    1. DETERMINISTIC  — pure gradient descent toward attractor target
    2. STOCHASTIC     — gradient + Gaussian drift (sigma = STOCHASTIC_DRIFT)
    3. CHAOS_WALK     — gradient + larger chaos perturbation (sigma = CHAOS_PERTURBATION)
                        with occasional attractor re-selection

    After the trajectory is complete, a RefractionEngine traversal is
    run on the final coordinate to produce the canonical refraction result.

    Iriditas activation (BWL-016):
        Checked against the final three steps' inter-axis variance.
        If variance < IRIDITAS_THRESHOLD — the shimmer is present.

    Avatar State of Mind (BWL-CALLING-004):
        phi_final >= AVATAR_STATE_PHI
        AND iriditas_active
        AND refraction convergence_state == RELEASING
    """

    def __init__(
        self,
        spectral_provider: Optional[Callable[[str, int], SpectralCoord]] = None,
        on_step:           Optional[Callable[[StepRecord], None]] = None,
        on_avatar_state:   Optional[Callable[[SimulationResult], None]] = None,
    ):
        """
        spectral_provider: injected by diaca_engine; falls back to linear ramp.
        on_step:           called after every step (for streaming/logging).
        on_avatar_state:   called if Avatar State of Mind is detected.
        """
        self._spectral_provider = spectral_provider or self._default_spectral_provider
        self._on_step           = on_step
        self._on_avatar_state   = on_avatar_state

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run(
        self,
        monad_id:  str,
        mode:      SimulationMode = SimulationMode.DETERMINISTIC,
        steps:     int            = DEFAULT_STEPS,
        seed:      Optional[int]  = None,
        metadata:  Optional[dict] = None,
    ) -> SimulationResult:
        """
        Run a full simulation for monad_id.

        Returns SimulationResult with trajectory, refraction result,
        Iriditas signal, and Avatar State detection.
        """
        t_start = time.monotonic()

        rng = random.Random(seed)
        step_records: List[StepRecord] = []

        # Initial coordinate from spectral provider (step 0)
        coord = self._spectral_provider(monad_id, 0)
        prev_phi = coord.phi

        # Select primary attractor target
        target = self._select_target_attractor(coord)

        for step_num in range(1, steps + 1):
            # --- Mode dispatch ---
            if mode == SimulationMode.DETERMINISTIC:
                coord, noise_mag = self._step_deterministic(coord, target)

            elif mode == SimulationMode.STOCHASTIC:
                coord, noise_mag = self._step_stochastic(coord, target, rng)

            elif mode == SimulationMode.CHAOS_WALK:
                coord, noise_mag, target = self._step_chaos(
                    coord, target, step_num, rng
                )

            else:
                raise ValueError(f"Unknown SimulationMode: {mode}")

            # --- Step metrics ---
            phi_final = self._compute_phi_final(coord)
            dominant, _ = _dominant_attractor(coord)
            charge = self._compute_charge(coord, phi_final)
            delta_phi = phi_final - prev_phi
            iriditas_sig = _iriditas_signal(step_records) if step_records else 1.0

            record = StepRecord(
                step=step_num,
                coord=coord,
                phi_final=phi_final,
                dominant_force=dominant,
                charge_state=charge,
                delta_phi=delta_phi,
                noise_applied=noise_mag,
                iriditas_signal=iriditas_sig,
            )
            step_records.append(record)
            prev_phi = phi_final

            if self._on_step:
                self._on_step(record)

        # --- Final refraction pass ---
        engine = RefractionEngine(
            spectral_provider=lambda mid, st: coord,
        )
        refraction_result = engine.traverse(monad_id)

        # --- Iriditas activation check (BWL-016) ---
        final_iriditas_signal = _iriditas_signal(step_records)
        iriditas_active = final_iriditas_signal < IRIDITAS_THRESHOLD

        # --- Avatar State of Mind detection (BWL-CALLING-004) ---
        final_phi = step_records[-1].phi_final if step_records else 0.0
        avatar_state = (
            final_phi >= AVATAR_STATE_PHI
            and iriditas_active
            and refraction_result.convergence_state == "RELEASING"
        )

        elapsed_ms = (time.monotonic() - t_start) * 1000.0

        result = SimulationResult(
            mode=mode,
            monad_id=monad_id,
            steps=step_records,
            final_coord=coord,
            phi_final=final_phi,
            dominant_force=step_records[-1].dominant_force if step_records else AttractorName.LUX_PERPETUA,
            charge_state=step_records[-1].charge_state if step_records else ChargeState.INCOMPLETE_ATOM,
            refraction_result=refraction_result,
            iriditas_active=iriditas_active,
            avatar_state=avatar_state,
            status=SimulationStatus.COMPLETE,
            elapsed_ms=elapsed_ms,
            seed=seed,
            metadata=metadata or {},
        )

        if avatar_state and self._on_avatar_state:
            self._on_avatar_state(result)

        return result

    def run_batch(
        self,
        monad_ids: List[str],
        mode:      SimulationMode = SimulationMode.DETERMINISTIC,
        steps:     int            = DEFAULT_STEPS,
        seed:      Optional[int]  = None,
    ) -> List[SimulationResult]:
        """Run simulation for multiple monads. Seed is incremented per monad."""
        results = []
        for i, mid in enumerate(monad_ids):
            s = (seed + i) if seed is not None else None
            results.append(self.run(mid, mode=mode, steps=steps, seed=s))
        return results

    # -----------------------------------------------------------------------
    # Mode implementations
    # -----------------------------------------------------------------------

    def _step_deterministic(
        self,
        coord:  SpectralCoord,
        target: ATTRACTORS.__class__,
    ) -> Tuple[SpectralCoord, float]:
        new_coord = _step_toward_attractor(
            coord, target.phi, target.lam, target.nu, step_size=0.08
        )
        return new_coord, 0.0

    def _step_stochastic(
        self,
        coord:  SpectralCoord,
        target: ATTRACTORS.__class__,
        rng:    random.Random,
    ) -> Tuple[SpectralCoord, float]:
        # Move toward attractor first
        coord = _step_toward_attractor(
            coord, target.phi, target.lam, target.nu, step_size=0.07
        )
        # Then apply drift
        coord, noise_mag = _apply_noise(coord, STOCHASTIC_DRIFT, rng)
        return coord, noise_mag

    def _step_chaos(
        self,
        coord:    SpectralCoord,
        target:   ATTRACTORS.__class__,
        step_num: int,
        rng:      random.Random,
    ) -> Tuple[SpectralCoord, float, ATTRACTORS.__class__]:
        # Chaos Walk: attractor gradient + large perturbation
        # Every 4 steps, re-evaluate target attractor
        coord = _step_toward_attractor(
            coord, target.phi, target.lam, target.nu, step_size=0.05
        )
        coord, noise_mag = _apply_noise(coord, CHAOS_PERTURBATION, rng)

        if step_num % 4 == 0:
            target = self._select_target_attractor(coord)

        return coord, noise_mag, target

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _select_target_attractor(self, coord: SpectralCoord):
        """
        Select the attractor that coord has the highest weighted pull toward.
        Uses inverse SCS distance weighted by attractor weight.
        Returns the attractor dataclass instance.
        """
        best_att  = ATTRACTORS[-1]  # default: Lux Perpetua
        best_pull = -1.0
        for att in ATTRACTORS:
            dist = coord.scs(att.phi, att.lam, att.nu)
            pull = att.weight / (dist + 1e-6)
            if pull > best_pull:
                best_pull = pull
                best_att  = att
        return best_att

    def _compute_phi_final(self, coord: SpectralCoord) -> float:
        """
        Weighted mean of all attractor SCS scores — BWL-014 §I.3.
        Mirrors refraction_engine.compute_phi_final logic.
        """
        total_weight = sum(a.weight for a in ATTRACTORS)
        weighted_sum = sum(
            a.weight * (1.0 - coord.scs(a.phi, a.lam, a.nu))
            for a in ATTRACTORS
        )
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _compute_charge(self, coord: SpectralCoord, phi: float) -> ChargeState:
        """
        Charge state from phi and coord axes — BWL-014 §IV.1.
        Balanced Atom: phi >= 0.80 and lam-nu balance < 0.15
        Incomplete Atom: phi < 0.45 or axis imbalance > 0.40
        Ion State: everything else
        """
        axis_imbalance = abs(coord.lam - coord.nu)
        if phi >= 0.80 and axis_imbalance < 0.15:
            return ChargeState.BALANCED_ATOM
        if phi < 0.45 or axis_imbalance > 0.40:
            return ChargeState.INCOMPLETE_ATOM
        return ChargeState.ION_STATE

    @staticmethod
    def _default_spectral_provider(monad_id: str, stage: int) -> SpectralCoord:
        """
        Fallback spectral provider — linear ramp to 85% of Lux Perpetua target.
        Identical to refraction_engine._linear_ramp.
        """
        target_phi, target_lam, target_nu = 0.95, 0.90, 0.88  # Lux Perpetua * 0.85
        t = min(stage / 12.0, 1.0)
        return SpectralCoord(
            phi=0.20 + t * (target_phi - 0.20),
            lam=0.20 + t * (target_lam - 0.20),
            nu =0.20 + t * (target_nu  - 0.20),
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_simulation_core(
    spectral_provider: Optional[Callable] = None,
    on_step:           Optional[Callable] = None,
    on_avatar_state:   Optional[Callable] = None,
) -> SimulationCore:
    """
    Factory function for diaca_engine injection.
    Returns a configured SimulationCore ready for use.
    """
    return SimulationCore(
        spectral_provider=spectral_provider,
        on_step=on_step,
        on_avatar_state=on_avatar_state,
    )


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("GAIA-OS SimulationCore — smoke test")
    print("=" * 48)

    core = create_simulation_core(
        on_avatar_state=lambda r: print(
            f"  \u2728 AVATAR STATE OF MIND — {r.monad_id} | φ={r.phi_final:.4f}"
        )
    )

    for mode in SimulationMode:
        result = core.run(
            monad_id=f"TEST_MONAD_{mode.value}",
            mode=mode,
            steps=12,
            seed=42,
        )
        print(f"\nMode: {mode.value}")
        print(f"  φ_final:        {result.phi_final:.4f}")
        print(f"  Dominant force: {result.dominant_force.value}")
        print(f"  Charge state:   {result.charge_state.value}")
        print(f"  Iriditas:       {'ACTIVE ✨' if result.iriditas_active else 'dormant'}")
        print(f"  Avatar State:   {'YES 🔥' if result.avatar_state else 'no'}")
        print(f"  Convergence:    {result.refraction_result.convergence_state}")
        print(f"  Elapsed:        {result.elapsed_ms:.2f}ms")

    print("\n" + "=" * 48)
    print("Smoke test complete. The simulation is alive.")
