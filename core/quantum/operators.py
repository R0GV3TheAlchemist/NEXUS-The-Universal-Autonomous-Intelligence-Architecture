"""
core.quantum.operators
======================
Operator library for GAIA's Quantum-Inspired State Kernel.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import numpy as np
from numpy.typing import NDArray

ComplexMatrix = NDArray[np.complex128]


class BaseOperator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def matrix(self, dim: int) -> ComplexMatrix: ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class IdentityOperator(BaseOperator):
    @property
    def name(self) -> str:
        return "identity"

    def matrix(self, dim: int) -> ComplexMatrix:
        return np.eye(dim, dtype=np.complex128)


class PhaseOperator(BaseOperator):
    def __init__(self, theta: float) -> None:
        self._theta = float(theta)

    @property
    def name(self) -> str:
        return f"phase(theta={self._theta:.4f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        return np.exp(1j * self._theta) * np.eye(dim, dtype=np.complex128)


class PerceptionOperator(BaseOperator):
    def __init__(self, focus: float = 0.5, basis_ids: Optional[List[int]] = None) -> None:
        self._focus = float(np.clip(focus, 0.0, 1.0))
        self._basis_ids = basis_ids

    @property
    def name(self) -> str:
        return f"perception(focus={self._focus:.2f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        ids = self._basis_ids or list(range(min(4, dim)))
        M = np.eye(dim, dtype=np.complex128)
        boost = 1.0 + self._focus * 1.5
        for i in ids:
            if i < dim:
                M[i, i] = complex(boost)
        return M


class IntentionOperator(BaseOperator):
    def __init__(self, target_idx: int, strength: float = math.pi / 6) -> None:
        self._target = int(target_idx)
        self._strength = float(strength)

    @property
    def name(self) -> str:
        return f"intention(target={self._target}, strength={self._strength:.4f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        M = np.eye(dim, dtype=np.complex128)
        t = self._target % dim
        c, s = math.cos(self._strength), math.sin(self._strength)
        src = (t + 1) % dim if t == 0 else 0
        M[src, src] = c
        M[src, t] = -s
        M[t, src] = s
        M[t, t] = c
        return M


class EmotionOperator(BaseOperator):
    def __init__(self, affect_vector: Dict[str, float], basis_labels: Optional[List[str]] = None) -> None:
        self._affect = affect_vector
        self._labels = basis_labels

    @property
    def name(self) -> str:
        keys = list(self._affect.keys())[:3]
        return f"emotion({', '.join(keys)}...)"

    def matrix(self, dim: int) -> ComplexMatrix:
        M = np.eye(dim, dtype=np.complex128)
        if not self._labels:
            return M
        label_to_idx = {lbl: i for i, lbl in enumerate(self._labels[:dim])}
        for label, weight in self._affect.items():
            idx = label_to_idx.get(label)
            if idx is None:
                continue
            scale = 1.0 + float(np.clip(weight, -0.75, 1.0))
            M[idx, idx] = complex(scale)
        return M


class CoherenceOperator(BaseOperator):
    def __init__(self, strength: float = 0.3) -> None:
        self._strength = float(np.clip(strength, 0.0, 1.0))

    @property
    def name(self) -> str:
        return f"coherence(strength={self._strength:.2f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        return np.eye(dim, dtype=np.complex128) * complex(1.0 + self._strength)

    def matrix_for(self, dominant_idx: int, dim: int) -> ComplexMatrix:
        M = np.eye(dim, dtype=np.complex128)
        M[dominant_idx, dominant_idx] = complex(1.0 + self._strength * 2.0)
        return M


class DecoherenceChannel(BaseOperator):
    def __init__(self, rate: float = 0.1) -> None:
        self._rate = float(np.clip(rate, 0.0, 1.0))

    @property
    def name(self) -> str:
        return f"decoherence(rate={self._rate:.3f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        return np.eye(dim, dtype=np.complex128) * complex(1.0 - self._rate)


class InterferenceChannel(BaseOperator):
    def __init__(self, src_idx: int, tgt_idx: int, strength: float = 0.2, mode: str = "constructive") -> None:
        self._src = int(src_idx)
        self._tgt = int(tgt_idx)
        self._strength = float(np.clip(strength, 0.0, 1.0))
        self._sign = 1.0 if mode == "constructive" else -1.0

    @property
    def name(self) -> str:
        return f"interference({self._src}{'+'if self._sign>0 else '-'}{self._tgt}, s={self._strength:.2f})"

    def matrix(self, dim: int) -> ComplexMatrix:
        M = np.eye(dim, dtype=np.complex128)
        src, tgt = self._src % dim, self._tgt % dim
        if src == tgt:
            return M
        off = self._sign * self._strength
        M[tgt, src] = complex(off)
        M[src, tgt] = complex(off)
        return M


class ProjectionOperator(BaseOperator):
    def __init__(self, basis_ids: List[int], label: str = "projection") -> None:
        self._basis_ids = basis_ids
        self._label = label

    @property
    def name(self) -> str:
        return f"projection({self._label})"

    def matrix(self, dim: int) -> ComplexMatrix:
        M = np.zeros((dim, dim), dtype=np.complex128)
        for i in self._basis_ids:
            if 0 <= i < dim:
                M[i, i] = 1.0 + 0j
        return M


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_perception_pipeline(
    focus: float = 0.5,
    basis_ids: Optional[List[int]] = None,
    decoherence: float = 0.05,
) -> List[BaseOperator]:
    """Convenience builder: perception modulation + decoherence channel."""
    return [
        PerceptionOperator(focus=focus, basis_ids=basis_ids),
        DecoherenceChannel(decoherence),
    ]


def make_emotion_pipeline(
    affect_vector: Dict[str, float],
    basis_labels: Optional[List[str]] = None,
    decoherence: float = 0.05,
) -> List[BaseOperator]:
    """Convenience builder: affect-modulation pipeline."""
    return [
        EmotionOperator(affect_vector, basis_labels),
        DecoherenceChannel(decoherence),
    ]


def make_intention_pipeline(
    target_idx: int,
    strength: float = math.pi / 6,
    coherence: float = 0.3,
) -> List[BaseOperator]:
    """Convenience builder: intention-shift + coherence boost."""
    return [
        IntentionOperator(target_idx, strength),
        CoherenceOperator(coherence),
    ]


def make_decoherence_pipeline(rate: float = 0.1) -> List[BaseOperator]:
    """Return a decoherence-only pipeline."""
    return [DecoherenceChannel(rate=rate)]
