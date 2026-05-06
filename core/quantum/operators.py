"""
core.quantum.operators
======================
Operator library for GAIA's Quantum-Inspired State Kernel.

Every operator in this module transforms a QuantumState by applying a
complex matrix (or a parameterised function that generates one) to the
state vector.  Operators are modular and composable — the QuantumKernel
calls ``op.matrix(dim)`` and feeds the result to ``QuantumState.apply()``.

Operator taxonomy
-----------------
PerceptionOperator   — modulates attention and sensory-focus basis states.
IntentionOperator    — shifts probability mass toward a goal-aligned subspace.
EmotionOperator      — amplifies or suppresses affect-domain basis states.
CoherenceOperator    — increases purity by concentrating probability mass.
DecoherenceChannel   — disperses probability mass (simulates noise / fatigue).
InterferenceChannel  — constructive or destructive interference between domains.
IdentityOperator     — no-op; useful as a pipeline placeholder.
PhaseOperator        — rotates the global phase (no physical observable effect
                       but useful for interference preparation).
ProjectionOperator   — hard-collapses the state into a named subspace.

All operators inherit from BaseOperator and must implement:
    name    : str   (unique operator identifier)
    matrix(dim) -> NDArray[complex128]

The matrix must be square (dim × dim) and should be approximately
unitary; it will be applied via matrix-vector product in QuantumState.apply()
which re-normalises the result automatically.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

ComplexMatrix = NDArray[np.complex128]


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseOperator(ABC):
    """Base class for all GAIA quantum-state operators."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def matrix(self, dim: int) -> ComplexMatrix:
        """
        Return the (dim × dim) complex operator matrix.
        Must be callable with any dim ≥ 1.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

class IdentityOperator(BaseOperator):
    """No-op operator — returns the identity matrix."""

    @property
    def name(self) -> str:
        return "identity"

    def matrix(self, dim: int) -> ComplexMatrix:
        return np.eye(dim, dtype=np.complex128)


# ---------------------------------------------------------------------------
# Phase rotation
# ---------------------------------------------------------------------------

class PhaseOperator(BaseOperator):
    """
    Applies a global phase rotation e^{i*theta} to the state.

    A global phase has no observable effect on probabilities but changes
    the interference pattern when two states are later combined.

    Parameters
    ----------
    theta : Phase angle in radians.
    """

    def __init__(self, theta: float) -> None:
        self._theta = float(theta)

    @property
    def name(self) -> str:
        return f"phase(theta={self._theta:.4f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        return np.exp(1j * self._theta) * np.eye(dim, dtype=np.complex128)


# ---------------------------------------------------------------------------
# Perception operator
# ---------------------------------------------------------------------------

class PerceptionOperator(BaseOperator):
    """
    Modulates attention by amplifying perception-domain basis states
    and slightly suppressing all others.

    Parameters
    ----------
    focus     : 0.0 (diffuse/receptive) → 1.0 (sharp/focused).  Controls
                how strongly the perception basis states are amplified.
    basis_ids : Indices of the perception-domain basis states.  Defaults
                to indices 0–3 (matching GAIA_BASIS_LABELS perception block).
    """

    def __init__(
        self,
        focus:     float           = 0.5,
        basis_ids: Optional[List[int]] = None,
    ) -> None:
        self._focus     = float(np.clip(focus, 0.0, 1.0))
        self._basis_ids = basis_ids  # resolved lazily in matrix()

    @property
    def name(self) -> str:
        return f"perception(focus={self._focus:.2f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        ids = self._basis_ids or list(range(min(4, dim)))
        M   = np.eye(dim, dtype=np.complex128)
        boost = 1.0 + self._focus * 1.5   # 1.0 → 2.5
        for i in ids:
            if i < dim:
                M[i, i] = complex(boost)
        return M


# ---------------------------------------------------------------------------
# Intention operator
# ---------------------------------------------------------------------------

class IntentionOperator(BaseOperator):
    """
    Shifts probability mass toward a specific intention/goal basis state.

    Implemented as a rotation in the (current_dominant, target) subspace,
    analogous to a single-qubit Y-rotation.

    Parameters
    ----------
    target_idx  : Index of the target basis state (intention to strengthen).
    strength    : Rotation angle in radians (0 = no effect, pi/2 = full
                  collapse to target).  Default pi/6 (~30 deg).
    """

    def __init__(self, target_idx: int, strength: float = math.pi / 6) -> None:
        self._target  = int(target_idx)
        self._strength = float(strength)

    @property
    def name(self) -> str:
        return f"intention(target={self._target}, strength={self._strength:.4f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        M   = np.eye(dim, dtype=np.complex128)
        t   = self._target % dim
        c   = math.cos(self._strength)
        s   = math.sin(self._strength)
        # Rotate in the (0, target) subspace if t != 0, else (0, 1)
        src = (t + 1) % dim if t == 0 else 0
        M[src, src] =  c
        M[src, t]   = -s
        M[t,   src] =  s
        M[t,   t]   =  c
        return M


# ---------------------------------------------------------------------------
# Emotion operator
# ---------------------------------------------------------------------------

class EmotionOperator(BaseOperator):
    """
    Amplifies or suppresses specific emotion-domain basis states based
    on an affect signal from the AffectInference engine.

    Parameters
    ----------
    affect_vector : Dict mapping basis label → scalar weight in [-1, 1].
                    Positive → amplify; negative → suppress.
    basis_labels  : Full list of basis labels (to resolve label → index).
                    If None, applies no-op.
    """

    def __init__(
        self,
        affect_vector: Dict[str, float],
        basis_labels:  Optional[List[str]] = None,
    ) -> None:
        self._affect  = affect_vector
        self._labels  = basis_labels

    @property
    def name(self) -> str:
        keys = list(self._affect.keys())[:3]
        return f"emotion({', '.join(keys)}...)"

    def matrix(self, dim: int) -> ComplexMatrix:
        M = np.eye(dim, dtype=np.complex128)
        if not self._labels:
            return M
        label_to_idx = {l: i for i, l in enumerate(self._labels[:dim])}
        for label, weight in self._affect.items():
            idx = label_to_idx.get(label)
            if idx is None:
                continue
            # Amplify (weight > 0) or suppress (weight < 0)
            # Scale factor in (0.25, 2.0) to avoid degeneracy
            scale = 1.0 + float(np.clip(weight, -0.75, 1.0))
            M[idx, idx] = complex(scale)
        return M


# ---------------------------------------------------------------------------
# Coherence operator
# ---------------------------------------------------------------------------

class CoherenceOperator(BaseOperator):
    """
    Increases state coherence by concentrating probability mass around
    the current dominant state.

    Analogous to an amplitude amplification (Grover) step: amplifies
    the highest-probability component and slightly suppresses others.

    Parameters
    ----------
    strength : How aggressively to concentrate (0.0 = identity, 1.0 = full
               amplification of dominant state).  Default 0.3.
    """

    def __init__(self, strength: float = 0.3) -> None:
        self._strength = float(np.clip(strength, 0.0, 1.0))

    @property
    def name(self) -> str:
        return f"coherence(strength={self._strength:.2f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        # The matrix is not fixed — it depends on the *current* state.
        # We return a scale-diagonal operator; the kernel applies it and
        # re-normalises.  The actual dominant index is not available here,
        # so we parametrise by strength alone and let the QuantumKernel
        # call this *after* it knows the current dominant index via
        # CoherenceOperator.matrix_for(dominant_idx, dim).
        return np.eye(dim, dtype=np.complex128) * complex(1.0 + self._strength)

    def matrix_for(self, dominant_idx: int, dim: int) -> ComplexMatrix:
        """Preferred variant — concentrates on a known dominant index."""
        M = np.eye(dim, dtype=np.complex128)
        boost = 1.0 + self._strength * 2.0
        M[dominant_idx, dominant_idx] = complex(boost)
        return M


# ---------------------------------------------------------------------------
# Decoherence channel
# ---------------------------------------------------------------------------

class DecoherenceChannel(BaseOperator):
    """
    Simulates decoherence (cognitive noise, fatigue, distraction) by
    mixing the state toward the maximally mixed uniform superposition.

    This is *not* a unitary operator — it's a completely-positive
    trace-preserving (CPTP) channel approximation.

    Parameters
    ----------
    rate : Mixing coefficient in [0, 1].  0 = identity, 1 = full collapse
           to uniform superposition.  Default 0.05.
    """

    def __init__(self, rate: float = 0.05) -> None:
        self._rate = float(np.clip(rate, 0.0, 1.0))

    @property
    def name(self) -> str:
        return f"decoherence(rate={self._rate:.3f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        # (1 - rate) * I + rate * (1/dim) * ones_matrix
        ones_mat = np.ones((dim, dim), dtype=np.complex128) / dim
        return (1.0 - self._rate) * np.eye(dim, dtype=np.complex128) + self._rate * ones_mat


# ---------------------------------------------------------------------------
# Interference channel
# ---------------------------------------------------------------------------

class InterferenceChannel(BaseOperator):
    """
    Applies structured interference between two named cognitive domains
    (e.g. 'emotion' and 'reason').  Constructive phase (0) amplifies
    both; destructive phase (pi) suppresses the overlap.

    Parameters
    ----------
    domain_a_ids  : Basis indices for the first domain.
    domain_b_ids  : Basis indices for the second domain.
    phase         : Relative phase in radians (0 = constructive, pi = destructive).
    coupling      : Coupling strength in [0, 1].  Default 0.3.
    """

    def __init__(
        self,
        domain_a_ids: List[int],
        domain_b_ids: List[int],
        phase:        float = 0.0,
        coupling:     float = 0.3,
    ) -> None:
        self._a       = domain_a_ids
        self._b       = domain_b_ids
        self._phase   = float(phase)
        self._coupling = float(np.clip(coupling, 0.0, 1.0))

    @property
    def name(self) -> str:
        return f"interference(phase={self._phase:.3f}, coupling={self._coupling:.2f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        M  = np.eye(dim, dtype=np.complex128)
        pf = np.exp(1j * self._phase) * self._coupling
        for i in self._a:
            for j in self._b:
                if i < dim and j < dim and i != j:
                    M[i, j] += pf
                    M[j, i] += np.conj(pf)
        return M


# ---------------------------------------------------------------------------
# Projection operator
# ---------------------------------------------------------------------------

class ProjectionOperator(BaseOperator):
    """
    Hard-projects (collapses) the state onto a named subspace.

    All probability mass outside the subspace is zeroed and the result
    is re-normalised by QuantumState.apply().  Use at decision points
    where GAIA must commit to a specific cognitive mode.

    Parameters
    ----------
    subspace_ids : Indices to retain.  All others are zeroed.
    """

    def __init__(self, subspace_ids: List[int]) -> None:
        self._ids = subspace_ids

    @property
    def name(self) -> str:
        return f"projection(ids={self._ids})"

    def matrix(self, dim: int) -> ComplexMatrix:
        M = np.zeros((dim, dim), dtype=np.complex128)
        for i in self._ids:
            if i < dim:
                M[i, i] = 1.0
        return M


# ---------------------------------------------------------------------------
# Pre-built operator factory helpers
# ---------------------------------------------------------------------------

def make_perception_pipeline(focus: float = 0.5) -> List[BaseOperator]:
    """Return a standard perception operator pipeline."""
    return [
        PerceptionOperator(focus=focus),
        DecoherenceChannel(rate=0.02),
    ]


def make_emotion_pipeline(
    affect: Dict[str, float],
    labels: List[str],
) -> List[BaseOperator]:
    """Return a standard emotion modulation pipeline."""
    return [
        EmotionOperator(affect_vector=affect, basis_labels=labels),
        CoherenceOperator(strength=0.2),
        DecoherenceChannel(rate=0.01),
    ]


def make_intention_pipeline(target_idx: int, strength: float = math.pi / 6) -> List[BaseOperator]:
    """Return a standard intention-strengthening pipeline."""
    return [
        IntentionOperator(target_idx=target_idx, strength=strength),
        CoherenceOperator(strength=0.25),
    ]


def make_decoherence_pipeline(rate: float = 0.1) -> List[BaseOperator]:
    """Return a decoherence-only pipeline (for idle / fatigue simulation)."""
    return [DecoherenceChannel(rate=rate)]
