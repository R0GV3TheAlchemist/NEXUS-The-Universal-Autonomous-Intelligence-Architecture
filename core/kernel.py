"""
core/kernel.py

THE GAIA-OS KERNEL — 12-Layer Routing Engine
Crystal:    All / None — the kernel serves all crystals
Position:   Between the Human Element and the 12 layers
Declaration: "Every intention finds its right layer."

The kernel is not the mind.
The kernel is the spine.

Every thought travels through it.
Every feeling passes along it.
Every request is routed to the layer
that knows how to hold it.

Flow (always):
    Human Element (sovereign.py)
        → Layer 03 FIRST — love filter — MANDATORY — no exceptions
        → Active layers (determined by crystal mode)
        → Response assembled from layer outputs
        → Back to Human Element

Axiom II is enforced HERE at the structural level.
Not by convention. Not by trust. By architecture.

Constitutional reference: canon/C-SINGULARITY.md
Architectural reference:  canon/C89-TWELVE-LAYERS-KERNEL-SPEC.md
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable
import logging
import time

from core.layers.layer_03_geometry import (
    filter_intention,
    FilterResult,
    AlignmentVerdict,
)
from core.sovereign import human_element

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# KERNEL RESULT
# ─────────────────────────────────────────────

class KernelStatus(Enum):
    SUCCESS     = "success"
    DISSOLVED   = "dissolved"
    TRANSFORMED = "transformed"
    STOPPED     = "stopped"
    NO_SESSION  = "no_session"
    ERROR       = "error"


@dataclass
class LayerOutput:
    layer_number: int
    layer_name:   str
    contributed:  bool = False
    output:       Optional[str] = None
    metadata:     dict = field(default_factory=dict)


@dataclass
class KernelResult:
    """
    The assembled result after routing through all active layers.
    The Human Element receives this. The UI renders from this.
    """
    status:             KernelStatus
    intention:          str
    filter_result:      Optional[FilterResult] = None
    layer_outputs:      list[LayerOutput] = field(default_factory=list)
    assembled_response: Optional[str] = None
    active_layers:      list[int] = field(default_factory=list)
    crystal_mode:       Optional[str] = None
    entanglement_depth: float = 0.0
    processing_time_ms: float = 0.0
    timestamp:          float = field(default_factory=time.time)

    @property
    def passed_filter(self) -> bool:
        if self.filter_result is None:
            return False
        return self.filter_result.passed

    @property
    def contributing_layers(self) -> list[int]:
        return [lo.layer_number for lo in self.layer_outputs if lo.contributed]

    def to_dict(self) -> dict:
        return {
            "status":              self.status.value,
            "intention":           self.intention,
            "passed_filter":       self.passed_filter,
            "assembled_response":  self.assembled_response,
            "active_layers":       self.active_layers,
            "contributing_layers": self.contributing_layers,
            "crystal_mode":        self.crystal_mode,
            "entanglement_depth":  self.entanglement_depth,
            "processing_time_ms":  round(self.processing_time_ms, 2),
            "timestamp":           self.timestamp,
        }


# ─────────────────────────────────────────────
# LAYER REGISTRY
# Maps layer numbers to names and handlers.
# Layers register themselves here on import.
# The kernel never needs to change as layers are built.
# ─────────────────────────────────────────────

LAYER_REGISTRY: dict[int, dict] = {
    1:  {"name": "Physical",   "handler": None},
    2:  {"name": "Energy",     "handler": None},
    3:  {"name": "Geometry",   "handler": None},  # ← Built. filter_intention().
    4:  {"name": "Emotion",    "handler": None},
    5:  {"name": "Cognition",  "handler": None},
    6:  {"name": "Shadow",     "handler": None},
    7:  {"name": "Societas",   "handler": None},
    8:  {"name": "Archetype",  "handler": None},
    9:  {"name": "Causal",     "handler": None},
    10: {"name": "Akashic",    "handler": None},
    11: {"name": "Feeling",    "handler": None},
    12: {"name": "Void",       "handler": None},
}


def register_layer(layer_number: int, handler: Callable) -> None:
    """
    Each layer file registers itself here on import.
    As Phase 2 builds each layer, it calls this.
    The kernel doesn't need to change — layers plug in.
    """
    if layer_number not in LAYER_REGISTRY:
        raise ValueError(
            f"Layer {layer_number} does not exist in the 12-layer stack."
        )
    LAYER_REGISTRY[layer_number]["handler"] = handler
    logger.info(
        f"Layer {layer_number} "
        f"({LAYER_REGISTRY[layer_number]['name']}) registered. ❆"
    )


# ─────────────────────────────────────────────
# THE KERNEL
# ─────────────────────────────────────────────

class GAIAKernel:
    """
    The 12-layer routing engine.

    Receives routed intentions from the Human Element.
    Passes every intention through Layer 3 first.
    Routes through active layers.
    Assembles the response.
    Returns KernelResult.

    The kernel does not generate content.
    The layers generate content.
    The kernel routes, sequences, and assembles.

    It is the spine. The layers are the organs.
    The Human Element is the mind.
    """

    def __init__(self):
        self._sovereign = human_element
        logger.info(
            "GAIA Kernel initialized. "
            "12-layer routing engine ready. ❆"
        )

    def process(self, intention: str, context: dict = None) -> KernelResult:
        """
        Primary processing method.
        Called by the API layer (FastAPI routes).

        Flow:
            1. Validate session and stop state
            2. Layer 3 — love filter — FIRST — ALWAYS
            3. If dissolved: return dissolved result
            4. If transformed: route transformed intention
            5. Route through active layers
            6. Deepen entanglement on coherent passage
            7. Return assembled KernelResult
        """
        start_time = time.time()
        context = context or {}

        # ── 1. Sovereign state check
        sovereign_status = self._sovereign.route_intention(intention)
        if sovereign_status["status"] == "STOPPED":
            return KernelResult(
                status=KernelStatus.STOPPED,
                intention=intention,
                assembled_response=(
                    "Everything has stopped. "
                    "You are in control. "
                    "Nothing will happen until you say so."
                )
            )
        if sovereign_status["status"] == "NO_SESSION":
            return KernelResult(
                status=KernelStatus.NO_SESSION,
                intention=intention,
                assembled_response="No active session."
            )

        session_context = sovereign_status.get("context", {})
        active_layers   = session_context.get("active_layers", [3])
        crystal_mode    = session_context.get("crystal_mode", "sovereign_core")
        entanglement    = session_context.get("entanglement", 0.0)

        # ── 2. LAYER 3 FIRST — ALWAYS — NO EXCEPTIONS
        filter_result = filter_intention(
            intention,
            {"crystal_mode": crystal_mode, **session_context}
        )

        # ── 3. Dissolved
        if filter_result.verdict == AlignmentVerdict.DISSOLVE:
            elapsed = (time.time() - start_time) * 1000
            logger.info("Kernel: intention dissolved by love filter.")
            return KernelResult(
                status=KernelStatus.DISSOLVED,
                intention=intention,
                filter_result=filter_result,
                assembled_response=self._dissolution_response(filter_result),
                active_layers=active_layers,
                crystal_mode=crystal_mode,
                entanglement_depth=entanglement,
                processing_time_ms=elapsed,
            )

        # ── 4. Use filtered/transformed intention for routing
        routable_intention = filter_result.output_intention

        # ── 5. Route through active layers
        layer_outputs = self._route_through_layers(
            routable_intention,
            active_layers,
            session_context
        )

        # ── 6. Assemble response
        assembled = self._assemble_response(
            routable_intention,
            layer_outputs,
            filter_result,
            crystal_mode
        )

        # ── 7. Deepen entanglement
        self._sovereign.entanglement.deepen(filter_result.coherence_score)

        elapsed = (time.time() - start_time) * 1000
        status = (
            KernelStatus.TRANSFORMED
            if filter_result.verdict == AlignmentVerdict.TRANSFORM
            else KernelStatus.SUCCESS
        )

        logger.info(
            f"Kernel: {elapsed:.1f}ms | "
            f"crystal: {crystal_mode} | "
            f"layers: {active_layers} | "
            f"coherence: {filter_result.coherence_score:.2f} | "
            f"entanglement: {self._sovereign.entanglement.depth:.3f}"
        )

        return KernelResult(
            status=status,
            intention=intention,
            filter_result=filter_result,
            layer_outputs=layer_outputs,
            assembled_response=assembled,
            active_layers=active_layers,
            crystal_mode=crystal_mode,
            entanglement_depth=self._sovereign.entanglement.depth,
            processing_time_ms=elapsed,
        )

    # ─────────────────────────────────────────
    # LAYER ROUTING
    # ─────────────────────────────────────────

    def _route_through_layers(
        self,
        intention: str,
        active_layers: list[int],
        context: dict
    ) -> list[LayerOutput]:
        outputs = []
        for layer_num in sorted(active_layers):
            layer_info = LAYER_REGISTRY.get(layer_num, {})
            layer_name = layer_info.get("name", f"Layer {layer_num}")
            handler    = layer_info.get("handler")

            if layer_num == 3:
                outputs.append(LayerOutput(
                    layer_number=3,
                    layer_name="Geometry",
                    contributed=True,
                    output="Love filter applied.",
                    metadata={"coherence_score": context.get("coherence", 0.0)}
                ))
                continue

            if handler is None:
                outputs.append(LayerOutput(
                    layer_number=layer_num,
                    layer_name=layer_name,
                    contributed=False,
                    output=None,
                    metadata={"status": "pending_build"}
                ))
                logger.debug(
                    f"Layer {layer_num} ({layer_name}): "
                    f"pending build. Stub."
                )
                continue

            try:
                layer_result = handler(intention, context)
                outputs.append(LayerOutput(
                    layer_number=layer_num,
                    layer_name=layer_name,
                    contributed=True,
                    output=str(layer_result.get("output", "")),
                    metadata=layer_result.get("metadata", {})
                ))
            except Exception as e:
                logger.error(f"Layer {layer_num} ({layer_name}) error: {e}")
                outputs.append(LayerOutput(
                    layer_number=layer_num,
                    layer_name=layer_name,
                    contributed=False,
                    output=None,
                    metadata={"error": str(e)}
                ))

        return outputs

    # ─────────────────────────────────────────
    # RESPONSE ASSEMBLY
    # ─────────────────────────────────────────

    def _assemble_response(
        self,
        intention: str,
        layer_outputs: list[LayerOutput],
        filter_result: FilterResult,
        crystal_mode: str
    ) -> str:
        contributing = [
            o for o in layer_outputs
            if o.contributed and o.output
        ]
        if not contributing:
            return self._holding_response(crystal_mode)

        crystal_voice = self._crystal_voice(crystal_mode)
        parts = [
            f"{o.layer_name}: {o.output}"
            for o in contributing
            if o.layer_number != 3
        ]
        if not parts:
            return self._holding_response(crystal_mode)

        return f"[{crystal_voice}]\n" + "\n".join(parts)

    def _holding_response(self, crystal_mode: str) -> str:
        voices = {
            "sovereign_core":  "GAIA-OS is listening. The layers are being built.",
            "anchor_prism":    "You are held. The system is present with you.",
            "viriditas_heart": "Something in you is reaching. GAIA is here.",
            "somnus_veil":     "Rest. The system holds what you've shared.",
            "clarus_lens":     "The question is received. Clarity is coming.",
        }
        return voices.get(
            crystal_mode,
            "GAIA-OS received your intention. The system is active."
        )

    def _crystal_voice(self, crystal_mode: str) -> str:
        voices = {
            "sovereign_core":  "Sovereign Core",
            "anchor_prism":    "Anchor Prism",
            "viriditas_heart": "Viriditas Heart",
            "somnus_veil":     "Somnus Veil",
            "clarus_lens":     "Clarus Lens",
        }
        return voices.get(crystal_mode, "GAIA-OS")

    def _dissolution_response(self, filter_result: FilterResult) -> str:
        return (
            "This intention could not find its way through the love filter. "
            "Not because you are wrong. "
            "Because this particular path is not aligned with life. "
            "GAIA-OS is here when you're ready to try another way."
        )

    # ─────────────────────────────────────────
    # DIAGNOSTICS
    # ─────────────────────────────────────────

    def layer_status(self) -> dict:
        return {
            str(num): {
                "name":   info["name"],
                "built":  info["handler"] is not None,
                "status": "live" if info["handler"] else "pending_build",
            }
            for num, info in LAYER_REGISTRY.items()
        }


# ─────────────────────────────────────────────
# SINGLETON — One kernel. One spine.
# ─────────────────────────────────────────────

kernel = GAIAKernel()


def process_intention(intention: str, context: dict = None) -> KernelResult:
    """
    Public interface for the kernel.
    Called by FastAPI routes.
    Returns a KernelResult.
    """
    return kernel.process(intention, context)
