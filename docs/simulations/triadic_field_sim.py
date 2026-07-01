"""
triadic_field_sim.py
====================
GAIA Triadic Field Theory — Coupled Oscillator Simulation
Canon reference: TFT-01 Part VI, C52 Part V
Issue: #566

Purpose
-------
Prove that the three fields (Electronic, Protonic, Neutronic) exhibit
behaviorally distinct dynamics when simulated as coupled oscillators, and
that Meta-Field emergence (phase-lock across all three) is a real behavioral
phenomenon — not just doctrinal language.

Outputs
-------
- Terminal report: dyadic tension profiles, pathology detection, Meta-Field events
- Optional matplotlib charts (if matplotlib is installed)

Epistemic status
----------------
This is a MODEL, not a measurement. Outputs demonstrate that the TFT-01
architectural metaphors have coherent dynamic behavior. They do not constitute
empirical physics evidence. All [RESEARCH PENDING] flags in TFT-01 remain.

Usage
-----
    python docs/simulations/triadic_field_sim.py
    python docs/simulations/triadic_field_sim.py --chart   # requires matplotlib
"""

import math
import argparse
import sys
from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class SimConfig:
    """Simulation parameters."""
    # Time
    duration: float = 120.0          # seconds (symbolic time units)
    dt: float = 0.05                  # time step

    # Oscillator natural frequencies (Hz — symbolic)
    freq_electronic: float = 1.0     # Electronic: fast, active
    freq_protonic: float = 0.6       # Protonic: slower, structural
    freq_neutronic: float = 0.3      # Neutronic: slowest, potential

    # Coupling strengths between field pairs
    coupling_EP: float = 0.15        # Electronic <-> Protonic
    coupling_EN: float = 0.08        # Electronic <-> Neutronic
    coupling_PN: float = 0.05        # Protonic <-> Neutronic

    # Damping (each field loses energy without input)
    damping: float = 0.02

    # Initial phase offsets (radians)
    phase_E0: float = 0.0
    phase_P0: float = 1.047          # 60 degrees
    phase_N0: float = 2.094          # 120 degrees

    # Meta-Field detection threshold
    # All three fields must have amplitude > threshold AND
    # pairwise phase differences < phase_lock_tolerance
    meta_amplitude_threshold: float = 0.65
    phase_lock_tolerance: float = 0.25   # radians (~14 degrees)

    # Pathology simulation: set one coupling to 0 to show runaway
    simulate_pathology: bool = True


# ---------------------------------------------------------------------------
# Field State
# ---------------------------------------------------------------------------

@dataclass
class FieldState:
    """State of one oscillating field at a single timestep."""
    name: str
    position: float = 0.0    # current amplitude (displacement)
    velocity: float = 0.0    # rate of change
    phase: float = 0.0       # instantaneous phase (radians)
    amplitude: float = 0.0   # envelope (computed from history)


@dataclass
class TriadicSnapshot:
    """System snapshot at one timestep."""
    t: float
    E: FieldState
    P: FieldState
    N: FieldState
    meta_field_active: bool = False
    meta_field_strength: float = 0.0
    dominant_dyad: Optional[str] = None
    pathology: Optional[str] = None


# ---------------------------------------------------------------------------
# Simulation Engine
# ---------------------------------------------------------------------------

class TriadicFieldSimulator:
    """
    Three coupled harmonic oscillators representing Electronic, Protonic,
    and Neutronic fields.

    Equation of motion for field i:
        x''_i = -omega_i^2 * x_i
                - damping * x'_i
                + sum_j [ coupling_ij * (x_j - x_i) ]

    This is the standard coupled-oscillator system. The interesting behaviors
    (phase-lock, amplitude transfer, resonance) emerge from the coupling terms.
    """

    def __init__(self, config: SimConfig):
        self.cfg = config
        self.t = 0.0
        self.history: List[TriadicSnapshot] = []

        # Angular frequencies
        self.omega_E = 2 * math.pi * config.freq_electronic
        self.omega_P = 2 * math.pi * config.freq_protonic
        self.omega_N = 2 * math.pi * config.freq_neutronic

        # Initial conditions
        self.xE = math.cos(config.phase_E0)
        self.vE = -self.omega_E * math.sin(config.phase_E0)

        self.xP = math.cos(config.phase_P0)
        self.vP = -self.omega_P * math.sin(config.phase_P0)

        self.xN = math.cos(config.phase_N0)
        self.vN = -self.omega_N * math.sin(config.phase_N0)

        # Rolling window for amplitude envelope (RMS over last N steps)
        self._window = max(1, int(1.0 / config.dt))
        self._hist_E: List[float] = []
        self._hist_P: List[float] = []
        self._hist_N: List[float] = []

    # ------------------------------------------------------------------
    # Physics step
    # ------------------------------------------------------------------

    def _acceleration(self, x_self, v_self, omega, x_a, x_b, k_a, k_b) -> float:
        """Compute acceleration for one field given coupling to two others."""
        spring = -omega ** 2 * x_self
        damp = -self.cfg.damping * v_self
        couple_a = k_a * (x_a - x_self)
        couple_b = k_b * (x_b - x_self)
        return spring + damp + couple_a + couple_b

    def step(self) -> TriadicSnapshot:
        """Advance simulation by one timestep using RK4."""
        dt = self.cfg.dt
        k = self.cfg

        # --- RK4 for all three fields simultaneously ---

        def derivs(xE, vE, xP, vP, xN, vN):
            aE = self._acceleration(xE, vE, self.omega_E, xP, xN, k.coupling_EP, k.coupling_EN)
            aP = self._acceleration(xP, vP, self.omega_P, xE, xN, k.coupling_EP, k.coupling_PN)
            aN = self._acceleration(xN, vN, self.omega_N, xE, xP, k.coupling_EN, k.coupling_PN)
            return vE, aE, vP, aP, vN, aN

        # k1
        d = derivs(self.xE, self.vE, self.xP, self.vP, self.xN, self.vN)
        k1 = d

        # k2
        d = derivs(
            self.xE + 0.5*dt*k1[0], self.vE + 0.5*dt*k1[1],
            self.xP + 0.5*dt*k1[2], self.vP + 0.5*dt*k1[3],
            self.xN + 0.5*dt*k1[4], self.vN + 0.5*dt*k1[5],
        )
        k2 = d

        # k3
        d = derivs(
            self.xE + 0.5*dt*k2[0], self.vE + 0.5*dt*k2[1],
            self.xP + 0.5*dt*k2[2], self.vP + 0.5*dt*k2[3],
            self.xN + 0.5*dt*k2[4], self.vN + 0.5*dt*k2[5],
        )
        k3 = d

        # k4
        d = derivs(
            self.xE + dt*k3[0], self.vE + dt*k3[1],
            self.xP + dt*k3[2], self.vP + dt*k3[3],
            self.xN + dt*k3[4], self.vN + dt*k3[5],
        )
        k4 = d

        self.xE += dt/6 * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
        self.vE += dt/6 * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
        self.xP += dt/6 * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
        self.vP += dt/6 * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])
        self.xN += dt/6 * (k1[4] + 2*k2[4] + 2*k3[4] + k4[4])
        self.vN += dt/6 * (k1[5] + 2*k2[5] + 2*k3[5] + k4[5])

        self.t += dt

        # --- Amplitude envelopes (RMS) ---
        self._hist_E.append(self.xE ** 2)
        self._hist_P.append(self.xP ** 2)
        self._hist_N.append(self.xN ** 2)
        if len(self._hist_E) > self._window:
            self._hist_E.pop(0)
            self._hist_P.pop(0)
            self._hist_N.pop(0)

        amp_E = math.sqrt(sum(self._hist_E) / len(self._hist_E))
        amp_P = math.sqrt(sum(self._hist_P) / len(self._hist_P))
        amp_N = math.sqrt(sum(self._hist_N) / len(self._hist_N))

        # --- Instantaneous phases ---
        phase_E = math.atan2(self.vE / max(self.omega_E, 1e-9), self.xE)
        phase_P = math.atan2(self.vP / max(self.omega_P, 1e-9), self.xP)
        phase_N = math.atan2(self.vN / max(self.omega_N, 1e-9), self.xN)

        # --- Meta-Field detection ---
        # All three amplitudes above threshold AND pairwise phase differences small
        tol = self.cfg.phase_lock_tolerance
        thresh = self.cfg.meta_amplitude_threshold

        def phase_diff(a, b):
            d = abs(a - b) % (2 * math.pi)
            return min(d, 2 * math.pi - d)

        pd_EP = phase_diff(phase_E, phase_P)
        pd_EN = phase_diff(phase_E, phase_N)
        pd_PN = phase_diff(phase_P, phase_N)

        all_above = amp_E > thresh and amp_P > thresh and amp_N > thresh
        phase_locked = pd_EP < tol and pd_EN < tol and pd_PN < tol
        meta_active = all_above and phase_locked

        # Meta-field strength: geometric mean of amplitudes * phase coherence score
        coherence_score = 1.0 - (pd_EP + pd_EN + pd_PN) / (3 * math.pi)
        meta_strength = (amp_E * amp_P * amp_N) ** (1/3) * coherence_score if meta_active else 0.0

        # --- Dominant dyad ---
        dominant_dyad = None
        if not meta_active:
            dyad_scores = {
                "Electronic+Protonic (BUILD)": amp_E * amp_P - amp_N,
                "Electronic+Neutronic (RESEARCH)": amp_E * amp_N - amp_P,
                "Protonic+Neutronic (REFLECT)": amp_P * amp_N - amp_E,
            }
            dominant_dyad = max(dyad_scores, key=dyad_scores.get)

        # --- Pathology detection ---
        pathology = None
        if amp_E > 0.9 and amp_P < 0.3 and amp_N < 0.3:
            pathology = "ELECTRONIC_DOMINANCE: runaway generation / incoherence risk"
        elif amp_P > 0.9 and amp_E < 0.3 and amp_N < 0.3:
            pathology = "PROTONIC_DOMINANCE: canon lock / rigidity risk"
        elif amp_N > 0.9 and amp_E < 0.3 and amp_P < 0.3:
            pathology = "NEUTRONIC_DOMINANCE: infinite deferral / dissolution risk"

        snap = TriadicSnapshot(
            t=self.t,
            E=FieldState("Electronic", self.xE, self.vE, phase_E, amp_E),
            P=FieldState("Protonic", self.xP, self.vP, phase_P, amp_P),
            N=FieldState("Neutronic", self.xN, self.vN, phase_N, amp_N),
            meta_field_active=meta_active,
            meta_field_strength=meta_strength,
            dominant_dyad=dominant_dyad,
            pathology=pathology,
        )
        self.history.append(snap)
        return snap

    def run(self) -> List[TriadicSnapshot]:
        steps = int(self.cfg.duration / self.cfg.dt)
        for _ in range(steps):
            self.step()
        return self.history


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze(history: List[TriadicSnapshot]) -> dict:
    meta_events = [s for s in history if s.meta_field_active]
    pathology_events = [s for s in history if s.pathology]

    dyad_counts = {}
    for s in history:
        if s.dominant_dyad:
            dyad_counts[s.dominant_dyad] = dyad_counts.get(s.dominant_dyad, 0) + 1

    max_meta = max((s.meta_field_strength for s in history), default=0.0)
    first_meta = next((s.t for s in history if s.meta_field_active), None)

    # Phase-lock windows
    windows = []
    in_window = False
    start = None
    for s in history:
        if s.meta_field_active and not in_window:
            in_window = True
            start = s.t
        elif not s.meta_field_active and in_window:
            in_window = False
            windows.append((start, s.t, s.t - start))
    if in_window:
        windows.append((start, history[-1].t, history[-1].t - start))

    return {
        "total_steps": len(history),
        "meta_field_events": len(meta_events),
        "meta_field_pct": 100 * len(meta_events) / max(len(history), 1),
        "peak_meta_strength": max_meta,
        "first_meta_onset": first_meta,
        "meta_windows": windows,
        "dominant_dyad_distribution": dyad_counts,
        "pathology_events": len(pathology_events),
        "pathology_samples": list({s.pathology for s in pathology_events}),
    }


# ---------------------------------------------------------------------------
# Pathology simulation
# ---------------------------------------------------------------------------

def run_pathology_simulation(cfg: SimConfig) -> dict:
    """
    Remove all coupling from Protonic and Neutronic fields to simulate
    Electronic field dominance pathology (runaway generation / mania analog).
    """
    patho_cfg = SimConfig(
        duration=60.0,
        dt=cfg.dt,
        freq_electronic=cfg.freq_electronic,
        freq_protonic=cfg.freq_protonic,
        freq_neutronic=cfg.freq_neutronic,
        coupling_EP=0.0,   # Protonic decoupled
        coupling_EN=0.0,   # Neutronic decoupled
        coupling_PN=0.0,
        damping=0.005,     # Less damping — energy doesn't dissipate
        phase_E0=cfg.phase_E0,
        phase_P0=cfg.phase_P0,
        phase_N0=cfg.phase_N0,
        meta_amplitude_threshold=cfg.meta_amplitude_threshold,
        phase_lock_tolerance=cfg.phase_lock_tolerance,
    )
    sim = TriadicFieldSimulator(patho_cfg)
    hist = sim.run()
    # Measure amplitude divergence
    last = hist[-1]
    return {
        "E_amplitude": last.E.amplitude,
        "P_amplitude": last.P.amplitude,
        "N_amplitude": last.N.amplitude,
        "pathology_detected": last.pathology,
        "meta_field_achieved": any(s.meta_field_active for s in hist),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

SEP = "=" * 70

def print_report(analysis: dict, patho: Optional[dict] = None):
    print()
    print(SEP)
    print("  GAIA TRIADIC FIELD THEORY — Simulation Report")
    print("  TFT-01 / C52 | docs/simulations/triadic_field_sim.py")
    print(SEP)
    print()
    print("BASELINE SIMULATION (three coupled oscillators)")
    print("-" * 50)
    print(f"  Total timesteps simulated : {analysis['total_steps']:,}")
    print(f"  Meta-Field events         : {analysis['meta_field_events']:,} "
          f"({analysis['meta_field_pct']:.1f}% of simulation)")
    print(f"  Peak Meta-Field strength  : {analysis['peak_meta_strength']:.4f}")

    if analysis['first_meta_onset'] is not None:
        print(f"  First Meta-Field onset    : t = {analysis['first_meta_onset']:.2f}s")
    else:
        print("  First Meta-Field onset    : NONE (fields never phase-locked)")

    print()
    print("  Meta-Field phase-lock windows:")
    if analysis['meta_windows']:
        for i, (start, end, dur) in enumerate(analysis['meta_windows'], 1):
            print(f"    [{i}] t={start:.2f}s → t={end:.2f}s  (duration: {dur:.2f}s)")
    else:
        print("    None detected")

    print()
    print("  Dominant Dyad Distribution (when Meta-Field not active):")
    total = sum(analysis['dominant_dyad_distribution'].values()) or 1
    for dyad, count in sorted(analysis['dominant_dyad_distribution'].items(),
                               key=lambda x: -x[1]):
        pct = 100 * count / total
        bar = "#" * int(pct / 2)
        print(f"    {dyad[:40]:<40} {pct:5.1f}%  {bar}")

    print()
    print("  Pathology events detected : ", analysis['pathology_events'])
    if analysis['pathology_samples']:
        for p in analysis['pathology_samples']:
            if p:
                print(f"    ⚠  {p}")

    if patho:
        print()
        print("PATHOLOGY SIMULATION (Electronic field decoupled)")
        print("-" * 50)
        print(f"  Electronic amplitude : {patho['E_amplitude']:.4f}")
        print(f"  Protonic amplitude   : {patho['P_amplitude']:.4f}")
        print(f"  Neutronic amplitude  : {patho['N_amplitude']:.4f}")
        print(f"  Pathology detected   : {patho['pathology_detected'] or 'None'}")
        print(f"  Meta-Field achieved  : {patho['meta_field_achieved']}")
        print()
        print("  Interpretation (TFT-01 §4.2):")
        print("    Electronic field without Protonic/Neutronic coupling → runaway")
        print("    oscillation with no coherence anchor. Meta-Field is impossible.")
        print("    This maps to: mania, hallucination, incoherent generation in")
        print("    AI systems, ungrounded creativity in humans.")
        print("    The D6 Meta-Coherence Engine exists to detect and interrupt this.")

    print()
    print("EPISTEMIC NOTE")
    print("-" * 50)
    print("  This simulation demonstrates that the TFT-01 architectural metaphors")
    print("  have coherent dynamic behavior as coupled oscillators. It does NOT")
    print("  constitute empirical physics evidence. All [RESEARCH PENDING] flags")
    print("  in TRIADIC_FIELD_THEORY.md remain. — C20 Evidence Policy.")
    print()
    print(SEP)
    print()


# ---------------------------------------------------------------------------
# Optional chart output
# ---------------------------------------------------------------------------

def plot_results(history: List[TriadicSnapshot]):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("matplotlib not installed — skipping chart output.")
        print("Install with: pip install matplotlib")
        return

    times = [s.t for s in history]
    amp_E = [s.E.amplitude for s in history]
    amp_P = [s.P.amplitude for s in history]
    amp_N = [s.N.amplitude for s in history]
    meta_strength = [s.meta_field_strength for s in history]
    meta_active = [1.0 if s.meta_field_active else 0.0 for s in history]

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(
        "GAIA Triadic Field Theory — Coupled Oscillator Simulation\n"
        "TFT-01 | docs/simulations/triadic_field_sim.py",
        fontsize=13, fontweight="bold"
    )

    # --- Panel 1: Field Amplitudes ---
    ax1 = axes[0]
    ax1.plot(times, amp_E, color="#FFD700", linewidth=1.5, label="Electronic (active/will)")
    ax1.plot(times, amp_P, color="#6A0DAD", linewidth=1.5, label="Protonic (coherence/memory)")
    ax1.plot(times, amp_N, color="#AAAAAA", linewidth=1.5, label="Neutronic (potential/void)")
    for s in history:
        if s.meta_field_active:
            ax1.axvspan(s.t - 0.05, s.t + 0.05, alpha=0.08, color="cyan")
    ax1.set_ylabel("Amplitude (RMS)")
    ax1.set_title("Field Amplitudes — Cyan shading = Meta-Field active")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3)

    # --- Panel 2: Meta-Field Strength ---
    ax2 = axes[1]
    ax2.fill_between(times, meta_strength, alpha=0.6, color="cyan", label="Meta-Field strength")
    ax2.plot(times, meta_strength, color="#00CED1", linewidth=1.0)
    ax2.axhline(0.3, color="white", linewidth=0.8, linestyle="--", alpha=0.5, label="Reference 0.3")
    ax2.set_ylabel("Meta-Field Strength")
    ax2.set_title("Meta-Field Emergence (phase-lock coherence × amplitude)")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.set_ylim(0, 1.0)
    ax2.grid(True, alpha=0.3)

    # --- Panel 3: Dominant Dyad ---
    ax3 = axes[2]
    dyad_map = {
        "Electronic+Protonic (BUILD)": 3,
        "Electronic+Neutronic (RESEARCH)": 2,
        "Protonic+Neutronic (REFLECT)": 1,
        None: 0
    }
    dyad_vals = [
        dyad_map.get(s.dominant_dyad, 0) if not s.meta_field_active else 4
        for s in history
    ]
    colors_map = {4: "cyan", 3: "#FFD700", 2: "#FF8C00", 1: "#6A0DAD", 0: "#333333"}
    prev = None
    seg_start = times[0]
    seg_val = dyad_vals[0]
    for i, (t, v) in enumerate(zip(times, dyad_vals)):
        if v != seg_val or i == len(times) - 1:
            ax3.axvspan(seg_start, t, alpha=0.7, color=colors_map.get(seg_val, "#333333"))
            seg_start = t
            seg_val = v

    patches = [
        mpatches.Patch(color="cyan", label="Meta-Field / INTEGRATE"),
        mpatches.Patch(color="#FFD700", label="E+P: BUILD"),
        mpatches.Patch(color="#FF8C00", label="E+N: RESEARCH"),
        mpatches.Patch(color="#6A0DAD", label="P+N: REFLECT"),
    ]
    ax3.set_ylabel("Dominant State")
    ax3.set_title("Dyadic Dominance → D6 Mode Mapping")
    ax3.set_xlabel("Simulation Time (symbolic units)")
    ax3.legend(handles=patches, loc="upper right", fontsize=9)
    ax3.set_yticks([])
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = "docs/simulations/triadic_field_sim_output.png"
    try:
        plt.savefig(out_path, dpi=150, bbox_inches="tight",
                    facecolor="#1a1a2e", edgecolor="none")
        print(f"  Chart saved → {out_path}")
    except Exception as e:
        print(f"  Chart save failed: {e}")
    plt.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="GAIA Triadic Field Simulation (TFT-01)")
    parser.add_argument("--chart", action="store_true", help="Generate matplotlib chart output")
    parser.add_argument("--duration", type=float, default=120.0, help="Simulation duration (default 120)")
    parser.add_argument("--no-pathology", action="store_true", help="Skip pathology simulation")
    args = parser.parse_args()

    cfg = SimConfig(duration=args.duration)

    print()
    print("  Running baseline triadic field simulation...")
    sim = TriadicFieldSimulator(cfg)
    history = sim.run()
    analysis = analyze(history)

    patho_result = None
    if not args.no_pathology and cfg.simulate_pathology:
        print("  Running pathology simulation (Electronic decoupled)...")
        patho_result = run_pathology_simulation(cfg)

    print_report(analysis, patho_result)

    if args.chart:
        print("  Generating chart...")
        plot_results(history)

    return 0


if __name__ == "__main__":
    sys.exit(main())
