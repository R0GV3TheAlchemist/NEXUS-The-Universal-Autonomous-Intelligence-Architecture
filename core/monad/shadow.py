"""
Shadow Monad — core/monad/shadow.py
Canon: SHADOW_INTERROGATOR.md, FALSIFICATION_PROTOCOL.md

The subconscious questioning engine — runs the SHADOW_INTERROGATOR protocol.
Always active. Speaks when not asked. Detects dark lines (phi collapse patterns),
flags OA-4 open items, and holds falsification pending queue.
Outputs: shadow_active_flags, interrogator_questions, falsification_pending
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from .base import GaiaMonad

if TYPE_CHECKING:
    from core.gaian_runtime_extension import ProcessContext


@dataclass
class ShadowFlag:
    """A detected shadow pattern requiring attention."""
    flag_type: str    # e.g. 'phi_collapse', 'dark_turn_streak', 'oa4_open'
    message: str
    phi_at_detection: float
    turn_at_detection: int
    resolved: bool = False


# Shadow interrogator questions — drawn from SHADOW_INTERROGATOR.md canonical set
_INTERROGATOR_QUESTIONS: list[tuple[float, str]] = [
    (0.0,  "What are you avoiding naming?"),
    (0.15, "What assumption is hiding inside that certainty?"),
    (0.28, "What would need to be false for this to be wrong?"),
    (0.42, "What is the cost of being right here?"),
    (0.58, "Who benefits if this claim holds?"),
    (0.72, "What is the shadow of this strength?"),
    (0.85, "What is purified away that should be kept?"),
    (0.92, "What arrives beyond the white light that you are not yet naming?"),
]

# OA-4 open item tags
_OA4_OPEN_TAGS: frozenset[str] = frozenset({
    "IOSIS_CORRIDOR_UNRESOLVED",
    "TRANSMUTATION_INCOMPLETE",
    "SHADOW_UNINTEGRATED",
    "CANON_ALIGNMENT_PENDING",
    "MONAD_ISOLATION_VIOLATION",
})


class ShadowMonad(GaiaMonad):
    """
    The Shadow Monad never sleeps. It is always active regardless of phi.
    Its job is to surface what the other Monads cannot see about themselves.

    Leibniz isolation law is the Shadow's mirror:
    it cannot see the other Monads' state — which means it must infer
    shadow patterns from phi trajectory alone.

    Dark line: 3+ consecutive turns with phi delta < -0.03 (collapsing field).
    OA-4: Any unresolved item from the open action list.
    Falsification pending: claims not yet subjected to the falsification protocol.
    """

    monad_type = "shadow"

    def __init__(self, monad_id: str) -> None:
        super().__init__(monad_id=monad_id)
        self._phi_history: list[float] = []
        self._shadow_flags: list[ShadowFlag] = []
        self._falsification_pending: list[str] = []
        self._oa4_open: set[str] = set()

    def harmonize(self, ctx: "ProcessContext") -> Optional[dict]:
        phi = getattr(ctx, "coherence_phi", 0.5)
        turn = getattr(ctx, "turn_number", 0) or 0

        self._phi_history.append(phi)
        if len(self._phi_history) > 20:
            self._phi_history = self._phi_history[-20:]

        # Detect phi collapse (dark line)
        dark_line_detected = self._detect_dark_line()
        if dark_line_detected:
            flag = ShadowFlag(
                flag_type="phi_collapse",
                message="Dark line detected: phi collapsing for 3+ consecutive turns.",
                phi_at_detection=phi,
                turn_at_detection=turn,
            )
            self._shadow_flags.append(flag)

        # OA-4 flag: IOSIS corridor auto-flagged when phi in range
        if 0.72 <= phi <= 0.85:
            self._oa4_open.add("IOSIS_CORRIDOR_UNRESOLVED")
        elif phi > 0.85 and "IOSIS_CORRIDOR_UNRESOLVED" in self._oa4_open:
            self._oa4_open.discard("IOSIS_CORRIDOR_UNRESOLVED")

        # Select the interrogator question most relevant to current phi
        interrogator_question = self._select_interrogator_question(phi)

        # Shadow active flags (unresolved only)
        active_flags = [
            {"type": f.flag_type, "message": f.message}
            for f in self._shadow_flags
            if not f.resolved
        ]

        return {
            "shadow_active_flags": active_flags,
            "interrogator_questions": [interrogator_question],
            "falsification_pending": list(self._falsification_pending),
            "oa4_open": list(self._oa4_open),
            "dark_line_detected": dark_line_detected,
            "phi_history_length": len(self._phi_history),
        }

    def add_falsification_claim(self, claim: str) -> None:
        """Registers a claim for the falsification protocol queue."""
        if claim not in self._falsification_pending:
            self._falsification_pending.append(claim)

    def resolve_flag(self, flag_type: str) -> int:
        """Marks all flags of the given type as resolved. Returns count resolved."""
        count = 0
        for flag in self._shadow_flags:
            if flag.flag_type == flag_type and not flag.resolved:
                flag.resolved = True
                count += 1
        return count

    def _detect_dark_line(self) -> bool:
        """True if phi has declined for 3+ consecutive turns."""
        h = self._phi_history
        if len(h) < 3:
            return False
        return h[-1] < h[-2] < h[-3]

    @staticmethod
    def _select_interrogator_question(phi: float) -> str:
        """Returns the canonical interrogator question nearest to current phi."""
        best_q = _INTERROGATOR_QUESTIONS[0][1]
        best_delta = abs(phi - _INTERROGATOR_QUESTIONS[0][0])
        for threshold, question in _INTERROGATOR_QUESTIONS[1:]:
            delta = abs(phi - threshold)
            if delta < best_delta:
                best_delta = delta
                best_q = question
        return best_q
