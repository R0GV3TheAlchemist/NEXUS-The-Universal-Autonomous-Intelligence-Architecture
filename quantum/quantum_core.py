"""Quantum execution facade and backend orchestration for NEXUS."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class QuantumExecutionRequest:
    """Encapsulates a request to execute a quantum circuit on a backend.

    Attributes:
        job_id: Unique identifier for this execution job.
        circuit_name: Human-readable label for the circuit being executed.
        backend: Target backend name (must match a registered adapter key).
        shots: Number of measurement shots to run.
        parameters: Gate-level or circuit-level parameter overrides.
        metadata: Arbitrary key-value pairs for audit and traceability.
    """

    job_id: str
    circuit_name: str
    backend: str = "simulator"
    shots: int = 1024
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QuantumExecutionResult:
    """Captures the outcome of a quantum execution job.

    Attributes:
        job_id: Matches the originating QuantumExecutionRequest.job_id.
        backend: The backend that produced this result.
        success: True if execution completed without fatal errors.
        counts: Measurement outcome histogram (bitstring -> count).
        metrics: Backend-specific performance and fidelity metrics.
        warnings: Non-fatal warnings emitted during execution.
        error: Structured error message if success is False.
    """

    job_id: str
    backend: str
    success: bool
    counts: Dict[str, int] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


class QuantumCore:
    """Backend-agnostic facade for quantum circuit execution.

    QuantumCore maintains a registry of named backend adapters and delegates
    execution requests to the appropriate adapter.  If no adapter is registered
    for the requested backend, a structured failure result is returned rather
    than raising an exception, ensuring classical callers always receive a
    typed response.

    This is the primary entry point for classical NEXUS agents that need to
    submit work to the quantum layer.
    """

    def __init__(self, adapter_registry: Optional[Dict[str, Any]] = None) -> None:
        """Initialise QuantumCore with an optional pre-populated adapter registry."""
        self.adapter_registry: Dict[str, Any] = adapter_registry or {}

    def register_adapter(self, name: str, adapter: Any) -> None:
        """Register a named quantum backend adapter.

        Args:
            name: The backend identifier (e.g. 'simulator', 'qiskit', 'cirq').
            adapter: Any object that exposes an execute(request) -> QuantumExecutionResult method.
        """
        self.adapter_registry[name] = adapter

    def unregister_adapter(self, name: str) -> bool:
        """Remove a named adapter. Returns True if it existed."""
        return self.adapter_registry.pop(name, None) is not None

    def available_backends(self) -> List[str]:
        """Return the list of currently registered backend names."""
        return list(self.adapter_registry.keys())

    def execute(self, request: QuantumExecutionRequest) -> QuantumExecutionResult:
        """Dispatch a quantum execution request to the appropriate adapter.

        If the requested backend has no registered adapter, returns a
        QuantumExecutionResult with success=False and a descriptive error
        rather than raising.  This preserves safe degradation for callers.

        Args:
            request: The fully specified execution request.

        Returns:
            A QuantumExecutionResult from the adapter, or a failure result.
        """
        adapter = self.adapter_registry.get(request.backend)
        if adapter is None:
            return QuantumExecutionResult(
                job_id=request.job_id,
                backend=request.backend,
                success=False,
                error=(
                    f"No adapter registered for backend '{request.backend}'. "
                    f"Available backends: {self.available_backends()}"
                ),
            )
        return adapter.execute(request)
