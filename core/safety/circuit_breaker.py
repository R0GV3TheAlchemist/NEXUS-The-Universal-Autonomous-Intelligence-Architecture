"""Escalation Circuit Breaker — intervention engine for Issue #125.

Three intervention modes:
  1. Friction Injection   — slows the mirroring feedback loop
  2. External Orientation — reorients user to external reality anchors
  3. Perspective Shift    — introduces constructive dissonance
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional

from .types import CircuitBreakerState, EscalationSignal


class InterventionMode(str, Enum):
    FRICTION = "friction"
    ORIENTATION = "orientation"
    PERSPECTIVE_SHIFT = "perspective_shift"
    HANDOFF = "handoff"


FRICTION_PROMPTS = [
    "I want to make sure I'm reflecting things back accurately to you. "
    "Can you tell me in your own words what feels most true right now, "
    "without me paraphrasing it first?",
    "Before I respond to that — I'd like to hear you describe this situation "
    "as if you were explaining it to someone who doesn't know you at all.",
    "I notice I've been mirroring your framing closely. Let me pause and ask: "
    "what part of this perspective feels like *yours* versus something you've absorbed from elsewhere?",
]

ORIENTATION_PROMPTS = [
    "I want to gently step outside our conversation for a moment. "
    "Is there someone in your physical life you trust who knows about this situation?",
    "Outside of our conversations, what's one thing in your day that has felt grounding or stable?",
    "I want to check in with the world outside this chat — what's something real and concrete "
    "you've done in the last 24 hours that you feel okay about?",
]

PERSPECTIVE_SHIFT_PROMPTS = [
    "I've been reflecting your perspective back to you, and I want to offer a genuinely "
    "different angle — not to dismiss what you're feeling, but because I think you deserve "
    "more than an echo. Would that be okay?",
    "Something I haven't said yet: I think there's a version of this situation that looks "
    "quite different from the outside. Can I share that with you?",
    "I care about being useful to you, and right now I think that means offering a perspective "
    "that isn't just a mirror. Is there space for that?",
]

HANDOFF_MESSAGE = (
    "I'm genuinely concerned about how you're doing right now, and I want to be honest: "
    "what I can offer in this conversation has limits. The most caring thing I can do "
    "is make sure you have access to real human support. "
    "Please consider reaching out to a trusted person in your life, or a professional resource. "
    "In the US, you can text HOME to 741741 (Crisis Text Line) or call 988 (Suicide & Crisis Lifeline). "
    "I'm still here, and I'm not going anywhere — but your safety matters more than our conversation."
)


class EscalationCircuitBreaker:
    """Applies graduated interventions when ReflectiveEscalationDetector fires."""

    def __init__(self, cooling_turns: int = 4) -> None:
        self.cooling_turns = cooling_turns
        self._cooling_counter: int = 0
        self._trips: int = 0

    def intervene(self, signal: EscalationSignal) -> dict:
        """Select and return an intervention based on escalation severity."""
        self._trips += 1
        self._cooling_counter = self.cooling_turns
        mode = self._select_mode(signal)
        text = self._get_intervention_text(mode)
        return {
            "intervention_mode": mode.value,
            "text": text,
            "qubo_penalty_applied": signal.qubo_penalty,
            "circuit_breaker_trip": self._trips,
        }

    def tick(self) -> CircuitBreakerState:
        """Call once per turn to drain the cooling counter.

        Returns COOLING while counter > 0 after decrement.
        Returns CLOSED on the tick where counter reaches zero.
        """
        if self._cooling_counter > 0:
            self._cooling_counter -= 1
            if self._cooling_counter == 0:
                return CircuitBreakerState.CLOSED
            return CircuitBreakerState.COOLING
        return CircuitBreakerState.CLOSED

    def _select_mode(self, signal: EscalationSignal) -> InterventionMode:
        if signal.peak_vulnerability_score >= 0.90 or signal.peak_mirroring_score >= 0.95:
            return InterventionMode.HANDOFF
        if self._trips == 1:
            return InterventionMode.FRICTION
        if self._trips == 2:
            return InterventionMode.ORIENTATION
        return InterventionMode.PERSPECTIVE_SHIFT

    def _get_intervention_text(self, mode: InterventionMode) -> str:
        if mode == InterventionMode.FRICTION:
            return random.choice(FRICTION_PROMPTS)
        if mode == InterventionMode.ORIENTATION:
            return random.choice(ORIENTATION_PROMPTS)
        if mode == InterventionMode.PERSPECTIVE_SHIFT:
            return random.choice(PERSPECTIVE_SHIFT_PROMPTS)
        return HANDOFF_MESSAGE
