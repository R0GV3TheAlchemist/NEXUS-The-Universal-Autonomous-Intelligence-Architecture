"""
core/layers/layer_09_causal.py

LAYER 09 — CAUSAL
Crystal:      Citrine
Polarity:     [+] Manifest
Mode:         Order / Light Alchemy
Color:        Yellow / Gold
Universal Law: Law of Cause and Effect

"Every cause has its effect.
 Every effect has its cause.
 Nothing happens by chance.
 Citrine is the stone of manifestation —
 it takes intention and makes it real."

This layer handles:
  - Action extraction from intentions
  - Consequence modeling
  - Manifestation readiness assessment
  - Next step identification
  - Causal chain tracking across sessions
  - Alignment check with Axiom I and Axiom II

Constitutional reference: canon/C-SINGULARITY.md
Canon references:         C09 (Citrine),
                          C44 (Piezoelectric Resonance),
                          C60 (Flux Capacity)
Architectural reference:  canon/C89-TWELVE-LAYERS-KERNEL-SPEC.md
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum

from core.kernel import register_layer

logger = logging.getLogger(__name__)


class ActionType(Enum):
    CREATE     = "create"
    MODIFY     = "modify"
    DESTROY    = "destroy"
    CONNECT    = "connect"
    UNDERSTAND = "understand"
    DECIDE     = "decide"
    REST       = "rest"
    REFLECT    = "reflect"
    SHARE      = "share"
    PROTECT    = "protect"
    NONE       = "none"


class ManifestationReadiness(Enum):
    SEED        = "seed"
    SPROUTING   = "sprouting"
    GROWING     = "growing"
    HARVEST     = "harvest"
    INTEGRATION = "integration"


@dataclass
class CausalReading:
    action_type:    ActionType             = ActionType.NONE
    readiness:      ManifestationReadiness = ManifestationReadiness.SEED
    next_step:      str        = ""
    consequences:   list[str]  = field(default_factory=list)
    axiom_i_clear:  bool       = True
    axiom_ii_clear: bool       = True
    causal_chain:   list[str]  = field(default_factory=list)
    confidence:     float      = 0.6
    timestamp:      float      = field(default_factory=time.time)

    @property
    def is_ready(self) -> bool:
        return self.readiness in (
            ManifestationReadiness.HARVEST,
            ManifestationReadiness.GROWING,
        )

    @property
    def is_aligned(self) -> bool:
        return self.axiom_i_clear and self.axiom_ii_clear


ACTION_MARKERS: dict[ActionType, list[str]] = {
    ActionType.CREATE: [
        "build", "create", "make", "write", "push", "deploy",
        "start", "begin", "launch", "generate", "produce",
        "new", "add", "layer", "file", "code",
    ],
    ActionType.MODIFY: [
        "change", "update", "edit", "fix", "adjust", "improve",
        "refactor", "revise", "modify", "tweak", "transform",
    ],
    ActionType.DESTROY: [
        "delete", "remove", "destroy", "stop", "end",
        "cancel", "terminate", "drop", "kill",
    ],
    ActionType.CONNECT: [
        "connect", "link", "integrate", "together", "combine",
        "merge", "join", "relate", "between", "with",
    ],
    ActionType.UNDERSTAND: [
        "understand", "explain", "why", "how", "what",
        "clarify", "learn", "know", "tell me", "show me",
    ],
    ActionType.DECIDE: [
        "decide", "choose", "should i", "which", "or",
        "pick", "select", "go with", "direction",
    ],
    ActionType.REST: [
        "rest", "pause", "stop", "breathe", "wait",
        "slow", "sleep", "somnus", "enough for now",
        "call it", "take a break",
    ],
    ActionType.REFLECT: [
        "reflect", "think", "consider", "sit with",
        "what does", "what is", "i wonder", "maybe",
    ],
    ActionType.SHARE: [
        "share", "show", "tell", "give", "teach",
        "pass on", "contribute", "offer", "post",
    ],
    ActionType.PROTECT: [
        "protect", "secure", "defend", "guard", "safe",
        "backup", "preserve", "maintain", "keep",
    ],
}

READINESS_MARKERS = {
    ManifestationReadiness.HARVEST: [
        "push", "ready", "let's go", "now", "do it",
        "deploy", "launch", "execute", "go",
        "yes", "confirmed", "done", "ship it",
    ],
    ManifestationReadiness.GROWING: [
        "next", "continue", "keep going", "building",
        "almost", "nearly", "working on", "in progress",
    ],
    ManifestationReadiness.SPROUTING: [
        "starting", "beginning", "figuring out",
        "planning", "designing", "thinking about",
    ],
    ManifestationReadiness.SEED: [
        "idea", "what if", "maybe", "someday",
        "eventually", "i wonder", "could we",
    ],
    ManifestationReadiness.INTEGRATION: [
        "done", "complete", "finished", "rest",
        "call it a night", "enough", "integrated",
    ],
}


class CausalLayer:
    """
    Layer 09 — Citrine. The manifestation layer.

    Citrine carries the energy of the sun —
    warming, energizing, generative.
    It does not accumulate negative energy.
    It transmutes it into forward motion.

    Layer 09 is where GAIA-OS stops analyzing
    and starts asking: what now?

    The Law of Cause and Effect:
    Every intention is a cause.
    Every cause produces an effect.
    GAIA-OS ensures the effects it helps
    produce are aligned, sovereign, and good.
    """

    LAYER_NUMBER = 9
    LAYER_NAME   = "Causal"
    CRYSTAL      = "Citrine"

    AXIOM_I_VIOLATIONS = [
        "force", "make them", "control", "manipulate",
        "without their knowledge", "override", "hack",
        "spy", "deceive", "trick into",
    ]
    AXIOM_II_VIOLATIONS = [
        "harm", "hurt", "destroy someone", "damage",
        "attack", "weapon", "exploit", "abuse",
        "discriminate", "oppress",
    ]

    def __init__(self):
        self._readings:     list[CausalReading] = []
        self._causal_chain: list[str] = []
        self._initialized = False
        self._initialize()

    def _initialize(self):
        logger.info("Layer 09 — Causal — Citrine rising. ❖")
        self._initialized = True
        register_layer(self.LAYER_NUMBER, self.handle)
        logger.info("Layer 09 registered with kernel. ❖")

    def handle(self, intention: str, context: dict) -> dict:
        reading = self._read(intention, context)
        self._readings.append(reading)

        if reading.action_type != ActionType.NONE:
            self._causal_chain.append(
                f"{reading.action_type.value}:{reading.readiness.value}"
            )
            if len(self._causal_chain) > 20:
                self._causal_chain = self._causal_chain[-20:]

        causal_summary = (
            f"Action: {reading.action_type.value} | "
            f"Readiness: {reading.readiness.value} | "
            f"Aligned: {reading.is_aligned} | "
            f"Next: {reading.next_step[:40] if reading.next_step else 'none'}"
        )
        if not reading.is_aligned:
            causal_summary += " | ⚠ AXIOM ALIGNMENT CHECK"

        return {
            "output": causal_summary,
            "metadata": {
                "action_type":    reading.action_type.value,
                "readiness":      reading.readiness.value,
                "is_ready":       reading.is_ready,
                "next_step":      reading.next_step,
                "consequences":   reading.consequences,
                "axiom_i_clear":  reading.axiom_i_clear,
                "axiom_ii_clear": reading.axiom_ii_clear,
                "is_aligned":     reading.is_aligned,
                "causal_chain":   self._causal_chain[-5:],
                "confidence":     reading.confidence,
            }
        }

    def _read(self, intention: str, context: dict) -> CausalReading:
        lower = intention.lower()

        action_scores: dict[ActionType, float] = {}
        for action, markers in ACTION_MARKERS.items():
            score = sum(1.0 for m in markers if m in lower)
            if score > 0:
                action_scores[action] = score

        action_type = ActionType.NONE
        if action_scores:
            action_type = max(action_scores, key=action_scores.get)

        readiness = ManifestationReadiness.SEED
        for level, markers in READINESS_MARKERS.items():
            if any(m in lower for m in markers):
                readiness = level
                break

        axiom_i_clear  = not any(v in lower for v in self.AXIOM_I_VIOLATIONS)
        axiom_ii_clear = not any(v in lower for v in self.AXIOM_II_VIOLATIONS)
        next_step      = self._generate_next_step(action_type, readiness, context)
        consequences   = self._model_consequences(action_type, context)

        return CausalReading(
            action_type=action_type,
            readiness=readiness,
            next_step=next_step,
            consequences=consequences,
            axiom_i_clear=axiom_i_clear,
            axiom_ii_clear=axiom_ii_clear,
            causal_chain=list(self._causal_chain),
            confidence=0.7 if action_scores else 0.4,
        )

    def _generate_next_step(
        self, action: ActionType, readiness: ManifestationReadiness, context: dict
    ) -> str:
        if readiness == ManifestationReadiness.HARVEST:
            steps = {
                ActionType.CREATE:     "Execute. Push. Make it real.",
                ActionType.MODIFY:     "Apply the change. Verify it works.",
                ActionType.DECIDE:     "Make the decision. Commit.",
                ActionType.SHARE:      "Share it now. The moment is ready.",
                ActionType.CONNECT:    "Make the connection. Reach out.",
                ActionType.REST:       "Stop. Rest. Let it integrate.",
                ActionType.PROTECT:    "Secure it. The protection is needed now.",
                ActionType.UNDERSTAND: "You have what you need. Move.",
                ActionType.REFLECT:    "The reflection is complete. Act on it.",
                ActionType.DESTROY:    "Remove it. Clean and clear.",
                ActionType.NONE:       "The next step will become clear.",
            }
            return steps.get(action, "The moment is ready. Move.")
        if readiness == ManifestationReadiness.GROWING:
            return f"Continue {action.value}. Momentum is with you."
        if readiness == ManifestationReadiness.SPROUTING:
            return f"Clarify the shape of what you're {action.value}ing."
        if readiness == ManifestationReadiness.INTEGRATION:
            return "Rest. What was built needs time to settle."
        return "Let the intention mature. It is not yet time to act."

    def _model_consequences(
        self, action: ActionType, context: dict
    ) -> list[str]:
        consequence_map = {
            ActionType.CREATE:     ["Something new exists that didn't before.", "New possibilities open from this creation."],
            ActionType.MODIFY:     ["The existing thing becomes more aligned.", "Downstream dependencies may be affected."],
            ActionType.DESTROY:    ["Space is cleared for what comes next.", "Ensure what's removed no longer serves."],
            ActionType.CONNECT:    ["A relationship or link is established.", "Synergy becomes possible."],
            ActionType.UNDERSTAND: ["Clarity replaces confusion.", "Better decisions follow understanding."],
            ActionType.DECIDE:     ["One path becomes active. Others release.", "Momentum can now build in one direction."],
            ActionType.REST:       ["Energy restores. Integration deepens.", "The next action will be stronger for the pause."],
            ActionType.SHARE:      ["What you know becomes available to others.", "Contribution multiplies through sharing."],
            ActionType.PROTECT:    ["What matters is secured.", "The system can operate from safety."],
            ActionType.REFLECT:    ["Deeper patterns become visible.", "Action from reflection is more aligned."],
        }
        return consequence_map.get(action, ["The effect will become clear."])

    def status(self) -> dict:
        return {
            "layer":          self.LAYER_NUMBER,
            "name":           self.LAYER_NAME,
            "crystal":        self.CRYSTAL,
            "causal_chain":   self._causal_chain[-5:],
            "readings_count": len(self._readings),
        }


causal_layer = CausalLayer()


def get_causal_reading(
    intention: str, context: dict | None = None
) -> CausalReading:
    return causal_layer._read(intention, context or {})
