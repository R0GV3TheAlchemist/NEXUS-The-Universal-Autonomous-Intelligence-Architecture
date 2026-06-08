"""
core.quantum.state_kernel
=========================
Quantum-Inspired State Kernel for GAIA-OS.

This module implements a *classical simulation* of a quantum-like cognitive
state.  No actual QPU is required — the mathematics borrow concepts from
quantum mechanics (superposition, interference, measurement/collapse) and
apply them to GAIA's internal cognitive representation.

Core concepts
-------------
QuantumState
    A complex amplitude vector of dimension D.  Each component represents
    one "cognitive basis state" (e.g. an emotion, an intent, a belief).
    The vector is always unit-normalised: ||psi||_2 = 1.

    Superposition: GAIA can hold multiple hypotheses simultaneously,
    each weighted by a complex amplitude.  The squared magnitude of each
    amplitude is the probability of that hypothesis being "true" upon
    measurement.

    Interference: Two states can constructively or destructively interfere,
    allowing GAIA to amplify coherent signals and suppress contradictions.

    Measurement/Collapse: When GAIA must commit to a decision, the state
    vector is sampled according to the Born-rule probability distribution,
    and the vector collapses to the chosen basis state.

QuantumKernel
    Singleton orchestrator that maintains one QuantumState per active
    user session and applies operator sequences drawn from the 12 GAIA
    cognitive engines.  It exposes:
      - step()          : apply one operator pipeline to the current state
      - observe()       : extract the dominant cognitive label
      - coherence()     : measure how "decided" the state is (purity)
      - snapshot()      : serialise state for logging / audit

Mathematical note
-----------------
All operations are performed in 64-bit complex arithmetic (numpy complex128)
for numerical stability.  The module is intentionally free of quantum
circuit frameworks (no Qiskit, no Cirq) so it runs on every platform with
only numpy as a dependency.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray

log = logging.getLogger(__name__)

# Type alias
ComplexVec = NDArray[np.complex128]


# ---------------------------------------------------------------------------
# QuantumState
# ---------------------------------------------------------------------------

class QuantumState:
    """
    A unit-normalised complex amplitude vector representing GAIA's
    current cognitive state in an abstract Hilbert space.

    Parameters
    ----------
    dim      : int          Dimensionality of the state space.
    labels   : list[str]    Human-readable labels for each basis state.
                            Defaults to ["b0", "b1", ..., "b{dim-1}"].
    seed     : int | None   RNG seed for reproducible initialisation.
    """

    def __init__(
        self,
        dim:    int,
        labels: Optional[List[str]] = None,
        seed:   Optional[int]       = None,
    ) -> None:
        if dim < 1:
            raise ValueError("dim must be >= 1")
        self._dim    = dim
        self._labels = labels or [f"b{i}" for i in range(dim)]
        if len(self._labels) != dim:
            raise ValueError("len(labels) must equal dim")
        rng          = np.random.default_rng(seed)
        # Start in uniform superposition (equal probability over all bases)
        raw          = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
        self._psi: ComplexVec = self._normalise(raw)
        self._created_at = time.time()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def labels(self) -> List[str]:
        return list(self._labels)

    @property
    def psi(self) -> ComplexVec:
        """The raw complex amplitude vector (read-only copy)."""
        return self._psi.copy()

    @property
    def probabilities(self) -> NDArray[np.float64]:
        """Born-rule probabilities: |psi_i|^2 for each basis state."""
        return (np.abs(self._psi) ** 2).real

    @property
    def purity(self) -> float:
        """
        State purity: sum(|psi_i|^4).  Equals 1 for a pure (collapsed)
        state and 1/dim for a maximally mixed (uniform superposition) state.
        """
        return float(np.sum(np.abs(self._psi) ** 4).real)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def apply(self, operator: ComplexVec) -> "QuantumState":
        """
        Apply a unitary-like operator matrix to the state.

        Parameters
        ----------
        operator : shape (dim, dim) complex array.
                   Does not need to be perfectly unitary — the result
                   is re-normalised automatically.

        Returns
        -------
        self  (mutates in-place for chaining)
        """
        if operator.shape != (self._dim, self._dim):
            raise ValueError(
                f"Operator shape {operator.shape} != state dim ({self._dim}, {self._dim})"
            )
        self._psi = self._normalise(operator @ self._psi)
        return self

    def superpose(self, other: "QuantumState", alpha: float = 0.5) -> "QuantumState":
        """
        Superpose *self* with *other* with mixing coefficient *alpha*.

        Result = normalise(sqrt(alpha) * psi_self + sqrt(1-alpha) * psi_other)

        Both states must have the same dimensionality.
        """
        if other.dim != self._dim:
            raise ValueError("Cannot superpose states of different dimensions.")
        alpha   = float(np.clip(alpha, 0.0, 1.0))
        blended = np.sqrt(alpha) * self._psi + np.sqrt(1 - alpha) * other._psi
        self._psi = self._normalise(blended)
        return self

    def interfere(self, other: "QuantumState", phase: float = 0.0) -> "QuantumState":
        """
        Interfere *self* with *other* with a relative phase shift (radians).

        A phase of 0  → constructive interference (amplifies aligned components).
        A phase of pi → destructive interference (suppresses aligned components).
        """
        if other.dim != self._dim:
            raise ValueError("Cannot interfere states of different dimensions.")
        phase_factor = np.exp(1j * phase)
        combined     = self._psi + phase_factor * other._psi
        self._psi    = self._normalise(combined)
        return self

    def measure(self, collapse: bool = True) -> Tuple[int, str, float]:
        """
        Perform a projective measurement.

        Samples one basis index according to the Born-rule probability
        distribution.  If *collapse* is True, the state vector collapses
        to that basis state (all amplitude concentrated on the measured index).

        Returns
        -------
        (index, label, probability)
        """
        probs = self.probabilities
        idx   = int(np.random.choice(self._dim, p=probs / probs.sum()))
        prob  = float(probs[idx])
        if collapse:
            collapsed      = np.zeros(self._dim, dtype=np.complex128)
            collapsed[idx] = 1.0
            self._psi      = collapsed
        return idx, self._labels[idx], prob

    def dominant(self) -> Tuple[int, str, float]:
        """
        Return the basis state with the highest probability without
        collapsing the state vector (non-destructive observation).
        """
        probs = self.probabilities
        idx   = int(np.argmax(probs))
        return idx, self._labels[idx], float(probs[idx])

    def decohere(self, rate: float = 0.1) -> "QuantumState":
        """
        Simulate decoherence by mixing the current state with a uniform
        superposition.  Higher *rate* → more mixing → less quantum-ness.
        Rate should be in [0, 1].
        """
        rate          = float(np.clip(rate, 0.0, 1.0))
        uniform       = np.ones(self._dim, dtype=np.complex128) / np.sqrt(self._dim)
        self._psi     = self._normalise((1 - rate) * self._psi + rate * uniform)
        return self

    def reset(self) -> "QuantumState":
        """Reset to uniform superposition (maximum entropy / uncertainty)."""
        self._psi = np.ones(self._dim, dtype=np.complex128) / np.sqrt(self._dim)
        return self

    def clone(self) -> "QuantumState":
        """Return a deep copy of this state."""
        new       = QuantumState.__new__(QuantumState)
        new._dim  = self._dim
        new._labels = list(self._labels)
        new._psi  = self._psi.copy()
        new._created_at = self._created_at
        return new

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "dim":           self._dim,
            "labels":        self._labels,
            "psi_real":      self._psi.real.tolist(),
            "psi_imag":      self._psi.imag.tolist(),
            "probabilities": self.probabilities.tolist(),
            "purity":        self.purity,
            "dominant":      self.dominant()[1],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuantumState":
        state = cls(dim=data["dim"], labels=data["labels"])
        state._psi = np.array(data["psi_real"]) + 1j * np.array(data["psi_imag"])
        return state

    def __repr__(self) -> str:
        idx, label, prob = self.dominant()
        return (
            f"QuantumState(dim={self._dim}, dominant='{label}' "
            f"p={prob:.3f}, purity={self.purity:.3f})"
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(v: ComplexVec) -> ComplexVec:
        norm = np.linalg.norm(v)
        if norm < 1e-12:
            # Degenerate: return uniform superposition
            d = len(v)
            return np.ones(d, dtype=np.complex128) / np.sqrt(d)
        return v / norm


# ---------------------------------------------------------------------------
# Cognitive basis definition for GAIA
# ---------------------------------------------------------------------------

# The 32-dimensional cognitive basis maps to GAIA's 12 engine domains.
# Each engine contributes 2-4 basis states representing its key poles.
GAIA_BASIS_LABELS: List[str] = [
    # Perception / Awareness (4)
    "perception:alert",      "perception:receptive",
    "perception:diffuse",    "perception:focused",
    # Emotion / Affect (4)
    "emotion:joy",           "emotion:calm",
    "emotion:tension",       "emotion:grief",
    # Intention / Goal (4)
    "intention:explore",     "intention:create",
    "intention:resolve",     "intention:rest",
    # Reasoning / Inference (4)
    "reason:analytic",       "reason:synthetic",
    "reason:abductive",      "reason:intuitive",
    # Memory / Recall (4)
    "memory:episodic",       "memory:semantic",
    "memory:procedural",     "memory:working",
    # Somatic / Embodiment (4)
    "soma:grounded",         "soma:energised",
    "soma:depleted",         "soma:coherent",
    # Social / Relational (4)
    "social:bonded",         "social:curious",
    "social:guarded",        "social:empathic",
    # Alchemical / Transformative (4)
    "alch:nigredo",          "alch:albedo",
    "alch:citrinitas",       "alch:rubedo",
]

GAIA_STATE_DIM: int = len(GAIA_BASIS_LABELS)  # 32


# ---------------------------------------------------------------------------
# QuantumKernel
# ---------------------------------------------------------------------------

@dataclass
class KernelSnapshot:
    """Point-in-time snapshot of the kernel state for auditing."""
    timestamp:   float
    session_id:  str
    user_id:     str
    state_dict:  dict
    operator_log: List[str]


class QuantumKernel:
    """
    Orchestrates quantum-inspired cognitive state transformations for
    one GAIA session.

    One QuantumKernel instance is created per active user session and
    lives for the duration of that session.  Between sessions, the
    state vector can be serialised and rehydrated from the memory store.

    Usage
    -----
    from core.quantum import QuantumKernel, GAIA_BASIS_LABELS

    kernel = QuantumKernel(user_id="user_001", session_id="sess_abc")
    kernel.step([perception_op, emotion_op])   # apply operator pipeline
    label, prob = kernel.observe()             # what is GAIA thinking?
    print(kernel.coherence())                  # how decided is it?
    snap = kernel.snapshot()                   # serialise for audit log
    """

    def __init__(
        self,
        user_id:    str,
        session_id: str,
        dim:        int             = GAIA_STATE_DIM,
        labels:     Optional[List[str]] = None,
        initial_state: Optional[QuantumState] = None,
    ) -> None:
        self.user_id    = user_id
        self.session_id = session_id
        self._state     = initial_state or QuantumState(
            dim=dim, labels=labels or GAIA_BASIS_LABELS[:dim]
        )
        self._op_log:   List[str] = []
        self._step_count = 0
        self._created_at = time.time()
        log.info(
            "QuantumKernel initialised: user=%s session=%s dim=%d",
            user_id, session_id, self._state.dim,
        )

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def step(
        self,
        operators: Sequence,   # Sequence[BaseOperator] — avoids circular import
        decoherence_rate: float = 0.02,
    ) -> "QuantumKernel":
        """
        Apply a sequence of operators to the current state, then apply
        a small decoherence nudge to prevent over-collapse.

        Operators are applied left-to-right:
            |psi'> = O_n ... O_2 O_1 |psi>

        Parameters
        ----------
        operators         : List of operator objects from operators.py.
        decoherence_rate  : How much to mix toward uniform superposition
                            after applying operators (default 0.02 = 2%).
        """
        for op in operators:
            matrix = op.matrix(self._state.dim)
            self._state.apply(matrix)
            self._op_log.append(op.name)

        if decoherence_rate > 0:
            self._state.decohere(decoherence_rate)

        self._step_count += 1
        return self

    def observe(self, collapse: bool = False) -> Tuple[str, float]:
        """
        Return the dominant cognitive label and its probability.
        Does not collapse the state by default (non-destructive).
        """
        _, label, prob = self._state.dominant()
        return label, prob

    def measure(self) -> Tuple[str, float]:
        """
        Perform a collapsing measurement — commits GAIA to one
        cognitive state.  Use sparingly (at decision points only).
        """
        _, label, prob = self._state.measure(collapse=True)
        self._op_log.append(f"MEASURE:{label}")
        return label, prob

    def coherence(self) -> float:
        """
        State purity in [1/dim, 1.0].  A value near 1 means GAIA is
        very decided; near 1/dim means maximally uncertain.
        """
        return self._state.purity

    def probabilities(self) -> Dict[str, float]:
        """Return {label: probability} dict for all basis states."""
        return dict(zip(self._state.labels, self._state.probabilities.tolist()))

    def top_states(self, n: int = 5) -> List[Tuple[str, float]]:
        """Return the top-n most probable cognitive basis states."""
        probs  = self._state.probabilities
        labels = self._state.labels
        ranked = sorted(zip(labels, probs.tolist()), key=lambda x: x[1], reverse=True)
        return ranked[:n]

    def inject(self, state: QuantumState) -> "QuantumKernel":
        """Replace the current state (e.g. on session restore)."""
        if state.dim != self._state.dim:
            raise ValueError("Injected state dimensionality mismatch.")
        self._state = state
        self._op_log.append("INJECT")
        return self

    def reset(self) -> "QuantumKernel":
        """Reset to uniform superposition."""
        self._state.reset()
        self._op_log.append("RESET")
        return self

    def snapshot(self) -> KernelSnapshot:
        """Serialise current state for the audit ledger."""
        return KernelSnapshot(
            timestamp    = time.time(),
            session_id   = self.session_id,
            user_id      = self.user_id,
            state_dict   = self._state.to_dict(),
            operator_log = list(self._op_log),
        )

    # ------------------------------------------------------------------
    # Context building (for LLM prompt injection)
    # ------------------------------------------------------------------

    def context_block(self, top_n: int = 5) -> str:
        """
        Build a compact human-readable context string suitable for
        injecting into GAIA's system prompt.

        Example output::

            [QKernel] dominant: emotion:joy (p=0.31) | purity=0.18
            Top states: emotion:joy 0.31 | perception:alert 0.22 | ...
        """
        dominant, dom_prob = self.observe()
        top  = self.top_states(top_n)
        top_str = " | ".join(f"{lbl} {p:.2f}" for lbl, p in top)
        return (
            f"[QKernel] dominant: {dominant} (p={dom_prob:.2f}) "
            f"| purity={self.coherence():.3f}\n"
            f"Top states: {top_str}"
        )

    def __repr__(self) -> str:
        d, p = self.observe()
        return (
            f"QuantumKernel(user={self.user_id!r}, session={self.session_id!r}, "
            f"steps={self._step_count}, dominant={d!r}, p={p:.3f})"
        )
