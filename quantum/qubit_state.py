"""Canonical qubit and quantum register state abstractions for NEXUS."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class QubitState:
    """Represents the state of a single logical qubit.

    Attributes:
        index: Qubit index within its parent register.
        alpha_real: Real part of the |0> amplitude.
        alpha_imag: Imaginary part of the |0> amplitude.
        beta_real: Real part of the |1> amplitude.
        beta_imag: Imaginary part of the |1> amplitude.
        measured_value: Classical bit result after measurement (0 or 1), or None.
        coherence_score: Normalised decoherence health metric [0.0, 1.0].
        tags: Arbitrary metadata key-value pairs for audit and traceability.
    """

    index: int
    alpha_real: float = 1.0
    alpha_imag: float = 0.0
    beta_real: float = 0.0
    beta_imag: float = 0.0
    measured_value: Optional[int] = None
    coherence_score: float = 1.0
    tags: Dict[str, str] = field(default_factory=dict)

    def is_measured(self) -> bool:
        """Return True if this qubit has been collapsed to a classical value."""
        return self.measured_value is not None

    def is_coherent(self, threshold: float = 0.5) -> bool:
        """Return True if coherence_score is above the given threshold."""
        return self.coherence_score >= threshold


@dataclass(slots=True)
class QuantumRegisterState:
    """Represents the collective state of a quantum register across a backend.

    Attributes:
        register_id: Unique identifier for this register within a session.
        qubits: Ordered list of QubitState objects.
        entanglement_groups: Lists of qubit index groups that share entanglement.
        backend_name: The execution backend this register is bound to.
    """

    register_id: str
    qubits: List[QubitState] = field(default_factory=list)
    entanglement_groups: List[List[int]] = field(default_factory=list)
    backend_name: str = "simulator"

    def measured_count(self) -> int:
        """Return the number of qubits that have been measured."""
        return sum(1 for qubit in self.qubits if qubit.is_measured())

    def all_measured(self) -> bool:
        """Return True if every qubit in the register has been measured."""
        return all(qubit.is_measured() for qubit in self.qubits)

    def coherence_summary(self) -> Dict[str, float]:
        """Return min, max, and mean coherence scores across all qubits."""
        if not self.qubits:
            return {"min": 0.0, "max": 0.0, "mean": 0.0}
        scores = [q.coherence_score for q in self.qubits]
        return {
            "min": min(scores),
            "max": max(scores),
            "mean": sum(scores) / len(scores),
        }
