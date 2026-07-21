"""Translation layer between NEXUS internal circuits and OpenQASM output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class CircuitInstruction:
    """A single gate instruction within a NEXUS quantum circuit.

    Attributes:
        gate: Gate name as a string (e.g. 'h', 'x', 'ry', 'cx').
        targets: Qubit indices that this gate operates on.
        controls: Qubit indices that control this gate (for controlled gates).
        parameter: Optional rotation angle or gate parameter in radians.
    """

    gate: str
    targets: List[int]
    controls: List[int] = field(default_factory=list)
    parameter: Optional[float] = None


class QASMBridge:
    """Translates a bounded list of CircuitInstructions into an OpenQASM 2.0 program.

    This first implementation supports:
    - Single-target, parameterless gates (h, x, y, z, s, t, etc.)
    - Single-target, single-parameter rotation gates (rx, ry, rz)
    - Single-control, single-target CNOT (cx) gates
    - Automatic measurement of all qubits to classical bits at the end

    Future extensions will add multi-qubit gates, mid-circuit measurement,
    classical conditionals, and OpenQASM 3.0 output.
    """

    def to_openqasm(
        self,
        qubit_count: int,
        instructions: List[CircuitInstruction],
        circuit_name: str = "nexus_circuit",
    ) -> str:
        """Render the instruction list as an OpenQASM 2.0 program string.

        Args:
            qubit_count: Total number of qubits in the register.
            instructions: Ordered list of gate instructions to emit.
            circuit_name: Optional label embedded as a comment header.

        Returns:
            A complete OpenQASM 2.0 program as a newline-delimited string.

        Raises:
            ValueError: If an instruction uses an unsupported gate configuration.
        """
        lines: List[str] = [
            f"// NEXUS circuit: {circuit_name}",
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            f"qreg q[{qubit_count}];",
            f"creg c[{qubit_count}];",
            "",
        ]

        for instr in instructions:
            if instr.controls:
                if len(instr.controls) != 1 or len(instr.targets) != 1:
                    raise ValueError(
                        f"Gate '{instr.gate}': only single-control, single-target "
                        "controlled instructions are supported in this release."
                    )
                ctrl = instr.controls[0]
                tgt = instr.targets[0]
                lines.append(f"cx q[{ctrl}],q[{tgt}];")
                continue

            if len(instr.targets) != 1:
                raise ValueError(
                    f"Gate '{instr.gate}': only single-target uncontrolled "
                    "instructions are supported in this release."
                )
            tgt = instr.targets[0]
            gate = instr.gate.lower()

            if instr.parameter is not None:
                lines.append(f"{gate}({instr.parameter:.6f}) q[{tgt}];")
            else:
                lines.append(f"{gate} q[{tgt}];")

        lines.append("")
        for idx in range(qubit_count):
            lines.append(f"measure q[{idx}] -> c[{idx}];")

        return "\n".join(lines)

    def validate_qubit_bounds(
        self, qubit_count: int, instructions: List[CircuitInstruction]
    ) -> List[str]:
        """Return a list of validation error strings, or an empty list if valid.

        Checks that all qubit indices referenced in instructions are within
        the range [0, qubit_count).
        """
        errors: List[str] = []
        for i, instr in enumerate(instructions):
            for idx in instr.targets + instr.controls:
                if idx < 0 or idx >= qubit_count:
                    errors.append(
                        f"Instruction {i} ('{instr.gate}'): qubit index {idx} "
                        f"is out of range for a {qubit_count}-qubit register."
                    )
        return errors
