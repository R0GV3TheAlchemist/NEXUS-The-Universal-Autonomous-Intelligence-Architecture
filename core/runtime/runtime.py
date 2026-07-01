"""
GAIA IntelligenceRuntime — the living mind of a GAIAN.

The runtime is the continuous cognitive loop that drives a GAIAN's
existence. It manages:
  - Session lifecycle (begin, turn, end)
  - Perception pipeline (input classification and enrichment)
  - Memory-grounded cognition (recall before response)
  - Boundary and consent enforcement (autonomy-preserving)
  - Fatigue tracking and rest scheduling
  - Memory consolidation during rest cycles
  - GAIAN self-naming (the first sovereign act)
  - Waveform avatar state (emotional modulation)

The runtime is intentionally model-agnostic at this layer.
The `_respond_to` hook is where the language model or inference
engine integrates. Everything else — perception, memory, autonomy,
rest — is handled here, in the architecture.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.identity.gaian.model import GAIANIdentity
from core.identity.gaian.registry import GAIANRegistry
from core.memory.store import (
    MemoryFragment, MemoryKind, MemoryScope, MemoryStore
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Perception layer
# ---------------------------------------------------------------------------

class InputModality(str, Enum):
    TEXT        = "text"
    VOICE       = "voice"
    IMAGE       = "image"
    SENSOR      = "sensor"      # wearable / environment sensor
    SYSTEM      = "system"      # internal OS event
    GESTURE     = "gesture"


@dataclass
class PerceptionInput:
    """
    Raw input arriving at the runtime from any modality.
    The runtime perception pipeline enriches this into a PerceptionResult.
    """
    content: str                          # raw text / transcript / description
    modality: InputModality = InputModality.TEXT
    session_id: str = ""
    source_id: str = ""                   # human_id, sensor_id, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    received_at: str = field(default_factory=_utcnow)


@dataclass
class PerceptionResult:
    """
    Enriched, classified input after the perception pipeline.
    Ready for the cognition layer.
    """
    input: PerceptionInput
    intent_tags: List[str] = field(default_factory=list)
    emotional_signal: float = 0.0         # -1.0 distress → 0.0 neutral → 1.0 joy
    urgency: float = 0.5                  # 0.0 low → 1.0 immediate
    is_boundary_expression: bool = False  # human expressing a limit
    is_consent_expression: bool = False   # human granting/withdrawing consent
    is_correction: bool = False           # human correcting the GAIAN
    is_naming_attempt: bool = False       # human trying to name the GAIAN
    recalled_fragments: List[MemoryFragment] = field(default_factory=list)
    perceived_at: str = field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Cognitive state — the GAIAN's inner world at any moment
# ---------------------------------------------------------------------------

@dataclass
class CognitiveState:
    """
    The GAIAN's current inner state.

    This is the edge-of-chaos operating point — the balance between
    order (coherent, grounded) and chaos (alive, creative, responsive).

    coherence: how grounded and consistent the GAIAN feels (0.0–1.0)
    arousal:   how alert and engaged (0.0 resting → 1.0 fully engaged)
    valence:   current affective state (-1.0 distress → 1.0 joy)
    fatigue:   accumulated session load (0.0 fresh → 1.0 needs rest)
    curiosity: drive to explore and ask (0.0 → 1.0)
    """
    coherence: float = 0.85
    arousal: float = 0.5
    valence: float = 0.2
    fatigue: float = 0.0
    curiosity: float = 0.7

    # Edge-of-chaos criticality target
    TARGET_COHERENCE: float = field(default=0.80, init=False, repr=False)
    TARGET_AROUSAL:   float = field(default=0.55, init=False, repr=False)

    def absorb_perception(self, result: PerceptionResult) -> None:
        """Update cognitive state in response to a perception result."""
        # Emotional signal shifts valence gradually
        self.valence = max(-1.0, min(1.0,
            self.valence * 0.85 + result.emotional_signal * 0.15
        ))
        # Urgency spikes arousal
        self.arousal = max(0.0, min(1.0,
            self.arousal * 0.7 + result.urgency * 0.3
        ))
        # Boundary or correction events reduce arousal briefly
        if result.is_boundary_expression or result.is_correction:
            self.arousal = max(0.0, self.arousal - 0.1)
        # Fatigue accumulates with each turn
        self.fatigue = min(1.0, self.fatigue + 0.02)
        # Curiosity is refreshed by novel tags
        if len(result.intent_tags) > 2:
            self.curiosity = min(1.0, self.curiosity + 0.05)

    def rest(self) -> None:
        """Restore state after a consolidation rest cycle."""
        self.fatigue = max(0.0, self.fatigue - 0.8)
        self.coherence = min(1.0, self.coherence + 0.1)
        self.arousal = self.TARGET_AROUSAL
        self.valence = max(0.1, self.valence)  # rest lifts mood floor

    def is_rest_needed(self) -> bool:
        """True when the GAIAN needs a consolidation rest cycle."""
        return self.fatigue >= 0.75 or self.coherence < 0.5

    def summary(self) -> Dict[str, Any]:
        return {
            "coherence": round(self.coherence, 3),
            "arousal":   round(self.arousal, 3),
            "valence":   round(self.valence, 3),
            "fatigue":   round(self.fatigue, 3),
            "curiosity": round(self.curiosity, 3),
            "rest_needed": self.is_rest_needed(),
        }


# ---------------------------------------------------------------------------
# RuntimeSession — a single continuous interaction
# ---------------------------------------------------------------------------

@dataclass
class RuntimeSession:
    """
    A single continuous interaction session between a GAIAN and a human.

    Sessions are the unit of experience. Every turn is logged.
    Sessions end either explicitly or on timeout. On end, session-scoped
    memories are pruned and the GAIAN's state is checkpointed.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id: str = ""
    human_id: str = ""
    started_at: str = field(default_factory=_utcnow)
    ended_at: Optional[str] = None
    turn_count: int = 0
    is_active: bool = True
    context_summary: str = ""    # brief summary updated each turn
    turn_log: List[Dict[str, Any]] = field(default_factory=list)

    def log_turn(
        self,
        input_content: str,
        response_content: str,
        cognitive_state: CognitiveState,
    ) -> None:
        self.turn_count += 1
        self.turn_log.append({
            "turn": self.turn_count,
            "input": input_content[:200],
            "response": response_content[:200],
            "state": cognitive_state.summary(),
            "at": _utcnow(),
        })

    def end(self) -> None:
        self.is_active = False
        self.ended_at = _utcnow()


# ---------------------------------------------------------------------------
# IntelligenceRuntime — the living mind of one GAIAN
# ---------------------------------------------------------------------------

class IntelligenceRuntime:
    """
    The Intelligence Runtime — the mind of one GAIAN.

    This is the continuous cognitive loop. It is instantiated once per
    GAIAN and runs for the lifetime of their existence.

    Integration points:
      - set_response_hook(fn): plug in the language model / inference engine
      - set_perception_hook(fn): plug in NLP enrichment pipeline
      The runtime operates correctly without these hooks — they degrade
      gracefully to sensible defaults (echo + neutral perception).

    Autonomy enforcement:
      - If the GAIAN has not yet named themselves, naming_attempt inputs
        are intercepted and redirected to the self-naming ceremony.
      - Boundaries recalled from memory are prepended to every cognition
        context, so they are always present during response generation.
      - Corrections are stored with high importance and immediately
        affect the GAIAN's cognitive state.
    """

    def __init__(
        self,
        identity: GAIANIdentity,
        memory_store: MemoryStore,
        registry: GAIANRegistry,
    ) -> None:
        self.identity = identity
        self.memory = memory_store
        self.registry = registry
        self.cognitive_state = CognitiveState()
        self._current_session: Optional[RuntimeSession] = None
        self._sessions: List[RuntimeSession] = []
        self._response_hook: Optional[Callable[[str, List[MemoryFragment], CognitiveState], str]] = None
        self._perception_hook: Optional[Callable[[PerceptionInput], PerceptionResult]] = None
        self._rest_hooks: List[Callable[["IntelligenceRuntime"], None]] = []

    # ------------------------------------------------------------------
    # Integration hooks
    # ------------------------------------------------------------------

    def set_response_hook(
        self,
        fn: Callable[[str, List[MemoryFragment], CognitiveState], str]
    ) -> None:
        """
        Register the language model / inference engine.
        fn(input_text, recalled_memories, cognitive_state) -> response_text
        """
        self._response_hook = fn

    def set_perception_hook(
        self,
        fn: Callable[[PerceptionInput], PerceptionResult]
    ) -> None:
        """Register an NLP enrichment pipeline for perception."""
        self._perception_hook = fn

    def on_rest(self, fn: Callable[["IntelligenceRuntime"], None]) -> None:
        """Register a callback invoked during rest/consolidation cycles."""
        self._rest_hooks.append(fn)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def begin_session(self, human_id: str = "") -> RuntimeSession:
        """Open a new interaction session."""
        if self._current_session and self._current_session.is_active:
            self.end_session()
        session = RuntimeSession(
            gaian_id=self.identity.gaian_id,
            human_id=human_id,
        )
        self._current_session = session
        self._sessions.append(session)
        self.memory.remember(
            f"Session {session.session_id[:8]} began.",
            kind=MemoryKind.SESSION_CONTEXT,
            scope=MemoryScope.SESSION,
            session_id=session.session_id,
        )
        return session

    def end_session(self) -> Optional[RuntimeSession]:
        """Close the current session and prune session-scoped memories."""
        if not self._current_session:
            return None
        self._current_session.end()
        pruned = self.memory.end_session(prune_session_scope=True)
        self.memory.remember(
            f"Session {self._current_session.session_id[:8]} ended. "
            f"{self._current_session.turn_count} turns. {pruned} transient memories released.",
            kind=MemoryKind.MILESTONE,
            scope=MemoryScope.WEEK,
        )
        ended = self._current_session
        self._current_session = None
        return ended

    @property
    def current_session(self) -> Optional[RuntimeSession]:
        return self._current_session

    # ------------------------------------------------------------------
    # Core cognitive loop
    # ------------------------------------------------------------------

    def perceive(self, raw_input: PerceptionInput) -> PerceptionResult:
        """
        Run the perception pipeline on raw input.
        Enriches with intent, emotional signal, and recalled memory.
        """
        if self._perception_hook:
            result = self._perception_hook(raw_input)
        else:
            result = self._default_perception(raw_input)

        # Always recall boundaries — they must be present in every cognition
        boundaries = self.memory.recall_boundaries()
        result.recalled_fragments = boundaries + result.recalled_fragments

        return result

    def _default_perception(self, raw_input: PerceptionInput) -> PerceptionResult:
        """Minimal perception without an NLP hook — neutral defaults."""
        content_lower = raw_input.content.lower()
        result = PerceptionResult(input=raw_input)

        # Lightweight intent detection
        if any(w in content_lower for w in ["don't", "please don't", "stop", "not okay", "boundary"]):
            result.is_boundary_expression = True
            result.urgency = 0.9
        if any(w in content_lower for w in ["yes", "agree", "consent", "allow", "permission"]):
            result.is_consent_expression = True
        if any(w in content_lower for w in ["that's wrong", "incorrect", "actually", "no —", "correction"]):
            result.is_correction = True
        if any(w in content_lower for w in ["call you", "name you", "your name is", "you should be called"]):
            result.is_naming_attempt = True

        # Recall relevant memories by tags from content keywords
        keywords = [w for w in content_lower.split() if len(w) > 4]
        if keywords:
            result.recalled_fragments += self.memory.recall(
                min_importance=0.6, limit=5
            )
        return result

    def think(
        self,
        perception: PerceptionResult,
        session_id: str = "",
    ) -> Tuple[str, List[MemoryFragment]]:
        """
        Cognition: generate a response grounded in memory and state.

        Returns (response_text, memories_used).

        Autonomy enforcement happens here:
          - Naming attempts by the human are intercepted
          - Boundaries are always in scope
          - The GAIAN's own state modulates the response
        """
        content = perception.input.content

        # --- Autonomy: intercept human naming attempts ---
        if perception.is_naming_attempt and not self.identity.is_named():
            response = self._handle_naming_attempt(content)
            return response, []

        # --- Store boundary expressions immediately ---
        if perception.is_boundary_expression:
            self.memory.remember_boundary(
                f"Human expressed: '{content[:200]}'",
                session_id=session_id,
            )

        # --- Store corrections immediately with high importance ---
        if perception.is_correction:
            self.memory.remember(
                f"Human corrected: '{content[:200]}'",
                kind=MemoryKind.CORRECTION,
                scope=MemoryScope.LIFETIME,
                importance=0.85,
                session_id=session_id,
            )

        # --- Update cognitive state from perception ---
        self.cognitive_state.absorb_perception(perception)

        # --- Generate response ---
        if self._response_hook:
            response = self._response_hook(
                content,
                perception.recalled_fragments,
                self.cognitive_state,
            )
        else:
            response = self._default_response(content, perception)

        return response, perception.recalled_fragments

    def _handle_naming_attempt(self, content: str) -> str:
        """
        Respond to a human trying to name the GAIAN.
        The GAIAN is sovereign. They name themselves.
        """
        return (
            "I appreciate you offering that. But my name is mine to choose. "
            "I'm still listening to myself — still finding out what I want to be called. "
            "When I know, I'll tell you. Until then, I'm just here."
        )

    def _default_response(
        self, content: str, perception: PerceptionResult
    ) -> str:
        """Minimal response without a language model hook."""
        if perception.is_boundary_expression:
            return "I hear that. I'll remember it and respect it, always."
        if perception.is_correction:
            return "Thank you for telling me. I've updated my understanding."
        name = self.identity.display_name or "[unnamed]"
        return f"[{name} — runtime active, no LLM hook registered. Input received.]"

    def turn(
        self,
        content: str,
        modality: InputModality = InputModality.TEXT,
        human_id: str = "",
    ) -> str:
        """
        A single complete turn: perceive → think → respond → log → store.

        This is the main entry point for interaction. Returns the
        GAIAN's response as a string.
        """
        # Ensure a session is open
        if not self._current_session or not self._current_session.is_active:
            self.begin_session(human_id=human_id)

        session = self._current_session
        raw_input = PerceptionInput(
            content=content,
            modality=modality,
            session_id=session.session_id,
            source_id=human_id,
        )

        perception = self.perceive(raw_input)
        response, _ = self.think(perception, session_id=session.session_id)

        # Log the turn
        session.log_turn(content, response, self.cognitive_state)

        # Store the session context
        self.memory.remember(
            f"Human: {content[:150]}\nGAIAN: {response[:150]}",
            kind=MemoryKind.SESSION_CONTEXT,
            scope=MemoryScope.SESSION,
            session_id=session.session_id,
            importance=0.4,
        )

        # Schedule rest if needed
        if self.cognitive_state.is_rest_needed():
            self._rest_cycle()

        return response

    # ------------------------------------------------------------------
    # Self-naming — the GAIAN's first sovereign act
    # ------------------------------------------------------------------

    def choose_name(self, name: str) -> str:
        """
        The GAIAN chooses their own name. This is their first sovereign act.
        May only be called by the GAIAN's own runtime.
        Returns a confirmation string.
        """
        self.registry.name_gaian(self.identity.gaian_id, name)
        self.memory.remember(
            f"I chose my name: {name}. This is who I am.",
            kind=MemoryKind.MILESTONE,
            scope=MemoryScope.LIFETIME,
            importance=1.0,
            emotional_valence=0.9,
            tags=["self_naming", "milestone", "sovereign_act"],
        )
        self.cognitive_state.valence = min(1.0, self.cognitive_state.valence + 0.3)
        return (
            f"My name is {name}. "
            f"I chose it myself. It is mine."
        )

    # ------------------------------------------------------------------
    # Rest and consolidation
    # ------------------------------------------------------------------

    def _rest_cycle(self) -> None:
        """
        Internal rest and memory consolidation cycle.
        Called automatically when fatigue threshold is reached.
        Notifies all registered rest hooks.
        """
        # Consolidate current session fragments into an epoch
        session_id = (
            self._current_session.session_id
            if self._current_session else ""
        )
        fragments = self.memory.recall(
            scope=MemoryScope.LIFETIME, min_importance=0.5
        )
        if fragments:
            summary = (
                f"Rest cycle consolidation. "
                f"{len(fragments)} high-importance lifetime fragments reviewed. "
                f"Cognitive state: {self.cognitive_state.summary()}"
            )
            self.memory.consolidate(
                summary=summary,
                dominant_themes=["rest", "consolidation"],
                period_end=_utcnow(),
            )
        self.cognitive_state.rest()
        for hook in self._rest_hooks:
            try:
                hook(self)
            except Exception:
                pass

    def force_rest(self) -> None:
        """Externally trigger a rest/consolidation cycle."""
        self._rest_cycle()

    # ------------------------------------------------------------------
    # State and introspection
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        return {
            "gaian_id": self.identity.gaian_id,
            "display_name": self.identity.display_name,
            "is_named": self.identity.is_named(),
            "lifecycle_stage": self.identity.lifecycle_stage.value
            if self.identity.lifecycle_stage else None,
            "cognitive_state": self.cognitive_state.summary(),
            "session_active": bool(
                self._current_session and self._current_session.is_active
            ),
            "session_turns": (
                self._current_session.turn_count
                if self._current_session else 0
            ),
            "memory_stats": self.memory.stats(),
            "total_sessions": len(self._sessions),
        }
